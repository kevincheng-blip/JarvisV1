"""
Decision V3 Compare Engine

Compares Decision V3 against a baseline decision using evaluation metrics.
"""

import logging
from typing import Dict, Literal, Optional
from datetime import date

from jgod.decision_v3.models import DecisionV3Result, StrategyWeight, RiskPlan
from jgod.decision_v3.evaluation import evaluate_decision_v3, EvaluationVerdict
from jgod.observer.prediction_stability import TimelineItem

logger = logging.getLogger(__name__)


class CompareWinner:
    """Compare winner types"""
    V3 = "V3"
    BASELINE = "BASELINE"
    TIE = "TIE"
    NO_DATA = "NO_DATA"


def build_baseline_decision(
    symbol: str,
    mode: str = "performance",
    limit: int = 60,
    k: int = 5,
) -> DecisionV3Result:
    """
    Build a baseline decision with fixed parameters.
    
    Baseline definition:
    - risk_state: "CAUTION"
    - position_scale: 0.50
    - primary_strategy: "momentum" (or "trend_follow" if momentum not available)
    - confidence: 0.50
    
    Args:
        symbol: Stock symbol
        mode: Decision mode (not used in baseline, but kept for consistency)
        limit: Number of timeline items (not used in baseline)
        k: Number of strategies (not used in baseline)
        
    Returns:
        DecisionV3Result with fixed baseline parameters
    """
    # Fixed baseline strategy
    primary_strategy = "momentum"  # Can fallback to "trend_follow" if needed
    
    # Fixed baseline weights (simple distribution)
    weights = [
        StrategyWeight(
            strategy_id=primary_strategy,
            weight=0.60,
            rationale="Baseline fixed strategy",
        ),
        StrategyWeight(
            strategy_id="trend_follow",
            weight=0.25,
            rationale="Baseline secondary",
        ),
        StrategyWeight(
            strategy_id="risk_off",
            weight=0.15,
            rationale="Baseline risk buffer",
        ),
    ]
    
    # Fixed baseline risk plan
    risk_plan = RiskPlan(
        position_scale=0.50,
        risk_state="CAUTION",
        reasons=["Baseline fixed risk parameters"],
    )
    
    # Fixed baseline confidence
    confidence = 0.50
    
    # Generate baseline explanation
    explain = f"""Baseline 決策（固定參數）：
- 主要策略：{primary_strategy}
- 建議倉位：50%
- 風險狀態：謹慎操作
- 信心度：50%
此為對照基準，用於評估 Decision V3 的相對表現。"""
    
    return DecisionV3Result(
        symbol=symbol,
        as_of_date=date.today(),
        selected_primary_strategy=primary_strategy,
        selected_secondary_strategies=["trend_follow", "risk_off"],
        weights=weights,
        risk_plan=risk_plan,
        confidence=confidence,
        explain=explain,
    )


