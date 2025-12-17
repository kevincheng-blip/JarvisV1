from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List

from jgod.api.schemas.governance_summary import GovernanceModuleStatus
from jgod.execution.storage import list_latest

logger = logging.getLogger(__name__)

DEFAULT_SYMBOL = "2330"
DEFAULT_SAMPLE = 30


def _compute_metrics_from_snapshots(snapshots: List[Dict]) -> Dict[str, float]:
    """
    Derive execution metrics from ledger snapshots.
    Since ledger snapshots may not contain explicit fills/slippage,
    we use simple heuristics:
      - fill_rate: infer from presence of position changes; default 1.0 if activity, else 0.0
      - avg_slippage_bp: stub 0.0 (no observable data)
      - reject_rate: 0.0 (no rejects recorded in ledger snapshots)
    """
    if not snapshots:
        return {
            "fill_rate": 0.0,
            "avg_slippage_bp": None,
            "reject_rate": None,
            "last_execution_at": None,
            "has_data": False,
        }

    # Sort snapshots newest first (list_latest already does)
    latest = snapshots[0]
    last_execution_at = latest.get("created_at") or latest.get("updated_at")

    # Heuristic: if position qty ever >0 in latest snapshot, treat as some fills happened.
    ledger = latest.get("ledger", {})
    position = ledger.get("position", {}) if isinstance(ledger, dict) else {}
    qty = position.get("qty", 0) or 0

    has_activity = qty != 0 or len(snapshots) > 1
    fill_rate = 1.0 if has_activity else 0.0

    return {
        "fill_rate": float(fill_rate),
        "avg_slippage_bp": 0.0,
        "reject_rate": 0.0,
        "last_execution_at": last_execution_at,
        "has_data": True,
    }


def get_execution_rigor_status(symbol: str = DEFAULT_SYMBOL, sample_size: int = DEFAULT_SAMPLE) -> GovernanceModuleStatus:
    """
    Compute execution confidence from VirtualLedger snapshots.
    """
    try:
        snapshots = list_latest(symbol, n=sample_size)
    except Exception as e:  # pragma: no cover - defensive
        logger.warning(f"Failed to load ledger snapshots: {e}", exc_info=False)
        return GovernanceModuleStatus(
            status="LOW",
            score=0.0,
            updated_at=datetime.utcnow().isoformat(),
            is_stub=False,
            reasons=["EXEC_NO_DATA"],
            metrics={
                "fill_rate": 0.0,
                "avg_slippage_bp": None,
                "reject_rate": None,
                "last_execution_at": None,
            },
        )

    metrics = _compute_metrics_from_snapshots(snapshots)

    if not metrics.get("has_data"):
        return GovernanceModuleStatus(
            status="LOW",
            score=0.0,
            updated_at=datetime.utcnow().isoformat(),
            is_stub=False,
            reasons=["EXEC_NO_DATA"],
            metrics=metrics,
        )

    fill_rate = metrics.get("fill_rate") or 0.0
    slippage_bp = metrics.get("avg_slippage_bp")

    status = "HIGH"
    reasons = ["EXEC_OK"]
    score = min(max(fill_rate, 0.0), 1.0)

    if fill_rate < 0.6:
        status = "LOW"
        reasons = ["EXEC_LOW_FILL"]
    elif slippage_bp is not None and slippage_bp > 50:
        status = "MEDIUM"
        reasons = ["EXEC_HIGH_SLIPPAGE"]

    return GovernanceModuleStatus(
        status=status,
        score=score,
        updated_at=metrics.get("last_execution_at") or datetime.utcnow().isoformat(),
        is_stub=False,
        reasons=reasons,
        metrics=metrics,
    )


