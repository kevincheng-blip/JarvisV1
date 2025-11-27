"""
Data Feed 模組：統一處理多家 API 來源的 Tick 資料

本模組提供：
- UnifiedTick：統一的 Tick 數據結構
- BaseTickConverter：抽象基底類別
- SinopacConverter：永豐 API 的轉換器
- MockSinopacAPI：模擬永豐 API 的資料來源
"""

from .tick_handler import (
    UnifiedTick,
    BaseTickConverter,
    SinopacConverter,
    MockSinopacAPI,
)

__all__ = [
    "UnifiedTick",
    "BaseTickConverter",
    "SinopacConverter",
    "MockSinopacAPI",
]

