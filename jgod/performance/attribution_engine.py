"""Attribution Engine v1

績效歸因分析引擎，包含 PerformanceEngine 核心類別。

Reference:
- docs/JGOD_PERFORMANCE_ENGINE_STANDARD_v1.md
- spec/JGOD_PerformanceEngine_Spec.md
"""

from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from .performance_types import (
    PerformanceEngineRequest,
    PerformanceSummary,
    AttributionReport,
    PerformanceEngineResult,
)
from .performance_metrics import (
    compute_cumulative_return,
    compute_cagr,
    compute_annualized_vol,
    compute_sharpe,
    compute_max_drawdown,
    compute_calmar,
    compute_hit_rate,
    compute_avg_win_loss,
    compute_turnover,
    compute_tracking_error,
    compute_information_ratio,
)


class PerformanceEngine:
    """Performance & Attribution Engine 核心類別
    
    負責計算績效指標和歸因分析。
    """
    
    def __init__(
        self,
        periods_per_year: int = 252,
        risk_free_rate: float = 0.0
    ):
        """初始化 Performance Engine
        
        Args:
            periods_per_year: 年化基數（台股通常為 252）
            risk_free_rate: 無風險利率（年化）
        """
        self.periods_per_year = periods_per_year
        self.risk_free_rate = risk_free_rate
    
    def compute_summary(
        self,
        request: PerformanceEngineRequest
    ) -> PerformanceSummary:
        """計算績效摘要
        
        Args:
            request: PerformanceEngineRequest 物件
        
        Returns:
            PerformanceSummary 物件
        """
        # 驗證輸入
        request.validate()
        
        returns = request.portfolio_returns
        nav = request.portfolio_nav
        
        # 計算基礎指標
        total_return = compute_cumulative_return(returns)
        cagr = compute_cagr(returns, self.periods_per_year)
        vol_annualized = compute_annualized_vol(returns, self.periods_per_year)
        sharpe = compute_sharpe(returns, self.risk_free_rate, self.periods_per_year)
        max_drawdown = compute_max_drawdown(nav)
        calmar = compute_calmar(cagr, max_drawdown)
        hit_rate = compute_hit_rate(returns)
        avg_win, avg_loss = compute_avg_win_loss(returns)
        
        # 計算換手率
        turnover_annualized = compute_turnover(request.trades_by_date, nav)
        # 簡化：假設換手率已為年化，或可根據 rebalance 頻率調整
        
        # 計算基準相關指標（如果有基準）
        active_return = None
        tracking_error = None
        information_ratio = None
        
        if request.benchmark_returns is not None:
            benchmark_returns = request.benchmark_returns
            active_return = float((returns - benchmark_returns).mean() * self.periods_per_year)
            tracking_error = compute_tracking_error(returns, benchmark_returns, self.periods_per_year)
            information_ratio = compute_information_ratio(returns, benchmark_returns, self.periods_per_year)
        
        return PerformanceSummary(
            total_return=total_return,
            cagr=cagr,
            vol_annualized=vol_annualized,
            sharpe=sharpe,
            max_drawdown=max_drawdown,
            calmar=calmar,
            hit_rate=hit_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            turnover_annualized=turnover_annualized,
            active_return=active_return,
            tracking_error=tracking_error,
            information_ratio=information_ratio,
        )
    
    def compute_attribution(
        self,
        request: PerformanceEngineRequest
    ) -> AttributionReport:
        """計算歸因報告
        
        Args:
            request: PerformanceEngineRequest 物件
        
        Returns:
            AttributionReport 物件
        """
        # Symbol Attribution
        by_symbol = self._compute_symbol_attribution(request)
        
        # Sector Attribution（如果有 sector_map）
        by_sector = None
        if request.sector_map:
            by_sector = self._compute_sector_attribution(request)
        
        # Factor Attribution（如果有 factor data）
        by_factor = None
        residual = 0.0
        if request.factor_returns is not None and request.factor_exposures_by_date:
            by_factor, residual = self._compute_factor_attribution(request)
        
        return AttributionReport(
            by_symbol=by_symbol,
            by_sector=by_sector,
            by_factor=by_factor,
            residual=residual,
        )
    
    def compute_full_report(
        self,
        request: PerformanceEngineRequest
    ) -> PerformanceEngineResult:
        """計算完整報告（績效摘要 + 歸因報告）
        
        Args:
            request: PerformanceEngineRequest 物件
        
        Returns:
            PerformanceEngineResult 物件
        """
        summary = self.compute_summary(request)
        attribution = self.compute_attribution(request)
        
        # 儲存原始 DataFrame 以供除錯
        raw_frames = {
            "portfolio_returns": request.portfolio_returns,
            "portfolio_nav": request.portfolio_nav,
        }
        
        if request.benchmark_returns is not None:
            raw_frames["benchmark_returns"] = request.benchmark_returns
        
        return PerformanceEngineResult(
            summary=summary,
            attribution=attribution,
            raw_frames=raw_frames,
        )
    
    def _compute_symbol_attribution(
        self,
        request: PerformanceEngineRequest
    ) -> pd.DataFrame:
        """計算 Symbol 層級歸因
        
        使用「平均權重 × 總報酬」作為貢獻。
        
        Args:
            request: PerformanceEngineRequest 物件
        
        Returns:
            DataFrame with columns: [symbol, return_contrib, weight_avg, sector]
        """
        # 收集所有標的
        all_symbols = set()
        for weights in request.weights_by_date.values():
            all_symbols.update(weights.index)
        
        if not all_symbols:
            return pd.DataFrame(columns=["symbol", "return_contrib", "weight_avg"])
        
        # 計算每個標的的平均權重
        symbol_weights = {}
        symbol_returns = {}
        
        for symbol in all_symbols:
            weights_list = []
            for date, weights in request.weights_by_date.items():
                if symbol in weights.index:
                    weights_list.append(weights.loc[symbol])
            
            if weights_list:
                symbol_weights[symbol] = np.mean(weights_list)
            
            # 簡化：從 portfolio returns 無法直接取得單一標的的報酬
            # 這裡使用權重作為近似，實際需要標的的個別報酬資料
            symbol_returns[symbol] = 0.0  # TODO: 需要標的的個別報酬
        
        # 計算總期間報酬（從 NAV 計算）
        total_return = compute_cumulative_return(request.portfolio_returns)
        
        # 建立 DataFrame
        data = []
        for symbol in sorted(all_symbols):
            avg_weight = symbol_weights.get(symbol, 0.0)
            # 簡化版：使用平均權重 × 總報酬作為貢獻
            # 實際應該使用標的的個別報酬
            return_contrib = avg_weight * total_return
            
            sector = None
            if request.sector_map and symbol in request.sector_map:
                sector = request.sector_map[symbol]
            
            data.append({
                "symbol": symbol,
                "return_contrib": return_contrib,
                "weight_avg": avg_weight,
                "sector": sector,
            })
        
        df = pd.DataFrame(data)
        return df
    
    def _compute_sector_attribution(
        self,
        request: PerformanceEngineRequest
    ) -> pd.DataFrame:
        """計算 Sector 層級歸因（簡化版 Brinson-style）
        
        Args:
            request: PerformanceEngineRequest 物件
        
        Returns:
            DataFrame with columns: [sector, allocation_effect, selection_effect, total_effect]
        """
        if not request.sector_map:
            return pd.DataFrame(columns=["sector", "allocation_effect", "selection_effect", "total_effect"])
        
        # 收集所有 Sector
        all_sectors = set(request.sector_map.values())
        
        # 簡化版：v1 先計算總貢獻，詳細的 Brinson 分解可後續實作
        data = []
        for sector in sorted(all_sectors):
            # 找出屬於此 Sector 的標的
            sector_symbols = [
                symbol for symbol, s in request.sector_map.items()
                if s == sector
            ]
            
            # 計算 Sector 總貢獻（簡化版）
            total_effect = 0.0  # TODO: 需要實作完整的 Brinson 分解
            
            data.append({
                "sector": sector,
                "allocation_effect": 0.0,  # TODO: 實作配置效應
                "selection_effect": 0.0,   # TODO: 實作選股效應
                "total_effect": total_effect,
            })
        
        df = pd.DataFrame(data)
        return df
    
    def _compute_factor_attribution(
        self,
        request: PerformanceEngineRequest
    ) -> tuple[pd.DataFrame, float]:
        """計算 Factor 層級歸因
        
        Args:
            request: PerformanceEngineRequest 物件
        
        Returns:
            (by_factor DataFrame, residual) tuple
        """
        if request.factor_returns is None or not request.factor_exposures_by_date:
            return (
                pd.DataFrame(columns=["factor", "factor_return", "factor_contribution", "exposure_avg"]),
                0.0
            )
        
        factor_returns_df = request.factor_returns
        
        # 計算每個因子的平均暴露
        all_factors = factor_returns_df.columns.tolist()
        factor_avg_exposures = {}
        
        for factor in all_factors:
            exposures_list = []
            for date, exposures in request.factor_exposures_by_date.items():
                if factor in exposures.index:
                    exposures_list.append(exposures.loc[factor])
            
            if exposures_list:
                factor_avg_exposures[factor] = np.mean(exposures_list)
        
        # 計算因子總報酬
        factor_total_returns = {}
        for factor in all_factors:
            factor_ret_series = factor_returns_df[factor]
            factor_total_returns[factor] = compute_cumulative_return(factor_ret_series)
        
        # 計算因子貢獻
        data = []
        total_factor_contribution = 0.0
        
        for factor in all_factors:
            avg_exposure = factor_avg_exposures.get(factor, 0.0)
            factor_return = factor_total_returns.get(factor, 0.0)
            factor_contribution = avg_exposure * factor_return
            
            total_factor_contribution += factor_contribution
            
            data.append({
                "factor": factor,
                "factor_return": factor_return,
                "factor_contribution": factor_contribution,
                "exposure_avg": avg_exposure,
            })
        
        # 計算殘差（特質收益）
        portfolio_total_return = compute_cumulative_return(request.portfolio_returns)
        residual = portfolio_total_return - total_factor_contribution
        
        df = pd.DataFrame(data)
        return (df, residual)

