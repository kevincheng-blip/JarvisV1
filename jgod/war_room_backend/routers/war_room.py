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
    """WebSocket 端點 - 真正即時串流版本"""
    connection_id = str(uuid.uuid4())
    
    await manager.connect(websocket, connection_id, session_id)
    logger.info(f"WebSocket connected: {connection_id} for session {session_id}")
    
    try:
        # 等待客戶端發送啟動參數（最多等待 30 秒）
        import asyncio
        try:
            data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
        except asyncio.TimeoutError:
            await websocket.send_json({
                "type": "error",
                "session_id": session_id,
                "error_type": "TIMEOUT",
                "message": "等待啟動參數超時",
            })
            return
        
        mode = data.get("mode", "Lite")
        custom_providers = data.get("custom_providers")
        stock_id = data.get("stock_id", "")
        start_date = data.get("start_date", "")
        end_date = data.get("end_date", "")
        user_question = data.get("question", "")
        market_context = data.get("market_context", "")
        
        logger.info(f"Starting War Room session {session_id}: mode={mode}, stock_id={stock_id}")
        
        # 執行 War Room 分析並即時發送事件
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
            # 即時發送事件到 WebSocket
            try:
                await websocket.send_json(event.dict())
                logger.debug(f"Sent event: {event.type} for session {session_id}")
            except Exception as send_error:
                logger.error(f"Failed to send event: {send_error}")
                break  # 如果發送失敗，停止 streaming
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "session_id": session_id,
                "error_type": "WEBSOCKET_ERROR",
                "message": str(e),
            })
        except Exception:
            pass  # 如果連線已斷開，忽略發送錯誤
    finally:
        manager.disconnect(connection_id, session_id)
        logger.info(f"WebSocket connection closed: {connection_id}")

