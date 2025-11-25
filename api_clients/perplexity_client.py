from typing import Protocol
import os
import requests


class AIProvider(Protocol):
    def ask(self, system_prompt: str, user_prompt: str) -> str:
        ...


class PerplexityProvider:
    """
    戰情室的 Perplexity AI Provider
    使用 PERPLEXITY_API_KEY 呼叫 Perplexity Chat Completions API
    """

    def __init__(self, model: str | None = None):
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise RuntimeError("PERPLEXITY_API_KEY 沒設定（請檢查 .env）")

        # 從環境變數讀取 model，預設為 "sonar"
        env_model = os.getenv("PERPLEXITY_MODEL")
        if model is None:
            model = env_model or "sonar"

        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.perplexity.ai/chat/completions"

        # Debug 用：印出目前實際用的 model
        print(f"[Perplexity] using model: {self.model}")

    def ask(self, system_prompt: str, user_prompt: str) -> str:
        """
        使用 Perplexity 進行回答，與 tests/test_perplexity.py 的結構一致。
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
        }

        resp = None
        try:
            resp = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
        except Exception as e:
            # 把伺服器真正回的錯誤訊息一起帶出來
            detail = None
            try:
                if resp is not None:
                    detail = resp.text
            except Exception:
                pass
            raise RuntimeError(f"Perplexity API call failed: {e}, detail={detail}") from e

        try:
            data = resp.json()
            # OpenAI 相容格式：choices[0].message.content
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Perplexity 回傳內容解析失敗：{e}") from e
    
    def ask_stream(self, system_prompt: str, user_prompt: str):
        """
        Streaming 版本（模擬 SSE 分段流式）
        Perplexity 目前不支援真正的 streaming，我們模擬逐句輸出
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,  # 啟用 streaming（如果 API 支援）
        }
        
        try:
            resp = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=60,
                stream=True,  # 啟用 streaming
            )
            resp.raise_for_status()
            
            # 嘗試解析 SSE 格式
            for line in resp.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            import json
                            data = json.loads(line_str[6:])
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                        except Exception:
                            continue
        except Exception as e:
            # 如果 streaming 失敗，回退到非 streaming 模式
            result = self.ask(system_prompt, user_prompt)
            # 模擬分段輸出（每句一段）
            sentences = result.split('。')
            for sentence in sentences:
                if sentence.strip():
                    yield sentence.strip() + '。'
                    import time
                    time.sleep(0.1)  # 模擬延遲