def compute_compare(
    symbol: str,
    mode: str = "performance",
    limit: int = 60,
    k: int = 5,
    window: int = 20,
) -> Dict:
    """
    Compute comparison between Decision V3 and Baseline.
    
    Args:
        symbol: Stock symbol
        mode: Decision mode
        limit: Number of timeline items to use
        k: Number of top strategies to recommend
        window: Evaluation window size
        
    Returns:
        Compare result dict with:
        - winner: V3 | BASELINE | TIE | NO_DATA
        - delta_metrics: dict of metric differences (v3 - baseline)
        - summary: Traditional Chinese summary (<= 8 lines)
        - recommendation_next_step: Traditional Chinese recommendation (<= 6 lines)
    """
    # Step 1: Get Decision V3 result (avoid circular import)
    from jgod.decision_v3.service import compute_decision
    v3_result = compute_decision(symbol, mode, limit, k)
    v3_dict = {
        "symbol": v3_result.symbol,
        "selected_primary_strategy": v3_result.selected_primary_strategy,
        "risk_plan": {
            "position_scale": v3_result.risk_plan.position_scale if v3_result.risk_plan else 0.0,
            "risk_state": v3_result.risk_plan.risk_state if v3_result.risk_plan else "RISK_OFF",
        },
        "confidence": v3_result.confidence,
    }
    
    # Step 2: Get Baseline result
    baseline_result = build_baseline_decision(symbol, mode, limit, k)
    baseline_dict = {
        "symbol": baseline_result.symbol,
        "selected_primary_strategy": baseline_result.selected_primary_strategy,
        "risk_plan": {
            "position_scale": baseline_result.risk_plan.position_scale if baseline_result.risk_plan else 0.0,
            "risk_state": baseline_result.risk_plan.risk_state if baseline_result.risk_plan else "RISK_OFF",
        },
        "confidence": baseline_result.confidence,
    }
    
    # Step 3: Fetch timeline items (reuse from service, avoid circular import)
    from jgod.decision_v3.service import _fetch_timeline_items
    timeline_items = _fetch_timeline_items(symbol, limit)
    
    # Step 4: Evaluate both decisions
    v3_eval = evaluate_decision_v3(timeline_items, v3_dict, window)
    baseline_eval = evaluate_decision_v3(timeline_items, baseline_dict, window)
    
    # Step 5: Check for NO_DATA
    if v3_eval["verdict"] == EvaluationVerdict.NO_DATA or baseline_eval["verdict"] == EvaluationVerdict.NO_DATA:
        return {
            "winner": CompareWinner.NO_DATA,
            "delta_metrics": {
                "hit_rate_proxy": 0.0,
                "avg_return_proxy": 0.0,
                "max_drawdown_proxy": 0.0,
                "turnover_proxy": 0.0,
                "decision_consistency": 0.0,
            },
            "summary": "資料不足，無法進行對照評估。",
            "recommendation_next_step": "請等待更多預測資料後再進行對照。",
        }
    
    # Step 6: Calculate delta metrics (v3 - baseline)
    delta_metrics = {
        "hit_rate_proxy": v3_eval["hit_rate_proxy"] - baseline_eval["hit_rate_proxy"],
        "avg_return_proxy": v3_eval["avg_return_proxy"] - baseline_eval["avg_return_proxy"],
        "max_drawdown_proxy": v3_eval["max_drawdown_proxy"] - baseline_eval["max_drawdown_proxy"],
        "turnover_proxy": v3_eval["turnover_proxy"] - baseline_eval["turnover_proxy"],
        "decision_consistency": v3_eval["decision_consistency"] - baseline_eval["decision_consistency"],
    }
    
    # Step 7: Calculate composite scores
    # score = avg_return_proxy - 0.7*max_drawdown_proxy + 0.2*hit_rate_proxy - 0.1*turnover_proxy
    score_v3 = (
        v3_eval["avg_return_proxy"]
        - 0.7 * v3_eval["max_drawdown_proxy"]
        + 0.2 * v3_eval["hit_rate_proxy"]
        - 0.1 * v3_eval["turnover_proxy"]
    )
    
    score_baseline = (
        baseline_eval["avg_return_proxy"]
        - 0.7 * baseline_eval["max_drawdown_proxy"]
        + 0.2 * baseline_eval["hit_rate_proxy"]
        - 0.1 * baseline_eval["turnover_proxy"]
    )
    
    # Step 8: Determine winner
    score_diff = score_v3 - score_baseline
    if abs(score_diff) < 0.01:  # Tie threshold
        winner = CompareWinner.TIE
    elif score_v3 > score_baseline:
        winner = CompareWinner.V3
    else:
        winner = CompareWinner.BASELINE
    
    # Step 9: Generate summary (Traditional Chinese, <= 8 lines)
    summary_parts = []
    
    if winner == CompareWinner.V3:
        summary_parts.append("Decision V3 表現優於 Baseline。")
        if delta_metrics["avg_return_proxy"] > 0:
            summary_parts.append(f"平均報酬提升 {delta_metrics['avg_return_proxy']*100:.2f}%。")
        if delta_metrics["max_drawdown_proxy"] < 0:
            summary_parts.append(f"最大回撤降低 {abs(delta_metrics['max_drawdown_proxy'])*100:.1f}%。")
        if delta_metrics["hit_rate_proxy"] > 0:
            summary_parts.append(f"命中率提升 {delta_metrics['hit_rate_proxy']*100:.1f}%。")
        summary_parts.append("綜合評分：V3 領先。")
    elif winner == CompareWinner.BASELINE:
        summary_parts.append("Baseline 表現優於 Decision V3。")
        if delta_metrics["avg_return_proxy"] < 0:
            summary_parts.append(f"平均報酬落後 {abs(delta_metrics['avg_return_proxy'])*100:.2f}%。")
        if delta_metrics["max_drawdown_proxy"] > 0:
            summary_parts.append(f"最大回撤增加 {delta_metrics['max_drawdown_proxy']*100:.1f}%。")
        summary_parts.append("建議檢視 Decision V3 的決策邏輯。")
    else:  # TIE
        summary_parts.append("Decision V3 與 Baseline 表現相當。")
        summary_parts.append("兩者評分接近，建議持續監控。")
    
    summary = "\n".join(summary_parts[:8])
    
    # Step 10: Generate recommendation_next_step (Traditional Chinese, <= 6 lines)
    recommendation_parts = []
    
    if winner == CompareWinner.V3:
        recommendation_parts.append("建議：")
        recommendation_parts.append("1. 維持 Decision V3 當前配置")
        recommendation_parts.append("2. 持續監控關鍵指標變化")
        if delta_metrics["decision_consistency"] < 0:
            recommendation_parts.append("3. 注意決策一致性仍有改善空間")
    elif winner == CompareWinner.BASELINE:
        recommendation_parts.append("建議：")
        recommendation_parts.append("1. 檢視 Decision V3 的風險控制參數")
        recommendation_parts.append("2. 考慮調整策略選擇邏輯")
        recommendation_parts.append("3. 分析為何 Baseline 表現較佳")
    else:  # TIE or NO_DATA
        recommendation_parts.append("建議：")
        recommendation_parts.append("1. 持續收集更多資料")
        recommendation_parts.append("2. 等待更明確的差異出現")
    
    recommendation_next_step = "\n".join(recommendation_parts[:6])
    
    return {
        "winner": winner,
        "delta_metrics": {
            "hit_rate_proxy": round(delta_metrics["hit_rate_proxy"], 4),
            "avg_return_proxy": round(delta_metrics["avg_return_proxy"], 4),
            "max_drawdown_proxy": round(delta_metrics["max_drawdown_proxy"], 4),
            "turnover_proxy": round(delta_metrics["turnover_proxy"], 4),
            "decision_consistency": round(delta_metrics["decision_consistency"], 4),
        },
        "summary": summary,
        "recommendation_next_step": recommendation_next_step,
    }

