"""Performance Metrics v1

純績效指標計算函式，不牽涉歸因分析。

Reference:
- docs/JGOD_PERFORMANCE_ENGINE_STANDARD_v1.md
"""

from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from jgod.execution.execution_types import Trade


def compute_cumulative_return(returns: pd.Series) -> float:
    """計算累積報酬
    
    公式：R_total = (1 + r1) * (1 + r2) * ... * (1 + rn) - 1
    
    Args:
        returns: 報酬序列
    
    Returns:
        累積報酬（例如 0.15 表示 15%）
    """
    if returns.empty:
        return 0.0
    
    cumulative = (1 + returns).prod()
    return float(cumulative - 1.0)


def compute_cagr(
    returns: pd.Series,
    periods_per_year: int = 252
) -> float:
    """計算年化報酬（CAGR）
    
    公式：CAGR = ((1 + R_total)^(1/T) - 1)
    其中 T 為年數 = len(returns) / periods_per_year
    
    Args:
        returns: 報酬序列
        periods_per_year: 年化基數（台股通常為 252）
    
    Returns:
        年化報酬（例如 0.12 表示 12%）
    """
    if returns.empty:
        return 0.0
    
    total_return = compute_cumulative_return(returns)
    num_periods = len(returns)
    years = num_periods / periods_per_year
    
    if years <= 0:
        return 0.0
    
    if total_return <= -1.0:
        return -1.0  # 完全虧損
    
    cagr = (1.0 + total_return) ** (1.0 / years) - 1.0
    return float(cagr)


def compute_annualized_vol(
    returns: pd.Series,
    periods_per_year: int = 252
) -> float:
    """計算年化波動度
    
    公式：σ_annual = σ_daily × √periods_per_year
    
    Args:
        returns: 報酬序列
        periods_per_year: 年化基數（台股通常為 252）
    
    Returns:
        年化波動度（例如 0.15 表示 15%）
    """
    if returns.empty:
        return 0.0
    
    vol_daily = returns.std()
    vol_annual = vol_daily * np.sqrt(periods_per_year)
    return float(vol_annual)


