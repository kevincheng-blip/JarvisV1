"""
績效分析引擎（PerformanceAnalyzer）：Step 8

本模組實作創世紀量化系統 Step 8：績效分析引擎。

核心功能：
1. DailyReturn：單一時間點的報酬紀錄
2. PerformanceMetrics：績效指標總結
3. PerformanceAnalyzer：將 F_Signal 訊號轉換為績效指標

設計原則：
- 使用 Mock 報酬邏輯（基於 F_Signal 的 raw_score 和 bucket）
- 計算標準量化指標：Sharpe、Max Drawdown、CAGR、Hit Rate
- 不需要真實價格資料，即可測試整條 pipeline

作者：創世紀量化系統開發團隊
版本：v1.0
建立日期：2024-11-28
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
import numpy as np

from pipeline.walk_forward_simulator import SimulationResult
from factor_engine.signal_factor import (
    FSignalFactor,
    FSignalConfig,
    FSignalBucket,
)


@dataclass
class DailyReturn:
    """單一時間點的報酬紀錄（以 F_Signal 為基礎的模擬績效）"""
    
    timestamp: float
    symbol: str
    signal_bucket: FSignalBucket
    daily_pnl: float = 0.0  # 當期模擬報酬率
    cumulative_pnl: float = 0.0  # 從起點累積的模擬淨值（起始為 1.0）


@dataclass
class PerformanceMetrics:
    """單一標的在一段模擬期間內的績效總結。"""
    
    symbol: str
    num_days: int = 0  # 一共幾個 time-step（預設當作「日」頻率）
    total_return: float = 0.0  # 總報酬率
    cagr: float = 0.0  # 年化報酬率 (Compound Annual Growth Rate)
    sharpe_ratio: float = 0.0  # 夏普比率（假設無風險利率為 0）
    max_drawdown: float = 0.0  # 最大回檔（以淨值百分比表示）
    hit_rate: float = 0.0  # 勝率（報酬 > 0 的比例）
    
    # 原始模擬序列
    daily_returns: List[DailyReturn] = field(default_factory=list)


class PerformanceAnalyzer:
    """
    績效分析引擎 (Step 8)：
    將 WalkForwardSimulator 產出的 F_SignalFactor 訊號，轉換為
    模擬 PnL 序列與標準量化指標。
    
    v0 版本使用「Mock 報酬」邏輯：
    - 以 F_Signal 的 raw_score 與訊號分桶 (FSignalBucket) 來近似未來超額報酬。
    - 不需要真實價格資料，即可測試整條 pipeline 的行為與數學正確性。
    
    未來若要切換到真實價格：
    - 可以新增使用價格序列的版本（例如 _calculate_pnl_with_prices），
      保留本模組整體 API 不變。
    """
    
    def __init__(self, config: FSignalConfig):
        # 目前 v0 未直接使用 config（僅保留以便未來擴充）
        self.config = config
    
    # ------------------------------------------------------------------
    # Step 1：將 F_SignalFactor 序列轉成「模擬報酬序列」
    # ------------------------------------------------------------------
    
    def _calculate_pnl_sequence_from_signals(
        self, signal_history: List[FSignalFactor]
    ) -> List[DailyReturn]:
        """
        使用純訊號 (F_SignalFactor) 產生「模擬報酬序列」。
        
        Mock 交易邏輯：
        - 根據訊號分桶決定部位：
          STRONG_BUY / WEAK_BUY  → +1（偏多）
          STRONG_SELL / WEAK_SELL → -1（偏空）
          NEUTRAL                → 0（空手）
        - Mock 報酬：
          daily_return = position * raw_score * 0.01
        
        注意：這裡不使用真實價格，只用來測試整條績效管線。
        """
        if not signal_history:
            return []
        
        # 確保依時間排序
        sorted_signals = sorted(signal_history, key=lambda s: s.timestamp)
        
        daily_returns: List[DailyReturn] = []
        cumulative_pnl = 1.0  # 初始淨值
        
        for signal in sorted_signals:
            bucket = signal.bucket
            
            # 根據 bucket 決定部位
            if bucket in (FSignalBucket.STRONG_BUY, FSignalBucket.WEAK_BUY):
                position = 1
            elif bucket in (FSignalBucket.STRONG_SELL, FSignalBucket.WEAK_SELL):
                position = -1
            else:
                position = 0
            
            # Mock 報酬：依照訊號強度當成未來報酬 proxy
            if position != 0:
                daily_return = position * float(signal.raw_score) * 0.01
            else:
                daily_return = 0.0
            
            cumulative_pnl *= (1.0 + daily_return)
            
            daily_returns.append(
                DailyReturn(
                    timestamp=signal.timestamp,
                    symbol=signal.symbol,
                    signal_bucket=bucket,
                    daily_pnl=daily_return,
                    cumulative_pnl=cumulative_pnl,
                )
            )
        
        return daily_returns
    
    # ------------------------------------------------------------------
    # Step 2：由報酬序列計算標準績效指標
    # ------------------------------------------------------------------
    
    def _calculate_metrics(
        self, daily_returns: List[DailyReturn]
    ) -> PerformanceMetrics:
        """
        計算標準量化指標：Sharpe, Max Drawdown, CAGR, Hit Rate。
        """
        if not daily_returns:
            return PerformanceMetrics(symbol="N/A", num_days=0)
        
        symbol = daily_returns[0].symbol
        num_days = len(daily_returns)
        
        # 1. 報酬率序列
        returns = np.array([d.daily_pnl for d in daily_returns], dtype=float)
        
        # 2. 總報酬 & CAGR
        total_return = float(np.prod(1.0 + returns) - 1.0)
        
        # 假設為 Daily 資料，252 交易日
        num_years = num_days / 252.0 if num_days > 0 else 0.0
        if num_years > 0.0:
            cagr = (1.0 + total_return) ** (1.0 / num_years) - 1.0
        else:
            cagr = 0.0
        
        # 3. Sharpe Ratio（處理「完全沒波動」的特例）
        if num_days > 1:
            mean_daily = float(np.mean(returns))
            std_daily = float(np.std(returns, ddof=0))
        else:
            mean_daily = float(returns[0]) if num_days == 1 else 0.0
            std_daily = 0.0
        
        annualized_return = mean_daily * 252.0
        annualized_volatility = std_daily * np.sqrt(252.0)
        
        if annualized_volatility > 1e-6:
            sharpe_ratio = annualized_return / annualized_volatility
        else:
            # 幾乎沒波動：
            # - 年化報酬 ≈ 0 → Sharpe = 0
            # - 年化報酬 > 0 → 視為極高 Sharpe（幾乎無風險賺錢）
            # - 年化報酬 < 0 → 視為極低 Sharpe（幾乎無風險虧錢）
            if abs(annualized_return) < 1e-12:
                sharpe_ratio = 0.0
            elif annualized_return > 0:
                sharpe_ratio = 1_000_000.0
            else:
                sharpe_ratio = -1_000_000.0
        
        # 4. Max Drawdown
        cumulative_pnl = np.array([d.cumulative_pnl for d in daily_returns], dtype=float)
        if cumulative_pnl.size == 0:
            max_drawdown = 0.0
        else:
            peak = np.maximum.accumulate(cumulative_pnl)
            drawdown = (peak - cumulative_pnl) / peak
            max_drawdown = float(np.max(drawdown))
        
        # 5. Hit Rate
        winning_days = int(np.sum(returns > 1e-6))
        hit_rate = winning_days / num_days if num_days > 0 else 0.0
        
        return PerformanceMetrics(
            symbol=symbol,
            num_days=num_days,
            total_return=total_return,
            cagr=cagr,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            hit_rate=hit_rate,
            daily_returns=daily_returns,
        )
    
    # ------------------------------------------------------------------
    # Step 3：對整個 Walk-Forward 結果做績效分析
    # ------------------------------------------------------------------
    
    def analyze_simulation_results(
        self, results: List[SimulationResult]
    ) -> List[PerformanceMetrics]:
        """
        將多個 SimulationResult（每個 period × symbol）轉成績效指標列表。
        
        目前 v0 作法：
        - 每個 SimulationResult 都產生一份 PerformanceMetrics
        - 尚未跨 period 聚合同一個 symbol（之後可以再加 aggregate 功能）
        """
        metrics_list: List[PerformanceMetrics] = []
        
        for sim_result in results:
            daily_returns = self._calculate_pnl_sequence_from_signals(
                sim_result.signal_history
            )
            metrics = self._calculate_metrics(daily_returns)
            metrics_list.append(metrics)
        
        return metrics_list

