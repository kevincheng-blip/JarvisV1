"""
Execution Engine Extreme - Professional Quant Fund Grade

This module provides an extreme-level execution engine with:
- Damped execution (controls large position changes)
- Volume-based slippage model
- Market impact cost model
- Detailed execution statistics

Reference: docs/JGOD_EXTREME_MODE_EDITOR_INSTRUCTIONS.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid
import numpy as np

from jgod.execution.execution_types import (
    Order, Fill, Trade, Position, PortfolioState
)
from jgod.execution.cost_model import CostModel, DefaultCostModel


@dataclass
class ExecutionEngineExtremeConfig:
    """Configuration for Execution Engine Extreme."""
    
    # Damped execution parameters
    damp_threshold: float = 0.1  # If |Δw| > threshold, damp by half
    damp_factor: float = 0.5  # Damping factor
    
    # Slippage model parameters
    slippage_k: float = 0.001  # Base slippage coefficient
    slippage_alpha: float = 0.5  # Volume impact exponent
    
    # Market impact parameters
    impact_linear_coeff: float = 0.0001  # Linear impact coefficient
    impact_quadratic_coeff: float = 0.00001  # Quadratic impact coefficient
    
    # Time slicing (for large orders)
    enable_time_slicing: bool = True
    max_slice_participation: float = 0.1  # Max 10% of daily volume per slice
    
    # Minimum trade threshold
    min_trade_threshold: float = 0.001


@dataclass
class ExecutionStatistics:
    """Detailed execution statistics."""
    
    realized_slippage: float = 0.0
    realized_cost: float = 0.0
    market_impact_cost: float = 0.0
    fill_ratio: float = 1.0  # Filled quantity / Order quantity
    volume_participation_rate: float = 0.0  # Order volume / Daily volume
    num_slices: int = 1  # Number of execution slices


class ExecutionEngineExtreme:
    """
    Extreme Execution Engine for professional quant fund applications.
    
    Features:
    - Damped execution to control large position changes
    - Volume-based slippage model
    - Market impact cost calculation
    - Time slicing for large orders
    - Detailed execution statistics
    """
    
    def __init__(
        self,
        cost_model: Optional[CostModel] = None,
        config: Optional[ExecutionEngineExtremeConfig] = None,
    ):
        """
        Initialize Execution Engine Extreme.
        
        Args:
            cost_model: Cost model for commission/tax calculation
            config: Configuration object. If None, uses default config.
        """
        self.config = config or ExecutionEngineExtremeConfig()
        self.cost_model = cost_model or DefaultCostModel()
    
    def _damp_position_change(
        self,
        target_weights: Dict[str, float],
        current_weights: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Apply damping to large position changes.
        
        If |Δw| > threshold, reduce the change by damp_factor.
        
        Args:
            target_weights: Target weights {symbol: weight}
            current_weights: Current weights {symbol: weight}
        
        Returns:
            Damped target weights
        """
        damped_weights = {}
        
        all_symbols = set(target_weights.keys()) | set(current_weights.keys())
        
        for symbol in all_symbols:
            target_w = target_weights.get(symbol, 0.0)
            current_w = current_weights.get(symbol, 0.0)
            
            delta_w = target_w - current_w
            
            # Check if change exceeds threshold
            if abs(delta_w) > self.config.damp_threshold:
                # Apply damping
                damped_delta = delta_w * self.config.damp_factor
                damped_weights[symbol] = current_w + damped_delta
            else:
                # No damping needed
                damped_weights[symbol] = target_w
        
        return damped_weights
    
    def _compute_slippage(
        self,
        order_size: float,
        daily_volume: float,
        base_price: float,
    ) -> float:
        """
        Compute volume-based slippage.
        
        Formula: slippage = k * (order_size / daily_volume)^α
        
        Args:
            order_size: Order size in shares
            daily_volume: Daily trading volume in shares
            base_price: Base price
        
        Returns:
            Slippage amount (in price units)
        """
        if daily_volume <= 0:
            # If no volume data, use conservative slippage
            return base_price * self.config.slippage_k * 0.02
        
        # Volume participation rate
        participation = order_size / daily_volume
        
        # Slippage percentage
        slippage_pct = self.config.slippage_k * (participation ** self.config.slippage_alpha)
        
        # Convert to price units
        slippage = base_price * slippage_pct
        
        return slippage
    
    def _compute_market_impact(
        self,
        order_size: float,
        daily_volume: float,
        base_price: float,
    ) -> float:
        """
        Compute market impact cost using linear + quadratic model.
        
        Formula: impact = linear_coeff * participation + quadratic_coeff * participation^2
        
        Args:
            order_size: Order size in shares
            daily_volume: Daily trading volume in shares
            base_price: Base price
        
        Returns:
            Market impact cost (in price units)
        """
        if daily_volume <= 0:
            return 0.0
        
        # Volume participation rate
        participation = order_size / daily_volume
        
        # Linear + quadratic impact
        impact_pct = (
            self.config.impact_linear_coeff * participation +
            self.config.impact_quadratic_coeff * (participation ** 2)
        )
        
        # Convert to price units
        impact = base_price * impact_pct
        
        return impact
    
    def _slice_order(
        self,
        order: Order,
        daily_volume: float,
    ) -> List[Order]:
        """
        Slice large orders into smaller pieces for execution.
        
        Args:
            order: Original order
            daily_volume: Daily trading volume
        
        Returns:
            List of sliced orders
        """
        if not self.config.enable_time_slicing or daily_volume <= 0:
            return [order]
        
        # Calculate max slice size
        max_slice_size = daily_volume * self.config.max_slice_participation
        
        if order.quantity <= max_slice_size:
            # Order is small enough, no slicing needed
            return [order]
        
        # Slice the order
        num_slices = int(np.ceil(order.quantity / max_slice_size))
        slice_size = order.quantity / num_slices
        
        slices = []
        for i in range(num_slices):
            # Last slice gets remaining quantity
            if i == num_slices - 1:
                slice_qty = order.quantity - (slice_size * (num_slices - 1))
            else:
                slice_qty = slice_size
            
            slice_order = Order(
                symbol=order.symbol,
                side=order.side,
                quantity=slice_qty,
                order_type=order.order_type,
                limit_price=order.limit_price,
            )
            slices.append(slice_order)
        
        return slices
    
    def execute_order(
        self,
        order: Order,
        market_price: float,
        daily_volume: float,
    ) -> Tuple[Fill, ExecutionStatistics]:
        """
        Execute a single order with extreme-level modeling.
        
        Args:
            order: Order to execute
            market_price: Current market price
            daily_volume: Daily trading volume
        
        Returns:
            Tuple of (Fill, ExecutionStatistics)
        """
        # Slice order if needed
        order_slices = self._slice_order(order, daily_volume)
        
        # Execute slices (for simplicity, we execute all at once)
        # In practice, slices would be executed over time
        total_filled_qty = 0.0
        total_slippage = 0.0
        total_cost = 0.0
        total_impact = 0.0
        
        avg_fill_price = market_price
        
        for slice_order in order_slices:
            # Compute slippage
            slippage = self._compute_slippage(
                slice_order.quantity,
                daily_volume,
                market_price
            )
            
            # Compute market impact
            impact = self._compute_market_impact(
                slice_order.quantity,
                daily_volume,
                market_price
            )
            
            # Fill price = market_price + slippage + impact
            if order.side == "BUY":
                fill_price = market_price + slippage + impact
            else:  # SELL
                fill_price = market_price - slippage - impact
            
            # Ensure fill price is positive
            fill_price = max(fill_price, market_price * 0.01)
            
            # Compute costs
            commission = self.cost_model.compute_commission(slice_order, fill_price)
            tax = self.cost_model.compute_tax(slice_order, fill_price)
            slice_cost = commission + tax
            
            # Accumulate statistics
            total_filled_qty += slice_order.quantity
            total_slippage += slippage * slice_order.quantity
            total_impact += impact * slice_order.quantity
            total_cost += slice_cost
            
            # Weighted average fill price
            avg_fill_price = (
                (avg_fill_price * (total_filled_qty - slice_order.quantity) +
                 fill_price * slice_order.quantity) / total_filled_qty
            )
        
        # Create Fill
        fill = Fill(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            filled_quantity=total_filled_qty,
            fill_price=avg_fill_price,
            slippage=total_slippage,
            commission=total_cost,  # Total commission + tax
            tax=0.0,  # Already included in commission for simplicity
        )
        
        # Compute execution statistics
        stats = ExecutionStatistics(
            realized_slippage=total_slippage,
            realized_cost=total_cost,
            market_impact_cost=total_impact,
            fill_ratio=total_filled_qty / order.quantity if order.quantity > 0 else 0.0,
            volume_participation_rate=total_filled_qty / daily_volume if daily_volume > 0 else 0.0,
            num_slices=len(order_slices),
        )
        
        return fill, stats
    
    def rebalance_to_weights(
        self,
        target_weights: Dict[str, float],
        current_weights: Dict[str, float],
        prices: Dict[str, float],
        volumes: Dict[str, float],
        portfolio_value: float,
    ) -> Tuple[List[Fill], ExecutionStatistics]:
        """
        Execute rebalancing to target weights.
        
        Args:
            target_weights: Target weights {symbol: weight}
            current_weights: Current weights {symbol: weight}
            prices: Current prices {symbol: price}
            volumes: Daily volumes {symbol: volume}
            portfolio_value: Total portfolio value
        
        Returns:
            Tuple of (List[Fills], AggregateExecutionStatistics)
        """
        # Apply damping
        damped_target_weights = self._damp_position_change(
            target_weights,
            current_weights
        )
        
        # Generate orders
        orders = []
        all_symbols = set(damped_target_weights.keys()) | set(current_weights.keys())
        
        for symbol in all_symbols:
            target_w = damped_target_weights.get(symbol, 0.0)
            current_w = current_weights.get(symbol, 0.0)
            
            delta_w = target_w - current_w
            
            # Skip if change is too small
            if abs(delta_w) < self.config.min_trade_threshold:
                continue
            
            # Skip if no price
            if symbol not in prices:
                continue
            
            # Calculate order quantity
            target_value = portfolio_value * target_w
            current_value = portfolio_value * current_w
            delta_value = target_value - current_value
            
            price = prices[symbol]
            quantity = abs(delta_value) / price
            
            if quantity < 1:
                continue
            
            # Determine side
            side = "BUY" if delta_value > 0 else "SELL"
            
            order = Order(
                symbol=symbol,
                side=side,
                quantity=quantity,
            )
            orders.append(order)
        
        # Execute all orders
        fills = []
        total_stats = ExecutionStatistics()
        
        for order in orders:
            market_price = prices.get(order.symbol, 0.0)
            daily_volume = volumes.get(order.symbol, 0.0)
            
            if market_price <= 0:
                continue
            
            fill, stats = self.execute_order(
                order,
                market_price,
                daily_volume
            )
            
            fills.append(fill)
            
            # Aggregate statistics
            total_stats.realized_slippage += stats.realized_slippage
            total_stats.realized_cost += stats.realized_cost
            total_stats.market_impact_cost += stats.market_impact_cost
            total_stats.num_slices += stats.num_slices - 1  # Subtract 1 since we count total
        
        # Compute aggregate fill ratio and participation
        if orders:
            total_order_qty = sum(order.quantity for order in orders)
            total_filled_qty = sum(fill.filled_quantity for fill in fills)
            total_stats.fill_ratio = total_filled_qty / total_order_qty if total_order_qty > 0 else 0.0
        
        return fills, total_stats

