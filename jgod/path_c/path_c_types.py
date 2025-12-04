"""
Path C v1 - Type Definitions

This module defines all data structures used by Path C Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal, Any
from datetime import datetime


# Type aliases
ModeType = Literal["basic", "extreme"]
DataSourceType = Literal["mock", "finmind"]


@dataclass
class PathCScenarioConfig:
    """
    Path C Scenario Configuration
    
    定義一個完整的測試場景，包含所有必要的參數。
    每個 Scenario 會被轉換為 Path B Config 並執行。
    """
    
    # 基本資訊
    name: str
    description: str
    
    # Path B / Path A 相關設定
    start_date: str  # "YYYY-MM-DD" - 整體實驗開始日期
    end_date: str    # "YYYY-MM-DD" - 整體實驗結束日期
    rebalance_frequency: str  # "D", "W", "M"
    universe: List[str]  # 股票代號列表
    
    # Path B 相關設定
    walkforward_window: str  # "6m", "1y" 等
    walkforward_step: str    # "1m", "3m" 等
    
    # 系統模式
    data_source: DataSourceType = "mock"
    mode: ModeType = "basic"
    
    # 治理門檻（可以覆寫 Path B 預設值）
    max_drawdown_limit: Optional[float] = None  # 例如 -0.15
    min_sharpe: Optional[float] = None          # 例如 2.0
    max_tracking_error: Optional[float] = None  # 例如 0.04
    max_turnover: Optional[float] = None        # 例如 1.0
    
    # Alpha Engine 配置（可選）
    alpha_config_set: Optional[List[Dict[str, Any]]] = None
    
    # Governance Rules（可選）
    governance_rules: Optional[Dict[str, Any]] = None
    
    # Tag 用於報表分類
    regime_tag: Optional[str] = None  # 例如 "bull", "bear", "covid", "post_qe"
    metadata: Dict[str, str] = field(default_factory=dict)
    
    # 其他 Path A 設定
    initial_nav: float = 100.0
    transaction_cost_bps: float = 5.0
    slippage_bps: float = 0.0


@dataclass
class PathCScenarioResult:
    """
    Path C Scenario Execution Result
    
    包含從 Path B Engine 回來的關鍵數字，用於排名與比較。
    """
    
    scenario: PathCScenarioConfig
    
    # 從 Path B Engine 回來的關鍵數字
    sharpe: float  # 平均 Sharpe Ratio
    max_drawdown: float  # 最大回撤
    total_return: float  # 總報酬
    governance_breach_ratio: float  # Governance breach 比例 (0.0 - 1.0)
    governance_breach_count: int  # Governance breach 次數
    windows_count: int  # 總共幾個 window
    
    # 原始 Path B 結果（或其子集）
    raw_path_b_summary: Dict  # Path B summary 字典
    raw_governance_summary: Dict  # Path B governance summary 字典
    
    # 執行資訊
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None
    
    # 其他可選指標
    avg_tracking_error: Optional[float] = None
    avg_turnover: Optional[float] = None


@dataclass
class PathCExperimentConfig:
    """
    Path C Experiment Configuration
    
    定義一個完整的實驗，包含多個 scenario。
    """
    
    name: str
    scenarios: List[PathCScenarioConfig]
    output_dir: str = "output/path_c"
    
    # 實驗元資料
    description: Optional[str] = None
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class PathCRunSummary:
    """
    Path C Run Summary
    
    包含所有 scenario 的執行結果、排名、最佳 scenario 等。
    """
    
    experiment_name: str
    scenarios: List[PathCScenarioResult]
    ranking_table: List[Dict]  # 已排序好的 scenario 排名列表
    best_scenarios: List[str]  # 名稱清單（例如前 3 名）
    created_at: str  # ISO format datetime string
    
    # 完整配置快照（序列化結果）
    config_snapshot: Dict
    
    # 實驗統計
    total_scenarios: int = 0
    successful_scenarios: int = 0
    failed_scenarios: int = 0
    
    # 輸出檔案路徑
    output_files: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """自動計算統計數字"""
        if self.total_scenarios == 0:
            self.total_scenarios = len(self.scenarios)
        
        if self.successful_scenarios == 0:
            self.successful_scenarios = sum(
                1 for s in self.scenarios if s.error_message is None
            )
        
        if self.failed_scenarios == 0:
            self.failed_scenarios = self.total_scenarios - self.successful_scenarios

