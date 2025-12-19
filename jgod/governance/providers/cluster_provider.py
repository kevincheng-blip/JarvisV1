"""Cluster Risk Provider

Computes cluster risk based on M50 signal consensus (MVP proxy).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable, List, Dict, Optional

from jgod.api.schemas.governance_summary import GovernanceModuleStatus
from jgod.governance.signal_bus import get_signal_bus, SignalPayload

logger = logging.getLogger(__name__)


def _default_signal_provider() -> List[Dict]:
    """
    Default stub signal provider (synthetic signals for testing).
    Returns a small synthetic list: 10 positive, 3 negative.
    """
    return [
        {"signal_value": 0.8, "symbol": "2330"},
        {"signal_value": 0.6, "symbol": "2317"},
        {"signal_value": 0.7, "symbol": "2454"},
        {"signal_value": 0.5, "symbol": "2308"},
        {"signal_value": 0.9, "symbol": "2382"},
        {"signal_value": 0.4, "symbol": "2412"},
        {"signal_value": 0.3, "symbol": "2891"},
        {"signal_value": 0.6, "symbol": "2886"},
        {"signal_value": 0.7, "symbol": "2882"},
        {"signal_value": 0.5, "symbol": "2881"},
        {"signal_value": -0.4, "symbol": "1301"},
        {"signal_value": -0.3, "symbol": "1303"},
        {"signal_value": -0.5, "symbol": "1326"},
    ]


def _try_get_signals_from_existing() -> Optional[List[Dict]]:
    """
    Try to get signals from existing system (signal_conflict / decision / observer).
    Returns None if not available (defensive).
    """
    try:
        # Try signal_conflict first
        from jgod.signal_aggregation.data_access import get_latest_signals
        signals = get_latest_signals(limit=50)
        if signals:
            # Convert to expected format: [{"signal_value": float, "symbol": str}]
            result = []
            for sig in signals:
                if isinstance(sig, dict):
                    signal_value = sig.get("signal_value") or sig.get("value") or 0.0
                    symbol = sig.get("symbol") or sig.get("stock_id") or ""
                    if symbol:
                        result.append({"signal_value": float(signal_value), "symbol": str(symbol)})
            if result:
                return result
    except Exception:
        pass
    
    try:
        # Try decision inputs
        from jgod.decision.data_access import get_recent_decision_inputs
        inputs = get_recent_decision_inputs(limit=50)
        if inputs:
            result = []
            for inp in inputs:
                if isinstance(inp, dict):
                    signal_value = inp.get("signal_value") or inp.get("signal") or 0.0
                    symbol = inp.get("symbol") or inp.get("stock_id") or ""
                    if symbol:
                        result.append({"signal_value": float(signal_value), "symbol": str(symbol)})
            if result:
                return result
    except Exception:
        pass
    
    return None


def get_cluster_risk_status(
    signal_bus_override: Optional[Callable[[], List[SignalPayload]]] = None,
) -> GovernanceModuleStatus:
    """
    Compute cluster risk based on M50 signal consensus.
    
    Args:
        signal_bus_override: Optional callable that returns list of SignalPayload.
                            If None, uses global SignalBus.
    
    Returns:
        GovernanceModuleStatus with cluster risk assessment.
    """
    # Get signals from SignalBus
    signal_payloads: List[SignalPayload] = []
    
    if signal_bus_override:
        try:
            signal_payloads = signal_bus_override()
        except Exception as e:
            logger.warning(f"Signal bus override failed: {e}", exc_info=False)
            signal_payloads = []
    else:
        # Use global SignalBus
        try:
            signal_bus = get_signal_bus()
            signal_payloads = signal_bus.get_latest_signals(family="M50")
        except Exception as e:
            logger.warning(f"SignalBus failed: {e}", exc_info=False)
            signal_payloads = []
    
    # Convert SignalPayload to dict format for compatibility
    signals: List[Dict] = []
    for payload in signal_payloads:
        if isinstance(payload, dict) and "value" in payload:
            signals.append({
                "signal_value": payload["value"],
                "symbol": payload.get("id", "unknown"),
            })
    
    # Filter valid signals (signal_value != 0)
    valid_signals = [
        s for s in signals
        if isinstance(s, dict)
        and "signal_value" in s
        and isinstance(s["signal_value"], (int, float))
        and s["signal_value"] != 0
    ]
    
    total_signals = len(valid_signals)
    
    # Edge case: no valid signals
    if total_signals == 0:
        return GovernanceModuleStatus(
            status="UNKNOWN",
            score=None,
            updated_at=datetime.utcnow().isoformat(),
            is_stub=True,
            reasons=["CLUSTER_NO_SIGNALS"],
            metrics={
                "positive_count": 0,
                "negative_count": 0,
                "total_signals": 0,
                "consensus_side": "NONE",
            },
        )
    
    # Count positive and negative
    positive_count = sum(1 for s in valid_signals if s["signal_value"] > 0)
    negative_count = sum(1 for s in valid_signals if s["signal_value"] < 0)
    
    # Compute consensus score
    max_count = max(positive_count, negative_count)
    consensus_score = (max_count / total_signals) * 100.0
    
    # Determine consensus side
    if positive_count > negative_count:
        consensus_side = "BUY"
    elif negative_count > positive_count:
        consensus_side = "SELL"
    else:
        consensus_side = "MIXED"
    
    # Determine status and reasons
    if consensus_score >= 85.0:
        status = "HIGH"
        reasons = ["CLUSTER_HIGH_CONSENSUS"]
    elif consensus_score >= 75.0:
        status = "MEDIUM"
        reasons = ["CLUSTER_MEDIUM_CONSENSUS"]
    else:
        status = "LOW"
        reasons = ["CLUSTER_LOW"]
    
    # Determine is_stub: False if we have signals (even if from stub provider, the calculation is real)
    is_stub = False
    
    return GovernanceModuleStatus(
        status=status,
        score=consensus_score,
        updated_at=datetime.utcnow().isoformat(),
        is_stub=is_stub,
        reasons=reasons,
        metrics={
            "positive_count": positive_count,
            "negative_count": negative_count,
            "total_signals": total_signals,
            "consensus_side": consensus_side,
        },
    )
