"""
War Room Engine v5.0 - 後端版本
支援真正的 async generator streaming
"""
import asyncio
import time
import logging
from typing import AsyncIterator, Optional, Dict, List
from uuid import uuid4

from jgod.war_room.providers import ProviderManager
from jgod.war_room.core.models import RoleName, ProviderKey, ROLE_PROVIDER_MAP, MODE_PROVIDER_MAP
from jgod.war_room_backend.models import (
    WarRoomEvent,
    SessionStartEvent,
    RoleChunkEvent,
    RoleDoneEvent,
    SummaryEvent,
    ErrorEvent,
)

logger = logging.getLogger("war_room_backend.engine")


class WarRoomEngineBackend:
    """War Room Engine 後端版本（支援 WebSocket streaming）"""
    
    def __init__(self):
        self.provider_manager = ProviderManager()
        self.logger = logger
    
    def _get_enabled_providers(self, mode: str, custom_providers: Optional[List[ProviderKey]]) -> List[ProviderKey]:
        """取得啟用的 Provider 列表"""
        if mode in ["Lite", "Pro", "God"]:
            return MODE_PROVIDER_MAP.get(mode, ["gpt"])
        elif mode == "Custom" and custom_providers:
            return custom_providers
        else:
            return ["gpt"]
    
    async def run_war_room(
        self,
        session_id: str,
        mode: str,
        custom_providers: Optional[List[ProviderKey]],
        stock_id: str,
        start_date: str,
        end_date: str,
        user_question: str,
        market_context: str = "",
    ) -> AsyncIterator[WarRoomEvent]:
        """
        執行 War Room 分析（async generator，支援真正的 streaming）
        
        Yields:
            WarRoomEvent: 各種戰情室事件（包含即時 chunk）
        """
        try:
            # 取得啟用的 Provider
            enabled_providers = self._get_enabled_providers(mode, custom_providers)
            self.logger.info(f"War Room session {session_id} started: mode={mode}, providers={enabled_providers}")
            
            # 發送會話開始事件
            yield SessionStartEvent(
                session_id=session_id,
                mode=mode,
                enabled_providers=enabled_providers,
                stock_id=stock_id,
                question=user_question,
            )
            
            # 組合完整提示
            if market_context:
                full_prompt = f"{market_context}\n\n問題: {user_question}"
            else:
                full_prompt = f"股票代號: {stock_id}\n日期區間: {start_date} ~ {end_date}\n\n問題: {user_question}"
            
            # 建立所有角色的任務（使用 queue 實現即時 chunk 更新）
            tasks = []
            task_to_role = {}
            role_sequences = {}  # 追蹤每個角色的 chunk 序列號
            event_queue = asyncio.Queue()  # 統一的事件佇列
            
            for role in RoleName:
                provider_key = ROLE_PROVIDER_MAP.get(role)
                
                if provider_key not in enabled_providers:
                    continue
                
                provider = self.provider_manager.providers.get(provider_key)
                if not provider:
                    continue
                
                system_prompt = f"你是 J-GOD 戰情室的{role.value}，負責提供專業分析。"
                role_sequences[role] = 0
                
                # 建立任務（會透過 event_queue 發送 chunk 和 done 事件）
                async def create_role_task(r: RoleName, p, pk: ProviderKey, sp: str, prompt: str):
                    """建立角色任務（透過 event_queue 發送事件）"""
                    await self._run_single_role_streaming(
                        role=r,
                        prompt=prompt,
                        system_prompt=sp,
                        provider=p,
                        provider_key=pk,
                        session_id=session_id,
                        role_sequences=role_sequences,
                        event_queue=event_queue,
                    )
                
                task = asyncio.create_task(
                    create_role_task(role, provider, provider_key, system_prompt, full_prompt)
                )
                tasks.append(task)
                task_to_role[task] = role
            
            if not tasks:
                yield ErrorEvent(
                    session_id=session_id,
                    error_type="NO_TASKS",
                    message="沒有可執行的角色任務",
                )
                return
            
            # 使用 as_completed 實現即時更新
            self.logger.info(f"Executing {len(tasks)} roles in parallel...")
            
            # 持續監聽事件 queue 並 yield
            completed_count = 0
            while completed_count < len(tasks):
                try:
                    # 等待事件（最多 0.1 秒）
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    yield event
                    
                    # 如果是 done 事件，增加完成計數
                    if isinstance(event, RoleDoneEvent):
                        completed_count += 1
                except asyncio.TimeoutError:
                    # 檢查是否有任務完成
                    done, pending = await asyncio.wait(tasks, timeout=0.01, return_when=asyncio.FIRST_COMPLETED)
                    if done:
                        # 處理剩餘事件
                        while not event_queue.empty():
                            try:
                                event = event_queue.get_nowait()
                                yield event
                                if isinstance(event, RoleDoneEvent):
                                    completed_count += 1
                            except asyncio.QueueEmpty:
                                break
                    continue
            
            # 確保所有事件都已發送
            while not event_queue.empty():
                try:
                    event = event_queue.get_nowait()
                    yield event
                except asyncio.QueueEmpty:
                    break
            
            # 發送總結
            yield SummaryEvent(
                session_id=session_id,
                content="所有角色分析完成",
                execution_time=0.0,
            )
            
        except Exception as e:
            self.logger.error(f"War Room execution failed: {e}", exc_info=True)
            yield ErrorEvent(
                session_id=session_id,
                error_type="EXECUTION_ERROR",
                message=str(e),
            )
    
    async def _run_single_role_streaming(
        self,
        role: RoleName,
        prompt: str,
        system_prompt: str,
        provider,
        provider_key: ProviderKey,
        session_id: str,
        role_sequences: Dict[RoleName, int],
        event_queue: asyncio.Queue,
    ) -> None:
        """執行單一角色（透過 event_queue 發送 chunk 和 done 事件）"""
        start_time = time.time()
        full_content = ""
        sequence = 0
        
        try:
            def chunk_callback(chunk: str):
                """Chunk 回調（透過 queue 發送即時 chunk 事件）"""
                nonlocal full_content, sequence
                full_content += chunk
                sequence += 1
                
                # 建立 chunk 事件並放入 queue
                chunk_event = RoleChunkEvent(
                    session_id=session_id,
                    role=role.value.lower().replace(" ", "_"),
                    role_label=self._get_role_label(role.value),
                    provider=provider_key,
                    chunk=chunk,
                    sequence=sequence,
                    is_final=False,
                )
                # 使用 asyncio 確保非阻塞
                try:
                    event_queue.put_nowait(chunk_event)
                except asyncio.QueueFull:
                    # Queue 滿了，記錄警告但不阻塞
                    self.logger.warning(f"Event queue full for role {role.value}")
            
            result = await provider.run_stream(
                prompt=prompt,
                system_prompt=system_prompt,
                on_chunk=chunk_callback,
            )
            
            execution_time = time.time() - start_time
            
            # 發送角色完成事件
            done_event = RoleDoneEvent(
                session_id=session_id,
                role=role.value.lower().replace(" ", "_"),
                role_label=self._get_role_label(role.value),
                provider=provider_key,
                success=result.success,
                content=result.content or full_content,
                execution_time=execution_time,
                error_message=result.error if not result.success else None,
            )
            await event_queue.put(done_event)
            
        except Exception as e:
            execution_time = time.time() - start_time
            done_event = RoleDoneEvent(
                session_id=session_id,
                role=role.value.lower().replace(" ", "_"),
                role_label=self._get_role_label(role.value),
                provider=provider_key,
                success=False,
                content="",
                execution_time=execution_time,
                error_message=str(e),
            )
            await event_queue.put(done_event)
    
    def _get_role_label(self, role_name: str) -> str:
        """取得角色中文標籤"""
        labels = {
            "Intel Officer": "情報官",
            "Scout": "斥候",
            "Risk Officer": "風控長",
            "Quant Lead": "量化長",
            "Strategist": "策略統整",
            "Execution Officer": "執行官",
        }
        return labels.get(role_name, role_name)

