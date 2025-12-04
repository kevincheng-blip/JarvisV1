"""
Portfolio State for Path E

追蹤投資組合的當前狀態（現金、持倉、淨值、損益等）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional
import pandas as pd
import numpy as np

from jgod.path_e.live_types import PlannedOrder


@dataclass
class PortfolioState:
    """投資組合狀態"""
    
    cash: float
    positions: Dict[str, int]  # {symbol: quantity}
    equity: float  # 總淨值
    pnl: float  # 損益
    max_drawdown: float
    timestamp: pd.Timestamp
    initial_cash: float = field(default=0.0)
    equity_high_water_mark: float = field(default=0.0)  # 用於計算 max_drawdown
    
    def __post_init__(self):
        """初始化"""
        if self.initial_cash == 0.0:
            self.initial_cash = self.cash
        if self.equity_high_water_mark == 0.0:
            self.equity_high_water_mark = self.equity
    
    def revalue(self, market_prices: Dict[str, float]) -> None:
        """
        根據市場價格重新計算淨值
        
        Args:
            market_prices: {symbol: price} 字典
        """
        # 計算持倉價值
        position_value = 0.0
        for symbol, qty in self.positions.items():
            if symbol in market_prices and qty > 0:
                position_value += qty * market_prices[symbol]
        
        # 總淨值 = 現金 + 持倉價值
        self.equity = self.cash + position_value
        
        # 計算損益
        self.pnl = self.equity - self.initial_cash
        
        # 更新高水位線與最大回撤
        if self.equity > self.equity_high_water_mark:
            self.equity_high_water_mark = self.equity
        
        if self.equity_high_water_mark > 0:
            drawdown = (self.equity - self.equity_high_water_mark) / self.equity_high_water_mark
            self.max_drawdown = min(self.max_drawdown, drawdown)
    
    def update_from_fill(self, order: PlannedOrder, fill_price: float, commission: float = 0.0) -> None:
        """
        根據成交記錄更新狀態
        
        Args:
            order: 訂單
            fill_price: 成交價格
            commission: 手續費
        """
        cost = order.qty * fill_price + commission
        
        if order.side == "buy":
            # 買入：減少現金，增加持倉
            self.cash -= cost
            current_qty = self.positions.get(order.symbol, 0)
            self.positions[order.symbol] = current_qty + order.qty
        else:
            # 賣出：增加現金，減少持倉
            self.cash += cost - commission
            current_qty = self.positions.get(order.symbol, 0)
            new_qty = current_qty - order.qty
            if new_qty <= 0:
                # 全部賣出或做空（v1 不支援做空，但保留邏輯）
                self.positions.pop(order.symbol, None)
            else:
                self.positions[order.symbol] = new_qty
    
    def get_position_value(self, symbol: str, price: float) -> float:
        """
        取得某標的的持倉價值
        
        Args:
            symbol: 標的代碼
            price: 當前價格
        
        Returns:
            持倉價值
        """
        qty = self.positions.get(symbol, 0)
        return qty * price
    
    def get_total_value(self, market_prices: Dict[str, float]) -> float:
        """
        取得總淨值
        
        Args:
            market_prices: {symbol: price} 字典
        
        Returns:
            總淨值
        """
        position_value = 0.0
        for symbol, qty in self.positions.items():
            if symbol in market_prices:
                position_value += qty * market_prices[symbol]
        return self.cash + position_value
    
    def get_position_weight(self, symbol: str, price: float) -> float:
        """
        取得某標的的持倉權重
        
        Args:
            symbol: 標的代碼
            price: 當前價格
        
        Returns:
            持倉權重（0.0 - 1.0）
        """
        if self.equity <= 0:
            return 0.0
        position_value = self.get_position_value(symbol, price)
        return position_value / self.equity

