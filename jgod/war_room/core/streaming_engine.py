"""
Streaming 引擎：負責 token 級 streaming 處理
"""
import asyncio
from typing import Callable, Optional, AsyncIterator
from dataclasses import dataclass
import time

from jgod.war_room.providers.base_provider import ProviderResult


@dataclass
class StreamingChunk:
    """Streaming 資料塊"""
    role_name: str
    chunk: str
    is_complete: bool = False
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class StreamingEngine:
    """Streaming 引擎：統一管理所有 Provider 的 streaming"""
    
    def __init__(self):
        self.active_streams = {}  # {role_name: AsyncIterator}
        self.streaming_callbacks = {}  # {role_name: Callable}
    
    async def stream_provider(
        self,
        role_name: str,
        provider,
        prompt: str,
        system_prompt: Optional[str] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> ProviderResult:
        """
        執行 Provider streaming
        
        Args:
            role_name: 角色名稱
            provider: Provider 實例（必須有 run_stream 方法）
            prompt: 使用者提示
            system_prompt: 系統提示
            on_chunk: 每收到一個 chunk 時的回調 (chunk: str) -> None
        
        Returns:
            ProviderResult（包含完整內容）
        """
        full_content = ""
        start_time = time.time()
        
        try:
            # 使用 list 作為可變引用
            full_content_ref = [full_content]
            
            # 檢查 Provider 是否支援 streaming
            if hasattr(provider, 'run_stream'):
                # 使用 streaming 模式
                def chunk_handler(chunk: str):
                    if chunk:
                        full_content_ref[0] += chunk
                        if on_chunk:
                            on_chunk(chunk)
                
                result = await provider.run_stream(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    on_chunk=chunk_handler
                )
                # 確保 content 是最新的
                if result.success:
                    result.content = full_content_ref[0]
                return result
            else:
                # 回退到非 streaming 模式
                result = await provider.run(prompt, system_prompt)
                # 模擬 streaming（分段輸出）
                if result.success and result.content:
                    content = result.content
                    chunk_size = 10  # 每 10 個字元一段
                    for i in range(0, len(content), chunk_size):
                        chunk = content[i:i+chunk_size]
                        full_content_ref[0] += chunk
                        if on_chunk:
                            on_chunk(chunk)
                        await asyncio.sleep(0.05)  # 模擬延遲
                    result.content = full_content_ref[0]
                return result
        except Exception as e:
            execution_time = time.time() - start_time
            return ProviderResult(
                success=False,
                content=full_content,
                error=f"API_CALL_FAILED:{str(e)}",
                provider_name=getattr(provider, 'provider_name', 'unknown'),
                execution_time=execution_time,
            )

