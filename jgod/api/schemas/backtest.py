"""
J-GOD Backtest Service v1 - API Schemas

定義 Backtest Service API 的 Request / Response 資料結構。
"""

from typing import Optional
from pydantic import BaseModel, Field


class PathABacktestRequest(BaseModel):
    """
    Path A 回測請求
    
    包含所有執行回測所需的參數。
    """
    start_date: str = Field(..., description="回測開始日期 (YYYY-MM-DD)")
    end_date: str = Field(..., description="回測結束日期 (YYYY-MM-DD)")
    capital: float = Field(default=1_000_000.0, description="初始資金")
    long_budget: float = Field(default=0.6, description="Long 部位預算 (0.0-1.0)")
    short_budget: float = Field(default=0.2, description="Short 部位預算 (0.0-1.0)")
    max_weight_per_symbol: float = Field(default=0.1, description="單檔最大權重 (0.0-1.0)")
    min_score: float = Field(default=0.0, description="最低分數門檻")
    allow_short: bool = Field(default=True, description="是否允許放空")
    risk_config_file: Optional[str] = Field(
        default=None,
        description="RiskConfig YAML 檔案路徑（若提供，會覆蓋部分參數）"
    )
    tag: Optional[str] = Field(
        default=None,
        description="實驗標籤（用於標記本次實驗，未來可寫進 log）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "capital": 1000000.0,
                "long_budget": 0.6,
                "short_budget": 0.2,
                "max_weight_per_symbol": 0.1,
                "min_score": 0.0,
                "allow_short": True,
                "risk_config_file": None,
                "tag": "api_test_001"
            }
        }


class PathABacktestSummary(BaseModel):
    """
    Path A 回測結果摘要
    
    回傳給前端／外部服務用的精簡版績效摘要。
    """
    run_id: Optional[str] = Field(default=None, description="實驗 Run ID（若寫入 log 則有值）")
    start_date: str = Field(..., description="回測開始日期")
    end_date: str = Field(..., description="回測結束日期")
    initial_capital: float = Field(..., description="初始資金")
    final_capital: float = Field(..., description="最終淨值")
    total_return: float = Field(..., description="總報酬率")
    annualized_return: float = Field(..., description="年化報酬率")
    annualized_volatility: float = Field(..., description="年化波動率")
    sharpe_ratio: float = Field(..., description="Sharpe Ratio")
    max_drawdown: float = Field(..., description="最大回撤")
    win_rate: float = Field(..., description="勝率")
    num_days: int = Field(..., description="交易日數")
    num_trades: int = Field(..., description="總交易次數")
    long_trades: int = Field(..., description="Long 交易次數")
    short_trades: int = Field(..., description="Short 交易次數")

    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "abc123def456",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "initial_capital": 1000000.0,
                "final_capital": 1200000.0,
                "total_return": 0.20,
                "annualized_return": 0.20,
                "annualized_volatility": 0.15,
                "sharpe_ratio": 1.33,
                "max_drawdown": 0.08,
                "win_rate": 0.55,
                "num_days": 252,
                "num_trades": 120,
                "long_trades": 80,
                "short_trades": 40
            }
        }


class PathABacktestResponse(BaseModel):
    """
    Path A 回測 API 回應
    
    包含原始請求與回測結果摘要。
    """
    request: PathABacktestRequest = Field(..., description="原始請求參數")
    summary: PathABacktestSummary = Field(..., description="回測結果摘要")

    class Config:
        json_schema_extra = {
            "example": {
                "request": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "capital": 1000000.0,
                    "long_budget": 0.6,
                    "short_budget": 0.2,
                    "max_weight_per_symbol": 0.1,
                    "min_score": 0.0,
                    "allow_short": True,
                    "risk_config_file": None,
                    "tag": "api_test_001"
                },
                "summary": {
                    "run_id": "abc123def456",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "initial_capital": 1000000.0,
                    "final_capital": 1200000.0,
                    "total_return": 0.20,
                    "annualized_return": 0.20,
                    "annualized_volatility": 0.15,
                    "sharpe_ratio": 1.33,
                    "max_drawdown": 0.08,
                    "win_rate": 0.55,
                    "num_days": 252,
                    "num_trades": 120,
                    "long_trades": 80,
                    "short_trades": 40
                }
            }
        }

