"""
Execution Engine - 執行引擎
提供模擬成交、交易記錄、滑價模擬等功能
"""
from .virtual_broker import VirtualBroker
from .trade_recorder import TradeRecorder
from .slippage import SlippageModel

__all__ = [
    "VirtualBroker",
    "TradeRecorder",
    "SlippageModel",
]

