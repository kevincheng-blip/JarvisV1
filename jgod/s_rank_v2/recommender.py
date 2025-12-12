"""
S-Rank Engine V2 Recommender

Rule-based strategy recommendation engine.
Computes metrics and recommends top K strategies with weights.
"""

import math
from typing import List, Dict, Tuple
from jgod.s_rank_v2.models import (
    Metrics,
    RecommendationItem,
    StabilityGrade,
)
from jgod.observer.prediction_stability import (
    compute_stability_metrics,
    TimelineItem,
)


# Fixed strategy pool (v2.0 - hardcoded, future: configurable)
STRATEGY_POOL = [
    "trend_follow",
    "mean_reversion",
    "breakout",
    "risk_off",
    "momentum",
]

# Base weights for each strategy (sum = 1.0)
BASE_WEIGHTS = {
    "trend_follow": 0.3,
    "mean_reversion": 0.2,
    "breakout": 0.2,
    "risk_off": 0.15,
    "momentum": 0.15,
}

# Weight coefficients
TREND_WEIGHT = 0.2
STABILITY_WEIGHT = 0.3
VOLATILITY_PENALTY = 0.15


def compute_metrics(timeline_items: List[TimelineItem]) -> Metrics:
    """
    Compute metrics from timeline items.
    
    Args:
        timeline_items: List of {date, final_score} items
        
    Returns:
        Metrics object
    """
    if not timeline_items or len(timeline_items) < 5:
        return Metrics(
            n_points=len(timeline_items),
            score_std=0.0,
            max_abs_delta=0.0,
            trend_slope=0.0,
            stability_grade=StabilityGrade.NO_DATA,
        )
    
    # Use existing stability metrics computation
    stability_result = compute_stability_metrics(timeline_items)
    
    return Metrics(
        n_points=stability_result["n_points"],
        score_std=stability_result["score_std"],
        max_abs_delta=stability_result["max_abs_delta"],
        trend_slope=stability_result["trend_slope"],
        stability_grade=StabilityGrade(stability_result["stability_grade"]),
    )


def compute_strategy_scores(metrics: Metrics) -> Dict[str, float]:
    """
    Compute raw strategy scores for each strategy.
    
    Args:
        metrics: Computed metrics
        
    Returns:
        Dict mapping strategy -> raw score
    """
    if metrics.stability_grade == StabilityGrade.NO_DATA:
        return {strategy: 0.0 for strategy in STRATEGY_POOL}
    
    strategy_scores = {}
    
    for strategy in STRATEGY_POOL:
        base_score = BASE_WEIGHTS[strategy]
        
        # Trend component
        trend_component = 0.0
        if metrics.trend_slope > 0.1:
            # Positive trend: favor trend_follow and momentum
            if strategy in ["trend_follow", "momentum"]:
                trend_component = 0.3
            elif strategy == "mean_reversion":
                trend_component = -0.2
        elif metrics.trend_slope < -0.1:
            # Negative trend: favor mean_reversion
            if strategy == "mean_reversion":
                trend_component = 0.3
            elif strategy in ["trend_follow", "momentum"]:
                trend_component = -0.2
        
        # Stability component
        stability_component = 0.0
        if metrics.stability_grade == StabilityGrade.STABLE:
            # Stable: all strategies benefit, but trend_follow more
            stability_component = 0.2 if strategy == "trend_follow" else 0.1
        elif metrics.stability_grade == StabilityGrade.VOLATILE:
            # Volatile: favor risk_off
            if strategy == "risk_off":
                stability_component = 0.3
            else:
                stability_component = -0.1
        
        # Volatility penalty
        volatility_penalty = 0.0
        if metrics.score_std > 0.3:
            # High volatility: penalize all except risk_off
            if strategy != "risk_off":
                volatility_penalty = 0.2
        elif metrics.score_std < 0.1:
            # Low volatility: slight bonus for breakout
            if strategy == "breakout":
                volatility_penalty = -0.1  # Negative penalty = bonus
        
        # Calculate final score
        strategy_score = (
            base_score
            + TREND_WEIGHT * trend_component
            + STABILITY_WEIGHT * stability_component
            - VOLATILITY_PENALTY * volatility_penalty
        )
        
        strategy_scores[strategy] = max(0.0, strategy_score)  # Ensure non-negative
    
    return strategy_scores


