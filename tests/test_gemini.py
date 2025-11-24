import os
from google import genai
from google.genai.errors import APIError

MODEL_NAME = "gemini-2.5-flash"

def test_gemini_basic():
    api_key = os.getenv("GEMINI_API_KEY")
    assert api_key, "GEMINI_API_KEY 沒設定"

    client = genai.Client(api_key=api_key)

    try:
        resp = client.models.generate_content(
            model=MODEL_NAME,
            contents="用一句話回答：你現在是 J-GOD 股神作戰系統中的 Gemini 助理。",
        )
        assert resp.text
        print("Gemini 回覆：", resp.text)
    except APIError as e:
        raise AssertionError(f"Gemini API 錯誤：{e}")
