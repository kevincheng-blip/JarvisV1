"""
War Room Engine v6.0 - 純事件流引擎
專為 FastAPI WebSocket 和 Next.js 前端設計
不依賴 Streamlit，純粹的事件驅動架構
"""
import asyncio
import time
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Literal, Optional, AsyncGenerator, Callable

from jgod.war_room.providers import ProviderManager
from jgod.war_room.providers.base_provider import ProviderResult
from jgod.war_room_v6.config import (
    ROLE_PROVIDER_MAP,
    ROLE_SYSTEM_PROMPTS,
    ROLE_CHINESE_NAMES,
)

logger = logging.getLogger("war_room")


# 事件類型定義
EventType = Literal["session_start", "role_start", "role_chunk", "role_done", "summary", "error"]


@dataclass
class WarRoomRequest:
    """War Room 執行請求"""
    session_id: str
    stock_ids: List[str]  # 例如 ["2330", "2412"]
    mode: Literal["god", "custom"]
    enabled_providers: List[str]  # ["gpt", "claude", "gemini", "perplexity"]
    max_tokens: int = 512
    user_prompt: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    market_context: Optional[str] = None


@dataclass
class WarRoomEvent:
    """War Room 事件（可序列化為 JSON）"""
    type: EventType
    session_id: str
    role: Optional[str] = None
    role_label: Optional[str] = None  # 中文名稱
    provider: Optional[str] = None
    chunk: Optional[str] = None
    content: Optional[str] = None
    error: Optional[str] = None
    meta: Optional[Dict] = None
    
    def dict(self) -> Dict:
        """轉換為字典（用於 JSON 序列化）"""
        return asdict(self)


