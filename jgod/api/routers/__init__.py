"""
J-GOD API Routers

匯出所有 API router 模組。
"""

from jgod.api.routers import (
    backtest,
    decision,
    decision_ab,
    doctrine_alert,
    doctrine_v2,
    error_review,
    error_replay,
    indicators,
    orders,
    policy,
    predictions,
    predictions_v2,
    rule_sim,
    s_rank_engine,
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
    "doctrine_v2",
    "error_review",
    "error_replay",
    "indicators",
    "orders",
    "policy",
    "predictions",
    "predictions_v2",
    "rule_sim",
    "s_rank_engine",
    "self_repair",
    "signal_conflict",
    "strategy",
    "universe",
]
