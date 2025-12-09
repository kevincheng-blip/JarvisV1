"""
J-GOD API Routers

匯出所有 API router 模組。
"""

from jgod.api.routers import (
    backtest,
    decision,
    error_review,
    indicators,
    orders,
    policy,
    predictions,
    strategy,
    universe,
)

__all__ = [
    "backtest",
    "decision",
    "error_review",
    "indicators",
    "orders",
    "policy",
    "predictions",
    "strategy",
    "universe",
]
