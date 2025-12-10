"""S-Rank Factor Engine Data Models

Defines data structures for strategy performance evaluation and ranking.
"""

from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass, field
from pydantic import BaseModel


@dataclass
class StrategyPerformanceSnapshot:
    """Snapshot of strategy performance metrics"""
    strategy_id: str  # e.g., "S1", "S2"
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    avg_holding_period_days: int
    last_run_date: date
    is_active: bool = True
    market_correlation: float = 0.0


@dataclass
class SignalQualityFactors:
    """Signal quality evaluation factors"""
    signal_strength_confidence: float  # Past N signals win rate
    factor_decay_rate: float  # How quickly factor effectiveness decays
    consistency_score: float  # Consistency of performance


@dataclass
class SRankFactor:
    """S-Rank factor for a strategy"""
    strategy_id: str
    performance_snapshot: StrategyPerformanceSnapshot
    quality_factors: SignalQualityFactors
    s_rank_score: float  # 0.0 ~ 1.0
    rank_level: str  # "S" | "A" | "B" | "C" | "D"
    calculated_at: datetime = field(default_factory=datetime.now)


class SRankFactorPydantic(BaseModel):
    """Pydantic model for API serialization"""
    strategy_id: str
    performance_snapshot: dict
    quality_factors: dict
    s_rank_score: float
    rank_level: str
    calculated_at: datetime
    
    class Config:
        from_attributes = True

