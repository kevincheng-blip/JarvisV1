"""
S-Rank Engine V2 Service

Service layer that combines timeline fetching, recommendation computation, and storage.
"""

import logging
from typing import List, Optional
from datetime import date

from jgod.s_rank_v2.models import RecommendationSnapshot, RecommendationItem
from jgod.s_rank_v2.recommender import recommend, recommend_from_performance, TimelineItem
from jgod.s_rank_v2.storage import save_snapshot, load_latest

logger = logging.getLogger(__name__)


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


def get_recommendation(
    symbol: str,
    limit: int = 60,
    k: int = 5,
    mode: str = "performance",
) -> RecommendationSnapshot:
    """
    Get recommendation for a symbol (compute on-the-fly, no storage).
    
    Args:
        symbol: Stock symbol
        limit: Number of timeline items to use
        k: Number of top strategies to recommend
        mode: "signals" (rule-based) or "performance" (performance-driven)
        
    Returns:
        RecommendationSnapshot (without snapshot_id if no data)
    """
    # Fetch timeline
    timeline_items = _fetch_timeline_from_db(symbol, limit)
    
    if not timeline_items:
        # Return empty snapshot
        from jgod.s_rank_v2.models import Metrics, StabilityGrade
        return RecommendationSnapshot(
            symbol=symbol,
            metrics=Metrics(
                n_points=0,
                score_std=0.0,
                max_abs_delta=0.0,
                trend_slope=0.0,
                stability_grade=StabilityGrade.NO_DATA,
            ),
        )
    
    # Determine date range
    start_date = date.fromisoformat(timeline_items[0]["date"]) if timeline_items else None
    end_date = date.fromisoformat(timeline_items[-1]["date"]) if timeline_items else None
    
    if mode == "performance":
        # Performance-driven mode
        try:
            from jgod.strategy_perf.service import get_performance
            
            # Get performance snapshot
            perf_snapshot = get_performance(symbol, limit, window=20)
            
            if not perf_snapshot.items:
                # No performance data, fallback to signals mode
                items, weights, rationale, metrics = recommend(timeline_items, k)
            else:
                # Convert performance items to dict format
                perf_items = [
                    {
                        "strategy_id": item.strategy_id,
                        "sharpe_proxy": item.sharpe_proxy,
                        "max_drawdown_proxy": item.max_drawdown_proxy,
                        "turnover_proxy": item.turnover_proxy,
                        "avg_return_proxy": item.avg_return_proxy,
                        "decay_slope": item.decay_slope,
                        "grade": item.grade.value,
                    }
                    for item in perf_snapshot.items
                ]
                
                # Get recommendation from performance
                items, weights, rationale = recommend_from_performance(perf_items, k)
                
                # Still compute metrics for display
                from jgod.s_rank_v2.recommender import compute_metrics
                metrics = compute_metrics(timeline_items)
        except Exception as e:
            logger.warning(f"Failed to get performance for {symbol}, falling back to signals mode: {e}")
            # Fallback to signals mode
            items, weights, rationale, metrics = recommend(timeline_items, k)
    else:
        # Signals mode (original rule-based)
        items, weights, rationale, metrics = recommend(timeline_items, k)
    
    return RecommendationSnapshot(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        items=items,
        weights=weights,
        metrics=metrics,
        rationale=rationale,
    )


def recompute_and_save(
    symbol: str,
    limit: int = 60,
    k: int = 5,
    mode: str = "performance",
) -> RecommendationSnapshot:
    """
    Recompute recommendation and save as snapshot.
    
    Args:
        symbol: Stock symbol
        limit: Number of timeline items to use
        k: Number of top strategies to recommend
        mode: "signals" (rule-based) or "performance" (performance-driven)
        
    Returns:
        Saved RecommendationSnapshot (with snapshot_id)
    """
    # Get recommendation (same as get_recommendation)
    snapshot = get_recommendation(symbol, limit, k, mode)
    
    # Save to storage
    save_snapshot(snapshot)
    
    logger.info(f"Recomputed and saved recommendation for {symbol} (mode={mode})")
    return snapshot


def get_latest_snapshot(symbol: str) -> Optional[RecommendationSnapshot]:
    """
    Get the latest saved snapshot for a symbol.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        RecommendationSnapshot if found, None otherwise
    """
    return load_latest(symbol)

