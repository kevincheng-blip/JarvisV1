"""
War Room API Key Authentication
共用於 v5.0 和 v6.0 的 API Key 驗證模組
"""
import os
import logging
from typing import Optional
from fastapi import Header, HTTPException, WebSocket, WebSocketException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# 從環境變數讀取 API Key
WAR_ROOM_API_KEY: Optional[str] = os.getenv("WAR_ROOM_API_KEY")

# 記錄 API Key 狀態
if WAR_ROOM_API_KEY:
    logger.info("[AUTH] War Room API Key is configured (protection enabled)")
else:
    logger.warning(
        "[AUTH] ⚠️  WAR_ROOM_API_KEY environment variable is not set. "
        "War Room API is running WITHOUT authentication protection. "
        "This is only suitable for local development. DO NOT deploy to production without setting the API key."
    )


def verify_api_key(api_key: Optional[str] = None) -> bool:
    """
    驗證 API Key
    
    Args:
        api_key: 提供的 API Key
        
    Returns:
        True if valid or no key required, False otherwise
    """
    # 如果環境變數沒有設定 API Key，允許通過（開發模式）
    if not WAR_ROOM_API_KEY:
        return True
    
    # 如果環境變數有設定，但提供的 key 為 None 或空，拒絕
    if not api_key:
        return False
    
    # 比較 key
    return api_key == WAR_ROOM_API_KEY


def require_api_key_header(x_war_room_key: Optional[str] = Header(None, alias="X-WAR-ROOM-KEY")) -> str:
    """
    FastAPI Dependency: 驗證 HTTP Header 中的 API Key
    
    Usage:
        @router.post("/endpoint")
        async def endpoint(api_key: str = Depends(require_api_key_header)):
            ...
    """
    if not WAR_ROOM_API_KEY:
        # 開發模式：允許通過
        return "dev_mode"
    
    if not x_war_room_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Please provide X-WAR-ROOM-KEY header."
        )
    
    if not verify_api_key(x_war_room_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key."
        )
    
    return x_war_room_key


async def require_api_key_websocket(websocket: WebSocket, api_key: Optional[str] = None) -> bool:
    """
    驗證 WebSocket 連線的 API Key
    
    API Key 可以透過：
    1. Query parameter: ?api_key=...
    2. Header: X-WAR-ROOM-KEY
    
    注意：此函數不會自動 accept WebSocket 連線，需要在驗證通過後由呼叫者（通常是 manager.connect()）處理 accept。
    
    Args:
        websocket: WebSocket 連線（尚未 accept）
        api_key: 從 query 參數取得的 key（可選）
        
    Returns:
        True if valid, raises WebSocketException otherwise
    """
    # 如果環境變數沒有設定 API Key，允許通過（開發模式）
    if not WAR_ROOM_API_KEY:
        return True
    
    # 優先檢查 query parameter
    if api_key:
        if verify_api_key(api_key):
            return True
    
    # 檢查 header
    headers = dict(websocket.headers)
    header_key = headers.get("X-WAR-ROOM-KEY") or headers.get("x-war-room-key")
    if header_key and verify_api_key(header_key):
        return True
    
    # 如果都沒有或都不正確，拒絕連線（在 accept 之前關閉）
    await websocket.close(
        code=status.WS_1008_POLICY_VIOLATION,
        reason="API key required. Provide ?api_key=... in query string or X-WAR-ROOM-KEY header."
    )
    raise WebSocketException(
        code=status.WS_1008_POLICY_VIOLATION,
        reason="API key required"
    )

