"""S-Rank Factor Engine API Schemas

Pydantic models for S-Rank API endpoints.
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel


class SRankCalculateRequest(BaseModel):
    """Request to calculate S-Rank factors"""
    time_horizon_days: int = 90
    force_recalculate: bool = False


class SRankCalculateResponse(BaseModel):
    """Response for S-Rank calculation"""
    run_at: datetime
    strategy_count: int
    time_horizon_days: int


class StrategyPerformanceSnapshotSchema(BaseModel):
    """Strategy performance snapshot schema"""
    strategy_id: str
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    avg_holding_period_days: int
    last_run_date: str
    is_active: bool
    market_correlation: float


class SignalQualityFactorsSchema(BaseModel):
    """Signal quality factors schema"""
    signal_strength_confidence: float
    factor_decay_rate: float
    consistency_score: float


class SRankFactorSchema(BaseModel):
    """S-Rank factor schema"""
    strategy_id: str
    performance_snapshot: StrategyPerformanceSnapshotSchema
    quality_factors: SignalQualityFactorsSchema
    s_rank_score: float
    rank_level: str
    calculated_at: datetime

