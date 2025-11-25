"""
WebSocket 訊息模型 - v5.0
"""
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


class WarRoomEvent(BaseModel):
    """戰情室事件基類"""
    type: str
    session_id: str
    timestamp: str = datetime.now().isoformat()


class SessionStartEvent(WarRoomEvent):
    """會話開始事件"""
    type: Literal["session_start"] = "session_start"
    mode: str
    enabled_providers: list[str]
    stock_id: str
    question: str


class RoleChunkEvent(WarRoomEvent):
    """角色 chunk 事件"""
    type: Literal["role_chunk"] = "role_chunk"
    role: str
    role_label: str
    provider: str
    chunk: str
    sequence: int
    is_final: bool = False
    mode: Optional[str] = None  # 可選：模式資訊


class RoleDoneEvent(WarRoomEvent):
    """角色完成事件"""
    type: Literal["role_done"] = "role_done"
    role: str
    role_label: str
    provider: str
    success: bool
    content: str
    execution_time: float
    error_message: Optional[str] = None


class SummaryEvent(WarRoomEvent):
    """總結事件"""
    type: Literal["summary"] = "summary"
    content: str
    execution_time: float


class ErrorEvent(WarRoomEvent):
    """錯誤事件"""
    type: Literal["error"] = "error"
    error_type: str
    message: str
    details: Optional[dict] = None

