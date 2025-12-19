from __future__ import annotations

from datetime import datetime
from typing import Tuple

from jgod.api.schemas.governance_summary import GovernanceModuleStatus
from jgod.governance.providers.execution_provider import get_execution_rigor_status as _exec_provider
from jgod.governance.providers.cluster_provider import get_cluster_risk_status as _cluster_provider
from jgod.governance.providers.regime_provider import get_regime_status as _regime_provider

__all__ = [
    "get_execution_rigor_status",
    "get_cluster_risk_status",
    "get_market_regime_status",
]


def get_execution_rigor_status() -> GovernanceModuleStatus:
    try:
        return _exec_provider()
    except Exception:
        return GovernanceModuleStatus(
            status="LOW",
            score=0.0,
            updated_at=datetime.utcnow().isoformat(),
            is_stub=True,
            reasons=["EXEC_NO_DATA"],
            metrics={
                "fill_rate": 0.0,
                "avg_slippage_bp": None,
                "reject_rate": None,
                "last_execution_at": None,
            },
        )


def get_cluster_risk_status() -> GovernanceModuleStatus:
    """Get cluster risk status from ClusterProvider."""
    try:
        return _cluster_provider()
    except Exception:
        # Fallback to stub on error
        return GovernanceModuleStatus(
            status="UNKNOWN",
            score=None,
            updated_at=datetime.utcnow().isoformat(),
            is_stub=True,
            reasons=["CLUSTER_NO_SIGNALS"],
            metrics={},
        )


def get_market_regime_status() -> Tuple[GovernanceModuleStatus, str]:
    """Get market regime status from RegimeProvider."""
    try:
        return _regime_provider()
    except Exception:
        # Fallback to stub on error
        return (
            GovernanceModuleStatus(
                status="UNKNOWN",
                score=None,
                updated_at=datetime.utcnow().isoformat(),
                is_stub=True,
                reasons=["REGIME_STUB"],
                metrics={},
            ),
            "MEDIUM",
        )


