"""
Order Planner for Path E

根據目標權重與當前持倉，計算需要執行的訂單（買/賣多少股）。
"""

from __future__ import annotations

from typing import List, Dict
import pandas as pd
import numpy as np

from jgod.path_e.live_types import PlannedOrder
from jgod.path_e.portfolio_state import PortfolioState


class OrderPlanner:
    """
    訂單規劃器
    
    根據目標權重與當前持倉，計算需要執行的訂單。
    """
    
    def plan_orders(
        self,
        portfolio_state: PortfolioState,
        target_weights: Dict[str, float],
        latest_prices: Dict[str, float],
    ) -> List[PlannedOrder]:
        """
        規劃訂單
        
        Args:
            portfolio_state: 當前投資組合狀態
            target_weights: 目標權重 {symbol: weight}
            latest_prices: 最新價格 {symbol: price}
        
        Returns:
            計劃的訂單列表
        """
        orders = []
        equity = portfolio_state.equity
        current_ts = portfolio_state.timestamp
        
        # 對於每個有目標權重的標的
        for symbol, target_weight in target_weights.items():
            if symbol not in latest_prices:
                continue
            
            price = latest_prices[symbol]
            
            # 計算目標持倉價值與股數
            target_value = equity * target_weight
            target_qty = int(target_value / price)  # 向下取整
            
            # 取得當前持倉
            current_qty = portfolio_state.positions.get(symbol, 0)
            
            # 計算需要調整的股數
            delta_qty = target_qty - current_qty
            
            if delta_qty > 0:
                # 需要買入
                orders.append(PlannedOrder(
                    symbol=symbol,
                    side="buy",
                    qty=delta_qty,
                    price_type="market",
                    ts=current_ts,
                ))
            elif delta_qty < 0:
                # 需要賣出
                orders.append(PlannedOrder(
                    symbol=symbol,
                    side="sell",
                    qty=abs(delta_qty),
                    price_type="market",
                    ts=current_ts,
                ))
            # 如果 delta_qty == 0，不需要下單
        
        # 處理不在 target_weights 中的持倉（全部賣出）
        for symbol, current_qty in portfolio_state.positions.items():
            if symbol not in target_weights and current_qty > 0:
                if symbol in latest_prices:
                    orders.append(PlannedOrder(
                        symbol=symbol,
                        side="sell",
                        qty=current_qty,
                        price_type="market",
                        ts=current_ts,
                    ))
        
        return orders

