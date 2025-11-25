"""
後端配置
"""
import os
from pathlib import Path

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 載入環境變數
from jgod.config.env_loader import load_env
load_env()

# API 設定
API_HOST = os.getenv("WAR_ROOM_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("WAR_ROOM_API_PORT", "8000"))

# WebSocket 設定
WS_HEARTBEAT_INTERVAL = 30  # 秒

# Logging 設定
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

