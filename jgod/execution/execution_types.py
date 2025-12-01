"""Execution Types v1

定義 Execution Engine 使用的資料結構類型。

Reference:
- docs/JGOD_EXECUTION_ENGINE_STANDARD_v1.md
- spec/JGOD_ExecutionEngine_Spec.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
import uuid


@dataclass
class Order:
    """交易訂單
    
    Attributes:
        order_id: 唯一訂單 ID
        symbol: 標的代碼
        side: 交易方向（"BUY" 或 "SELL"）
        quantity: 交易數量（股數）
        order_type: 訂單類型（"MARKET" 或 "LIMIT"）
        limit_price: 限價（如果是限價單）
        timestamp: 訂單時間戳
    """
    
    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: float
    order_type: str = "MARKET"
    limit_price: Optional[float] = None
    timestamp: Optional[datetime] = None
    order_id: Optional[str] = None
    
    def __post_init__(self):
        """初始化後處理"""
        if self.order_id is None:
            self.order_id = f"order_{uuid.uuid4().hex[:8]}"
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        # 驗證
        if self.side not in ["BUY", "SELL"]:
            raise ValueError(f"Invalid side: {self.side}. Must be 'BUY' or 'SELL'")
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be positive: {self.quantity}")


@dataclass
class Fill:
    """成交記錄
    
    Attributes:
        fill_id: 唯一成交 ID
        order_id: 對應的訂單 ID
        symbol: 標的代碼
        side: 交易方向
        filled_quantity: 實際成交數量
        fill_price: 實際成交價格（已含滑價）
        slippage: 滑價金額
        commission: 手續費
        tax: 稅費
        timestamp: 成交時間戳
    """
    
    order_id: str
    symbol: str
    side: str
    filled_quantity: float
    fill_price: float
    slippage: float = 0.0
    commission: float = 0.0
    tax: float = 0.0
    timestamp: Optional[datetime] = None
    fill_id: Optional[str] = None
    
    def __post_init__(self):
        """初始化後處理"""
        if self.fill_id is None:
            self.fill_id = f"fill_{uuid.uuid4().hex[:8]}"
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def total_cost(self) -> float:
        """總交易成本"""
        return self.commission + self.tax
    
    @property
    def trade_amount(self) -> float:
        """交易金額"""
        return self.filled_quantity * self.fill_price


@dataclass
class Trade:
    """完整交易記錄
    
    Attributes:
        trade_id: 唯一交易 ID
        order: 訂單物件
        fill: 成交物件
        total_cost: 總成本（手續費 + 稅費）
        net_amount: 淨交易金額
    """
    
    order: Order
    fill: Fill
    total_cost: Optional[float] = None
    net_amount: Optional[float] = None
    trade_id: Optional[str] = None
    
    def __post_init__(self):
        """初始化後處理"""
        if self.trade_id is None:
            self.trade_id = f"trade_{uuid.uuid4().hex[:8]}"
        if self.total_cost is None:
            self.total_cost = self.fill.total_cost
        if self.net_amount is None:
            # 淨交易金額 = 交易金額 + 成本（買入時）或 - 成本（賣出時）
            trade_amount = self.fill.trade_amount
            if self.fill.side == "BUY":
                self.net_amount = trade_amount + self.total_cost
            else:  # SELL
                self.net_amount = trade_amount - self.total_cost


@dataclass
class Position:
    """單一標的的持倉狀態
    
    Attributes:
        symbol: 標的代碼
        quantity: 持有數量（正數為多頭，負數為空頭）
        avg_price: 平均成本價格
        current_price: 當前市場價格
        market_value: 市值
        unrealized_pnl: 未實現損益
    """
    
    symbol: str
    quantity: float
    avg_price: float
    current_price: float = 0.0
    
    def __post_init__(self):
        """初始化後處理"""
        if self.current_price == 0.0:
            self.current_price = self.avg_price
    
    @property
    def market_value(self) -> float:
        """市值"""
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        """未實現損益"""
        cost_basis = self.quantity * self.avg_price
        return self.market_value - cost_basis
    
    def update_price(self, new_price: float) -> None:
        """更新當前價格"""
        self.current_price = new_price
    
    def add_quantity(self, additional_quantity: float, price: float) -> None:
        """增加持倉數量（更新平均成本）"""
        if self.quantity == 0:
            self.quantity = additional_quantity
            self.avg_price = price
        else:
            total_cost = (self.quantity * self.avg_price) + (additional_quantity * price)
            self.quantity += additional_quantity
            if self.quantity != 0:
                self.avg_price = total_cost / self.quantity
    
    def reduce_quantity(self, reduce_quantity: float) -> None:
        """減少持倉數量（平均成本不變）"""
        self.quantity -= reduce_quantity
        if abs(self.quantity) < 1e-6:  # 接近 0
            self.quantity = 0.0


@dataclass
class PortfolioState:
    """投資組合的完整狀態
    
    Attributes:
        positions: 所有持倉 {symbol: Position}
        cash: 現金餘額
        total_value: 總資產價值
        timestamp: 狀態時間戳
        turnover: 換手率
        transaction_costs: 總交易成本
    """
    
    positions: Dict[str, Position] = field(default_factory=dict)
    cash: float = 0.0
    timestamp: Optional[datetime] = None
    turnover: float = 0.0
    transaction_costs: float = 0.0
    
    def __post_init__(self):
        """初始化後處理"""
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def total_value(self) -> float:
        """總資產價值"""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return positions_value + self.cash
    
    @property
    def weights(self) -> Dict[str, float]:
        """權重字典"""
        total = self.total_value
        if total == 0:
            return {}
        return {
            symbol: pos.market_value / total
            for symbol, pos in self.positions.items()
            if pos.quantity != 0
        }
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """取得持倉（如果不存在返回 None）"""
        return self.positions.get(symbol)
    
    def update_position(self, symbol: str, position: Position) -> None:
        """更新或新增持倉"""
        self.positions[symbol] = position
    
    def remove_position(self, symbol: str) -> None:
        """移除持倉（數量為 0 時）"""
        if symbol in self.positions:
            del self.positions[symbol]
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """批量更新價格"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)

