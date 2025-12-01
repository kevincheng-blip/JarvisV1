"""J-GOD Eight Risk Factors Definition

This module defines and implements the eight risk factors for J-GOD Risk Model v1.0:
1. R-MKT: Market (系统性风险)
2. R-SIZE: Size (规模风险)
3. R-VAL: Value (价值风险)
4. R-MOM: Momentum (动量风险)
5. R-LIQ: Liquidity (流动性风险)
6. R-VOL: Volatility (波动率风险)
7. R-FX/IR: FX/Interest Rate (汇率/利率风险)
8. R-FLOW: Ecosystem Flow (生态圈资金流风险)

Based on: docs/J-GOD風險模型八大風險因子_AI知識庫版_v1.md
"""

from __future__ import annotations

from typing import Dict, List, Optional
from enum import Enum
import pandas as pd
import numpy as np


class RiskFactor(str, Enum):
    """J-GOD Eight Risk Factors"""
    MARKET = "R_MKT"          # 市場系統性風險
    SIZE = "R_SIZE"           # 規模風險
    VALUE = "R_VAL"           # 價值風險
    MOMENTUM = "R_MOM"        # 動量風險
    LIQUIDITY = "R_LIQ"       # 流動性風險
    VOLATILITY = "R_VOL"      # 波動率風險
    FX_IR = "R_FX_IR"         # 匯率/利率風險
    FLOW = "R_FLOW"           # 生態圈資金流風險
    
    @classmethod
    def all_factors(cls) -> List[str]:
        """Get all risk factor names"""
        return [factor.value for factor in cls]


# Standard factor names mapping
STANDARD_FACTOR_NAMES = RiskFactor.all_factors()


