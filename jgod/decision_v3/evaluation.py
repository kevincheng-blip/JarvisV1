"""
Decision V3 Evaluation

Evaluates Decision V3 decisions by replaying prediction timeline and computing metrics.
Pure Python implementation (no external dependencies).
"""

import math
import logging
from typing import List, Dict, Literal, Optional
from datetime import date

from jgod.observer.prediction_stability import TimelineItem

logger = logging.getLogger(__name__)


class EvaluationVerdict:
    """Evaluation verdict types"""
    IMPROVED = "IMPROVED"
    NEUTRAL = "NEUTRAL"
    REGRESSED = "REGRESSED"
    NO_DATA = "NO_DATA"


def _calculate_equity_curve(returns: List[float], initial: float = 1.0) -> List[float]:
    """Calculate equity curve from returns"""
    equity = [initial]
    for ret in returns:
        equity.append(equity[-1] * (1.0 + ret))
    return equity


def _calculate_max_drawdown(equity_curve: List[float]) -> float:
    """Calculate maximum drawdown from equity curve"""
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


def _calculate_decision_consistency(
    timeline_items: List[TimelineItem],
    primary_strategy: Optional[str],
    window: int = 5,
) -> float:
    """
    Calculate decision consistency proxy.
    
    Uses signal stability from timeline as a proxy for decision consistency.
    """
    if not timeline_items or len(timeline_items) < window:
        return 0.0
    
    # Use last N items
    recent_items = timeline_items[:window]
    
    # Extract signals (if available) or use score direction
    signals = []
    for item in recent_items:
        # Use signal if available, otherwise infer from score direction
        signal = item.get("signal", "UNKNOWN")
        if signal == "UNKNOWN":
            # Infer from score: positive = LONG, negative = SHORT
            score = item.get("final_score", 0.0)
            signal = "LONG" if score > 0 else "SHORT"
        signals.append(signal)
    
    # Count consistent signals (same as most common)
    if not signals:
        return 0.0
    
    # Count occurrences
    signal_counts = {}
    for s in signals:
        signal_counts[s] = signal_counts.get(s, 0) + 1
    
    # Most common signal count
    max_count = max(signal_counts.values())
    consistency = max_count / len(signals)
    
    return consistency


def evaluate_decision_v3(
    timeline_items: List[TimelineItem],
    decision_result: Dict,
    window: int = 20,
) -> Dict:
    """
    Evaluate Decision V3 decision by replaying timeline.
    
    Args:
        timeline_items: List of timeline items (chronological order, newest first)
        decision_result: Decision V3 result dict (from service)
        window: Evaluation window size
    
    Returns:
        Evaluation metrics dict with:
        - n_points: int
        - hit_rate_proxy: float
        - avg_return_proxy: float
        - max_drawdown_proxy: float
        - turnover_proxy: float
        - decision_consistency: float
        - verdict: IMPROVED | NEUTRAL | REGRESSED | NO_DATA
        - recommendation_next_step: str (Traditional Chinese)
    """
    n_points = len(timeline_items)
    
    # NO_DATA check
    if n_points < 10:
        return {
            "n_points": n_points,
            "hit_rate_proxy": 0.0,
            "avg_return_proxy": 0.0,
            "max_drawdown_proxy": 0.0,
            "turnover_proxy": 0.0,
            "decision_consistency": 0.0,
            "verdict": EvaluationVerdict.NO_DATA,
            "recommendation_next_step": "資料點不足（<10），無法進行評估。請等待更多預測資料。",
        }
    
    # Reverse to chronological order (oldest first)
    items_chrono = list(reversed(timeline_items))
    
    # Extract scores
    scores = [item.get("final_score", 0.0) for item in items_chrono]
    
    # Get primary strategy from decision
    primary_strategy = decision_result.get("selected_primary_strategy")
    
    # Calculate return proxy: delta(final_score)
    returns = []
    for i in range(1, len(scores)):
        delta = scores[i] - scores[i - 1]
        returns.append(delta)
    
    if not returns:
        return {
            "n_points": n_points,
            "hit_rate_proxy": 0.0,
            "avg_return_proxy": 0.0,
            "max_drawdown_proxy": 0.0,
            "turnover_proxy": 0.0,
            "decision_consistency": 0.0,
            "verdict": EvaluationVerdict.NO_DATA,
            "recommendation_next_step": "無法計算報酬率代理指標。請確認預測資料完整性。",
        }
    
    # Calculate metrics
    n_returns = len(returns)
    avg_return_proxy = sum(returns) / n_returns
    
    # Hit rate proxy: depends on primary strategy
    # For trend_follow/breakout/momentum: positive delta is good
    # For mean_reversion: negative delta is good
    if primary_strategy in ["trend_follow", "breakout", "momentum"]:
        # Positive delta = hit
        hits = sum(1 for r in returns if r > 0)
    elif primary_strategy == "mean_reversion":
        # Negative delta = hit (contrarian)
        hits = sum(1 for r in returns if r < 0)
    else:
        # Default: positive delta
        hits = sum(1 for r in returns if r > 0)
    
    hit_rate_proxy = hits / n_returns if n_returns > 0 else 0.0
    
    # Max drawdown proxy: from equity curve
    equity_curve = _calculate_equity_curve(returns)
    max_drawdown_proxy = _calculate_max_drawdown(equity_curve)
    
    # Turnover proxy: abs(delta(final_score)) average
    turnover_proxy = sum(abs(r) for r in returns) / n_returns if n_returns > 0 else 0.0
    
    # Decision consistency
    decision_consistency = _calculate_decision_consistency(
        timeline_items,
        primary_strategy,
        window=min(5, n_points),
    )
    
    # Determine verdict
    if avg_return_proxy > 0 and hit_rate_proxy >= 0.55 and max_drawdown_proxy <= 0.18:
        verdict = EvaluationVerdict.IMPROVED
    elif avg_return_proxy < 0 and max_drawdown_proxy > 0.25:
        verdict = EvaluationVerdict.REGRESSED
    else:
        verdict = EvaluationVerdict.NEUTRAL
    
    # Generate recommendation
    recommendation_parts = []
    
    if verdict == EvaluationVerdict.IMPROVED:
        recommendation_parts.append("決策表現良好，建議維持當前策略配置。")
        if decision_consistency < 0.6:
            recommendation_parts.append("注意：決策一致性偏低，建議檢視策略選擇邏輯。")
    elif verdict == EvaluationVerdict.REGRESSED:
        recommendation_parts.append("決策表現下滑，建議：")
        recommendation_parts.append("1. 檢視風險控制參數（max_drawdown 偏高）")
        recommendation_parts.append("2. 考慮切換至備選策略或降低倉位")
        if hit_rate_proxy < 0.45:
            recommendation_parts.append("3. 命中率偏低，建議重新評估策略適用性")
    else:  # NEUTRAL
        recommendation_parts.append("決策表現中性，建議：")
        recommendation_parts.append("1. 持續監控關鍵指標（hit_rate, max_drawdown）")
        recommendation_parts.append("2. 若趨勢持續，考慮調整策略權重")
    
    recommendation_next_step = "\n".join(recommendation_parts[:6])  # Max 6 lines
    
    return {
        "n_points": n_points,
        "hit_rate_proxy": round(hit_rate_proxy, 4),
        "avg_return_proxy": round(avg_return_proxy, 4),
        "max_drawdown_proxy": round(max_drawdown_proxy, 4),
        "turnover_proxy": round(turnover_proxy, 4),
        "decision_consistency": round(decision_consistency, 4),
        "verdict": verdict,
        "recommendation_next_step": recommendation_next_step,
    }

