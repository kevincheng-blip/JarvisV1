from dotenv import load_dotenv
import os

# 啟動時載入 .env
load_dotenv()

def get_openai_api_key() -> str:
    """
    從環境變數中讀取 OPENAI_API_KEY。
    沒設時回傳空字串，讓 main 去決定要不要用。
    """
    key = os.getenv("OPENAI_API_KEY", "")
    return key

