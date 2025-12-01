"""Performance Types v1

定義 Performance Engine 使用的資料結構類型。

Reference:
- docs/JGOD_PERFORMANCE_ENGINE_STANDARD_v1.md
- spec/JGOD_PerformanceEngine_Spec.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Any

import pandas as pd

from jgod.execution.execution_types import Trade


@dataclass
class PerformanceEngineRequest:
    """Performance Engine 輸入請求資料結構
    
    Attributes:
        dates: 時間序列索引
        portfolio_nav: 投資組合淨值序列（以日期為索引）
        portfolio_returns: 投資組合報酬序列（以日期為索引）
        benchmark_nav: 基準淨值序列（可選）
        benchmark_returns: 基準報酬序列（可選）
        weights_by_date: 每個日期的權重字典 {date: {symbol: weight}}
        trades_by_date: 每個日期的交易列表 {date: [Trade, ...]}
        factor_returns: 因子報酬 DataFrame（可選，columns = factor，以日期為索引）
        factor_exposures_by_date: 每個日期的因子暴露（可選）
        sector_map: 標的到 Sector 的映射 {symbol: sector}
        config: 配置參數（年化基數、無風險利率等）
    """
    
    dates: Sequence[pd.Timestamp]
    portfolio_nav: pd.Series  # indexed by date
    portfolio_returns: pd.Series  # indexed by date
    benchmark_nav: Optional[pd.Series] = None
    benchmark_returns: Optional[pd.Series] = None
    weights_by_date: Dict[pd.Timestamp, pd.Series] = field(default_factory=dict)
    trades_by_date: Dict[pd.Timestamp, List[Trade]] = field(default_factory=dict)
    factor_returns: Optional[pd.DataFrame] = None  # columns = factor, indexed by date
    factor_exposures_by_date: Optional[Dict[pd.Timestamp, pd.Series]] = field(default_factory=dict)
    sector_map: Optional[Dict[str, str]] = None  # {symbol: sector}
    config: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> None:
        """驗證輸入資料的格式和合理性"""
        # 檢查 NAV 和 returns 的長度一致
        if len(self.portfolio_nav) != len(self.portfolio_returns):
            raise ValueError(
                f"portfolio_nav and portfolio_returns length mismatch: "
                f"{len(self.portfolio_nav)} != {len(self.portfolio_returns)}"
            )
        
        # 檢查索引一致性
        if not self.portfolio_nav.index.equals(self.portfolio_returns.index):
            raise ValueError("portfolio_nav and portfolio_returns must have the same index")
        
        # 檢查 benchmark（如果有）
        if self.benchmark_returns is not None:
            if not self.portfolio_returns.index.equals(self.benchmark_returns.index):
                raise ValueError("portfolio_returns and benchmark_returns must have the same index")
    
    @classmethod
    def from_path_a_result(
        cls,
        path_a_result,  # PathABacktestResult
        benchmark_returns: Optional[pd.Series] = None,
        factor_returns: Optional[pd.DataFrame] = None,
        factor_exposures_by_date: Optional[Dict] = None,
        sector_map: Optional[Dict[str, str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> PerformanceEngineRequest:
        """從 PathABacktestResult 建立 PerformanceEngineRequest
        
        這是一個 helper 方法，用於從 Path A 回測結果轉換為 Performance Engine 請求。
        
        Args:
            path_a_result: PathABacktestResult 物件
            benchmark_returns: 基準報酬序列（可選）
            factor_returns: 因子報酬 DataFrame（可選）
            factor_exposures_by_date: 因子暴露字典（可選）
            sector_map: Sector 映射（可選）
            config: 配置參數（可選）
        
        Returns:
            PerformanceEngineRequest 物件
        """
        # 從 portfolio snapshots 提取權重
        weights_by_date = {}
        for snapshot in path_a_result.portfolio_snapshots:
            if snapshot.weights is not None:
                weights_by_date[snapshot.date] = snapshot.weights
        
        # 提取交易（如果有）
        trades_by_date = {}
        if path_a_result.trades is not None and len(path_a_result.trades) > 0:
            # 將 Trade DataFrame 轉換為按日期分組的列表
            # 注意：這裡需要根據實際的 Trade 結構進行轉換
            pass  # TODO: 實作 Trade 轉換邏輯
        
        return cls(
            dates=path_a_result.nav_series.index.tolist(),
            portfolio_nav=path_a_result.nav_series,
            portfolio_returns=path_a_result.return_series,
            benchmark_returns=benchmark_returns,
            weights_by_date=weights_by_date,
            trades_by_date=trades_by_date,
            factor_returns=factor_returns,
            factor_exposures_by_date=factor_exposures_by_date or {},
            sector_map=sector_map,
            config=config or {}
        )


@dataclass
class PerformanceSummary:
    """績效摘要資料結構
    
    Attributes:
        total_return: 累積報酬
        cagr: 年化報酬
        vol_annualized: 年化波動度
        sharpe: Sharpe Ratio
        max_drawdown: 最大回落
        calmar: Calmar Ratio
        hit_rate: 勝率
        avg_win: 平均獲利
        avg_loss: 平均虧損
        turnover_annualized: 年化換手率
        active_return: 主動報酬（相對於基準）
        tracking_error: 追蹤誤差
        information_ratio: 資訊比率
    """
    
    total_return: float
    cagr: float
    vol_annualized: float
    sharpe: float
    max_drawdown: float
    calmar: float
    hit_rate: float
    avg_win: float
    avg_loss: float
    turnover_annualized: float
    
    # Benchmark / Relative（可選）
    active_return: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = {
            "total_return": self.total_return,
            "cagr": self.cagr,
            "vol_annualized": self.vol_annualized,
            "sharpe": self.sharpe,
            "max_drawdown": self.max_drawdown,
            "calmar": self.calmar,
            "hit_rate": self.hit_rate,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "turnover_annualized": self.turnover_annualized,
        }
        
        if self.active_return is not None:
            result["active_return"] = self.active_return
        if self.tracking_error is not None:
            result["tracking_error"] = self.tracking_error
        if self.information_ratio is not None:
            result["information_ratio"] = self.information_ratio
        
        return result


@dataclass
class AttributionReport:
    """歸因報告資料結構
    
    Attributes:
        by_symbol: Symbol 層級歸因 DataFrame
        by_sector: Sector 層級歸因 DataFrame
        by_factor: Factor 層級歸因 DataFrame
        residual: 特質收益（非解釋部分）
    """
    
    by_symbol: pd.DataFrame
    by_sector: Optional[pd.DataFrame] = None
    by_factor: Optional[pd.DataFrame] = None
    residual: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式（DataFrame 轉為 dict 格式）"""
        result = {
            "by_symbol": self.by_symbol.to_dict("records") if not self.by_symbol.empty else [],
            "residual": self.residual,
        }
        
        if self.by_sector is not None and not self.by_sector.empty:
            result["by_sector"] = self.by_sector.to_dict("records")
        
        if self.by_factor is not None and not self.by_factor.empty:
            result["by_factor"] = self.by_factor.to_dict("records")
        
        return result


@dataclass
class PerformanceEngineResult:
    """Performance Engine 完整輸出結果
    
    Attributes:
        summary: 績效摘要
        attribution: 歸因報告
        raw_frames: 原始 DataFrame（用於除錯）
    """
    
    summary: PerformanceSummary
    attribution: AttributionReport
    raw_frames: Dict[str, pd.DataFrame] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "summary": self.summary.to_dict(),
            "attribution": self.attribution.to_dict(),
            "raw_frames": {
                name: df.to_dict("records")
                for name, df in self.raw_frames.items()
            }
        }

