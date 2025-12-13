"""
Decision V3 Service

Service layer that combines decision computation and snapshot storage.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime

from jgod.decision_v3.engine import DecisionEngineV3
from jgod.decision_v3.models import DecisionV3Result
from jgod.decision_v3.storage import (
    save_snapshot, load_latest, list_latest,
    save_evaluation, load_latest_evaluation, list_evaluations,
    save_compare, load_latest_compare, list_compares,
    save_arena_snapshot, load_latest_arena, list_arena,
)
from jgod.decision_v3.evaluation import evaluate_decision_v3, EvaluationVerdict
from jgod.decision_v3.compare import compute_compare, CompareWinner
from jgod.decision_v3.arena import compute_arena, ArenaResult
from jgod.observer.prediction_stability import TimelineItem

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


def _fetch_timeline_items(symbol: str, limit: int = 60) -> List[TimelineItem]:
    """
    Fetch prediction timeline items for a symbol from database.
    
    Args:
        symbol: Stock symbol
        limit: Maximum number of items to fetch
        
    Returns:
        List of TimelineItem dicts (newest first)
    """
    try:
        from jgod.storage.models import PredictionSnapshot
        from jgod.storage.db import get_session
        
        session = next(get_session())
        
        predictions = session.query(PredictionSnapshot).filter(
            PredictionSnapshot.symbol == symbol
        ).order_by(
            PredictionSnapshot.date.desc()
        ).limit(limit).all()
        
        items = []
        for pred in predictions:
            raw_score = pred.score if hasattr(pred, 'score') and pred.score is not None else (pred.total_score or 0.0)
            signal = pred.signal or pred.verdict or "UNKNOWN"
            
            items.append({
                "date": pred.date.isoformat(),
                "final_score": float(raw_score),
                "signal": signal,
            })
        
        session.close()
        return items
    except Exception as e:
        logger.warning(f"Failed to fetch timeline for {symbol}: {e}")
        return []


def compute_evaluation(
    symbol: str,
    mode: str = "performance",
    limit: int = 60,
    k: int = 5,
    window: int = 20,
) -> Dict:
    """
    Compute evaluation for a symbol (no storage).
    
    Args:
        symbol: Stock symbol
        mode: "performance" (default) or "signals"
        limit: Number of timeline items to use
        k: Number of top strategies to recommend
        window: Evaluation window size
        
    Returns:
        Evaluation dict with metrics and verdict
    """
    # Step 1: Get decision result
    decision_result = compute_decision(symbol, mode, limit, k)
    decision_dict = _result_to_dict(decision_result)
    
    # Step 2: Fetch timeline items
    timeline_items = _fetch_timeline_items(symbol, limit)
    
    # Step 3: Evaluate
    metrics = evaluate_decision_v3(timeline_items, decision_dict, window)
    
    # Step 4: Build evaluation result
    return {
        "symbol": symbol,
        "mode": mode,
        "limit": limit,
        "k": k,
        "window": window,
        "decision": {
            "primary_strategy": decision_result.selected_primary_strategy,
            "risk_plan": {
                "position_scale": decision_result.risk_plan.position_scale if decision_result.risk_plan else 0.0,
                "risk_state": decision_result.risk_plan.risk_state if decision_result.risk_plan else "RISK_OFF",
            },
            "confidence": decision_result.confidence,
        },
        "inputs_summary": {
            "mode": mode,
            "limit": limit,
            "k": k,
            "stability_grade": "UNKNOWN",  # Can be enhanced later
            "perf_grade": "UNKNOWN",  # Can be enhanced later
        },
        "metrics": metrics,
    }


def recompute_evaluation_and_save(
    symbol: str,
    mode: str = "performance",
    limit: int = 60,
    k: int = 5,
    window: int = 20,
) -> Dict:
    """
    Recompute evaluation and save as snapshot.
    
    Args:
        symbol: Stock symbol
        mode: "performance" (default) or "signals"
        limit: Number of timeline items to use
        k: Number of top strategies to recommend
        window: Evaluation window size
        
    Returns:
        Evaluation snapshot dict with eval_id, created_at, and full evaluation
    """
    # Compute evaluation
    evaluation = compute_evaluation(symbol, mode, limit, k, window)
    
    # Build snapshot dict
    snapshot = {
        "created_at": datetime.now(),
        "symbol": symbol,
        "mode": mode,
        "limit": limit,
        "k": k,
        "window": window,
        "evaluation": evaluation,
    }
    
    # Save to storage
    eval_id = save_evaluation(snapshot)
    snapshot["eval_id"] = eval_id
    
    logger.info(f"Recomputed and saved Decision V3 evaluation {eval_id} for {symbol}")
    return snapshot


def get_latest_evaluation(symbol: str) -> Optional[Dict]:
    """
    Get the latest saved evaluation for a symbol.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Evaluation snapshot dict if found, None otherwise
    """
    return load_latest_evaluation(symbol)


def list_evaluation_snapshots(symbol: str, n: int = 20) -> List[Dict]:
    """
    List the latest N evaluation snapshots for a symbol.
    
    Args:
        symbol: Stock symbol
        n: Maximum number of snapshots to return
        
    Returns:
        List of evaluation snapshot dicts (newest first)
    """
    return list_evaluations(symbol, n)


# Compare service functions

def compute_compare_result(
    symbol: str,
    mode: str = "performance",
    limit: int = 60,
    k: int = 5,
    window: int = 20,
) -> Dict:
    """
    Compute comparison between Decision V3 and Baseline (no storage).
    
    Args:
        symbol: Stock symbol
        mode: "performance" (default) or "signals"
        limit: Number of timeline items to use
        k: Number of top strategies to recommend
        window: Evaluation window size
        
    Returns:
        Compare result dict with winner, delta_metrics, summary, recommendation_next_step
    """
    return compute_compare(symbol, mode, limit, k, window)


def recompute_compare_and_save(
    symbol: str,
    mode: str = "performance",
    limit: int = 60,
    k: int = 5,
    window: int = 20,
) -> Dict:
    """
    Recompute compare and save as snapshot.
    
    Args:
        symbol: Stock symbol
        mode: "performance" (default) or "signals"
        limit: Number of timeline items to use
        k: Number of top strategies to recommend
        window: Evaluation window size
        
    Returns:
        Compare snapshot dict with compare_id, created_at, and full compare result
    """
    # Compute compare
    compare_result = compute_compare(symbol, mode, limit, k, window)
    
    # Build snapshot dict (compare_result already has winner, delta_metrics, summary, recommendation_next_step)
    # We need to wrap it with symbol, mode, limit, k, window for the response schema
    snapshot = {
        "created_at": datetime.now(),
        "symbol": symbol,
        "mode": mode,
        "limit": limit,
        "k": k,
        "window": window,
        "compare": {
            "symbol": symbol,
            "mode": mode,
            "limit": limit,
            "k": k,
            "window": window,
            "winner": compare_result["winner"],
            "delta_metrics": compare_result["delta_metrics"],
            "summary": compare_result["summary"],
            "recommendation_next_step": compare_result["recommendation_next_step"],
        },
    }
    
    # Save to storage (save the compare_result directly, not the wrapped version)
    storage_snapshot = {
        "created_at": datetime.now(),
        "symbol": symbol,
        "mode": mode,
        "limit": limit,
        "k": k,
        "window": window,
        "compare": compare_result,
    }
    compare_id = save_compare(storage_snapshot)
    snapshot["compare_id"] = compare_id
    
    logger.info(f"Recomputed and saved Decision V3 compare {compare_id} for {symbol}")
    return snapshot


def get_latest_compare(symbol: str) -> Optional[Dict]:
    """
    Get the latest saved compare snapshot for a symbol.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Compare snapshot dict if found, None otherwise (wrapped for response schema)
    """
    snapshot = load_latest_compare(symbol)
    if not snapshot:
        return None
    
    # Wrap the compare result for response schema
    compare_result = snapshot.get("compare", {})
    return {
        "compare_id": snapshot.get("compare_id", ""),
        "created_at": snapshot.get("created_at"),
        "symbol": snapshot.get("symbol", symbol),
        "mode": snapshot.get("mode", "performance"),
        "limit": snapshot.get("limit", 60),
        "k": snapshot.get("k", 5),
        "window": snapshot.get("window", 20),
        "compare": {
            "symbol": snapshot.get("symbol", symbol),
            "mode": snapshot.get("mode", "performance"),
            "limit": snapshot.get("limit", 60),
            "k": snapshot.get("k", 5),
            "window": snapshot.get("window", 20),
            "winner": compare_result.get("winner", "NO_DATA"),
            "delta_metrics": compare_result.get("delta_metrics", {}),
            "summary": compare_result.get("summary", ""),
            "recommendation_next_step": compare_result.get("recommendation_next_step", ""),
        },
    }


def list_compare_snapshots(symbol: str, n: int = 20) -> List[Dict]:
    """
    List the latest N compare snapshots for a symbol.
    
    Args:
        symbol: Stock symbol
        n: Maximum number of snapshots to return
        
    Returns:
        List of compare snapshot dicts (newest first)
    """
    return list_compares(symbol, n)


# Arena functions

def recompute_arena_and_save(
    symbol: str,
    mode: str = "performance",
    limit: int = 60,
    k: int = 5,
    window: int = 20
) -> Dict:
    """
    Recompute arena comparison and save snapshot.
    
    Args:
        symbol: Stock symbol
        mode: Decision mode ("performance" or "signals")
        limit: Number of timeline items to fetch
        k: Number of top strategies to consider
        window: Evaluation window size
        
    Returns:
        Arena snapshot dict with arena_id
    """
    logger.info(f"Recomputing arena for {symbol} (mode={mode}, limit={limit}, k={k}, window={window})")
    
    # Compute arena result
    arena_result = compute_arena(symbol, mode, limit, k, window)
    
    # Convert ArenaResult to dict
    arena_dict = {
        "symbol": arena_result.symbol,
        "created_at": arena_result.created_at,
        "mode": arena_result.mode,
        "window": arena_result.window,
        "limit": arena_result.limit,
        "k": arena_result.k,
        "scoreboard": [
            {
                "challenger_id": score.challenger_id,
                "composite_score": score.composite_score,
                "metrics": score.metrics,
                "pareto_dominated": score.pareto_dominated,
            }
            for score in arena_result.scoreboard
        ],
        "winner_id": arena_result.winner_id,
        "is_regression": arena_result.is_regression,
        "auto_tuning": {
            "best_config": {
                "risk_mapping": arena_result.auto_tuning.best_config.risk_mapping if arena_result.auto_tuning and arena_result.auto_tuning.best_config else None,
                "composite_weights": arena_result.auto_tuning.best_config.composite_weights if arena_result.auto_tuning and arena_result.auto_tuning.best_config else None,
            } if arena_result.auto_tuning and arena_result.auto_tuning.best_config else None,
            "top_variants": [
                {
                    "config": {
                        "risk_mapping": variant[0].risk_mapping,
                        "composite_weights": variant[0].composite_weights,
                    },
                    "score": variant[1],
                }
                for variant in (arena_result.auto_tuning.top_variants if arena_result.auto_tuning else [])
            ],
            "notes": arena_result.auto_tuning.notes if arena_result.auto_tuning else "",
        } if arena_result.auto_tuning else None,
        "summary": arena_result.summary,
        "recommendation_next_step": arena_result.recommendation_next_step,
    }
    
    # Save to storage
    arena_id = save_arena_snapshot(arena_dict)
    arena_dict["arena_id"] = arena_id
    
    logger.info(f"Saved arena snapshot {arena_id} for {symbol}")
    return arena_dict


def get_latest_arena(symbol: str) -> Optional[Dict]:
    """
    Get the latest arena snapshot for a symbol.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Arena snapshot dict if found, None otherwise
    """
    snapshot = load_latest_arena(symbol)
    if not snapshot:
        return None
    
    return snapshot


def list_arena_snapshots(symbol: str, n: int = 20) -> List[Dict]:
    """
    List the latest N arena snapshots for a symbol.
    
    Args:
        symbol: Stock symbol
        n: Maximum number of snapshots to return
        
    Returns:
        List of arena snapshot dicts (newest first)
    """
    return list_arena(symbol, n)

