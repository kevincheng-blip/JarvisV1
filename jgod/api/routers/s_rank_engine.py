"""S-Rank Factor Engine API Router

Provides endpoints for S-Rank factor calculation and retrieval.
"""

import logging
from datetime import datetime, date, timedelta
from typing import List

from fastapi import APIRouter, HTTPException, Query

from jgod.api.schemas.s_rank_engine import (
    SRankCalculateRequest,
    SRankCalculateResponse,
    SRankFactorSchema,
    StrategyPerformanceSnapshotSchema,
    SignalQualityFactorsSchema,
)
from jgod.s_rank_engine.engine import SRankEngineV1
from jgod.s_rank_engine.storage import SRankFactorStorageV1
from jgod.s_rank_engine.models import SRankFactor

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize engine and storage (singleton)
_storage = SRankFactorStorageV1()
_engine = SRankEngineV1(storage=_storage)


def _factor_to_schema(factor: SRankFactor) -> SRankFactorSchema:
    """Convert SRankFactor to API schema"""
    return SRankFactorSchema(
        strategy_id=factor.strategy_id,
        performance_snapshot=StrategyPerformanceSnapshotSchema(
            strategy_id=factor.performance_snapshot.strategy_id,
            sharpe_ratio=factor.performance_snapshot.sharpe_ratio,
            max_drawdown=factor.performance_snapshot.max_drawdown,
            total_return=factor.performance_snapshot.total_return,
            avg_holding_period_days=factor.performance_snapshot.avg_holding_period_days,
            last_run_date=factor.performance_snapshot.last_run_date.isoformat(),
            is_active=factor.performance_snapshot.is_active,
            market_correlation=factor.performance_snapshot.market_correlation,
        ),
        quality_factors=SignalQualityFactorsSchema(
            signal_strength_confidence=factor.quality_factors.signal_strength_confidence,
            factor_decay_rate=factor.quality_factors.factor_decay_rate,
            consistency_score=factor.quality_factors.consistency_score,
        ),
        s_rank_score=factor.s_rank_score,
        rank_level=factor.rank_level,
        calculated_at=factor.calculated_at,
    )


@router.post(
    "/calculate",
    response_model=SRankCalculateResponse,
    summary="Calculate S-Rank factors",
    description="Calculates S-Rank scores for all strategies based on performance metrics.",
)
async def calculate_s_rank(request: SRankCalculateRequest) -> SRankCalculateResponse:
    """
    Calculate S-Rank factors for all strategies.
    
    For v1, always recalculates. The force_recalculate flag is reserved for future use.
    """
    try:
        factors = _engine.calculate(time_horizon_days=request.time_horizon_days)
        
        return SRankCalculateResponse(
            run_at=datetime.now(),
            strategy_count=len(factors),
            time_horizon_days=request.time_horizon_days,
        )
    except Exception as e:
        logger.error(f"Error calculating S-Rank: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/factors/latest",
    response_model=List[SRankFactorSchema],
    summary="Get latest S-Rank factors",
    description="Retrieves the most recent S-Rank factors, sorted by score descending.",
)
async def get_latest_factors() -> List[SRankFactorSchema]:
    """Get latest S-Rank factors, sorted by score descending"""
    try:
        factors = _storage.load_latest_factors()
        
        # Sort by score descending (should already be sorted, but ensure it)
        factors.sort(key=lambda x: x.s_rank_score, reverse=True)
        
        return [_factor_to_schema(f) for f in factors]
    except Exception as e:
        logger.error(f"Error loading latest factors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/history/{strategy_id}",
    response_model=List[SRankFactorSchema],
    summary="Get historical S-Rank factors for a strategy",
    description="Retrieves historical S-Rank factors for a specific strategy within a date range.",
)
async def get_strategy_history(
    strategy_id: str,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
) -> List[SRankFactorSchema]:
    """Get historical S-Rank factors for a strategy"""
    try:
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date must be <= end_date")
        
        all_factors: List[SRankFactor] = []
        
        # Load factors for each date in range
        current_date = start_date
        while current_date <= end_date:
            date_factors = _storage.load_historical_factors(current_date)
            all_factors.extend([f for f in date_factors if f.strategy_id == strategy_id])
            current_date = current_date + timedelta(days=1)
        
        # Sort by calculated_at descending
        all_factors.sort(key=lambda x: x.calculated_at, reverse=True)
        
        return [_factor_to_schema(f) for f in all_factors]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading strategy history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