def compute_sharpe(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """計算 Sharpe Ratio
    
    公式：Sharpe = (mean(R) - Rf) / σ
    
    Args:
        returns: 報酬序列
        risk_free_rate: 無風險利率（年化）
        periods_per_year: 年化基數
    
    Returns:
        Sharpe Ratio（無單位）
    """
    if returns.empty:
        return 0.0
    
    vol_annual = compute_annualized_vol(returns, periods_per_year)
    
    if vol_annual == 0:
        return 0.0
    
    # 計算年化平均報酬
    mean_return_annual = returns.mean() * periods_per_year
    
    sharpe = (mean_return_annual - risk_free_rate) / vol_annual
    return float(sharpe)


def compute_max_drawdown(nav: pd.Series) -> float:
    """計算最大回落（Max Drawdown）
    
    公式：MaxDD = max((Peak_t - NAV_t) / Peak_t)
    
    Args:
        nav: 淨值序列
    
    Returns:
        最大回落（例如 -0.15 表示 -15%，負數）
    """
    if nav.empty:
        return 0.0
    
    # 計算累積最高點
    running_max = nav.cummax()
    
    # 計算回撤
    drawdown = (nav - running_max) / running_max
    
    max_dd = drawdown.min()
    return float(max_dd)


def compute_calmar(cagr: float, max_drawdown: float) -> float:
    """計算 Calmar Ratio
    
    公式：Calmar = CAGR / |MaxDD|
    
    Args:
        cagr: 年化報酬
        max_drawdown: 最大回落（負數）
    
    Returns:
        Calmar Ratio（無單位）
    """
    if max_drawdown == 0:
        return 0.0
    
    calmar = cagr / abs(max_drawdown)
    return float(calmar)


def compute_hit_rate(returns: pd.Series) -> float:
    """計算勝率（Hit Rate）
    
    公式：Hit Rate = 正報酬日數 / 總交易日數
    
    Args:
        returns: 報酬序列
    
    Returns:
        勝率（0-1，例如 0.55 表示 55%）
    """
    if returns.empty:
        return 0.0
    
    positive_count = (returns > 0).sum()
    total_count = len(returns)
    
    if total_count == 0:
        return 0.0
    
    hit_rate = positive_count / total_count
    return float(hit_rate)


def compute_avg_win_loss(returns: pd.Series) -> tuple[float, float]:
    """計算平均獲利和平均虧損
    
    Args:
        returns: 報酬序列
    
    Returns:
        (avg_win, avg_loss) tuple
        - avg_win: 平均獲利（僅計算正報酬）
        - avg_loss: 平均虧損（僅計算負報酬，取絕對值）
    """
    if returns.empty:
        return (0.0, 0.0)
    
    wins = returns[returns > 0]
    losses = returns[returns < 0]
    
    avg_win = float(wins.mean()) if len(wins) > 0 else 0.0
    avg_loss = float(abs(losses.mean())) if len(losses) > 0 else 0.0
    
    return (avg_win, avg_loss)


def compute_turnover(
    trades_by_date: Dict[pd.Timestamp, List[Trade]],
    nav_series: pd.Series
) -> float:
    """計算平均換手率
    
    公式：Turnover = (1/T) × Σ_t Turnover_t
    其中 Turnover_t = Σ_i |w_i,t - w_i,t-1|
    
    簡化版：使用交易金額 / NAV 來估算
    
    Args:
        trades_by_date: 每個日期的交易列表
        nav_series: 淨值序列
    
    Returns:
        平均換手率（0-1，例如 0.20 表示 20%）
    """
    if not trades_by_date or nav_series.empty:
        return 0.0
    
    total_turnover = 0.0
    count = 0
    
    for date, trades in trades_by_date.items():
        if date not in nav_series.index:
            continue
        
        nav = nav_series.loc[date]
        if nav <= 0:
            continue
        
        # 計算當日交易總金額
        daily_trade_amount = 0.0
        for trade in trades:
            trade_amount = abs(trade.fill.fill_price * trade.fill.filled_quantity)
            daily_trade_amount += trade_amount
        
        # 換手率 = 交易金額 / NAV（簡化版）
        if nav > 0:
            daily_turnover = daily_trade_amount / nav
            total_turnover += daily_turnover
            count += 1
    
    if count == 0:
        return 0.0
    
    avg_turnover = total_turnover / count
    return float(avg_turnover)


def compute_tracking_error(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 252
) -> float:
    """計算追蹤誤差（Tracking Error）
    
    公式：TE = std(R_active) × √periods_per_year
    
    Args:
        portfolio_returns: 投資組合報酬序列
        benchmark_returns: 基準報酬序列
        periods_per_year: 年化基數
    
    Returns:
        年化追蹤誤差
    """
    if portfolio_returns.empty or benchmark_returns.empty:
        return 0.0
    
    # 計算主動報酬
    active_returns = portfolio_returns - benchmark_returns
    
    # 計算標準差並年化
    te_annual = active_returns.std() * np.sqrt(periods_per_year)
    return float(te_annual)


def compute_information_ratio(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 252
) -> float:
    """計算資訊比率（Information Ratio）
    
    公式：IR = mean(R_active) / TE
    
    Args:
        portfolio_returns: 投資組合報酬序列
        benchmark_returns: 基準報酬序列
        periods_per_year: 年化基數
    
    Returns:
        資訊比率
    """
    if portfolio_returns.empty or benchmark_returns.empty:
        return 0.0
    
    # 計算主動報酬
    active_returns = portfolio_returns - benchmark_returns
    
    # 計算平均主動報酬（年化）
    mean_active = active_returns.mean() * periods_per_year
    
    # 計算追蹤誤差
    te = compute_tracking_error(portfolio_returns, benchmark_returns, periods_per_year)
    
    if te == 0:
        return 0.0
    
    ir = mean_active / te
    return float(ir)

