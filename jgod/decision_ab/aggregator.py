"""Decision AB Test Aggregator

Computes delta metrics and aggregates AB test results.
"""

from jgod.decision_ab.models import DecisionAbResult, ArmResult


def compute_delta_metrics(raw_only: ArmResult, decision_on: ArmResult) -> dict:
    """Compute delta metrics between RAW_ONLY and DECISION_ON arms
    
    Args:
        raw_only: RAW_ONLY arm results
        decision_on: DECISION_ON arm results
    
    Returns:
        Dictionary with delta_* fields
    """
    return {
        "delta_sharpe": decision_on.metrics.sharpe - raw_only.metrics.sharpe,
        "delta_max_drawdown": decision_on.metrics.max_drawdown - raw_only.metrics.max_drawdown,
        "delta_total_return": decision_on.metrics.total_return - raw_only.metrics.total_return,
        "delta_win_rate": decision_on.metrics.win_rate - raw_only.metrics.win_rate,
        "delta_turnover": decision_on.metrics.turnover - raw_only.metrics.turnover,
    }


def create_ab_result(
    experiment_id: str,
    raw_only: ArmResult,
    decision_on: ArmResult,
) -> DecisionAbResult:
    """Create a DecisionAbResult with computed delta metrics
    
    Args:
        experiment_id: Experiment identifier
        raw_only: RAW_ONLY arm results
        decision_on: DECISION_ON arm results
    
    Returns:
        DecisionAbResult with delta metrics computed
    """
    from datetime import datetime
    
    deltas = compute_delta_metrics(raw_only, decision_on)
    
    return DecisionAbResult(
        experiment_id=experiment_id,
        created_at=datetime.now(),
        raw_only=raw_only,
        decision_on=decision_on,
        **deltas
    )

