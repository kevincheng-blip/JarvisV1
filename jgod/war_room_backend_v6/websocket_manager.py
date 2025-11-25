"""
WebSocket 連線管理器
管理 session_id 到 WebSocket 連線的映射（支援多對一）
"""
import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger("war_room")


class WebSocketManager:
    """
    WebSocket 連線管理器
    
    功能：
    - 管理 session_id → WebSocket 連線的映射（支援一個 session 多個連線）
    - 提供連線/斷線管理
    - 提供事件推送（單播和廣播）
    """
    
    def __init__(self):
        """初始化 WebSocket 管理器"""
        # session_id -> List[WebSocket] 的映射
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.logger = logger
    
    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """
        新增 WebSocket 連線
        
        Args:
            session_id: Session ID
            websocket: WebSocket 連線物件
        """
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        
        self.active_connections[session_id].append(websocket)
        self.logger.info(f"[WS_MANAGER] Connected: session={session_id}, total_connections={len(self.active_connections[session_id])}")
    
    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        """
        移除 WebSocket 連線
        
        Args:
            session_id: Session ID
            websocket: WebSocket 連線物件
        """
        if session_id not in self.active_connections:
            return
        
        if websocket in self.active_connections[session_id]:
            self.active_connections[session_id].remove(websocket)
            self.logger.info(f"[WS_MANAGER] Disconnected: session={session_id}, remaining_connections={len(self.active_connections[session_id])}")
        
        # 如果該 session 沒有連線了，移除 session
        if not self.active_connections[session_id]:
            del self.active_connections[session_id]
            self.logger.info(f"[WS_MANAGER] Session removed: {session_id}")
    
    async def send_json(self, session_id: str, data: Dict) -> None:
        """
        發送 JSON 資料給指定 session 的所有連線（廣播）
        
        Args:
            session_id: Session ID
            data: 要發送的資料（字典，會被轉為 JSON）
        """
        if session_id not in self.active_connections:
            self.logger.warning(f"[WS_MANAGER] No connections for session: {session_id}")
            return
        
        # 複製列表以避免迭代時修改
        connections = list(self.active_connections[session_id])
        
        for ws in connections:
            try:
                await ws.send_json(data)
            except Exception as e:
                self.logger.error(f"[WS_MANAGER] Error sending to session {session_id}: {e}")
                # 連線失敗，移除該連線
                self.disconnect(session_id, ws)
    
    async def send_personal_json(self, websocket: WebSocket, data: Dict) -> None:
        """
        發送 JSON 資料給單一 WebSocket 連線（單播）
        
        Args:
            websocket: WebSocket 連線物件
            data: 要發送的資料（字典，會被轉為 JSON）
        """
        try:
            await websocket.send_json(data)
        except Exception as e:
            self.logger.error(f"[WS_MANAGER] Error sending personal message: {e}")
    
    def get_connection_count(self, session_id: str) -> int:
        """
        取得指定 session 的連線數量
        
        Args:
            session_id: Session ID
            
        Returns:
            連線數量
        """
        return len(self.active_connections.get(session_id, []))
    
    def get_all_sessions(self) -> List[str]:
        """
        取得所有活躍的 session ID 列表
        
        Returns:
            Session ID 列表
        """
        return list(self.active_connections.keys())

