"""
Strategy Performance Feed Service

Service layer that combines timeline fetching, performance evaluation, and storage.
"""

import logging
from typing import List
from datetime import date

from jgod.strategy_perf.models import PerformanceSnapshot, StrategyPerformanceMetrics
from jgod.strategy_perf.evaluator import evaluate_all_strategies
from jgod.strategy_perf.storage import save_snapshot, load_latest
from jgod.observer.prediction_stability import TimelineItem

logger = logging.getLogger(__name__)

# Strategy pool (same as s_rank_v2)
STRATEGY_POOL = [
    "trend_follow",
    "mean_reversion",
    "breakout",
    "risk_off",
    "momentum",
]


def _fetch_timeline_from_db(symbol: str, limit: int = 60) -> List[TimelineItem]:
    """
    Fetch prediction timeline from database.
    
    Args:
        symbol: Stock symbol
        limit: Maximum number of items
        
    Returns:
        List of timeline items
    """
    try:
        from jgod.api.dependencies import get_db
        from jgod.storage.models import PredictionSnapshot
        
        db_gen = get_db()
        if not db_gen:
            return []
        
        db = next(db_gen)
        if not db:
            return []
        
        # Query predictions ordered by date desc
        predictions = db.query(PredictionSnapshot).filter(
            PredictionSnapshot.symbol == symbol
        ).order_by(
            PredictionSnapshot.date.desc()
        ).limit(limit).all()
        
        # Convert to timeline items (reverse to chronological order)
        items = []
        for pred in reversed(predictions):
            raw_score = pred.score if hasattr(pred, 'score') and pred.score is not None else (pred.total_score or 0.0)
            items.append({
                "date": pred.date.isoformat(),
                "final_score": float(raw_score),
            })
        
        return items
    except Exception as e:
        logger.warning(f"Failed to fetch timeline from DB for {symbol}: {e}")
        return []


def get_performance(
    symbol: str,
    limit: int = 60,
    window: int = 20,
) -> PerformanceSnapshot:
    """
    Get performance snapshot for a symbol (compute on-the-fly, no storage).
    
    Args:
        symbol: Stock symbol
        limit: Number of timeline items to use
        window: Window size for decay calculation
        
    Returns:
        PerformanceSnapshot (without snapshot_id if no data)
    """
    # Fetch timeline
    timeline_items = _fetch_timeline_from_db(symbol, limit)
    
    if not timeline_items:
        # Return empty snapshot
        return PerformanceSnapshot(
            symbol=symbol,
            limit=limit,
            window=window,
        )
    
    # Evaluate all strategies
    items = evaluate_all_strategies(timeline_items, STRATEGY_POOL, window)
    
    return PerformanceSnapshot(
        symbol=symbol,
        limit=limit,
        window=window,
        items=items,
    )


def recompute_and_save(
    symbol: str,
    limit: int = 60,
    window: int = 20,
) -> PerformanceSnapshot:
    """
    Recompute performance and save as snapshot.
    
    Args:
        symbol: Stock symbol
        limit: Number of timeline items to use
        window: Window size for decay calculation
        
    Returns:
        Saved PerformanceSnapshot (with snapshot_id)
    """
    # Get performance (same as get_performance)
    snapshot = get_performance(symbol, limit, window)
    
    # Save to storage
    save_snapshot(snapshot)
    
    logger.info(f"Recomputed and saved performance for {symbol}")
    return snapshot


def get_latest_snapshot(symbol: str) -> PerformanceSnapshot:
    """
    Get the latest saved snapshot for a symbol.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        PerformanceSnapshot if found, empty snapshot otherwise
    """
    snapshot = load_latest(symbol)
    if not snapshot:
        # Return empty snapshot
        return PerformanceSnapshot(
            symbol=symbol,
        )
    return snapshot

