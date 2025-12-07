"""
War Room Backend v5.0 - FastAPI 主程式
"""
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jgod.war_room_backend.config import API_HOST, API_PORT, LOG_LEVEL
from jgod.war_room_backend.routers import war_room

# 設定 logging
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("war_room_backend")

# 檢查 API Key 設定
WAR_ROOM_API_KEY = os.getenv("WAR_ROOM_API_KEY")
if not WAR_ROOM_API_KEY:
    logger.warning(
        "⚠️  WAR_ROOM_API_KEY environment variable is not set. "
        "War Room API v5.0 is running WITHOUT authentication protection. "
        "This is only suitable for local development. "
        "DO NOT deploy to production without setting the API key."
    )
else:
    logger.info("✓ War Room API v5.0 authentication protection is enabled")

# 建立 FastAPI 應用
app = FastAPI(
    title="J-GOD War Room Backend v5.0",
    description="真正即時串流的戰情室後端",
    version="5.0.0",
)

# CORS 設定
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

# 註冊路由
app.include_router(war_room.router)


@app.on_event("startup")
async def startup():
    """啟動事件"""
    logger.info("War Room Backend v5.0 starting up...")


@app.on_event("shutdown")
async def shutdown():
    """關閉事件"""
    logger.info("War Room Backend v5.0 shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)

