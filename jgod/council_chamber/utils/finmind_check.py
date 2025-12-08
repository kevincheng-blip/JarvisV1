"""
FinMind Token 檢查工具
"""
import os
import logging
from typing import Tuple, Optional


def check_finmind_token() -> Tuple[bool, str]:
    """
    檢查 FinMind Token 是否已設定
    
    Returns:
        (是否已設定, 訊息)
    """
    # 檢查環境變數（支援 FINMIND_TOKEN 和 FINMIND_API_TOKEN）
    token = os.getenv("FINMIND_TOKEN") or os.getenv("FINMIND_API_TOKEN")
    
    if token:
        logger = logging.getLogger("war_room.finmind_check")
        logger.info("FinMind Token loaded: Yes")
        return True, "FinMind Token loaded from env"
    else:
        logger = logging.getLogger("war_room.finmind_check")
        logger.warning("FinMind Token loaded: No")
        return False, "FinMind Token missing in env"


def get_finmind_token() -> Optional[str]:
    """
    取得 FinMind Token（如果有的話）
    
    Returns:
        Token 字串，如果沒有則返回 None
    """
    return os.getenv("FINMIND_TOKEN") or os.getenv("FINMIND_API_TOKEN") or None

