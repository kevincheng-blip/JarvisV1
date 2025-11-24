# config/env_loader.py
from dotenv import load_dotenv

def load_env():
    """
    載入 .env 的所有環境變數
    """
    load_dotenv()
