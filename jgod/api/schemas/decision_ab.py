"""Decision AB Test API Schemas

Pydantic models for Decision AB Test API endpoints.
"""

from datetime import datetime, date
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

