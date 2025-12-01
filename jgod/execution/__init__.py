"""
Execution Engine - 執行引擎
提供模擬成交、交易記錄、滑價模擬等功能

Reference:
- docs/JGOD_EXECUTION_ENGINE_STANDARD_v1.md (v1)
"""

# Execution Engine v1 (優先導入，避免循環導入)
from .execution_types import Order, Fill, Trade, Position, PortfolioState
from .execution_models import (
    ExecutionModel,
    FixedSlippageModel,
    PercentageSlippageModel,
    VolumeImpactSlippageModel
)
from .cost_model import CostModel, DefaultCostModel
from .broker_adapter import BrokerAdapter, MockBrokerAdapter
from .execution_engine import ExecutionEngine, ExecutionRequest, ExecutionResult

# Legacy exports (v0) - 延遲導入以避免循環依賴
# from .virtual_broker import VirtualBroker
# from .trade_recorder import TradeRecorder
# from .slippage import SlippageModel

__all__ = [
    # Execution Engine v1 exports
    "Order",
    "Fill",
    "Trade",
    "Position",
    "PortfolioState",
    "ExecutionModel",
    "FixedSlippageModel",
    "PercentageSlippageModel",
    "VolumeImpactSlippageModel",
    "CostModel",
    "DefaultCostModel",
    "BrokerAdapter",
    "MockBrokerAdapter",
    "ExecutionEngine",
    "ExecutionRequest",
    "ExecutionResult",
    # Legacy exports (v0) - 可選，視需要取消註解
    # "VirtualBroker",
    # "TradeRecorder",
    # "SlippageModel",
]

