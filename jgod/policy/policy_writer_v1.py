"""
J-GOD AI Policy Service v1 - Policy Writer

在 PolicyLogReaderV1 上，加一層：
從多個回測實驗中選出最佳組合 → 產生一份「建議版 RiskConfig 檔案」。

功能：
- 讀取回測實驗結果（透過 PolicyLogReaderV1）
- 選出最佳實驗（v1 版本直接取 Top 1）
- 產生 PolicySuggestion
- 寫出 YAML 格式的 RiskConfig 檔案

設計原則：
- 不動 Feature Store / Strategy / Decision / Path A
- 不動 Log Writer
- 包一層在 PolicyLogReaderV1 外面，不自己去讀檔案
"""

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from jgod.policy.policy_log_reader_v1 import (
    PolicyExperimentSummary,
    PolicyLogReaderV1,
    PolicyScoreConfig,
)


@dataclass
class PolicySuggestion:
    """
    Policy 建議（從最佳實驗來的風控參數組合）
    
    包含：
    - 來源實驗資訊（run_id, 日期區間等）
    - 績效指標
    - 建議的風控參數
    - 輸出檔案路徑（寫完檔案後填上）
    """
    # 來源資訊
    run_id: str
    created_at: datetime
    source_log_path: str
    start_date: str
    end_date: str
    
    # 績效指標
    score: float
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    win_rate: float
    num_days: int
    num_trades: int
    
    # 建議的風控參數
    long_budget: float
    short_budget: float
    max_weight_per_symbol: float
    min_score: float
    allow_short: bool
    
    # 輸出檔案路徑（寫完檔案後填上）
    output_path: Optional[str] = None
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "run_id": self.run_id,
            "created_at": self.created_at.isoformat(),
            "source_log_path": self.source_log_path,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "score": self.score,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "total_return": self.total_return,
            "win_rate": self.win_rate,
            "num_days": self.num_days,
            "num_trades": self.num_trades,
            "long_budget": self.long_budget,
            "short_budget": self.short_budget,
            "max_weight_per_symbol": self.max_weight_per_symbol,
            "min_score": self.min_score,
            "allow_short": self.allow_short,
            "output_path": self.output_path,
        }


