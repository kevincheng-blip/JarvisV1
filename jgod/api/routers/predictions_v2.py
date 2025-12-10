"""Predictions V2 API Router

Enhanced predictions API with Decision Layer V2 support.
"""

import logging
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from jgod.api.schemas.predictions_v2 import (
    FinalScoreRequest,
    FinalScoreItem,
    DoctrineFlagSchema,
)
from jgod.decision.models import RawScoreItem, DecisionOutput
from jgod.decision.integration_policy import generate_final_predictions_for_date
from jgod.decision.config import DecisionConfig

logger = logging.getLogger(__name__)

router = APIRouter()


def _decision_output_to_final_score_item(
    output: DecisionOutput,
    version: str = "v2",
) -> FinalScoreItem:
    """Convert DecisionOutput to FinalScoreItem"""
    return FinalScoreItem(
        symbol=output.symbol,
        date=output.date,
        raw_score=output.raw_score,
        final_score=output.final_score,
        correction_factor=output.correction_factor,
        doctrine_flags=[
            DoctrineFlagSchema(
                code=flag.code,
                severity=flag.severity,
                message=flag.message,
                doctrine_refs=flag.doctrine_refs,
            )
            for flag in output.doctrine_flags
        ],
        adjustment_reason=output.adjustment_reason,
        llm_model=output.llm_model,
        version=version,
    )


@router.get(
    "/final-score",
    response_model=FinalScoreItem,
    summary="Get final score for a symbol",
    description="Calculate final score using Decision Layer (v1 or v2).",
)
async def get_final_score(
    symbol: str = Query(..., description="Stock symbol"),
    date: date = Query(..., description="Date (YYYY-MM-DD)"),
    version: str = Query("v2", description="Decision Layer version: 'v1' or 'v2'"),
) -> FinalScoreItem:
    """
    Get final score for a specific symbol and date.
    
    For v2, uses S-Rank weighted strategy scores, conflict adjustment, and Doctrine alerts.
    For v1, uses LLM-based decision making.
    """
    try:
        # TODO: Load actual RawScoreItem from Prediction Engine or database
        # For now, create a mock RawScoreItem
        raw_item = RawScoreItem(
            symbol=symbol,
            date=date,
            raw_score=0.75,  # Mock score
            strategy_scores={
                "S1": 0.8,
                "S2": 0.7,
                "S3": 0.6,
            },
            risk_metrics={},
            context_tags=[],
        )
        
        # Get KnowledgeBrain if available
        knowledge_brain = None
        try:
            from jgod.council_chamber.knowledge_gateway import get_knowledge_brain
            knowledge_brain = get_knowledge_brain()
        except Exception as e:
            logger.debug(f"KnowledgeBrain not available: {e}")
        
        # Generate final prediction
        config = DecisionConfig() if version == "v1" else None
        outputs = generate_final_predictions_for_date(
            trade_date=date,
            raw_items=[raw_item],
            config=config,
            knowledge_brain=knowledge_brain,
            version=version,
        )
        
        if not outputs:
            raise HTTPException(status_code=404, detail=f"No prediction found for {symbol} on {date}")
        
        output = outputs[0]
        return _decision_output_to_final_score_item(output, version=version)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating final score for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/top-n/long",
    response_model=List[FinalScoreItem],
    summary="Get top N long predictions (V2)",
    description="Get top N long predictions sorted by Final Score v2.",
)
async def get_top_n_long_v2(
    date: date = Query(None, description="Date (YYYY-MM-DD), default: today"),
    limit: int = Query(30, ge=1, le=200, description="Number of items to return"),
    version: str = Query("v2", description="Decision Layer version"),
) -> List[FinalScoreItem]:
    """Get top N long predictions using Decision Layer V2"""
    try:
        if date is None:
            date = date.today()
        
        # TODO: Load actual RawScoreItems from Prediction Engine
        # For now, return empty list or mock data
        logger.warning("Top N API requires integration with Prediction Engine - returning empty list")
        return []
        
    except Exception as e:
        logger.error(f"Error getting top N long predictions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/top-n/short",
    response_model=List[FinalScoreItem],
    summary="Get top N short predictions (V2)",
    description="Get top N short predictions sorted by Final Score v2.",
)
async def get_top_n_short_v2(
    date: date = Query(None, description="Date (YYYY-MM-DD), default: today"),
    limit: int = Query(30, ge=1, le=200, description="Number of items to return"),
    version: str = Query("v2", description="Decision Layer version"),
) -> List[FinalScoreItem]:
    """Get top N short predictions using Decision Layer V2"""
    try:
        if date is None:
            date = date.today()
        
        # TODO: Load actual RawScoreItems from Prediction Engine
        logger.warning("Top N API requires integration with Prediction Engine - returning empty list")
        return []
        
    except Exception as e:
        logger.error(f"Error getting top N short predictions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

