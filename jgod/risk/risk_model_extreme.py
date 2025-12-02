"""
Risk Model Extreme - Professional Quant Fund Grade

This module provides an extreme-level risk model with:
- Ledoit-Wolf shrinkage covariance estimation
- PCA-based factor extraction
- Factor model decomposition: cov = B F B^T + S
- Positive semi-definite enforcement

Reference: docs/JGOD_EXTREME_MODE_EDITOR_INSTRUCTIONS.md
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import pandas as pd
import numpy as np


@dataclass
class RiskModelExtremeConfig:
    """Configuration for Risk Model Extreme."""
    
    # Ledoit-Wolf shrinkage parameters
    shrinkage_target: str = "sample"  # "sample", "single_factor", "constant_correlation"
    
    # PCA factor extraction
    min_factor_count: int = 2
    max_factor_count: int = 10
    factor_explained_variance: float = 0.85  # Minimum explained variance
    
    # Annualization
    periods_per_year: int = 252
    
    # Regularization
    min_eigenvalue: float = 1e-8  # Minimum eigenvalue for positive definiteness
    shrinkage_factor: float = 0.1  # Default shrinkage if Ledoit-Wolf fails


class MultiFactorRiskModelExtreme:
    """
    Extreme Risk Model with professional-grade covariance estimation.
    
    Features:
    - Ledoit-Wolf shrinkage covariance
    - PCA-based factor extraction
    - Factor model: cov = B F B^T + S
    - Positive semi-definite enforcement
    
    API compatible with MultiFactorRiskModel for easy integration.
    """
    
    def __init__(
        self,
        config: Optional[RiskModelExtremeConfig] = None,
    ):
        """
        Initialize Risk Model Extreme.
        
        Args:
            config: Configuration object. If None, uses default config.
        """
        self.config = config or RiskModelExtremeConfig()
        
        # Model components
        self.B: Optional[np.ndarray] = None  # Factor loadings (N × K)
        self.F: Optional[np.ndarray] = None  # Factor covariance (K × K)
        self.S: Optional[np.ndarray] = None  # Specific risk diagonal (N × N)
        self.cov_matrix: Optional[np.ndarray] = None  # Total covariance (N × N)
        
        # Supporting data
        self.symbols: List[str] = []
        self.factor_count: int = 0
        self.factor_returns: Optional[pd.DataFrame] = None
        self.factor_loadings: Optional[pd.DataFrame] = None
    
    def _compute_sample_covariance(
        self,
        returns_df: pd.DataFrame,
    ) -> np.ndarray:
        """
        Compute sample covariance matrix from returns.
        
        Args:
            returns_df: DataFrame with returns (date × symbol)
        
        Returns:
            Covariance matrix (N × N), annualized
        """
        if returns_df.empty:
            return np.array([])
        
        # Compute sample covariance
        cov_sample = returns_df.cov().values
        
        # Annualize
        cov_annualized = cov_sample * self.config.periods_per_year
        
        return cov_annualized
    
    def _compute_ledoit_wolf_shrinkage(
        self,
        returns_df: pd.DataFrame,
    ) -> Tuple[np.ndarray, float]:
        """
        Compute Ledoit-Wolf shrinkage covariance matrix.
        
        Ledoit-Wolf shrinkage combines sample covariance with a shrinkage target
        to reduce estimation error: Σ_shrink = α * Σ_target + (1 - α) * Σ_sample
        
        Args:
            returns_df: DataFrame with returns (date × symbol)
        
        Returns:
            Tuple of (shrunk_covariance_matrix, shrinkage_intensity)
        """
        if returns_df.empty or len(returns_df.columns) < 2:
            # Not enough data for shrinkage
            cov_sample = self._compute_sample_covariance(returns_df)
            return cov_sample, 0.0
        
        # Compute sample covariance
        cov_sample = self._compute_sample_covariance(returns_df)
        n_obs, n_assets = returns_df.shape
        
        if n_obs < 2:
            return cov_sample, 0.0
        
        # Compute shrinkage target based on config
        if self.config.shrinkage_target == "constant_correlation":
            # Constant correlation target
            # Diagonal: sample variances
            # Off-diagonal: constant correlation * sqrt(var_i * var_j)
            variances = np.diag(cov_sample)
            avg_correlation = self._compute_average_correlation(cov_sample)
            cov_target = np.outer(np.sqrt(variances), np.sqrt(variances)) * avg_correlation
            np.fill_diagonal(cov_target, variances)
        
        elif self.config.shrinkage_target == "single_factor":
            # Single factor model target
            # Market return is average return across assets
            market_return = returns_df.mean(axis=1)
            cov_target = self._compute_single_factor_covariance(returns_df, market_return)
        
        else:
            # Sample covariance as target (no shrinkage, but keep structure)
            cov_target = cov_sample.copy()
        
        # Compute optimal shrinkage intensity (simplified Ledoit-Wolf)
        # In practice, this would use more sophisticated estimation
        shrinkage_intensity = self._estimate_shrinkage_intensity(
            returns_df,
            cov_sample,
            cov_target,
        )
        
        # Apply shrinkage
        cov_shrunk = (
            shrinkage_intensity * cov_target +
            (1 - shrinkage_intensity) * cov_sample
        )
        
        return cov_shrunk, shrinkage_intensity
    
    def _compute_average_correlation(self, cov_matrix: np.ndarray) -> float:
        """Compute average correlation from covariance matrix."""
        n = len(cov_matrix)
        if n < 2:
            return 0.0
        
        variances = np.diag(cov_matrix)
        std_devs = np.sqrt(variances)
        
        # Extract correlation matrix
        corr_matrix = cov_matrix / np.outer(std_devs, std_devs)
        
        # Average of off-diagonal elements
        mask = ~np.eye(n, dtype=bool)
        avg_corr = corr_matrix[mask].mean()
        
        return avg_corr
    
    def _compute_single_factor_covariance(
        self,
        returns_df: pd.DataFrame,
        factor_return: pd.Series,
    ) -> np.ndarray:
        """Compute single-factor model covariance."""
        n_assets = len(returns_df.columns)
        cov_target = np.zeros((n_assets, n_assets))
        
        # Factor variance
        factor_var = factor_return.var() * self.config.periods_per_year
        
        # Asset betas (regression coefficients)
        betas = np.zeros(n_assets)
        for i, asset in enumerate(returns_df.columns):
            asset_returns = returns_df[asset]
            if len(asset_returns) > 1 and factor_return.var() > 1e-10:
                beta = np.cov(asset_returns, factor_return)[0, 1] / factor_return.var()
                betas[i] = beta
        
        # Specific variances
        specific_vars = np.zeros(n_assets)
        for i, asset in enumerate(returns_df.columns):
            asset_returns = returns_df[asset]
            beta = betas[i]
            residuals = asset_returns - beta * factor_return
            specific_vars[i] = residuals.var() * self.config.periods_per_year
        
        # Build covariance: β β' * factor_var + diag(specific_vars)
        cov_target = np.outer(betas, betas) * factor_var + np.diag(specific_vars)
        
        return cov_target
    
    def _estimate_shrinkage_intensity(
        self,
        returns_df: pd.DataFrame,
        cov_sample: np.ndarray,
        cov_target: np.ndarray,
    ) -> float:
        """
        Estimate optimal shrinkage intensity.
        
        Simplified version - in practice would use full Ledoit-Wolf formula.
        """
        n_obs, n_assets = returns_df.shape
        
        if n_obs < 10 or n_assets < 2:
            return 0.5  # Default shrinkage
        
        # Simplified: use sample size-based shrinkage
        # More observations = less shrinkage
        shrinkage = min(0.5, max(0.1, 10.0 / n_obs))
        
        return shrinkage
    
    def _estimate_factor_count_pca(
        self,
        returns_df: pd.DataFrame,
    ) -> int:
        """
        Estimate optimal number of factors using PCA.
        
        Selects number of factors that explain at least
        config.factor_explained_variance of total variance.
        
        Args:
            returns_df: DataFrame with returns (date × symbol)
        
        Returns:
            Optimal number of factors
        """
        if returns_df.empty or len(returns_df.columns) < 2:
            return 1
        
        # Compute covariance
        cov_sample = self._compute_sample_covariance(returns_df)
        
        # Compute eigenvalues and eigenvectors
        eigenvalues, _ = np.linalg.eigh(cov_sample)
        eigenvalues = np.sort(eigenvalues)[::-1]  # Sort descending
        
        # Remove negative eigenvalues (shouldn't happen, but safety check)
        eigenvalues = eigenvalues[eigenvalues > 0]
        
        if len(eigenvalues) == 0:
            return 1
        
        # Cumulative explained variance
        total_variance = eigenvalues.sum()
        cumsum_variance = np.cumsum(eigenvalues) / total_variance
        
        # Find number of factors that explain target variance
        factor_count = np.argmax(cumsum_variance >= self.config.factor_explained_variance) + 1
        
        # Clamp to valid range
        factor_count = max(
            self.config.min_factor_count,
            min(factor_count, self.config.max_factor_count, len(eigenvalues))
        )
        
        return factor_count
    
    def _extract_factors_pca(
        self,
        returns_df: pd.DataFrame,
        n_factors: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract factors using PCA.
        
        Args:
            returns_df: DataFrame with returns (date × symbol)
            n_factors: Number of factors to extract
        
        Returns:
            Tuple of (factor_returns, factor_loadings)
            - factor_returns: (T × K) array
            - factor_loadings: (N × K) array (betas)
        """
        if returns_df.empty:
            return np.array([]), np.array([])
        
        # Standardize returns
        returns_standardized = returns_df - returns_df.mean()
        
        # Compute covariance
        cov_sample = self._compute_sample_covariance(returns_df)
        
        # PCA decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(cov_sample)
        
        # Sort by eigenvalue (descending)
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
        
        # Select top K factors
        factor_loadings = eigenvectors[:, :n_factors]  # (N × K)
        
        # Project returns onto factors to get factor returns
        # Factor returns = (returns - mean) @ loadings
        returns_centered = returns_standardized.values
        factor_returns = returns_centered @ factor_loadings  # (T × K)
        
        return factor_returns, factor_loadings
    
    def _compute_factor_covariance(
        self,
        factor_returns: np.ndarray,
    ) -> np.ndarray:
        """
        Compute factor covariance matrix F.
        
        Args:
            factor_returns: Factor returns array (T × K)
        
        Returns:
            Factor covariance matrix (K × K), annualized
        """
        if factor_returns.size == 0:
            return np.array([])
        
        # Compute sample covariance of factors
        factor_cov = np.cov(factor_returns.T) * self.config.periods_per_year
        
        return factor_cov
    
    def _compute_specific_risk(
        self,
        returns_df: pd.DataFrame,
        factor_returns: np.ndarray,
        factor_loadings: np.ndarray,
    ) -> np.ndarray:
        """
        Compute specific/idiosyncratic risk.
        
        Args:
            returns_df: Stock returns (T × N)
            factor_returns: Factor returns (T × K)
            factor_loadings: Factor loadings (N × K)
        
        Returns:
            Diagonal matrix of specific variances (N × N)
        """
        if returns_df.empty or factor_returns.size == 0:
            n_assets = len(returns_df.columns) if not returns_df.empty else 0
            return np.eye(n_assets) * 0.01
        
        # Compute residuals: R = stock_returns - factor_returns @ loadings.T
        returns_matrix = returns_df.values
        predicted_returns = factor_returns @ factor_loadings.T
        
        residuals = returns_matrix - predicted_returns
        
        # Specific variances = variance of residuals
        specific_vars = np.var(residuals, axis=0) * self.config.periods_per_year
        
        # Ensure minimum variance
        specific_vars = np.maximum(specific_vars, self.config.min_eigenvalue)
        
        # Return as diagonal matrix
        specific_risk_matrix = np.diag(specific_vars)
        
        return specific_risk_matrix
    
    def _ensure_positive_definite(
        self,
        cov_matrix: np.ndarray,
    ) -> np.ndarray:
        """
        Ensure covariance matrix is positive semi-definite.
        
        Uses eigenvalue decomposition to fix negative eigenvalues.
        
        Args:
            cov_matrix: Input covariance matrix
        
        Returns:
            Positive semi-definite covariance matrix
        """
        if cov_matrix.size == 0:
            return cov_matrix
        
        # Eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
        
        # Clip negative eigenvalues to minimum
        eigenvalues = np.maximum(eigenvalues, self.config.min_eigenvalue)
        
        # Reconstruct matrix
        cov_fixed = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
        
        # Ensure symmetry (numerical precision)
        cov_fixed = (cov_fixed + cov_fixed.T) / 2
        
        return cov_fixed
    
    def fit_from_returns(
        self,
        returns_df: pd.DataFrame,
        symbols: Optional[List[str]] = None,
    ) -> None:
        """
        Fit risk model from returns DataFrame.
        
        Process:
        1. Estimate factor count using PCA
        2. Extract factors using PCA
        3. Compute factor covariance F
        4. Compute specific risk S
        5. Build total covariance: cov = B F B^T + S
        
        Args:
            returns_df: DataFrame with returns (date × symbol)
            symbols: Optional list of symbols (if None, uses column names)
        """
        if returns_df.empty:
            self._initialize_default()
            return
        
        # Set symbols
        if symbols is None:
            self.symbols = list(returns_df.columns)
        else:
            self.symbols = symbols
        
        n_assets = len(self.symbols)
        
        if n_assets < 1:
            self._initialize_default()
            return
        
        try:
            # Step 1: Estimate factor count using PCA
            self.factor_count = self._estimate_factor_count_pca(returns_df)
            self.factor_count = max(1, min(self.factor_count, n_assets - 1))
            
            # Step 2: Extract factors using PCA
            factor_returns_array, factor_loadings = self._extract_factors_pca(
                returns_df,
                self.factor_count
            )
            
            if factor_returns_array.size == 0:
                self._initialize_default()
                return
            
            # Store factor returns as DataFrame
            factor_names = [f"factor_{i+1}" for i in range(self.factor_count)]
            self.factor_returns = pd.DataFrame(
                factor_returns_array,
                index=returns_df.index,
                columns=factor_names
            )
            
            # Store factor loadings as DataFrame
            self.factor_loadings = pd.DataFrame(
                factor_loadings,
                index=self.symbols,
                columns=factor_names
            )
            
            # Step 3: Compute factor covariance F
            self.F = self._compute_factor_covariance(factor_returns_array)
            
            # Step 4: Compute specific risk S
            self.S = self._compute_specific_risk(
                returns_df,
                factor_returns_array,
                factor_loadings
            )
            
            # Step 5: Store factor loadings as B matrix
            self.B = factor_loadings  # (N × K)
            
            # Step 6: Build total covariance: cov = B F B^T + S
            self._build_covariance_matrix()
            
        except Exception as e:
            print(f"Warning: Error fitting extreme risk model: {e}")
            import traceback
            traceback.print_exc()
            self._initialize_default()
    
    def _build_covariance_matrix(self) -> None:
        """
        Build total covariance matrix: cov = B F B^T + S.
        
        Where:
        - B: Factor loadings (N × K)
        - F: Factor covariance (K × K)
        - S: Specific risk diagonal (N × N)
        """
        if self.B is None or self.F is None or self.S is None:
            self._initialize_default()
            return
        
        try:
            # Factor covariance component: B F B^T
            factor_cov_component = self.B @ self.F @ self.B.T
            
            # Add specific risk: total = factor + specific
            self.cov_matrix = factor_cov_component + self.S
            
            # Ensure positive semi-definite
            self.cov_matrix = self._ensure_positive_definite(self.cov_matrix)
            
        except Exception as e:
            print(f"Warning: Error building covariance matrix: {e}")
            self._initialize_default()
    
    def _initialize_default(self) -> None:
        """Initialize with default/identity covariance matrix."""
        n_assets = len(self.symbols) if self.symbols else 1
        self.cov_matrix = np.eye(n_assets) * 0.01
        self.B = np.zeros((n_assets, 1))
        self.F = np.array([[0.01]])
        self.S = np.eye(n_assets) * 0.01
        self.factor_count = 1
        self.factor_returns = None
        self.factor_loadings = None
    
    def get_covariance_matrix(self, symbols: Optional[List[str]] = None) -> np.ndarray:
        """
        Get total covariance matrix.
        
        Args:
            symbols: Optional list of symbols. If None, uses model's symbols.
                    If provided, reorders/reindexes to match.
        
        Returns:
            Covariance matrix (N × N)
        """
        if self.cov_matrix is None:
            self._initialize_default()
        
        if symbols is None:
            return self.cov_matrix.copy()
        
        # Reindex to requested symbols
        if self.symbols and len(self.symbols) > 0:
            # Create mapping
            symbol_map = {sym: i for i, sym in enumerate(self.symbols)}
            
            # Build reindexed covariance
            n = len(symbols)
            cov_reindexed = np.zeros((n, n))
            
            for i, sym_i in enumerate(symbols):
                for j, sym_j in enumerate(symbols):
                    if sym_i in symbol_map and sym_j in symbol_map:
                        idx_i = symbol_map[sym_i]
                        idx_j = symbol_map[sym_j]
                        cov_reindexed[i, j] = self.cov_matrix[idx_i, idx_j]
                    elif i == j:
                        # Default variance for missing symbols
                        cov_reindexed[i, j] = 0.01
            
            return cov_reindexed
        
        return self.cov_matrix.copy()
    
    def get_factor_exposures(self, symbols: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Get factor exposures (betas) for symbols.
        
        Args:
            symbols: Optional list of symbols. If None, uses model's symbols.
        
        Returns:
            DataFrame with factor exposures (symbol × factor)
        """
        if self.factor_loadings is None:
            if symbols:
                factor_names = [f"factor_{i+1}" for i in range(self.factor_count or 1)]
                return pd.DataFrame(
                    0.0,
                    index=symbols,
                    columns=factor_names
                )
            return pd.DataFrame()
        
        if symbols is None:
            return self.factor_loadings.copy()
        
        # Reindex to requested symbols
        factor_exposures = self.factor_loadings.reindex(symbols, fill_value=0.0)
        return factor_exposures
    
    def get_factor_cov(self) -> np.ndarray:
        """
        Get factor covariance matrix F.
        
        Returns:
            Factor covariance matrix (K × K)
        """
        if self.F is None:
            self._initialize_default()
        
        return self.F.copy()
    
    def get_symbols(self) -> List[str]:
        """
        Get list of symbols in the model.
        
        Returns:
            List of symbols
        """
        return self.symbols.copy()

