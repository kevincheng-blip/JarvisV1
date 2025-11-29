"""訊號引擎模組

詳見 spec/JGOD_Python_Interface_Spec.md 的 Signal Engine 章節。
未來實作需參考 structured_books/J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, Any, Literal, Dict, List, Optional
from enum import Enum
import pandas as pd


class SignalType(Enum):
    """訊號類型
    
    詳見 spec/JGOD_Python_Interface_Spec.md
    """
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    EXIT = "exit"
    NONE = "none"


@dataclass
class TradingSignal:
    """交易訊號資料結構
    
    詳見 spec/JGOD_Python_Interface_Spec.md 的 Signal 類別。
    對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
    對應概念：Watchlist 欄位設計（Setup_Condition、Entry_Price_Plan、Stop_Loss_Price、Target_Price）
    """
    signal_type: SignalType
    symbol: str
    confidence: float  # 0-1 信心分數
    strategy_tag: str  # 策略標籤（主流突破、強勢回檔等）
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None


class BaseSignalModel(ABC):
    """訊號模型基類
    
    詳見 spec/JGOD_Python_Interface_Spec.md 的 SignalEngine 章節。
    對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
    對應概念：六大武功策略（主流突破、強勢回檔、主力反轉、逆勢突襲、急攻狙擊、爆量警戒）
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化訊號引擎
        
        詳見 spec/JGOD_Python_Interface_Spec.md
        """
        self.config = config
        self.active_strategies: List[str] = []
    
    def compute_signals(self,
                       market_data: pd.DataFrame,
                       factors: Dict[str, float],
                       indicators: Optional[pd.DataFrame] = None) -> List[TradingSignal]:
        """根據因子與市場資料生成交易訊號
        
        詳見 spec/JGOD_Python_Interface_Spec.md 的 compute_signals 方法。
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：六大武功進場條件（Rules_Entry）與出場條件（Rules_Exit）
        """
        pass
    
    def check_entry_condition(self,
                             symbol: str,
                             strategy_tag: str,
                             market_data: pd.DataFrame,
                             factors: Dict[str, float]) -> bool:
        """檢查進場條件
        
        詳見 spec/JGOD_Python_Interface_Spec.md 的 check_entry_condition 方法。
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：六大武功 Rules_Entry（進場條件）
        """
        pass
    
    def check_exit_condition(self,
                            symbol: str,
                            strategy_tag: str,
                            current_position: Dict[str, Any],
                            market_data: pd.DataFrame) -> bool:
        """檢查出場條件
        
        詳見 spec/JGOD_Python_Interface_Spec.md 的 check_exit_condition 方法。
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：六大武功 Rules_Exit（出場條件）、Stop_Loss（停損）
        """
        pass

