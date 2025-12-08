"""
錯誤處理器：統一處理各種錯誤狀態
"""
from typing import Optional
from enum import Enum
from dataclasses import dataclass


class ErrorType(Enum):
    """錯誤類型"""
    NOT_ENABLED = "NOT_ENABLED"
    API_KEY_MISSING = "API_KEY_MISSING"
    API_CALL_FAILED = "API_CALL_FAILED"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    PARSE_ERROR = "PARSE_ERROR"
    PROVIDER_OFFLINE = "PROVIDER_OFFLINE"
    UNKNOWN = "UNKNOWN"


@dataclass
class ErrorInfo:
    """錯誤資訊"""
    error_type: ErrorType
    message: str
    details: Optional[str] = None
    provider_name: str = ""
    can_retry: bool = False


class ErrorHandler:
    """錯誤處理器"""
    
    @staticmethod
    def parse_error(error_msg: str, provider_name: str = "") -> ErrorInfo:
        """
        解析錯誤訊息，返回結構化錯誤資訊
        
        Args:
            error_msg: 錯誤訊息
            provider_name: Provider 名稱
        
        Returns:
            ErrorInfo
        """
        if not error_msg:
            return ErrorInfo(
                error_type=ErrorType.UNKNOWN,
                message="未知錯誤",
                provider_name=provider_name,
            )
        
        error_lower = error_msg.lower()
        
        # 檢查錯誤類型標記
        if error_msg.startswith("NOT_ENABLED:"):
            return ErrorInfo(
                error_type=ErrorType.NOT_ENABLED,
                message="此 Provider 在目前模式未啟用",
                details=error_msg.replace("NOT_ENABLED:", ""),
                provider_name=provider_name,
                can_retry=False,
            )
        elif error_msg.startswith("API_KEY_MISSING:"):
            return ErrorInfo(
                error_type=ErrorType.API_KEY_MISSING,
                message="此 Provider 的 API Key 未設定，相關功能暫停",
                details=error_msg.replace("API_KEY_MISSING:", ""),
                provider_name=provider_name,
                can_retry=False,
            )
        elif error_msg.startswith("API_CALL_FAILED:"):
            actual_error = error_msg.replace("API_CALL_FAILED:", "")
            
            # 進一步判斷具體錯誤類型
            if "timeout" in error_lower or "timed out" in error_lower:
                return ErrorInfo(
                    error_type=ErrorType.TIMEOUT,
                    message="呼叫 Provider 逾時，請稍後重試",
                    details=actual_error,
                    provider_name=provider_name,
                    can_retry=True,
                )
            elif "429" in error_msg or "rate limit" in error_lower:
                return ErrorInfo(
                    error_type=ErrorType.RATE_LIMIT,
                    message="Provider 遇到負載過高，請稍後重試",
                    details=actual_error,
                    provider_name=provider_name,
                    can_retry=True,
                )
            else:
                return ErrorInfo(
                    error_type=ErrorType.API_CALL_FAILED,
                    message="呼叫 Provider 失敗，請稍後重試",
                    details=actual_error,
                    provider_name=provider_name,
                    can_retry=True,
                )
        elif "parse" in error_lower or "json" in error_lower:
            return ErrorInfo(
                error_type=ErrorType.PARSE_ERROR,
                message="回應格式解析錯誤",
                details=error_msg,
                provider_name=provider_name,
                can_retry=False,
            )
        else:
            return ErrorInfo(
                error_type=ErrorType.UNKNOWN,
                message="發生未知錯誤",
                details=error_msg,
                provider_name=provider_name,
                can_retry=False,
            )
    
    @staticmethod
    def get_error_ui_message(error_info: ErrorInfo) -> tuple[str, str]:
        """
        取得錯誤的 UI 顯示訊息
        
        Returns:
            (標題, 詳細訊息)
        """
        messages = {
            ErrorType.NOT_ENABLED: ("⚠️ 此 Provider 在目前模式未啟用", "請在左側 Sidebar 選擇對應的 Provider"),
            ErrorType.API_KEY_MISSING: ("❌ 此 Provider 的 API Key 未設定，相關功能暫停", f"詳細：{error_info.details or ''}"),
            ErrorType.TIMEOUT: ("⏱️ 呼叫 Provider 逾時", "請稍後重試，詳細錯誤已記錄至 logs/error/"),
            ErrorType.RATE_LIMIT: ("🚦 Provider 遇到負載過高", "請稍後重試，詳細錯誤已記錄至 logs/error/"),
            ErrorType.API_CALL_FAILED: ("❌ 呼叫 Provider 失敗", f"錯誤：{error_info.details[:100] if error_info.details else ''}..."),
            ErrorType.PARSE_ERROR: ("⚠️ 回應格式解析錯誤", "請檢查 Provider 回應格式"),
            ErrorType.PROVIDER_OFFLINE: ("🔴 Provider 離線", "系統將自動 fallback 到其他 Provider"),
            ErrorType.UNKNOWN: ("❌ 發生未知錯誤", f"錯誤：{error_info.details or ''}"),
        }
        
        return messages.get(error_info.error_type, ("❌ 錯誤", error_info.message))

