"""
Rule-Based Filters for Prediction Engine
"""

from jgod.prediction.rules.stock_upside_filter_v1 import (
    StockUpsideFilterV1,
    StockUpsideResult,
    IndicatorScore,
)
from jgod.prediction.rules.stock_upside_filter_60_v1 import (
    StockUpsideFilter60V1,
)

__all__ = [
    "StockUpsideFilterV1",
    "StockUpsideResult",
    "IndicatorScore",
    "StockUpsideFilter60V1",
]