class WarRoomEngineV6:
    """
    War Room Engine v6.0 - 純事件流引擎
    
    特點：
    - 不依賴 Streamlit
    - 不依賴 session_state
    - 純事件驅動，透過 async generator 產生事件流
    - 完全並行執行所有角色
    - 專為 WebSocket 設計
    """
    
    def __init__(self, provider_manager: ProviderManager):
        """
        初始化 War Room Engine v6
        
        Args:
            provider_manager: Provider 管理器實例（重用現有的 ProviderManager）
        """
        self.provider_manager = provider_manager
        self.role_provider_map = ROLE_PROVIDER_MAP
        self.role_system_prompts = ROLE_SYSTEM_PROMPTS
        self.role_chinese_names = ROLE_CHINESE_NAMES
        self.logger = logger
    
    def _build_prompt(
        self,
        request: WarRoomRequest,
    ) -> str:
        """
        組合完整的提示字串
        
        Args:
            request: War Room 請求
            
        Returns:
            完整的提示字串
        """
        parts = []
        
        # 股票代號
        if request.stock_ids:
            stock_list = "、".join(request.stock_ids)
            parts.append(f"股票代號: {stock_list}")
        
        # 日期區間
        if request.start_date and request.end_date:
            parts.append(f"日期區間: {request.start_date} ~ {request.end_date}")
        
        # 市場上下文（如果有）
        if request.market_context:
            parts.append(f"\n{request.market_context}")
        
        # 使用者問題
        if request.user_prompt:
            parts.append(f"\n問題: {request.user_prompt}")
        
        return "\n".join(parts) if parts else request.user_prompt or "請進行分析"
    
    def _get_enabled_roles(
        self,
        request: WarRoomRequest,
    ) -> List[str]:
        """
        根據請求取得要執行的角色列表
        
        Args:
            request: War Room 請求
            
        Returns:
            角色名稱列表
        """
        enabled_roles = []
        
        for role_name, provider_key in self.role_provider_map.items():
            # 檢查此角色的 Provider 是否在 enabled_providers 中
            if provider_key in request.enabled_providers:
                enabled_roles.append(role_name)
        
        return enabled_roles
    
    async def run_session(
        self,
        request: WarRoomRequest,
    ) -> AsyncGenerator[WarRoomEvent, None]:
        """
        啟動一個戰情室 Session，並以 async generator 形式產生事件流
        
        事件順序：
        1. session_start - Session 開始
        2. role_start - 每個角色開始執行
        3. role_chunk - 每個角色的 streaming chunk（可能多次）
        4. role_done - 每個角色完成
        5. summary - 最終總結
        6. error - 錯誤事件（如果發生）
        
        Args:
            request: War Room 請求
            
        Yields:
            WarRoomEvent: 戰情室事件
        """
        self.logger.info(f"[ENGINE_V6] Starting session: {request.session_id}")
        self.logger.info(f"[ENGINE_V6] Mode: {request.mode}, Providers: {request.enabled_providers}")
        
        # 1. 產生 session_start 事件
        yield WarRoomEvent(
            type="session_start",
            session_id=request.session_id,
            meta={
                "mode": request.mode,
                "enabled_providers": request.enabled_providers,
                "stock_ids": request.stock_ids,
            },
        )
        
        # 2. 取得要執行的角色列表
        enabled_roles = self._get_enabled_roles(request)
        if not enabled_roles:
            error_msg = f"No roles enabled for providers: {request.enabled_providers}"
            self.logger.error(f"[ENGINE_V6] {error_msg}")
            yield WarRoomEvent(
                type="error",
                session_id=request.session_id,
                error=error_msg,
            )
            return
        
        self.logger.info(f"[ENGINE_V6] Enabled roles: {enabled_roles}")
        
        # 3. 組合完整提示
        full_prompt = self._build_prompt(request)
        
        # 4. 建立事件佇列和角色結果字典
        event_queue: asyncio.Queue[WarRoomEvent] = asyncio.Queue()
        role_results: Dict[str, ProviderResult] = {}
        role_tasks: Dict[str, asyncio.Task] = {}
        
        # 5. 定義單一角色執行函式
        async def run_single_role(role_name: str, provider_key: str):
            """執行單一角色（內部函式）"""
            role_start_time = time.time()
            
            try:
                # 5.1 產生 role_start 事件
                await event_queue.put(WarRoomEvent(
                    type="role_start",
                    session_id=request.session_id,
                    role=role_name,
                    role_label=self.role_chinese_names.get(role_name, role_name),
                    provider=provider_key,
                    meta={"started_at": time.time()},
                ))
                self.logger.info(f"[ENGINE_V6] Role started: {role_name} (provider: {provider_key})")
                
                # 5.2 取得系統提示
                system_prompt = self.role_system_prompts.get(
                    role_name,
                    "你是一個專業的股市分析師。"
                )
                
                # 5.3 建立 chunk 累積器
                full_content = ""
                
                # 5.4 定義 chunk callback（同步函式，需要轉換為異步）
                def on_chunk(chunk: str):
                    """Chunk 回調函式（同步）"""
                    nonlocal full_content
                    full_content += chunk
                    
                    # 將 chunk 事件放入佇列（使用 create_task 確保非阻塞）
                    chunk_event = WarRoomEvent(
                        type="role_chunk",
                        session_id=request.session_id,
                        role=role_name,
                        role_label=self.role_chinese_names.get(role_name, role_name),
                        provider=provider_key,
                        chunk=chunk,
                    )
                    # 使用 asyncio.create_task 將同步 callback 轉為異步
                    try:
                        loop = asyncio.get_event_loop()
                        loop.call_soon_threadsafe(
                            lambda: asyncio.create_task(event_queue.put(chunk_event))
                        )
                    except Exception as e:
                        self.logger.error(f"[ENGINE_V6] Error putting chunk event: {e}")
                
                # 5.5 呼叫 ProviderManager 執行角色
                result = await self.provider_manager.run_role_streaming(
                    role_name=role_name,
                    prompt=full_prompt,
                    enabled_providers=request.enabled_providers,
                    on_chunk=on_chunk,
                )
                
                execution_time = time.time() - role_start_time
                role_results[role_name] = result
                
                # 5.6 產生 role_done 事件
                await event_queue.put(WarRoomEvent(
                    type="role_done",
                    session_id=request.session_id,
                    role=role_name,
                    role_label=self.role_chinese_names.get(role_name, role_name),
                    provider=provider_key,
                    content=result.content if result.success else "",
                    error=result.error if not result.success else None,
                    meta={
                        "success": result.success,
                        "execution_time": execution_time,
                        "provider_name": result.provider_name,
                    },
                ))
                self.logger.info(
                    f"[ENGINE_V6] Role done: {role_name}, "
                    f"success={result.success}, time={execution_time:.2f}s"
                )
                
            except Exception as e:
                execution_time = time.time() - role_start_time
                error_msg = f"Role {role_name} failed: {str(e)}"
                self.logger.error(f"[ENGINE_V6] {error_msg}", exc_info=True)
                
                # 產生錯誤事件
                await event_queue.put(WarRoomEvent(
                    type="role_done",
                    session_id=request.session_id,
                    role=role_name,
                    role_label=self.role_chinese_names.get(role_name, role_name),
                    provider=provider_key,
                    error=error_msg,
                    meta={"success": False, "execution_time": execution_time},
                ))
                
                # 儲存錯誤結果
                role_results[role_name] = ProviderResult(
                    success=False,
                    content="",
                    error=error_msg,
                    provider_name=provider_key,
                    execution_time=execution_time,
                )
        
        # 6. 啟動所有角色任務（並行執行）
        for role_name in enabled_roles:
            provider_key = self.role_provider_map.get(role_name)
            if not provider_key:
                self.logger.warning(f"[ENGINE_V6] No provider mapping for role: {role_name}")
                continue
            
            task = asyncio.create_task(run_single_role(role_name, provider_key))
            role_tasks[role_name] = task
        
        if not role_tasks:
            error_msg = "No valid roles to execute"
            self.logger.error(f"[ENGINE_V6] {error_msg}")
            yield WarRoomEvent(
                type="error",
                session_id=request.session_id,
                error=error_msg,
            )
            return
        
        # 7. 從事件佇列中取出事件並 yield（直到所有角色完成）
        completed_roles = set()
        active_tasks = set(role_tasks.values())
        
        while len(completed_roles) < len(role_tasks) or not event_queue.empty():
            try:
                # 等待事件或任務完成（使用 asyncio.wait_for 避免無限等待）
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    yield event
                except asyncio.TimeoutError:
                    # 檢查是否有任務完成
                    done_tasks = {task for task in active_tasks if task.done()}
                    if done_tasks:
                        active_tasks -= done_tasks
                        # 繼續等待事件
                        continue
                    else:
                        # 沒有新事件也沒有完成的任務，繼續等待
                        continue
                
                # 檢查是否有角色完成
                for role_name, task in role_tasks.items():
                    if task.done() and role_name not in completed_roles:
                        completed_roles.add(role_name)
                        self.logger.debug(f"[ENGINE_V6] Role {role_name} task completed")
                
            except asyncio.CancelledError:
                self.logger.warning(f"[ENGINE_V6] Session cancelled: {request.session_id}")
                break
            except Exception as e:
                self.logger.error(f"[ENGINE_V6] Error processing event: {e}", exc_info=True)
                yield WarRoomEvent(
                    type="error",
                    session_id=request.session_id,
                    error=f"Event processing error: {str(e)}",
                )
                break
        
        # 8. 等待所有任務完成（確保所有角色都執行完畢）
        if active_tasks:
            try:
                await asyncio.gather(*active_tasks, return_exceptions=True)
            except Exception as e:
                self.logger.error(f"[ENGINE_V6] Error waiting for tasks: {e}", exc_info=True)
        
        # 9. 處理剩餘的事件（確保所有事件都被 yield）
        while not event_queue.empty():
            try:
                event = event_queue.get_nowait()
                yield event
            except asyncio.QueueEmpty:
                break
        
        # 10. 產生 summary 事件
        summary_content = self._generate_summary(role_results, request)
        yield WarRoomEvent(
            type="summary",
            session_id=request.session_id,
            content=summary_content,
            meta={
                "total_roles": len(role_results),
                "successful_roles": sum(1 for r in role_results.values() if r.success),
                "failed_roles": sum(1 for r in role_results.values() if not r.success),
            },
        )
        
        self.logger.info(f"[ENGINE_V6] Session completed: {request.session_id}")
    
    def _generate_summary(
        self,
        role_results: Dict[str, ProviderResult],
        request: WarRoomRequest,
    ) -> str:
        """
        產生總結內容
        
        Args:
            role_results: 角色結果字典
            request: War Room 請求
            
        Returns:
            總結文字
        """
        successful_roles = [name for name, result in role_results.items() if result.success]
        failed_roles = [name for name, result in role_results.items() if not result.success]
        
        summary_parts = [
            f"戰情室分析完成（Session: {request.session_id}）",
            f"執行角色數: {len(role_results)}",
            f"成功: {len(successful_roles)}",
        ]
        
        if failed_roles:
            summary_parts.append(f"失敗: {len(failed_roles)} ({', '.join(failed_roles)})")
        
        # 如果有 Strategist 角色的結果，優先使用
        if "Strategist" in role_results and role_results["Strategist"].success:
            strategist_content = role_results["Strategist"].content
            if strategist_content:
                summary_parts.append(f"\n策略統整建議:\n{strategist_content[:500]}...")
        
        return "\n".join(summary_parts)

