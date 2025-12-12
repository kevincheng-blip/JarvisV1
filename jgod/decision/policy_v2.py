"""Decision Layer V2 - Final Score Calculation Policy

Implements Final Score v2 calculation with S-Rank weighting, conflict adjustment, and Doctrine alert correction.
"""

import logging
from typing import List, Optional, Dict

from jgod.decision.models import DecisionContextV2, DoctrineFlag

logger = logging.getLogger(__name__)


def calculate_final_score_v2(context: DecisionContextV2) -> tuple[float, List[DoctrineFlag], str]:
    """
    Calculate Final Score v2 using S-Rank weighted strategy scores, conflict adjustment, and Doctrine alerts.
    
    Formula:
    Final Score = (
        S-Rank Weighted Strategy Average
        * Conflict Adjustment Factor
        * Doctrine Alert Correction Factor
    )
    
    Args:
        context: DecisionContextV2 with all necessary inputs
    
    Returns:
        Tuple of (final_score, doctrine_flags, adjustment_reason)
    """
    logger.debug(f"Calculating Final Score v2 for {context.symbol}")
    
    # Step 1: S-Rank Weighted Strategy Average
    weighted_score = _calculate_s_rank_weighted_average(
        context.raw_scores,
        context.s_rank_factors,
    )
    
    # Step 2: Conflict Adjustment Factor
    conflict_factor = _calculate_conflict_adjustment(context.conflict_summary)
    
    # Step 3: Doctrine Alert Correction Factor
    alert_factor, doctrine_flags = _calculate_doctrine_alert_correction(
        context.doctrine_alerts,
        context.risk_metrics,
    )
    
    # Step 4: Calculate final score
    final_score = weighted_score * conflict_factor * alert_factor
    
    # Build adjustment reason
    adjustment_reason = _build_adjustment_reason(
        weighted_score,
        conflict_factor,
        alert_factor,
        context,
    )
    
    logger.debug(
        f"Final Score v2 for {context.symbol}: {final_score:.4f} "
        f"(weighted={weighted_score:.4f}, conflict={conflict_factor:.3f}, alert={alert_factor:.3f})"
    )
    
    return final_score, doctrine_flags, adjustment_reason


def _calculate_s_rank_weighted_average(
    raw_scores: Dict[str, float],
    s_rank_factors: Optional[Dict[str, float]],
) -> float:
    """
    Calculate S-Rank weighted average of strategy scores.
    
    If S-Rank factors are available:
        weighted_avg = sum(raw_score[i] * s_rank_score[i]) / sum(s_rank_score[i])
    
    If S-Rank factors are not available, use simple average:
        weighted_avg = mean(raw_scores)
    
    Args:
        raw_scores: Dict[strategy_id, raw_score]
        s_rank_factors: Optional Dict[strategy_id, s_rank_score]
    
    Returns:
        Weighted average score
    """
    if not raw_scores:
        return 0.0
    
    # If no S-Rank factors, use simple average
    if not s_rank_factors or not s_rank_factors:
        return sum(raw_scores.values()) / len(raw_scores)
    
    # Calculate weighted average using S-Rank scores as weights
    weighted_sum = 0.0
    weight_sum = 0.0
    
    for strategy_id, raw_score in raw_scores.items():
        s_rank_score = s_rank_factors.get(strategy_id, 0.5)  # Default to 0.5 if not found
        weighted_sum += raw_score * s_rank_score
        weight_sum += s_rank_score
    
    if weight_sum > 0:
        return weighted_sum / weight_sum
    else:
        # Fallback to simple average
        return sum(raw_scores.values()) / len(raw_scores)


