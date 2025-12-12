"""
Strategy Performance Evaluator

Deterministic performance evaluation from prediction timeline scores.
Pure Python implementation (no external dependencies).
"""

import math
from typing import List, Dict
from jgod.strategy_perf.models import StrategyPerformanceMetrics, PerformanceGrade
from jgod.observer.prediction_stability import TimelineItem


# Strategy signal preferences (how to interpret score)
STRATEGY_SIGNAL_PREFERENCE = {
    "trend_follow": "positive",  # score > 0 = long
    "mean_reversion": "negative",  # score < 0 = long (contrarian)
    "breakout": "positive",  # score > threshold = long
    "risk_off": "neutral",  # always reduce position
    "momentum": "positive",  # score > 0 = long
}


def _score_to_signal(score: float, strategy_id: str) -> float:
    """
    Convert score to signal (position size: -1.0 to 1.0).
    
    Args:
        score: Prediction score
        strategy_id: Strategy ID
        
    Returns:
        Signal value (-1.0 to 1.0)
    """
    preference = STRATEGY_SIGNAL_PREFERENCE.get(strategy_id, "positive")
    
    if preference == "positive":
        # Long if score > 0, short if score < 0
        return 1.0 if score > 0 else -1.0
    elif preference == "negative":
        # Contrarian: long if score < 0, short if score > 0
        return -1.0 if score > 0 else 1.0
    elif preference == "neutral":
        # Risk off: always reduce position
        return 0.0
    else:
        # Default: positive
        return 1.0 if score > 0 else -1.0


def _calculate_returns(scores: List[float], signals: List[float]) -> List[float]:
    """
    Calculate return proxy series.
    
    Args:
        scores: Score series
        signals: Signal series (position sizes)
        
    Returns:
        Return proxy series
    """
    returns = []
    for i in range(1, len(scores)):
        # Return = previous position * score change
        prev_signal = signals[i - 1]
        score_change = scores[i] - scores[i - 1]
        ret = prev_signal * score_change
        returns.append(ret)
    return returns


def _calculate_equity_curve(returns: List[float], initial: float = 1.0) -> List[float]:
    """
    Calculate equity curve from returns.
    
    Args:
        returns: Return series
        initial: Initial equity
        
    Returns:
        Equity curve
    """
    equity = [initial]
    for ret in returns:
        equity.append(equity[-1] * (1.0 + ret))
    return equity


def _calculate_max_drawdown(equity_curve: List[float]) -> float:
    """
    Calculate maximum drawdown from equity curve.
    
    Args:
        equity_curve: Equity curve series
        
    Returns:
        Maximum drawdown (0.0 to 1.0)
    """
    if not equity_curve:
        return 0.0
    
    peak = equity_curve[0]
    max_dd = 0.0
    
    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    
    return max_dd


def _calculate_decay_slope(returns: List[float], window: int) -> float:
    """
    Calculate decay slope using rolling sharpe proxy.
    
    Args:
        returns: Return series
        window: Rolling window size
        
    Returns:
        Decay slope (negative = decay, positive = improvement)
    """
    if len(returns) < window or window < 2:
        return 0.0
    
    # Calculate rolling sharpe proxy for last window points
    rolling_sharpes = []
    start_idx = max(0, len(returns) - window)
    
    for i in range(start_idx, len(returns)):
        # Use a smaller window for each point (at least 2 points)
        window_size = min(window, i - start_idx + 1)
        if window_size < 2:
            continue
        
        window_returns = returns[max(0, i - window_size + 1):i + 1]
        if len(window_returns) < 2:
            continue
        
        mean_ret = sum(window_returns) / len(window_returns)
        variance = sum((r - mean_ret) ** 2 for r in window_returns) / len(window_returns)
        std_ret = math.sqrt(variance) if variance > 0 else 0.0
        sharpe = mean_ret / (std_ret + 1e-6) if std_ret > 0 else 0.0
        rolling_sharpes.append(sharpe)
    
    if len(rolling_sharpes) < 2:
        return 0.0
    
    # Linear regression on rolling sharpe indices
    n = len(rolling_sharpes)
    sum_x = sum(range(n))
    sum_y = sum(rolling_sharpes)
    sum_xy = sum(i * rolling_sharpes[i] for i in range(n))
    sum_x2 = sum(i * i for i in range(n))
    
    denominator = n * sum_x2 - sum_x * sum_x
    if abs(denominator) < 1e-10:
        return 0.0
    
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    # Clamp to reasonable range to avoid extreme values
    return max(-1.0, min(1.0, slope))


