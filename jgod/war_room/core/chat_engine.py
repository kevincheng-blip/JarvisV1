"""
War Room Engine v4.0 - 核心聊天引擎
乾淨、可維護、可擴充的多 AI 戰情室引擎
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Callable

from jgod.war_room.core.models import (
    RoleName,
    ProviderKey,
    RoleResult,
    WarRoomResult,
    ROLE_PROVIDER_MAP,
    ROLE_SYSTEM_PROMPTS,
    MODE_PROVIDER_MAP,
)
from jgod.war_room.providers import ProviderManager
from jgod.war_room.providers.base_provider import BaseProviderAsync, ProviderResult


logger = logging.getLogger("war_room")


class WarRoomEngine:
    """War Room Engine v4.0 - 多 AI 戰情室核心引擎"""
    
    def __init__(self, provider_manager: ProviderManager):
        """
        初始化 War Room Engine
        
        Args:
            provider_manager: Provider 管理器實例
        """
        self.provider_manager = provider_manager
        self.logger = logging.getLogger("war_room")
    
    def _get_enabled_providers(self, mode: str, custom_providers: Optional[List[ProviderKey]]) -> List[ProviderKey]:
        """
        根據 Mode 取得啟用的 Provider 列表
        
        Args:
            mode: 模式（Lite / Pro / God / Custom）
            custom_providers: Custom 模式下的自訂 Provider 列表
        
        Returns:
            啟用的 Provider 列表
        """
        if mode in ["Lite", "Pro", "God"]:
            providers = MODE_PROVIDER_MAP.get(mode, ["gpt"])
            self.logger.info(f"Mode {mode} -> enabled_providers: {providers}")
            return providers
        elif mode == "Custom":
            if custom_providers:
                self.logger.info(f"Custom mode -> enabled_providers: {custom_providers}")
                return custom_providers
            else:
                self.logger.warning("Custom mode but no custom_providers provided, defaulting to ['gpt']")
                return ["gpt"]
        else:
            self.logger.warning(f"Unknown mode: {mode}, defaulting to ['gpt']")
            return ["gpt"]
    
    async def _run_single_role(
        self,
        role: RoleName,
        prompt: str,
        system_prompt: str,
        provider: BaseProviderAsync,
        provider_key: ProviderKey,
        on_chunk: Optional[Callable[[RoleName, str], None]] = None,
    ) -> RoleResult:
        """
        執行單一角色的分析（支援 streaming）
        
        Args:
            role: 角色名稱
            prompt: 使用者提示
            system_prompt: 系統提示
            provider: Provider 實例
            provider_key: Provider 鍵值
            on_chunk: Streaming chunk 回調函數
        
        Returns:
            RoleResult
        """
        start_time = time.time()
        
        try:
            # 使用 streaming 模式
            full_content = ""
            
            def chunk_callback(chunk: str):
                """內部 chunk 回調（v4.1: 即時更新）"""
                nonlocal full_content
                full_content += chunk
                
                # Debug log
                self.logger.info(f"[ENGINE] Chunk received: role={role.value}, chunk={chunk[:50]}...")
                
                if on_chunk:
                    try:
                        # v4.1: 立即呼叫 callback 更新 UI
                        on_chunk(role, chunk)
                    except Exception as e:
                        self.logger.error(f"Error in on_chunk callback for {role}: {e}", exc_info=True)
            
            # 呼叫 provider 的 streaming 方法
            result = await provider.run_stream(
                prompt=prompt,
                system_prompt=system_prompt,
                on_chunk=chunk_callback,
            )
            
            execution_time = time.time() - start_time
            
            # Debug log: 角色完成
            self.logger.info(f"[ENGINE] Role done: {role.value}, success={result.success}")
            
            if result.success:
                # 如果 streaming 有累積內容，使用累積內容；否則使用 result.content
                final_content = full_content if full_content else result.content
                return RoleResult(
                    role=role,
                    provider_key=provider_key,
                    success=True,
                    content=final_content,
                    execution_time=execution_time,
                )
            else:
                return RoleResult(
                    role=role,
                    provider_key=provider_key,
                    success=False,
                    content="",
                    error=result.error or "Unknown error",
                    execution_time=execution_time,
                )
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.exception(f"Role {role} failed with exception")
            return RoleResult(
                role=role,
                provider_key=provider_key,
                success=False,
                content="",
                error=f"API_CALL_FAILED:{str(e)}",
                execution_time=execution_time,
            )
    
    async def run_war_room(
        self,
        mode: str,
        custom_providers: Optional[List[ProviderKey]],
        stock_id: str,
        start_date: str,
        end_date: str,
        user_question: str,
        market_context: str = "",
        streaming_callback: Optional[Callable[[RoleName, str], None]] = None,
    ) -> WarRoomResult:
        """
        執行 War Room 分析（核心方法）
        
        Args:
            mode: 模式（Lite / Pro / God / Custom）
            custom_providers: Custom 模式下的自訂 Provider 列表
            stock_id: 股票代號
            start_date: 開始日期
            end_date: 結束日期
            user_question: 使用者問題
            market_context: 市場資料上下文（可選）
            streaming_callback: Streaming chunk 回調函數 (role: RoleName, chunk: str) -> None
        
        Returns:
            WarRoomResult
        """
        self.logger.info(f"=== War Room Engine v4.0 Execution ===")
        self.logger.info(f"Mode: {mode}")
        
        # 取得啟用的 Provider
        enabled_providers = self._get_enabled_providers(mode, custom_providers)
        self.logger.info(f"Enabled Providers: {enabled_providers}")
        self.logger.info(f"Available Providers in manager: {list(self.provider_manager.providers.keys())}")
        
        # 組合完整提示
        if market_context:
            full_prompt = f"{market_context}\n\n問題: {user_question}"
        else:
            full_prompt = f"股票代號: {stock_id}\n日期區間: {start_date} ~ {end_date}\n\n問題: {user_question}"
        
        # 建立所有角色的任務
        tasks: List[asyncio.Task] = []
        task_to_role: Dict[asyncio.Task, RoleName] = {}
        
        for role in RoleName:
            provider_key = ROLE_PROVIDER_MAP.get(role)
            self.logger.info(f"[ENGINE] Dispatching role: {role.value}")
            self.logger.info(f"[ENGINE] Provider: {provider_key}")
            
            # 檢查此角色的 Provider 是否啟用
            if provider_key not in enabled_providers:
                self.logger.info(f"Role {role.value} (provider: {provider_key}) is not enabled, skipping")
                continue
            
            # 取得 Provider 實例
            provider = self.provider_manager.providers.get(provider_key)
            if not provider:
                # 檢查是否因為 API Key 未設定而導致 Provider 未初始化
                import os
                api_key_env_map = {
                    "gpt": ["OPENAI_API_KEY"],
                    "claude": ["ANTHROPIC_API_KEY"],
                    "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
                    "perplexity": ["PERPLEXITY_API_KEY"],
                }
                api_key_envs = api_key_env_map.get(provider_key, [])
                has_key = any(os.getenv(k) for k in api_key_envs) if api_key_envs else False
                
                if not has_key:
                    env_names = " 或 ".join(api_key_envs)
                    self.logger.warning(
                        f"Provider {provider_key} not initialized for role {role.value}: "
                        f"API Key not set ({env_names})"
                    )
                else:
                    self.logger.warning(
                        f"Provider {provider_key} not initialized for role {role.value}: "
                        f"Initialization failed (check logs)"
                    )
                continue
            
            # 取得系統提示
            system_prompt = ROLE_SYSTEM_PROMPTS.get(role, "你是一個專業的股市分析師。")
            
            # 建立任務（使用 lambda 確保閉包正確捕獲變數）
            async def create_role_task(r: RoleName, p: BaseProviderAsync, pk: ProviderKey, sp: str, prompt: str):
                """建立角色任務（閉包捕獲變數）"""
                return await self._run_single_role(
                    role=r,
                    prompt=prompt,
                    system_prompt=sp,
                    provider=p,
                    provider_key=pk,
                    on_chunk=streaming_callback,
                )
            
            task = asyncio.create_task(
                create_role_task(role, provider, provider_key, system_prompt, full_prompt)
            )
            tasks.append(task)
            task_to_role[task] = role
            self.logger.info(f"Created task for role: {role.value} (provider: {provider_key})")
        
        if not tasks:
            self.logger.warning("No tasks created! No roles will be executed.")
            return WarRoomResult(
                results={},
                executed_roles=[],
                failed_roles=[],
            )
        
        # 使用 gather 並行執行所有任務（確保所有 coroutine 都被正確 await）
        self.logger.info(f"Executing {len(tasks)} roles in parallel...")
        start_time = time.time()
        
        try:
            # 使用 gather 確保所有任務都被正確 await
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            execution_time = time.time() - start_time
            self.logger.info(f"All roles completed in {execution_time:.2f}s")
            
            # 處理結果
            role_results: Dict[RoleName, RoleResult] = {}
            
            for i, result in enumerate(results_list):
                task = tasks[i]
                role = task_to_role[task]
                
                if isinstance(result, Exception):
                    self.logger.error(f"Role {role.value} raised exception: {result}", exc_info=True)
                    role_results[role] = RoleResult(
                        role=role,
                        provider_key=ROLE_PROVIDER_MAP.get(role, "gpt"),
                        success=False,
                        content="",
                        error=f"EXCEPTION:{str(result)}",
                        execution_time=0.0,
                    )
                else:
                    role_results[role] = result
                    status = "Success" if result.success else "Failed"
                    self.logger.info(f"Role {role.value}: {status} (time={result.execution_time:.2f}s)")
            
            # 建立 WarRoomResult
            war_room_result = WarRoomResult(
                results=role_results,
                executed_roles=[],
                failed_roles=[],
            )
            
            # 記錄最終結果
            self.logger.info(f"War Room execution completed:")
            self.logger.info(f"  Executed roles: {[r.value for r in war_room_result.executed_roles]}")
            self.logger.info(f"  Failed roles: {[r.value for r in war_room_result.failed_roles]}")
            self.logger.info(f"  Total execution time: {execution_time:.2f}s")
            
            return war_room_result
            
        except Exception as e:
            self.logger.exception("War Room execution failed with exception")
            # 即使失敗，也返回已完成的結果
            role_results: Dict[RoleName, RoleResult] = {}
            for task in tasks:
                if task.done():
                    role = task_to_role[task]
                    try:
                        result = task.result()
                        role_results[role] = result
                    except Exception as task_error:
                        role_results[role] = RoleResult(
                            role=role,
                            provider_key=ROLE_PROVIDER_MAP.get(role, "gpt"),
                            success=False,
                            content="",
                            error=f"EXCEPTION:{str(task_error)}",
                            execution_time=0.0,
                        )
            
            return WarRoomResult(
                results=role_results,
                executed_roles=[],
                failed_roles=[],
            )

