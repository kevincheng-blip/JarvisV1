"""
Role Manager：管理角色與 Provider 的映射和執行
"""
from typing import Dict, List, Optional, Callable
import logging

from jgod.war_room.providers.base_provider import BaseProviderAsync, ProviderResult
from jgod.war_room.core.async_dispatcher import AsyncDispatcher


class RoleManager:
    """角色管理器：統一管理所有角色的執行"""
    
    # 角色到 Provider 的映射
    ROLE_PROVIDER_MAP = {
        "Intel Officer": "perplexity",
        "Scout": "gemini",
        "Risk Officer": "claude",
        "Quant Lead": "claude",
        "Strategist": "gpt",
        "Execution Officer": "gpt",
    }
    
    # 角色系統提示
    ROLE_SYSTEM_PROMPTS = {
        "Intel Officer": "你是 J-GOD 戰情室的情報官（Intel Officer），負責蒐集與整理市場資訊。",
        "Scout": "你是 J-GOD 戰情室的偵察兵（Scout），負責快速摘要與輔助分析。",
        "Risk Officer": "你是 J-GOD 戰情室的風險官（Risk Officer），負責評估風險與提供風險建議。",
        "Quant Lead": "你是 J-GOD 戰情室的量化主管（Quant Lead），負責技術分析與量化策略。",
        "Strategist": "你是 J-GOD 戰情室的策略師（Strategist），負責統整所有意見並給出最終建議。",
    }
    
    def __init__(self, providers: Dict[str, BaseProviderAsync]):
        """
        初始化角色管理器
        
        Args:
            providers: Provider 字典 {provider_key: provider_instance}
        """
        self.providers = providers
        self.dispatcher = AsyncDispatcher()
        self.logger = logging.getLogger("war_room.role_manager")
    
    async def run_all_roles_streaming(
        self,
        prompt: str,
        enabled_providers: List[str],
        on_role_complete: Optional[Callable[[str, ProviderResult], None]] = None,
        on_chunk: Optional[Callable[[str, str], None]] = None,
    ) -> Dict[str, ProviderResult]:
        """
        並行執行所有啟用的角色（使用 streaming）
        
        Args:
            prompt: 使用者提示
            enabled_providers: 啟用的 Provider 列表（內部鍵值）
            on_role_complete: 每當一個角色完成時的回調 (role_name, result) -> None
            on_chunk: 每收到一個 chunk 時的回調 (role_name, chunk) -> None
        
        Returns:
            角色名稱到結果的映射
        """
        self.logger.info(f"run_all_roles_streaming called with enabled_providers: {enabled_providers}")
        
        # 建立角色任務字典
        role_tasks = {}
        # 預先收集的錯誤結果（用於 Provider 未初始化的情況）
        pre_error_results = {}
        
        for role_name, provider_key in self.ROLE_PROVIDER_MAP.items():
            # 檢查此角色的 Provider 是否啟用
            if provider_key not in enabled_providers:
                self.logger.info(f"Role {role_name} (provider: {provider_key}) is not enabled, skipping")
                continue
            
            # 取得 Provider
            provider = self.providers.get(provider_key)
            if not provider:
                # Provider 未初始化
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
                    error_result = ProviderResult(
                        success=False,
                        content="",
                        error=f"API_KEY_MISSING:{env_names} 未設定",
                        provider_name=provider_key,
                    )
                else:
                    error_result = ProviderResult(
                        success=False,
                        content="",
                        error=f"NOT_FOUND:Provider {provider_key} 不存在或未初始化",
                        provider_name=provider_key,
                    )
                
                # 將錯誤結果加入預先收集的結果中
                pre_error_results[role_name] = error_result
                self.logger.warning(f"Role {role_name} (provider: {provider_key}) cannot be executed: {error_result.error}")
                
                # 呼叫回調（如果有的話）
                if on_role_complete:
                    try:
                        on_role_complete(role_name, error_result)
                    except Exception as callback_error:
                        self.logger.error(f"Error in on_role_complete callback for {role_name}: {callback_error}")
                continue
            
            # 取得系統提示
            system_prompt = self.ROLE_SYSTEM_PROMPTS.get(role_name, "你是一個專業的股市分析師。")
            
            # 建立 streaming 任務
            async def create_role_task(rn, prov, sys_prompt, user_prompt):
                """建立角色任務（閉包捕獲變數）"""
                def chunk_callback(chunk: str):
                    if on_chunk:
                        try:
                            on_chunk(rn, chunk)
                        except Exception as e:
                            self.logger.error(f"Error in on_chunk callback for {rn}: {e}")
                
                try:
                    result = await self.dispatcher.dispatch_with_streaming(
                        role_name=rn,
                        provider=prov,
                        prompt=user_prompt,
                        system_prompt=sys_prompt,
                        on_chunk=chunk_callback,
                    )
                    self.logger.info(f"Role {rn} task completed: success={result.success}")
                    return result
                except Exception as e:
                    self.logger.error(f"Role {rn} task failed with exception: {e}", exc_info=True)
                    return ProviderResult(
                        success=False,
                        content="",
                        error=f"API_CALL_FAILED:{str(e)}",
                        provider_name=getattr(prov, 'provider_name', 'unknown'),
                    )
            
            role_tasks[role_name] = create_role_task(role_name, provider, system_prompt, prompt)
            self.logger.info(f"Role {role_name} (provider: {provider_key}) will be executed")
        
        # 合併預先收集的錯誤結果和實際執行的結果
        all_results = pre_error_results.copy()
        
        if role_tasks:
            # 使用 dispatcher 執行所有任務
            execution_results = await self.dispatcher.dispatch_all_roles_streaming(
                role_tasks,
                on_role_complete=on_role_complete,
            )
            # 合併執行結果
            all_results.update(execution_results)
        else:
            self.logger.warning("No role tasks created! Only pre-error results available.")
        
        # 詳細記錄最終結果
        self.logger.info(f"RoleManager.run_all_roles_streaming completed.")
        self.logger.info(f"  enabled_providers: {enabled_providers}")
        self.logger.info(f"  executed_roles: {list(all_results.keys())}")
        for role_name, result in all_results.items():
            status = "Success" if result.success else "Failed"
            self.logger.info(f"  - {role_name}: {status} (provider={result.provider_name}, error={result.error or 'None'})")
        
        return all_results

