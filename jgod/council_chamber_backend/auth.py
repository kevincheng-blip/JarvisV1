"""
AI Council Chamber API Key Authentication & Rate Limiting
共用於 v5.0 和 v6.0 的 API Key 驗證與 Rate Limit 模組
"""
import os
import time
import logging
from typing import Optional, Dict, Tuple
from collections import deque
from fastapi import Header, HTTPException, WebSocket, WebSocketException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# 從環境變數讀取 API Key
WAR_ROOM_API_KEY: Optional[str] = os.getenv("WAR_ROOM_API_KEY")

# 記錄 API Key 狀態
if WAR_ROOM_API_KEY:
    logger.info("[AUTH] AI Council Chamber API Key is configured (protection enabled)")
else:
    logger.warning(
        "[AUTH] ⚠️  WAR_ROOM_API_KEY environment variable is not set. "
        "AI Council Chamber API is running WITHOUT authentication protection. "
        "This is only suitable for local development. DO NOT deploy to production without setting the API key."
    )

# Rate Limit 設定
WAR_ROOM_HTTP_RATE_PER_MIN = int(os.getenv("WAR_ROOM_HTTP_RATE_PER_MIN", "30"))
WAR_ROOM_WS_RATE_PER_MIN = int(os.getenv("WAR_ROOM_WS_RATE_PER_MIN", "10"))

logger.info(f"[AUTH] Rate Limit configured - HTTP: {WAR_ROOM_HTTP_RATE_PER_MIN}/min, WebSocket: {WAR_ROOM_WS_RATE_PER_MIN}/min")

# In-memory Rate Limit 儲存
# 結構：{identifier: deque([timestamp1, timestamp2, ...])}
_rate_limit_storage: Dict[str, deque] = {}


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


def _get_rate_limit_identifier(
    api_key: Optional[str] = None,
    request: Optional[Request] = None,
    websocket: Optional[WebSocket] = None
) -> Tuple[str, str]:
    """
    取得 Rate Limit 的識別值（API Key 或 IP）
    
    Args:
        api_key: 提供的 API Key（如果有）
        request: HTTP Request（用於取得 IP）
        websocket: WebSocket（用於取得 IP）
        
    Returns:
        (identifier, identifier_type) tuple
        identifier_type 為 "api_key" 或 "ip"
    """
    # 優先使用 API Key（如果有效）
    if api_key and WAR_ROOM_API_KEY and verify_api_key(api_key):
        # 部分遮蔽 API Key 用於日誌
        masked_key = api_key[:8] + "..." if len(api_key) > 8 else "***"
        return api_key, "api_key"
    
    # 退而求其次使用 IP
    ip = None
    if request:
        # 取得真實 IP（考慮反向代理）
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not ip:
            ip = request.headers.get("X-Real-IP", "").strip()
        if not ip:
            ip = request.client.host if request.client else "unknown"
    elif websocket:
        # WebSocket 取得 IP
        headers = dict(websocket.headers)
        ip = headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not ip:
            ip = headers.get("X-Real-IP", "").strip()
        if not ip:
            # WebSocket 沒有直接取得 IP 的方法，使用連線資訊
            ip = str(websocket.client) if hasattr(websocket, "client") and websocket.client else "unknown"
    
    if not ip or ip == "unknown":
        ip = "unknown_ip"
    
    return ip, "ip"


def _check_rate_limit(identifier: str, limit_per_min: int, endpoint_name: str, identifier_type: str) -> bool:
    """
    檢查是否超出 Rate Limit
    
    Args:
        identifier: 識別值（API Key 或 IP）
        limit_per_min: 每分鐘限制次數
        endpoint_name: 端點名稱（用於日誌）
        identifier_type: 識別類型（"api_key" 或 "ip"）
        
    Returns:
        True if within limit, False if exceeded
    """
    now = time.time()
    window_start = now - 60.0  # 過去 60 秒
    
    # 取得或建立該識別值的時間戳佇列
    if identifier not in _rate_limit_storage:
        _rate_limit_storage[identifier] = deque()
    
    timestamps = _rate_limit_storage[identifier]
    
    # 移除超過 60 秒的舊時間戳
    while timestamps and timestamps[0] < window_start:
        timestamps.popleft()
    
    # 檢查是否超過限制
    if len(timestamps) >= limit_per_min:
        # 部分遮蔽識別值用於日誌
        if identifier_type == "api_key":
            masked_id = identifier[:8] + "..." if len(identifier) > 8 else "***"
        else:
            masked_id = identifier[:12] + "..." if len(identifier) > 12 else identifier
        
        logger.warning(
            f"[RATE_LIMIT] Rate limit exceeded for {endpoint_name} - "
            f"{identifier_type}: {masked_id}, current: {len(timestamps)}/{limit_per_min} per minute"
        )
        return False
    
    # 記錄這次請求的時間戳
    timestamps.append(now)
    return True


def check_http_rate_limit(
    api_key: Optional[str] = None,
    request: Optional[Request] = None
) -> None:
    """
    檢查 HTTP 端點的 Rate Limit
    
    Args:
        api_key: API Key（如果有）
        request: FastAPI Request 物件
        
    Raises:
        HTTPException: 如果超出限制，回傳 429
    """
    identifier, identifier_type = _get_rate_limit_identifier(api_key=api_key, request=request)
    
    if not _check_rate_limit(
        identifier=identifier,
        limit_per_min=WAR_ROOM_HTTP_RATE_PER_MIN,
        endpoint_name="HTTP",
        identifier_type=identifier_type
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )


async def check_websocket_rate_limit(
    websocket: WebSocket,
    api_key: Optional[str] = None
) -> None:
    """
    檢查 WebSocket 端點的 Rate Limit
    
    Args:
        websocket: WebSocket 連線
        api_key: API Key（如果有）
        
    Raises:
        WebSocketException: 如果超出限制，拒絕連線
    """
    identifier, identifier_type = _get_rate_limit_identifier(api_key=api_key, websocket=websocket)
    
    if not _check_rate_limit(
        identifier=identifier,
        limit_per_min=WAR_ROOM_WS_RATE_PER_MIN,
        endpoint_name="WebSocket",
        identifier_type=identifier_type
    ):
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Rate limit exceeded. Please try again later."
        )
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Rate limit exceeded"
        )


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

