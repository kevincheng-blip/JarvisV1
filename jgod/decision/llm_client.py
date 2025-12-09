"""
Decision Layer v1 - LLM Client

封裝 LLM 呼叫（重用現有 API clients）
"""

import json
import logging
import time
from typing import Optional

from jgod.decision.config import DecisionConfig
from jgod.decision.models import LlmDecisionResponse

logger = logging.getLogger(__name__)


def _get_provider(model_name: str):
    """根據模型名稱取得對應的 Provider
    
    Args:
        model_name: 模型名稱（例如 "gpt-4o-mini", "gemini-2.5-flash"）
    
    Returns:
        Provider 實例（GPTProvider, GeminiProvider 等）
    """
    model_lower = model_name.lower()
    
    # OpenAI / GPT 模型
    if "gpt" in model_lower or "openai" in model_lower:
        try:
            from api_clients.openai_client import GPTProvider
            return GPTProvider(model=model_name)
        except ImportError:
            logger.warning("OpenAI client not available")
            return None
    
    # Gemini 模型
    elif "gemini" in model_lower:
        try:
            from api_clients.gemini_client import GeminiProvider
            return GeminiProvider(model=model_name)
        except ImportError:
            logger.warning("Gemini client not available")
            return None
    
    # Claude 模型
    elif "claude" in model_lower:
        try:
            from api_clients.anthropic_client import ClaudeProvider
            return ClaudeProvider()
        except ImportError:
            logger.warning("Claude client not available")
            return None
    
    else:
        # 預設使用 GPT
        logger.warning(f"Unknown model {model_name}, falling back to GPT")
        try:
            from api_clients.openai_client import GPTProvider
            return GPTProvider(model="gpt-4o-mini")
        except ImportError:
            return None


class DecisionLlmWrapper:
    """Decision Layer LLM Wrapper
    
    封裝 LLM 呼叫，包含 retry 邏輯和錯誤處理
    重用現有的 API clients (GPTProvider, GeminiProvider 等)
    """
    
    def __init__(self, config: DecisionConfig, provider=None):
        """
        Args:
            config: DecisionConfig 配置
            provider: 可選的 Provider 實例（如果不提供，會根據 config.llm_model 自動選擇）
        """
        self.config = config
        self.provider = provider
        
        if not self.provider:
            # 根據配置的模型名稱自動選擇 Provider
            self.provider = _get_provider(config.llm_model)
            
            if not self.provider:
                logger.warning(f"Could not initialize provider for model {config.llm_model}. LLM features will be disabled.")
    
    def call_llm(self, prompt: str) -> Optional[LlmDecisionResponse]:
        """呼叫 LLM 並解析回應
        
        Args:
            prompt: 完整的 Prompt 字串（包含 system + user content）
        
        Returns:
            LlmDecisionResponse 或 None（失敗時）
        """
        if not self.provider or not self.config.enable_llm:
            logger.info("LLM disabled or provider not available, using fallback")
            return None
        
        # 將完整 prompt 分為 system 和 user 部分
        # 簡單策略：如果 prompt 包含 "=== 輸入資料 ==="，之前的是 system，之後的是 user
        if "=== 輸入資料 ===" in prompt:
            parts = prompt.split("=== 輸入資料 ===", 1)
            system_prompt = parts[0].strip()
            user_prompt = "=== 輸入資料 ===" + parts[1] if len(parts) > 1 else prompt
        else:
            # 如果沒有明確分隔，全部當作 user prompt
            system_prompt = "You are a financial analysis assistant."
            user_prompt = prompt
        
        last_error = None
        for attempt in range(self.config.llm_max_retries + 1):
            try:
                # 使用 Provider 的 ask 方法（統一介面：system_prompt, user_prompt）
                response_text = self.provider.ask(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt
                )
                
                # 解析 JSON 回應
                return self._parse_response(response_text)
            
            except Exception as e:
                last_error = e
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt < self.config.llm_max_retries:
                    time.sleep(1)  # 簡單的 backoff
        
        # 所有重試都失敗
        logger.error(f"LLM call failed after {self.config.llm_max_retries + 1} attempts: {last_error}")
        return None
    
    def _parse_response(self, response_text: str) -> Optional[LlmDecisionResponse]:
        """解析 LLM 回應為 LlmDecisionResponse
        
        嘗試從回應中提取 JSON，並處理各種格式
        """
        try:
            # 嘗試直接解析 JSON
            response_json = json.loads(response_text)
        except json.JSONDecodeError:
            # 嘗試從 Markdown code block 中提取
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    response_json = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON from LLM response: {response_text[:200]}")
                    return None
            else:
                logger.error(f"No JSON found in LLM response: {response_text[:200]}")
                return None
        
        # 驗證必要欄位
        if "correction_factor" not in response_json:
            logger.error("LLM response missing 'correction_factor'")
            return None
        
        return LlmDecisionResponse(
            correction_factor=float(response_json.get("correction_factor", 1.0)),
            doctrine_flags=response_json.get("doctrine_flags", []),
            adjustment_reason=response_json.get("adjustment_reason", "")
        )

