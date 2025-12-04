"""
Path E - Type Definitions

定義 Path E Live Trading Engine 使用的所有資料結構。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal, Any
from datetime import datetime
import pandas as pd


@dataclass
class LiveBar:
    """即時 K 線資料"""
    symbol: str
    ts: pd.Timestamp  # 時間戳記
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class LiveDecision:
    """交易決策"""
    target_weights: Dict[str, float]  # 目標權重 {symbol: weight}
    meta: Dict[str, Any] = field(default_factory=dict)  # 額外資訊（策略類型、信心度等）


@dataclass
class PlannedOrder:
    """計劃中的訂單"""
    symbol: str
    side: Literal["buy", "sell"]
    qty: int  # 股數
    price_type: Literal["market", "limit"] = "market"
    ts: pd.Timestamp = field(default_factory=lambda: pd.Timestamp.now())
    limit_price: Optional[float] = None  # 限價單價格


@dataclass
class PathEConfig:
    """Path E Engine 配置"""
    
    # 模式設定
    mode: Literal["DRY_RUN", "PAPER", "LIVE"]  # v1 只支援 DRY_RUN, PAPER
    
    # 交易標的
    symbols: List[str]  # 例如 ["2330", "2317", "2454"]
    
    # 初始資金
    initial_cash: float = 1000000.0
    
    # 風險限制
    max_position_pct: float = 0.2  # 單檔最大部位不超過淨值 X%
    max_order_pct: float = 0.05    # 單筆下單金額不超過淨值 Y%
    
    # 資料來源設定
    data_feed_type: Literal["mock", "live"] = "mock"  # v1 只支援 mock
    bar_interval: str = "1d"  # 資料頻率（"1d", "1h", "5m" 等）
    
    # 策略設定（v1 為 placeholder）
    signal_engine_type: str = "placeholder"
    
    # 執行設定
    execution_mode: Literal["sim", "real"] = "sim"  # v1 只支援 sim
    
    # 日誌設定
    log_dir: str = "logs/path_e"
    
    # 實驗名稱
    experiment_name: str = "path_e_experiment"


@dataclass
class Fill:
    """成交記錄"""
    order: PlannedOrder
    filled_price: float
    filled_quantity: int
    filled_time: pd.Timestamp
    slippage: float = 0.0
    commission: float = 0.0

