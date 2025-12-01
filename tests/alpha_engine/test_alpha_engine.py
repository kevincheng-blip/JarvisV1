"""Tests for Alpha Engine Main Controller"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from jgod.alpha_engine.alpha_engine import AlphaEngine
from jgod.alpha_engine.factor_base import FactorBase


@pytest.fixture
def sample_stock_data():
    """Create sample stock data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    # Generate synthetic price data
    np.random.seed(42)
    price_base = 100.0
    returns = np.random.randn(100) * 0.02  # 2% daily volatility
    prices = [price_base]
    for r in returns[1:]:
        prices.append(prices[-1] * (1 + r))
    
    df = pd.DataFrame({
        'date': dates,
        'close': prices,
        'open': prices,
        'high': [p * 1.02 for p in prices],
        'low': [p * 0.98 for p in prices],
        'volume': np.random.randint(1000000, 10000000, 100),
        'foreign_flow': np.random.randn(100) * 1000000,
        'ecosystem_flow': np.random.randn(100) * 500000,
        'major_buy_volume': np.random.randint(100000, 500000, 100),
        'major_sell_volume': np.random.randint(100000, 500000, 100),
    })
    
    df = df.set_index('date')
    return df


@pytest.fixture
def alpha_engine():
    """Create AlphaEngine instance for testing"""
    return AlphaEngine(enable_micro_momentum=False)


def test_alpha_engine_init():
    """Test AlphaEngine initialization"""
    engine = AlphaEngine()
    assert engine is not None
    assert len(engine.factors) == 5  # 5 factors (excluding micro_momentum)
    
    engine_with_micro = AlphaEngine(enable_micro_momentum=True)
    assert len(engine_with_micro.factors) == 6  # 6 factors (including micro_momentum)


def test_alpha_engine_compute_all(sample_stock_data, alpha_engine):
    """Test compute_all method"""
    result_df = alpha_engine.compute_all(sample_stock_data)
    
    # Check result structure
    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == len(sample_stock_data)
    assert result_df.index.equals(sample_stock_data.index)
    
    # Check required columns
    expected_columns = [
        'flow_score', 'divergence_score', 'reversion_score',
        'inertia_score', 'value_quality_score', 'micro_momentum_score',
        'composite_alpha'
    ]
    for col in expected_columns:
        assert col in result_df.columns
    
    # Check no NaN values
    assert not result_df.isna().any().any()
    
    # Check composite_alpha is computed
    assert 'composite_alpha' in result_df.columns
    assert not result_df['composite_alpha'].isna().any()


def test_alpha_engine_empty_data(alpha_engine):
    """Test compute_all with empty DataFrame"""
    empty_df = pd.DataFrame()
    result_df = alpha_engine.compute_all(empty_df)
    
    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == 0


def test_alpha_engine_minimal_data(alpha_engine):
    """Test compute_all with minimal required data"""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    minimal_df = pd.DataFrame({
        'close': np.random.rand(50) * 100 + 100,
        'volume': np.random.randint(1000000, 5000000, 50),
    }, index=dates)
    
    result_df = alpha_engine.compute_all(minimal_df)
    
    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == len(minimal_df)
    assert not result_df.isna().any().any()


def test_alpha_engine_custom_weights():
    """Test AlphaEngine with custom factor weights"""
    custom_weights = {
        'flow_score': 0.4,
        'divergence_score': 0.3,
        'reversion_score': 0.2,
        'inertia_score': 0.1,
        'value_quality_score': 0.0,
    }
    
    engine = AlphaEngine(factor_weights=custom_weights)
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    df = pd.DataFrame({
        'close': np.random.rand(50) * 100 + 100,
        'volume': np.random.randint(1000000, 5000000, 50),
    }, index=dates)
    
    result_df = engine.compute_all(df)
    assert 'composite_alpha' in result_df.columns


def test_alpha_engine_get_factor(alpha_engine):
    """Test get_factor method"""
    factor = alpha_engine.get_factor('flow_factor')
    assert factor is not None
    assert factor.name == 'flow_factor'
    
    # Test non-existent factor
    factor = alpha_engine.get_factor('nonexistent_factor')
    assert factor is None


def test_alpha_engine_list_factors(alpha_engine):
    """Test list_factors method"""
    factors = alpha_engine.list_factors()
    assert isinstance(factors, list)
    assert len(factors) == 5
    assert 'flow_factor' in factors
    assert 'divergence_factor' in factors
    assert 'reversion_factor' in factors
    assert 'inertia_factor' in factors
    assert 'value_quality_factor' in factors


def test_alpha_engine_update_weights(alpha_engine):
    """Test update_factor_weights method"""
    new_weights = {
        'flow_score': 0.5,
        'divergence_score': 0.5,
    }
    alpha_engine.update_factor_weights(new_weights)
    
    # Check weights are normalized
    total_weight = sum(alpha_engine.factor_weights.values())
    assert abs(total_weight - 1.0) < 1e-6

