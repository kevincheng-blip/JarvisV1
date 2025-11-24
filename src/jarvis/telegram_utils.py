import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
CHAT_ID_PATH = BASE_DIR / "telegram_chat_id.txt"


class TelegramNotConfiguredError(RuntimeError):
    pass


def get_telegram_bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise TelegramNotConfiguredError(
            "找不到 TELEGRAM_BOT_TOKEN，請先在 .env 裡設定：\n"
            "TELEGRAM_BOT_TOKEN=從 BotFather 拿到的 token"
        )
    return token


def get_telegram_chat_id() -> str:
    if not CHAT_ID_PATH.exists():
        raise TelegramNotConfiguredError(
            "找不到 telegram_chat_id.txt，請先在 Telegram 對 Bot 送出一次 /start，讓 Jarvis 記錄 chat_id。"
        )
    chat_id = CHAT_ID_PATH.read_text(encoding="utf-8").strip()
    if not chat_id:
        raise TelegramNotConfiguredError(
            "telegram_chat_id.txt 是空的，請刪除後重新在 Telegram 使用 /start。"
        )
    return chat_id


def send_telegram_message(text: str):
    """
    從 CLI 發送訊息到你自己的 Telegram Bot chat。
    """
    token = get_telegram_bot_token()
    chat_id = get_telegram_chat_id()

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": text,
        },
        timeout=5,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Telegram 回傳錯誤：{resp.status_code} {resp.text}")

