"""
系統健康檢查
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

from api_clients.openai_client import GPTProvider
from api_clients.anthropic_client import ClaudeProvider
from api_clients.gemini_client import GeminiProvider
from api_clients.perplexity_client import PerplexityProvider
from api_clients.finmind_client import FinMindClient


@dataclass
class ProviderHealth:
    """Provider 健康狀態"""
    name: str
    ok: bool
    error: Optional[str] = None


class HealthChecker:
    """
    系統健康檢查器
    
    功能：
    - 檢查環境變數
    - 檢查 Provider 連線狀態
    """
    
    REQUIRED_ENV_VARS = {
        "openai": "OPENAI_API_KEY",
        "claude": "ANTHROPIC_API_KEY",
        "gemini": "GOOGLE_API_KEY",
        "perplexity": "PERPLEXITY_API_KEY",
        "finmind": "FINMIND_TOKEN",
    }
    
    def __init__(self):
        """初始化健康檢查器"""
        pass
    
    def check_env_var(self, provider: str) -> bool:
        """
        檢查環境變數是否存在
        
        Args:
            provider: Provider 名稱
        
        Returns:
            True 表示環境變數存在
        """
        env_var = self.REQUIRED_ENV_VARS.get(provider)
        if not env_var:
            return False
        
        value = os.getenv(env_var)
        return value is not None and value.strip() != ""
    
    def check_openai(self) -> ProviderHealth:
        """檢查 OpenAI Provider"""
        if not self.check_env_var("openai"):
            return ProviderHealth(
                name="OpenAI",
                ok=False,
                error="OPENAI_API_KEY 未設定",
            )
        
        try:
            provider = GPTProvider()
            # 簡單的 health ping
            result = provider.ask(
                system_prompt="你是一個測試助手。",
                user_prompt="請回覆 'OK'",
            )
            if result:
                return ProviderHealth(name="OpenAI", ok=True)
            else:
                return ProviderHealth(
                    name="OpenAI",
                    ok=False,
                    error="API 回傳空結果",
                )
        except Exception as e:
            return ProviderHealth(
                name="OpenAI",
                ok=False,
                error=str(e)[:100],  # 限制錯誤訊息長度
            )
    
    def check_claude(self) -> ProviderHealth:
        """檢查 Claude Provider"""
        if not self.check_env_var("claude"):
            return ProviderHealth(
                name="Claude",
                ok=False,
                error="ANTHROPIC_API_KEY 未設定",
            )
        
        try:
            provider = ClaudeProvider()
            result = provider.ask(
                system_prompt="你是一個測試助手。",
                user_prompt="請回覆 'OK'",
            )
            if result:
                return ProviderHealth(name="Claude", ok=True)
            else:
                return ProviderHealth(
                    name="Claude",
                    ok=False,
                    error="API 回傳空結果",
                )
        except Exception as e:
            return ProviderHealth(
                name="Claude",
                ok=False,
                error=str(e)[:100],
            )
    
    def check_gemini(self) -> ProviderHealth:
        """檢查 Gemini Provider"""
        if not self.check_env_var("gemini"):
            return ProviderHealth(
                name="Gemini",
                ok=False,
                error="GOOGLE_API_KEY 未設定",
            )
        
        try:
            provider = GeminiProvider()
            result = provider.ask(
                system_prompt="你是一個測試助手。",
                user_prompt="請回覆 'OK'",
            )
            if result:
                return ProviderHealth(name="Gemini", ok=True)
            else:
                return ProviderHealth(
                    name="Gemini",
                    ok=False,
                    error="API 回傳空結果",
                )
        except Exception as e:
            return ProviderHealth(
                name="Gemini",
                ok=False,
                error=str(e)[:100],
            )
    
    def check_perplexity(self) -> ProviderHealth:
        """檢查 Perplexity Provider"""
        if not self.check_env_var("perplexity"):
            return ProviderHealth(
                name="Perplexity",
                ok=False,
                error="PERPLEXITY_API_KEY 未設定",
            )
        
        try:
            provider = PerplexityProvider()
            result = provider.ask(
                system_prompt="你是一個測試助手。",
                user_prompt="請回覆 'OK'",
            )
            if result:
                return ProviderHealth(name="Perplexity", ok=True)
            else:
                return ProviderHealth(
                    name="Perplexity",
                    ok=False,
                    error="API 回傳空結果",
                )
        except Exception as e:
            return ProviderHealth(
                name="Perplexity",
                ok=False,
                error=str(e)[:100],
            )
    
    def check_finmind(self) -> ProviderHealth:
        """檢查 FinMind Provider"""
        if not self.check_env_var("finmind"):
            return ProviderHealth(
                name="FinMind",
                ok=False,
                error="FINMIND_TOKEN 未設定",
            )
        
        try:
            client = FinMindClient()
            # 簡單測試：查詢台積電最近一筆資料
            result = client.get_stock_daily(
                stock_id="2330",
                start_date="2024-01-01",
                end_date="2024-01-02",
            )
            if result is not None:
                return ProviderHealth(name="FinMind", ok=True)
            else:
                return ProviderHealth(
                    name="FinMind",
                    ok=False,
                    error="API 回傳空結果",
                )
        except Exception as e:
            return ProviderHealth(
                name="FinMind",
                ok=False,
                error=str(e)[:100],
            )
    
    def check_all(self) -> Dict[str, ProviderHealth]:
        """
        檢查所有 Provider
        
        Returns:
            Provider 名稱到健康狀態的映射
        """
        return {
            "openai": self.check_openai(),
            "claude": self.check_claude(),
            "gemini": self.check_gemini(),
            "perplexity": self.check_perplexity(),
            "finmind": self.check_finmind(),
        }


def check_all_providers() -> Dict[str, ProviderHealth]:
    """
    快速檢查所有 Provider（便利函式）
    
    Returns:
        Provider 健康狀態字典
    """
    checker = HealthChecker()
    return checker.check_all()


if __name__ == "__main__":
    # CLI 測試
    checker = HealthChecker()
    results = checker.check_all()
    
    print("=== 系統健康檢查 ===\n")
    for name, health in results.items():
        status = "✅ OK" if health.ok else f"❌ 失敗: {health.error}"
        print(f"{health.name}: {status}")

