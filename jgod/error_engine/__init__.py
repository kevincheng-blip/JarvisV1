"""
自動錯誤偵測系統
"""
from .error_watcher import ErrorWatcher, log_error, attempt_auto_fix

__all__ = [
    "ErrorWatcher",
    "log_error",
    "attempt_auto_fix",
]

