"""
Execution API Router

v0.6.11-A11: Real-time execution engine API endpoints
"""

import logging
from fastapi import APIRouter, Body
from typing import List
from pydantic import BaseModel

from jgod.execution.engine import ExecutionEngine, ExecutionStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/execution", tags=["execution"])


@router.get("/metrics")
async def get_execution_metrics() -> dict:
    """
    Get execution metrics snapshot.
    
    Always returns 200.
    """
    try:
        engine = ExecutionEngine.get_instance()
        snapshot = engine.metrics_logger.snapshot()
        return {
            "success": True,
            "metrics": snapshot,
        }
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "metrics": {},
        }


@router.get("/alerts")
async def get_execution_alerts(
    level: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """
    Get execution alerts.
    
    Always returns 200.
    """
    try:
        engine = ExecutionEngine.get_instance()
        
        if level:
            alerts = engine.alerting_service.get_alerts(level=level, limit=limit)
        else:
            alerts = engine.alerting_service.get_alerts(limit=limit)
        
        return {
            "success": True,
            "alerts": alerts,
            "total": len(alerts),
        }
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "alerts": [],
        }


class ExecutionStartRequest(BaseModel):
    """Execution start request schema."""
    symbols: List[str]
    tick_interval: float = 5.0
    doctrine_version: str = "v1.0"
    feature_version: str = "v1.0"


@router.post("/start")
async def start_execution(request: ExecutionStartRequest) -> dict:
    """
    Start execution engine.
    
    Always returns 200 (with error field if failed).
    """
    try:
        engine = ExecutionEngine.get_instance()
        success = engine.start(symbols=request.symbols)
        
        if success:
            return {
                "success": True,
                "status": engine.get_status(),
                "message": "Execution engine started",
            }
        else:
            return {
                "success": False,
                "status": engine.get_status(),
                "error": "Execution engine already running",
            }
    except Exception as e:
        logger.error(f"Failed to start execution engine: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/stop")
async def stop_execution() -> dict:
    """
    Stop execution engine.
    
    Always returns 200.
    """
    try:
        engine = ExecutionEngine.get_instance()
        success = engine.stop()
        
        return {
            "success": success,
            "status": engine.get_status(),
            "message": "Execution engine stopped" if success else "Execution engine was not running",
        }
    except Exception as e:
        logger.error(f"Failed to stop execution engine: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


@router.get("/status")
async def get_execution_status() -> dict:
    """
    Get execution engine status.
    
    Always returns 200.
    """
    try:
        engine = ExecutionEngine.get_instance()
        return {
            "success": True,
            "status": engine.get_status(),
        }
    except Exception as e:
        logger.error(f"Failed to get execution status: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "status": {"status": ExecutionStatus.ERROR.value},
        }
