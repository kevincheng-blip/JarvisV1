"""
War Room Backend v6.0 - FastAPI 啟動器
專為 Next.js 前端設計的戰情室後端
"""
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jgod.war_room.providers import ProviderManager
from jgod.war_room_v6.core.engine_v6 import WarRoomEngineV6
from jgod.war_room_backend_v6.websocket_manager import WebSocketManager
from jgod.war_room_backend_v6.routers.war_room_ws import (
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

# 建立 FastAPI 應用
app = FastAPI(
    title="J-GOD War Room Backend v6.0",
    description="FastAPI WebSocket 版本的戰情室後端，專為 Next.js 前端設計",
    version="6.0.0",
)

# 設定 CORS（允許 Next.js 前端連線）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境請改為特定域名
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

logger.info("[MAIN] War Room Backend v6.0 initialized")
logger.info(f"[MAIN] Provider Manager initialized with {len(provider_manager.providers)} providers")


# === Health Check ===

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "version": "6.0.0",
        "active_sessions": len(websocket_manager.get_all_sessions()),
        "providers": list(provider_manager.providers.keys()),
    }


@app.get("/")
async def root():
    """根路徑"""
    return {
        "name": "J-GOD War Room Backend v6.0",
        "version": "6.0.0",
        "endpoints": {
            "health": "/health",
            "create_session": "POST /api/v6/war-room/session",
            "websocket": "WS /ws/v6/war-room/{session_id}",
        },
    }


if __name__ == "__main__":
    # 啟動伺服器
    uvicorn.run(
        "jgod.war_room_backend_v6.main:app",
        host="0.0.0.0",
        port=8081,
        reload=True,  # 開發模式：自動重載
        log_level="info",
    )

