"""Execution Engine v1

J-GOD Execution Engine 核心類別，負責將目標權重轉換為實際交易執行。

Reference:
- docs/JGOD_EXECUTION_ENGINE_STANDARD_v1.md
- spec/JGOD_ExecutionEngine_Spec.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from .execution_types import (
    Order, Fill, Trade, Position, PortfolioState
)
from .execution_models import ExecutionModel
from .cost_model import CostModel
from .broker_adapter import BrokerAdapter, MockBrokerAdapter


@dataclass
class ExecutionRequest:
    """執行請求資料結構"""
    
    target_weights: Dict[str, float]      # 目標權重 {symbol: weight}
    prev_portfolio_state: PortfolioState  # 前一期組合狀態
    prices: Dict[str, float]              # 當前價格 {symbol: price}
    volumes: Optional[Dict[str, float]] = None  # 日成交量 {symbol: volume}
    cost_params: Optional[Dict[str, any]] = None    # 成本參數
    slippage_params: Optional[Dict[str, any]] = None  # 滑價參數


@dataclass
class ExecutionResult:
    """執行結果資料結構"""
    
    trades: List[Trade]                    # 所有交易記錄
    fills: List[Fill]                      # 所有成交記錄
    new_portfolio_state: PortfolioState    # 更新後的組合狀態
    turnover: float                        # 換手率
    transaction_costs: float               # 總交易成本
    diagnostics: Dict[str, any]            # 診斷資訊


class ExecutionEngine:
    """Execution Engine 核心類別
    
    負責將目標權重轉換為實際交易執行，包含：
    - 生成交易訂單
    - 套用滑價模型
    - 計算交易成本
    - 更新投資組合狀態
    """
    
    def __init__(
        self,
        execution_model: ExecutionModel,
        cost_model: CostModel,
        broker_adapter: Optional[BrokerAdapter] = None,
        min_trade_threshold: float = 0.001  # 最小交易權重門檻
    ):
        """初始化 Execution Engine
        
        Args:
            execution_model: 滑價模型
            cost_model: 成本模型
            broker_adapter: 券商介面（可選，預設使用 MockBrokerAdapter）
            min_trade_threshold: 最小交易權重門檻（低於此值忽略）
        """
        self.execution_model = execution_model
        self.cost_model = cost_model
        self.broker_adapter = broker_adapter or MockBrokerAdapter()
        self.min_trade_threshold = min_trade_threshold
    
    def rebalance_to_weights(
        self,
        target_weights: Dict[str, float],
        prev_portfolio: PortfolioState,
        prices: Dict[str, float],
        volumes: Optional[Dict[str, float]] = None
    ) -> ExecutionResult:
        """執行再平衡到目標權重
        
        Args:
            target_weights: 目標權重字典 {symbol: weight}
            prev_portfolio: 前一期的組合狀態
            prices: 當前價格 {symbol: price}
            volumes: 日成交量 {symbol: volume}（可選）
        
        Returns:
            ExecutionResult 物件
        """
        # Step 1: 計算換手量
        turnover = self.compute_turnover(target_weights, prev_portfolio)
        
        # Step 2: 生成訂單
        orders = self._generate_orders(
            target_weights,
            prev_portfolio,
            prices
        )
        
        # Step 3-7: 執行訂單並更新組合
        return self.execute_orders(orders, prices, volumes, prev_portfolio)
    
    def execute_orders(
        self,
        orders: List[Order],
        prices: Dict[str, float],
        volumes: Optional[Dict[str, float]] = None,
        prev_portfolio: Optional[PortfolioState] = None
    ) -> ExecutionResult:
        """執行訂單列表
        
        Args:
            orders: 訂單列表
            prices: 當前價格
            volumes: 日成交量（可選）
            prev_portfolio: 前一期的組合狀態（用於計算換手率）
        
        Returns:
            ExecutionResult 物件
        """
        fills: List[Fill] = []
        trades: List[Trade] = []
        total_transaction_costs = 0.0
        
        # 建立新的組合狀態（複製前一期的狀態）
        if prev_portfolio:
            new_portfolio = self._copy_portfolio_state(prev_portfolio)
        else:
            new_portfolio = PortfolioState()
        
        # 更新價格
        new_portfolio.update_prices(prices)
        
        # 執行每個訂單
        for order in orders:
            if order.symbol not in prices:
                continue  # 跳過沒有價格的標的
            
            market_price = prices[order.symbol]
            
            # Step 4: 套用 ExecutionModel（計算滑價）
            market_data = {}
            if volumes and order.symbol in volumes:
                market_data["daily_volume"] = volumes[order.symbol]
            
            fill_price = self.execution_model.apply_slippage(
                order,
                market_price,
                market_data
            )
            
            slippage = abs(fill_price - market_price) * order.quantity
            
            # Step 5: 套用 CostModel
            commission = self.cost_model.compute_commission(order, fill_price)
            tax = self.cost_model.compute_tax(order, fill_price)
            total_cost = commission + tax
            total_transaction_costs += total_cost
            
            # Step 6: 生成 Fill
            fill = Fill(
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                filled_quantity=order.quantity,
                fill_price=fill_price,
                slippage=slippage,
                commission=commission,
                tax=tax
            )
            fills.append(fill)
            
            # 生成 Trade
            trade = Trade(order=order, fill=fill)
            trades.append(trade)
            
            # Step 7: 更新 PortfolioState
            self._update_portfolio_with_fill(new_portfolio, fill)
        
        # 計算換手率（如果提供了前一期的組合）
        turnover = 0.0
        if prev_portfolio:
            turnover = self.compute_turnover(
                {symbol: pos.market_value / prev_portfolio.total_value
                 for symbol, pos in prev_portfolio.positions.items()},
                prev_portfolio
            )
        
        # 更新組合狀態的換手率和交易成本
        new_portfolio.turnover = turnover
        new_portfolio.transaction_costs = total_transaction_costs
        
        return ExecutionResult(
            trades=trades,
            fills=fills,
            new_portfolio_state=new_portfolio,
            turnover=turnover,
            transaction_costs=total_transaction_costs,
            diagnostics={
                "num_orders": len(orders),
                "num_fills": len(fills),
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def compute_turnover(
        self,
        target_weights: Dict[str, float],
        current_portfolio: PortfolioState
    ) -> float:
        """計算換手率
        
        公式：turnover = 0.5 * sum(|target_weight[i] - current_weight[i]|)
        
        Args:
            target_weights: 目標權重字典
            current_portfolio: 當前組合狀態
        
        Returns:
            換手率（0-1）
        """
        current_weights = current_portfolio.weights
        
        # 取得所有標的的並集
        all_symbols = set(target_weights.keys()) | set(current_weights.keys())
        
        turnover = 0.0
        for symbol in all_symbols:
            target_w = target_weights.get(symbol, 0.0)
            current_w = current_weights.get(symbol, 0.0)
            turnover += abs(target_w - current_w)
        
        return 0.5 * turnover
    
    def _generate_orders(
        self,
        target_weights: Dict[str, float],
        current_portfolio: PortfolioState,
        prices: Dict[str, float]
    ) -> List[Order]:
        """生成交易訂單
        
        Args:
            target_weights: 目標權重字典
            current_portfolio: 當前組合狀態
            prices: 當前價格
        
        Returns:
            交易訂單列表
        """
        orders: List[Order] = []
        total_value = current_portfolio.total_value
        
        current_weights = current_portfolio.weights
        
        for symbol, target_weight in target_weights.items():
            if symbol not in prices:
                continue  # 跳過沒有價格的標的
            
            current_weight = current_weights.get(symbol, 0.0)
            weight_diff = target_weight - current_weight
            
            # 如果差異太小，忽略
            if abs(weight_diff) < self.min_trade_threshold:
                continue
            
            current_price = prices[symbol]
            target_value = target_weight * total_value
            current_value = current_weight * total_value
            trade_value = target_value - current_value
            
            # 計算交易數量
            if abs(trade_value) < 1.0:  # 交易金額太小，忽略
                continue
            
            quantity = abs(trade_value) / current_price
            side = "BUY" if trade_value > 0 else "SELL"
            
            # 建立訂單
            order = Order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type="MARKET"
            )
            orders.append(order)
        
        return orders
    
    def _update_portfolio_with_fill(
        self,
        portfolio: PortfolioState,
        fill: Fill
    ) -> None:
        """使用成交記錄更新投資組合狀態
        
        Args:
            portfolio: 投資組合狀態
            fill: 成交記錄
        """
        symbol = fill.symbol
        
        # 取得或建立持倉
        position = portfolio.get_position(symbol)
        
        if fill.side == "BUY":
            # 買入：增加持倉或建立新持倉
            if position is None:
                position = Position(
                    symbol=symbol,
                    quantity=fill.filled_quantity,
                    avg_price=fill.fill_price,
                    current_price=fill.fill_price
                )
                portfolio.update_position(symbol, position)
            else:
                position.add_quantity(fill.filled_quantity, fill.fill_price)
            
            # 扣除現金（成交金額 + 手續費）
            portfolio.cash -= (fill.trade_amount + fill.total_cost)
        
        else:  # SELL
            # 賣出：減少持倉
            if position is None or position.quantity < fill.filled_quantity:
                # 持倉不足，記錄錯誤但不中斷
                portfolio.cash = portfolio.cash  # 不變
                return
            
            position.reduce_quantity(fill.filled_quantity)
            
            # 如果持倉為 0，移除
            if position.quantity == 0:
                portfolio.remove_position(symbol)
            
            # 增加現金（成交金額 - 手續費 - 稅費）
            portfolio.cash += (fill.trade_amount - fill.total_cost)
    
    def _copy_portfolio_state(self, portfolio: PortfolioState) -> PortfolioState:
        """複製投資組合狀態
        
        Args:
            portfolio: 原始投資組合狀態
        
        Returns:
            複製的投資組合狀態
        """
        new_positions = {}
        for symbol, pos in portfolio.positions.items():
            new_positions[symbol] = Position(
                symbol=pos.symbol,
                quantity=pos.quantity,
                avg_price=pos.avg_price,
                current_price=pos.current_price
            )
        
        return PortfolioState(
            positions=new_positions,
            cash=portfolio.cash,
            timestamp=portfolio.timestamp,
            turnover=0.0,
            transaction_costs=0.0
        )
