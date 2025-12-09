"""Replay Report Data Models

Defines the data structures for error replay reports.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ReplayMeta(BaseModel):
    """Replay metadata"""
    error_id: str
    symbol: str
    date: date
    timeframe: str = Field(default="daily", description="'daily' or 'intraday'")
    error_type: Optional[str] = None
    human_summary: Optional[str] = None
    pnl_impact: Optional[float] = None


class PricePoint(BaseModel):
    """Price data point"""
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class FactorPoint(BaseModel):
    """Factor/scores data point"""
    ts: datetime
    raw_score: Optional[float] = None
    final_score: Optional[float] = None
    factor_values: Dict[str, float] = Field(default_factory=dict, description="e.g., {'momentum': 0.8, 'volatility': 0.3}")


class TradePoint(BaseModel):
    """Trade execution point"""
    ts: datetime
    action: str = Field(..., description="'BUY' or 'SELL'")
    price: float
    quantity: float


class ReplayDiagnosis(BaseModel):
    """Diagnostic analysis of the error"""
    root_cause: str = Field(..., description="Brief text explaining the root cause")
    contributing_factors: List[str] = Field(default_factory=list, description="List of contributing factors")
    missed_signals: List[str] = Field(default_factory=list, description="Signals that should have been noticed")
    doctrine_refs: List[str] = Field(default_factory=list, description="e.g., ['Book_03#S12', 'Book_08#R21']")


class ReplayReport(BaseModel):
    """Complete replay report"""
    meta: ReplayMeta
    price_series: List[PricePoint] = Field(default_factory=list)
    factor_series: List[FactorPoint] = Field(default_factory=list)
    trades: List[TradePoint] = Field(default_factory=list)
    diagnosis: ReplayDiagnosis

