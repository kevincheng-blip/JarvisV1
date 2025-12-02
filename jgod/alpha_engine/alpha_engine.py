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
    
    def _looks_like_date(self, val: str) -> bool:
        """檢查字串是否像日期格式
        
        Args:
            val: 要檢查的字串
        
        Returns:
            True 如果看起來像日期格式（例如：'2024-01-01'）
        """
        import re
        return bool(re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}', str(val)))
    
    def _detect_input_mode(self, df: pd.DataFrame) -> str:
        """偵測輸入 DataFrame 的模式
        
        Returns:
            "timeseries" - 時間序列模式（index 是 DatetimeIndex）
            "cross_sectional" - 橫截面模式（index 是 symbol）
        """
        if df.empty:
            return "timeseries"  # 預設
        
        if isinstance(df.index, pd.DatetimeIndex):
            return "timeseries"
        
        # 檢查 index 是否為 symbol（字串且不像日期）
        if len(df.index) > 0:
            first_val = df.index[0]
            if isinstance(first_val, str) and not self._looks_like_date(first_val):
                return "cross_sectional"
        
        # 預設嘗試時間序列
        return "timeseries"
    
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
        
        # 偵測輸入模式（時間序列 vs 橫截面）
        mode = self._detect_input_mode(df)
        
        # 根據模式處理 index
        if mode == "timeseries":
            # 時間序列模式：確保 index 是 DatetimeIndex
            if not isinstance(df.index, pd.DatetimeIndex):
                if 'date' in df.columns:
                    df = df.set_index('date')
                else:
                    # 只在確定是時間序列模式時才嘗試轉換
                    df.index = pd.to_datetime(df.index, errors='coerce')
                    # 處理無法解析的情況
                    invalid_mask = df.index.isna()
                    if invalid_mask.any():
                        # 如果無法解析，使用當前時間作為 fallback
                        df.index = df.index.fillna(pd.Timestamp.now())
        elif mode == "cross_sectional":
            # 橫截面模式：保持 index 為 symbol，不做 datetime 轉換
            # 對 features 做橫截面標準化（以便 factor 計算時使用）
            df = df.copy()  # 避免修改原始資料
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    mean = df[col].mean()
                    std = df[col].std()
                    if std > 0:
                        df[col] = (df[col] - mean) / std
                    else:
                        df[col] = 0.0
        
        # Compute all factors
        factor_scores: Dict[str, pd.Series] = {}
        
        for factor in self.factors:
            try:
                if mode == "cross_sectional":
                    # 橫截面模式：直接使用標準化後的 features 計算 factor
                    # 大部分 factor 需要時間序列，所以在橫截面模式下，我們使用簡化的計算
                    # 根據可用的欄位來決定 factor score
                    score = self._compute_cross_sectional_factor(factor, df)
                else:
                    # 時間序列模式：使用原始的 factor.compute()
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
    
    def _compute_cross_sectional_factor(
        self, 
        factor: FactorBase, 
        df: pd.DataFrame
    ) -> pd.Series:
        """在橫截面模式下計算 factor score
        
        這是一個簡化版本，因為大部分 factor 設計為時間序列計算。
        在橫截面模式下，我們使用可用的 features 來計算簡單的 z-score。
        
        Args:
            factor: Factor 實例
            df: DataFrame with index=symbol, columns=features（已標準化）
        
        Returns:
            pd.Series with factor scores, indexed by symbol
        """
        # 根據 factor 類型選擇合適的 feature
        if factor.name == 'flow_factor':
            # 使用 volume 或相關欄位
            if 'volume' in df.columns:
                return df['volume'].fillna(0.0)
        elif factor.name == 'divergence_factor':
            # 使用 daily_return_1d
            if 'daily_return_1d' in df.columns:
                return df['daily_return_1d'].fillna(0.0)
        elif factor.name == 'reversion_factor':
            # 使用 daily_return_1d 的反向
            if 'daily_return_1d' in df.columns:
                return -df['daily_return_1d'].fillna(0.0)
        elif factor.name == 'inertia_factor':
            # 使用 daily_return_1d（動量）
            if 'daily_return_1d' in df.columns:
                return df['daily_return_1d'].fillna(0.0)
        elif factor.name == 'value_quality_factor':
            # 使用 rolling_vol_5d（低波動表示高品質）
            if 'rolling_vol_5d' in df.columns:
                return -df['rolling_vol_5d'].fillna(0.0)
        
        # 預設：使用第一個數值欄位或返回零
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        if numeric_cols:
            return df[numeric_cols[0]].fillna(0.0)
        
        # 如果沒有任何欄位，返回零
        return pd.Series(0.0, index=df.index)

