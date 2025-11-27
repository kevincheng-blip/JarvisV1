"""
Factor Engine 模組：核心因子計算引擎

本模組提供：
- InfoTimeBarGenerator：信息時間 Volume Bar 生成器（Step 2）
- OrderbookFactorEngine：微觀流動性因子引擎（Step 3）
- CapitalFlowEngine：資金流基礎因子引擎（Step 4）
"""

from .info_time_engine import (
    VolumeBar,
    InfoTimeBarGenerator,
)

from .orderbook_factor import (
    OrderbookFactor,
    OrderbookFactorEngine,
)

from .capital_flow_factor import (
    CapitalFlowSample,
    CapitalFlowFactor,
    CapitalFlowEngine,
)

__all__ = [
    # Step 2 - F_InfoTime
    "VolumeBar",
    "InfoTimeBarGenerator",
    # Step 3 - F_Orderbook
    "OrderbookFactor",
    "OrderbookFactorEngine",
    # Step 4 - F_C (SAI & MOI)
    "CapitalFlowSample",
    "CapitalFlowFactor",
    "CapitalFlowEngine",
]

