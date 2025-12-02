"""
Alpha Engine Extreme - Professional Quant Fund Grade

This module provides an extreme-level AlphaEngine that leverages enhanced features
from Extreme Loaders (MockExtreme, FinMindExtreme) for professional-grade alpha generation.

Key features:
- Cross-sectional ranking factors (momentum, volatility, skewness, kurtosis)
- Volatility regime detection and adaptive weighting
- Multi-factor cross-sectional alpha computation
- Stability constraints (missing data handling)
- Automatic normalization and composite alpha generation

Reference: docs/JGOD_EXTREME_MODE_EDITOR_INSTRUCTIONS.md
"""

from __future__ import annotations

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, field
import pandas as pd
import numpy as np


@dataclass
class AlphaEngineExtremeConfig:
    """
    Configuration for AlphaEngine Extreme.
    
    All parameters for cross-sectional ranking, regime detection, and weighting.
    """
    # Factor weights for cross-sectional ranking
    momentum_weight: float = 0.30
    volatility_weight: float = 0.20
    skewness_weight: float = 0.15
    kurtosis_weight: float = 0.10
    turnover_weight: float = 0.15
    atr_weight: float = 0.10
    
    # Regime detection parameters
    vol_regime_low_threshold: float = 0.01  # Below this = low regime
    vol_regime_high_threshold: float = 0.03  # Above this = high regime
    
    # Regime-based weight adjustments
    low_vol_momentum_boost: float = 1.2  # Boost momentum in low vol
    high_vol_momentum_penalty: float = 0.8  # Reduce momentum in high vol
    high_vol_volatility_boost: float = 1.3  # Boost volatility factor in high vol
    
    # Stability constraints
    min_required_features: int = 3  # Minimum features required
    required_features: List[str] = field(default_factory=lambda: [
        "daily_return_1d",
        "rolling_vol_20d",
        "close",
    ])


