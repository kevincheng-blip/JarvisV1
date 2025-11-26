from typing import Protocol
import os
import logging
from google import genai
from google.genai.errors import APIError

logger = logging.getLogger("war_room")

# Fast model（優先使用，速度最快）
FAST_MODEL_ID = "gemini-1.5-flash"

# Fallback model（當 fast model 不可用時使用，原本穩定版本）
FALLBACK_MODEL_ID = "gemini-2.5-flash"


class AIProvider(Protocol):
    def ask(self, system_prompt: str, user_prompt: str) -> str:
        ...


class GeminiProvider:
    """
    使用 Google 最新版 SDK (google-genai)
    呼叫 Gemini 2.x 模型
    支援 fast model 和 fallback model 自動切換
    """

    def __init__(self, model: str = None):
        # 先嘗試 GEMINI_API_KEY，再 fallback 到 GOOGLE_API_KEY
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY 或 GOOGLE_API_KEY 沒設定")

        self.client = genai.Client(api_key=api_key)
        # 如果沒有指定 model，使用 fast model
        self.fast_model_id = model or FAST_MODEL_ID
        self.fallback_model_id = FALLBACK_MODEL_ID

    def ask(self, system_prompt: str, user_prompt: str) -> str:
        prompt = f"{system_prompt}\n\n使用者問題：{user_prompt}"

        try:
            # 先嘗試使用 fast model
            response = self.client.models.generate_content(
                model=self.fast_model_id,
                contents=prompt,
            )
            return response.text
        except APIError as e:
            # 檢查是否為 404 錯誤（檢查錯誤訊息或 status_code）
            error_str = str(e).lower()
            is_404 = (
                (hasattr(e, 'status_code') and e.status_code == 404) or
                "404" in error_str or
                "not found" in error_str
            )
            
            if is_404:
                logger.warning(
                    "[GEMINI] Fast model %s returned 404, falling back to %s",
                    self.fast_model_id,
                    self.fallback_model_id,
                )
                try:
                    fallback_response = self.client.models.generate_content(
                        model=self.fallback_model_id,
                        contents=prompt,
                    )
                    return fallback_response.text
                except Exception as fallback_error:
                    return f"[Gemini API 錯誤（fallback 也失敗）：{fallback_error}]"
            return f"[Gemini API 錯誤：{e}]"
        except Exception as e:
            return f"[Gemini 呼叫失敗：{e}]"
    
    def ask_stream(self, system_prompt: str, user_prompt: str, max_tokens: int = 512):
        """
        Streaming 版本（改為一次性取得完整結果，但仍維持 generator 介面）
        注意：google-genai SDK 不支援 stream=True，所以改為一次性取得完整結果
        支援 fast model 和 fallback model 自動切換
        """
        prompt = f"{system_prompt}\n\n使用者問題：{user_prompt}"
        
        # 使用 generation_config 優化參數以加速回應
        generation_config = {}
        if max_tokens:
            # 限制輸出長度以加速（Scout 角色使用較短的 max_tokens）
            generation_config["max_output_tokens"] = min(max_tokens, 768)
        
        try:
            # 先嘗試使用 fast model
            response = self.client.models.generate_content(
                model=self.fast_model_id,
                contents=prompt,
                config=generation_config if generation_config else None,
            )
            
            # 從 response 中萃取出完整文字
            full_text = ""
            if hasattr(response, 'text') and response.text:
                full_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                # 如果 response.text 不存在，嘗試從 candidates 中提取
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    full_text += part.text
            
            if not full_text:
                full_text = "[Gemini returned empty content]"
            
            # 一次性 yield 完整文字（維持 generator 介面）
            yield full_text
        except APIError as e:
            # 檢查是否為 404 錯誤（檢查錯誤訊息或 status_code）
            error_str = str(e).lower()
            is_404 = (
                (hasattr(e, 'status_code') and e.status_code == 404) or
                "404" in error_str or
                "not found" in error_str
            )
            
            if is_404:
                logger.warning(
                    "[GEMINI] Fast model %s returned 404, falling back to %s",
                    self.fast_model_id,
                    self.fallback_model_id,
                )
                try:
                    fallback_response = self.client.models.generate_content(
                        model=self.fallback_model_id,
                        contents=prompt,
                        config=generation_config if generation_config else None,
                    )
                    
                    # 從 fallback response 中萃取出完整文字
                    full_text = ""
                    if hasattr(fallback_response, 'text') and fallback_response.text:
                        full_text = fallback_response.text
                    elif hasattr(fallback_response, 'candidates') and fallback_response.candidates:
                        for candidate in fallback_response.candidates:
                            if hasattr(candidate, 'content') and candidate.content:
                                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                    for part in candidate.content.parts:
                                        if hasattr(part, 'text') and part.text:
                                            full_text += part.text
                    
                    if not full_text:
                        full_text = "[Gemini returned empty content]"
                    
                    yield full_text
                except Exception as fallback_error:
                    yield f"[Gemini API 錯誤（fallback 也失敗）：{fallback_error}]"
            else:
                yield f"[Gemini API 錯誤：{e}]"
        except Exception as e:
            yield f"[Gemini 呼叫失敗：{e}]"
