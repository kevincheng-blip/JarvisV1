"""
J-GOD Policy Service v1 - API Schemas

定義 Policy Service API 的 Request / Response 資料結構。
"""

from typing import Optional
from pydantic import BaseModel, Field


class PolicyExperimentHistoryItem(BaseModel):
    """
    政策實驗歷史項目
    
    用於 Policy Evolution Panel，顯示實驗的完整資訊。
    """
    run_id: str = Field(..., description="實驗 Run ID")
    timestamp: str = Field(..., description="實驗時間戳記 (ISO format)")
    start_date: str = Field(..., description="回測開始日期")
    end_date: str = Field(..., description="回測結束日期")
    score: float = Field(..., description="政策評分")
    sharpe_ratio: float = Field(..., description="Sharpe Ratio")
    max_drawdown: float = Field(..., description="最大回撤")
    total_return: float = Field(..., description="總報酬率")
    win_rate: float = Field(..., description="勝率")
    num_days: int = Field(..., description="交易日數")
    num_trades: int = Field(..., description="總交易次數")
    long_budget: Optional[float] = Field(None, description="Long 部位預算")
    short_budget: Optional[float] = Field(None, description="Short 部位預算")
    max_weight_per_symbol: Optional[float] = Field(None, description="單檔最大權重")
    min_score: Optional[float] = Field(None, description="最低分數門檻")
    allow_short: Optional[bool] = Field(None, description="是否允許放空")
    tag: Optional[str] = Field(None, description="實驗標籤")

    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "abc123def456",
                "timestamp": "2024-12-01T10:00:00",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "score": 0.85,
                "sharpe_ratio": 1.33,
                "max_drawdown": 0.08,
                "total_return": 0.20,
                "win_rate": 0.55,
                "num_days": 252,
                "num_trades": 120,
                "long_budget": 0.6,
                "short_budget": 0.2,
                "max_weight_per_symbol": 0.1,
                "min_score": 0.0,
                "allow_short": True,
                "tag": "policy_v2_round1"
            }
        }


class PolicyActiveConfig(BaseModel):
    """
    當前生效的 RiskConfig
    
    從 YAML 檔案載入的配置資訊。
    """
    file_path: str = Field(..., description="配置檔案路徑")
    exists: bool = Field(..., description="檔案是否存在")
    risk_version: Optional[int] = Field(None, description="風險配置版本號")
    run_id: Optional[str] = Field(None, description="來源實驗 Run ID")
    start_date: Optional[str] = Field(None, description="來源實驗開始日期")
    end_date: Optional[str] = Field(None, description="來源實驗結束日期")
    long_budget: Optional[float] = Field(None, description="Long 部位預算")
    short_budget: Optional[float] = Field(None, description="Short 部位預算")
    max_weight_per_symbol: Optional[float] = Field(None, description="單檔最大權重")
    min_score: Optional[float] = Field(None, description="最低分數門檻")
    allow_short: Optional[bool] = Field(None, description="是否允許放空")
    sharpe_ratio: Optional[float] = Field(None, description="來源實驗 Sharpe Ratio")
    max_drawdown: Optional[float] = Field(None, description="來源實驗 Max Drawdown")
    total_return: Optional[float] = Field(None, description="來源實驗 Total Return")
    win_rate: Optional[float] = Field(None, description="來源實驗 Win Rate")

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "policy/risk_config_suggested_v1.yaml",
                "exists": True,
                "risk_version": 1,
                "run_id": "abc123def456",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "long_budget": 0.6,
                "short_budget": 0.2,
                "max_weight_per_symbol": 0.1,
                "min_score": 0.0,
                "allow_short": True,
                "sharpe_ratio": 1.33,
                "max_drawdown": 0.08,
                "total_return": 0.20,
                "win_rate": 0.55
            }
        }

