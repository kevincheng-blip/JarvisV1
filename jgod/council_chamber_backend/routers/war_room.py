"""
AI Council Chamber API 路由
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, Request
from typing import Optional
import logging
import uuid

jgod.council_chamber_backend.websocket_manager import manager
jgod.council_chamber_backend.engine.war_room_engine import WarRoomEngineBackend
jgod.council_chamber_backend.models import WarRoomEvent
jgod.council_chamber_backend.auth import (
    require_api_key_header,
    require_api_key_websocket,
    check_http_rate_limit,
    check_websocket_rate_limit,
)

logger = logging.getLogger("war_room_backend.routers")

router = APIRouter()
engine = WarRoomEngineBackend()


@router.get("/health")
async def health_check():
    """健康檢查（不需要 API Key）"""
    return {"status": "ok"}


@router.post("/api/war-room/session")
async def create_session(
    request: Request,
    api_key: str = Depends(require_api_key_header)
):
    """建立新的幕僚會議室會話（需要 API Key 和 Rate Limit 檢查）"""
    # 檢查 Rate Limit（在 API Key 驗證之後）
    check_http_rate_limit(api_key=api_key, request=request)
    
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}


@router.websocket("/ws/war-room/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    api_key: Optional[str] = Query(None, description="API Key for WebSocket authentication")
):
    """WebSocket 端點 - 真正即時串流版本（需要 API Key 和 Rate Limit 檢查）"""
    # 先檢查 Rate Limit（在連線建立前）
    await check_websocket_rate_limit(websocket, api_key)
    
    # 驗證 API Key（內部會處理 accept，如果驗證通過）
    await require_api_key_websocket(websocket, api_key)
    
    connection_id = str(uuid.uuid4())
    
    # manager.connect 可能會再次 accept，但不會有問題（已經 accept 的會直接返回）
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
        
        logger.info(f"Starting AI Council Chamber session {session_id}: mode={mode}, stock_id={stock_id}")
        
        # 執行 AI Council Chamber 分析並即時發送事件
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