def evaluate_strategy_performance(
    timeline_items: List[TimelineItem],
    strategy_id: str,
    window: int = 20,
) -> StrategyPerformanceMetrics:
    """
    Evaluate strategy performance from timeline items.
    
    Args:
        timeline_items: List of {date, final_score} items
        strategy_id: Strategy ID
        window: Window size for decay calculation
        
    Returns:
        StrategyPerformanceMetrics
    """
    if not timeline_items or len(timeline_items) < 10:
        return StrategyPerformanceMetrics(
            strategy_id=strategy_id,
            n_points=len(timeline_items),
            avg_return_proxy=0.0,
            sharpe_proxy=0.0,
            max_drawdown_proxy=0.0,
            turnover_proxy=0.0,
            decay_slope=0.0,
            grade=PerformanceGrade.NO_DATA,
        )
    
    # Extract scores (chronological order)
    scores = [item["final_score"] for item in timeline_items]
    
    # Convert scores to signals
    signals = [_score_to_signal(score, strategy_id) for score in scores]
    
    # Calculate returns
    returns = _calculate_returns(scores, signals)
    
    if not returns:
        return StrategyPerformanceMetrics(
            strategy_id=strategy_id,
            n_points=len(timeline_items),
            avg_return_proxy=0.0,
            sharpe_proxy=0.0,
            max_drawdown_proxy=0.0,
            turnover_proxy=0.0,
            decay_slope=0.0,
            grade=PerformanceGrade.NO_DATA,
        )
    
    # Calculate metrics
    n_points = len(returns)
    avg_return_proxy = sum(returns) / n_points
    
    # Sharpe proxy
    std_ret = math.sqrt(sum((r - avg_return_proxy) ** 2 for r in returns) / n_points)
    sharpe_proxy = avg_return_proxy / (std_ret + 1e-6) if std_ret > 0 else 0.0
    
    # Max drawdown
    equity_curve = _calculate_equity_curve(returns)
    max_drawdown_proxy = _calculate_max_drawdown(equity_curve)
    
    # Turnover proxy (position changes)
    position_changes = sum(1 for i in range(1, len(signals)) if signals[i] != signals[i - 1])
    turnover_proxy = position_changes / len(signals) if len(signals) > 0 else 0.0
    
    # Decay slope
    decay_slope = _calculate_decay_slope(returns, window)
    
    # Grade
    if sharpe_proxy >= 0.8 and max_drawdown_proxy <= 0.2 and decay_slope >= -0.01:
        grade = PerformanceGrade.GOOD
    elif sharpe_proxy >= 0.3 and max_drawdown_proxy <= 0.35:
        grade = PerformanceGrade.WATCH
    else:
        grade = PerformanceGrade.BAD
    
    return StrategyPerformanceMetrics(
        strategy_id=strategy_id,
        n_points=n_points,
        avg_return_proxy=round(avg_return_proxy, 4),
        sharpe_proxy=round(sharpe_proxy, 4),
        max_drawdown_proxy=round(max_drawdown_proxy, 4),
        turnover_proxy=round(turnover_proxy, 4),
        decay_slope=round(decay_slope, 4),
        grade=grade,
    )


def evaluate_all_strategies(
    timeline_items: List[TimelineItem],
    strategy_pool: List[str],
    window: int = 20,
) -> List[StrategyPerformanceMetrics]:
    """
    Evaluate performance for all strategies.
    
    Args:
        timeline_items: List of {date, final_score} items
        strategy_pool: List of strategy IDs
        window: Window size for decay calculation
        
    Returns:
        List of StrategyPerformanceMetrics
    """
    return [
        evaluate_strategy_performance(timeline_items, strategy_id, window)
        for strategy_id in strategy_pool
    ]

