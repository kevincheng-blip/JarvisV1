from typing import Protocol, Generator
from openai import OpenAI
import os


class AIProvider(Protocol):
    def ask(self, system_prompt: str, user_prompt: str) -> str:
        ...


class GPTProvider:
    """
    OpenAI GPT Provider with fallback error handling.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        # ✅ 正確初始化
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")  # 從環境變數讀取，更安全
        )
        self.model = model

    def ask(self, system_prompt: str, user_prompt: str) -> str:
        """一般一次性 completion"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=512,
            )
            return response.choices[0].message.content

        except Exception as e:
            return f"[GPT Error: {str(e)}]"

    def ask_stream(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Generator[str, None, None]:
        """Streaming 版本"""
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=512,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content

        except Exception as e:
            yield f"[GPT Error: {str(e)}]"
