"""
Intelligence Status API Router

v0.6.13-P1.1: Method Layer Drift Score endpoint
"""

import logging
from fastapi import APIRouter
from typing import Dict

from jgod.research import storage as research_storage
from jgod.api.schemas.intelligence_status import IntelligenceStatusSchema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])


@router.get("/status/latest", response_model=IntelligenceStatusSchema)
async def get_latest_intelligence_status() -> IntelligenceStatusSchema:
    """
    Get the latest intelligence status snapshot.
    Always returns 200, even if no data (returns default empty status).
    """
    try:
        # Get latest drift event (any symbol, or could be filtered)
        drift_event = research_storage.latest_drift_event(symbol=None)
        
        # Build response
        if drift_event:
            drift_score = drift_event.get("drift_score", 0.0)
            drift_level = drift_event.get("drift_level", "LOW")
            drift_updated_at = drift_event.get("created_at")
        else:
            drift_score = 0.0
            drift_level = "LOW"
            drift_updated_at = None
        
        # Get base intelligence status (if exists)
        base_status = research_storage.latest_intelligence_status()
        
        return IntelligenceStatusSchema(
            method_layer_drift_score=drift_score,
            method_layer_drift_status=drift_level,
            method_layer_drift_updated_at=drift_updated_at,
            health_flags=base_status.get("health_flags", {}),
            activities=base_status.get("activities", []),
            created_at=base_status.get("created_at"),
        )
    except Exception as e:
        logger.error(f"Failed to get latest intelligence status: {e}", exc_info=True)
        # Return default empty status on error
        return IntelligenceStatusSchema(
            method_layer_drift_score=0.0,
            method_layer_drift_status="LOW",
            method_layer_drift_updated_at=None,
            health_flags={},
            activities=[],
            created_at=None,
        )

