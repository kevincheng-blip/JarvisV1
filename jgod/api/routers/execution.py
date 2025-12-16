"""
Execution API Router

v0.6.11-A11: Real-time execution engine API endpoints
v0.6.5-A6: VirtualLedger endpoints for execution grounding
"""

import logging
from fastapi import APIRouter, Body
from typing import List, Optional
from pydantic import BaseModel

from jgod.execution.engine import ExecutionEngine, ExecutionStatus
from jgod.execution.service import get_latest_ledger, recompute_ledger, simulate_order_from_latest_decision
from jgod.api.schemas.execution import LedgerResponseSchema, ExecutionSimulateResponseSchema

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


# v0.6.5-A6: VirtualLedger endpoints for execution grounding

@router.get("/ledger/latest/{symbol}", response_model=LedgerResponseSchema)
async def get_ledger_latest(symbol: str, initial_cash: float = 1_000_000.0) -> LedgerResponseSchema:
    """
    Get latest ledger snapshot for a symbol.
    
    Returns default empty ledger if no snapshots exist (200 OK, never 404).
    
    Args:
        symbol: Stock symbol
        initial_cash: Initial cash for default ledger (if no snapshot exists)
        
    Returns:
        LedgerResponseSchema with ledger snapshot or default ledger
    """
    try:
        snapshot = get_latest_ledger(symbol, initial_cash)
        return LedgerResponseSchema(**snapshot)
    except Exception as e:
        logger.error(f"Failed to get ledger latest for {symbol}: {e}", exc_info=True)
        # Return default ledger on error
        from jgod.execution.virtual_ledger import VirtualLedger
        from datetime import datetime
        ledger = VirtualLedger(symbol=symbol, cash=initial_cash)
        ledger.mark_to_market(symbol, 100.0)
        return LedgerResponseSchema(
            snapshot_id="",
            created_at=datetime.now().isoformat(),
            symbol=symbol,
            ledger=ledger.snapshot(symbol),
            is_default=True,
        )


@router.post("/ledger/recompute/{symbol}", response_model=LedgerResponseSchema)
async def post_ledger_recompute(symbol: str, initial_cash: float = 1_000_000.0) -> LedgerResponseSchema:
    """
    Recompute (reset) ledger for a symbol and save snapshot.
    
    Always returns 200 OK.
    
    Args:
        symbol: Stock symbol
        initial_cash: Initial cash amount
        
    Returns:
        LedgerResponseSchema with new snapshot
    """
    try:
        snapshot = recompute_ledger(symbol, initial_cash)
        return LedgerResponseSchema(**snapshot)
    except Exception as e:
        logger.error(f"Failed to recompute ledger for {symbol}: {e}", exc_info=True)
        # Return default ledger on error
        from jgod.execution.virtual_ledger import VirtualLedger
        from datetime import datetime
        ledger = VirtualLedger(symbol=symbol, cash=initial_cash)
        ledger.mark_to_market(symbol, 100.0)
        return LedgerResponseSchema(
            snapshot_id="",
            created_at=datetime.now().isoformat(),
            symbol=symbol,
            ledger=ledger.snapshot(symbol),
            is_default=True,
        )


@router.post("/order/simulate/{symbol}", response_model=ExecutionSimulateResponseSchema)
async def post_order_simulate(
    symbol: str,
    mode: str = "performance",
    limit: int = 60,
    k: int = 5
) -> ExecutionSimulateResponseSchema:
    """
    Simulate order from latest Decision V3 snapshot.
    
    Always returns 200 OK (even if no data, returns HOLD order).
    
    Args:
        symbol: Stock symbol
        mode: Decision mode (default: "performance")
        limit: Timeline limit (default: 60)
        k: Number of top strategies (default: 5)
        
    Returns:
        ExecutionSimulateResponseSchema with ledger, decision, and order request
    """
    try:
        result = simulate_order_from_latest_decision(symbol, mode, limit, k)
        return ExecutionSimulateResponseSchema(**result)
    except Exception as e:
        logger.error(f"Failed to simulate order for {symbol}: {e}", exc_info=True)
        # Return default response on error
        from jgod.execution.virtual_ledger import VirtualLedger
        from datetime import datetime
        ledger = VirtualLedger(symbol=symbol, cash=1_000_000.0)
        ledger.mark_to_market(symbol, 100.0)
        return ExecutionSimulateResponseSchema(
            symbol=symbol,
            ledger=ledger.snapshot(symbol),
            decision_v3={},
            order_request={
                "symbol": symbol,
                "side": "HOLD",
                "qty": 0,
                "reason": f"模擬失敗：{str(e)}",
                "target_position_scale": 0.0,
                "current_position_scale": 0.0,
            },
            price=100.0,
            has_data=False,
        )
