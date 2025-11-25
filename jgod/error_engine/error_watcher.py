"""
自動錯誤偵測與記錄系統
"""
import traceback
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import functools


# 設定日誌
LOG_DIR = Path("logs/error")
LOG_DIR.mkdir(parents=True, exist_ok=True)

error_logger = logging.getLogger("error_engine")
error_logger.setLevel(logging.ERROR)

# 建立檔案 handler
log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}_error.log"
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setLevel(logging.ERROR)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d\n"
)
file_handler.setFormatter(formatter)
error_logger.addHandler(file_handler)


class ErrorWatcher:
    """錯誤監視器"""
    
    @staticmethod
    def log_error(
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        記錄錯誤
        
        Args:
            error: 例外物件
            context: 額外上下文資訊
        
        Returns:
            錯誤記錄檔案路徑
        """
        error_msg = str(error)
        error_traceback = traceback.format_exc()
        
        # 記錄到日誌
        error_logger.error(
            f"Error: {error_msg}\nContext: {context}\n{traceback.format_exc()}"
        )
        
        # 回傳檔案路徑
        return str(log_file)
    
    @staticmethod
    def attempt_auto_fix(error: Exception) -> bool:
        """
        嘗試自動修復錯誤（預留功能）
        
        Args:
            error: 例外物件
        
        Returns:
            是否成功修復
        """
        # TODO: 實作自動修復邏輯
        return False


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
    """便利函式：記錄錯誤"""
    return ErrorWatcher.log_error(error, context)


def attempt_auto_fix(error: Exception) -> bool:
    """便利函式：嘗試自動修復"""
    return ErrorWatcher.attempt_auto_fix(error)


def error_handler(func):
    """裝飾器：自動捕捉並記錄錯誤"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            log_error(e, {"function": func.__name__, "args": str(args), "kwargs": str(kwargs)})
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_error(e, {"function": func.__name__, "args": str(args), "kwargs": str(kwargs)})
            raise
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

