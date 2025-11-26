"""
Gemini Provider 非同步實作（支援 Streaming）
"""
import asyncio
import time
import logging
from typing import Optional, Callable

from api_clients.gemini_client import GeminiProvider
from .base_provider import BaseProviderAsync, ProviderResult

logger = logging.getLogger("war_room.gemini_provider")


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
        加入 timeout 控制，確保 Scout 角色能在 8 秒內回應
        """
        start_time = time.time()
        full_content = ""
        first_chunk_time = None
        
        try:
            loop = asyncio.get_event_loop()
            
            # 一次性取得完整結果（不使用 stream 參數）
            def get_full_response():
                nonlocal full_content, first_chunk_time
                try:
                    # Scout 角色使用較短的 max_tokens 以加速（512-768）
                    effective_max_tokens = max_tokens if max_tokens is not None else 512
                    # ask_stream 現在會一次性返回完整文字（但仍維持 generator 介面）
                    for chunk in self._provider.ask_stream(
                        system_prompt=system_prompt or "你是一個專業的股市分析師。",
                        user_prompt=prompt,
                        max_tokens=effective_max_tokens,
                    ):
                        if chunk and chunk.strip():
                            # 記錄第一個 chunk 的時間
                            if first_chunk_time is None:
                                first_chunk_time = time.time()
                            full_content += chunk
                except Exception as e:
                    # 不要直接把錯誤訊息當作內容，記錄 log 即可
                    import logging
                    logger = logging.getLogger("war_room.gemini_provider")
                    logger.exception("[GEMINI] Error in get_full_response: %s", e)
                    # 不設定 full_content，讓後續的空內容檢查處理
                return full_content
            
            # 在 executor 中執行同步呼叫，加入 8 秒 timeout（Scout 加速）
            try:
                full_content = await asyncio.wait_for(
                    loop.run_in_executor(None, get_full_response),
                    timeout=8.0
                )
            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                timeout_msg = f"Gemini API call timeout after {execution_time:.2f}s"
                return ProviderResult(
                    success=False,
                    content=full_content or "[Timeout: Gemini 回應超時]",
                    error=f"TIMEOUT:{timeout_msg}",
                    provider_name=self.provider_name,
                    execution_time=execution_time,
                )
            
            # 檢查內容是否為空
            if not full_content or not full_content.strip():
                # 如果內容為空，使用備援訊息
                logger.warning("[GEMINI] Empty content returned from client, using fallback message")
                full_content = "【GEMINI 備援提示】本次 Gemini 回傳的是空內容，建議參考其他角色（Intel / Quant / Strategist）的分析。"
                execution_time = time.time() - start_time
                return ProviderResult(
                    success=False,
                    content=full_content,
                    error="EMPTY_CONTENT",
                    provider_name=self.provider_name,
                    execution_time=execution_time,
                )
            
            # 取得完整結果後，一次性觸發 on_chunk（維持上層介面）
            if on_chunk and full_content:
                try:
                    on_chunk(full_content)
                except Exception as callback_error:
                    # 如果 on_chunk 回調失敗，記錄但不影響主流程
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

