"""
Decision V3 Arena: Multi-Challenger Comparison + Auto-Tuning

This module implements a champion-challenger arena system that compares
Decision V3 against multiple baselines and variants, with auto-tuning
capabilities for risk mapping and composite weights.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Literal, Optional, Tuple
from datetime import datetime
import json

from jgod.decision_v3.models import DecisionV3Result, RiskPlan, StrategyWeight
from jgod.decision_v3.engine import DecisionEngineV3
from jgod.decision_v3.evaluation import evaluate_decision_v3, TimelineItem


ChallengerId = Literal["V3", "RISK_OFF", "MOMENTUM", "EQUAL_WEIGHT", "V3_VARIANT"]


@dataclass
class ChallengerScore:
    """Score for a single challenger in the arena."""
    challenger_id: str
    composite_score: float
    metrics: Dict[str, float] = field(default_factory=dict)
    pareto_dominated: bool = False


@dataclass
class VariantConfig:
    """Configuration for a V3 variant."""
    risk_mapping: Dict[str, float]  # STABLE/WATCH/VOLATILE -> position_scale
    composite_weights: Dict[str, float]  # avg_return, max_drawdown, hit_rate, turnover, consistency


@dataclass
class AutoTuningResult:
    """Result of auto-tuning grid search."""
    best_config: Optional[VariantConfig] = None
    top_variants: List[Tuple[VariantConfig, float]] = field(default_factory=list)
    notes: str = ""


@dataclass
class ArenaResult:
    """Complete arena comparison result."""
    symbol: str
    created_at: str
    mode: str
    window: int
    limit: int
    k: int
    scoreboard: List[ChallengerScore] = field(default_factory=list)
    winner_id: str = "NO_DATA"
    is_regression: bool = False
    auto_tuning: Optional[AutoTuningResult] = None
    summary: str = ""
    recommendation_next_step: str = ""


def _build_risk_off_decision(symbol: str, mode: str, limit: int, k: int) -> DecisionV3Result:
    """Build RISK_OFF baseline decision."""
    return DecisionV3Result(
        symbol=symbol,
        as_of_date=None,
        selected_primary_strategy="risk_off",
        selected_secondary_strategies=[],
        weights=[
            StrategyWeight(strategy_id="risk_off", weight=1.0)
        ],
        risk_plan=RiskPlan(
            position_scale=0.20,
            risk_state="RISK_OFF",
            reasons=["Baseline: RISK_OFF mode"]
        ),
        confidence=0.30,
        explain="RISK_OFF baseline: 固定風險規避模式，position_scale=0.20"
    )


def _build_momentum_decision(symbol: str, mode: str, limit: int, k: int) -> DecisionV3Result:
    """Build MOMENTUM baseline decision."""
    return DecisionV3Result(
        symbol=symbol,
        as_of_date=None,
        selected_primary_strategy="momentum",
        selected_secondary_strategies=["trend_follow"],
        weights=[
            StrategyWeight(strategy_id="momentum", weight=0.60),
            StrategyWeight(strategy_id="trend_follow", weight=0.25),
            StrategyWeight(strategy_id="risk_off", weight=0.15)
        ],
        risk_plan=RiskPlan(
            position_scale=0.50,
            risk_state="CAUTION",
            reasons=["Baseline: MOMENTUM mode"]
        ),
        confidence=0.50,
        explain="MOMENTUM baseline: 固定動量策略，position_scale=0.50"
    )


def _build_equal_weight_decision(symbol: str, mode: str, limit: int, k: int) -> DecisionV3Result:
    """Build EQUAL_WEIGHT baseline decision."""
    strategies = ["trend_follow", "mean_reversion", "breakout", "momentum", "risk_off"]
    weight = 1.0 / len(strategies)
    return DecisionV3Result(
        symbol=symbol,
        as_of_date=None,
        selected_primary_strategy="equal_weight",
        selected_secondary_strategies=strategies[1:],
        weights=[
            StrategyWeight(strategy_id=s, weight=weight) for s in strategies
        ],
        risk_plan=RiskPlan(
            position_scale=0.50,
            risk_state="CAUTION",
            reasons=["Baseline: EQUAL_WEIGHT mode"]
        ),
        confidence=0.40,
        explain="EQUAL_WEIGHT baseline: 均等權重策略，position_scale=0.50"
    )


def _build_v3_variant_decision(
    symbol: str,
    mode: str,
    limit: int,
    k: int,
    variant_config: VariantConfig
) -> DecisionV3Result:
    """Build V3 variant decision with custom risk mapping."""
    # Get base V3 decision (local import to avoid circular dependency)
    from jgod.decision_v3.service import compute_decision
    base_result = compute_decision(symbol, mode, limit, k)
    
    # Override risk mapping based on stability grade
    from jgod.observer.prediction_stability import compute_stability_metrics
    from jgod.decision_v3.service import _fetch_timeline_items
    
    timeline_items = _fetch_timeline_items(symbol, limit)
    if len(timeline_items) < 5:
        return base_result
    
    stability = compute_stability_metrics([{"date": item["date"], "final_score": item["final_score"]} for item in timeline_items])
    stability_grade = stability.get("stability_grade", "NO_DATA")
    
    # Apply variant risk mapping
    position_scale = variant_config.risk_mapping.get(stability_grade, base_result.risk_plan.position_scale)
    
    # Clamp position_scale
    position_scale = max(0.05, min(1.0, position_scale))
    
    # Determine risk_state
    if position_scale <= 0.25:
        risk_state = "RISK_OFF"
    elif position_scale <= 0.55:
        risk_state = "CAUTION"
    else:
        risk_state = "RISK_ON"
    
    # Create new risk plan
    new_risk_plan = RiskPlan(
        position_scale=position_scale,
        risk_state=risk_state,
        reasons=base_result.risk_plan.reasons + [f"Variant: {stability_grade} -> {position_scale:.2f}"]
    )
    
    return DecisionV3Result(
        symbol=base_result.symbol,
        as_of_date=base_result.as_of_date,
        selected_primary_strategy=base_result.selected_primary_strategy,
        selected_secondary_strategies=base_result.selected_secondary_strategies,
        weights=base_result.weights,
        risk_plan=new_risk_plan,
        confidence=base_result.confidence,
        explain=f"V3 Variant: {base_result.explain} [Risk mapping: {stability_grade} -> {position_scale:.2f}]"
    )


def _compute_composite_score(metrics: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> float:
    """Compute composite score from metrics."""
    if weights is None:
        weights = {
            "avg_return_proxy": 1.0,
            "max_drawdown_proxy": -0.9,
            "hit_rate_proxy": 0.15,
            "turnover_proxy": -0.12,
            "decision_consistency": 0.08
        }
    
    score = (
        metrics.get("avg_return_proxy", 0.0) * weights.get("avg_return_proxy", 1.0) +
        metrics.get("max_drawdown_proxy", 0.0) * weights.get("max_drawdown_proxy", -0.9) +
        metrics.get("hit_rate_proxy", 0.0) * weights.get("hit_rate_proxy", 0.15) +
        metrics.get("turnover_proxy", 0.0) * weights.get("turnover_proxy", -0.12) +
        metrics.get("decision_consistency", 0.0) * weights.get("decision_consistency", 0.08)
    )
    
    return round(score, 6)


def _check_pareto_dominated(
    challenger_metrics: Dict[str, float],
    other_metrics: Dict[str, float]
) -> bool:
    """Check if challenger is Pareto dominated by other."""
    # For (avg_return↑, max_drawdown↓, turnover↓), challenger is dominated if:
    # other has >= avg_return AND <= max_drawdown AND <= turnover
    # AND at least one is strictly better
    
    avg_return_ok = other_metrics.get("avg_return_proxy", 0.0) >= challenger_metrics.get("avg_return_proxy", 0.0)
    mdd_ok = other_metrics.get("max_drawdown_proxy", 1.0) <= challenger_metrics.get("max_drawdown_proxy", 1.0)
    turnover_ok = other_metrics.get("turnover_proxy", 1.0) <= challenger_metrics.get("turnover_proxy", 1.0)
    
    if not (avg_return_ok and mdd_ok and turnover_ok):
        return False
    
    # At least one must be strictly better
    better_return = other_metrics.get("avg_return_proxy", 0.0) > challenger_metrics.get("avg_return_proxy", 0.0)
    better_mdd = other_metrics.get("max_drawdown_proxy", 1.0) < challenger_metrics.get("max_drawdown_proxy", 1.0)
    better_turnover = other_metrics.get("turnover_proxy", 1.0) < challenger_metrics.get("turnover_proxy", 1.0)
    
    return better_return or better_mdd or better_turnover


def _run_auto_tuning(
    symbol: str,
    mode: str,
    limit: int,
    k: int,
    timeline_items: List[TimelineItem]
) -> AutoTuningResult:
    """Run grid search for V3 variant optimization."""
    # Risk mapping candidates
    risk_mapping_candidates = [
        {"STABLE": 0.70, "WATCH": 0.45, "VOLATILE": 0.25, "NO_DATA": 0.20},
        {"STABLE": 0.80, "WATCH": 0.55, "VOLATILE": 0.35, "NO_DATA": 0.20},
        {"STABLE": 0.90, "WATCH": 0.65, "VOLATILE": 0.45, "NO_DATA": 0.20},
    ]
    
    # Composite weight candidates (simplified: only 3 key combinations)
    weight_candidates = [
        {"avg_return_proxy": 1.0, "max_drawdown_proxy": -0.9, "hit_rate_proxy": 0.15, "turnover_proxy": -0.12, "decision_consistency": 0.08},
        {"avg_return_proxy": 1.1, "max_drawdown_proxy": -1.0, "hit_rate_proxy": 0.20, "turnover_proxy": -0.10, "decision_consistency": 0.10},
        {"avg_return_proxy": 0.9, "max_drawdown_proxy": -0.8, "hit_rate_proxy": 0.10, "turnover_proxy": -0.15, "decision_consistency": 0.05},
    ]
    
    variant_scores: List[Tuple[VariantConfig, float]] = []
    
    # Grid search (limited to 3x3 = 9 combinations for performance)
    for risk_mapping in risk_mapping_candidates:
        for weights in weight_candidates:
            variant_config = VariantConfig(
                risk_mapping=risk_mapping,
                composite_weights=weights
            )
            
            # Build variant decision
            variant_decision = _build_v3_variant_decision(symbol, mode, limit, k, variant_config)
            
            # Evaluate variant
            eval_result = evaluate_decision_v3(
                timeline_items,
                _result_to_dict(variant_decision),
                window=20
            )
            
            if eval_result.get("n_points", 0) < 10:
                continue
            
            # Compute composite score with variant weights
            composite_score = _compute_composite_score(eval_result, weights)
            
            variant_scores.append((variant_config, composite_score))
    
    if not variant_scores:
        return AutoTuningResult(
            notes="自動調參：資料不足，無法產生有效變體"
        )
    
    # Sort by score descending
    variant_scores.sort(key=lambda x: x[1], reverse=True)
    
    best_config, best_score = variant_scores[0]
    top_variants = variant_scores[:5]
    
    # Generate notes
    notes_parts = []
    if best_score > 0.05:
        notes_parts.append(f"最佳變體分數：{best_score:.4f}")
        notes_parts.append(f"風險映射：STABLE={best_config.risk_mapping.get('STABLE', 0):.2f}, WATCH={best_config.risk_mapping.get('WATCH', 0):.2f}, VOLATILE={best_config.risk_mapping.get('VOLATILE', 0):.2f}")
        if best_score > 0.10:
            notes_parts.append("建議：可考慮更新風險映射參數")
    else:
        notes_parts.append("自動調參：當前 V3 配置已接近最優，無需大幅調整")
    
    return AutoTuningResult(
        best_config=best_config,
        top_variants=top_variants,
        notes="\n".join(notes_parts)
    )


def _result_to_dict(result: DecisionV3Result) -> Dict:
    """Convert DecisionV3Result to dict for evaluation."""
    return {
        "symbol": result.symbol,
        "selected_primary_strategy": result.selected_primary_strategy,
        "selected_secondary_strategies": result.selected_secondary_strategies,
        "risk_plan": {
            "position_scale": result.risk_plan.position_scale,
            "risk_state": result.risk_plan.risk_state,
            "reasons": result.risk_plan.reasons
        },
        "confidence": result.confidence,
        "weights": [
            {"strategy_id": w.strategy_id, "weight": w.weight}
            for w in result.weights
        ]
    }


def compute_arena(
    symbol: str,
    mode: str = "performance",
    limit: int = 60,
    k: int = 5,
    window: int = 20
) -> ArenaResult:
    """Compute arena comparison for a symbol."""
    # Fetch timeline (local import to avoid circular dependency)
    from jgod.decision_v3.service import _fetch_timeline_items, compute_decision
    timeline_items = _fetch_timeline_items(symbol, limit)
    
    if len(timeline_items) < 10:
        return ArenaResult(
            symbol=symbol,
            created_at=datetime.now().isoformat(),
            mode=mode,
            window=window,
            limit=limit,
            k=k,
            winner_id="NO_DATA",
            summary="資料不足，無法進行競技場對照",
            recommendation_next_step="請確保至少有 10 筆預測資料"
        )
    
    scoreboard: List[ChallengerScore] = []
    
    # 1. V3 (Champion)
    v3_decision = compute_decision(symbol, mode, limit, k)  # compute_decision imported above
    v3_eval = evaluate_decision_v3(timeline_items, _result_to_dict(v3_decision), window)
    if v3_eval.get("n_points", 0) >= 10:
        v3_score = _compute_composite_score(v3_eval)
        scoreboard.append(ChallengerScore(
            challenger_id="V3",
            composite_score=v3_score,
            metrics={
                "hit_rate_proxy": v3_eval.get("hit_rate_proxy", 0.0),
                "avg_return_proxy": v3_eval.get("avg_return_proxy", 0.0),
                "max_drawdown_proxy": v3_eval.get("max_drawdown_proxy", 0.0),
                "turnover_proxy": v3_eval.get("turnover_proxy", 0.0),
                "decision_consistency": v3_eval.get("decision_consistency", 0.0)
            }
        ))
    
    # 2. RISK_OFF baseline
    risk_off_decision = _build_risk_off_decision(symbol, mode, limit, k)
    risk_off_eval = evaluate_decision_v3(timeline_items, _result_to_dict(risk_off_decision), window)
    if risk_off_eval.get("n_points", 0) >= 10:
        risk_off_score = _compute_composite_score(risk_off_eval)
        scoreboard.append(ChallengerScore(
            challenger_id="RISK_OFF",
            composite_score=risk_off_score,
            metrics={
                "hit_rate_proxy": risk_off_eval.get("hit_rate_proxy", 0.0),
                "avg_return_proxy": risk_off_eval.get("avg_return_proxy", 0.0),
                "max_drawdown_proxy": risk_off_eval.get("max_drawdown_proxy", 0.0),
                "turnover_proxy": risk_off_eval.get("turnover_proxy", 0.0),
                "decision_consistency": risk_off_eval.get("decision_consistency", 0.0)
            }
        ))
    
    # 3. MOMENTUM baseline
    momentum_decision = _build_momentum_decision(symbol, mode, limit, k)
    momentum_eval = evaluate_decision_v3(timeline_items, _result_to_dict(momentum_decision), window)
    if momentum_eval.get("n_points", 0) >= 10:
        momentum_score = _compute_composite_score(momentum_eval)
        scoreboard.append(ChallengerScore(
            challenger_id="MOMENTUM",
            composite_score=momentum_score,
            metrics={
                "hit_rate_proxy": momentum_eval.get("hit_rate_proxy", 0.0),
                "avg_return_proxy": momentum_eval.get("avg_return_proxy", 0.0),
                "max_drawdown_proxy": momentum_eval.get("max_drawdown_proxy", 0.0),
                "turnover_proxy": momentum_eval.get("turnover_proxy", 0.0),
                "decision_consistency": momentum_eval.get("decision_consistency", 0.0)
            }
        ))
    
    # 4. EQUAL_WEIGHT baseline
    equal_weight_decision = _build_equal_weight_decision(symbol, mode, limit, k)
    equal_weight_eval = evaluate_decision_v3(timeline_items, _result_to_dict(equal_weight_decision), window)
    if equal_weight_eval.get("n_points", 0) >= 10:
        equal_weight_score = _compute_composite_score(equal_weight_eval)
        scoreboard.append(ChallengerScore(
            challenger_id="EQUAL_WEIGHT",
            composite_score=equal_weight_score,
            metrics={
                "hit_rate_proxy": equal_weight_eval.get("hit_rate_proxy", 0.0),
                "avg_return_proxy": equal_weight_eval.get("avg_return_proxy", 0.0),
                "max_drawdown_proxy": equal_weight_eval.get("max_drawdown_proxy", 0.0),
                "turnover_proxy": equal_weight_eval.get("turnover_proxy", 0.0),
                "decision_consistency": equal_weight_eval.get("decision_consistency", 0.0)
            }
        ))
    
    if not scoreboard:
        return ArenaResult(
            symbol=symbol,
            created_at=datetime.now().isoformat(),
            mode=mode,
            window=window,
            limit=limit,
            k=k,
            winner_id="NO_DATA",
            summary="所有挑戰者評估失敗，無法產生有效分數",
            recommendation_next_step="請檢查預測資料品質"
        )
    
    # Check Pareto dominance
    for i, challenger in enumerate(scoreboard):
        for j, other in enumerate(scoreboard):
            if i != j:
                if _check_pareto_dominated(challenger.metrics, other.metrics):
                    challenger.pareto_dominated = True
                    # Penalize dominated challengers
                    challenger.composite_score *= 0.95
    
    # Sort by composite score (descending)
    scoreboard.sort(key=lambda x: x.composite_score, reverse=True)
    
    # Determine winner
    winner = scoreboard[0]
    winner_id = winner.challenger_id
    
    # Check regression
    v3_score = next((s.composite_score for s in scoreboard if s.challenger_id == "V3"), None)
    is_regression = False
    if v3_score is not None and winner_id != "V3":
        score_diff = winner.composite_score - v3_score
        if score_diff >= 0.03:  # Threshold
            is_regression = True
    
    # Run auto-tuning
    auto_tuning = _run_auto_tuning(symbol, mode, limit, k, timeline_items)
    
    # Generate summary
    summary_parts = []
    summary_parts.append(f"競技場對照結果：{winner_id} 勝出（分數：{winner.composite_score:.4f}）")
    if is_regression:
        summary_parts.append(f"⚠️ 回歸警報：{winner_id} 超越 V3 達 {score_diff:.4f}，建議檢視 V3 配置")
    summary_parts.append(f"參與挑戰者：{len(scoreboard)} 個")
    if any(s.pareto_dominated for s in scoreboard):
        dominated_count = sum(1 for s in scoreboard if s.pareto_dominated)
        summary_parts.append(f"Pareto 支配：{dominated_count} 個挑戰者被支配")
    
    # Generate recommendation
    rec_parts = []
    if is_regression:
        rec_parts.append(f"建議：檢視 {winner_id} 的策略配置，考慮調整 V3 參數")
    elif winner_id == "V3":
        rec_parts.append("V3 維持冠軍地位，建議持續監控")
    if auto_tuning.best_config and auto_tuning.top_variants:
        best_score = auto_tuning.top_variants[0][1]
        if best_score > (v3_score or 0) + 0.02:
            rec_parts.append("自動調參發現更優配置，可考慮更新風險映射")
    
    return ArenaResult(
        symbol=symbol,
        created_at=datetime.now().isoformat(),
        mode=mode,
        window=window,
        limit=limit,
        k=k,
        scoreboard=scoreboard,
        winner_id=winner_id,
        is_regression=is_regression,
        auto_tuning=auto_tuning,
        summary="\n".join(summary_parts),
        recommendation_next_step="\n".join(rec_parts) if rec_parts else "持續監控競技場表現"
    )

