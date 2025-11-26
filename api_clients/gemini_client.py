from typing import Protocol
import os
import logging
from google import genai
from google.genai import types as genai_types
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
        
        # 建立專門用來產生純文字回答的 GenerativeModel
        # 設定 response_mime_type="text/plain" 並關閉 AFC（避免 token 被用在 thoughts）
        try:
            # 嘗試使用 GenerativeModel（如果 SDK 支援）
            if hasattr(genai, 'GenerativeModel'):
                self.model = genai.GenerativeModel(
                    model_name=self.fast_model_id,
                )
            else:
                # 如果沒有 GenerativeModel，使用 client.models
                self.model = None
        except Exception as e:
            # 如果 GenerativeModel 初始化失敗，fallback 到原本的方式
            logger.warning(f"[GEMINI] Failed to create GenerativeModel: {e}, using default client")
            self.model = None
    
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
                # 如果是方法或 property，嘗試呼叫
                if callable(text):
                    text = text()
                
                # 檢查是否為有效字串
                if text:
                    if isinstance(text, str):
                        if text.strip():
                            logger.debug("[GEMINI] Successfully extracted text from response.text")
                            return text.strip()
                        else:
                            logger.debug("[GEMINI] response.text is empty string")
                    else:
                        # 如果不是字串，嘗試轉換
                        text_str = str(text).strip()
                        if text_str and not text_str.startswith("<"):
                            logger.debug(f"[GEMINI] Converted response.text to string: {type(text)}")
                            return text_str
                else:
                    logger.debug(f"[GEMINI] response.text is None or falsy: {repr(text)}")
            except Exception as e:
                logger.debug(f"[GEMINI] Failed to access response.text: {e}")
                import traceback
                logger.debug(f"[GEMINI] Traceback: {traceback.format_exc()}")
        
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
                f"Response type: {type(response).__name__}, "
                f"Has text attr: {hasattr(response, 'text')}, "
                f"Has candidates attr: {hasattr(response, 'candidates')}"
            )
            
            # Gemini-special fallback：最後一層嘗試直接讀取 response.text
            if hasattr(response, "text"):
                try:
                    maybe_text = response.text
                    if callable(maybe_text):
                        maybe_text = maybe_text()
                    if isinstance(maybe_text, str) and maybe_text.strip():
                        logger.debug("[GEMINI] Successfully extracted text from response.text in fallback")
                        return maybe_text.strip()
                    elif maybe_text is not None:
                        # 如果不是字串，嘗試轉換
                        text_str = str(maybe_text).strip()
                        if text_str:
                            logger.debug(f"[GEMINI] Converted response.text to string: {type(maybe_text)}")
                            return text_str
                except Exception as e:
                    logger.exception("[GEMINI] Failed to read response.text in fallback")
            
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
            # 建立 generation_config，強制使用 text/plain
            # 使用 dict 或正確的 config 型別（避免 GenerationConfig 沒有 tools 屬性的問題）
            # 先嘗試使用 GenerateContentConfig（如果有的話），否則使用 dict
            try:
                if hasattr(genai_types, 'GenerateContentConfig'):
                    generation_config = genai_types.GenerateContentConfig(
                        response_mime_type="text/plain",  # 強制純文字輸出
                        max_output_tokens=768,  # Scout 使用較短的輸出
                        temperature=0.4,  # 保持穩定但有一點變化
                    )
                else:
                    # Fallback 到 dict（SDK 應該會自動轉換）
                    generation_config = {
                        "response_mime_type": "text/plain",
                        "max_output_tokens": 768,
                        "temperature": 0.4,
                    }
            except Exception as config_error:
                logger.debug(f"[GEMINI] Failed to create config object: {config_error}, using dict")
                generation_config = {
                    "response_mime_type": "text/plain",
                    "max_output_tokens": 768,
                    "temperature": 0.4,
                }
            
            # 優先使用設定好的 GenerativeModel（有 text/plain）
            if self.model:
                response = self.model.generate_content(
                    contents=prompt,
                    generation_config=generation_config,
                )
            else:
                # Fallback 到原本的方式，但也要設定 text/plain
                response = self.client.models.generate_content(
                    model=self.fast_model_id,
                    contents=prompt,
                    config=generation_config,
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
                        logger.warning(f"[GEMINI] response.text value: {repr(text_value)[:500]}")
                        # 如果 text_value 不是 None，嘗試直接使用
                        if text_value and isinstance(text_value, str) and text_value.strip():
                            logger.warning("[GEMINI] Using response.text directly as fallback")
                            return text_value.strip()
                    except Exception as e:
                        logger.warning(f"[GEMINI] Failed to get response.text value: {e}")
                        import traceback
                        logger.warning(f"[GEMINI] Traceback: {traceback.format_exc()}")
                
                # 檢查 candidates 結構
                if hasattr(response, "candidates"):
                    try:
                        candidates = response.candidates
                        if candidates:
                            logger.warning(f"[GEMINI] candidates count: {len(candidates) if hasattr(candidates, '__len__') else 'N/A'}")
                            if len(candidates) > 0:
                                candidate = candidates[0]
                                logger.warning(f"[GEMINI] candidate type: {type(candidate).__name__}")
                                if hasattr(candidate, "content"):
                                    content = candidate.content
                                    logger.warning(f"[GEMINI] content type: {type(content).__name__}")
                                    if hasattr(content, "parts"):
                                        parts = content.parts
                                        logger.warning(f"[GEMINI] parts: {parts}")
                except Exception as e:
                    logger.warning(f"[GEMINI] Failed to inspect candidates: {e}")
                
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
                    # Fallback 時也使用設定好的 model（如果有的話），同樣設定 text/plain
                    try:
                        if hasattr(genai_types, 'GenerateContentConfig'):
                            generation_config = genai_types.GenerateContentConfig(
                                response_mime_type="text/plain",
                                max_output_tokens=768,
                                temperature=0.4,
                            )
                        else:
                            generation_config = {
                                "response_mime_type": "text/plain",
                                "max_output_tokens": 768,
                                "temperature": 0.4,
                            }
                    except Exception:
                        generation_config = {
                            "response_mime_type": "text/plain",
                            "max_output_tokens": 768,
                            "temperature": 0.4,
                        }
                    if self.model:
                        fallback_response = self.model.generate_content(
                            contents=prompt,
                            generation_config=generation_config,
                        )
                    else:
                        fallback_response = self.client.models.generate_content(
                            model=self.fallback_model_id,
                            contents=prompt,
                            config=generation_config,
                        )
                    text = self._extract_text_from_response(fallback_response)
                    if not text or not text.strip():
                        logger.warning("[GEMINI] Extracted empty text from fallback response")
                        return ""
                    return text
                except Exception as fallback_error:
                    logger.exception("[GEMINI] Fallback generate_content failed: %s", fallback_error)
                    return ""
            logger.exception("[GEMINI] API error: %s", e)
            return ""
    
    def ask_stream(self, system_prompt: str, user_prompt: str, max_tokens: int = 512):
        """
        Streaming 版本（改為一次性取得完整結果，但仍維持 generator 介面）
        注意：google-genai SDK 不支援 stream=True，所以改為一次性取得完整結果
        使用設定好的 GenerativeModel（text/plain + 關閉 AFC）
        """
        prompt = f"{system_prompt}\n\n使用者問題：{user_prompt}"
        
        try:
            # 建立 generation_config，強制使用 text/plain
            # 使用 dict 或正確的 config 型別（避免 GenerationConfig 沒有 tools 屬性的問題）
            try:
                if hasattr(genai_types, 'GenerateContentConfig'):
                    generation_config = genai_types.GenerateContentConfig(
                        response_mime_type="text/plain",  # 強制純文字輸出
                        max_output_tokens=min(max_tokens, 768) if max_tokens else 768,
                        temperature=0.4,
                    )
                else:
                    generation_config = {
                        "response_mime_type": "text/plain",
                        "max_output_tokens": min(max_tokens, 768) if max_tokens else 768,
                        "temperature": 0.4,
                    }
            except Exception as config_error:
                logger.debug(f"[GEMINI] Failed to create config object: {config_error}, using dict")
                generation_config = {
                    "response_mime_type": "text/plain",
                    "max_output_tokens": min(max_tokens, 768) if max_tokens else 768,
                    "temperature": 0.4,
                }
            
            # 優先使用設定好的 GenerativeModel（有 text/plain）
            if self.model:
                response = self.model.generate_content(
                    contents=prompt,
                    generation_config=generation_config,
                )
            else:
                # Fallback 到原本的方式
                response = self.client.models.generate_content(
                    model=self.fast_model_id,
                    contents=prompt,
                    config=generation_config,
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
                    # Fallback 時也使用設定好的 model（如果有的話），同樣設定 text/plain
                    try:
                        if hasattr(genai_types, 'GenerateContentConfig'):
                            generation_config = genai_types.GenerateContentConfig(
                                response_mime_type="text/plain",
                                max_output_tokens=min(max_tokens, 768) if max_tokens else 768,
                                temperature=0.4,
                            )
                        else:
                            generation_config = {
                                "response_mime_type": "text/plain",
                                "max_output_tokens": min(max_tokens, 768) if max_tokens else 768,
                                "temperature": 0.4,
                            }
                    except Exception:
                        generation_config = {
                            "response_mime_type": "text/plain",
                            "max_output_tokens": min(max_tokens, 768) if max_tokens else 768,
                            "temperature": 0.4,
                        }
                    if self.model:
                        fallback_response = self.model.generate_content(
                            contents=prompt,
                            generation_config=generation_config,
                        )
                    else:
                        fallback_response = self.client.models.generate_content(
                            model=self.fallback_model_id,
                            contents=prompt,
                            config=generation_config,
                        )
                    
                    # 使用穩健的文字提取方法
                    full_text = self._extract_text_from_response(fallback_response)
                    
                    # 如果提取到文字，才 yield（空字串就不送出了）
                    if full_text and full_text.strip():
                        yield full_text
                    # 如果沒有文字，不 yield 任何東西（讓上層處理空內容）
                except Exception as fallback_error:
                    logger.exception("[GEMINI] Fallback generate_content failed: %s", fallback_error)
                    # 不 yield 任何東西，讓上層處理空內容
            else:
                logger.exception("[GEMINI] API error: %s", e)
                # 不 yield 任何東西，讓上層處理空內容
        except Exception as e:
            logger.exception("[GEMINI] generate_content failed: %s", e)
            # 不 yield 任何東西，讓上層處理空內容
