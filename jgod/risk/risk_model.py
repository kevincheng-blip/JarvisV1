"""Multi-Factor Risk Model

This module implements a multi-factor risk model that decomposes stock returns
into factor-driven and idiosyncratic components, and estimates the covariance
structure of factors and specific risks.

Based on J-GOD Risk Model v1.0 standard specification:
- Full risk model: Σ = B F Bᵀ + D
- Betas (B): 12-month WLS regression + EWMA half-life 60
- Factor covariance (F): EWMA with λ = 0.94
- Specific risk (D): EWMA residual variance

Reference: docs/J-GOD_RISK_MODEL_STANDARD_v1.md
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from jgod.risk.exposure_schema import FactorExposure
from jgod.risk.risk_factors import STANDARD_FACTOR_NAMES


def _validate_factor_names(factor_names: List[str]) -> None:
    """Validate that all factor names are in the standard list
    
    Args:
        factor_names: List of factor names to validate
    
    Raises:
        ValueError: If any factor name is not in STANDARD_FACTOR_NAMES
    """
    invalid_factors = [f for f in factor_names if f not in STANDARD_FACTOR_NAMES]
    if invalid_factors:
        raise ValueError(
            f"Invalid factor names: {invalid_factors}. "
            f"Standard factor names are: {STANDARD_FACTOR_NAMES}"
        )


def _winsorize_series(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    """Winsorize a series to remove outliers
    
    Args:
        series: Input series
        lower: Lower quantile (default: 0.01, i.e., ±3σ ≈ 1%)
        upper: Upper quantile (default: 0.99)
    
    Returns:
        Winsorized series
    """
    if series.empty:
        return series
    
    lower_bound = series.quantile(lower)
    upper_bound = series.quantile(upper)
    
    return series.clip(lower=lower_bound, upper=upper_bound)


def _calculate_ewma_weights(n_observations: int, half_life: float = 60.0) -> np.ndarray:
    """Calculate EWMA weights with given half-life
    
    Args:
        n_observations: Number of observations
        half_life: Half-life in periods (default: 60)
    
    Returns:
        Array of weights (most recent observation has highest weight)
    """
    # Calculate decay factor
    decay_factor = np.exp(-np.log(2) / half_life)
    
    # Generate weights (most recent = 1, older = decay_factor, decay_factor^2, ...)
    weights = np.array([decay_factor ** i for i in range(n_observations - 1, -1, -1)])
    
    # Normalize so weights sum to n_observations
    weights = weights / weights.sum() * n_observations
    
    return weights


def _calculate_ewma_covariance(
    returns_df: pd.DataFrame,
    lambda_param: float = 0.94
) -> pd.DataFrame:
    """Calculate EWMA covariance matrix
    
    Formula: Cov_t = λ * Cov_{t-1} + (1 - λ) * r_t * r_tᵀ
    
    Args:
        returns_df: DataFrame with dates as index and returns as columns
        lambda_param: Decay factor (default: 0.94)
    
    Returns:
        Covariance matrix (annualized)
    """
    if returns_df.empty:
        return pd.DataFrame()
    
    # Initialize covariance matrix
    n_factors = len(returns_df.columns)
    cov_matrix = np.eye(n_factors) * 1e-6
    
    # Update covariance using EWMA recursion
    for i, (date, row) in enumerate(returns_df.iterrows()):
        r = row.values.reshape(-1, 1)
        cov_matrix = lambda_param * cov_matrix + (1 - lambda_param) * (r @ r.T)
    
    # Annualize (assuming daily returns)
    cov_matrix = cov_matrix * 252
    
    # Ensure positive semi-definite
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    eigenvalues = np.maximum(eigenvalues, 0)
    cov_matrix = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
    
    return pd.DataFrame(
        cov_matrix,
        index=returns_df.columns,
        columns=returns_df.columns
    )


class MultiFactorRiskModel:
    """Multi-Factor Risk Model
    
    Implements J-GOD Risk Model v1.0 standard:
    - Σ = B F Bᵀ + D
    
    Where:
        Σ: Total covariance matrix (N × N)
        B: Factor exposure matrix (N × K)
        F: Factor covariance matrix (K × K)
        D: Specific risk diagonal matrix (N × N)
    
    Based on: docs/J-GOD_RISK_MODEL_STANDARD_v1.md
    
    Example:
        model = MultiFactorRiskModel(factor_names=STANDARD_FACTOR_NAMES)
        
        # Fit the model using historical data
        model.fit(exposures, returns)
        
        # Get total covariance matrix
        cov_matrix = model.get_covariance_matrix()
        
        # Explain risk for a single stock
        risk_decomp = model.explain_risk(exposure)
    """
    
    def __init__(self, factor_names: Optional[List[str]] = None):
        """Initialize Multi-Factor Risk Model
        
        Args:
            factor_names: List of factor names (must be from STANDARD_FACTOR_NAMES)
                         If None, uses all 8 standard factors
        
        Raises:
            ValueError: If factor_names contains invalid factor names
        """
        # Use standard factors if not provided
        if factor_names is None:
            factor_names = STANDARD_FACTOR_NAMES
        
        # Validate factor names
        _validate_factor_names(factor_names)
        
        self.factor_names = factor_names
        self.K = len(factor_names)  # Number of factors
        
        # Model components
        self.B: Optional[np.ndarray] = None  # Factor exposure matrix (N × K)
        self.F: Optional[pd.DataFrame] = None  # Factor covariance matrix (K × K)
        self.D: Optional[np.ndarray] = None  # Specific risk diagonal matrix (N × N)
        self.cov_matrix: Optional[np.ndarray] = None  # Total covariance matrix (N × N)
        
        # Supporting data
        self.symbols: List[str] = []  # List of symbols (order matches B rows)
        self.specific_risk: Dict[str, float] = {}  # symbol -> specific volatility
        self.factor_returns: Optional[pd.DataFrame] = None  # Factor returns time series
        self.residuals: Dict[str, List[float]] = {}  # symbol -> list of residuals
        
        # Model parameters (from standard specification)
        self.beta_regression_window = 252  # 12 months trading days
        self.ewma_half_life = 60.0  # Half-life for beta regression weights
        self.factor_cov_lambda = 0.94  # EWMA decay for factor covariance
        self.specific_risk_lambda = 0.94  # EWMA decay for specific risk
        
    def fit(
        self,
        exposures: List[FactorExposure],
        returns: pd.Series,
        factor_returns: Optional[pd.DataFrame] = None,
        min_observations: int = 252
    ) -> None:
        """Fit the risk model using historical data
        
        Implements J-GOD standard:
        1. Estimate Betas (B) using 12-month WLS regression with EWMA weights
        2. Estimate Factor Covariance (F) using EWMA (λ=0.94)
        3. Estimate Specific Risk (D) using EWMA residual variance
        4. Build total covariance matrix: Σ = B F Bᵀ + D
        
        Args:
            exposures: List of FactorExposure objects across multiple stocks and dates
            returns: Series of stock returns with MultiIndex (date, symbol)
                     Values should be daily returns
            factor_returns: Optional DataFrame of factor returns (date × factors)
                           If None, will be estimated from exposures and returns
            min_observations: Minimum number of observations required (default: 252)
        
        Note:
            If insufficient data, the model will use default values.
        """
        if not exposures or returns.empty:
            self._initialize_default_model()
            return
        
        try:
            # Prepare data
            aligned_data = self._prepare_aligned_data(exposures, returns)
            
            if len(aligned_data) < min_observations:
                print(f"Warning: Insufficient data ({len(aligned_data)} < {min_observations}). Using default model.")
                self._initialize_default_model()
                return
            
            # Step 1: Get or estimate factor returns
            if factor_returns is None:
                factor_returns = self._estimate_factor_returns_from_exposures(aligned_data)
            
            if factor_returns is None or len(factor_returns) < min_observations:
                print("Warning: Insufficient factor returns. Using default model.")
                self._initialize_default_model()
                return
            
            # Winsorize factor returns and stock returns
            factor_returns = self._winsorize_factor_returns(factor_returns)
            aligned_data = self._winsorize_stock_returns(aligned_data)
            
            # Step 2: Estimate factor covariance matrix F (EWMA, λ=0.94)
            self.F = self._estimate_factor_covariance_ewma(factor_returns)
            
            # Step 3: Estimate Betas (B) using WLS regression (12 months, EWMA weights)
            self.B, self.symbols, residuals_dict = self._estimate_betas_wls(
                aligned_data, factor_returns
            )
            
            # Step 4: Estimate Specific Risk (D) using EWMA residual variance
            self.D, self.specific_risk = self._estimate_specific_risk_ewma(
                residuals_dict, self.symbols
            )
            
            # Step 5: Build total covariance matrix Σ = B F Bᵀ + D
            self._build_covariance_matrix()
            
            # Store factor returns for diagnostics
            self.factor_returns = factor_returns
            self.residuals = residuals_dict
            
        except Exception as e:
            print(f"Warning: Error fitting risk model: {e}. Using default model.")
            import traceback
            traceback.print_exc()
            self._initialize_default_model()
    
    def _prepare_aligned_data(
        self,
        exposures: List[FactorExposure],
        returns: pd.Series
    ) -> List[Dict]:
        """Prepare aligned data for estimation
        
        Args:
            exposures: List of FactorExposure objects
            returns: Series of stock returns
        
        Returns:
            List of dictionaries with 'date', 'symbol', 'return', 'exposure_vector'
        """
        # Build exposure mapping
        exposure_dict = {}
        for exp in exposures:
            key = (pd.Timestamp(exp.date), exp.symbol)
            exposure_dict[key] = exp
        
        # Align returns with exposures
        aligned_data = []
        
        if isinstance(returns.index, pd.MultiIndex):
            for (date, symbol), ret in returns.items():
                key = (pd.Timestamp(date), symbol)
                if key in exposure_dict:
                    exp = exposure_dict[key]
                    aligned_data.append({
                        'date': pd.Timestamp(date),
                        'symbol': symbol,
                        'return': float(ret),
                        'exposure_vector': exp.get_exposure_vector(self.factor_names)
                    })
        else:
            for idx, ret in returns.items():
                if isinstance(idx, tuple) and len(idx) == 2:
                    date, symbol = idx
                    key = (pd.Timestamp(date), symbol)
                    if key in exposure_dict:
                        exp = exposure_dict[key]
                        aligned_data.append({
                            'date': pd.Timestamp(date),
                            'symbol': symbol,
                            'return': float(ret),
                            'exposure_vector': exp.get_exposure_vector(self.factor_names)
                        })
        
        return aligned_data
    
    def _estimate_factor_returns_from_exposures(
        self,
        aligned_data: List[Dict]
    ) -> Optional[pd.DataFrame]:
        """Estimate factor returns using cross-sectional regression
        
        Args:
            aligned_data: List of aligned data dictionaries
        
        Returns:
            DataFrame of factor returns (date × factors)
        """
        # Group by date
        date_dict = {}
        for row in aligned_data:
            date = row['date']
            if date not in date_dict:
                date_dict[date] = []
            date_dict[date].append(row)
        
        factor_returns_list = []
        factor_dates = []
        
        for date in sorted(date_dict.keys()):
            rows = date_dict[date]
            
            if len(rows) < self.K:  # Need at least K observations
                continue
            
            # Build design matrix and return vector
            X = np.array([row['exposure_vector'] for row in rows])
            y = np.array([row['return'] for row in rows])
            
            # Cross-sectional regression: y = X * f
            try:
                XtX = X.T @ X
                if np.linalg.cond(XtX) > 1e10:
                    continue
                
                factor_ret = np.linalg.solve(XtX, X.T @ y)
                factor_returns_list.append(factor_ret)
                factor_dates.append(date)
            except np.linalg.LinAlgError:
                continue
        
        if not factor_returns_list:
            return None
        
        return pd.DataFrame(
            factor_returns_list,
            index=pd.to_datetime(factor_dates),
            columns=self.factor_names
        )
    
    def _winsorize_factor_returns(self, factor_returns: pd.DataFrame) -> pd.DataFrame:
        """Winsorize factor returns (±3σ)
        
        Args:
            factor_returns: DataFrame of factor returns
        
        Returns:
            Winsorized factor returns
        """
        winsorized = factor_returns.copy()
        for col in winsorized.columns:
            winsorized[col] = _winsorize_series(winsorized[col], lower=0.001, upper=0.999)
        return winsorized
    
    def _winsorize_stock_returns(self, aligned_data: List[Dict]) -> List[Dict]:
        """Winsorize stock returns (±3σ)
        
        Args:
            aligned_data: List of aligned data dictionaries
        
        Returns:
            List with winsorized returns
        """
        returns = [row['return'] for row in aligned_data]
        returns_series = pd.Series(returns)
        returns_winsorized = _winsorize_series(returns_series, lower=0.001, upper=0.999)
        
        winsorized_data = aligned_data.copy()
        for i, row in enumerate(winsorized_data):
            row['return'] = float(returns_winsorized.iloc[i])
        
        return winsorized_data
    
    def _estimate_factor_covariance_ewma(
        self,
        factor_returns: pd.DataFrame
    ) -> pd.DataFrame:
        """Estimate factor covariance matrix using EWMA (λ=0.94)
        
        Formula: Cov_t = λ * Cov_{t-1} + (1 - λ) * r_t * r_tᵀ
        
        Args:
            factor_returns: DataFrame of factor returns (date × factors)
        
        Returns:
            Factor covariance matrix (K × K)
        """
        if factor_returns.empty:
            # Return default identity matrix
            return pd.DataFrame(
                np.eye(self.K) * 1e-6,
                index=self.factor_names,
                columns=self.factor_names
            )
        
        cov_matrix = _calculate_ewma_covariance(
            factor_returns,
            lambda_param=self.factor_cov_lambda
        )
        
        return cov_matrix
    
    def _estimate_betas_wls(
        self,
        aligned_data: List[Dict],
        factor_returns: pd.DataFrame
    ) -> Tuple[np.ndarray, List[str], Dict[str, List[float]]]:
        """Estimate Betas using WLS regression with EWMA weights
        
        Specification:
        - Regression window: 12 months (252 trading days)
        - Weights: EWMA with half-life = 60
        - Winsorization: ±3σ (already done in fit())
        
        Args:
            aligned_data: List of aligned data dictionaries
            factor_returns: DataFrame of factor returns
        
        Returns:
            Tuple of (B matrix, symbols list, residuals dictionary)
        """
        # Group by symbol
        symbol_dict = {}
        for row in aligned_data:
            symbol = row['symbol']
            if symbol not in symbol_dict:
                symbol_dict[symbol] = []
            symbol_dict[symbol].append(row)
        
        # Sort symbols for consistent ordering
        symbols = sorted(symbol_dict.keys())
        
        # Estimate beta for each symbol
        beta_rows = []
        residuals_dict = {}
        
        for symbol in symbols:
            rows = symbol_dict[symbol]
            
            # Sort by date
            rows.sort(key=lambda x: x['date'])
            
            # Get recent 252 days (or all if less)
            recent_rows = rows[-self.beta_regression_window:]
            
            if len(recent_rows) < self.K:  # Need at least K observations
                # Use zero beta as default
                beta_rows.append(np.zeros(self.K))
                residuals_dict[symbol] = []
                continue
            
            # Extract dates, returns, and exposures
            dates = [row['date'] for row in recent_rows]
            returns = np.array([row['return'] for row in recent_rows])
            exposure_matrix = np.array([row['exposure_vector'] for row in recent_rows])
            
            # Get corresponding factor returns
            factor_ret_rows = []
            for date in dates:
                if date in factor_returns.index:
                    factor_ret_rows.append(factor_returns.loc[date].values)
                else:
                    # If factor return missing, skip this observation
                    continue
            
            if len(factor_ret_rows) < self.K:
                # Use recent exposure as fallback
                beta = np.array(recent_rows[-1]['exposure_vector']) if recent_rows else np.zeros(self.K)
                beta_rows.append(beta)
                residuals_dict[symbol] = []
                continue
            
            # Build factor return matrix (T × K)
            F_matrix = np.array(factor_ret_rows)
            
            # Align returns with factor returns (remove missing dates)
            aligned_returns = []
            aligned_exposures = []
            for i, date in enumerate(dates):
                if date in factor_returns.index:
                    aligned_returns.append(returns[i])
                    aligned_exposures.append(exposure_matrix[i])
            
            if len(aligned_returns) < self.K:
                # Use recent exposure as fallback
                beta = exposure_aligned[-1] if len(exposure_aligned) > 0 else np.zeros(self.K)
                beta_rows.append(beta)
                residuals_dict[symbol] = []
                continue
            
            returns_aligned = np.array(aligned_returns)
            exposure_aligned = np.array(aligned_exposures)
            
            # Build matrices for WLS regression: R = F * beta + epsilon
            R = returns_aligned.reshape(-1, 1)  # (T × 1)
            F = F_matrix  # (T × K)
            
            # Calculate EWMA weights (half-life = 60)
            T = len(R)
            weights = _calculate_ewma_weights(T, half_life=self.ewma_half_life)
            W = np.diag(weights)  # Weight matrix (T × T)
            
            # Weighted Least Squares: beta = (F' W F)^(-1) F' W R
            try:
                FtWF = F.T @ W @ F
                
                # Check condition number
                if np.linalg.cond(FtWF) > 1e10:
                    # Use recent exposure as fallback
                    beta = exposure_aligned[-1] if len(exposure_aligned) > 0 else np.zeros(self.K)
                    residuals_dict[symbol] = []
                else:
                    beta = np.linalg.solve(FtWF, F.T @ W @ R).flatten()
                    
                    # Calculate residuals: epsilon = R - F * beta
                    predicted = F @ beta
                    residuals = (R.flatten() - predicted).tolist()
                    residuals_dict[symbol] = residuals
                
            except np.linalg.LinAlgError:
                # Use recent exposure as fallback
                beta = exposure_aligned[-1] if len(exposure_aligned) > 0 else np.zeros(self.K)
                residuals_dict[symbol] = []
            
            beta_rows.append(beta)
        
        # Build B matrix (N × K)
        B = np.array(beta_rows)
        
        return B, symbols, residuals_dict
    
    def _estimate_specific_risk_ewma(
        self,
        residuals_dict: Dict[str, List[float]],
        symbols: List[str]
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """Estimate specific risk using EWMA residual variance
        
        Formula: D_i = EWMA(Var(ε_i))
        
        Args:
            residuals_dict: Dictionary mapping symbol to list of residuals
            symbols: List of symbols (order matches B matrix rows)
        
        Returns:
            Tuple of (D diagonal matrix, specific_risk dictionary)
        """
        N = len(symbols)
        D_diagonal = np.zeros(N)
        specific_risk_dict = {}
        
        lambda_param = self.specific_risk_lambda
        
        for i, symbol in enumerate(symbols):
            residuals = residuals_dict.get(symbol, [])
            
            if len(residuals) < 10:
                # Not enough data, use default
                D_diagonal[i] = 1e-6
                specific_risk_dict[symbol] = np.sqrt(1e-6)
                continue
            
            # Calculate EWMA variance of residuals
            residuals_array = np.array(residuals)
            
            # Initialize variance
            var_ewma = np.var(residuals_array) * 252  # Annualize
            
            # Apply EWMA recursion
            for residual in residuals_array:
                var_ewma = lambda_param * var_ewma + (1 - lambda_param) * ((residual * np.sqrt(252)) ** 2)
            
            # Ensure non-negative
            var_ewma = max(var_ewma, 1e-6)
            
            D_diagonal[i] = var_ewma
            specific_risk_dict[symbol] = np.sqrt(var_ewma)  # Store as volatility
        
        # Build D as diagonal matrix
        D = np.diag(D_diagonal)
        
        return D, specific_risk_dict
    
    def _build_covariance_matrix(self) -> None:
        """Build total covariance matrix: Σ = B F Bᵀ + D
        
        This is the core of J-GOD Risk Model v1.0
        """
        if self.B is None or self.F is None or self.D is None:
            # Use default if components missing
            N = len(self.symbols) if self.symbols else 1
            self.cov_matrix = np.eye(N) * 1e-6
            return
        
        # Get F as numpy array
        F_array = self.F.values
        
        # Calculate: Σ = B F Bᵀ + D
        self.cov_matrix = self.B @ F_array @ self.B.T + self.D
        
        # Ensure positive semi-definite
        eigenvalues, eigenvectors = np.linalg.eigh(self.cov_matrix)
        eigenvalues = np.maximum(eigenvalues, 1e-8)  # Ensure positive
        self.cov_matrix = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
    
    def _initialize_default_model(self) -> None:
        """Initialize model with default (neutral) values"""
        self.B = None
        self.F = pd.DataFrame(
            np.eye(self.K) * 1e-6,
            index=self.factor_names,
            columns=self.factor_names
        )
        self.D = None
        self.cov_matrix = None
        self.symbols = []
        self.specific_risk = {}
        self.residuals = {}
    
    def get_factor_covariance(self) -> pd.DataFrame:
        """Get factor covariance matrix F
        
        Returns:
            DataFrame representing F (K × K)
        """
        if self.F is None:
            self.F = pd.DataFrame(
                np.eye(self.K) * 1e-6,
                index=self.factor_names,
                columns=self.factor_names
            )
        return self.F.copy()
    
    def get_beta_matrix(self) -> Optional[np.ndarray]:
        """Get factor exposure matrix B
        
        Returns:
            B matrix (N × K), or None if not fitted
        """
        return self.B.copy() if self.B is not None else None
    
    def get_specific_risk_matrix(self) -> Optional[np.ndarray]:
        """Get specific risk diagonal matrix D
        
        Returns:
            D matrix (N × N), or None if not fitted
        """
        return self.D.copy() if self.D is not None else None
    
    def get_covariance_matrix(self) -> np.ndarray:
        """Get total covariance matrix Σ = B F Bᵀ + D
        
        Returns:
            Covariance matrix (N × N)
        """
        if self.cov_matrix is None:
            self._build_covariance_matrix()
        
        if self.cov_matrix is None:
            # Return default identity matrix
            N = len(self.symbols) if self.symbols else 1
            return np.eye(N) * 1e-6
        
        return self.cov_matrix.copy()
    
    def get_specific_risk(self, symbol: str) -> float:
        """Get specific/idiosyncratic risk for a symbol
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Specific risk (annualized volatility)
        """
        return self.specific_risk.get(symbol, np.sqrt(1e-6))
    
    def get_symbols(self) -> List[str]:
        """Get list of symbols in order of B matrix rows
        
        Returns:
            List of symbols
        """
        return self.symbols.copy()
    
    def explain_risk(self, exposure: FactorExposure) -> Dict[str, float]:
        """Decompose total risk for a single stock
        
        Given a FactorExposure, calculates:
        - Total variance = Factor variance + Specific variance
        - Factor variance = β' * F * β
        - Specific variance = D_i
        
        Args:
            exposure: FactorExposure object
        
        Returns:
            Dictionary with risk decomposition
        """
        if self.F is None:
            self._initialize_default_model()
        
        # Get exposure vector (beta)
        beta = exposure.get_exposure_vector(self.factor_names)
        
        # Factor variance: β' * F * β
        F_array = self.F.values
        factor_variance = float(beta.T @ F_array @ beta)
        factor_variance = max(factor_variance, 0.0)
        
        # Specific variance
        specific_vol = self.get_specific_risk(exposure.symbol)
        specific_variance = specific_vol ** 2
        
        # Total variance
        total_variance = factor_variance + specific_variance
        
        # Factor contributions
        factor_contributions = {}
        for i, factor_name in enumerate(self.factor_names):
            # Contribution from this factor
            contrib = (beta[i] ** 2) * F_array[i, i]
            factor_contributions[f'{factor_name}_contribution'] = float(contrib)
        
        result = {
            'total_variance': float(total_variance),
            'factor_variance': float(factor_variance),
            'specific_variance': float(specific_variance),
            **factor_contributions
        }
        
        return result
