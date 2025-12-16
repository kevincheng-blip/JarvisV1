"""Error Replay API Router

Provides endpoints for error replay functionality.
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
else:
    try:
        from sqlalchemy.orm import Session
    except ImportError:
        # Stub for environments without sqlalchemy
        class Session:
            pass

from jgod.api.schemas.error_replay import ReplayReport
from jgod.replay.engine import ErrorReplayEngineV1
from jgod.replay.data_access import ReplayNotFoundError
from jgod.council_chamber.knowledge_gateway import get_knowledge_brain

# Database dependencies
try:
    from jgod.api.dependencies import get_db
except ImportError:
    try:
        from jgod.storage.db import get_session as get_db
    except ImportError:
        # Fallback: create a dummy get_db
        def get_db():
            yield None

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{error_id}",
    response_model=ReplayReport,
    summary="Get Error Replay Report",
    description="Retrieves a complete replay report for an error event, including "
                "price series, factor data, trade records, and diagnostic analysis."
)
async def get_error_replay(
    error_id: str,
    db: Session = Depends(get_db)
) -> ReplayReport:
    """
    Get error replay report for a specific error event.
    
    Args:
        error_id: Unique identifier for the error event
        db: Database session dependency
    
    Returns:
        ReplayReport object containing all replay data
    
    Raises:
        404: If error event not found
        500: For other internal errors
    """
    try:
        # Initialize replay engine
        knowledge_brain = None
        try:
            knowledge_brain = get_knowledge_brain()
        except Exception as e:
            logger.warning(f"KnowledgeBrain not available: {e}, proceeding without it")
        
        # Get database session (handle generator)
        db_session = db
        if hasattr(db, '__next__'):
            db_session = next(db)
        
        engine = ErrorReplayEngineV1(
            db_session=db_session,
            knowledge_brain=knowledge_brain
        )
        
        # Build replay report
        report = engine.build_replay_report(error_id)
        
        logger.info(f"Successfully built replay report for error {error_id}")
        return report
    
    except ReplayNotFoundError as e:
        logger.warning(f"Error event not found: {error_id}")
        raise HTTPException(status_code=404, detail=f"Error event not found: {error_id}")
    
    except Exception as e:
        logger.error(f"Error building replay report for {error_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

