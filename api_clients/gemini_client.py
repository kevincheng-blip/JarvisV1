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
    
    def ask_stream(self, system_prompt: str, user_prompt: str):
        """
        Streaming 版本（真正的 token-level streaming）
        """
        prompt = f"{system_prompt}\n\n使用者問題：{user_prompt}"
        
        try:
            # 使用 stream=True 啟用 streaming
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                stream=True,
            )
            
            # 逐個 chunk 輸出
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except APIError as e:
            yield f"[Gemini API 錯誤：{e}]"
        except Exception as e:
            yield f"[Gemini 呼叫失敗：{e}]"
