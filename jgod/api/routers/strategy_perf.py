"""
Strategy Performance Feed API Router

Provides endpoints for strategy performance evaluation.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from jgod.api.schemas.strategy_perf import (
    PerformanceSnapshotResponseSchema,
    snapshot_to_response_schema,
)
from jgod.strategy_perf.service import (
    get_performance,
    recompute_and_save,
    get_latest_snapshot,
)
from jgod.strategy_perf.models import PerformanceGrade

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/latest/{symbol}",
    response_model=PerformanceSnapshotResponseSchema,
    summary="Get latest performance snapshot for symbol",
    description="讀取最新存檔的策略績效快照",
)
async def get_latest_endpoint(
    symbol: str,
) -> PerformanceSnapshotResponseSchema:
    """Get latest saved performance snapshot for a symbol"""
    try:
        snapshot = get_latest_snapshot(symbol)
        
        # If no snapshot, return empty (still 200)
        if not snapshot.items:
            from jgod.strategy_perf.models import PerformanceSnapshot
            empty_snapshot = PerformanceSnapshot(symbol=symbol)
            return snapshot_to_response_schema(empty_snapshot)
        
        return snapshot_to_response_schema(snapshot)
    except Exception as e:
        logger.error(f"Error getting latest performance snapshot for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/recompute/{symbol}",
    response_model=PerformanceSnapshotResponseSchema,
    summary="Recompute and save performance snapshot",
    description="計算並存檔策略績效快照",
)
async def recompute_endpoint(
    symbol: str,
    limit: int = Query(60, ge=1, le=200, description="Number of timeline items to use"),
    window: int = Query(20, ge=5, le=60, description="Window size for decay calculation"),
) -> PerformanceSnapshotResponseSchema:
    """Recompute performance and save as snapshot"""
    try:
        snapshot = recompute_and_save(symbol, limit, window)
        return snapshot_to_response_schema(snapshot)
    except Exception as e:
        logger.error(f"Error recomputing performance for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

