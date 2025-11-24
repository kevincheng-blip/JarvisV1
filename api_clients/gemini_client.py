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
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY 沒設定")

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
