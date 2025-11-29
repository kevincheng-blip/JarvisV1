"""
測試 PerformanceAnalyzer 模組

測試績效分析引擎：Mock 報酬計算、績效指標計算等情境
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from analysis.performance_analyzer import (
    PerformanceAnalyzer,
    PerformanceMetrics,
)
from factor_engine.signal_factor import (
    FSignalFactor,
    FSignalConfig,
    FSignalBucket,
)
from pipeline.walk_forward_config import WalkForwardPeriod
from pipeline.walk_forward_simulator import SimulationResult


# ---- 小工具：建立簡單的 SimulationResult ----

def _make_simulation_result(
    symbol: str,
    timestamps: List[float],
    raw_scores: List[float],
    buckets: List[FSignalBucket],
) -> SimulationResult:
    assert len(timestamps) == len(raw_scores) == len(buckets)
    
    signal_history: List[FSignalFactor] = []
    for ts, score, bucket in zip(timestamps, raw_scores, buckets):
        signal_history.append(
            FSignalFactor(
                symbol=symbol,
                timestamp=ts,
                raw_score=score,
                bucket=bucket,
            )
        )
    
    # WalkForwardPeriod 這裡只作為容器，不影響績效計算邏輯
    # 建立合理的最小 train 區間，確保符合驗證條件
    if not timestamps:
        # 如果 timestamps 為空，使用預設值（但理論上不應該發生，因為有 assert）
        first_ts = 0.0
        last_ts = 0.0
    else:
        first_ts = timestamps[0]
        last_ts = timestamps[-1]
    
    period = WalkForwardPeriod(
        train_start_ts=first_ts - 1.0,
        train_end_ts=first_ts,
        oos_start_ts=first_ts,
        oos_end_ts=last_ts,
    )
    
    return SimulationResult(
        period=period,
        symbol=symbol,
        signal_history=signal_history,
    )


# ---- 測試案例 ----

def test_all_strong_buy_signals_generate_positive_performance():
    """連續強烈買進訊號時，績效應該明顯為正，勝率接近 100%。"""
    symbol = "2330.TW"
    timestamps = [float(i) for i in range(10)]
    raw_scores = [0.8 for _ in range(10)]
    buckets = [FSignalBucket.STRONG_BUY for _ in range(10)]
    
    sim_result = _make_simulation_result(symbol, timestamps, raw_scores, buckets)
    
    cfg = FSignalConfig(symbol=symbol)
    analyzer = PerformanceAnalyzer(config=cfg)
    
    metrics_list = analyzer.analyze_simulation_results([sim_result])
    assert len(metrics_list) == 1
    
    metrics: PerformanceMetrics = metrics_list[0]
    
    assert metrics.symbol == symbol
    assert metrics.num_days == len(timestamps)
    assert metrics.total_return > 0.0
    assert metrics.hit_rate > 0.9  # 幾乎每天都賺錢
    assert metrics.sharpe_ratio > 0.0
    assert 0.0 <= metrics.max_drawdown < 1.0


def test_all_neutral_signals_has_zero_performance():
    """全部 NEUTRAL 訊號時，應該沒有任何損益，Sharpe / Hit Rate 皆為 0。"""
    symbol = "2330.TW"
    timestamps = [float(i) for i in range(5)]
    raw_scores = [0.5 for _ in range(5)]
    buckets = [FSignalBucket.NEUTRAL for _ in range(5)]
    
    sim_result = _make_simulation_result(symbol, timestamps, raw_scores, buckets)
    
    cfg = FSignalConfig(symbol=symbol)
    analyzer = PerformanceAnalyzer(config=cfg)
    
    metrics_list = analyzer.analyze_simulation_results([sim_result])
    metrics = metrics_list[0]
    
    assert metrics.num_days == len(timestamps)
    assert abs(metrics.total_return) < 1e-9
    assert metrics.sharpe_ratio == 0.0
    assert metrics.hit_rate == 0.0
    # 淨值都應該維持在 1.0
    for d in metrics.daily_returns:
        assert abs(d.daily_pnl) < 1e-9
        assert abs(d.cumulative_pnl - 1.0) < 1e-9


def test_mixed_buy_and_sell_signals_near_flat_total_return():
    """多空交錯訊號，整體績效應該接近打平，勝率接近 50%。"""
    symbol = "2330.TW"
    timestamps = [float(i) for i in range(8)]
    
    # 前 4 天偏多、後 4 天偏空，分數對稱
    raw_scores = [0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6]
    buckets = [
        FSignalBucket.STRONG_BUY,
        FSignalBucket.WEAK_BUY,
        FSignalBucket.STRONG_BUY,
        FSignalBucket.WEAK_BUY,
        FSignalBucket.STRONG_SELL,
        FSignalBucket.WEAK_SELL,
        FSignalBucket.STRONG_SELL,
        FSignalBucket.WEAK_SELL,
    ]
    
    sim_result = _make_simulation_result(symbol, timestamps, raw_scores, buckets)
    
    cfg = FSignalConfig(symbol=symbol)
    analyzer = PerformanceAnalyzer(config=cfg)
    
    metrics_list = analyzer.analyze_simulation_results([sim_result])
    metrics = metrics_list[0]
    
    # 總報酬應該接近 0（允許一點數值誤差）
    assert abs(metrics.total_return) < 0.05
    # 勝率大約在 30% ~ 70% 之間
    assert 0.3 <= metrics.hit_rate <= 0.7

