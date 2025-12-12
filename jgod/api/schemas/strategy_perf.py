"""
Strategy Performance Feed API Schemas

Pydantic models for Strategy Performance API endpoints.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from jgod.strategy_perf.models import PerformanceSnapshot, StrategyPerformanceMetrics, PerformanceGrade


class StrategyPerformanceMetricsSchema(BaseModel):
    """Strategy performance metrics schema"""
    strategy_id: str
    n_points: int
    avg_return_proxy: float
    sharpe_proxy: float
    max_drawdown_proxy: float
    turnover_proxy: float
    decay_slope: float
    grade: str  # "NO_DATA" | "GOOD" | "WATCH" | "BAD"

    class Config:
        from_attributes = True


class PerformanceSnapshotResponseSchema(BaseModel):
    """Response schema for performance snapshot"""
    snapshot_id: str
    created_at: datetime
    symbol: str
    limit: int
    window: int
    items: List[StrategyPerformanceMetricsSchema]

    class Config:
        from_attributes = True


def snapshot_to_response_schema(snapshot: PerformanceSnapshot) -> PerformanceSnapshotResponseSchema:
    """Convert PerformanceSnapshot to response schema"""
    return PerformanceSnapshotResponseSchema(
        snapshot_id=snapshot.snapshot_id,
        created_at=snapshot.created_at,
        symbol=snapshot.symbol,
        limit=snapshot.limit,
        window=snapshot.window,
        items=[
            StrategyPerformanceMetricsSchema(
                strategy_id=item.strategy_id,
                n_points=item.n_points,
                avg_return_proxy=item.avg_return_proxy,
                sharpe_proxy=item.sharpe_proxy,
                max_drawdown_proxy=item.max_drawdown_proxy,
                turnover_proxy=item.turnover_proxy,
                decay_slope=item.decay_slope,
                grade=item.grade.value,
            )
            for item in snapshot.items
        ],
    )

