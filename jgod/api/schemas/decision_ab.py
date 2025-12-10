"""Decision AB Test API Schemas

Pydantic models for Decision AB Test API endpoints.
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ArmMetricsSchema(BaseModel):
    """Performance metrics for a single arm"""
    sharpe: float
    max_drawdown: float
    total_return: float
    win_rate: float
    avg_trade_return: float
    num_trades: int
    turnover: float
    vol_annualized: float


class ArmResultSchema(BaseModel):
    """Results for a single test arm"""
    experiment_id: str
    mode: str
    start_date: date
    end_date: date
    metrics: ArmMetricsSchema


class DecisionAbResultSchema(BaseModel):
    """Complete AB test result"""
    experiment_id: str
    created_at: datetime
    raw_only: ArmResultSchema
    decision_on: ArmResultSchema
    delta_sharpe: float
    delta_max_drawdown: float
    delta_total_return: float
    delta_win_rate: float
    delta_turnover: float


# ============================================================================
# V1 vs V2 Decision AB Test Schemas (New)
# ============================================================================

class ArmBacktestResultSchema(BaseModel):
    """單一 Decision 版本的回測結果 Schema"""
    version: str
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    volatility: float
    win_rate: float
    turnover: float
    equity_curve: List[Dict[str, Any]] = []


class DecisionComparisonRequestSchema(BaseModel):
    """Decision V1 vs V2 AB Test 請求 Schema"""
    start_date: date
    end_date: date
    capital: float = 1_000_000
    path_a_config_name: str
    note: Optional[str] = None


class DecisionABTestReportSchema(BaseModel):
    """Decision V1 vs V2 AB Test 報告 Schema"""
    experiment_id: str
    created_at: datetime
    config: Dict[str, Any]
    baseline: ArmBacktestResultSchema
    variant: ArmBacktestResultSchema
    sharpe_delta: float
    max_drawdown_delta: float
    return_delta: float
    volatility_delta: float
    win_rate_delta: float
    turnover_delta: float
    recommendation: str
    notes: Optional[str] = None


class DecisionABTestReportSummarySchema(BaseModel):
    """Decision AB Test 報告概要（用於列表）"""
    experiment_id: str
    created_at: datetime
    path_a_config_name: str
    sharpe_delta: float
    return_delta: float
    max_drawdown_delta: float
    recommendation: str

