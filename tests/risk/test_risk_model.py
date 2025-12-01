"""Tests for Multi-Factor Risk Model"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from jgod.risk.risk_model import MultiFactorRiskModel
from jgod.risk.exposure_schema import FactorExposure


@pytest.fixture
def sample_factor_names():
    """Sample factor names for testing"""
    return ['flow', 'value_quality']


@pytest.fixture
def sample_exposures(sample_factor_names):
    """Create sample factor exposures for testing
    
    3 stocks, 20 trading days
    """
    symbols = ['STOCK_A', 'STOCK_B', 'STOCK_C']
    dates = pd.date_range(start='2024-01-01', periods=20, freq='D')
    
    np.random.seed(42)
    exposures = []
    
    for date in dates:
        for symbol in symbols:
            exposure_dict = {}
            for factor in sample_factor_names:
                exposure_dict[factor] = np.random.randn() * 0.5
            exposure_dict['beta'] = 1.0
            
            exposures.append(
                FactorExposure(
                    symbol=symbol,
                    date=date,
                    exposures=exposure_dict
                )
            )
    
    return exposures


@pytest.fixture
def sample_returns(sample_exposures):
    """Create sample returns matching exposures"""
    np.random.seed(42)
    returns_data = []
    
    for exp in sample_exposures:
        # Generate return that's somewhat correlated with exposures
        factor_ret = np.random.randn() * 0.01
        specific_ret = np.random.randn() * 0.005
        total_ret = sum(exp.exposures.values()) * factor_ret * 0.1 + specific_ret
        
        returns_data.append({
            'date': exp.date,
            'symbol': exp.symbol,
            'return': total_ret
        })
    
    returns_df = pd.DataFrame(returns_data)
    returns_series = pd.Series(
        returns_df['return'].values,
        index=pd.MultiIndex.from_frame(returns_df[['date', 'symbol']])
    )
    
    return returns_series


def test_risk_model_init(sample_factor_names):
    """Test MultiFactorRiskModel initialization"""
    model = MultiFactorRiskModel(factor_names=sample_factor_names)
    
    assert model.factor_names == sample_factor_names
    assert model.factor_cov is None
    assert model.specific_risk == {}
    assert model.factor_returns is None


def test_risk_model_fit(sample_exposures, sample_returns, sample_factor_names):
    """Test risk model fitting"""
    model = MultiFactorRiskModel(factor_names=sample_factor_names)
    model.fit(sample_exposures, sample_returns, min_observations=10)
    
    # Check that model was fitted
    assert model.factor_cov is not None
    assert isinstance(model.factor_cov, pd.DataFrame)
    assert list(model.factor_cov.index) == sample_factor_names
    assert list(model.factor_cov.columns) == sample_factor_names
    
    # Check specific risk was estimated
    assert len(model.specific_risk) > 0
    assert all(vol >= 0 for vol in model.specific_risk.values())


def test_risk_model_get_factor_covariance(sample_factor_names):
    """Test get_factor_covariance method"""
    model = MultiFactorRiskModel(factor_names=sample_factor_names)
    
    # Before fitting, should return default (identity matrix)
    factor_cov = model.get_factor_covariance()
    assert isinstance(factor_cov, pd.DataFrame)
    assert factor_cov.shape == (len(sample_factor_names), len(sample_factor_names))
    
    # Should be identity matrix
    np.testing.assert_array_almost_equal(
        factor_cov.values,
        np.eye(len(sample_factor_names))
    )


def test_risk_model_get_specific_risk(sample_exposures, sample_returns, sample_factor_names):
    """Test get_specific_risk method"""
    model = MultiFactorRiskModel(factor_names=sample_factor_names)
    model.fit(sample_exposures, sample_returns, min_observations=10)
    
    # Test for existing symbol
    risk_a = model.get_specific_risk('STOCK_A')
    assert risk_a >= 0
    
    # Test for non-existing symbol
    risk_nonexistent = model.get_specific_risk('NONEXISTENT')
    assert risk_nonexistent == 0.0


def test_risk_model_explain_risk(sample_exposures, sample_returns, sample_factor_names):
    """Test explain_risk method"""
    model = MultiFactorRiskModel(factor_names=sample_factor_names)
    model.fit(sample_exposures, sample_returns, min_observations=10)
    
    # Get a sample exposure
    exposure = sample_exposures[0]
    
    # Explain risk
    risk_decomp = model.explain_risk(exposure)
    
    # Check structure
    assert isinstance(risk_decomp, dict)
    assert 'total_variance' in risk_decomp
    assert 'factor_variance' in risk_decomp
    assert 'specific_variance' in risk_decomp
    
    # Check values are non-negative
    assert risk_decomp['total_variance'] >= 0
    assert risk_decomp['factor_variance'] >= 0
    assert risk_decomp['specific_variance'] >= 0
    
    # Total variance should equal factor + specific
    total_expected = risk_decomp['factor_variance'] + risk_decomp['specific_variance']
    assert abs(risk_decomp['total_variance'] - total_expected) < 1e-6
    
    # Check factor contributions exist
    for factor in sample_factor_names:
        assert f'{factor}_contribution' in risk_decomp


def test_risk_model_empty_data(sample_factor_names):
    """Test risk model with empty data"""
    model = MultiFactorRiskModel(factor_names=sample_factor_names)
    
    empty_exposures = []
    empty_returns = pd.Series(dtype=float)
    
    model.fit(empty_exposures, empty_returns)
    
    # Should use default model
    factor_cov = model.get_factor_covariance()
    assert isinstance(factor_cov, pd.DataFrame)
    assert factor_cov.shape == (len(sample_factor_names), len(sample_factor_names))


def test_risk_model_minimal_data(sample_factor_names):
    """Test risk model with minimal data"""
    model = MultiFactorRiskModel(factor_names=sample_factor_names)
    
    # Create minimal data (less than min_observations)
    minimal_exposures = []
    minimal_returns_data = []
    
    for i in range(5):  # Only 5 observations
        date = pd.Timestamp('2024-01-01') + pd.Timedelta(days=i)
        symbol = 'STOCK_A'
        
        exposure_dict = {factor: 0.5 for factor in sample_factor_names}
        exposure_dict['beta'] = 1.0
        
        minimal_exposures.append(
            FactorExposure(
                symbol=symbol,
                date=date,
                exposures=exposure_dict
            )
        )
        
        minimal_returns_data.append({
            'date': date,
            'symbol': symbol,
            'return': 0.01
        })
    
    minimal_returns_df = pd.DataFrame(minimal_returns_data)
    minimal_returns = pd.Series(
        minimal_returns_df['return'].values,
        index=pd.MultiIndex.from_frame(minimal_returns_df[['date', 'symbol']])
    )
    
    model.fit(minimal_exposures, minimal_returns, min_observations=10)
    
    # Should use default model due to insufficient data
    factor_cov = model.get_factor_covariance()
    assert isinstance(factor_cov, pd.DataFrame)

