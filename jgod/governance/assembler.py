from __future__ import annotations

from datetime import datetime
from typing import List

from jgod.api.schemas.governance_summary import GovernanceSummary, GovernanceModuleStatus
from jgod.governance.action_gate import decide_ai_action
from jgod.governance.reason_catalog import REASON_CATALOG, ReasonSpec

try:
    from jgod.research import storage as research_storage
except Exception:  # pragma: no cover
    research_storage = None


def _get_drift_status() -> GovernanceModuleStatus:
    try:
        if research_storage:
            drift_event = research_storage.latest_drift_event(symbol=None)
            if drift_event:
                level = drift_event.get("drift_level", "LOW")
                updated_at = drift_event.get("created_at") or datetime.utcnow().isoformat()
                return GovernanceModuleStatus(
                    status=str(level),
                    score=drift_event.get("drift_score"),
                    updated_at=updated_at,
                    is_stub=False,
                    reasons=[],
                )
    except Exception:
        pass
    return GovernanceModuleStatus(
        status="UNKNOWN",
        score=None,
        updated_at=datetime.utcnow().isoformat(),
        is_stub=True,
        reasons=["DRIFT_UNKNOWN"],
    )


def assemble_governance_summary() -> GovernanceSummary:
    from jgod.governance import providers

    drift = _get_drift_status()
    execution = providers.get_execution_rigor_status()
    cluster = providers.get_cluster_risk_status()
    regime, market_complexity = providers.get_market_regime_status()

    # market_complexity comes from RegimeProvider
    # If regime has a score (ER), use it to derive complexity
    if regime.score is not None:
        er = regime.score
        if er < 0.2:
            market_complexity = "HIGH"
        elif er < 0.5:
            market_complexity = "MEDIUM"
        else:
            market_complexity = "LOW"

    ai_action, gate_reasons, primary_reason_code, action_confidence, explain, recommended_ops, guardrails = decide_ai_action(
        drift_status=drift.status,
        execution=execution,
        cluster=cluster,
        regime=regime,
        market_complexity=market_complexity,
    )

    # Use catalog to derive human sentences (single wording source)
    spec: ReasonSpec = REASON_CATALOG.get(primary_reason_code) or REASON_CATALOG["UNKNOWN_REASON_CODE"]
    human_sentence = spec.human_sentence
    recommended_human_action = spec.recommended_human_action

    summary_reasons: List[str] = list({primary_reason_code, *gate_reasons} - {None})
    module_reasons: List[str] = []
    # Merge reasons from all modules (deduplicate)
    for mod in (execution, cluster, regime):
        module_reasons.extend(mod.reasons or [])
    if drift.reasons:
        module_reasons.extend(drift.reasons)
    summary_reasons = list({*summary_reasons, *module_reasons})  # Deduplicate

    if primary_reason_code not in REASON_CATALOG:
        summary_reasons.append("UNKNOWN_REASON_CODE")

    is_stub = any([drift.is_stub, execution.is_stub, cluster.is_stub, regime.is_stub]) or drift.status == "UNKNOWN"

    # enrich explain with catalog info for debug
    explain = explain or {}
    explain.setdefault("primary_reason", {
        "code": spec.reason_code,
        "title": spec.title,
        "severity": spec.severity,
    })

    # Build decision_context (P2.0 Governance Matrix)
    decision_context = {
        "type": "GOVERNANCE_MATRIX",
        "regime": regime.status,
        "cluster": cluster.status,
    }
    
    return GovernanceSummary(
        drift_status=drift.status,
        execution_confidence=execution,
        cluster_risk=cluster,
        regime=regime,
        market_complexity=market_complexity,
        ai_action=ai_action,
        updated_at=datetime.utcnow().isoformat(),
        is_stub=is_stub,
        reasons=summary_reasons,
        primary_reason_code=primary_reason_code,
        human_sentence=human_sentence,
        recommended_human_action=recommended_human_action,
        action_confidence=action_confidence,
        explain=explain,
        recommended_ops=recommended_ops,
        guardrails=guardrails,
        decision_context=decision_context,
    )