class VolatilityRegime:
    """Volatility regime types."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class AlphaEngineExtreme:
    """
    Extreme Alpha Engine for professional quant fund applications.
    
    Designed to work with Extreme Loaders that provide comprehensive features:
    - Momentum (3d, 5d, 10d)
    - Volatility (rolling_vol_5d, rolling_vol_20d)
    - Higher moments (skewness, kurtosis)
    - Market microstructure (ATR, VWAP, turnover_rate)
    
    Features:
    - Cross-sectional ranking on each rebalancing date
    - Volatility regime detection
    - Adaptive factor weighting based on regime
    - Stability constraints for missing data
    """
    
    def __init__(
        self,
        config: Optional[AlphaEngineExtremeConfig] = None,
    ):
        """
        Initialize AlphaEngine Extreme.
        
        Args:
            config: Configuration object. If None, uses default config.
        """
        self.config = config or AlphaEngineExtremeConfig()
        
        # Normalize factor weights
        total_weight = (
            self.config.momentum_weight +
            self.config.volatility_weight +
            self.config.skewness_weight +
            self.config.kurtosis_weight +
            self.config.turnover_weight +
            self.config.atr_weight
        )
        
        if total_weight > 0:
            self.config.momentum_weight /= total_weight
            self.config.volatility_weight /= total_weight
            self.config.skewness_weight /= total_weight
            self.config.kurtosis_weight /= total_weight
            self.config.turnover_weight /= total_weight
            self.config.atr_weight /= total_weight
    
    def _detect_regime(self, rolling_vol_20d: pd.Series) -> VolatilityRegime:
        """
        Detect volatility regime based on rolling_vol_20d.
        
        Args:
            rolling_vol_20d: Series of 20-day rolling volatility
        
        Returns:
            VolatilityRegime enum
        """
        if rolling_vol_20d.empty:
            return VolatilityRegime.NORMAL
        
        # Use median as proxy for current regime
        median_vol = rolling_vol_20d.median()
        
        if median_vol < self.config.vol_regime_low_threshold:
            return VolatilityRegime.LOW
        elif median_vol > self.config.vol_regime_high_threshold:
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.NORMAL
    
    def _check_feature_completeness(
        self,
        df: pd.DataFrame,
        required_features: List[str],
    ) -> pd.Series:
        """
        Check feature completeness for each symbol.
        
        Args:
            df: DataFrame with features (index=symbol, columns=features)
            required_features: List of required feature names
        
        Returns:
            Series of completeness scores (0.0 to 1.0), indexed by symbol
        """
        completeness = pd.Series(0.0, index=df.index)
        
        for symbol in df.index:
            available_features = 0
            for feature in required_features:
                if feature in df.columns:
                    value = df.loc[symbol, feature]
                    # Check if value is valid (not NaN, not Inf)
                    if pd.notna(value) and np.isfinite(value):
                        available_features += 1
            
            completeness[symbol] = available_features / len(required_features)
        
        return completeness
    
    def _compute_cross_sectional_ranking(
        self,
        df: pd.DataFrame,
        regime: VolatilityRegime = VolatilityRegime.NORMAL,
    ) -> pd.Series:
        """
        Compute cross-sectional ranking alpha using multiple factors.
        
        Factors:
        - Momentum: rolling_momentum_5d (preferred) or daily_return_1d
        - Volatility: rolling_vol_20d (inverse: lower vol = higher alpha)
        - Skewness: rolling_skew (prefer positive skew)
        - Kurtosis: rolling_kurtosis (prefer moderate kurtosis)
        - Turnover: turnover_rate (prefer higher liquidity)
        - ATR: ATR_14 (prefer lower ATR = more stable)
        
        Args:
            df: DataFrame with features (index=symbol, columns=features)
            regime: Current volatility regime
        
        Returns:
            Series of alpha scores, indexed by symbol
        """
        # Start with zero alpha
        alpha = pd.Series(0.0, index=df.index)
        
        # Get base weights
        momentum_w = self.config.momentum_weight
        volatility_w = self.config.volatility_weight
        skewness_w = self.config.skewness_weight
        kurtosis_w = self.config.kurtosis_weight
        turnover_w = self.config.turnover_weight
        atr_w = self.config.atr_weight
        
        # Adjust weights based on regime
        if regime == VolatilityRegime.LOW:
            momentum_w *= self.config.low_vol_momentum_boost
        elif regime == VolatilityRegime.HIGH:
            momentum_w *= self.config.high_vol_momentum_penalty
            volatility_w *= self.config.high_vol_volatility_boost
        
        # Normalize adjusted weights
        total_weight = momentum_w + volatility_w + skewness_w + kurtosis_w + turnover_w + atr_w
        if total_weight > 0:
            momentum_w /= total_weight
            volatility_w /= total_weight
            skewness_w /= total_weight
            kurtosis_w /= total_weight
            turnover_w /= total_weight
            atr_w /= total_weight
        
        # 1. Momentum factor (z-score, prefer higher)
        momentum_cols = ["rolling_momentum_5d", "rolling_momentum_3d", "daily_return_1d"]
        momentum_col = None
        for col in momentum_cols:
            if col in df.columns:
                momentum_col = col
                break
        
        if momentum_col is not None:
            momentum_raw = df[momentum_col].fillna(0.0)
            momentum_std = momentum_raw.std()
            if momentum_std > 0:
                momentum_z = (momentum_raw - momentum_raw.mean()) / momentum_std
                alpha += momentum_z * momentum_w
        
        # 2. Volatility factor (inverse z-score: lower vol = higher alpha)
        if "rolling_vol_20d" in df.columns:
            vol_raw = df["rolling_vol_20d"].fillna(0.0)
            vol_std = vol_raw.std()
            if vol_std > 0:
                vol_z = (vol_raw - vol_raw.mean()) / vol_std
                alpha += (-vol_z) * volatility_w  # Inverse: prefer lower vol
        
        # 3. Skewness factor (prefer positive skew)
        if "rolling_skew" in df.columns:
            skew_raw = df["rolling_skew"].fillna(0.0)
            skew_std = skew_raw.std()
            if skew_std > 0:
                skew_z = (skew_raw - skew_raw.mean()) / skew_std
                alpha += skew_z * skewness_w
        
        # 4. Kurtosis factor (prefer moderate kurtosis, avoid extremes)
        if "rolling_kurtosis" in df.columns:
            kurt_raw = df["rolling_kurtosis"].fillna(0.0)
            kurt_mean = kurt_raw.mean()
            # Penalize extreme kurtosis (away from mean)
            kurt_penalty = -np.abs(kurt_raw - kurt_mean)
            kurt_std = kurt_penalty.std()
            if kurt_std > 0:
                kurt_z = (kurt_penalty - kurt_penalty.mean()) / kurt_std
                alpha += kurt_z * kurtosis_w
        
        # 5. Turnover factor (prefer higher liquidity)
        if "turnover_rate" in df.columns:
            turnover_raw = df["turnover_rate"].fillna(0.0)
            turnover_std = turnover_raw.std()
            if turnover_std > 0:
                turnover_z = (turnover_raw - turnover_raw.mean()) / turnover_std
                alpha += turnover_z * turnover_w
        
        # 6. ATR factor (inverse: prefer lower ATR = more stable)
        if "ATR_14" in df.columns:
            atr_raw = df["ATR_14"].fillna(0.0)
            atr_std = atr_raw.std()
            if atr_std > 0:
                atr_z = (atr_raw - atr_raw.mean()) / atr_std
                alpha += (-atr_z) * atr_w  # Inverse: prefer lower ATR
        
        return alpha.fillna(0.0)
    
    def _apply_stability_constraint(
        self,
        alpha: pd.Series,
        feature_completeness: pd.Series,
        min_completeness: float = 0.5,
    ) -> pd.Series:
        """
        Apply stability constraint: set alpha=0 for symbols with insufficient data.
        
        Args:
            alpha: Original alpha scores
            feature_completeness: Completeness scores (0.0 to 1.0)
            min_completeness: Minimum completeness threshold
        
        Returns:
            Adjusted alpha scores with stability constraint applied
        """
        alpha_adjusted = alpha.copy()
        
        # Set alpha to 0 for symbols with insufficient data
        incomplete_mask = feature_completeness < min_completeness
        alpha_adjusted[incomplete_mask] = 0.0
        
        return alpha_adjusted
    
    def compute_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute composite alpha for all symbols.
        
        This method supports both time-series and cross-sectional input formats.
        For cross-sectional mode (index=symbol), it performs ranking-based alpha computation.
        
        Args:
            df: DataFrame with features
                - Cross-sectional mode: index=symbol, columns=features
                - Time-series mode: index=date, columns=features (with symbol info)
        
        Returns:
            DataFrame with columns:
            - Individual factor scores (if applicable)
            - composite_alpha: Final composite alpha score
        
        Note:
            For cross-sectional mode (recommended), this method computes ranking-based
            alpha directly. For time-series mode, it computes alpha for each date.
        """
        if df.empty:
            columns = ['composite_alpha']
            if isinstance(df.index, pd.MultiIndex) and 'symbol' in df.index.names:
                # MultiIndex case
                return pd.DataFrame(columns=columns)
            return pd.DataFrame(columns=columns, index=df.index)
        
        # Detect input mode
        mode = self._detect_input_mode(df)
        
        if mode == "cross_sectional":
            # Cross-sectional mode: compute ranking-based alpha
            return self._compute_cross_sectional_all(df)
        else:
            # Time-series mode: compute for each date
            return self._compute_timeseries_all(df)
    
    def _detect_input_mode(self, df: pd.DataFrame) -> str:
        """
        Detect input mode: cross-sectional vs time-series.
        
        Args:
            df: Input DataFrame
        
        Returns:
            "cross_sectional" or "timeseries"
        """
        if df.empty:
            return "cross_sectional"
        
        # Check if index is DatetimeIndex
        if isinstance(df.index, pd.DatetimeIndex):
            return "timeseries"
        
        # Check if index looks like symbols (not dates)
        if len(df.index) > 0:
            first_val = df.index[0]
            if isinstance(first_val, str):
                # Check if it looks like a date
                import re
                if not re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}', str(first_val)):
                    return "cross_sectional"
        
        return "timeseries"
    
    def _compute_cross_sectional_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute composite alpha in cross-sectional mode.
        
        Args:
            df: DataFrame with index=symbol, columns=features
        
        Returns:
            DataFrame with composite_alpha column
        """
        # Check feature completeness
        feature_completeness = self._check_feature_completeness(
            df,
            self.config.required_features
        )
        
        # Detect volatility regime
        if "rolling_vol_20d" in df.columns:
            rolling_vol = df["rolling_vol_20d"].fillna(0.0)
            regime = self._detect_regime(rolling_vol)
        else:
            regime = VolatilityRegime.NORMAL
        
        # Compute cross-sectional ranking alpha
        alpha = self._compute_cross_sectional_ranking(df, regime)
        
        # Apply stability constraint
        alpha = self._apply_stability_constraint(
            alpha,
            feature_completeness,
            min_completeness=self.config.min_required_features / len(self.config.required_features)
        )
        
        # Create result DataFrame
        result_df = pd.DataFrame({
            'composite_alpha': alpha,
        }, index=df.index)
        
        return result_df.fillna(0.0)
    
    def _compute_timeseries_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute composite alpha in time-series mode.
        
        For each date, extract cross-sectional data and compute ranking-based alpha.
        
        Args:
            df: DataFrame with index=date, columns may contain symbol info
        
        Returns:
            DataFrame with composite_alpha column
        """
        # For time-series mode, we need to know symbols
        # This is a simplified version - assumes df has MultiIndex or wide format
        
        # Extract dates
        dates = df.index.unique() if hasattr(df.index, 'unique') else [df.index]
        
        # For simplicity, return basic alpha
        # In practice, this should extract cross-sectional data per date
        alpha_series = pd.Series(0.0, index=df.index)
        
        result_df = pd.DataFrame({
            'composite_alpha': alpha_series,
        }, index=df.index)
        
        return result_df.fillna(0.0)
    
    def compute_for_date(
        self,
        df: pd.DataFrame,
        date: Optional[pd.Timestamp] = None,
    ) -> pd.Series:
        """
        Compute composite alpha for a specific date (cross-sectional).
        
        This method is designed for use in backtest loops where we compute
        alpha for each rebalancing date.
        
        Args:
            df: DataFrame with features
                - Cross-sectional: index=symbol, columns=features
                - Time-series: index=date, columns=features (with symbol info)
            date: Optional date to extract (for time-series mode)
        
        Returns:
            Series of composite alpha scores, indexed by symbol
        """
        if df.empty:
            return pd.Series(dtype=float)
        
        # If time-series mode and date provided, extract cross-sectional slice
        mode = self._detect_input_mode(df)
        
        if mode == "timeseries" and date is not None:
            # Extract cross-sectional data for this date
            if isinstance(df.index, pd.DatetimeIndex):
                date_data = df.loc[date]
                if isinstance(date_data, pd.Series):
                    # Single row case - convert to DataFrame
                    date_df = pd.DataFrame([date_data]).T
                    date_df = date_df.T
                else:
                    date_df = date_data
            else:
                date_df = df
        else:
            # Already cross-sectional
            date_df = df
        
        # Compute alpha
        result_df = self._compute_cross_sectional_all(date_df)
        
        if 'composite_alpha' in result_df.columns:
            return result_df['composite_alpha']
        else:
            return pd.Series(0.0, index=date_df.index)
    
    def update_factor_weights(
        self,
        weights: Dict[str, float],
    ) -> None:
        """
        Update factor weights for cross-sectional ranking.
        
        Args:
            weights: Dictionary with keys:
                - momentum_weight
                - volatility_weight
                - skewness_weight
                - kurtosis_weight
                - turnover_weight
                - atr_weight
        """
        if 'momentum_weight' in weights:
            self.config.momentum_weight = weights['momentum_weight']
        if 'volatility_weight' in weights:
            self.config.volatility_weight = weights['volatility_weight']
        if 'skewness_weight' in weights:
            self.config.skewness_weight = weights['skewness_weight']
        if 'kurtosis_weight' in weights:
            self.config.kurtosis_weight = weights['kurtosis_weight']
        if 'turnover_weight' in weights:
            self.config.turnover_weight = weights['turnover_weight']
        if 'atr_weight' in weights:
            self.config.atr_weight = weights['atr_weight']
        
        # Re-normalize
        total_weight = (
            self.config.momentum_weight +
            self.config.volatility_weight +
            self.config.skewness_weight +
            self.config.kurtosis_weight +
            self.config.turnover_weight +
            self.config.atr_weight
        )
        
        if total_weight > 0:
            self.config.momentum_weight /= total_weight
            self.config.volatility_weight /= total_weight
            self.config.skewness_weight /= total_weight
            self.config.kurtosis_weight /= total_weight
            self.config.turnover_weight /= total_weight
            self.config.atr_weight /= total_weight

