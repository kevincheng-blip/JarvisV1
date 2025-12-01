"""Portfolio Risk Calculation Tools

This module provides utility functions for calculating portfolio-level risks
using the multi-factor risk model.

Portfolio risk is decomposed into:
- Factor risk: Risk from factor exposures
- Specific risk: Risk from individual stock idiosyncratic movements

Based on J-GOD Risk Model v1.0 standard: Σ = B F Bᵀ + D
Reference: docs/J-GOD_RISK_MODEL_STANDARD_v1.md
"""

from __future__ import annotations

from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from jgod.risk.exposure_schema import FactorExposure
from jgod.risk.risk_model import MultiFactorRiskModel
from jgod.risk.risk_factors import STANDARD_FACTOR_NAMES


def compute_portfolio_exposure(
    weights: Dict[str, float],
    exposures: List[FactorExposure],
    as_of: pd.Timestamp,
    factor_names: List[str],
    beta_matrix: Optional[np.ndarray] = None,
    symbols: Optional[List[str]] = None
) -> np.ndarray:
    """Compute portfolio factor exposure vector
    
    Calculates the weighted average factor exposure for a portfolio:
        β_p = wᵀ B = Σ_i w_i * β_i
    
    Where:
        w_i: Weight of stock i in portfolio
        β_i: Factor exposure vector of stock i (from B matrix)
    
    If beta_matrix is provided, uses it directly (wᵀB).
    Otherwise, calculates from FactorExposure objects.
    
    Args:
        weights: Dictionary mapping symbol to portfolio weight
                 (e.g., {"2330": 0.5, "2317": 0.5})
        exposures: List of FactorExposure objects across multiple stocks and dates
        as_of: Date to evaluate portfolio exposure
        factor_names: List of factor names (must match MultiFactorRiskModel.factor_names)
        beta_matrix: Optional B matrix (N × K) from RiskModel.get_beta_matrix()
        symbols: Optional list of symbols corresponding to beta_matrix rows
    
    Returns:
        numpy array representing portfolio factor exposure vector β_p
        Length equals len(factor_names)
        Returns zero vector if no matching exposures found
    """
    # If beta_matrix is provided, use it directly
    if beta_matrix is not None and symbols is not None:
        # Build weight vector matching symbols order
        weight_vector = np.array([weights.get(symbol, 0.0) for symbol in symbols])
        
        # Calculate: β_p = wᵀ B
        portfolio_exposure = weight_vector @ beta_matrix
        
        return portfolio_exposure
    
    # Otherwise, calculate from exposures
    # Filter exposures to the specified date
    date_exposures = [
        exp for exp in exposures
        if pd.Timestamp(exp.date) == pd.Timestamp(as_of)
    ]
    
    if not date_exposures:
        return np.zeros(len(factor_names))
    
    # Initialize portfolio exposure vector
    portfolio_exposure = np.zeros(len(factor_names))
    total_weight = 0.0
    
    # Weighted sum of individual stock exposures
    for exp in date_exposures:
        symbol = exp.symbol
        if symbol in weights:
            weight = weights[symbol]
            stock_exposure = exp.get_exposure_vector(factor_names)
            portfolio_exposure += weight * stock_exposure
            total_weight += weight
    
    # Normalize if total weight doesn't sum to 1.0 (in case of missing stocks)
    if total_weight > 0 and abs(total_weight - 1.0) > 1e-6:
        portfolio_exposure = portfolio_exposure / total_weight
    
    return portfolio_exposure


def compute_portfolio_risk(
    model: MultiFactorRiskModel,
    portfolio_exposure: np.ndarray,
    weights: Dict[str, float]
) -> Dict[str, float]:
    """Compute portfolio risk using multi-factor risk model
    
    Uses J-GOD standard formula: Σ = B F Bᵀ + D
    
    Portfolio risk decomposition:
    - Factor risk: σ_f² = β_p' * F * β_p
    - Specific risk: σ_s² = Σ_i w_i² * D_ii
    - Total risk: σ_p² = σ_f² + σ_s²
    
    Where:
        β_p: Portfolio factor exposure vector (wᵀB)
        F: Factor covariance matrix
        w: Weight vector
        D: Specific risk diagonal matrix
    
    Args:
        model: MultiFactorRiskModel instance
        portfolio_exposure: Portfolio factor exposure vector (from compute_portfolio_exposure)
        weights: Dictionary mapping symbol to portfolio weight
    
    Returns:
        Dictionary with keys:
            - 'total_variance': Total portfolio risk variance
            - 'factor_variance': Risk from factor exposures
            - 'specific_variance': Risk from stock-specific movements
            - 'total_volatility': Total portfolio volatility (sqrt of variance)
            - 'factor_volatility': Factor volatility
            - 'specific_volatility': Specific volatility
    """
    # Factor variance: β_p' * F * β_p
    factor_cov = model.get_factor_covariance().values
    factor_variance = float(portfolio_exposure.T @ factor_cov @ portfolio_exposure)
    factor_variance = max(factor_variance, 0.0)
    
    # Specific variance: Σ_i w_i² * D_ii = Σ_i w_i² * σ_e,i²
    specific_variance = 0.0
    for symbol, weight in weights.items():
        spec_vol = model.get_specific_risk(symbol)
        specific_variance += (weight ** 2) * (spec_vol ** 2)
    
    # Total variance
    total_variance = factor_variance + specific_variance
    
    # Convert to volatilities (annualized)
    total_volatility = np.sqrt(total_variance) if total_variance > 0 else 0.0
    factor_volatility = np.sqrt(factor_variance) if factor_variance > 0 else 0.0
    specific_volatility = np.sqrt(specific_variance) if specific_variance > 0 else 0.0
    
    return {
        'total_variance': float(total_variance),
        'factor_variance': float(factor_variance),
        'specific_variance': float(specific_variance),
        'total_volatility': float(total_volatility),
        'factor_volatility': float(factor_volatility),
        'specific_volatility': float(specific_volatility),
    }


def decompose_portfolio_risk_by_factor(
    model: MultiFactorRiskModel,
    portfolio_exposure: np.ndarray
) -> Dict[str, float]:
    """Decompose portfolio factor risk by individual factors
    
    Shows the contribution of each factor to portfolio factor risk.
    Must decompose according to the 8 standard risk factors.
    
    Formula for each factor i:
        Contribution_i = β_p,i² * F_ii + Σ_{j≠i} β_p,i * β_p,j * F_ij
    
    Args:
        model: MultiFactorRiskModel instance
        portfolio_exposure: Portfolio factor exposure vector
    
    Returns:
        Dictionary mapping factor names to their risk contributions (variance)
        Keys must be from STANDARD_FACTOR_NAMES
    """
    factor_cov = model.get_factor_covariance()
    factor_names = model.factor_names
    
    contributions = {}
    
    for i, factor_name in enumerate(factor_names):
        # Contribution from this factor (including interactions with other factors)
        contrib = 0.0
        
        for j in range(len(factor_names)):
            if i == j:
                # Diagonal contribution: β_i² * F_ii
                contrib += (portfolio_exposure[i] ** 2) * factor_cov.iloc[i, j]
            else:
                # Cross-factor contribution: β_i * β_j * F_ij
                contrib += portfolio_exposure[i] * portfolio_exposure[j] * factor_cov.iloc[i, j]
        
        contributions[factor_name] = float(contrib)
    
    return contributions