class PolicyWriterV1:
    """
    Policy Writer v1
    
    核心功能：
    - 從多個回測實驗中選出最佳組合
    - 產生 PolicySuggestion
    - 寫出建議版 RiskConfig 檔案
    """
    
    def __init__(
        self,
        log_path: str = "data/path_a_backtest_logs.jsonl",
        score_config: Optional[PolicyScoreConfig] = None,
        min_days: int = 60,
        min_trades: int = 30,
    ):
        """
        初始化 Policy Writer
        
        Args:
            log_path: Log 檔案路徑
            score_config: 評分配置（如果為 None，使用預設配置）
            min_days: 最少交易日數
            min_trades: 最少總交易次數
        """
        # 建立 PolicyLogReaderV1（如果 score_config 沒有指定 min_days/min_trades，用傳入的參數更新）
        if score_config is None:
            score_config = PolicyScoreConfig(
                min_days=min_days,
                min_trades=min_trades,
            )
        else:
            # 如果傳入了 score_config，用它的值，但可以覆蓋 min_days/min_trades
            if min_days != 60:
                score_config.min_days = min_days
            if min_trades != 30:
                score_config.min_trades = min_trades
        
        self.reader = PolicyLogReaderV1(
            log_path=log_path,
            score_config=score_config,
        )
    
    def select_top_experiments(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        top_n: int = 10,
    ) -> List[PolicyExperimentSummary]:
        """
        選出 Top N 實驗摘要
        
        包一層，直接呼叫 PolicyLogReaderV1.filter_and_rank(...)
        
        Args:
            start_date: 開始日期（選填）
            end_date: 結束日期（選填）
            top_n: 回傳前 N 筆（預設 10）
        
        Returns:
            List[PolicyExperimentSummary]: 排序好的 Top N 實驗摘要
            若沒有任何有效實驗，回傳空 list，不丟例外
        """
        try:
            return self.reader.filter_and_rank(
                start_date=start_date,
                end_date=end_date,
                top_n=top_n,
            )
        except Exception as e:
            # 若發生錯誤（例如檔案不存在），回傳空 list
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to select top experiments: {e}")
            return []
    
    def generate_suggestion(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        top_k: int = 3,
    ) -> Optional[PolicySuggestion]:
        """
        從 Top K 實驗中選出最終建議的風控參數組合
        
        v1 策略：直接取排名第 1 筆
        
        Args:
            start_date: 開始日期（選填）
            end_date: 結束日期（選填）
            top_k: 從前 K 筆中選（v1 版本只用 Top 1）
        
        Returns:
            Optional[PolicySuggestion]: 建議的風控參數組合，若無有效實驗則回傳 None
        """
        # 1. 呼叫 select_top_experiments
        top_list = self.select_top_experiments(
            start_date=start_date,
            end_date=end_date,
            top_n=top_k,
        )
        
        # 2. 若結果為空 → 回傳 None
        if not top_list:
            return None
        
        # 3. 取 best = top_list[0]
        best = top_list[0]
        
        # 4. 建立 PolicySuggestion
        suggestion = PolicySuggestion(
            # run / meta
            run_id=best.run_id,
            created_at=datetime.now(),
            source_log_path=str(self.reader.log_path),
            start_date=best.start_date,
            end_date=best.end_date,
            # metrics
            score=best.score,
            sharpe_ratio=best.sharpe_ratio,
            max_drawdown=best.max_drawdown,
            total_return=best.total_return,
            win_rate=best.win_rate,
            num_days=best.num_days,
            num_trades=best.num_long_trades + best.num_short_trades,
            # config
            long_budget=best.long_budget or 0.6,
            short_budget=best.short_budget or 0.2,
            max_weight_per_symbol=best.max_weight_per_symbol or 0.1,
            min_score=best.min_score or 0.0,
            allow_short=best.allow_short if best.allow_short is not None else True,
        )
        
        return suggestion
    
    def write_risk_config_file(
        self,
        suggestion: PolicySuggestion,
        output_dir: str = "policy",
        file_name: Optional[str] = None,
    ) -> str:
        """
        將建議的風控參數寫成 YAML 風格的文字檔（不依賴 PyYAML），回傳實際寫入路徑
        
        Args:
            suggestion: PolicySuggestion 物件
            output_dir: 輸出目錄（預設 "policy"）
            file_name: 檔案名稱（如果為 None，使用預設名稱）
        
        Returns:
            str: 實際寫入的檔案路徑
        """
        # 1. 決定檔案名稱
        if file_name is None:
            file_name = "risk_config_suggested_v1.yaml"
        
        # 2. 確保 output_dir 存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 3. 組合完整路徑
        output_path = os.path.join(output_dir, file_name)
        
        # 4. 準備檔案內容（純文字 YAML 風格，直接用 f-string）
        content = f"""# Auto-generated by PolicyWriterV1
# created_at: {suggestion.created_at.isoformat()}
# source_log_path: {suggestion.source_log_path}
# source_run_id: {suggestion.run_id}

risk_version: 1

source:
  run_id: "{suggestion.run_id}"
  start_date: "{suggestion.start_date}"
  end_date: "{suggestion.end_date}"

metrics:
  score: {suggestion.score:.4f}
  sharpe_ratio: {suggestion.sharpe_ratio:.4f}
  max_drawdown: {suggestion.max_drawdown:.4f}
  total_return: {suggestion.total_return:.4f}
  win_rate: {suggestion.win_rate:.4f}
  num_days: {suggestion.num_days}
  num_trades: {suggestion.num_trades}

config:
  long_budget: {suggestion.long_budget:.2f}
  short_budget: {suggestion.short_budget:.2f}
  max_weight_per_symbol: {suggestion.max_weight_per_symbol:.2f}
  min_score: {suggestion.min_score:.2f}
  allow_short: {str(suggestion.allow_short).lower()}
"""
        
        # 5. 寫入檔案
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # 6. 更新 suggestion.output_path
        suggestion.output_path = output_path
        
        # 7. 回傳 output_path
        return output_path