def compute_weights(strategy_scores: Dict[str, float]) -> Dict[str, float]:
    """
    Normalize strategy scores using softmax to get weights (sum = 1.0).
    
    Args:
        strategy_scores: Dict mapping strategy -> raw score
        
    Returns:
        Dict mapping strategy -> normalized weight
    """
    # Softmax: exp(x) / sum(exp(x))
    # To avoid overflow, subtract max score before exp
    if not strategy_scores:
        return {}
    
    max_score = max(strategy_scores.values())
    exp_scores = {s: math.exp(score - max_score) for s, score in strategy_scores.items()}
    sum_exp = sum(exp_scores.values())
    
    if sum_exp == 0:
        # Fallback: equal weights
        n = len(strategy_scores)
        return {s: 1.0 / n for s in strategy_scores.keys()}
    
    weights = {s: exp_s / sum_exp for s, exp_s in exp_scores.items()}
    return weights


def generate_rationale(
    strategy: str,
    metrics: Metrics,
    weight: float,
) -> str:
    """
    Generate rationale text for a strategy recommendation.
    
    Args:
        strategy: Strategy name
        metrics: Computed metrics
        weight: Normalized weight
        
    Returns:
        Rationale text (Chinese)
    """
    if metrics.stability_grade == StabilityGrade.NO_DATA:
        return "資料不足，無法產生推薦理由"
    
    rationale_parts = []
    
    # Trend-based rationale
    if metrics.trend_slope > 0.1:
        if strategy == "trend_follow":
            rationale_parts.append("趨勢斜率為正，適合趨勢跟隨策略")
        elif strategy == "momentum":
            rationale_parts.append("動量指標顯示持續上升趨勢")
        elif strategy == "mean_reversion":
            rationale_parts.append("上升趨勢中，均值回歸策略權重較低")
    elif metrics.trend_slope < -0.1:
        if strategy == "mean_reversion":
            rationale_parts.append("下降趨勢中，適合均值回歸策略")
        elif strategy in ["trend_follow", "momentum"]:
            rationale_parts.append("下降趨勢中，趨勢跟隨策略權重較低")
    
    # Stability-based rationale
    if metrics.stability_grade == StabilityGrade.STABLE:
        if strategy == "trend_follow":
            rationale_parts.append("預測穩定性高，趨勢跟隨策略可靠")
        else:
            rationale_parts.append("預測穩定性高，策略執行風險較低")
    elif metrics.stability_grade == StabilityGrade.VOLATILE:
        if strategy == "risk_off":
            rationale_parts.append("預測波動大，建議採用風險規避策略")
        else:
            rationale_parts.append("預測波動大，策略權重降低")
    
    # Volatility-based rationale
    if metrics.score_std > 0.3:
        if strategy == "risk_off":
            rationale_parts.append("高波動環境，風險規避策略優先")
    elif metrics.score_std < 0.1:
        if strategy == "breakout":
            rationale_parts.append("低波動環境，適合突破策略")
    
    # Weight-based rationale
    if weight > 0.3:
        rationale_parts.append(f"權重 {weight:.1%}，為主要推薦策略")
    elif weight < 0.1:
        rationale_parts.append(f"權重 {weight:.1%}，建議謹慎使用")
    
    if not rationale_parts:
        return f"基於當前 metrics，{strategy} 策略權重為 {weight:.1%}"
    
    return "；".join(rationale_parts)


def recommend(
    timeline_items: List[TimelineItem],
    k: int = 5,
) -> Tuple[List[RecommendationItem], Dict[str, float], Dict[str, str], Metrics]:
    """
    Recommend top K strategies based on timeline metrics (mode=signals).
    
    Args:
        timeline_items: List of {date, final_score} items
        k: Number of top strategies to recommend
        
    Returns:
        Tuple of (items, weights, rationale, metrics)
    """
    # Compute metrics
    metrics = compute_metrics(timeline_items)
    
    # If no data, return empty
    if metrics.stability_grade == StabilityGrade.NO_DATA:
        return [], {}, {}, metrics
    
    # Compute strategy scores
    strategy_scores = compute_strategy_scores(metrics)
    
    # Normalize to weights
    weights = compute_weights(strategy_scores)
    
    # Sort by weight and take top K
    sorted_strategies = sorted(
        weights.items(),
        key=lambda x: x[1],
        reverse=True
    )[:k]
    
    # Build items
    items = [
        RecommendationItem(
            strategy=strategy,
            weight=weight,
            score=strategy_scores[strategy],
        )
        for strategy, weight in sorted_strategies
    ]
    
    # Generate rationale for each strategy
    rationale = {
        strategy: generate_rationale(strategy, metrics, weight)
        for strategy, weight in weights.items()
    }
    
    return items, weights, rationale, metrics


