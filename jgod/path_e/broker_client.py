"""
Broker Client for Path E

執行交易指令（提交訂單、查詢成交狀態等）。

v1 實作 SimBrokerClient，模擬券商，只更新 PortfolioState，不呼叫任何外部 API。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, Optional
import pandas as pd
import logging

from jgod.path_e.live_types import PlannedOrder, Fill


logger = logging.getLogger(__name__)


class BrokerClient(Protocol):
    """券商客戶端介面"""
    
    def submit_order(self, order: PlannedOrder, current_price: float) -> Optional[Fill]:
        """
        提交訂單
        
        Args:
            order: 訂單
            current_price: 當前市價
        
        Returns:
            成交記錄，如果失敗則回傳 None
        """
        ...


class SimBrokerClient:
    """
    模擬券商客戶端（v1）
    
    立即假設訂單以當前市價成交，計算滑價與手續費，並更新 PortfolioState。
    不呼叫任何外部 API。
    """
    
    def __init__(
        self,
        commission_rate: float = 0.001425,  # 台股手續費率 0.1425%
        slippage_bps: float = 5.0,  # 滑價（basis points，例如 5 bps = 0.05%）
    ):
        """
        初始化 SimBrokerClient
        
        Args:
            commission_rate: 手續費率（例如 0.001425 = 0.1425%）
            slippage_bps: 滑價（basis points，例如 5.0 = 5 bps = 0.05%）
        """
        self.commission_rate = commission_rate
        self.slippage_bps = slippage_bps
    
    def submit_order(self, order: PlannedOrder, current_price: float) -> Optional[Fill]:
        """
        提交訂單（模擬執行）
        
        Args:
            order: 訂單
            current_price: 當前市價
        
        Returns:
            成交記錄
        """
        # 計算滑價
        slippage_pct = self.slippage_bps / 10000.0  # 轉換為小數
        if order.side == "buy":
            # 買入：價格往上滑
            fill_price = current_price * (1.0 + slippage_pct)
        else:
            # 賣出：價格往下滑
            fill_price = current_price * (1.0 - slippage_pct)
        
        # 計算手續費
        trade_value = order.qty * fill_price
        commission = trade_value * self.commission_rate
        
        # 建立成交記錄
        fill = Fill(
            order=order,
            filled_price=fill_price,
            filled_quantity=order.qty,
            filled_time=order.ts,
            slippage=abs(fill_price - current_price),
            commission=commission,
        )
        
        logger.info(
            f"Order filled: {order.symbol} {order.side} {order.qty} @ {fill_price:.2f} "
            f"(slippage: {fill.slippage:.2f}, commission: {commission:.2f})"
        )
        
        return fill

