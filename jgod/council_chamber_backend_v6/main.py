"""
AI Council Chamber Backend v6.0 - FastAPI 啟動器
專為 Next.js 前端設計的幕僚會議室後端
"""
import logging
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

jgod.council_chamber.providers import ProviderManager
jgod.council_chamber_v6.core.engine_v6 import WarRoomEngineV6
jgod.council_chamber_backend_v6.websocket_manager import WebSocketManager
jgod.council_chamber_backend_v6.routers.war_room_ws import (
    router,
    set_websocket_manager,
    set_engine,
)

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("war_room")

# 檢查 API Key 設定
WAR_ROOM_API_KEY = os.getenv("WAR_ROOM_API_KEY")
if not WAR_ROOM_API_KEY:
    logger.warning(
        "⚠️  WAR_ROOM_API_KEY environment variable is not set. "
        "AI Council Chamber API v6.0 is running WITHOUT authentication protection. "
        "This is only suitable for local development. "
        "DO NOT deploy to production without setting the API key."
    )
else:
    logger.info("✓ AI Council Chamber API v6.0 authentication protection is enabled")

# 建立 FastAPI 應用
app = FastAPI(
    title="J-GOD AI Council Chamber Backend v6.0",
    description="FastAPI WebSocket 版本的幕僚會議室後端，專為 Next.js 前端設計",
    version="6.0.0",
)

# 設定 CORS（允許 Next.js 前端連線）
# Only allow localhost origins for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 WebSocket 管理器和引擎
websocket_manager = WebSocketManager()
provider_manager = ProviderManager()
engine = WarRoomEngineV6(provider_manager)

# 設定全域變數（供 router 使用）
set_websocket_manager(websocket_manager)
set_engine(engine)

# 註冊路由
app.include_router(router)

logger.info("[MAIN] AI Council Chamber Backend v6.0 initialized")
logger.info(f"[MAIN] Provider Manager initialized with {len(provider_manager.providers)} providers")


# === Health Check ===

@app.get("/health")
async def health_check():
    """健康檢查端點（不需要 API Key，已精簡內容）"""
    return {"status": "ok"}


@app.get("/")
async def root():
    """根路徑（不需要 API Key，已精簡內容）"""
    return "J-GOD AI Council Chamber Backend v6.0"


if __name__ == "__main__":
    # 啟動伺服器
    uvicorn.run(
        "jgod.council_chamber_backend_v6.main:app",
        host="0.0.0.0",
        port=8081,
        reload=True,  # 開發模式：自動重載
        log_level="info",
    )

