"""
風險管理器：管理最大虧損、最大持倉等風險限制
"""
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RiskLimits:
    """風險限制設定"""
    max_loss_per_trade: float = 0.02  # 單筆交易最大虧損比例（2%）
    max_total_loss: float = 0.10  # 總虧損上限（10%）
    max_position_size: float = 0.20  # 單一標的最大持倉比例（20%）
    max_total_exposure: float = 1.0  # 總曝險上限（100%）


@dataclass
class TradeRecord:
    """交易記錄"""
    symbol: str
    entry_price: float
    entry_time: datetime
    quantity: int
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl: float = 0.0
    pnl_percent: float = 0.0


class RiskManager:
    """
    風險管理器
    
    功能：
    - 檢查單筆交易風險
    - 追蹤總虧損
    - 限制最大持倉
    - 分散風險模型
    """
    
    def __init__(self, initial_capital: float, risk_limits: Optional[RiskLimits] = None):
        """
        初始化風險管理器
        
        Args:
            initial_capital: 初始資金
            risk_limits: 風險限制設定
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_limits = risk_limits or RiskLimits()
        self.trades: list[TradeRecord] = []
        self.positions: Dict[str, TradeRecord] = {}
    
    def can_open_position(
        self,
        symbol: str,
        price: float,
        quantity: int,
    ) -> tuple[bool, str]:
        """
        檢查是否可以開倉
        
        Args:
            symbol: 股票代號
            price: 價格
            quantity: 數量
        
        Returns:
            (是否可以開倉, 原因)
        """
        position_value = price * quantity
        
        # 檢查單一標的最大持倉
        max_position_value = self.current_capital * self.risk_limits.max_position_size
        if position_value > max_position_value:
            return False, f"超過單一標的最大持倉限制（{self.risk_limits.max_position_size*100:.1f}%）"
        
        # 檢查總曝險
        total_exposure = sum(
            pos.entry_price * pos.quantity
            for pos in self.positions.values()
        ) + position_value
        
        max_exposure = self.current_capital * self.risk_limits.max_total_exposure
        if total_exposure > max_exposure:
            return False, f"超過總曝險上限（{self.risk_limits.max_total_exposure*100:.1f}%）"
        
        # 檢查是否已有相同標的
        if symbol in self.positions:
            return False, f"標的 {symbol} 已有持倉"
        
        return True, "OK"
    
    def can_close_position(self, symbol: str) -> tuple[bool, str]:
        """
        檢查是否可以平倉
        
        Args:
            symbol: 股票代號
        
        Returns:
            (是否可以平倉, 原因)
        """
        if symbol not in self.positions:
            return False, f"標的 {symbol} 沒有持倉"
        return True, "OK"
    
    def open_position(
        self,
        symbol: str,
        price: float,
        quantity: int,
    ) -> bool:
        """
        開倉
        
        Args:
            symbol: 股票代號
            price: 價格
            quantity: 數量
        
        Returns:
            是否成功開倉
        """
        can_open, reason = self.can_open_position(symbol, price, quantity)
        if not can_open:
            print(f"無法開倉 {symbol}: {reason}")
            return False
        
        trade = TradeRecord(
            symbol=symbol,
            entry_price=price,
            entry_time=datetime.now(),
            quantity=quantity,
        )
        
        self.positions[symbol] = trade
        self.trades.append(trade)
        
        return True
    
    def close_position(
        self,
        symbol: str,
        price: float,
    ) -> Optional[TradeRecord]:
        """
        平倉
        
        Args:
            symbol: 股票代號
            price: 平倉價格
        
        Returns:
            交易記錄，如果失敗則回傳 None
        """
        can_close, reason = self.can_close_position(symbol)
        if not can_close:
            print(f"無法平倉 {symbol}: {reason}")
            return None
        
        trade = self.positions.pop(symbol)
        trade.exit_price = price
        trade.exit_time = datetime.now()
        
        # 計算損益
        pnl = (price - trade.entry_price) * trade.quantity
        pnl_percent = (price - trade.entry_price) / trade.entry_price
        
        trade.pnl = pnl
        trade.pnl_percent = pnl_percent
        
        # 更新資金
        self.current_capital += pnl
        
        return trade
    
    def get_total_pnl(self) -> float:
        """
        取得總損益
        
        Returns:
            總損益金額
        """
        return sum(trade.pnl for trade in self.trades)
    
    def get_total_pnl_percent(self) -> float:
        """
        取得總損益百分比
        
        Returns:
            總損益百分比
        """
        if self.initial_capital == 0:
            return 0.0
        return (self.current_capital - self.initial_capital) / self.initial_capital
    
    def check_risk_limits(self) -> tuple[bool, str]:
        """
        檢查是否超過風險限制
        
        Returns:
            (是否安全, 警告訊息)
        """
        total_pnl_percent = self.get_total_pnl_percent()
        
        if total_pnl_percent <= -self.risk_limits.max_total_loss:
            return False, f"總虧損已達上限（{total_pnl_percent*100:.2f}%）"
        
        return True, "OK"
    
    def get_position_summary(self) -> Dict[str, Dict]:
        """
        取得持倉摘要
        
        Returns:
            持倉摘要字典
        """
        summary = {}
        for symbol, trade in self.positions.items():
            summary[symbol] = {
                "entry_price": trade.entry_price,
                "quantity": trade.quantity,
                "value": trade.entry_price * trade.quantity,
            }
        return summary

