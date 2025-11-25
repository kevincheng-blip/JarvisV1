"""
War Room API 路由
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional
import logging
import uuid

from jgod.war_room_backend.websocket_manager import manager
from jgod.war_room_backend.engine.war_room_engine import WarRoomEngineBackend
from jgod.war_room_backend.models import WarRoomEvent

logger = logging.getLogger("war_room_backend.routers")

router = APIRouter()
engine = WarRoomEngineBackend()


@router.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "ok", "service": "war_room_backend_v5.0"}


@router.post("/api/war-room/session")
async def create_session():
    """建立新的戰情室會話"""
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}


@router.websocket("/ws/war-room/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket 端點"""
    connection_id = str(uuid.uuid4())
    
    await manager.connect(websocket, connection_id, session_id)
    
    try:
        # 等待客戶端發送啟動參數
        data = await websocket.receive_json()
        
        mode = data.get("mode", "Lite")
        custom_providers = data.get("custom_providers")
        stock_id = data.get("stock_id", "")
        start_date = data.get("start_date", "")
        end_date = data.get("end_date", "")
        user_question = data.get("question", "")
        market_context = data.get("market_context", "")
        
        # 執行 War Room 分析並發送事件
        async for event in engine.run_war_room(
            session_id=session_id,
            mode=mode,
            custom_providers=custom_providers,
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date,
            user_question=user_question,
            market_context=market_context,
        ):
            await manager.send_to_session(session_id, event.dict())
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await manager.send_to_session(session_id, {
            "type": "error",
            "session_id": session_id,
            "error_type": "WEBSOCKET_ERROR",
            "message": str(e),
        })
    finally:
        manager.disconnect(connection_id, session_id)

