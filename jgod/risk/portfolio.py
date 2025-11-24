"""
投資組合管理器：管理多個標的的持倉
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd


@dataclass
class Position:
    """持倉資訊"""
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    entry_time: datetime
    unrealized_pnl: float = 0.0
    unrealized_pnl_percent: float = 0.0


class Portfolio:
    """
    投資組合管理器
    
    功能：
    - 管理多個標的的持倉
    - 計算投資組合總價值
    - 計算未實現損益
    - 分散風險分析
    """
    
    def __init__(self, initial_cash: float = 1000000.0):
        """
        初始化投資組合
        
        Args:
            initial_cash: 初始現金
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Dict] = []
    
    def add_position(
        self,
        symbol: str,
        quantity: int,
        price: float,
    ) -> bool:
        """
        新增持倉
        
        Args:
            symbol: 股票代號
            quantity: 數量
            price: 價格
        
        Returns:
            是否成功
        """
        cost = quantity * price
        if cost > self.cash:
            return False
        
        if symbol in self.positions:
            # 更新現有持倉
            pos = self.positions[symbol]
            total_quantity = pos.quantity + quantity
            total_cost = (pos.avg_price * pos.quantity) + cost
            pos.avg_price = total_cost / total_quantity
            pos.quantity = total_quantity
        else:
            # 新增持倉
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=price,
                current_price=price,
                entry_time=datetime.now(),
            )
        
        self.cash -= cost
        
        # 記錄交易
        self.trade_history.append({
            "timestamp": datetime.now(),
            "action": "buy",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
        })
        
        return True
    
    def remove_position(
        self,
        symbol: str,
        quantity: int,
        price: float,
    ) -> bool:
        """
        減少持倉
        
        Args:
            symbol: 股票代號
            quantity: 數量
            price: 價格
        
        Returns:
            是否成功
        """
        if symbol not in self.positions:
            return False
        
        pos = self.positions[symbol]
        if quantity > pos.quantity:
            return False
        
        # 更新持倉
        pos.quantity -= quantity
        if pos.quantity == 0:
            del self.positions[symbol]
        
        # 更新現金
        self.cash += quantity * price
        
        # 記錄交易
        self.trade_history.append({
            "timestamp": datetime.now(),
            "action": "sell",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
        })
        
        return True
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """
        更新標的價格
        
        Args:
            prices: 標的代號到價格的映射
        """
        for symbol, price in prices.items():
            if symbol in self.positions:
                pos = self.positions[symbol]
                pos.current_price = price
                pos.unrealized_pnl = (price - pos.avg_price) * pos.quantity
                pos.unrealized_pnl_percent = (price - pos.avg_price) / pos.avg_price
    
    def get_total_value(self) -> float:
        """
        取得投資組合總價值
        
        Returns:
            總價值（現金 + 持倉價值）
        """
        positions_value = sum(
            pos.current_price * pos.quantity
            for pos in self.positions.values()
        )
        return self.cash + positions_value
    
    def get_unrealized_pnl(self) -> float:
        """
        取得未實現損益
        
        Returns:
            未實現損益
        """
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    def get_total_return(self) -> float:
        """
        取得總報酬率
        
        Returns:
            總報酬率（百分比）
        """
        if self.initial_cash == 0:
            return 0.0
        return (self.get_total_value() - self.initial_cash) / self.initial_cash
    
    def get_position_weights(self) -> Dict[str, float]:
        """
        取得各標的的權重
        
        Returns:
            標的代號到權重的映射
        """
        total_value = self.get_total_value()
        if total_value == 0:
            return {}
        
        weights = {}
        for symbol, pos in self.positions.items():
            position_value = pos.current_price * pos.quantity
            weights[symbol] = position_value / total_value
        
        return weights
    
    def get_summary(self) -> Dict:
        """
        取得投資組合摘要
        
        Returns:
            投資組合摘要字典
        """
        return {
            "cash": self.cash,
            "positions_value": sum(
                pos.current_price * pos.quantity
                for pos in self.positions.values()
            ),
            "total_value": self.get_total_value(),
            "unrealized_pnl": self.get_unrealized_pnl(),
            "total_return": self.get_total_return(),
            "num_positions": len(self.positions),
            "position_weights": self.get_position_weights(),
        }

