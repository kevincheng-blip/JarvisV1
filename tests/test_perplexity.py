import os
import sys
import pathlib

# 確保專案根目錄在 sys.path 裡
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api_clients.perplexity_client import PerplexityProvider


def test_perplexity_basic():
    """
    最小可行測試：確認 PERPLEXITY_API_KEY 有設定，且可以成功打一個簡單的 Perplexity 請求。
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    assert api_key, "環境變數 PERPLEXITY_API_KEY 沒有設定，請先在 .env 裡設定。"

    provider = PerplexityProvider()

    reply = provider.ask(
        system_prompt="你是 J-GOD 股神作戰系統中的情報官，擅長搜尋與整理最新市場資訊。",
        user_prompt="請用一句很短的話做自我介紹。",
    )

    assert reply is not None
    assert isinstance(reply, str)
    assert len(reply) > 0

    print("Perplexity 回傳內容：", reply)


if __name__ == "__main__":
    test_perplexity_basic()
