"""Inertia Alpha Factor

This module implements the Inertia Alpha factor, measuring:
1. Long-short power ratio (buy volume / sell volume)
2. Momentum inertia (recent momentum + capital flow)
3. Direction persistence (consistency period)

Based on inertia concepts from J-GOD knowledge base.
"""

from __future__ import annotations

from typing import Optional
import pandas as pd
import numpy as np

from jgod.alpha_engine.factor_base import FactorBase


class InertiaFactor(FactorBase):
    """Inertia Alpha Factor
    
    Measures the persistence of market movements and the strength of directional momentum.
    High inertia suggests continuation of current trend.
    
    Example:
        factor = InertiaFactor()
        inertia_score = factor.compute(df)
    """
    
    def __init__(self, lookback_window: int = 20, momentum_window: int = 10):
        """Initialize Inertia Factor
        
        Args:
            lookback_window: Window size for rolling statistics (default: 20)
            momentum_window: Window size for momentum calculation (default: 10)
        """
        super().__init__("inertia_factor")
        self.lookback_window = lookback_window
        self.momentum_window = momentum_window
    
    def compute(self, df: pd.DataFrame) -> pd.Series:
        """Compute inertia factor values
        
        Args:
            df: DataFrame with columns:
                - close: Close price
                - volume: Trading volume
                - buy_volume: Buy volume (optional)
                - sell_volume: Sell volume (optional)
                - foreign_flow: Foreign investor net flow (optional)
        
        Returns:
            pd.Series: Inertia score (z-score standardized)
        """
        if df.empty:
            return pd.Series(dtype=float)
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df = df.set_index('date')
            else:
                df.index = pd.to_datetime(df.index)
        
        inertia_scores = []
        
        # 1. Long-short power ratio
        power_ratio = self._compute_power_ratio(df)
        if power_ratio is not None:
            inertia_scores.append(power_ratio)
        
        # 2. Momentum inertia
        momentum_inertia = self._compute_momentum_inertia(df)
        if momentum_inertia is not None:
            inertia_scores.append(momentum_inertia)
        
        # 3. Direction persistence
        direction_persistence = self._compute_direction_persistence(df)
        if direction_persistence is not None:
            inertia_scores.append(direction_persistence)
        
        if not inertia_scores:
            return pd.Series(0.0, index=df.index)
        
        # Combine scores (equal weight)
        combined_score = pd.Series(0.0, index=df.index)
        for score in inertia_scores:
            combined_score = combined_score + score.fillna(0)
        
        combined_score = combined_score / len(inertia_scores)
        
        # Standardize
        combined_score = self.standardize(combined_score, window=self.lookback_window)
        
        # Fill NaN with 0
        combined_score = self.fillna(combined_score, fill_value=0.0)
        
        return combined_score
    
    def _compute_power_ratio(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Compute long-short power ratio (buy volume / sell volume)
        
        Args:
            df: DataFrame with volume data
        
        Returns:
            pd.Series: Power ratio score
        """
        if 'buy_volume' in df.columns and 'sell_volume' in df.columns:
            buy_vol = df['buy_volume'].fillna(0)
            sell_vol = df['sell_volume'].fillna(0)
            
            # Calculate ratio
            total_vol = buy_vol + sell_vol
            ratio = pd.Series(0.0, index=df.index)
            mask = total_vol > 0
            ratio[mask] = (buy_vol[mask] - sell_vol[mask]) / total_vol[mask]
            
            # Normalize to [-1, 1] range
            ratio = ratio.clip(-1, 1)
        else:
            # Fallback: estimate from price and volume
            if 'close' in df.columns and 'volume' in df.columns:
                price = df['close'].fillna(method='ffill')
                volume = df['volume'].fillna(0)
                
                # Estimate buy/sell from price direction
                price_change = price.pct_change().fillna(0)
                buy_pressure = np.where(price_change > 0, volume, 0)
                sell_pressure = np.where(price_change < 0, volume, 0)
                
                total_pressure = buy_pressure + sell_pressure
                ratio = pd.Series(0.0, index=df.index)
                mask = total_pressure > 0
                ratio[mask] = (buy_pressure[mask] - sell_pressure[mask]) / total_pressure[mask]
            else:
                return None
        
        return ratio
    
    def _compute_momentum_inertia(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Compute momentum inertia (recent momentum + capital flow)
        
        Args:
            df: DataFrame with price and flow data
        
        Returns:
            pd.Series: Momentum inertia score
        """
        if 'close' not in df.columns:
            return None
        
        price = df['close'].fillna(method='ffill')
        
        # Calculate price momentum
        returns = price.pct_change().fillna(0)
        momentum = returns.rolling(window=self.momentum_window, min_periods=1).sum()
        
        # Add capital flow component
        if 'foreign_flow' in df.columns:
            foreign_flow = df['foreign_flow'].fillna(0)
            foreign_flow_normalized = self.standardize(foreign_flow, window=self.lookback_window)
            momentum = momentum + foreign_flow_normalized * 0.3
        
        # Smooth momentum to represent inertia
        momentum_inertia = momentum.rolling(window=self.momentum_window // 2, min_periods=1).mean()
        
        return momentum_inertia
    
    def _compute_direction_persistence(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Compute direction persistence (consistency period)
        
        Measures how long price has been moving in the same direction.
        
        Args:
            df: DataFrame with price data
        
        Returns:
            pd.Series: Direction persistence score
        """
        if 'close' not in df.columns:
            return None
        
        price = df['close'].fillna(method='ffill')
        returns = price.pct_change().fillna(0)
        
        # Determine direction (1 for up, -1 for down, 0 for flat)
        direction = np.sign(returns)
        
        # Count consecutive same-direction periods
        persistence = pd.Series(0.0, index=df.index)
        current_direction = 0
        current_count = 0
        
        for i, d in enumerate(direction):
            if d == 0:
                # Flat: reset
                current_count = 0
                current_direction = 0
            elif d == current_direction:
                # Same direction: increment
                current_count += 1
            else:
                # New direction: reset
                current_direction = d
                current_count = 1
            
            persistence.iloc[i] = current_count * d  # Signed persistence
        
        # Normalize by lookback window
        persistence_normalized = persistence / self.lookback_window
        
        return persistence_normalized

