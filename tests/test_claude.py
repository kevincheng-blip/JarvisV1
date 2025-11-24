import os
from anthropic import Anthropic


CLAUDE_TEST_MODEL = "claude-3-haiku-20240307"  # 和 DEFAULT_CLAUDE_MODEL 保持一致


def test_claude_basic():
    """
    最小可行測試：確認 Anthropic API Key 有設定，且可以成功打一個簡單的 Claude 請求。
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    assert api_key, "環境變數 ANTHROPIC_API_KEY 沒有設定，請先在 .env 裡設定。"

    client = Anthropic(api_key=api_key)

    resp = client.messages.create(
        model=CLAUDE_TEST_MODEL,
        max_tokens=50,
        messages=[
            {
                "role": "user",
                "content": "hi, just say hello in one short sentence."
            }
        ],
    )

    # 確認有回傳東西
    assert resp is not None
    # Anthropic v1 messages API 會回傳一個有 content 屬性的物件
    assert hasattr(resp, "content")
    # 內容應該是非空
    assert len(resp.content) > 0

    print("Claude 回傳內容：", resp.content)


if __name__ == "__main__":
    # 方便不用 pytest 時，直接跑這個檔案手動測試
    test_claude_basic()
