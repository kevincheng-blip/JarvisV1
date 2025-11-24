"""
虛擬券商：模擬股票交易執行
"""
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from .slippage import SlippageModel
from .trade_recorder import TradeRecorder


@dataclass
class Order:
    """訂單"""
    symbol: str
    side: str  # "buy" or "sell"
    quantity: int
    price: Optional[float] = None  # 如果為 None 則為市價單
    order_type: str = "market"  # "market" or "limit"
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Fill:
    """成交記錄"""
    order: Order
    filled_price: float
    filled_quantity: int
    filled_time: datetime
    slippage: float = 0.0
    commission: float = 0.0


class VirtualBroker:
    """
    虛擬券商
    
    功能：
    - 模擬股票交易執行
    - 處理滑價
    - 計算手續費
    - 記錄交易
    """
    
    def __init__(
        self,
        initial_cash: float = 1000000.0,
        commission_rate: float = 0.001425,  # 台股手續費率
        slippage_model: Optional[SlippageModel] = None,
        trade_recorder: Optional[TradeRecorder] = None,
    ):
        """
        初始化虛擬券商
        
        Args:
            initial_cash: 初始現金
            commission_rate: 手續費率
            slippage_model: 滑價模型
            trade_recorder: 交易記錄器
        """
        self.cash = initial_cash
        self.commission_rate = commission_rate
        self.slippage_model = slippage_model or SlippageModel()
        self.trade_recorder = trade_recorder or TradeRecorder()
        self.positions: Dict[str, int] = {}  # symbol -> quantity
        self.order_history: list[Order] = []
        self.fill_history: list[Fill] = []
    
    def submit_order(self, order: Order) -> Optional[Fill]:
        """
        提交訂單
        
        Args:
            order: 訂單
        
        Returns:
            成交記錄，如果失敗則回傳 None
        """
        self.order_history.append(order)
        
        # 取得成交價格（考慮滑價）
        if order.price is None:
            # 市價單：需要從市場取得當前價格（這裡簡化處理）
            fill_price = self._get_market_price(order.symbol)
            if fill_price is None:
                return None
        else:
            fill_price = order.price
        
        # 應用滑價
        fill_price = self.slippage_model.apply_slippage(
            fill_price,
            order.side,
            order.quantity,
        )
        
        # 計算手續費
        trade_value = fill_price * order.quantity
        commission = trade_value * self.commission_rate
        
        # 檢查資金/持倉
        if order.side == "buy":
            total_cost = trade_value + commission
            if total_cost > self.cash:
                return None
            self.cash -= total_cost
            self.positions[order.symbol] = self.positions.get(order.symbol, 0) + order.quantity
        else:  # sell
            if order.symbol not in self.positions or self.positions[order.symbol] < order.quantity:
                return None
            self.cash += trade_value - commission
            self.positions[order.symbol] -= order.quantity
            if self.positions[order.symbol] == 0:
                del self.positions[order.symbol]
        
        # 建立成交記錄
        fill = Fill(
            order=order,
            filled_price=fill_price,
            filled_quantity=order.quantity,
            filled_time=datetime.now(),
            slippage=abs(fill_price - (order.price or fill_price)),
            commission=commission,
        )
        
        self.fill_history.append(fill)
        
        # 記錄交易
        self.trade_recorder.record_trade(fill)
        
        return fill
    
    def _get_market_price(self, symbol: str) -> Optional[float]:
        """
        取得市場價格（簡化版，實際應該從市場資料取得）
        
        Args:
            symbol: 股票代號
        
        Returns:
            市場價格
        """
        # 這裡簡化處理，實際應該從市場資料引擎取得
        # 暫時回傳 None，需要整合市場資料
        return None
    
    def buy(
        self,
        symbol: str,
        quantity: int,
        price: Optional[float] = None,
    ) -> Optional[Fill]:
        """
        買入
        
        Args:
            symbol: 股票代號
            quantity: 數量
            price: 價格（如果為 None 則為市價單）
        
        Returns:
            成交記錄
        """
        order = Order(
            symbol=symbol,
            side="buy",
            quantity=quantity,
            price=price,
            order_type="limit" if price else "market",
        )
        return self.submit_order(order)
    
    def sell(
        self,
        symbol: str,
        quantity: int,
        price: Optional[float] = None,
    ) -> Optional[Fill]:
        """
        賣出
        
        Args:
            symbol: 股票代號
            quantity: 數量
            price: 價格（如果為 None 則為市價單）
        
        Returns:
            成交記錄
        """
        order = Order(
            symbol=symbol,
            side="sell",
            quantity=quantity,
            price=price,
            order_type="limit" if price else "market",
        )
        return self.submit_order(order)
    
    def get_cash(self) -> float:
        """取得當前現金"""
        return self.cash
    
    def get_positions(self) -> Dict[str, int]:
        """取得當前持倉"""
        return self.positions.copy()
    
    def get_account_summary(self) -> Dict[str, Any]:
        """取得帳戶摘要"""
        return {
            "cash": self.cash,
            "positions": self.positions.copy(),
            "num_positions": len(self.positions),
            "total_trades": len(self.fill_history),
        }

