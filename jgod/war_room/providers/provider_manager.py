"""
Provider 管理器：統一管理所有 Provider 的非同步執行
"""
import asyncio
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime

from .gpt_provider import GPTProviderAsync
from .claude_provider import ClaudeProviderAsync
from .gemini_provider import GeminiProviderAsync
from .perplexity_provider import PerplexityProviderAsync
from .base_provider import BaseProviderAsync, ProviderResult


class ProviderManager:
    """Provider 管理器"""
    
    # 角色到 Provider 的映射
    ROLE_PROVIDER_MAP = {
        "Intel Officer": "perplexity",
        "Scout": "gemini",
        "Risk Officer": "claude",
        "Quant Lead": "claude",
        "Strategist": "gpt",
        "Execution Officer": "gpt",  # 執行官（如果未來需要）
    }
    
    # 角色系統提示
    ROLE_SYSTEM_PROMPTS = {
        "Intel Officer": "你是 J-GOD 戰情室的情報官（Intel Officer），負責蒐集與整理市場資訊。",
        "Scout": "你是 J-GOD 戰情室的偵察兵（Scout），負責快速摘要與輔助分析。",
        "Risk Officer": "你是 J-GOD 戰情室的風險官（Risk Officer），負責評估風險與提供風險建議。",
        "Quant Lead": "你是 J-GOD 戰情室的量化主管（Quant Lead），負責技術分析與量化策略。",
        "Strategist": "你是 J-GOD 戰情室的策略師（Strategist），負責統整所有意見並給出最終建議。",
    }
    
    def __init__(self):
        """初始化 Provider 管理器"""
        # 初始化時捕獲 API Key 錯誤，但不阻止初始化
        self.providers: Dict[str, BaseProviderAsync] = {}
        
        try:
            self.providers["gpt"] = GPTProviderAsync()
        except Exception as e:
            # API Key 未設定，稍後在 run 時會處理
            pass
        
        try:
            self.providers["claude"] = ClaudeProviderAsync()
        except Exception as e:
            pass
        
        try:
            self.providers["gemini"] = GeminiProviderAsync()
        except Exception as e:
            pass
        
        try:
            self.providers["perplexity"] = PerplexityProviderAsync()
        except Exception as e:
            pass
    
    async def run_role(
        self,
        role_name: str,
        prompt: str,
        enabled_providers: Optional[List[str]] = None,
    ) -> ProviderResult:
        """
        執行特定角色的分析
        
        Args:
            role_name: 角色名稱
            prompt: 使用者提示
            enabled_providers: 啟用的 Provider 列表（如果為 None 則使用角色預設）
        
        Returns:
            ProviderResult（error 欄位會包含錯誤類型標記）
        """
        # 取得角色對應的 Provider
        provider_key = self.ROLE_PROVIDER_MAP.get(role_name, "gpt")
        
        # 如果指定了 enabled_providers，檢查是否包含此 Provider
        if enabled_providers and provider_key not in enabled_providers:
            return ProviderResult(
                success=False,
                content="",
                error=f"NOT_ENABLED:Provider {provider_key} 未啟用",
                provider_name=provider_key,
            )
        
        # 取得 Provider
        provider = self.providers.get(provider_key)
        if not provider:
            # Provider 未初始化（可能是 API Key 未設定）
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
                return ProviderResult(
                    success=False,
                    content="",
                    error=f"API_KEY_MISSING:{env_names} 未設定",
                    provider_name=provider_key,
                )
            
            return ProviderResult(
                success=False,
                content="",
                error=f"NOT_FOUND:Provider {provider_key} 不存在或未初始化",
                provider_name=provider_key,
            )
        
        # 取得系統提示
        system_prompt = self.ROLE_SYSTEM_PROMPTS.get(role_name, "你是一個專業的股市分析師。")
        
        # 執行 Provider（會自動處理 API Key 和 API 呼叫錯誤）
        result = await provider.run(prompt, system_prompt)
        
        # 如果錯誤已經標記過，直接返回
        if result.error and (result.error.startswith("API_KEY_MISSING:") or 
                           result.error.startswith("API_CALL_FAILED:") or
                           result.error.startswith("NOT_ENABLED:")):
            return result
        
        # 檢查錯誤類型並標記（如果尚未標記）
        if not result.success and result.error:
            error_lower = result.error.lower()
            if "api key" in error_lower or "api_key" in error_lower or "未設定" in result.error or "not found" in error_lower or "沒設定" in result.error:
                result.error = f"API_KEY_MISSING:{result.error}"
            elif "timeout" in error_lower or "429" in result.error or "5" in result.error[:3] or "failed" in error_lower or "error" in error_lower:
                result.error = f"API_CALL_FAILED:{result.error}"
        
        return result
    
    async def run_role_streaming(
        self,
        role_name: str,
        prompt: str,
        enabled_providers: Optional[List[str]] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> ProviderResult:
        """
        執行特定角色的分析（Streaming 版本）
        
        Args:
            role_name: 角色名稱
            prompt: 使用者提示
            enabled_providers: 啟用的 Provider 列表（如果為 None 則使用角色預設）
            on_chunk: 每收到一個 chunk 時的回調函數 (chunk: str) -> None
        
        Returns:
            ProviderResult
        """
        # 取得角色對應的 Provider
        provider_key = self.ROLE_PROVIDER_MAP.get(role_name, "gpt")
        
        # 如果指定了 enabled_providers，檢查是否包含此 Provider
        if enabled_providers and provider_key not in enabled_providers:
            return ProviderResult(
                success=False,
                content="",
                error=f"NOT_ENABLED:Provider {provider_key} 未啟用",
                provider_name=provider_key,
            )
        
        # 取得 Provider
        provider = self.providers.get(provider_key)
        if not provider:
            # Provider 未初始化（可能是 API Key 未設定）
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
                return ProviderResult(
                    success=False,
                    content="",
                    error=f"API_KEY_MISSING:{env_names} 未設定",
                    provider_name=provider_key,
                )
            
            return ProviderResult(
                success=False,
                content="",
                error=f"NOT_FOUND:Provider {provider_key} 不存在或未初始化",
                provider_name=provider_key,
            )
        
        # 取得系統提示
        system_prompt = self.ROLE_SYSTEM_PROMPTS.get(role_name, "你是一個專業的股市分析師。")
        
        # 執行 Provider（Streaming 模式）
        result = await provider.run_stream(prompt, system_prompt, on_chunk=on_chunk)
        
        # 如果錯誤已經標記過，直接返回
        if result.error and (result.error.startswith("API_KEY_MISSING:") or 
                           result.error.startswith("API_CALL_FAILED:") or
                           result.error.startswith("NOT_ENABLED:")):
            return result
        
        # 檢查錯誤類型並標記（如果尚未標記）
        if not result.success and result.error:
            error_lower = result.error.lower()
            if "api key" in error_lower or "api_key" in error_lower or "未設定" in result.error or "not found" in error_lower or "沒設定" in result.error:
                result.error = f"API_KEY_MISSING:{result.error}"
            elif "timeout" in error_lower or "429" in result.error or "5" in result.error[:3] or "failed" in error_lower or "error" in error_lower:
                result.error = f"API_CALL_FAILED:{result.error}"
        
        return result
    
    async def run_all_roles_streaming(
        self,
        prompt: str,
        enabled_providers: Optional[List[str]] = None,
        on_role_complete: Optional[Callable[[str, ProviderResult], None]] = None,
        on_chunk: Optional[Callable[[str, str], None]] = None,
    ) -> Dict[str, ProviderResult]:
        """
        並行執行所有角色的分析（Streaming 版本，使用 asyncio.as_completed）
        
        Args:
            prompt: 使用者提示
            enabled_providers: 啟用的 Provider 列表（內部鍵值，例如：['gpt', 'claude']）
            on_role_complete: 每當一個角色完成時的回調函數 (role_name: str, result: ProviderResult) -> None
            on_chunk: 每收到一個 chunk 時的回調函數 (role_name: str, chunk: str) -> None
        
        Returns:
            角色名稱到結果的映射（只包含真正執行過的角色）
        """
        import logging
        logger = logging.getLogger("war_room.provider_manager")
        
        # 記錄執行資訊
        logger.info(f"run_all_roles_streaming called with enabled_providers: {enabled_providers}")
        
        # 如果沒有指定 enabled_providers，預設只使用 gpt
        if enabled_providers is None:
            enabled_providers = ["gpt"]
            logger.warning("enabled_providers is None, defaulting to ['gpt']")
        
        roles = list(self.ROLE_PROVIDER_MAP.keys())
        
        # 建立任務列表和映射（使用 id(task) 作為 key，因為 as_completed 返回的 task 可能不是同一個對象）
        tasks = []
        task_id_to_role = {}
        
        for role_name in roles:
            provider_key = self.ROLE_PROVIDER_MAP.get(role_name)
            
            # 檢查此角色的 Provider 是否啟用
            if provider_key in enabled_providers:
                # 建立 chunk 回調（如果有的話）
                def make_chunk_callback(rn):
                    def chunk_callback(chunk: str):
                        if on_chunk:
                            try:
                                on_chunk(rn, chunk)
                            except Exception as e:
                                logger.error(f"Error in on_chunk callback for {rn}: {e}")
                    return chunk_callback
                
                # 建立 streaming coroutine
                coro = self.run_role_streaming(
                    role_name, 
                    prompt, 
                    enabled_providers,
                    on_chunk=make_chunk_callback(role_name) if on_chunk else None
                )
                # 轉換為 task
                task = asyncio.create_task(coro)
                tasks.append(task)
                # 使用 task 的 id 作為 key（更可靠）
                task_id_to_role[id(task)] = role_name
                logger.info(f"Role {role_name} (provider: {provider_key}) will be executed")
            else:
                # Provider 未啟用，跳過（不加入結果）
                logger.info(f"Role {role_name} (provider: {provider_key}) is not enabled, skipping")
        
        # 使用 as_completed 實現逐角色即時更新
        role_results = {}
        executed_roles = []
        
        if tasks:
            # 正確使用 async for 遍歷 as_completed
            for completed_task in asyncio.as_completed(tasks):
                # 使用 task id 來查找 role_name
                task_id = id(completed_task)
                role_name = task_id_to_role.get(task_id)
                
                if not role_name:
                    # 如果找不到，嘗試從所有 tasks 中查找
                    for t in tasks:
                        if id(t) == task_id:
                            role_name = task_id_to_role.get(id(t))
                            break
                    
                    if not role_name:
                        logger.error(f"Could not find role_name for completed task (task_id={task_id})")
                        continue
                
                try:
                    result = await completed_task
                    role_results[role_name] = result
                    executed_roles.append(role_name)
                    status = "Success" if result.success else "Failed"
                    logger.info(f"Role {role_name} completed: {status} (execution_time={result.execution_time:.2f}s)")
                    
                    if not result.success:
                        logger.warning(f"Role {role_name} failed with error: {result.error}")
                    
                    # 呼叫回調函數（用於即時更新 UI）
                    if on_role_complete:
                        try:
                            on_role_complete(role_name, result)
                        except Exception as callback_error:
                            logger.error(f"Error in on_role_complete callback for {role_name}: {callback_error}")
                except Exception as e:
                    error_result = ProviderResult(
                        success=False,
                        content="",
                        error=f"API_CALL_FAILED:{str(e)}",
                        provider_name=self.ROLE_PROVIDER_MAP.get(role_name, "unknown"),
                    )
                    role_results[role_name] = error_result
                    executed_roles.append(role_name)
                    logger.error(f"Role {role_name} failed with exception: {e}", exc_info=True)
                    
                    if on_role_complete:
                        try:
                            on_role_complete(role_name, error_result)
                        except Exception as callback_error:
                            logger.error(f"Error in on_role_complete callback for {role_name}: {callback_error}")
        else:
            logger.warning("No tasks to execute!")
        
        # 詳細記錄執行結果
        logger.info(f"run_all_roles_streaming completed.")
        logger.info(f"  enabled_providers: {enabled_providers}")
        logger.info(f"  executed_roles: {executed_roles}")
        for role_name, result in role_results.items():
            status = "Success" if result.success else "Failed"
            logger.info(f"  - {role_name}: {status} (provider={result.provider_name}, error={result.error or 'None'})")
        
        return role_results
    
    async def run_all_roles(
        self,
        prompt: str,
        enabled_providers: Optional[List[str]] = None,
    ) -> Dict[str, ProviderResult]:
        """
        並行執行所有角色的分析（穩定版本，使用 asyncio.gather）
        
        Args:
            prompt: 使用者提示
            enabled_providers: 啟用的 Provider 列表（內部鍵值，例如：['gpt', 'claude']）
        
        Returns:
            角色名稱到結果的映射（只包含真正執行過的角色）
        """
        import logging
        logger = logging.getLogger("war_room.provider_manager")
        
        logger.info(f"run_all_roles called with enabled_providers: {enabled_providers}")
        
        if enabled_providers is None:
            enabled_providers = ["gpt"]
            logger.warning("enabled_providers is None, defaulting to ['gpt']")
        
        roles = list(self.ROLE_PROVIDER_MAP.keys())
        tasks = []
        role_names_to_run = []
        
        # 建立任務列表
        for role_name in roles:
            provider_key = self.ROLE_PROVIDER_MAP.get(role_name)
            if provider_key in enabled_providers:
                # 建立 coroutine（不立即 await）
                coro = self.run_role(role_name, prompt, enabled_providers)
                tasks.append(coro)
                role_names_to_run.append(role_name)
                logger.info(f"Role {role_name} (provider: {provider_key}) will be executed")
            else:
                logger.info(f"Role {role_name} (provider: {provider_key}) is not enabled, skipping")
        
        # 使用 gather 並行執行所有任務
        role_results = {}
        if tasks:
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 處理結果
                for i, result in enumerate(results):
                    role_name = role_names_to_run[i]
                    if isinstance(result, Exception):
                        logger.error(f"Role {role_name} raised exception: {result}", exc_info=True)
                        role_results[role_name] = ProviderResult(
                            success=False,
                            content="",
                            error=f"API_CALL_FAILED:{str(result)}",
                            provider_name=self.ROLE_PROVIDER_MAP.get(role_name, "unknown"),
                        )
                    else:
                        role_results[role_name] = result
                        status = "Success" if result.success else "Failed"
                        logger.info(f"Role {role_name} completed: {status}")
            except Exception as e:
                logger.error(f"run_all_roles failed with exception: {e}", exc_info=True)
                # 即使失敗，也要返回已完成的結果
        else:
            logger.warning("No tasks to execute!")
        
        # 詳細記錄執行結果
        logger.info(f"run_all_roles completed.")
        logger.info(f"  enabled_providers: {enabled_providers}")
        logger.info(f"  executed_roles: {list(role_results.keys())}")
        for role_name, result in role_results.items():
            status = "Success" if result.success else "Failed"
            logger.info(f"  - {role_name}: {status} (provider={result.provider_name}, error={result.error or 'None'})")
        
        return role_results
    
    async def run_strategist_summary(
        self,
        role_results: Dict[str, ProviderResult],
        original_question: str,
    ) -> ProviderResult:
        """
        執行 Strategist 總結
        
        Args:
            role_results: 所有角色的結果
            original_question: 原始問題
        
        Returns:
            Strategist 的總結結果
        """
        # 組合所有角色的意見
        opinions_text = []
        for role_name, result in role_results.items():
            if result.success:
                opinions_text.append(f"【{role_name}】\n{result.content}")
            else:
                opinions_text.append(f"【{role_name}】\n錯誤：{result.error}")
        
        summary_prompt = f"""
原始問題：{original_question}

以下是各角色的意見：

{chr(10).join(opinions_text)}

請你作為 Strategist，統整以上所有意見，給出最終的投資建議與結論。
"""
        
        return await self.run_role("Strategist", summary_prompt, enabled_providers=["gpt"])

