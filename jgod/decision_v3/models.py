"""
Decision Engine V3 Data Models

Defines data structures for Decision V3 (Rule-based × S-Rank V2 × Performance Feed).
"""

from datetime import date
from typing import List, Optional, Dict, Literal
from dataclasses import dataclass, field


@dataclass
class StrategyWeight:
    """Strategy weight with optional grade and metrics"""
    strategy_id: str
    weight: float
    grade: Optional[str] = None  # "GOOD" | "WATCH" | "BAD" | "NO_DATA"
    metrics: Optional[Dict[str, float]] = None  # e.g., {"sharpe_proxy": 0.85, "max_drawdown_proxy": 0.12}
    rationale: Optional[str] = None


@dataclass
class RiskPlan:
    """Risk management plan"""
    position_scale: float  # 0.0 ~ 1.0
    risk_state: Literal["RISK_ON", "RISK_OFF", "CAUTION"]
    reasons: List[str] = field(default_factory=list)


@dataclass
class DecisionV3Result:
    """Decision V3 result"""
    symbol: str
    as_of_date: Optional[date] = None
    selected_primary_strategy: Optional[str] = None
    selected_secondary_strategies: List[str] = field(default_factory=list)
    weights: List[StrategyWeight] = field(default_factory=list)
    risk_plan: Optional[RiskPlan] = None
    confidence: float = 0.0  # 0.0 ~ 1.0
    explain: str = ""  # Traditional Chinese, <= 10 lines

