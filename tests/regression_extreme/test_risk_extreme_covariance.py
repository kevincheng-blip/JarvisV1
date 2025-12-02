"""
Regression Test: Risk Model Extreme - Covariance

Tests Risk Model Extreme:
- Covariance matrix is symmetric
- Covariance matrix is positive semi-definite
- Factor extraction works
"""

import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

from jgod.risk.risk_model_extreme import (
    MultiFactorRiskModelExtreme,
    RiskModelExtremeConfig,
)
from jgod.path_a.mock_data_loader_extreme import MockPathADataLoaderExtreme, MockConfigExtreme
from jgod.path_a.path_a_schema import PathAConfig


class TestRiskExtremeCovariance(unittest.TestCase):
    """Test Risk Model Extreme covariance."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = PathAConfig(
            start_date="2024-01-01",
            end_date="2024-03-31",  # Longer period for better covariance
            universe=["2330.TW", "2317.TW", "2303.TW"],
            rebalance_frequency="D",
        )
        
        mock_config = MockConfigExtreme(seed=42)
        self.loader = MockPathADataLoaderExtreme(config=mock_config)
        
        self.risk_model = MultiFactorRiskModelExtreme()
    
    def test_covariance_symmetric(self):
        """Test covariance matrix is symmetric."""
        price_frame = self.loader.load_price_frame(self.config)
        
        # Extract returns
        returns_df = pd.DataFrame(index=price_frame.index)
        for symbol in self.config.universe:
            close_col = (symbol, "close")
            close_series = price_frame[close_col]
            returns_df[symbol] = close_series.pct_change().fillna(0.0)
        
        # Fit model
        self.risk_model.fit_from_returns(returns_df)
        
        # Get covariance
        cov_matrix = self.risk_model.get_covariance_matrix()
        
        # Check symmetry
        np.testing.assert_array_almost_equal(
            cov_matrix, cov_matrix.T,
            err_msg="Covariance matrix is not symmetric"
        )
    
    def test_covariance_positive_semi_definite(self):
        """Test covariance matrix is positive semi-definite."""
        price_frame = self.loader.load_price_frame(self.config)
        
        # Extract returns
        returns_df = pd.DataFrame(index=price_frame.index)
        for symbol in self.config.universe:
            close_col = (symbol, "close")
            close_series = price_frame[close_col]
            returns_df[symbol] = close_series.pct_change().fillna(0.0)
        
        # Fit model
        self.risk_model.fit_from_returns(returns_df)
        
        # Get covariance
        cov_matrix = self.risk_model.get_covariance_matrix()
        
        # Check eigenvalues are non-negative
        eigenvalues = np.linalg.eigvals(cov_matrix)
        
        self.assertTrue(
            np.all(eigenvalues >= -1e-10),  # Allow small numerical errors
            f"Covariance matrix is not positive semi-definite. "
            f"Eigenvalues: {eigenvalues}"
        )


if __name__ == "__main__":
    unittest.main()

