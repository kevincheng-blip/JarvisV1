from typing import Protocol
import os
from google import genai
from google.genai.errors import APIError


class AIProvider(Protocol):
    def ask(self, system_prompt: str, user_prompt: str) -> str:
        ...


class GeminiProvider:
    """
    使用 Google 最新版 SDK (google-genai)
    呼叫 Gemini 2.x 模型
    """

    def __init__(self, model: str = "gemini-2.5-flash"):
        # 先嘗試 GEMINI_API_KEY，再 fallback 到 GOOGLE_API_KEY
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY 或 GOOGLE_API_KEY 沒設定")

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def ask(self, system_prompt: str, user_prompt: str) -> str:
        prompt = f"{system_prompt}\n\n使用者問題：{user_prompt}"

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text
        except APIError as e:
            return f"[Gemini API 錯誤：{e}]"
        except Exception as e:
            return f"[Gemini 呼叫失敗：{e}]"
    
    def ask_stream(self, system_prompt: str, user_prompt: str, max_tokens: int = 512):
        """
        Streaming 版本（改為一次性取得完整結果，但仍維持 generator 介面）
        注意：google-genai SDK 不支援 stream=True，所以改為一次性取得完整結果
        max_tokens 參數目前不支援（google-genai SDK 限制），但保留參數以維持介面一致性
        """
        prompt = f"{system_prompt}\n\n使用者問題：{user_prompt}"
        
        try:
            # 不使用 stream 參數，一次性取得完整結果
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
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
            yield f"[Gemini API 錯誤：{e}]"
        except Exception as e:
            yield f"[Gemini 呼叫失敗：{e}]"
