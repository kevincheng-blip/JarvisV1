"""Tests for Portfolio Risk Calculation Tools"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from jgod.risk.risk_model import MultiFactorRiskModel
from jgod.risk.exposure_schema import FactorExposure
from jgod.risk.portfolio_risk import (
    compute_portfolio_exposure,
    compute_portfolio_risk,
    decompose_portfolio_risk_by_factor
)


@pytest.fixture
def sample_factor_names():
    """Sample factor names for testing"""
    return ['flow', 'divergence', 'reversion']


@pytest.fixture
def sample_risk_model(sample_factor_names):
    """Create a simple risk model for testing"""
    model = MultiFactorRiskModel(factor_names=sample_factor_names)
    
    # Set factor covariance manually (identity matrix for simplicity)
    model.factor_cov = pd.DataFrame(
        np.eye(len(sample_factor_names)) * 0.04,  # 20% annual vol per factor
        index=sample_factor_names,
        columns=sample_factor_names
    )
    
    # Set specific risks
    model.specific_risk = {
        'STOCK_A': 0.15,  # 15% annual volatility
        'STOCK_B': 0.20,  # 20% annual volatility
        'STOCK_C': 0.25,  # 25% annual volatility
    }
    
    return model


@pytest.fixture
def sample_exposures(sample_factor_names):
    """Create sample exposures for a specific date"""
    date = pd.Timestamp('2024-01-15')
    
    exposures = [
        FactorExposure(
            symbol='STOCK_A',
            date=date,
            exposures={
                'flow': 0.5,
                'divergence': -0.2,
                'reversion': 0.3,
                'beta': 1.0
            }
        ),
        FactorExposure(
            symbol='STOCK_B',
            date=date,
            exposures={
                'flow': 0.3,
                'divergence': 0.4,
                'reversion': -0.1,
                'beta': 1.0
            }
        ),
        FactorExposure(
            symbol='STOCK_C',
            date=date,
            exposures={
                'flow': -0.1,
                'divergence': 0.2,
                'reversion': 0.5,
                'beta': 1.0
            }
        ),
    ]
    
    return exposures


@pytest.fixture
def sample_weights():
    """Sample portfolio weights"""
    return {
        'STOCK_A': 0.5,
        'STOCK_B': 0.3,
        'STOCK_C': 0.2
    }


def test_compute_portfolio_exposure(sample_exposures, sample_weights, sample_factor_names):
    """Test compute_portfolio_exposure function"""
    date = pd.Timestamp('2024-01-15')
    
    portfolio_exp = compute_portfolio_exposure(
        weights=sample_weights,
        exposures=sample_exposures,
        as_of=date,
        factor_names=sample_factor_names
    )
    
    # Check output shape
    assert isinstance(portfolio_exp, np.ndarray)
    assert len(portfolio_exp) == len(sample_factor_names)
    
    # Check that it's a weighted average
    # Manual calculation for verification
    exp_a = sample_exposures[0].get_exposure_vector(sample_factor_names)
    exp_b = sample_exposures[1].get_exposure_vector(sample_factor_names)
    exp_c = sample_exposures[2].get_exposure_vector(sample_factor_names)
    
    expected = (
        sample_weights['STOCK_A'] * exp_a +
        sample_weights['STOCK_B'] * exp_b +
        sample_weights['STOCK_C'] * exp_c
    )
    
    np.testing.assert_array_almost_equal(portfolio_exp, expected)


def test_compute_portfolio_exposure_wrong_date(sample_exposures, sample_weights, sample_factor_names):
    """Test compute_portfolio_exposure with wrong date"""
    wrong_date = pd.Timestamp('2024-01-20')  # No exposures for this date
    
    portfolio_exp = compute_portfolio_exposure(
        weights=sample_weights,
        exposures=sample_exposures,
        as_of=wrong_date,
        factor_names=sample_factor_names
    )
    
    # Should return zero vector
    assert isinstance(portfolio_exp, np.ndarray)
    assert len(portfolio_exp) == len(sample_factor_names)
    assert np.allclose(portfolio_exp, 0.0)


def test_compute_portfolio_exposure_missing_stock(sample_exposures, sample_weights, sample_factor_names):
    """Test compute_portfolio_exposure with missing stock in exposures"""
    incomplete_weights = {
        'STOCK_A': 0.5,
        'STOCK_B': 0.3,
        'STOCK_D': 0.2  # This stock is not in exposures
    }
    
    date = pd.Timestamp('2024-01-15')
    
    portfolio_exp = compute_portfolio_exposure(
        weights=incomplete_weights,
        exposures=sample_exposures,
        as_of=date,
        factor_names=sample_factor_names
    )
    
    # Should only include STOCK_A and STOCK_B
    assert isinstance(portfolio_exp, np.ndarray)
    assert len(portfolio_exp) == len(sample_factor_names)


def test_compute_portfolio_risk(sample_risk_model, sample_weights, sample_factor_names):
    """Test compute_portfolio_risk function"""
    # Create portfolio exposure vector
    portfolio_exposure = np.array([0.3, -0.1, 0.2])
    
    # Calculate portfolio risk
    risk_result = compute_portfolio_risk(
        model=sample_risk_model,
        portfolio_exposure=portfolio_exposure,
        weights=sample_weights
    )
    
    # Check structure
    assert isinstance(risk_result, dict)
    assert 'total_variance' in risk_result
    assert 'factor_variance' in risk_result
    assert 'specific_variance' in risk_result
    assert 'total_volatility' in risk_result
    assert 'factor_volatility' in risk_result
    assert 'specific_volatility' in risk_result
    
    # Check values are non-negative
    assert risk_result['total_variance'] >= 0
    assert risk_result['factor_variance'] >= 0
    assert risk_result['specific_variance'] >= 0
    assert risk_result['total_volatility'] >= 0
    assert risk_result['factor_volatility'] >= 0
    assert risk_result['specific_volatility'] >= 0
    
    # Check variance relationships
    total_expected = risk_result['factor_variance'] + risk_result['specific_variance']
    assert abs(risk_result['total_variance'] - total_expected) < 1e-6
    
    # Check volatility is sqrt of variance
    assert abs(risk_result['total_volatility'] - np.sqrt(risk_result['total_variance'])) < 1e-6
    assert abs(risk_result['factor_volatility'] - np.sqrt(risk_result['factor_variance'])) < 1e-6
    assert abs(risk_result['specific_volatility'] - np.sqrt(risk_result['specific_variance'])) < 1e-6
    
    # Total variance should be >= factor variance
    assert risk_result['total_variance'] >= risk_result['factor_variance']


def test_compute_portfolio_risk_zero_exposure(sample_risk_model, sample_weights):
    """Test compute_portfolio_risk with zero portfolio exposure"""
    portfolio_exposure = np.array([0.0, 0.0, 0.0])
    
    risk_result = compute_portfolio_risk(
        model=sample_risk_model,
        portfolio_exposure=portfolio_exposure,
        specific_risk=sample_risk_model.specific_risk,
        weights=sample_weights
    )
    
    # Factor variance should be zero
    assert risk_result['factor_variance'] == 0.0
    assert risk_result['factor_volatility'] == 0.0
    
    # Total variance should equal specific variance
    assert abs(risk_result['total_variance'] - risk_result['specific_variance']) < 1e-6


def test_decompose_portfolio_risk_by_factor(sample_risk_model, sample_factor_names):
    """Test decompose_portfolio_risk_by_factor function"""
    portfolio_exposure = np.array([0.5, -0.3, 0.2])
    
    contributions = decompose_portfolio_risk_by_factor(
        model=sample_risk_model,
        portfolio_exposure=portfolio_exposure
    )
    
    # Check structure
    assert isinstance(contributions, dict)
    assert len(contributions) == len(sample_factor_names)
    
    for factor in sample_factor_names:
        assert factor in contributions
        assert isinstance(contributions[factor], float)


def test_portfolio_risk_integration(sample_exposures, sample_weights, sample_factor_names, sample_risk_model):
    """Integration test: full portfolio risk calculation"""
    date = pd.Timestamp('2024-01-15')
    
    # Step 1: Compute portfolio exposure
    portfolio_exposure = compute_portfolio_exposure(
        weights=sample_weights,
        exposures=sample_exposures,
        as_of=date,
        factor_names=sample_factor_names
    )
    
    # Step 2: Compute portfolio risk
    risk_result = compute_portfolio_risk(
        model=sample_risk_model,
        portfolio_exposure=portfolio_exposure,
        specific_risk=sample_risk_model.specific_risk,
        weights=sample_weights
    )
    
    # Step 3: Decompose by factor
    factor_contributions = decompose_portfolio_risk_by_factor(
        model=sample_risk_model,
        portfolio_exposure=portfolio_exposure
    )
    
    # All should work together
    assert len(portfolio_exposure) == len(sample_factor_names)
    assert risk_result['total_variance'] > 0
    assert len(factor_contributions) == len(sample_factor_names)

