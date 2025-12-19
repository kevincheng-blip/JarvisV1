from __future__ import annotations

from typing import List, Tuple, Union, Optional

from jgod.api.schemas.governance_summary import GovernanceModuleStatus


def _norm_drift(drift_status: str) -> str:
    if not drift_status:
        return "UNKNOWN"
    s = drift_status.upper()
    if s in {"LOW", "MED", "MEDIUM", "HIGH", "SEVERE"}:
        return "HIGH" if s in {"HIGH", "SEVERE"} else ("MED" if s == "MEDIUM" else s)
    return "UNKNOWN"


def _governance_matrix_decision(
    regime_status: str,
    cluster_status: str,
) -> Optional[Tuple[str, str, float]]:
    """
    Governance Matrix Decision (P2.0).
    
    Matrix:
        Regime \ Cluster    HIGH        MEDIUM      LOW
        CHAOS               BLOCK_AI    BLOCK_AI    BLOCK_AI
        COMPLEX             BLOCK_AI    REDUCE_30%  OBSERVE_ONLY
        STABLE              CAUTIOUS   CAUTIOUS    FULL_TRUST
    
    Args:
        regime_status: Regime status (CHAOS, COMPLEX, STABLE)
        cluster_status: Cluster status (HIGH, MEDIUM, LOW)
    
    Returns:
        Tuple of (ai_action, reason_code, exposure_cap)
    """
    regime_upper = regime_status.upper()
    cluster_upper = cluster_status.upper()
    
    # CHAOS × ANY → BLOCK_AI (highest priority)
    if regime_upper == "CHAOS":
        return ("BLOCK_AI", "REGIME_CHAOS_ANY", 0.0)
    
    # COMPLEX × HIGH → BLOCK_AI
    if regime_upper == "COMPLEX" and cluster_upper == "HIGH":
        return ("BLOCK_AI", "COMPLEX_HIGH_CLUSTER", 0.0)
    
    # COMPLEX × MEDIUM → REDUCE_EXPOSURE (30%)
    if regime_upper == "COMPLEX" and cluster_upper == "MEDIUM":
        return ("REDUCE_EXPOSURE", "COMPLEX_MEDIUM_CLUSTER", 0.3)
    
    # COMPLEX × LOW → OBSERVE_ONLY
    if regime_upper == "COMPLEX" and cluster_upper == "LOW":
        return ("OBSERVE_ONLY", "COMPLEX_MEDIUM_CLUSTER", 0.1)  # Use existing reason code for simplicity
    
    # Fallback: if regime/cluster not in matrix, return None to use legacy logic
    if regime_upper not in {"CHAOS", "COMPLEX", "STABLE"} or cluster_upper not in {"HIGH", "MEDIUM", "LOW"}:
        return None
    
    # STABLE × HIGH → CAUTIOUS_USE
    if regime_upper == "STABLE" and cluster_upper == "HIGH":
        return ("CAUTIOUS_USE", "STABLE_HIGH_CLUSTER", 0.8)
    
    # STABLE × MEDIUM → CAUTIOUS_USE
    if regime_upper == "STABLE" and cluster_upper == "MEDIUM":
        return ("CAUTIOUS_USE", "STABLE_HIGH_CLUSTER", 0.8)  # Use same as HIGH for simplicity
    
    # STABLE × LOW → FULL_TRUST
    if regime_upper == "STABLE" and cluster_upper == "LOW":
        return ("FULL_TRUST", "STABLE_LOW_CLUSTER", 1.0)
    
    # Fallback (should not happen with valid inputs)
    return ("OBSERVE_ONLY", "UNKNOWN_REASON_CODE", 0.1)


