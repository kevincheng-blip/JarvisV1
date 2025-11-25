"""
Gemini Provider 非同步實作（支援 Streaming）
"""
import asyncio
import time
from typing import Optional, Callable

from api_clients.gemini_client import GeminiProvider
from .base_provider import BaseProviderAsync, ProviderResult


class GeminiProviderAsync(BaseProviderAsync):
    """Gemini Provider 非同步包裝（支援 Streaming）"""
    
    def __init__(self):
        super().__init__("Gemini Flash 2.5")
        self._provider = GeminiProvider()
    
    async def run(self, prompt: str, system_prompt: Optional[str] = None) -> ProviderResult:
        """執行 Gemini 請求（一次性完成）"""
        start_time = time.time()
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._provider.ask(
                    system_prompt=system_prompt or "你是一個專業的股市分析師。",
                    user_prompt=prompt,
                )
            )
            
            execution_time = time.time() - start_time
            
            return ProviderResult(
                success=True,
                content=result or "",
                provider_name=self.provider_name,
                execution_time=execution_time,
            )
        except RuntimeError as e:
            execution_time = time.time() - start_time
            error_msg = str(e).lower()
            if "api key" in error_msg or "api_key" in error_msg or "未設定" in str(e) or "not found" in error_msg:
                return ProviderResult(
                    success=False,
                    content="",
                    error=f"API_KEY_MISSING:{str(e)}",
                    provider_name=self.provider_name,
                    execution_time=execution_time,
                )
            else:
                return ProviderResult(
                    success=False,
                    content="",
                    error=f"API_CALL_FAILED:{str(e)}",
                    provider_name=self.provider_name,
                    execution_time=execution_time,
                )
        except Exception as e:
            execution_time = time.time() - start_time
            return ProviderResult(
                success=False,
                content="",
                error=f"API_CALL_FAILED:{str(e)}",
                provider_name=self.provider_name,
                execution_time=execution_time,
            )
    
    async def run_stream(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> ProviderResult:
        """執行 Gemini 請求（真正的 Streaming 模式）"""
        start_time = time.time()
        full_content = ""
        
        try:
            loop = asyncio.get_event_loop()
            
            # 使用真正的 streaming API
            def process_stream():
                nonlocal full_content
                try:
                    for chunk in self._provider.ask_stream(
                        system_prompt=system_prompt or "你是一個專業的股市分析師。",
                        user_prompt=prompt,
                    ):
                        if chunk:
                            full_content += chunk
                            if on_chunk:
                                on_chunk(chunk)
                except Exception as e:
                    error_msg = f"[Gemini Error: {str(e)}]"
                    full_content += error_msg
                    if on_chunk:
                        on_chunk(error_msg)
                return full_content
            
            await loop.run_in_executor(None, process_stream)
            
            execution_time = time.time() - start_time
            
            return ProviderResult(
                success=True,
                content=full_content,
                provider_name=self.provider_name,
                execution_time=execution_time,
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ProviderResult(
                success=False,
                content=full_content,
                error=f"API_CALL_FAILED:{str(e)}",
                provider_name=self.provider_name,
                execution_time=execution_time,
            )

