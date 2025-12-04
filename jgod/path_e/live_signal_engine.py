"""
Live Signal Engine for Path E

根據當前市場狀況與投資組合狀態，生成交易決策（目標權重）。

v1 實作簡單 placeholder 策略，未來會整合 Path D policy。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List
import pandas as pd
import numpy as np

from jgod.path_e.live_types import LiveBar, LiveDecision
from jgod.path_e.portfolio_state import PortfolioState


class LiveSignalEngine(ABC):
    """即時訊號引擎抽象介面"""
    
    @abstractmethod
    def generate_decision(
        self,
        portfolio_state: PortfolioState,
        latest_bars: Dict[str, LiveBar],
    ) -> LiveDecision:
        """
        生成交易決策
        
        Args:
            portfolio_state: 當前投資組合狀態
            latest_bars: 最新 bar 資料 {symbol: LiveBar}
        
        Returns:
            LiveDecision（目標權重）
        """
        ...


class PlaceholderSignalEngine(LiveSignalEngine):
    """
    Placeholder 策略引擎（v1）
    
    實作簡單策略，用於測試 Path E 框架。
    
    v1 策略：
    - 全部持有現金（target_weights = {}）
    
    未來會替換為 Path D policy 整合的策略。
    """
    
    def __init__(self, strategy_type: str = "cash_only"):
        """
        初始化 Placeholder 策略引擎
        
        Args:
            strategy_type: 策略類型
                - "cash_only": 全部持有現金
                - "simple_ma": 簡單均線策略（若 close > MA 則持有小部位）
        """
        self.strategy_type = strategy_type
        self.ma_period = 20  # 均線週期（用於 simple_ma 策略）
        self.position_size = 0.1  # 持有部位大小（用於 simple_ma 策略）
        
        # 用於計算均線的歷史資料（簡單版本，只保留最近 N 筆）
        self.price_history: Dict[str, List[float]] = {}
    
    def generate_decision(
        self,
        portfolio_state: PortfolioState,
        latest_bars: Dict[str, LiveBar],
    ) -> LiveDecision:
        """
        生成交易決策
        
        Args:
            portfolio_state: 當前投資組合狀態
            latest_bars: 最新 bar 資料
        
        Returns:
            LiveDecision
        """
        if self.strategy_type == "cash_only":
            return self._cash_only_strategy(portfolio_state, latest_bars)
        elif self.strategy_type == "simple_ma":
            return self._simple_ma_strategy(portfolio_state, latest_bars)
        else:
            # 預設：全部持有現金
            return LiveDecision(
                target_weights={},
                meta={"strategy_type": "cash_only", "reason": "unknown_strategy"},
            )
    
    def _cash_only_strategy(
        self,
        portfolio_state: PortfolioState,
        latest_bars: Dict[str, LiveBar],
    ) -> LiveDecision:
        """現金策略：全部持有現金"""
        return LiveDecision(
            target_weights={},
            meta={
                "strategy_type": "cash_only",
                "reason": "v1 placeholder strategy",
            },
        )
    
    def _simple_ma_strategy(
        self,
        portfolio_state: PortfolioState,
        latest_bars: Dict[str, LiveBar],
    ) -> LiveDecision:
        """
        簡單均線策略：若當前 close > N 日均線，則持有小部位
        """
        target_weights = {}
        
        for symbol, bar in latest_bars.items():
            # 更新價格歷史
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            self.price_history[symbol].append(bar.close)
            
            # 只保留最近 N 筆
            if len(self.price_history[symbol]) > self.ma_period * 2:
                self.price_history[symbol] = self.price_history[symbol][-self.ma_period:]
            
            # 計算均線
            if len(self.price_history[symbol]) >= self.ma_period:
                ma = np.mean(self.price_history[symbol][-self.ma_period:])
                
                # 若當前 close > 均線，則持有小部位
                if bar.close > ma:
                    target_weights[symbol] = self.position_size
        
        return LiveDecision(
            target_weights=target_weights,
            meta={
                "strategy_type": "simple_ma",
                "ma_period": self.ma_period,
                "position_size": self.position_size,
            },
        )

