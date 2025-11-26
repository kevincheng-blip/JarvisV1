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
        on_chunk: Optional[Callable[[str], None]] = None,
        max_tokens: Optional[int] = None
    ) -> ProviderResult:
        """
        執行 Gemini 請求（改為一次性取得完整結果，但仍維持 streaming 介面）
        注意：google-genai SDK 不支援 stream=True，所以改為一次性取得完整結果後再觸發 on_chunk
        """
        start_time = time.time()
        full_content = ""
        
        try:
            loop = asyncio.get_event_loop()
            
            # 一次性取得完整結果（不使用 stream 參數）
            def get_full_response():
                nonlocal full_content
                try:
                    # 使用傳入的 max_tokens，如果為 None 則使用預設值 512
                    # 注意：Gemini 目前不支援 max_tokens，但保留參數以維持介面一致性
                    effective_max_tokens = max_tokens if max_tokens is not None else 512
                    # ask_stream 現在會一次性返回完整文字（但仍維持 generator 介面）
                    for chunk in self._provider.ask_stream(
                        system_prompt=system_prompt or "你是一個專業的股市分析師。",
                        user_prompt=prompt,
                        max_tokens=effective_max_tokens,
                    ):
                        if chunk:
                            full_content += chunk
                except Exception as e:
                    error_msg = f"[Gemini Error: {str(e)}]"
                    full_content = error_msg
                return full_content
            
            # 在 executor 中執行同步呼叫
            full_content = await loop.run_in_executor(None, get_full_response)
            
            # 取得完整結果後，一次性觸發 on_chunk（維持上層介面）
            if on_chunk and full_content:
                try:
                    on_chunk(full_content)
                except Exception as callback_error:
                    # 如果 on_chunk 回調失敗，記錄但不影響主流程
                    import logging
                    logger = logging.getLogger("war_room.gemini_provider")
                    logger.warning(f"on_chunk callback failed: {callback_error}")
            
            execution_time = time.time() - start_time
            
            return ProviderResult(
                success=True,
                content=full_content,
                provider_name=self.provider_name,
                execution_time=execution_time,
            )
        except RuntimeError as e:
            execution_time = time.time() - start_time
            error_msg = str(e).lower()
            if "api key" in error_msg or "api_key" in error_msg or "未設定" in str(e) or "not found" in error_msg:
                return ProviderResult(
                    success=False,
                    content=full_content,
                    error=f"API_KEY_MISSING:{str(e)}",
                    provider_name=self.provider_name,
                    execution_time=execution_time,
                )
            else:
                return ProviderResult(
                    success=False,
                    content=full_content,
                    error=f"API_CALL_FAILED:{str(e)}",
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

