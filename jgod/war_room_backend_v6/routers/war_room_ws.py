"""
War Room WebSocket 路由 - v6.0
提供 WebSocket API 供 Next.js 前端訂閱戰情室事件流
"""
import uuid
import asyncio
import logging
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from jgod.war_room_v6.core.engine_v6 import (
    WarRoomEngineV6,
    WarRoomRequest,
    WarRoomEvent,
)
from jgod.war_room.providers import ProviderManager
from jgod.war_room_backend_v6.websocket_manager import WebSocketManager

logger = logging.getLogger("war_room")

router = APIRouter(prefix="/api/v6/war-room", tags=["war-room-v6"])

# 全域 WebSocket 管理器（由 main.py 注入）
websocket_manager: Optional[WebSocketManager] = None

# 全域引擎（由 main.py 初始化）
engine: Optional[WarRoomEngineV6] = None


def set_websocket_manager(manager: WebSocketManager) -> None:
    """設定 WebSocket 管理器（由 main.py 呼叫）"""
    global websocket_manager
    websocket_manager = manager


def set_engine(engine_instance: WarRoomEngineV6) -> None:
    """設定引擎實例（由 main.py 呼叫）"""
    global engine
    engine = engine_instance


# === REST API ===

class CreateSessionRequest(BaseModel):
    """建立 Session 請求"""
    stock_ids: list[str]
    mode: str  # "god" | "custom"
    enabled_providers: list[str]
    user_prompt: str
    max_tokens: int = 512
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    market_context: Optional[str] = None


class CreateSessionResponse(BaseModel):
    """建立 Session 回應"""
    session_id: str
    websocket_url: str


@router.post("/session", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """
    建立新的戰情室 Session
    
    前端先呼叫此 API 取得 session_id，然後用該 session_id 連線 WebSocket
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    # 產生 session_id
    session_id = str(uuid.uuid4())
    
    logger.info(f"[API] Session created: {session_id}, mode={request.mode}, providers={request.enabled_providers}")
    
    return CreateSessionResponse(
        session_id=session_id,
        websocket_url=f"/ws/v6/war-room/{session_id}",
    )


# === WebSocket API ===

@router.websocket("/ws/v6/war-room/{session_id}")
async def war_room_websocket(websocket: WebSocket, session_id: str):
    """
    War Room WebSocket 端點
    
    流程：
    1. 前端連線到此 WebSocket
    2. 前端發送 JSON 請求（包含 stock_ids, mode, enabled_providers 等）
    3. 後端啟動 engine.run_session()
    4. 後端持續推送事件（session_start, role_start, role_chunk, role_done, summary）
    5. 所有事件完成後，WebSocket 保持連線（前端可選擇關閉）
    """
    if not websocket_manager:
        await websocket.close(code=1011, reason="WebSocket manager not initialized")
        return
    
    if not engine:
        await websocket.close(code=1011, reason="Engine not initialized")
        return
    
    # 連線 WebSocket
    await websocket_manager.connect(session_id, websocket)
    logger.info(f"[WS] Client connected: session={session_id}")
    
    try:
        # 等待前端發送請求
        request_data = await websocket.receive_json()
        logger.info(f"[WS] Received request for session {session_id}: {request_data}")
        
        # 驗證請求資料
        try:
            war_room_request = WarRoomRequest(
                session_id=session_id,
                stock_ids=request_data.get("stock_ids", []),
                mode=request_data.get("mode", "god"),
                enabled_providers=request_data.get("enabled_providers", []),
                user_prompt=request_data.get("user_prompt", ""),
                max_tokens=request_data.get("max_tokens", 512),
                start_date=request_data.get("start_date"),
                end_date=request_data.get("end_date"),
                market_context=request_data.get("market_context"),
            )
        except Exception as e:
            error_msg = f"Invalid request data: {str(e)}"
            logger.error(f"[WS] {error_msg}")
            await websocket_manager.send_personal_json(
                websocket,
                {
                    "type": "error",
                    "session_id": session_id,
                    "error": error_msg,
                }
            )
            return
        
        # 啟動引擎並推送事件
        logger.info(f"[WS] Starting engine for session {session_id}")
        
        # 建立一個獨立的 task 來執行 engine 並廣播事件
        async def run_engine_and_broadcast():
            """執行 engine 並廣播事件給所有連線"""
            try:
                async for event in engine.run_session(war_room_request):
                    # 檢查是否還有連線（如果沒有連線，就不需要繼續推送）
                    if not websocket_manager.has_connections(session_id):
                        logger.info(f"[WS] No connections for session {session_id}, stopping engine")
                        break
                    
                    # 將事件轉為字典並推送給前端
                    event_dict = event.dict()
                    await websocket_manager.send_json(session_id, event_dict)
                    logger.debug(f"[WS] Event sent: {event.type} for session {session_id}")
                
                logger.info(f"[WS] Session completed: {session_id}")
            except asyncio.CancelledError:
                logger.info(f"[WS] Engine task cancelled for session {session_id}")
                raise
            except Exception as e:
                logger.error(f"[WS] Engine error for session {session_id}: {e}", exc_info=True)
        
        engine_task = asyncio.create_task(run_engine_and_broadcast())
        
        try:
            # 監聽 WebSocket 訊息（目前可能只是心跳或握手）
            while True:
                try:
                    # 設定較短的 timeout，以便定期檢查連線狀態
                    msg = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                    # 可以處理心跳或其他訊息
                    logger.debug(f"[WS] Received message from session {session_id}: {msg[:50]}")
                except asyncio.TimeoutError:
                    # Timeout 是正常的，繼續檢查連線狀態
                    if not websocket_manager.has_connections(session_id):
                        logger.info(f"[WS] No connections for session {session_id}, cancelling engine")
                        break
                    # 檢查 engine task 是否已完成
                    if engine_task.done():
                        break
                    continue
        except WebSocketDisconnect:
            logger.info(f"[WS] Client disconnected: session={session_id}")
        finally:
            # 斷線處理
            websocket_manager.disconnect(session_id, websocket)
            
            # 如果這個 session 已經沒有任何連線，就取消 engine 任務
            if not websocket_manager.has_connections(session_id):
                if not engine_task.done():
                    logger.info(f"[WS] Cancelling engine task for session {session_id}")
                    engine_task.cancel()
                    try:
                        await engine_task
                    except asyncio.CancelledError:
                        logger.info(f"[WS] Engine task cancelled successfully for session {session_id}")
                    except Exception as e:
                        logger.error(f"[WS] Error while cancelling engine task: {e}")
    except Exception as e:
        logger.error(f"[WS] Error in session {session_id}: {e}", exc_info=True)
        
        # 發送錯誤事件
        try:
            await websocket_manager.send_personal_json(
                websocket,
                {
                    "type": "error",
                    "session_id": session_id,
                    "error": f"Internal error: {str(e)}",
                }
            )
        except Exception:
            pass
        
        websocket_manager.disconnect(session_id, websocket)
    
    finally:
        # 確保連線被清理
        websocket_manager.disconnect(session_id, websocket)

