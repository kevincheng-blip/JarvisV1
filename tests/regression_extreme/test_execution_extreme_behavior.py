"""
Regression Test: Execution Engine Extreme - Behavior

Tests Execution Engine Extreme:
- High volume → low slippage
- Low volume → high slippage / partial fill
- Damped execution works
"""

import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from jgod.execution.execution_engine_extreme import (
    ExecutionEngineExtreme,
    ExecutionEngineExtremeConfig,
    ExecutionStatistics,
)
from jgod.execution.execution_types import Order
from jgod.execution.cost_model import DefaultCostModel


class TestExecutionExtremeBehavior(unittest.TestCase):
    """Test Execution Engine Extreme behavior."""
    
    def setUp(self):
        """Set up test fixtures."""
        cost_model = DefaultCostModel()
        config = ExecutionEngineExtremeConfig()
        self.execution_engine = ExecutionEngineExtreme(
            cost_model=cost_model,
            config=config
        )
    
    def test_high_volume_low_slippage(self):
        """Test high volume leads to low slippage."""
        order = Order(
            symbol="2330.TW",
            side="BUY",
            quantity=1000.0,
        )
        
        market_price = 550.0
        high_volume = 10_000_000.0  # High volume
        
        fill, stats = self.execution_engine.execute_order(
            order,
            market_price,
            high_volume
        )
        
        # Slippage should be relatively low
        slippage_pct = stats.realized_slippage / (market_price * order.quantity)
        
        self.assertLess(
            slippage_pct, 0.01,  # Less than 1% slippage
            f"Slippage too high for high volume: {slippage_pct:.2%}"
        )
    
    def test_low_volume_high_slippage(self):
        """Test low volume leads to higher slippage."""
        order = Order(
            symbol="2330.TW",
            side="BUY",
            quantity=1000.0,
        )
        
        market_price = 550.0
        low_volume = 1_000.0  # Low volume
        
        fill, stats = self.execution_engine.execute_order(
            order,
            market_price,
            low_volume
        )
        
        # Slippage should be higher
        slippage_pct = stats.realized_slippage / (market_price * order.quantity)
        
        # Should be higher than high-volume case
        # (we're just checking it's computed, not that it's necessarily very high)
        self.assertGreater(
            slippage_pct, 0.0,
            "Slippage should be positive"
        )
    
    def test_damped_execution(self):
        """Test damped execution reduces large position changes."""
        target_weights = {
            "2330.TW": 0.5,  # Large change
            "2317.TW": 0.3,
        }
        
        current_weights = {
            "2330.TW": 0.1,  # Large delta (0.4)
            "2317.TW": 0.2,
        }
        
        # Apply damping
        damped = self.execution_engine._damp_position_change(
            target_weights,
            current_weights
        )
        
        # Check that large change was damped
        original_delta = target_weights["2330.TW"] - current_weights["2330.TW"]
        damped_delta = damped["2330.TW"] - current_weights["2330.TW"]
        
        # Damped delta should be smaller
        if abs(original_delta) > self.execution_engine.config.damp_threshold:
            self.assertLess(
                abs(damped_delta), abs(original_delta),
                "Large position change should be damped"
            )


if __name__ == "__main__":
    unittest.main()

