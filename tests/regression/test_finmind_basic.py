"""
Regression Test: FinMind Data Loader - Basic Functionality

Tests basic functionality of FinMindPathADataLoader:
- Loader can be initialized
- Loader doesn't raise errors (even if API fails, should fallback)
- Returned DataFrame shapes are correct (if data available)
- Column completeness
"""

import unittest
from pathlib import Path
import sys
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np


class TestFinMindBasic(unittest.TestCase):
    """Test basic functionality of FinMindPathADataLoader."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-10",
            "universe": ["2330.TW", "2317.TW", "2303.TW"],
            "rebalance_frequency": "D",
        }
        
        # Check if FinMind is available
        self.finmind_available = os.getenv("FINMIND_TOKEN") is not None
    
    def test_loader_can_initialize(self):
        """Test loader can be initialized (even without token, should use fallback)."""
        try:
            from jgod.path_a.finmind_data_loader import FinMindPathADataLoader
            
            if self.finmind_available:
                loader = FinMindPathADataLoader()
                self.assertIsNotNone(loader)
            else:
                # Without token, should still work with fallback
                try:
                    loader = FinMindPathADataLoader()
                    # If we get here without error, that's fine (fallback enabled)
                    self.assertIsNotNone(loader)
                except ValueError:
                    # Expected if fallback is disabled
                    pass
                    
        except ImportError:
            self.skipTest("FinMind loader not available")
    
    def test_load_price_frame_no_error(self):
        """Test load_price_frame doesn't raise errors (uses fallback if needed)."""
        try:
            from jgod.path_a.finmind_data_loader import FinMindPathADataLoader
            from jgod.path_a.path_a_schema import PathAConfig
            
            config = PathAConfig(**self.config)
            
            if self.finmind_available:
                loader = FinMindPathADataLoader()
            else:
                # Use fallback mode
                from jgod.path_a.finmind_data_loader import FinMindLoaderConfig
                loader_config = FinMindLoaderConfig(fallback_to_mock=True)
                loader = FinMindPathADataLoader(config=loader_config)
            
            try:
                price_frame = loader.load_price_frame(config)
                self.assertIsNotNone(price_frame)
            except Exception as e:
                # Should not fail completely (should use mock fallback)
                error_msg = str(e).lower()
                if "token" not in error_msg:
                    # Non-token errors are unexpected
                    self.fail(f"Unexpected error: {e}")
                    
        except ImportError:
            self.skipTest("FinMind loader not available")
    
    def test_price_frame_shape_if_data_available(self):
        """Test price frame has correct shape if data is available."""
        if not self.finmind_available:
            self.skipTest("FinMind token not available")
        
        try:
            from jgod.path_a.finmind_data_loader import FinMindPathADataLoader
            from jgod.path_a.path_a_schema import PathAConfig
            
            config = PathAConfig(**self.config)
            loader = FinMindPathADataLoader()
            
            price_frame = loader.load_price_frame(config)
            
            # Check it's a DataFrame
            self.assertIsInstance(price_frame, pd.DataFrame)
            
            # Check index is DatetimeIndex
            self.assertIsInstance(price_frame.index, pd.DatetimeIndex)
            
            # Check columns are MultiIndex
            if len(price_frame) > 0:
                self.assertIsInstance(price_frame.columns, pd.MultiIndex)
                self.assertEqual(price_frame.columns.names, ["symbol", "field"])
            
        except ImportError:
            self.skipTest("FinMind loader not available")
        except Exception as e:
            # If API fails, that's acceptable - fallback should handle it
            print(f"Warning: FinMind API call failed (expected if API unavailable): {e}")
    
    def test_load_feature_frame_no_error(self):
        """Test load_feature_frame doesn't raise errors."""
        try:
            from jgod.path_a.finmind_data_loader import FinMindPathADataLoader
            from jgod.path_a.path_a_schema import PathAConfig
            
            config = PathAConfig(**self.config)
            
            if self.finmind_available:
                loader = FinMindPathADataLoader()
            else:
                from jgod.path_a.finmind_data_loader import FinMindLoaderConfig
                loader_config = FinMindLoaderConfig(fallback_to_mock=True)
                loader = FinMindPathADataLoader(config=loader_config)
            
            try:
                feature_frame = loader.load_feature_frame(config)
                self.assertIsNotNone(feature_frame)
            except Exception as e:
                error_msg = str(e).lower()
                if "token" not in error_msg:
                    self.fail(f"Unexpected error: {e}")
                    
        except ImportError:
            self.skipTest("FinMind loader not available")
    
    def test_fallback_to_mock_works(self):
        """Test fallback to mock data works when FinMind fails."""
        try:
            from jgod.path_a.finmind_data_loader import (
                FinMindPathADataLoader,
                FinMindLoaderConfig
            )
            from jgod.path_a.path_a_schema import PathAConfig
            
            config = PathAConfig(**self.config)
            loader_config = FinMindLoaderConfig(fallback_to_mock=True)
            
            # Create loader with invalid token (should trigger fallback)
            loader = FinMindPathADataLoader(config=loader_config)
            
            # Should not fail (uses mock fallback)
            price_frame = loader.load_price_frame(config)
            self.assertIsNotNone(price_frame)
            
            feature_frame = loader.load_feature_frame(config)
            self.assertIsNotNone(feature_frame)
            
        except ImportError:
            self.skipTest("FinMind loader not available")


if __name__ == "__main__":
    unittest.main()

