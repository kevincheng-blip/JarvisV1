"""
Policy Reward Adapter v1

提供 RL / learning 模組使用 Path A 回測日誌作為 reward proxy 的介面。

設計目標：
- 將回測實驗結果轉換為標量 reward
- 供 RL 進行 Hyperparameter search、Policy search 使用
- 不修改現有 RL 核心邏輯，只提供適配層
"""

from dataclasses import dataclass
from typing import List, Optional

from jgod.policy.policy_log_reader_v1 import (
    PolicyScoreConfig,
    PolicyExperimentSummary,
    PolicyLogReaderV1,
)


@dataclass
class PolicyRewardSample:
    """
    單一 Policy Reward Sample
    
    代表一個 RiskConfig 組合對應的 reward。
    """
    run_id: str
    long_budget: float
    short_budget: float
    max_weight_per_symbol: float
    min_score: float
    allow_short: bool
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_days: int
    num_trades: int
    reward: float  # 最終標量 reward


class PolicyRewardAdapterV1:
    """
    Policy Reward Adapter v1
    
    將 Path A 回測日誌轉換為 RL 可使用的 reward samples。
    """
    
    def __init__(
        self,
        log_path: str = "data/path_a_backtest_logs.jsonl",
        score_config: Optional[PolicyScoreConfig] = None,
    ):
        """
        初始化 Policy Reward Adapter
        
        Args:
            log_path: 回測日誌檔案路徑
            score_config: PolicyScoreConfig（如果為 None，使用預設值）
        """
        self.log_path = log_path
        self.score_config = score_config or PolicyScoreConfig()
        self.reader = PolicyLogReaderV1(log_path=log_path, score_config=self.score_config)
    
    def load_samples(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_days: Optional[int] = None,
        min_trades: Optional[int] = None,
    ) -> List[PolicyRewardSample]:
        """
        載入 Policy Reward Samples
        
        Args:
            start_date: 開始日期（YYYY-MM-DD）
            end_date: 結束日期（YYYY-MM-DD）
            min_days: 最小交易日數（如果為 None，使用 score_config.min_days）
            min_trades: 最小交易次數（如果為 None，使用 score_config.min_trades）
        
        Returns:
            PolicyRewardSample 列表（已按 reward 排序，從高到低）
        """
        # 使用 PolicyLogReaderV1 載入並過濾實驗
        # 先臨時覆蓋 min_days 和 min_trades（如果提供）
        original_min_days = self.score_config.min_days
        original_min_trades = self.score_config.min_trades
        
        if min_days is not None:
            self.score_config.min_days = min_days
        if min_trades is not None:
            self.score_config.min_trades = min_trades
        
        try:
            # 載入所有有效實驗（不限制 top_n，讓它返回所有符合條件的）
            experiments = self.reader.filter_and_rank(
                start_date=start_date,
                end_date=end_date,
                top_n=10000,  # 足夠大的數字，確保返回所有符合條件的
            )
            
            # 轉換為 PolicyRewardSample
            samples = []
            for exp in experiments:
                # 計算 reward（使用與 PolicyLogReaderV1 相同的計分邏輯）
                # reward = sharpe_weight * sharpe_ratio - max_dd_weight * max_drawdown
                reward = (
                    self.score_config.sharpe_weight * exp.sharpe_ratio
                    - self.score_config.max_dd_weight * exp.max_drawdown
                )
                
                sample = PolicyRewardSample(
                    run_id=exp.run_id,
                    long_budget=exp.long_budget or 0.0,
                    short_budget=exp.short_budget or 0.0,
                    max_weight_per_symbol=exp.max_weight_per_symbol or 0.0,
                    min_score=exp.min_score or 0.0,
                    allow_short=exp.allow_short if exp.allow_short is not None else True,
                    total_return=exp.total_return,
                    sharpe_ratio=exp.sharpe_ratio,
                    max_drawdown=exp.max_drawdown,
                    win_rate=exp.win_rate,
                    num_days=exp.num_days,
                    num_trades=exp.num_long_trades + exp.num_short_trades,
                    reward=reward,
                )
                samples.append(sample)
            
            # 按 reward 排序（從高到低）
            samples.sort(key=lambda x: x.reward, reverse=True)
            
            return samples
        
        finally:
            # 恢復原始值
            self.score_config.min_days = original_min_days
            self.score_config.min_trades = original_min_trades
    
    def find_best_reward(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_days: Optional[int] = None,
        min_trades: Optional[int] = None,
    ) -> Optional[PolicyRewardSample]:
        """
        找出最佳 reward sample
        
        Args:
            start_date: 開始日期（YYYY-MM-DD）
            end_date: 結束日期（YYYY-MM-DD）
            min_days: 最小交易日數
            min_trades: 最小交易次數
        
        Returns:
            最佳 PolicyRewardSample，如果沒有符合條件的則返回 None
        """
        samples = self.load_samples(
            start_date=start_date,
            end_date=end_date,
            min_days=min_days,
            min_trades=min_trades,
        )
        
        if not samples:
            return None
        
        return samples[0]  # 已經按 reward 排序，第一個就是最好的

