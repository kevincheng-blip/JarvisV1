"""Alpha Engine Main Controller

This module provides the main AlphaEngine class that orchestrates all alpha factors
and computes composite alpha scores.

Based on: structured_books/股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md
"""

from __future__ import annotations

from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from jgod.alpha_engine.factor_base import FactorBase
from jgod.alpha_engine.flow_factor import FlowFactor
from jgod.alpha_engine.divergence_factor import DivergenceFactor
from jgod.alpha_engine.reversion_factor import ReversionFactor
from jgod.alpha_engine.inertia_factor import InertiaFactor
from jgod.alpha_engine.value_quality_factor import ValueQualityFactor
from jgod.alpha_engine.micro_momentum_factor import MicroMomentumFactor


class AlphaEngine:
    """Alpha Engine Main Controller
    
    Orchestrates all alpha factors and computes composite alpha scores.
    
    Example:
        engine = AlphaEngine()
        result_df = engine.compute_all(df)
        
        # Access individual factor scores
        flow_score = result_df['flow_score']
        composite_alpha = result_df['composite_alpha']
    """
    
    def __init__(
        self,
        enable_micro_momentum: bool = False,
        factor_weights: Optional[Dict[str, float]] = None
    ):
        """Initialize Alpha Engine
        
        Args:
            enable_micro_momentum: Whether to enable MicroMomentumFactor (default: False)
            factor_weights: Custom weights for each factor in composite alpha.
                          If None, uses equal weights.
                          Keys: 'flow_score', 'divergence_score', 'reversion_score',
                                'inertia_score', 'value_quality_score', 'micro_momentum_score'
        """
        # Initialize all factors
        self.factors: List[FactorBase] = [
            FlowFactor(),
            DivergenceFactor(),
            ReversionFactor(),
            InertiaFactor(),
            ValueQualityFactor(),
        ]
        
        # Optionally add MicroMomentumFactor
        if enable_micro_momentum:
            self.factors.append(MicroMomentumFactor())
        
        # Factor name mapping
        self.factor_names = {
            'flow_factor': 'flow_score',
            'divergence_factor': 'divergence_score',
            'reversion_factor': 'reversion_score',
            'inertia_factor': 'inertia_score',
            'value_quality_factor': 'value_quality_score',
            'micro_momentum_factor': 'micro_momentum_score',
        }
        
        # Default weights (equal weight)
        default_weight = 1.0 / len(self.factors)
        self.factor_weights = {
            'flow_score': default_weight,
            'divergence_score': default_weight,
            'reversion_score': default_weight,
            'inertia_score': default_weight,
            'value_quality_score': default_weight,
            'micro_momentum_score': default_weight if enable_micro_momentum else 0.0,
        }
        
        # Override with custom weights if provided
        if factor_weights:
            self.factor_weights.update(factor_weights)
        
        # Normalize weights to sum to 1.0
        total_weight = sum(self.factor_weights.values())
        if total_weight > 0:
            self.factor_weights = {
                k: v / total_weight
                for k, v in self.factor_weights.items()
            }
    
    def compute_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute all alpha factors for a single stock
        
        Args:
            df: DataFrame containing stock data with required columns:
                - Required: close, volume
                - Optional: open, high, low, foreign_flow, ecosystem_flow,
                          major_buy_volume, major_sell_volume, buy_volume, sell_volume,
                          roa, gpa, bm, debt_ratio, etc.
        
        Returns:
            pd.DataFrame with columns:
                - flow_score: Flow alpha score
                - divergence_score: Divergence alpha score
                - reversion_score: Reversion alpha score
                - inertia_score: Inertia alpha score
                - value_quality_score: Value/Quality alpha score
                - micro_momentum_score: Micro-Momentum alpha score (if enabled)
                - composite_alpha: Weighted average of all factor scores
            All columns have the same index as input df.
        """
        if df.empty:
            # Return empty DataFrame with expected columns
            columns = [
                'flow_score', 'divergence_score', 'reversion_score',
                'inertia_score', 'value_quality_score', 'micro_momentum_score',
                'composite_alpha'
            ]
            return pd.DataFrame(columns=columns)
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df = df.set_index('date')
            else:
                df.index = pd.to_datetime(df.index)
        
        # Compute all factors
        factor_scores: Dict[str, pd.Series] = {}
        
        for factor in self.factors:
            try:
                score = factor.compute(df)
                score_name = self.factor_names.get(factor.name, factor.name)
                factor_scores[score_name] = score.fillna(0.0)
            except Exception as e:
                # If factor computation fails, use neutral score
                score_name = self.factor_names.get(factor.name, factor.name)
                factor_scores[score_name] = pd.Series(0.0, index=df.index)
                print(f"Warning: Factor {factor.name} computation failed: {e}")
        
        # Ensure all expected columns exist (fill missing with zeros)
        expected_columns = list(self.factor_names.values())
        for col in expected_columns:
            if col not in factor_scores:
                factor_scores[col] = pd.Series(0.0, index=df.index)
        
        # Create result DataFrame
        result_df = pd.DataFrame(factor_scores, index=df.index)
        
        # Compute composite alpha (weighted average)
        composite_alpha = pd.Series(0.0, index=df.index)
        for score_name, weight in self.factor_weights.items():
            if score_name in result_df.columns:
                composite_alpha = composite_alpha + result_df[score_name] * weight
        
        result_df['composite_alpha'] = composite_alpha.fillna(0.0)
        
        # Ensure no NaN values remain
        result_df = result_df.fillna(0.0)
        
        return result_df
    
    def get_factor(self, factor_name: str) -> Optional[FactorBase]:
        """Get a specific factor by name
        
        Args:
            factor_name: Factor name (e.g., "flow_factor", "divergence_factor")
        
        Returns:
            FactorBase instance, or None if not found
        """
        for factor in self.factors:
            if factor.name == factor_name:
                return factor
        return None
    
    def update_factor_weights(self, weights: Dict[str, float]) -> None:
        """Update factor weights for composite alpha calculation
        
        Args:
            weights: Dictionary mapping factor score names to weights
                    (e.g., {'flow_score': 0.3, 'divergence_score': 0.2, ...})
        """
        self.factor_weights.update(weights)
        
        # Normalize weights to sum to 1.0
        total_weight = sum(self.factor_weights.values())
        if total_weight > 0:
            self.factor_weights = {
                k: v / total_weight
                for k, v in self.factor_weights.items()
            }
    
    def list_factors(self) -> List[str]:
        """List all available factor names
        
        Returns:
            List of factor names
        """
        return [factor.name for factor in self.factors]

