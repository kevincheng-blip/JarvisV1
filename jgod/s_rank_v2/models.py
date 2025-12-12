"""
S-Rank Engine V2 Data Models

Defines data structures for strategy recommendation system.
"""

import uuid
from datetime import datetime, date
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum


class StabilityGrade(str, Enum):
    """Stability grade enum"""
    NO_DATA = "NO_DATA"
    STABLE = "STABLE"
    WATCH = "WATCH"
    VOLATILE = "VOLATILE"


@dataclass
class Metrics:
    """Metrics computed from prediction timeline"""
    n_points: int
    score_std: float
    max_abs_delta: float
    trend_slope: float
    stability_grade: StabilityGrade


@dataclass
class RecommendationItem:
    """Single strategy recommendation item"""
    strategy: str  # e.g., "trend_follow", "mean_reversion"
    weight: float  # Normalized weight (0.0 ~ 1.0)
    score: float   # Raw strategy score (before softmax)


@dataclass
class RecommendationSnapshot:
    """Complete recommendation snapshot"""
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    symbol: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    items: List[RecommendationItem] = field(default_factory=list)
    weights: Dict[str, float] = field(default_factory=dict)  # strategy -> weight
    metrics: Optional[Metrics] = None
    rationale: Dict[str, str] = field(default_factory=dict)  # strategy -> rationale text

