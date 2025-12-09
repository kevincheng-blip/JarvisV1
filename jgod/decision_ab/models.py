"""Decision AB Test Data Models

Defines data structures for AB test results.
"""

from datetime import date, datetime
from pydantic import BaseModel


class ArmMetrics(BaseModel):
    """Performance metrics for a single arm (mode)"""
    sharpe: float
    max_drawdown: float
    total_return: float
    win_rate: float
    avg_trade_return: float
    num_trades: int
    turnover: float
    vol_annualized: float


class ArmResult(BaseModel):
    """Results for a single test arm"""
    experiment_id: str
    mode: str  # "RAW_ONLY" or "DECISION_ON"
    path_a_config_id: str
    decision_config_id: str | None
    start_date: date
    end_date: date
    metrics: ArmMetrics


class DecisionAbResult(BaseModel):
    """Complete AB test result comparing RAW_ONLY vs DECISION_ON"""
    experiment_id: str
    created_at: datetime
    raw_only: ArmResult
    decision_on: ArmResult
    
    # Delta metrics (convenience fields for frontend)
    delta_sharpe: float
    delta_max_drawdown: float
    delta_total_return: float
    delta_win_rate: float
    delta_turnover: float


class DecisionAbExperimentConfig(BaseModel):
    """Configuration for a single AB experiment"""
    experiment_id: str
    description: str
    start_date: date
    end_date: date
    universe: str | None = None
    path_a_config_id: str
    decision_config_id: str | None = None
    run_modes: list[str] = ["RAW_ONLY", "DECISION_ON"]

