"""
S-Rank Engine V2 API Router

Provides endpoints for strategy recommendation system.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from jgod.api.schemas.s_rank_v2 import (
    RecommendationResponseSchema,
    RecommendationSnapshotResponseSchema,
    snapshot_to_response_schema,
    snapshot_to_snapshot_response_schema,
)
from jgod.s_rank_v2.service import (
    get_recommendation,
    recompute_and_save,
    get_latest_snapshot,
)
from jgod.s_rank_v2.models import StabilityGrade

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/recommendation/{symbol}",
    response_model=RecommendationResponseSchema,
    summary="Get strategy recommendation for symbol",
    description="即時計算策略推薦（不存檔）",
)
async def get_recommendation_endpoint(
    symbol: str,
    limit: int = Query(60, ge=1, le=200, description="Number of timeline items to use"),
    k: int = Query(5, ge=1, le=10, description="Number of top strategies to recommend"),
    mode: str = Query("performance", description="Recommendation mode: 'signals' (rule-based) or 'performance' (performance-driven)"),
) -> RecommendationResponseSchema:
    """Get strategy recommendation for a symbol"""
    try:
        snapshot = get_recommendation(symbol, limit, k, mode)
        return snapshot_to_response_schema(snapshot)
    except Exception as e:
        logger.error(f"Error getting recommendation for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/recompute/{symbol}",
    response_model=RecommendationSnapshotResponseSchema,
    summary="Recompute and save recommendation snapshot",
    description="計算並存檔策略推薦快照",
)
async def recompute_endpoint(
    symbol: str,
    limit: int = Query(60, ge=1, le=200, description="Number of timeline items to use"),
    k: int = Query(5, ge=1, le=10, description="Number of top strategies to recommend"),
    mode: str = Query("performance", description="Recommendation mode: 'signals' (rule-based) or 'performance' (performance-driven)"),
) -> RecommendationSnapshotResponseSchema:
    """Recompute recommendation and save as snapshot"""
    try:
        snapshot = recompute_and_save(symbol, limit, k, mode)
        return snapshot_to_snapshot_response_schema(snapshot)
    except Exception as e:
        logger.error(f"Error recomputing recommendation for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/latest/{symbol}",
    response_model=RecommendationSnapshotResponseSchema,
    summary="Get latest recommendation snapshot for symbol",
    description="讀取最新存檔的策略推薦快照",
)
async def get_latest_endpoint(
    symbol: str,
) -> RecommendationSnapshotResponseSchema:
    """Get latest saved snapshot for a symbol"""
    try:
        snapshot = get_latest_snapshot(symbol)
        
        if not snapshot:
            # Return empty snapshot (NO_DATA) - still 200
            from jgod.s_rank_v2.models import RecommendationSnapshot, Metrics, StabilityGrade
            empty_snapshot = RecommendationSnapshot(
                symbol=symbol,
                metrics=Metrics(
                    n_points=0,
                    score_std=0.0,
                    max_abs_delta=0.0,
                    trend_slope=0.0,
                    stability_grade=StabilityGrade.NO_DATA,
                ),
            )
            return snapshot_to_snapshot_response_schema(empty_snapshot)
        
        return snapshot_to_snapshot_response_schema(snapshot)
    except Exception as e:
        logger.error(f"Error getting latest snapshot for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

