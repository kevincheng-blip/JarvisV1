from typing import Protocol
import os
import logging
from google import genai
from google.genai.errors import APIError

logger = logging.getLogger("war_room")

# 使用 gemini-2.5-flash 作為主要與備援模型，避免 1.5-flash 404 噴 log
FAST_MODEL_ID = "gemini-2.5-flash"
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
    
    def _extract_text_from_response(self, response) -> str:
        """
        從 Gemini API response 中穩健地提取文字內容
        
        Args:
            response: Google Gemini API 的回應物件
            
        Returns:
            提取的文字內容，如果沒有文字則返回空字串
        """
        # 1) 優先使用 .text（若為 google-genai 官方物件）
        if hasattr(response, "text") and response.text:
            text = response.text
            if isinstance(text, str) and text.strip():
                return text.strip()
        
        # 2) 退而求其次：從 candidates / content / parts 裡面找 text
        text_parts = []
        
        # 取得 candidates（可能是屬性或方法）
        candidates = None
        if hasattr(response, "candidates"):
            candidates = response.candidates
        elif hasattr(response, "get") and callable(getattr(response, "get")):
            candidates = response.get("candidates", [])
        
        # 遍歷所有 candidates
        if candidates:
            for candidate in candidates:
                # 取得 content
                content = None
                if hasattr(candidate, "content"):
                    content = candidate.content
                elif isinstance(candidate, dict):
                    content = candidate.get("content")
                
                if not content:
                    continue
                
                # 取得 parts
                parts = None
                if hasattr(content, "parts"):
                    parts = content.parts
                elif isinstance(content, dict):
                    parts = content.get("parts", [])
                elif hasattr(content, "get") and callable(getattr(content, "get")):
                    parts = content.get("parts", [])
                
                if not parts:
                    continue
                
                # 遍歷所有 parts，提取文字
                for part in parts:
                    part_text = None
                    if hasattr(part, "text"):
                        part_text = part.text
                    elif isinstance(part, dict):
                        part_text = part.get("text")
                    
                    if isinstance(part_text, str) and part_text.strip():
                        text_parts.append(part_text.strip())
        
        # 組合所有文字部分
        full_text = "\n".join(text_parts).strip()
        
        if not full_text:
            logger.warning("[GEMINI] Response parsed but no text content extracted")
        
        return full_text

    def ask(self, system_prompt: str, user_prompt: str) -> str:
        prompt = f"{system_prompt}\n\n使用者問題：{user_prompt}"

        try:
            # 先嘗試使用 fast model
            response = self.client.models.generate_content(
                model=self.fast_model_id,
                contents=prompt,
            )
            # 使用穩健的文字提取方法
            text = self._extract_text_from_response(response)
            # 為了避免前端看到空內容，這裡做一層防禦
            if not text or not text.strip():
                logger.warning("[GEMINI] Extracted empty text from response")
                return ""
            return text
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
                    text = self._extract_text_from_response(fallback_response)
                    if not text or not text.strip():
                        logger.warning("[GEMINI] Extracted empty text from fallback response")
                        return ""
                    return text
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
            
            # 使用穩健的文字提取方法
            full_text = self._extract_text_from_response(response)
            
            # 如果提取到文字，才 yield（空字串就不送出了）
            if full_text and full_text.strip():
                yield full_text
            # 如果沒有文字，不 yield 任何東西（讓上層處理空內容）
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
                    
                    # 使用穩健的文字提取方法
                    full_text = self._extract_text_from_response(fallback_response)
                    
                    # 如果提取到文字，才 yield（空字串就不送出了）
                    if full_text and full_text.strip():
                        yield full_text
                    # 如果沒有文字，不 yield 任何東西（讓上層處理空內容）
                except Exception as fallback_error:
                    yield f"[Gemini API 錯誤（fallback 也失敗）：{fallback_error}]"
            else:
                yield f"[Gemini API 錯誤：{e}]"
        except Exception as e:
            yield f"[Gemini 呼叫失敗：{e}]"
