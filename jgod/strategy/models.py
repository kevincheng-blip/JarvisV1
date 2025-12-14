"""
Portfolio Models: Data structures for Portfolio Manager

v0.6.10-A10: Portfolio configuration, allocation, and daily logs
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal


@dataclass
class PortfolioConfig:
    """Portfolio configuration."""
    symbols: List[str]
    initial_cash_total: float
    allocation_mode: Literal["equal_weight", "vol_parity"] = "equal_weight"
    risk_budget: Optional[Dict] = None  # Optional risk budget constraints
    doctrine_version: str = "v1.0"
    feature_version: str = "v1.0"
    feature_lookback: int = 60
    vol_lookback: int = 20  # For vol_parity calculation


@dataclass
class AllocationResult:
    """Capital allocation result."""
    per_symbol_cash: Dict[str, float]  # {symbol: cash_amount}
    weights: Dict[str, float]  # {symbol: weight (0.0 ~ 1.0)}
    method: str  # "equal_weight" or "vol_parity"
    notes: str = ""  # Allocation rationale


@dataclass
class PortfolioDailyLog:
    """Portfolio daily log entry."""
    date: str  # YYYY-MM-DD
    portfolio_nav: float
    portfolio_cash: float
    portfolio_pnl_realized: float
    portfolio_pnl_unrealized: float
    per_symbol_nav: Dict[str, float]  # {symbol: nav}
    per_symbol_pnl: Dict[str, float]  # {symbol: total_pnl}
    per_symbol_cash: Dict[str, float]  # {symbol: cash}
    notes: str = ""  # Portfolio-level notes

