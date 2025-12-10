"""
J-GOD API Routers

匯出所有 API router 模組。
"""

from jgod.api.routers import (
    backtest,
    decision,
    decision_ab,
    doctrine_alert,
    error_review,
    error_replay,
    indicators,
    orders,
    policy,
    predictions,
    self_repair,
    signal_conflict,
    strategy,
    universe,
)

__all__ = [
    "backtest",
    "decision",
    "decision_ab",
    "doctrine_alert",
    "error_review",
    "error_replay",
    "indicators",
    "orders",
    "policy",
    "predictions",
    "self_repair",
    "signal_conflict",
    "strategy",
    "universe",
]