def recommend_from_performance(
    perf_items: List[dict],  # List of {strategy_id, metrics...}
    k: int = 5,
) -> Tuple[List[RecommendationItem], Dict[str, float], Dict[str, str]]:
    """
    Recommend top K strategies based on performance metrics (mode=performance).
    
    Args:
        perf_items: List of performance metrics dicts (from strategy_perf)
        k: Number of top strategies to recommend
        
    Returns:
        Tuple of (items, weights, rationale)
    """
    if not perf_items:
        return [], {}, {}
    
    # Weight coefficients for performance mode
    W1_SHARPE = 0.4
    W2_MDD = 0.2
    W3_TURNOVER = 0.1
    W4_RETURN = 0.2
    W5_DECAY = 0.1
    DECAY_PENALTY_K = 2.0
    
    strategy_scores = {}
    
    for perf in perf_items:
        strategy_id = perf.get("strategy_id", "")
        if not strategy_id:
            continue
        
        sharpe = perf.get("sharpe_proxy", 0.0)
        mdd = perf.get("max_drawdown_proxy", 0.0)
        turnover = perf.get("turnover_proxy", 0.0)
        avg_return = perf.get("avg_return_proxy", 0.0)
        decay_slope = perf.get("decay_slope", 0.0)
        grade = perf.get("grade", "NO_DATA")
        
        # Skip NO_DATA
        if grade == "NO_DATA":
            strategy_scores[strategy_id] = 0.0
            continue
        
        # Decay penalty (negative decay_slope = decay, penalize it)
        decay_penalty = max(0.0, -decay_slope) * DECAY_PENALTY_K
        
        # Calculate strategy score
        score = (
            W1_SHARPE * sharpe
            - W2_MDD * mdd
            - W3_TURNOVER * turnover
            + W4_RETURN * avg_return
            - W5_DECAY * decay_penalty
        )
        
        strategy_scores[strategy_id] = max(0.0, score)  # Ensure non-negative
    
    # Normalize to weights
    weights = compute_weights(strategy_scores)
    
    # Sort by weight and take top K
    sorted_strategies = sorted(
        weights.items(),
        key=lambda x: x[1],
        reverse=True
    )[:k]
    
    # Build items
    items = [
        RecommendationItem(
            strategy=strategy,
            weight=weight,
            score=strategy_scores[strategy],
        )
        for strategy, weight in sorted_strategies
    ]
    
    # Generate performance-based rationale
    rationale = {}
    for perf in perf_items:
        strategy_id = perf.get("strategy_id", "")
        if strategy_id not in weights:
            continue
        
        weight = weights[strategy_id]
        sharpe = perf.get("sharpe_proxy", 0.0)
        mdd = perf.get("max_drawdown_proxy", 0.0)
        decay_slope = perf.get("decay_slope", 0.0)
        grade = perf.get("grade", "NO_DATA")
        
        rationale_parts = []
        rationale_parts.append("基於績效指標驅動")
        
        if sharpe > 0.8:
            rationale_parts.append(f"sharpe_proxy={sharpe:.2f} 表現優異")
        elif sharpe < 0.3:
            rationale_parts.append(f"sharpe_proxy={sharpe:.2f} 表現不佳")
        
        if decay_slope < -0.05:
            rationale_parts.append(f"decay_slope={decay_slope:.3f} 顯示近期衰退，建議謹慎使用")
        elif decay_slope > 0.01:
            rationale_parts.append(f"decay_slope={decay_slope:.3f} 顯示績效改善")
        
        if mdd > 0.3:
            rationale_parts.append(f"max_drawdown={mdd:.2%} 風險較高")
        
        if weight > 0.3:
            rationale_parts.append(f"權重 {weight:.1%}，為主要推薦策略")
        
        rationale[strategy_id] = "；".join(rationale_parts) if rationale_parts else f"權重 {weight:.1%}"
    
    return items, weights, rationale

