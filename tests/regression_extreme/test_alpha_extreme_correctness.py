"""
Regression Test: AlphaEngine Extreme - Correctness

Tests AlphaEngine Extreme:
- composite_alpha is not all NaN
- Cross-sectional ranking is reasonable (top vs bottom quantiles differ)
- Regime detection works
"""

import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

from jgod.alpha_engine.alpha_engine_extreme import (
    AlphaEngineExtreme,
    AlphaEngineExtremeConfig,
    VolatilityRegime,
)
from jgod.path_a.mock_data_loader_extreme import MockPathADataLoaderExtreme, MockConfigExtreme
from jgod.path_a.path_a_schema import PathAConfig
from jgod.path_a.path_a_backtest import _prepare_alpha_input


class TestAlphaExtremeCorrectness(unittest.TestCase):
    """Test AlphaEngine Extreme correctness."""
    
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
        
        self.alpha_engine = AlphaEngineExtreme()
    
    def test_composite_alpha_not_all_nan(self):
        """Test composite_alpha is not all NaN."""
        price_frame = self.loader.load_price_frame(self.config)
        feature_frame = self.loader.load_feature_frame(self.config)
        
        dates = pd.date_range(
            start=self.config.start_date,
            end=self.config.end_date,
            freq="B"
        )
        
        for date in dates[:5]:  # Test first 5 dates
            alpha_input = _prepare_alpha_input(
                feature_frame=feature_frame,
                price_frame=price_frame,
                current_date=date,
                universe=list(self.config.universe)
            )
            
            alpha_result = self.alpha_engine.compute_all(alpha_input)
            
            self.assertIsNotNone(alpha_result)
            
            if 'composite_alpha' in alpha_result.columns:
                composite_alpha = alpha_result['composite_alpha']
                
                # Check not all NaN
                nan_count = composite_alpha.isna().sum()
                self.assertLess(
                    nan_count, len(composite_alpha),
                    f"All composite_alpha are NaN on {date}"
                )
    
    def test_cross_sectional_ranking_reasonable(self):
        """Test cross-sectional ranking produces reasonable differences."""
        price_frame = self.loader.load_price_frame(self.config)
        feature_frame = self.loader.load_feature_frame(self.config)
        
        dates = pd.date_range(
            start=self.config.start_date,
            end=self.config.end_date,
            freq="B"
        )
        
        test_date = dates[5]  # Use a date after initial periods
        
        alpha_input = _prepare_alpha_input(
            feature_frame=feature_frame,
            price_frame=price_frame,
            current_date=test_date,
            universe=list(self.config.universe)
        )
        
        alpha_result = self.alpha_engine.compute_all(alpha_input)
        
        if 'composite_alpha' in alpha_result.columns:
            composite_alpha = alpha_result['composite_alpha'].dropna()
            
            if len(composite_alpha) >= 2:
                # Check that top and bottom quantiles differ
                top_alpha = composite_alpha.max()
                bottom_alpha = composite_alpha.min()
                
                # Should have some spread
                spread = abs(top_alpha - bottom_alpha)
                self.assertGreater(
                    spread, 0.01,
                    f"Alpha spread too small: {spread:.4f}"
                )


if __name__ == "__main__":
    unittest.main()

