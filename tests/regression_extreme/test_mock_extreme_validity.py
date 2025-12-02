"""
Regression Test: Mock Loader Extreme - Validity

Tests MockPathADataLoaderExtreme output validity:
- Price relationships (high >= max(open, close), etc.)
- Volatility is reasonable
- No severe NaN values
- Features are complete
"""

import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

from jgod.path_a.mock_data_loader_extreme import (
    MockPathADataLoaderExtreme,
    MockConfigExtreme,
    VolatilityRegime,
)
from jgod.path_a.path_a_schema import PathAConfig


class TestMockExtremeValidity(unittest.TestCase):
    """Test Mock Loader Extreme validity."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = PathAConfig(
            start_date="2024-01-01",
            end_date="2024-01-31",
            universe=["2330.TW", "2317.TW", "2303.TW"],
            rebalance_frequency="D",
        )
        
        mock_config = MockConfigExtreme(seed=42)
        self.loader = MockPathADataLoaderExtreme(config=mock_config)
    
    def test_price_relationships(self):
        """Test price relationships are valid."""
        price_frame = self.loader.load_price_frame(self.config)
        
        for symbol in self.config.universe:
            open_col = (symbol, "open")
            high_col = (symbol, "high")
            low_col = (symbol, "low")
            close_col = (symbol, "close")
            
            for date in price_frame.index:
                open_val = price_frame.loc[date, open_col]
                high_val = price_frame.loc[date, high_col]
                low_val = price_frame.loc[date, low_col]
                close_val = price_frame.loc[date, close_col]
                
                # high >= max(open, close)
                self.assertGreaterEqual(
                    high_val, max(open_val, close_val),
                    f"Invalid high at {date} for {symbol}"
                )
                
                # low <= min(open, close)
                self.assertLessEqual(
                    low_val, min(open_val, close_val),
                    f"Invalid low at {date} for {symbol}"
                )
                
                # All prices > 0
                self.assertGreater(open_val, 0)
                self.assertGreater(high_val, 0)
                self.assertGreater(low_val, 0)
                self.assertGreater(close_val, 0)
    
    def test_volatility_reasonable(self):
        """Test volatility is in reasonable range."""
        price_frame = self.loader.load_price_frame(self.config)
        
        for symbol in self.config.universe:
            close_col = (symbol, "close")
            close_series = price_frame[close_col]
            
            # Compute returns
            returns = close_series.pct_change().dropna()
            
            # Check daily returns are within bounds (e.g., ±10%)
            max_return = returns.abs().max()
            self.assertLess(
                max_return, 0.10,
                f"Daily return exceeds 10% for {symbol}: {max_return:.2%}"
            )
    
    def test_no_severe_nan(self):
        """Test no severe NaN values in price frame."""
        price_frame = self.loader.load_price_frame(self.config)
        
        # Check for NaN
        nan_count = price_frame.isna().sum().sum()
        total_cells = price_frame.size
        
        nan_ratio = nan_count / total_cells if total_cells > 0 else 0.0
        
        self.assertLess(
            nan_ratio, 0.01,
            f"Too many NaN values: {nan_ratio:.2%}"
        )
    
    def test_features_complete(self):
        """Test feature frame has all required features."""
        feature_frame = self.loader.load_feature_frame(self.config)
        
        required_features = [
            "daily_return_1d",
            "rolling_vol_5d",
            "rolling_vol_20d",
            "rolling_momentum_3d",
            "rolling_momentum_5d",
            "rolling_momentum_10d",
            "ATR_14",
            "rolling_skew",
            "rolling_kurtosis",
            "VWAP_14",
            "turnover_rate",
        ]
        
        for feature in required_features:
            self.assertIn(
                feature, feature_frame.columns,
                f"Missing feature: {feature}"
            )


if __name__ == "__main__":
    unittest.main()

