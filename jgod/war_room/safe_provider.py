"""
安全的 Provider 呼叫包裝器
"""
from typing import Callable, Any, Optional, Tuple
import traceback
import logging

logger = logging.getLogger(__name__)


def safe_call_provider(
    provider_name: str,
    fn: Callable,
    *args,
    **kwargs,
) -> Tuple[bool, Any, Optional[str]]:
    """
    安全地呼叫 Provider 函式
    
    Args:
        provider_name: Provider 名稱（用於錯誤訊息）
        fn: 要呼叫的函式
        *args: 位置參數
        **kwargs: 關鍵字參數
    
    Returns:
        (是否成功, 結果, 錯誤訊息)
    """
    try:
        result = fn(*args, **kwargs)
        return (True, result, None)
    except Exception as e:
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        
        # 記錄完整 traceback 到 log
        logger.error(f"[{provider_name}] 呼叫失敗：\n{error_traceback}")
        
        # 回傳簡短的錯誤訊息
        return (False, None, error_msg)

