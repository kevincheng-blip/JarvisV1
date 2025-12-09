"""Signal Conflict API Router

Provides endpoints for signal conflict and consensus analysis.
"""

import logging
from datetime import date, datetime
from typing import List, Optional, Literal

from fastapi import APIRouter, HTTPException, Query

from jgod.api.schemas.signal_conflict import ConflictItem
from jgod.signal_aggregation.engine import SignalAggregationEngineV1
from jgod.signal_aggregation.models import ConflictItem as ConflictItemModel

logger = logging.getLogger(__name__)

router = APIRouter()


def _convert_to_schema(item: ConflictItemModel) -> ConflictItem:
    """Convert internal ConflictItem model to API schema"""
    return ConflictItem(
        symbol=item.symbol,
        name=item.name,
        consensus_score=item.consensus_score,
        conflict_score=item.conflict_score,
        majority_vote=item.majority_vote,
        strategy_votes=item.strategy_votes,
        raw_score=item.raw_score,
        final_score=item.final_score,
    )


@router.get(
    "/conflicts",
    response_model=List[ConflictItem],
    summary="Get signal conflicts for a specific date",
    description="Retrieves signal conflict and consensus analysis for all symbols on a given date.",
)
async def get_signal_conflicts(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format, default: latest trading day"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of items to return"),
    side: Literal["all", "long", "short"] = Query("all", description="Filter by majority vote side"),
) -> List[ConflictItem]:
    """
    Get signal conflicts for a specific date.
    
    Returns list of ConflictItem objects sorted by conflict_score (descending),
    showing stocks with the highest strategy conflicts first.
    """
    # Parse date
    if date:
        try:
            trade_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        trade_date = date.today()  # Default to today
    
    try:
        # Initialize engine
        engine = SignalAggregationEngineV1()
        
        # Get conflicts
        conflict_items = engine.get_conflicts_for_date(
            trade_date=trade_date,
            limit=limit,
            side=side,
        )
        
        # Convert to API schemas
        result = [_convert_to_schema(item) for item in conflict_items]
        
        logger.info(f"Returning {len(result)} conflict items for date {trade_date}")
        return result
    
    except Exception as e:
        logger.error(f"Error getting signal conflicts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

