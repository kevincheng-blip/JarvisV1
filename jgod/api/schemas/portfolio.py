"""
Portfolio API Schemas

v0.6.10-A10: Pydantic schemas for portfolio endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class PortfolioRunRequestSchema(BaseModel):
    """Portfolio run request schema."""
    symbols: List[str] = Field(..., description="List of stock symbols")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_cash_total: float = Field(1_000_000.0, description="Total initial cash")
    allocation_mode: str = Field("equal_weight", description="Allocation mode: equal_weight or vol_parity")
    autopilot_enabled: bool = Field(False, description="Enable autopilot")
    doctrine_version: str = Field("v1.0", description="Doctrine version")
    feature_version: str = Field("v1.0", description="Feature version")


class PortfolioReportSchema(BaseModel):
    """Portfolio report schema."""
    date: str
    portfolio_nav: float
    portfolio_cash: float
    portfolio_pnl_realized: float
    portfolio_pnl_unrealized: float
    per_symbol_nav: Dict[str, float]
    per_symbol_pnl: Dict[str, float]
    per_symbol_cash: Dict[str, float]
    notes: str = ""


class PortfolioLogListSchema(BaseModel):
    """Portfolio log list response schema."""
    logs: List[PortfolioReportSchema]
    total: int

