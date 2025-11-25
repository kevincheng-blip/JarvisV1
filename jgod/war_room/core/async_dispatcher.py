"""
Async Dispatcher：負責非同步任務調度和即時更新
"""
import asyncio
from typing import Dict, List, Optional, Callable
import logging

from jgod.war_room.providers.base_provider import ProviderResult
from jgod.war_room.core.streaming_engine import StreamingEngine


class AsyncDispatcher:
    """非同步任務調度器：使用 as_completed 實現逐角色即時更新"""
    
    def __init__(self):
        self.streaming_engine = StreamingEngine()
        self.logger = logging.getLogger("war_room.async_dispatcher")
    
    async def dispatch_all_roles_streaming(
        self,
        role_tasks: Dict[str, Callable],  # {role_name: async_function}
        on_role_complete: Optional[Callable[[str, ProviderResult], None]] = None,
    ) -> Dict[str, ProviderResult]:
        """
        並行執行所有角色任務，使用 as_completed 實現逐角色即時更新
        
        Args:
            role_tasks: 角色任務字典 {role_name: async_function}
            on_role_complete: 每當一個角色完成時的回調 (role_name, result) -> None
        
        Returns:
            角色名稱到結果的映射
        """
        if not role_tasks:
            self.logger.warning("No tasks to dispatch")
            return {}
        
        # 將所有 coroutine 轉換為 task
        tasks = []
        task_to_role = {}
        for role_name, coro in role_tasks.items():
            task = asyncio.create_task(coro)
            tasks.append(task)
            task_to_role[task] = role_name
            self.logger.info(f"Created task for role: {role_name}")
        
        role_results = {}
        
        # 使用 as_completed 逐個處理完成的任務（正確使用 async for）
        async for completed_task in asyncio.as_completed(tasks):
            role_name = task_to_role.get(completed_task)
            
            if not role_name:
                self.logger.error(f"Could not find role_name for completed task")
                continue
            
            try:
                result = await completed_task
                role_results[role_name] = result
                status = "Success" if result.success else "Failed"
                self.logger.info(f"Role {role_name} completed: {status} (execution_time={result.execution_time:.2f}s)")
                
                if not result.success:
                    self.logger.warning(f"Role {role_name} failed with error: {result.error}")
                
                # 呼叫回調函數（用於即時更新 UI）
                if on_role_complete:
                    try:
                        on_role_complete(role_name, result)
                    except Exception as callback_error:
                        self.logger.error(f"Error in on_role_complete callback for {role_name}: {callback_error}")
            except Exception as e:
                error_result = ProviderResult(
                    success=False,
                    content="",
                    error=f"API_CALL_FAILED:{str(e)}",
                    provider_name="unknown",
                )
                role_results[role_name] = error_result
                self.logger.error(f"Role {role_name} failed with exception: {e}", exc_info=True)
                
                if on_role_complete:
                    try:
                        on_role_complete(role_name, error_result)
                    except Exception as callback_error:
                        self.logger.error(f"Error in on_role_complete callback for {role_name}: {callback_error}")
        
        self.logger.info(f"dispatch_all_roles_streaming completed. Executed roles: {list(role_results.keys())}")
        for role_name, result in role_results.items():
            status = "Success" if result.success else "Failed"
            self.logger.info(f"  - {role_name}: {status}")
        
        return role_results
    
    async def dispatch_with_streaming(
        self,
        role_name: str,
        provider,
        prompt: str,
        system_prompt: Optional[str] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> ProviderResult:
        """
        使用 streaming 引擎執行單個角色
        
        Args:
            role_name: 角色名稱
            provider: Provider 實例
            prompt: 使用者提示
            system_prompt: 系統提示
            on_chunk: 每收到一個 chunk 時的回調
        
        Returns:
            ProviderResult
        """
        return await self.streaming_engine.stream_provider(
            role_name=role_name,
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt,
            on_chunk=on_chunk,
        )

