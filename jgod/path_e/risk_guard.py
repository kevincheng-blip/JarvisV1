"""
Risk Guard for Path E

過濾不符合風險要求的交易指令。
"""

from __future__ import annotations

from typing import List, Dict
import logging

from jgod.path_e.live_types import PlannedOrder
from jgod.path_e.portfolio_state import PortfolioState


logger = logging.getLogger(__name__)


class RiskGuard:
    """
    風險守衛
    
    過濾不符合風險要求的交易指令。
    
    v1 基本規則：
    1. 單檔最大部位不超過淨值 X%
    2. 單筆下單金額不超過淨值 Y%
    """
    
    def __init__(
        self,
        max_position_pct: float = 0.2,
        max_order_pct: float = 0.05,
    ):
        """
        初始化 RiskGuard
        
        Args:
            max_position_pct: 單檔最大部位不超過淨值百分比（例如 0.2 = 20%）
            max_order_pct: 單筆下單金額不超過淨值百分比（例如 0.05 = 5%）
        """
        self.max_position_pct = max_position_pct
        self.max_order_pct = max_order_pct
    
    def filter_orders(
        self,
        portfolio_state: PortfolioState,
        proposed_orders: List[PlannedOrder],
        latest_prices: Dict[str, float],
    ) -> List[PlannedOrder]:
        """
        過濾訂單
        
        Args:
            portfolio_state: 當前投資組合狀態
            proposed_orders: 計劃的訂單列表
            latest_prices: 最新價格 {symbol: price}
        
        Returns:
            過濾後的訂單列表
        """
        filtered_orders = []
        equity = portfolio_state.equity
        
        for order in proposed_orders:
            if order.symbol not in latest_prices:
                logger.warning(f"Symbol {order.symbol} not in latest_prices, skipping order")
                continue
            
            price = latest_prices[order.symbol]
            order_value = order.qty * price
            
            # 規則 1: 單筆下單金額不超過淨值 Y%
            if order_value > equity * self.max_order_pct:
                logger.warning(
                    f"Order filtered: order_value {order_value:.2f} > "
                    f"max_order_pct {equity * self.max_order_pct:.2f}"
                )
                continue
            
            # 規則 2: 單檔最大部位不超過淨值 X%
            if order.side == "buy":
                # 計算買入後的新持倉價值
                current_qty = portfolio_state.positions.get(order.symbol, 0)
                new_qty = current_qty + order.qty
                new_position_value = new_qty * price
                
                if new_position_value > equity * self.max_position_pct:
                    logger.warning(
                        f"Order filtered: new_position_value {new_position_value:.2f} > "
                        f"max_position_pct {equity * self.max_position_pct:.2f}"
                    )
                    continue
            
            # 通過過濾
            filtered_orders.append(order)
        
        return filtered_orders