def _calculate_conflict_adjustment(conflict_summary: Optional[Dict[str, any]]) -> float:
    """
    Calculate conflict adjustment factor based on signal conflict scores.
    
    Formula:
        conflict_factor = 1.0 - (conflict_score / 100) * 0.3
    
    This means:
        - conflict_score = 0 (no conflict) -> factor = 1.0
        - conflict_score = 50 (moderate) -> factor = 0.85
        - conflict_score = 100 (maximum) -> factor = 0.7
    
    Args:
        conflict_summary: Optional conflict summary dict with conflict_score
    
    Returns:
        Conflict adjustment factor (0.7-1.0)
    """
    if not conflict_summary:
        return 1.0
    
    conflict_score = conflict_summary.get("conflict_score", 0.0)
    
    # Clamp conflict_score to [0, 100]
    conflict_score = max(0.0, min(100.0, conflict_score))
    
    # Calculate adjustment: reduce score by up to 30% for high conflict
    conflict_factor = 1.0 - (conflict_score / 100.0) * 0.3
    
    # Clamp to [0.7, 1.0]
    conflict_factor = max(0.7, min(1.0, conflict_factor))
    
    return conflict_factor


def _calculate_doctrine_alert_correction(
    doctrine_alerts: List[DoctrineFlag],
    risk_metrics: Dict[str, float],
) -> tuple[float, List[DoctrineFlag]]:
    """
    Calculate Doctrine alert correction factor and return filtered flags.
    
    Logic:
        - Critical alerts: reduce score by 50% (factor = 0.5)
        - Warning alerts: reduce score by 20% (factor = 0.8)
        - Info alerts: no reduction (factor = 1.0)
    
    Multiple alerts: factors are multiplied (e.g., critical + warning = 0.5 * 0.8 = 0.4)
    
    Args:
        doctrine_alerts: List of Doctrine alerts
        risk_metrics: Risk metrics dict
    
    Returns:
        Tuple of (correction_factor, filtered_flags)
    """
    if not doctrine_alerts:
        return 1.0, []
    
    correction_factor = 1.0
    filtered_flags = []
    
    for alert in doctrine_alerts:
        # Only process warning and critical alerts
        if alert.severity == "critical":
            correction_factor *= 0.5
            filtered_flags.append(alert)
        elif alert.severity == "warning":
            correction_factor *= 0.8
            filtered_flags.append(alert)
        # Info alerts don't affect score, but still include in flags
        elif alert.severity == "info":
            filtered_flags.append(alert)
    
    # Clamp correction factor to reasonable range
    correction_factor = max(0.3, min(1.0, correction_factor))
    
    return correction_factor, filtered_flags


def _build_adjustment_reason(
    weighted_score: float,
    conflict_factor: float,
    alert_factor: float,
    context: DecisionContextV2,
) -> str:
    """
    Build human-readable adjustment reason.
    
    Args:
        weighted_score: S-Rank weighted score
        conflict_factor: Conflict adjustment factor
        alert_factor: Doctrine alert correction factor
        context: Decision context
    
    Returns:
        Adjustment reason string
    """
    reasons = []
    
    # S-Rank weighting info
    if context.s_rank_factors:
        avg_s_rank = sum(context.s_rank_factors.values()) / len(context.s_rank_factors) if context.s_rank_factors else 0.5
        reasons.append(f"S-Rank weighted (avg rank: {avg_s_rank:.2f})")
    else:
        reasons.append("Simple average (no S-Rank)")
    
    # Conflict adjustment
    if conflict_factor < 1.0:
        conflict_score = context.conflict_summary.get("conflict_score", 0.0) if context.conflict_summary else 0.0
        reasons.append(f"Conflict adjusted ({conflict_score:.1f}% conflict, factor: {conflict_factor:.2f})")
    
    # Doctrine alert correction
    critical_count = sum(1 for a in context.doctrine_alerts if a.severity == "critical")
    warning_count = sum(1 for a in context.doctrine_alerts if a.severity == "warning")
    
    if critical_count > 0:
        reasons.append(f"Critical alerts: {critical_count} (factor: {alert_factor:.2f})")
    elif warning_count > 0:
        reasons.append(f"Warning alerts: {warning_count} (factor: {alert_factor:.2f})")
    
    return "; ".join(reasons) if reasons else "No adjustments"

