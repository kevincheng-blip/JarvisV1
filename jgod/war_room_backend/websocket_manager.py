"""
WebSocket 管理器
"""
from typing import Dict, Set
from fastapi import WebSocket
import logging

logger = logging.getLogger("war_room_backend.websocket_manager")


class WebSocketManager:
    """管理所有 WebSocket 連線"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, Set[str]] = {}  # session_id -> set of connection_ids
    
    async def connect(self, websocket: WebSocket, connection_id: str, session_id: str):
        """建立連線"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if session_id not in self.session_connections:
            self.session_connections[session_id] = set()
        self.session_connections[session_id].add(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} for session {session_id}")
    
    def disconnect(self, connection_id: str, session_id: str):
        """斷開連線"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if session_id in self.session_connections:
            self.session_connections[session_id].discard(connection_id)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_to_session(self, session_id: str, message: dict):
        """發送訊息到指定會話的所有連線"""
        if session_id not in self.session_connections:
            return
        
        disconnected = []
        for connection_id in self.session_connections[session_id]:
            websocket = self.active_connections.get(connection_id)
            if websocket:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to {connection_id}: {e}")
                    disconnected.append(connection_id)
        
        # 清理斷開的連線
        for connection_id in disconnected:
            self.disconnect(connection_id, session_id)
    
    async def broadcast(self, message: dict):
        """廣播訊息到所有連線"""
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # 清理斷開的連線
        for connection_id in disconnected:
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]


# 全域 WebSocket 管理器實例
manager = WebSocketManager()

