"""Decision AB Test API Router

Provides endpoints for Decision Layer AB test results.
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Query

from jgod.api.schemas.decision_ab import DecisionAbResultSchema, ArmResultSchema, ArmMetricsSchema
from jgod.decision_ab.storage import AbResultStorage
from jgod.decision_ab.models import DecisionAbResult

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize storage
_storage = AbResultStorage()


def _convert_ab_result_to_schema(result: DecisionAbResult) -> DecisionAbResultSchema:
    """Convert DecisionAbResult to API schema"""
    return DecisionAbResultSchema(
        experiment_id=result.experiment_id,
        created_at=result.created_at,
        raw_only=ArmResultSchema(
            experiment_id=result.raw_only.experiment_id,
            mode=result.raw_only.mode,
            start_date=result.raw_only.start_date,
            end_date=result.raw_only.end_date,
            metrics=ArmMetricsSchema(**result.raw_only.metrics.model_dump()),
        ),
        decision_on=ArmResultSchema(
            experiment_id=result.decision_on.experiment_id,
            mode=result.decision_on.mode,
            start_date=result.decision_on.start_date,
            end_date=result.decision_on.end_date,
            metrics=ArmMetricsSchema(**result.decision_on.metrics.model_dump()),
        ),
        delta_sharpe=result.delta_sharpe,
        delta_max_drawdown=result.delta_max_drawdown,
        delta_total_return=result.delta_total_return,
        delta_win_rate=result.delta_win_rate,
        delta_turnover=result.delta_turnover,
    )


@router.get(
    "/recent",
    response_model=List[DecisionAbResultSchema],
    summary="Get recent Decision AB test results",
    description="Retrieves recent Decision Layer AB test results, comparing RAW_ONLY vs DECISION_ON modes.",
)
async def get_recent_ab_results(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results to return"),
) -> List[DecisionAbResultSchema]:
    """
    Get recent Decision AB test results.
    
    Returns:
        List of DecisionAbResultSchema, sorted by created_at (newest first)
    """
    try:
        results = _storage.load_recent(limit=limit)
        return [_convert_ab_result_to_schema(r) for r in results]
    except Exception as e:
        logger.error(f"Error loading recent AB results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/{experiment_id}",
    response_model=DecisionAbResultSchema,
    summary="Get Decision AB test result by experiment ID",
    description="Retrieves a specific Decision AB test result by experiment_id.",
)
async def get_ab_result_by_id(
    experiment_id: str,
) -> DecisionAbResultSchema:
    """
    Get Decision AB test result by experiment ID.
    
    Args:
        experiment_id: Experiment identifier
    
    Returns:
        DecisionAbResultSchema
    
    Raises:
        404: If experiment not found
    """
    try:
        result = _storage.load_by_experiment_id(experiment_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Experiment not found: {experiment_id}")
        return _convert_ab_result_to_schema(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading AB result for {experiment_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

