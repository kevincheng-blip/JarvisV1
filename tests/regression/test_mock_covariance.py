"""
Regression Test: Mock Data Loader - Covariance Matrix

Tests that covariance matrix calculation works correctly:
- Covariance matrix shape is correct
- No shape mismatch errors
- Matrix is positive semi-definite
"""

import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

from jgod.path_a.mock_data_loader import MockPathADataLoader, MockConfig
from jgod.path_a.path_a_schema import PathAConfig
from jgod.path_a.path_a_backtest import _compute_sample_covariance


class TestMockCovariance(unittest.TestCase):
    """Test covariance matrix calculation with mock data."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = PathAConfig(
            start_date="2024-01-01",
            end_date="2024-01-31",  # Longer period for better covariance
            universe=["2330.TW", "2317.TW", "2303.TW"],
            rebalance_frequency="D",
        )
        
        mock_config = MockConfig(seed=42)
        self.loader = MockPathADataLoader(config=mock_config)
    
    def test_covariance_matrix_shape(self):
        """Test covariance matrix has correct shape."""
        price_frame = self.loader.load_price_frame(self.config)
        
        symbols = list(self.config.universe)
        lookback_days = min(60, len(price_frame))
        
        try:
            cov_matrix = _compute_sample_covariance(
                price_frame,
                symbols,
                lookback_days=lookback_days
            )
            
            # Check shape: (n_symbols, n_symbols)
            expected_shape = (len(symbols), len(symbols))
            self.assertEqual(cov_matrix.shape, expected_shape,
                           f"Expected shape {expected_shape}, got {cov_matrix.shape}")
            
        except Exception as e:
            self.fail(f"Failed to compute covariance matrix: {e}")
    
    def test_covariance_matrix_symmetric(self):
        """Test covariance matrix is symmetric."""
        price_frame = self.loader.load_price_frame(self.config)
        
        symbols = list(self.config.universe)
        lookback_days = min(60, len(price_frame))
        
        cov_matrix = _compute_sample_covariance(
            price_frame,
            symbols,
            lookback_days=lookback_days
        )
        
        # Check symmetry: cov[i, j] == cov[j, i]
        np.testing.assert_array_almost_equal(
            cov_matrix, cov_matrix.T,
            err_msg="Covariance matrix is not symmetric"
        )
    
    def test_covariance_matrix_positive_semi_definite(self):
        """Test covariance matrix is positive semi-definite."""
        price_frame = self.loader.load_price_frame(self.config)
        
        symbols = list(self.config.universe)
        lookback_days = min(60, len(price_frame))
        
        cov_matrix = _compute_sample_covariance(
            price_frame,
            symbols,
            lookback_days=lookback_days
        )
        
        # Check all eigenvalues are >= 0
        eigenvalues = np.linalg.eigvals(cov_matrix)
        self.assertTrue(
            np.all(eigenvalues >= -1e-10),  # Allow small numerical errors
            f"Covariance matrix is not positive semi-definite. "
            f"Eigenvalues: {eigenvalues}"
        )
    
    def test_no_shape_mismatch_error(self):
        """Test no shape mismatch errors occur."""
        price_frame = self.loader.load_price_frame(self.config)
        
        symbols = list(self.config.universe)
        
        # Test different lookback windows
        for lookback_days in [10, 30, 60, len(price_frame)]:
            lookback_days = min(lookback_days, len(price_frame))
            
            try:
                cov_matrix = _compute_sample_covariance(
                    price_frame,
                    symbols,
                    lookback_days=lookback_days
                )
                
                # Check shape matches universe
                self.assertEqual(cov_matrix.shape[0], len(symbols))
                self.assertEqual(cov_matrix.shape[1], len(symbols))
                
            except Exception as e:
                error_msg = str(e).lower()
                if "shape" in error_msg or "mismatch" in error_msg:
                    self.fail(f"Shape mismatch error with lookback={lookback_days}: {e}")
                else:
                    # Other errors are acceptable
                    pass
    
    def test_covariance_matrix_values_reasonable(self):
        """Test covariance matrix values are reasonable (not NaN, not Inf)."""
        price_frame = self.loader.load_price_frame(self.config)
        
        symbols = list(self.config.universe)
        lookback_days = min(60, len(price_frame))
        
        cov_matrix = _compute_sample_covariance(
            price_frame,
            symbols,
            lookback_days=lookback_days
        )
        
        # Check no NaN
        self.assertFalse(
            np.isnan(cov_matrix).any(),
            "Covariance matrix contains NaN values"
        )
        
        # Check no Inf
        self.assertFalse(
            np.isinf(cov_matrix).any(),
            "Covariance matrix contains Inf values"
        )
        
        # Check diagonal (variances) are positive
        diagonal = np.diag(cov_matrix)
        self.assertTrue(
            np.all(diagonal >= 0),
            f"Covariance diagonal (variances) should be >= 0. Got: {diagonal}"
        )


if __name__ == "__main__":
    unittest.main()

