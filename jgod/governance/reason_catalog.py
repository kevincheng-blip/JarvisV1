from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ReasonSpec:
    reason_code: str
    title: str
    human_sentence: str
    recommended_human_action: str
    severity: str  # LOW | MED | HIGH | CRITICAL
    default_ai_action: str


REASON_CATALOG: Dict[str, ReasonSpec] = {
    "REGIME_CHAOS": ReasonSpec(
        reason_code="REGIME_CHAOS",
        title="Regime is CHAOS",
        human_sentence="Market complexity is too high (Noise > Signal). Trading is dangerous.",
        recommended_human_action="Stop all AI-driven trading immediately.",
        severity="CRITICAL",
        default_ai_action="BLOCK_AI",
    ),
    "REGIME_STABLE": ReasonSpec(
        reason_code="REGIME_STABLE",
        title="Regime is Stable",
        human_sentence="Market regime is stable and predictable.",
        recommended_human_action="Normal operation allowed.",
        severity="LOW",
        default_ai_action="FULL_TRUST",
    ),
    "REGIME_CHAOS_ANY": ReasonSpec(
        reason_code="REGIME_CHAOS_ANY",
        title="Market is Chaotic",
        human_sentence="Market is chaotic. All strategies disabled.",
        recommended_human_action="Stop all AI-driven trading immediately. Wait for market to stabilize.",
        severity="CRITICAL",
        default_ai_action="BLOCK_AI",
    ),
    "COMPLEX_HIGH_CLUSTER": ReasonSpec(
        reason_code="COMPLEX_HIGH_CLUSTER",
        title="Complex Market with High Cluster Risk",
        human_sentence="Complex market with high signal consensus. Systemic failure risk.",
        recommended_human_action="Block all AI trading. Market is too complex and signals are overcrowded.",
        severity="CRITICAL",
        default_ai_action="BLOCK_AI",
    ),
    "COMPLEX_MEDIUM_CLUSTER": ReasonSpec(
        reason_code="COMPLEX_MEDIUM_CLUSTER",
        title="Complex Market with Medium Cluster Risk",
        human_sentence="Complex market. Partial exposure only.",
        recommended_human_action="Reduce exposure to 30% of normal limits. Monitor closely.",
        severity="HIGH",
        default_ai_action="REDUCE_EXPOSURE",
    ),
    "STABLE_HIGH_CLUSTER": ReasonSpec(
        reason_code="STABLE_HIGH_CLUSTER",
        title="Stable Market with High Cluster Risk",
        human_sentence="Stable trend but signals overcrowded. Use cautiously.",
        recommended_human_action="Use AI with caution. Reduce position sizing to 80% of normal limits.",
        severity="MEDIUM",
        default_ai_action="CAUTIOUS_USE",
    ),
    "STABLE_LOW_CLUSTER": ReasonSpec(
        reason_code="STABLE_LOW_CLUSTER",
        title="Stable Market with Low Cluster Risk",
        human_sentence="Stable market with diversified signals. Optimal condition.",
        recommended_human_action="Proceed with normal AI operation. All conditions are optimal.",
        severity="LOW",
        default_ai_action="FULL_TRUST",
    ),
    "REGIME_HIGH_COMPLEXITY": ReasonSpec(
        reason_code="REGIME_HIGH_COMPLEXITY",
        title="Market complexity is high",
        human_sentence="Market complexity is high — use AI cautiously.",
        recommended_human_action="De-risk positions; double-check AI outputs.",
        severity="HIGH",
        default_ai_action="CAUTIOUS_USE",
    ),
    "DRIFT_HIGH": ReasonSpec(
        reason_code="DRIFT_HIGH",
        title="Model drift is high",
        human_sentence="Model drift is high — observe only, do not execute.",
        recommended_human_action="Pause AI-driven trades; review models.",
        severity="HIGH",
        default_ai_action="OBSERVE_ONLY",
    ),
    "DRIFT_MEDIUM": ReasonSpec(
        reason_code="DRIFT_MEDIUM",
        title="Model drift is medium",
        human_sentence="Model drift is elevated — use AI with caution.",
        recommended_human_action="Use reduced size; monitor performance closely.",
        severity="MED",
        default_ai_action="CAUTIOUS_USE",
    ),
    "CLUSTER_HIGH": ReasonSpec(
        reason_code="CLUSTER_HIGH",
        title="Cluster risk is high",
        human_sentence="Cluster risk is high — reduce exposure.",
        recommended_human_action="Avoid concentration; diversify signals.",
        severity="HIGH",
        default_ai_action="REDUCE_EXPOSURE",
    ),
    "CLUSTER_MEDIUM": ReasonSpec(
        reason_code="CLUSTER_MEDIUM",
        title="Cluster risk is medium",
        human_sentence="Cluster risk is elevated — use AI cautiously.",
        recommended_human_action="Spread positions; limit new exposure.",
        severity="MED",
        default_ai_action="CAUTIOUS_USE",
    ),
    "CLUSTER_HIGH_CONSENSUS": ReasonSpec(
        reason_code="CLUSTER_HIGH_CONSENSUS",
        title="Critical Cluster Risk",
        human_sentence="Extreme signal consensus observed. Multi-strategy failure risk is high.",
        recommended_human_action="Immediately reduce exposure to 50% and manually diversify.",
        severity="CRITICAL",
        default_ai_action="REDUCE_EXPOSURE",
    ),
    "CLUSTER_MEDIUM_CONSENSUS": ReasonSpec(
        reason_code="CLUSTER_MEDIUM_CONSENSUS",
        title="Moderate Cluster Risk",
        human_sentence="Moderate signal consensus detected. Check factor exposure.",
        recommended_human_action="Reduce position sizing to 80% of normal limit.",
        severity="MEDIUM",
        default_ai_action="CAUTIOUS_USE",
    ),
    "CLUSTER_LOW": ReasonSpec(
        reason_code="CLUSTER_LOW",
        title="Cluster Risk Low",
        human_sentence="Signal independence is optimal.",
        recommended_human_action="None required; proceed with normal limits.",
        severity="LOW",
        default_ai_action="FULL_TRUST",
    ),
    "CLUSTER_NO_SIGNALS": ReasonSpec(
        reason_code="CLUSTER_NO_SIGNALS",
        title="Cluster Risk Unknown",
        human_sentence="No valid signals available to estimate cluster risk.",
        recommended_human_action="Observe only until signal inputs are available.",
        severity="MEDIUM",
        default_ai_action="OBSERVE_ONLY",
    ),
    "EXEC_LOW": ReasonSpec(
        reason_code="EXEC_LOW",
        title="Execution confidence is low",
        human_sentence="Execution confidence is low — use AI cautiously.",
        recommended_human_action="Lower size; require human review before actions.",
        severity="HIGH",
        default_ai_action="CAUTIOUS_USE",
    ),
    "EXEC_MEDIUM": ReasonSpec(
        reason_code="EXEC_MEDIUM",
        title="Execution confidence is medium",
        human_sentence="Execution confidence is medium — use AI cautiously.",
        recommended_human_action="Reduce size; monitor fills.",
        severity="MED",
        default_ai_action="CAUTIOUS_USE",
    ),
    "EXEC_NO_DATA": ReasonSpec(
        reason_code="EXEC_NO_DATA",
        title="Execution data unavailable",
        human_sentence="Execution data is unavailable — execution confidence is low.",
        recommended_human_action="Gather recent execution data before trusting AI.",
        severity="HIGH",
        default_ai_action="OBSERVE_ONLY",
    ),
    "EXEC_LOW_FILL": ReasonSpec(
        reason_code="EXEC_LOW_FILL",
        title="Execution fill rate is low",
        human_sentence="Execution fill rate is low — reduce exposure.",
        recommended_human_action="Lower size; review venue/liquidity; retry with smaller orders.",
        severity="HIGH",
        default_ai_action="CAUTIOUS_USE",
    ),
    "EXEC_HIGH_SLIPPAGE": ReasonSpec(
        reason_code="EXEC_HIGH_SLIPPAGE",
        title="Execution slippage is high",
        human_sentence="Execution slippage is high — reduce exposure.",
        recommended_human_action="Tighten limits; reduce aggression; monitor fills.",
        severity="MED",
        default_ai_action="CAUTIOUS_USE",
    ),
    "EXEC_OK": ReasonSpec(
        reason_code="EXEC_OK",
        title="Execution quality is acceptable",
        human_sentence="Execution quality is acceptable.",
        recommended_human_action="Proceed with normal sizing.",
        severity="LOW",
        default_ai_action="FULL_TRUST",
    ),
    "ALL_CLEAR": ReasonSpec(
        reason_code="ALL_CLEAR",
        title="All clear",
        human_sentence="AI outputs are allowed.",
        recommended_human_action="Proceed with AI recommendations.",
        severity="LOW",
        default_ai_action="FULL_TRUST",
    ),
    "UNKNOWN_REASON_CODE": ReasonSpec(
        reason_code="UNKNOWN_REASON_CODE",
        title="Unknown reason",
        human_sentence="Unknown governance reason — observe only.",
        recommended_human_action="Observe; investigate governance signals.",
        severity="MED",
        default_ai_action="OBSERVE_ONLY",
    ),
    "EXEC_STUB": ReasonSpec(
        reason_code="EXEC_STUB",
        title="Execution stub",
        human_sentence="Execution rigor is stubbed — use AI cautiously.",
        recommended_human_action="Treat execution outputs as provisional; review manually.",
        severity="MED",
        default_ai_action="CAUTIOUS_USE",
    ),
    "CLUSTER_STUB": ReasonSpec(
        reason_code="CLUSTER_STUB",
        title="Cluster stub",
        human_sentence="Cluster risk is stubbed — use AI cautiously.",
        recommended_human_action="Avoid over-concentration until cluster risk is live.",
        severity="MED",
        default_ai_action="CAUTIOUS_USE",
    ),
    "REGIME_STUB": ReasonSpec(
        reason_code="REGIME_STUB",
        title="Regime stub",
        human_sentence="Market regime is stubbed — use AI cautiously.",
        recommended_human_action="Wait for regime detector to be available; reduce size.",
        severity="MED",
        default_ai_action="CAUTIOUS_USE",
    ),
    "DRIFT_UNKNOWN": ReasonSpec(
        reason_code="DRIFT_UNKNOWN",
        title="Drift unknown",
        human_sentence="Model drift is unknown — observe only.",
        recommended_human_action="Observe; refresh drift signals.",
        severity="MED",
        default_ai_action="OBSERVE_ONLY",
    ),
}


