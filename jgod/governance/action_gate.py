from __future__ import annotations

from typing import List, Tuple, Union

from jgod.api.schemas.governance_summary import GovernanceModuleStatus


def _norm_drift(drift_status: str) -> str:
    if not drift_status:
        return "UNKNOWN"
    s = drift_status.upper()
    if s in {"LOW", "MED", "MEDIUM", "HIGH", "SEVERE"}:
        return "HIGH" if s in {"HIGH", "SEVERE"} else ("MED" if s == "MEDIUM" else s)
    return "UNKNOWN"


def decide_ai_action(
    drift_status: str,
    execution: GovernanceModuleStatus,
    cluster: GovernanceModuleStatus,
    regime: GovernanceModuleStatus,
    market_complexity: Union[str, float],
) -> Tuple[str, List[str], str, str, dict, dict, dict]:
    """
    Action Gate priority: Regime -> Drift -> Cluster -> Execution (with complexity guard).
    Returns (ai_action, reason_codes, primary_reason_code, action_confidence, explain, recommended_ops, guardrails)
    """
    reasons: List[str] = []
    explain: dict = {}
    action = "FULL_TRUST"
    primary_reason_code = "ALL_CLEAR"
    action_confidence = "MEDIUM"

    regime_status = (regime.status or "").upper()
    drift_norm = _norm_drift(drift_status)
    exec_status = (execution.status or "").upper()
    cluster_status = (cluster.status or "").upper()
    complexity = (market_complexity.upper() if isinstance(market_complexity, str) else str(market_complexity)).upper()
    drift_high = drift_norm in {"HIGH", "SEVERE"}
    cluster_high = cluster_status == "HIGH"

    # Regime (highest priority). If CHAOS/CHAOTIC -> immediate BLOCK_AI.
    if regime_status in {"CHAOS", "CHAOTIC"}:
        action = "BLOCK_AI"
        primary_reason_code = "REGIME_CHAOS"
        action_confidence = "HIGH"
        reasons.append("REGIME_CHAOS")
        explain["regime"] = regime_status
        recommended_ops = {"mode": "BLOCK_AI", "suggested_exposure_cap": 0.0, "notes": list(reasons)}
        guardrails = {
            "max_position_pct": 0.2,
            "max_turnover": 0.1,
            "allow_new_positions": False,
            "allow_leverage": False,
        }
        return (
            action,
            reasons or ["REGIME_CHAOS"],
            primary_reason_code,
            action_confidence,
            explain,
            recommended_ops,
            guardrails,
        )
    elif complexity == "HIGH":
        action = "CAUTIOUS_USE"
        primary_reason_code = "REGIME_HIGH_COMPLEXITY"
        reasons.append("REGIME_HIGH_COMPLEXITY")
        explain["market_complexity"] = complexity

    # Drift
    if drift_high:
        if action != "BLOCK_AI":
            action = "OBSERVE_ONLY"
        primary_reason_code = "DRIFT_HIGH"
        reasons.append("DRIFT_HIGH")
        explain["drift_status"] = drift_norm
    elif drift_norm in {"MED", "MEDIUM"} and action == "FULL_TRUST":
        primary_reason_code = "DRIFT_MEDIUM"
        reasons.append("DRIFT_MEDIUM")

    # Cluster
    if cluster_high:
        if action not in {"BLOCK_AI", "OBSERVE_ONLY"}:
            action = "REDUCE_EXPOSURE"
            primary_reason_code = "CLUSTER_HIGH"
        reasons.append("CLUSTER_HIGH")
        explain["cluster_risk"] = cluster_status
    elif cluster_status == "MEDIUM":
        reasons.append("CLUSTER_MEDIUM")

    # Execution
    if exec_status == "LOW":
        if action not in {"BLOCK_AI", "OBSERVE_ONLY"}:
            action = "CAUTIOUS_USE"
            primary_reason_code = "EXEC_LOW" if primary_reason_code == "ALL_CLEAR" else primary_reason_code
        reasons.append("EXEC_LOW")
        explain["execution_confidence"] = exec_status
    elif exec_status == "MEDIUM":
        if action == "FULL_TRUST":
            action = "CAUTIOUS_USE"
            primary_reason_code = "EXEC_MEDIUM"
        reasons.append("EXEC_MEDIUM")

    if not reasons:
        reasons.append("ALL_CLEAR")
        primary_reason_code = "ALL_CLEAR"

    # Escalation: if both drift and cluster are high, block AI.
    if drift_high and cluster_high:
        action = "BLOCK_AI"
        primary_reason_code = "DRIFT_HIGH"
        if "DRIFT_HIGH" not in reasons:
            reasons.append("DRIFT_HIGH")
        if "CLUSTER_HIGH" not in reasons:
            reasons.append("CLUSTER_HIGH")

    # Machine-readable ops mapping (must align with ai_action 1:1)
    if action == "BLOCK_AI":
        recommended_ops = {"mode": "BLOCK_AI", "suggested_exposure_cap": 0.0, "notes": list(reasons)}
    elif action == "OBSERVE_ONLY":
        recommended_ops = {"mode": "OBSERVE_ONLY", "suggested_exposure_cap": 0.1, "notes": list(reasons)}
    elif action == "REDUCE_EXPOSURE":
        recommended_ops = {"mode": "REDUCE_EXPOSURE", "suggested_exposure_cap": 0.5, "notes": list(reasons)}
    elif action == "CAUTIOUS_USE":
        recommended_ops = {"mode": "CAUTIOUS_USE", "suggested_exposure_cap": 0.8, "notes": list(reasons)}
    else:
        recommended_ops = {"mode": "FULL_TRUST", "suggested_exposure_cap": 1.0, "notes": list(reasons)}

    # Execution guard: if execution confidence is LOW, cap exposure to 0.3 (but do not escalate ai_action)
    if exec_status == "LOW":
        cap = recommended_ops.get("suggested_exposure_cap")
        if isinstance(cap, (int, float)):
            recommended_ops["suggested_exposure_cap"] = min(cap, 0.3)
        else:
            recommended_ops["suggested_exposure_cap"] = 0.3

    guardrails = {
        "max_position_pct": 0.2,
        "max_turnover": 0.1,
        "allow_new_positions": action not in {"BLOCK_AI", "OBSERVE_ONLY"},
        "allow_leverage": False,
    }

    return (
        action,
        reasons,
        primary_reason_code,
        action_confidence,
        explain,
        recommended_ops,
        guardrails,
    )


