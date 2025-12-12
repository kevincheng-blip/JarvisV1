"""
Decision V3 Service

Service layer that combines decision computation and snapshot storage.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime

from jgod.decision_v3.engine import DecisionEngineV3
from jgod.decision_v3.models import DecisionV3Result
from jgod.decision_v3.storage import save_snapshot, load_latest, list_latest

logger = logging.getLogger(__name__)


def _result_to_dict(result: DecisionV3Result) -> Dict:
    """Convert DecisionV3Result to dict for storage"""
    return {
        "symbol": result.symbol,
        "as_of_date": result.as_of_date.isoformat() if result.as_of_date else None,
        "selected_primary_strategy": result.selected_primary_strategy,
        "selected_secondary_strategies": result.selected_secondary_strategies,
        "weights": [
            {
                "strategy_id": w.strategy_id,
                "weight": w.weight,
                "grade": w.grade,
                "metrics": w.metrics,
                "rationale": w.rationale,
            }
            for w in result.weights
        ],
        "risk_plan": {
            "position_scale": result.risk_plan.position_scale if result.risk_plan else 0.0,
            "risk_state": result.risk_plan.risk_state if result.risk_plan else "RISK_OFF",
            "reasons": result.risk_plan.reasons if result.risk_plan else [],
        },
        "confidence": result.confidence,
        "explain": result.explain,
    }


def compute_decision(
    symbol: str,
    mode: str = "performance",
    limit: int = 60,
    k: int = 5,
) -> DecisionV3Result:
    """
    Compute decision for a symbol (no storage).
    
    Args:
        symbol: Stock symbol
        mode: "performance" (default) or "signals"
        limit: Number of timeline items to use
        k: Number of top strategies to recommend
        
    Returns:
        DecisionV3Result
    """
    engine = DecisionEngineV3()
    return engine.decide(symbol, mode, limit, k)


def recompute_and_save(
    symbol: str,
    mode: str = "performance",
    limit: int = 60,
    k: int = 5,
) -> Dict:
    """
    Recompute decision and save as snapshot.
    
    Args:
        symbol: Stock symbol
        mode: "performance" (default) or "signals"
        limit: Number of timeline items to use
        k: Number of top strategies to recommend
        
    Returns:
        Snapshot dict with snapshot_id, created_at, symbol, mode, limit, k, result
    """
    # Compute decision
    result = compute_decision(symbol, mode, limit, k)
    
    # Build snapshot dict
    snapshot = {
        "created_at": datetime.now(),
        "symbol": symbol,
        "mode": mode,
        "limit": limit,
        "k": k,
        "result": _result_to_dict(result),
    }
    
    # Save to storage
    snapshot_id = save_snapshot(snapshot)
    snapshot["snapshot_id"] = snapshot_id
    
    logger.info(f"Recomputed and saved Decision V3 snapshot {snapshot_id} for {symbol}")
    return snapshot


def get_latest_snapshot(symbol: str) -> Optional[Dict]:
    """
    Get the latest saved snapshot for a symbol.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Snapshot dict if found, None otherwise
    """
    return load_latest(symbol)


def list_snapshots(symbol: str, n: int = 20) -> List[Dict]:
    """
    List the latest N snapshots for a symbol.
    
    Args:
        symbol: Stock symbol
        n: Maximum number of snapshots to return
        
    Returns:
        List of snapshot dicts (newest first)
    """
    return list_latest(symbol, n)