class RiskFactorCalculator:
    """Risk Factor Calculator
    
    Calculates the eight J-GOD risk factors from market data.
    This class provides methods to compute each risk factor's return.
    """
    
    def __init__(self):
        """Initialize Risk Factor Calculator"""
        pass
    
    def calculate_market_factor(
        self,
        market_index_returns: pd.Series
    ) -> pd.Series:
        """Calculate R-MKT: Market factor return
        
        Formula: R-MKT = 當期市場指數報酬
        
        Args:
            market_index_returns: Daily returns of market index (e.g., 加權指數)
        
        Returns:
            Series of market factor returns (same as input)
        """
        return market_index_returns.fillna(0.0)
    
    def calculate_size_factor(
        self,
        small_cap_returns: pd.Series,
        large_cap_returns: pd.Series
    ) -> pd.Series:
        """Calculate R-SIZE: Size factor return
        
        Formula: R-SIZE = 小市值組合報酬 − 大市值組合報酬
        
        Args:
            small_cap_returns: Returns of small cap portfolio
            large_cap_returns: Returns of large cap portfolio
        
        Returns:
            Series of size factor returns
        """
        # Align indices
        common_dates = small_cap_returns.index.intersection(large_cap_returns.index)
        small_aligned = small_cap_returns.reindex(common_dates).fillna(0.0)
        large_aligned = large_cap_returns.reindex(common_dates).fillna(0.0)
        
        size_factor = small_aligned - large_aligned
        return size_factor
    
    def calculate_value_factor(
        self,
        high_bm_returns: pd.Series,
        low_bm_returns: pd.Series
    ) -> pd.Series:
        """Calculate R-VAL: Value factor return
        
        Formula: R-VAL = 高 B/M 組合報酬 − 低 B/M 組合報酬
        
        Args:
            high_bm_returns: Returns of high B/M (value) portfolio
            low_bm_returns: Returns of low B/M (growth) portfolio
        
        Returns:
            Series of value factor returns
        """
        # Align indices
        common_dates = high_bm_returns.index.intersection(low_bm_returns.index)
        high_aligned = high_bm_returns.reindex(common_dates).fillna(0.0)
        low_aligned = low_bm_returns.reindex(common_dates).fillna(0.0)
        
        value_factor = high_aligned - low_aligned
        return value_factor
    
    def calculate_momentum_factor(
        self,
        winner_returns: pd.Series,
        loser_returns: pd.Series
    ) -> pd.Series:
        """Calculate R-MOM: Momentum factor return
        
        Formula: R-MOM = 贏家組合報酬 − 輸家組合報酬
        
        Args:
            winner_returns: Returns of winner portfolio (past performers)
            loser_returns: Returns of loser portfolio (past poor performers)
        
        Returns:
            Series of momentum factor returns
        """
        # Align indices
        common_dates = winner_returns.index.intersection(loser_returns.index)
        winner_aligned = winner_returns.reindex(common_dates).fillna(0.0)
        loser_aligned = loser_returns.reindex(common_dates).fillna(0.0)
        
        momentum_factor = winner_aligned - loser_aligned
        return momentum_factor
    
    def calculate_liquidity_factor(
        self,
        turnover_data: pd.DataFrame
    ) -> pd.Series:
        """Calculate R-LIQ: Liquidity factor return
        
        Formula options:
        - R-LIQ = (成交量 × 股價) / 市值
        - Or use Amihud Illiquidity / Bid-Ask Spread
        
        Args:
            turnover_data: DataFrame with columns:
                - 'volume': Trading volume
                - 'price': Stock price
                - 'market_cap': Market capitalization
                - 'returns': Stock returns (optional, for illiquidity measure)
        
        Returns:
            Series of liquidity factor returns
        """
        if 'volume' in turnover_data.columns and 'price' in turnover_data.columns:
            # Simple turnover-based measure
            if 'market_cap' in turnover_data.columns:
                turnover = (turnover_data['volume'] * turnover_data['price']) / turnover_data['market_cap']
            else:
                turnover = turnover_data['volume'] * turnover_data['price']
            
            # Convert to factor return (high turnover = low illiquidity)
            # Group into high/low liquidity portfolios and return spread
            # For now, return normalized turnover as proxy
            liquidity_factor = self._normalize_to_factor_return(turnover)
        else:
            # Return zeros if insufficient data
            liquidity_factor = pd.Series(0.0, index=turnover_data.index)
        
        return liquidity_factor
    
    def calculate_volatility_factor(
        self,
        high_vol_returns: pd.Series,
        low_vol_returns: pd.Series
    ) -> pd.Series:
        """Calculate R-VOL: Volatility factor return
        
        Formula: R-VOL = 高波動率組合報酬 − 低波動率組合報酬
        
        Args:
            high_vol_returns: Returns of high volatility portfolio
            low_vol_returns: Returns of low volatility portfolio
        
        Returns:
            Series of volatility factor returns
        """
        # Align indices
        common_dates = high_vol_returns.index.intersection(low_vol_returns.index)
        high_aligned = high_vol_returns.reindex(common_dates).fillna(0.0)
        low_aligned = low_vol_returns.reindex(common_dates).fillna(0.0)
        
        volatility_factor = high_aligned - low_aligned
        return volatility_factor
    
    def calculate_fx_ir_factor(
        self,
        fx_returns: Optional[pd.Series] = None,
        interest_rate_changes: Optional[pd.Series] = None
    ) -> pd.Series:
        """Calculate R-FX/IR: FX/Interest Rate factor return
        
        Formula: R-FX/IR = 主要貨幣匯率變動 + 公債殖利率變動
        
        Args:
            fx_returns: Exchange rate returns (optional)
            interest_rate_changes: Interest rate changes (optional)
        
        Returns:
            Series of FX/IR factor returns
        """
        factors = []
        
        if fx_returns is not None:
            factors.append(fx_returns)
        
        if interest_rate_changes is not None:
            factors.append(interest_rate_changes)
        
        if not factors:
            # Return zeros if no data
            return pd.Series(dtype=float)
        
        # Combine factors (average or sum)
        if len(factors) == 1:
            return factors[0].fillna(0.0)
        else:
            # Align all series
            common_index = factors[0].index
            for series in factors[1:]:
                common_index = common_index.intersection(series.index)
            
            combined = pd.Series(0.0, index=common_index)
            for series in factors:
                aligned = series.reindex(common_index).fillna(0.0)
                combined = combined + aligned
            
            return combined / len(factors)  # Average
    
    def calculate_flow_factor(
        self,
        high_flow_returns: pd.Series,
        low_flow_returns: pd.Series
    ) -> pd.Series:
        """Calculate R-FLOW: Ecosystem Flow factor return (J-GOD獨有)
        
        Formula: R-FLOW = 高 Flow 暴露組合報酬 − 低 Flow 暴露組合報酬
        
        Args:
            high_flow_returns: Returns of high flow exposure portfolio
            low_flow_returns: Returns of low flow exposure portfolio
        
        Returns:
            Series of flow factor returns
        """
        # Align indices
        common_dates = high_flow_returns.index.intersection(low_flow_returns.index)
        high_aligned = high_flow_returns.reindex(common_dates).fillna(0.0)
        low_aligned = low_flow_returns.reindex(common_dates).fillna(0.0)
        
        flow_factor = high_aligned - low_aligned
        return flow_factor
    
    def _normalize_to_factor_return(self, series: pd.Series) -> pd.Series:
        """Normalize a series to look like a factor return
        
        Args:
            series: Input series
        
        Returns:
            Normalized series (z-score)
        """
        if series.empty:
            return series
        
        mean = series.mean()
        std = series.std()
        
        if std == 0 or np.isnan(std):
            return pd.Series(0.0, index=series.index)
        
        normalized = (series - mean) / std
        return normalized.fillna(0.0)


def get_standard_risk_factor_names() -> List[str]:
    """Get standard list of J-GOD eight risk factor names
    
    Returns:
        List of risk factor names:
        ['R_MKT', 'R_SIZE', 'R_VAL', 'R_MOM', 'R_LIQ', 'R_VOL', 'R_FX_IR', 'R_FLOW']
    """
    return STANDARD_FACTOR_NAMES


def map_alpha_to_risk_factors() -> Dict[str, str]:
    """Map Alpha Engine factors to Risk Factors
    
    Returns:
        Dictionary mapping alpha factor names to risk factor names
    """
    return {
        'flow': 'R_FLOW',
        'reversion': 'R_VOL',
        'inertia': 'R_MOM',
        'value_quality': 'R_VAL',
    }