def decide_ai_action(
    drift_status: str,
    execution: GovernanceModuleStatus,
    cluster: GovernanceModuleStatus,
    regime: GovernanceModuleStatus,
    market_complexity: Union[str, float],
) -> Tuple[str, List[str], str, str, dict, dict, dict]:
    """
    Action Gate with Governance Matrix (P2.0).
    
    Priority:
    1. CHAOS regime (always BLOCK_AI)
    2. Governance Matrix (Regime × Cluster)
    3. Drift (if not blocked by matrix)
    4. Execution (guard only, does not override matrix)
    
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

    # Step 1: CHAOS check (highest priority)
    if regime_status == "CHAOS":
        action = "BLOCK_AI"
        primary_reason_code = "REGIME_CHAOS_ANY"
        action_confidence = "HIGH"
        reasons.append("REGIME_CHAOS_ANY")
        explain["regime"] = regime_status
        explain["cluster_risk"] = cluster_status
        recommended_ops = {"mode": "BLOCK_AI", "suggested_exposure_cap": 0.0, "notes": list(reasons)}
        guardrails = {
            "max_position_pct": 0.2,
            "max_turnover": 0.1,
            "allow_new_positions": False,
            "allow_leverage": False,
        }
        return (
            action,
            reasons or ["REGIME_CHAOS_ANY"],
            primary_reason_code,
            action_confidence,
            explain,
            recommended_ops,
            guardrails,
        )
    
    # Step 2: Governance Matrix Decision
    matrix_result = _governance_matrix_decision(
        regime_status=regime_status,
        cluster_status=cluster_status,
    )
    
    matrix_exposure = 0.8  # Default exposure cap
    
    if matrix_result is not None:
        # Use matrix decision
        matrix_action, matrix_reason, matrix_exposure = matrix_result
        action = matrix_action
        primary_reason_code = matrix_reason
        reasons.append(matrix_reason)
        explain["regime"] = regime_status
        explain["cluster_risk"] = cluster_status
        explain["matrix_decision"] = {
            "regime": regime_status,
            "cluster": cluster_status,
            "action": matrix_action,
        }
    else:
        # Fallback to legacy logic if regime/cluster not in matrix
        # This handles edge cases like UNKNOWN regime or invalid cluster status
        explain["regime"] = regime_status
        explain["cluster_risk"] = cluster_status
        
        # Legacy cluster logic (for non-matrix cases)
        cluster_high = cluster_status == "HIGH"
        if cluster_high:
            if action not in {"BLOCK_AI", "OBSERVE_ONLY"}:
                action = "REDUCE_EXPOSURE"
                primary_reason_code = "CLUSTER_HIGH_CONSENSUS"
            reasons.append("CLUSTER_HIGH_CONSENSUS")
        elif cluster_status == "MEDIUM":
            if action not in {"BLOCK_AI", "OBSERVE_ONLY", "REDUCE_EXPOSURE"}:
                action = "CAUTIOUS_USE"
                if primary_reason_code == "ALL_CLEAR":
                    primary_reason_code = "CLUSTER_MEDIUM_CONSENSUS"
            reasons.append("CLUSTER_MEDIUM_CONSENSUS")
        elif cluster_status == "LOW":
            reasons.append("CLUSTER_LOW")

    # Step 3: Drift override (only if not already BLOCK_AI)
    if drift_high and action != "BLOCK_AI":
        action = "OBSERVE_ONLY"
        primary_reason_code = "DRIFT_HIGH"
        if "DRIFT_HIGH" not in reasons:
            reasons.append("DRIFT_HIGH")
        explain["drift_status"] = drift_norm
    elif drift_norm in {"MED", "MEDIUM"}:
        if "DRIFT_MEDIUM" not in reasons:
            reasons.append("DRIFT_MEDIUM")
        explain["drift_status"] = drift_norm
    
    # Step 4: Execution guard (does not override action, only caps exposure)
    if exec_status == "LOW":
        if "EXEC_LOW" not in reasons:
            reasons.append("EXEC_LOW")
        explain["execution_confidence"] = exec_status
    elif exec_status == "MEDIUM":
        if "EXEC_MEDIUM" not in reasons:
            reasons.append("EXEC_MEDIUM")
    
    if not reasons:
        reasons.append("ALL_CLEAR")
        primary_reason_code = "ALL_CLEAR"
    
    # Machine-readable ops mapping
    if action == "BLOCK_AI":
        recommended_ops = {"mode": "BLOCK_AI", "suggested_exposure_cap": 0.0, "notes": list(reasons)}
    elif action == "OBSERVE_ONLY":
        recommended_ops = {"mode": "OBSERVE_ONLY", "suggested_exposure_cap": 0.1, "notes": list(reasons)}
    elif action == "REDUCE_EXPOSURE":
        # Use matrix exposure cap (or default 0.5 for legacy)
        recommended_ops = {"mode": "REDUCE_EXPOSURE", "suggested_exposure_cap": matrix_exposure if matrix_result else 0.5, "notes": list(reasons)}
    elif action == "CAUTIOUS_USE":
        # Use matrix exposure cap (or default 0.8 for legacy)
        recommended_ops = {"mode": "CAUTIOUS_USE", "suggested_exposure_cap": matrix_exposure if matrix_result else 0.8, "notes": list(reasons)}
    else:
        recommended_ops = {"mode": "FULL_TRUST", "suggested_exposure_cap": 1.0, "notes": list(reasons)}
    
    # Execution guard: cap exposure if execution is LOW (but don't override action)
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


