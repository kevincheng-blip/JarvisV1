"""Decision AB Test Data Models

Defines data structures for AB test results.
"""

from datetime import date, datetime
from typing import List, Dict, Any, Optional
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


# ============================================================================
# V1 vs V2 Decision AB Test Models (New)
# ============================================================================

class ArmBacktestResult(BaseModel):
    """單一 Decision 版本（手臂）的回測結果"""
    version: str  # 'v1' or 'v2'
    sharpe_ratio: float
    max_drawdown: float  # 負值，如 -0.15 代表 -15%
    total_return: float  # 總報酬，例如 0.25 = +25%
    volatility: float  # 年化波動度
    win_rate: float  # 勝率 (0~1)
    turnover: float  # 換手率
    equity_curve: List[Dict[str, Any]] = []  # [{"date": "2024-01-01", "equity": 1000000}, ...]


class DecisionABTestReport(BaseModel):
    """Decision V1 vs V2 的 AB 測試報告"""
    experiment_id: str
    created_at: datetime
    config: Dict[str, Any]  # 包含 start_date, end_date, capital, path_a_config_name 等
    
    baseline: ArmBacktestResult  # V1 結果
    variant: ArmBacktestResult  # V2 結果
    
    sharpe_delta: float
    max_drawdown_delta: float
    return_delta: float
    volatility_delta: float
    win_rate_delta: float
    turnover_delta: float
    
    recommendation: str  # "V2_PREFERRED", "NO_SIGNIFICANT_CHANGE", "V1_PREFERRED"
    notes: Optional[str] = None

