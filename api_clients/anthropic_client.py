from typing import Protocol
import os
import anthropic


class AIProvider(Protocol):
    def ask(self, system_prompt: str, user_prompt: str) -> str:
        ...


DEFAULT_CLAUDE_MODEL = "claude-3-haiku-20240307"


class ClaudeProvider:
    """
    戰情室的 Claude AI Provider
    使用你的 ANTHROPIC_API_KEY 來呼叫 Claude 模型
    """

    def __init__(self, model: str = DEFAULT_CLAUDE_MODEL):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY 沒設定（請檢查你的 .env）")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def ask(self, system_prompt: str, user_prompt: str) -> str:
        """
        使用 Claude 進行回答
        """
        try:
            msg = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            # Claude 回傳的是一個「list of content blocks」
            # 這裡取第一個 block 的文字
            return msg.content[0].text
        except Exception as e:
            # 先簡單回傳錯誤字串，之後可加入 logging
            return f"[Claude 發生錯誤：{e}]"
    
    def ask_stream(self, system_prompt: str, user_prompt: str):
        """
        Streaming 版本
        """
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=512,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"[Claude 發生錯誤：{e}]"