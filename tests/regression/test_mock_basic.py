"""
Regression Test: Mock Data Loader - Basic Functionality

Tests basic functionality of MockPathADataLoader:
- Loader doesn't raise errors
- Returned DataFrame shapes are correct
- Column completeness (open/high/low/close/volume)
- No unexpected NaN values
"""

import unittest
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

from jgod.path_a.mock_data_loader import MockPathADataLoader, MockConfig
from jgod.path_a.path_a_schema import PathAConfig


class TestMockBasic(unittest.TestCase):
    """Test basic functionality of MockPathADataLoader."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = PathAConfig(
            start_date="2024-01-01",
            end_date="2024-01-10",
            universe=["2330.TW", "2317.TW", "2303.TW"],
            rebalance_frequency="D",
        )
        
        mock_config = MockConfig(seed=42)
        self.loader = MockPathADataLoader(config=mock_config)
    
    def test_loader_initialization(self):
        """Test loader can be initialized without errors."""
        self.assertIsNotNone(self.loader)
        self.assertIsNotNone(self.loader.config)
    
    def test_load_price_frame_no_error(self):
        """Test load_price_frame doesn't raise errors."""
        try:
            price_frame = self.loader.load_price_frame(self.config)
            self.assertIsNotNone(price_frame)
        except Exception as e:
            self.fail(f"load_price_frame raised an exception: {e}")
    
    def test_price_frame_shape(self):
        """Test price frame has correct shape."""
        price_frame = self.loader.load_price_frame(self.config)
        
        # Check it's a DataFrame
        self.assertIsInstance(price_frame, pd.DataFrame)
        
        # Check index is DatetimeIndex
        self.assertIsInstance(price_frame.index, pd.DatetimeIndex)
        
        # Check columns are MultiIndex
        self.assertIsInstance(price_frame.columns, pd.MultiIndex)
        self.assertEqual(price_frame.columns.names, ["symbol", "field"])
        
        # Check shape: dates x (symbols * fields)
        n_dates = len(pd.date_range(
            start=self.config.start_date,
            end=self.config.end_date,
            freq="B"
        ))
        n_symbols = len(self.config.universe)
        n_fields = 5  # open, high, low, close, volume
        
        self.assertEqual(price_frame.shape[0], n_dates)
        self.assertEqual(price_frame.shape[1], n_symbols * n_fields)
    
    def test_price_frame_columns_completeness(self):
        """Test price frame has all required columns."""
        price_frame = self.loader.load_price_frame(self.config)
        
        required_fields = ["open", "high", "low", "close", "volume"]
        
        for symbol in self.config.universe:
            for field in required_fields:
                col = (symbol, field)
                self.assertIn(col, price_frame.columns, 
                             f"Missing column: {col}")
    
    def test_price_frame_no_unexpected_nan(self):
        """Test price frame doesn't have unexpected NaN values."""
        price_frame = self.loader.load_price_frame(self.config)
        
        # Check for NaN in price columns
        for symbol in self.config.universe:
            for field in ["open", "high", "low", "close", "volume"]:
                col = (symbol, field)
                if col in price_frame.columns:
                    nan_count = price_frame[col].isna().sum()
                    self.assertEqual(nan_count, 0, 
                                   f"Unexpected NaN in {col}: {nan_count} values")
    
    def test_price_frame_price_relationships(self):
        """Test price relationships are valid (high >= max(open, close), etc.)."""
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
                
                # high - low >= 0
                self.assertGreaterEqual(
                    high_val - low_val, 0,
                    f"Invalid range at {date} for {symbol}"
                )
                
                # All prices > 0
                self.assertGreater(open_val, 0, f"Invalid open at {date} for {symbol}")
                self.assertGreater(high_val, 0, f"Invalid high at {date} for {symbol}")
                self.assertGreater(low_val, 0, f"Invalid low at {date} for {symbol}")
                self.assertGreater(close_val, 0, f"Invalid close at {date} for {symbol}")
    
    def test_load_feature_frame_no_error(self):
        """Test load_feature_frame doesn't raise errors."""
        try:
            feature_frame = self.loader.load_feature_frame(self.config)
            self.assertIsNotNone(feature_frame)
        except Exception as e:
            self.fail(f"load_feature_frame raised an exception: {e}")
    
    def test_feature_frame_shape(self):
        """Test feature frame has correct shape."""
        feature_frame = self.loader.load_feature_frame(self.config)
        
        # Check it's a DataFrame
        self.assertIsInstance(feature_frame, pd.DataFrame)
        
        # Check index is MultiIndex
        self.assertIsInstance(feature_frame.index, pd.MultiIndex)
        self.assertEqual(feature_frame.index.names, ["date", "symbol"])
        
        # Check expected columns
        expected_features = [
            "daily_return_1d",
            "rolling_vol_5d",
            "rolling_vol_20d",
            "momentum_5d",
            "momentum_20d",
            "turnover_rate",
            "close", "volume", "open", "high", "low",
        ]
        
        for feature in expected_features:
            self.assertIn(feature, feature_frame.columns,
                         f"Missing feature: {feature}")
    
    def test_feature_frame_index_completeness(self):
        """Test feature frame has all date-symbol combinations."""
        feature_frame = self.loader.load_feature_frame(self.config)
        
        dates = pd.date_range(
            start=self.config.start_date,
            end=self.config.end_date,
            freq="B"
        )
        
        expected_combinations = len(dates) * len(self.config.universe)
        self.assertEqual(len(feature_frame), expected_combinations)


if __name__ == "__main__":
    unittest.main()

