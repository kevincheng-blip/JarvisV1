"""
Path A v1 - Schema Definitions

This module defines the core data structures used by the Path A
(Validation Lab) pipeline. It should remain light and free of
heavy dependencies or business logic.

Path A is responsible for:
- Defining the experiment configuration
- Describing the shapes of inputs / features / predictions / portfolio states
- Providing type hints for the Path A backtest engine
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd


# ---------------------------------------------------------------------------
# 1. Core configuration
# ---------------------------------------------------------------------------

@dataclass
class PathAConfig:
    """
    Configuration for a Path A experiment.
    
    This config should be created by the caller (CLI / notebook / script)
    and passed into the Path A pipeline.
    """
    
    start_date: str  # "YYYY-MM-DD"
    end_date: str  # "YYYY-MM-DD"
    universe: Sequence[str]  # list of symbols, e.g. TW50 constituents
    rebalance_frequency: str = "M"  # "M" (monthly), "W" (weekly), etc.
    lookback_window_days: int = 252  # for risk model & feature building
    benchmark_symbol: Optional[str] = None  # e.g. market index
    initial_nav: float = 100.0
    transaction_cost_bps: float = 5.0  # per side, in basis points
    slippage_bps: float = 0.0
    max_weight_per_symbol: float = 0.1
    min_weight_per_symbol: float = 0.0
    allow_short: bool = False
    
    # Optional tags / metadata for logging & reproducibility
    experiment_name: str = "path_a_experiment"
    tags: Dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# 2. Input data structures
# ---------------------------------------------------------------------------

@dataclass
class PathADailyInput:
    """
    Raw daily input for a given date and universe.
    
    This is the lowest-level "what we got from the data loader"
    representation, typically built from FinMind or other sources.
    
    All fields are pandas Series indexed by symbol.
    """
    
    date: pd.Timestamp
    symbols: List[str]
    
    # Price-related
    open: pd.Series
    high: pd.Series
    low: pd.Series
    close: pd.Series
    volume: pd.Series
    
    # Optional fields for chips / fundamentals etc.
    foreign_net: Optional[pd.Series] = None
    investment_trust_net: Optional[pd.Series] = None
    dealer_net: Optional[pd.Series] = None
    margin_balance: Optional[pd.Series] = None
    short_balance: Optional[pd.Series] = None
    pe: Optional[pd.Series] = None
    pb: Optional[pd.Series] = None
    roe: Optional[pd.Series] = None
    roa: Optional[pd.Series] = None
    market_cap: Optional[pd.Series] = None
    
    # Any additional, pre-computed features can be attached here.
    extra_features: Dict[str, pd.Series] = field(default_factory=dict)


@dataclass
class PathAFeatureFrame:
    """
    Feature matrix for the entire experiment window.
    
    This is typically a MultiIndex DataFrame:
        index: [date, symbol]
        columns: feature names
    
    But we keep it generic and just model it as a DataFrame here.
    """
    
    features: pd.DataFrame  # multi-index or (date, symbol) columns
    feature_names: List[str]


# ---------------------------------------------------------------------------
# 3. Predictions & portfolio states
# ---------------------------------------------------------------------------

@dataclass
class PathAPrediction:
    """
    Prediction snapshot for a single date across the entire universe.
    
    This is typically derived from AlphaEngine's composite_alpha.
    """
    
    date: pd.Timestamp
    symbols: List[str]
    
    # e.g. composite alpha or standardized expected return
    scores: pd.Series
    
    # Optional: store factor exposures / additional info if available
    extra: Dict[str, pd.Series] = field(default_factory=dict)


@dataclass
class PathAPortfolioSnapshot:
    """
    Portfolio state at a given date.
    
    Contains:
    - Weights per symbol
    - NAV (portfolio value)
    - Per-symbol and total returns for that date
    - Optional diagnostic information (factor exposure, TE, etc.)
    """
    
    date: pd.Timestamp
    symbols: List[str]
    weights: pd.Series  # portfolio weights at the end of the day
    nav: float
    
    # realized return for this date (portfolio-level)
    portfolio_return: float
    
    # per-symbol realized returns for this date (if needed)
    symbol_returns: Optional[pd.Series] = None
    
    # Optional diagnostics
    factor_exposure: Optional[pd.Series] = None
    tracking_error: Optional[float] = None
    extra: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# 4. Backtest results and error events
# ---------------------------------------------------------------------------

@dataclass
class PathABacktestResult:
    """
    Aggregate result of a Path A backtest run.
    
    This object is intentionally simple; consumers (e.g. reporting / plotting
    modules) can build richer views on top of it.
    """
    
    config: PathAConfig
    
    # Time series of NAV and returns
    nav_series: pd.Series  # indexed by date
    return_series: pd.Series  # indexed by date
    
    # Portfolio snapshots (e.g. at rebalance dates or daily)
    portfolio_snapshots: List[PathAPortfolioSnapshot]
    
    # Optional trade list (symbol, date, trade size, etc.)
    trades: Optional[pd.DataFrame] = None
    
    # Optional: list of ErrorEvent objects or their serialized forms
    error_events: Optional[List[object]] = None
    
    # Optional: any summary statistics (Sharpe, max drawdown, etc.)
    summary_stats: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# 5. Type aliases / helper types
# ---------------------------------------------------------------------------

# Rebalance schedule: list of dates at which we rebalance
RebalanceSchedule = List[pd.Timestamp]

# Convenient alias for (date, symbol) identifier
DateSymbol = Tuple[pd.Timestamp, str]

