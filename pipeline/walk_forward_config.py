"""
Walk-Forward 配置模組

定義 Walk-Forward 的時間切片與全局設定。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence


@dataclass(frozen=True)
class WalkForwardPeriod:
    """
    定義單一 Walk-Forward 週期的時間切片。
    
    時間全部用 float timestamp（秒）表示，和專案裡其他地方一致。
    
    train_start_ts < train_end_ts <= oos_start_ts < oos_end_ts
    """
    train_start_ts: float
    train_end_ts: float
    oos_start_ts: float
    oos_end_ts: float
    
    def __post_init__(self) -> None:
        if not (self.train_start_ts < self.train_end_ts):
            raise ValueError(
                f"Invalid train range: {self.train_start_ts} >= {self.train_end_ts}"
            )
        if not (self.train_end_ts <= self.oos_start_ts):
            raise ValueError(
                f"train_end_ts must be <= oos_start_ts "
                f"(train_end_ts={self.train_end_ts}, oos_start_ts={self.oos_start_ts})"
            )
        if not (self.oos_start_ts < self.oos_end_ts):
            raise ValueError(
                f"Invalid oos range: {self.oos_start_ts} >= {self.oos_end_ts}"
            )


@dataclass
class WalkForwardConfig:
    """
    Walk-Forward 模擬的全局配置。
    
    - target_symbols: 要模擬的標的清單（例如 ["2330.TW"]）
    - periods: 多個 WalkForwardPeriod，依時間順序排列
    - engine_config: 各引擎的初始化參數（目前主要用在 FSignalConfig）
    
    範例：
        {
            "CapitalFlowConfig": {...},   # 預留，當前版本可為空
            "InertiaWindowConfig": {...}, # 預留，當前版本可為空
            "FSignalConfig": {
                "w_sai": 0.4,
                "w_moi": 0.2,
                "w_inertia": 0.4,
                "strong_threshold": 0.4,
                "weak_threshold": 0.15,
            },
        }
    """
    target_symbols: Sequence[str]
    periods: List[WalkForwardPeriod] = field(default_factory=list)
    engine_config: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        if not self.target_symbols:
            raise ValueError("WalkForwardConfig.target_symbols cannot be empty")
        if not self.periods:
            raise ValueError("WalkForwardConfig.periods cannot be empty")
        
        # 確保 periods 依時間排序，且不重疊（最簡單版本：只檢查遞增）
        for i in range(1, len(self.periods)):
            prev = self.periods[i - 1]
            curr = self.periods[i]
            if prev.oos_end_ts > curr.train_start_ts:
                raise ValueError(
                    "WalkForward periods overlap or are out of order: "
                    f"prev.oos_end_ts={prev.oos_end_ts}, curr.train_start_ts={curr.train_start_ts}"
                )

