"""
War Room Backend v5.0 - FastAPI 主程式
"""
import logging
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

# 建立 FastAPI 應用
app = FastAPI(
    title="J-GOD War Room Backend v5.0",
    description="真正即時串流的戰情室後端",
    version="5.0.0",
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境應限制
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

