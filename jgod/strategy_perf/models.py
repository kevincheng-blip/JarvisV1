"""
Strategy Performance Feed Data Models

Defines data structures for strategy performance evaluation.
"""

import uuid
from datetime import datetime, date
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class PerformanceGrade(str, Enum):
    """Performance grade enum"""
    NO_DATA = "NO_DATA"
    GOOD = "GOOD"
    WATCH = "WATCH"
    BAD = "BAD"


@dataclass
class StrategyPerformanceMetrics:
    """Performance metrics for a single strategy"""
    strategy_id: str
    n_points: int
    avg_return_proxy: float
    sharpe_proxy: float
    max_drawdown_proxy: float
    turnover_proxy: float
    decay_slope: float
    grade: PerformanceGrade


@dataclass
class PerformanceSnapshot:
    """Complete performance snapshot for a symbol"""
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    symbol: str = ""
    limit: int = 60
    window: int = 20  # Window for decay calculation
    items: List[StrategyPerformanceMetrics] = field(default_factory=list)

