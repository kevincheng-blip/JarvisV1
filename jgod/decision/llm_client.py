"""
Decision Layer v1 - LLM Client

封裝 LLM 呼叫（可重用現有 client 或實作簡單版本）
"""

import json
import logging
import time
from typing import Protocol, Optional

from jgod.decision.config import DecisionConfig
from jgod.decision.models import LlmDecisionResponse

logger = logging.getLogger(__name__)


class DecisionLlmClient(Protocol):
    """LLM Client 介面（Protocol）"""
    def ask(self, prompt: str, model: str, timeout: int = 30) -> str:
        """呼叫 LLM 並回傳回應"""
        ...


class SimpleOpenAIClient:
    """簡單的 OpenAI Client 封裝
    
    注意：如果專案中已有 openai_client，應該重用該模組
    這裡提供一個簡單的實作作為 fallback
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        try:
            import openai
            self.openai = openai
            if api_key:
                self.openai.api_key = api_key
        except ImportError:
            logger.warning("OpenAI library not installed. LLM features will be disabled.")
            self.openai = None
    
    def ask(self, prompt: str, model: str = "gpt-4o-mini", timeout: int = 30) -> str:
        """呼叫 OpenAI API"""
        if not self.openai:
            raise RuntimeError("OpenAI library not available")
        
        try:
            # 嘗試使用新版 OpenAI API (v1.0+)
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a financial analysis assistant."},
                    {"role": "user", "content": prompt}
                ],
                timeout=timeout,
                temperature=0.3,  # 降低隨機性，提高穩定性
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise


class DecisionLlmWrapper:
    """Decision Layer LLM Wrapper
    
    封裝 LLM 呼叫，包含 retry 邏輯和錯誤處理
    """
    
    def __init__(self, config: DecisionConfig, client: Optional[DecisionLlmClient] = None):
        self.config = config
        self.client = client
        if not self.client:
            # 預設使用 SimpleOpenAIClient（需要環境變數 OPENAI_API_KEY）
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = SimpleOpenAIClient(api_key=api_key)
            else:
                logger.warning("No OpenAI API key found. LLM features will be disabled.")
                self.client = None
    
    def call_llm(self, prompt: str) -> Optional[LlmDecisionResponse]:
        """呼叫 LLM 並解析回應
        
        Returns:
            LlmDecisionResponse 或 None（失敗時）
        """
        if not self.client or not self.config.enable_llm:
            logger.info("LLM disabled or client not available, using fallback")
            return None
        
        last_error = None
        for attempt in range(self.config.llm_max_retries + 1):
            try:
                response_text = self.client.ask(
                    prompt=prompt,
                    model=self.config.llm_model,
                    timeout=self.config.llm_timeout
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

