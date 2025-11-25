"""
Provider 基礎類別
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncIterator, Callable, List
from dataclasses import dataclass


@dataclass
class ProviderResult:
    """Provider 執行結果"""
    success: bool
    content: str
    error: Optional[str] = None
    provider_name: str = ""
    execution_time: float = 0.0


class BaseProviderAsync(ABC):
    """非同步 Provider 基礎類別"""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
    
    @abstractmethod
    async def run(self, prompt: str, system_prompt: Optional[str] = None) -> ProviderResult:
        """
        執行 Provider 請求（一次性完成）
        
        Args:
            prompt: 使用者提示
            system_prompt: 系統提示（可選）
        
        Returns:
            ProviderResult
        """
        pass
    
    async def run_stream(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
        max_tokens: Optional[int] = None
    ) -> ProviderResult:
        """
        執行 Provider 請求（Streaming 模式）
        
        Args:
            prompt: 使用者提示
            system_prompt: 系統提示（可選）
            on_chunk: 每收到一個 chunk 時的回調函數 (chunk: str) -> None
        
        Returns:
            ProviderResult（content 為完整內容）
        """
        # 預設實作：回退到非 streaming 模式
        return await self.run(prompt, system_prompt)

