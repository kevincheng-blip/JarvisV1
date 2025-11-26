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
        if hasattr(response, "text"):
            try:
                text = response.text
                if text and isinstance(text, str) and text.strip():
                    return text.strip()
                # 如果 text 是方法，嘗試呼叫
                if callable(text):
                    text = text()
                    if text and isinstance(text, str) and text.strip():
                        return text.strip()
            except Exception as e:
                logger.debug(f"[GEMINI] Failed to access response.text: {e}")
        
        # 2) 退而求其次：從 candidates / content / parts 裡面找 text
        text_parts = []
        
        # 取得 candidates（可能是屬性或方法）
        candidates = None
        try:
            if hasattr(response, "candidates"):
                candidates = response.candidates
                # 如果是方法，嘗試呼叫
                if callable(candidates):
                    candidates = candidates()
        except Exception as e:
            logger.debug(f"[GEMINI] Failed to access response.candidates: {e}")
        
        # 如果 candidates 是 None 或空，嘗試其他方式
        if not candidates:
            # 嘗試直接檢查 response 的屬性
            if hasattr(response, "__dict__"):
                logger.debug(f"[GEMINI] Response attributes: {list(response.__dict__.keys())}")
            # 嘗試檢查是否有其他文字欄位
            for attr_name in ["content", "result", "output"]:
                if hasattr(response, attr_name):
                    attr_value = getattr(response, attr_name)
                    if isinstance(attr_value, str) and attr_value.strip():
                        return attr_value.strip()
        
        # 遍歷所有 candidates
        if candidates:
            try:
                # 確保 candidates 是可迭代的
                if not hasattr(candidates, "__iter__"):
                    candidates = [candidates]
                
                for candidate in candidates:
                    # 取得 content
                    content = None
                    try:
                        if hasattr(candidate, "content"):
                            content = candidate.content
                            if callable(content):
                                content = content()
                        elif isinstance(candidate, dict):
                            content = candidate.get("content")
                    except Exception as e:
                        logger.debug(f"[GEMINI] Failed to access candidate.content: {e}")
                        continue
                    
                    if not content:
                        continue
                    
                    # 取得 parts
                    parts = None
                    try:
                        if hasattr(content, "parts"):
                            parts = content.parts
                            if callable(parts):
                                parts = parts()
                        elif isinstance(content, dict):
                            parts = content.get("parts", [])
                    except Exception as e:
                        logger.debug(f"[GEMINI] Failed to access content.parts: {e}")
                        continue
                    
                    if not parts:
                        # 如果沒有 parts，嘗試直接從 content 取得文字
                        if hasattr(content, "text"):
                            part_text = content.text
                            if callable(part_text):
                                part_text = part_text()
                            if isinstance(part_text, str) and part_text.strip():
                                text_parts.append(part_text.strip())
                        continue
                    
                    # 確保 parts 是可迭代的
                    if not hasattr(parts, "__iter__"):
                        parts = [parts]
                    
                    # 遍歷所有 parts，提取文字
                    for part in parts:
                        part_text = None
                        try:
                            if hasattr(part, "text"):
                                part_text = part.text
                                if callable(part_text):
                                    part_text = part_text()
                            elif isinstance(part, dict):
                                part_text = part.get("text")
                            elif isinstance(part, str):
                                part_text = part
                            
                            if isinstance(part_text, str) and part_text.strip():
                                text_parts.append(part_text.strip())
                        except Exception as e:
                            logger.debug(f"[GEMINI] Failed to extract text from part: {e}")
                            continue
            except Exception as e:
                logger.debug(f"[GEMINI] Error iterating candidates: {e}")
        
        # 組合所有文字部分
        full_text = "\n".join(text_parts).strip()
        
        if not full_text:
            # 加入更詳細的 debug log
            logger.warning(
                "[GEMINI] Response parsed but no text content extracted. "
                f"Response type: {type(response)}, "
                f"Has text attr: {hasattr(response, 'text')}, "
                f"Has candidates attr: {hasattr(response, 'candidates')}"
            )
            # 嘗試直接轉換 response 為字串（最後手段）
            try:
                response_str = str(response)
                if response_str and response_str.strip() and not response_str.startswith("<"):
                    logger.debug(f"[GEMINI] Using response string representation: {response_str[:100]}")
                    return response_str.strip()
            except Exception:
                pass
        
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
                # 加入更詳細的 debug 資訊
                logger.warning(
                    f"[GEMINI] Extracted empty text from response. "
                    f"Response type: {type(response).__name__}, "
                    f"Has text attr: {hasattr(response, 'text')}"
                )
                # 嘗試直接檢查 response.text 的值
                if hasattr(response, "text"):
                    try:
                        text_value = response.text
                        if callable(text_value):
                            text_value = text_value()
                        logger.warning(f"[GEMINI] response.text value: {repr(text_value)[:200]}")
                    except Exception as e:
                        logger.warning(f"[GEMINI] Failed to get response.text value: {e}")
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
