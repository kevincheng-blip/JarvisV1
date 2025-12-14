"""
Execution API Router

Endpoints for virtual ledger and order simulation.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Query
from typing import Optional

from jgod.api.schemas.execution import (
    LedgerResponseSchema,
    ExecutionSimulateResponseSchema,
    LedgerSnapshotSchema,
    OrderRequestSchema,
)
from jgod.execution.service import (
    get_latest_ledger,
    recompute_ledger,
    simulate_order_from_latest_decision,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["execution"])


@router.get(
    "/ledger/latest/{symbol}",
    response_model=LedgerResponseSchema,
    summary="Get Latest Ledger",
    description="Get the latest ledger snapshot for a symbol (always returns 200, default ledger if no data)",
)
async def get_ledger_latest(
    symbol: str,
) -> LedgerResponseSchema:
    """Get latest ledger snapshot (always returns 200, default if no data)"""
    try:
        snapshot = get_latest_ledger(symbol)
        
        return LedgerResponseSchema(
            snapshot_id=snapshot.get("snapshot_id", ""),
            created_at=snapshot.get("created_at", datetime.now().isoformat()),
            symbol=snapshot.get("symbol", symbol),
            ledger=LedgerSnapshotSchema(**snapshot.get("ledger", {})),
            is_default=snapshot.get("is_default", False),
        )
    except Exception as e:
        logger.error(f"Error getting ledger for {symbol}: {e}", exc_info=True)
        # Return default on error - still 200
        return LedgerResponseSchema(
            snapshot_id="",
            created_at=datetime.now().isoformat(),
            symbol=symbol,
            ledger=LedgerSnapshotSchema(
                symbol=symbol,
                cash=1_000_000.0,
            ),
            is_default=True,
        )


@router.post(
    "/ledger/recompute/{symbol}",
    response_model=LedgerResponseSchema,
    summary="Recompute Ledger",
    description="Create and save a fresh ledger snapshot (reset)",
)
async def recompute_ledger_endpoint(
    symbol: str,
    initial_cash: float = Query(1_000_000.0, ge=0, description="Initial cash amount"),
) -> LedgerResponseSchema:
    """Recompute ledger and save snapshot (always returns 200)"""
    try:
        snapshot = recompute_ledger(symbol, initial_cash)
        
        return LedgerResponseSchema(
            snapshot_id=snapshot.get("snapshot_id", ""),
            created_at=snapshot.get("created_at", datetime.now().isoformat()),
            symbol=snapshot.get("symbol", symbol),
            ledger=LedgerSnapshotSchema(**snapshot.get("ledger", {})),
            is_default=snapshot.get("is_default", False),
        )
    except Exception as e:
        logger.error(f"Error recomputing ledger for {symbol}: {e}", exc_info=True)
        # Return default on error - still 200
        return LedgerResponseSchema(
            snapshot_id="",
            created_at=datetime.now().isoformat(),
            symbol=symbol,
            ledger=LedgerSnapshotSchema(
                symbol=symbol,
                cash=initial_cash,
            ),
            is_default=True,
        )


@router.post(
    "/order/simulate/{symbol}",
    response_model=ExecutionSimulateResponseSchema,
    summary="Simulate Order",
    description="Simulate order generation from latest Decision V3 (always returns 200)",
)
async def simulate_order(
    symbol: str,
    mode: str = Query("performance", description="Decision mode: 'performance' or 'signals'"),
    limit: int = Query(60, ge=10, le=200, description="Number of timeline items to fetch"),
    k: int = Query(5, ge=1, le=10, description="Number of top strategies to consider"),
) -> ExecutionSimulateResponseSchema:
    """Simulate order from latest Decision V3 (always returns 200)"""
    try:
        result = simulate_order_from_latest_decision(symbol, mode, limit, k)
        
        return ExecutionSimulateResponseSchema(
            symbol=result.get("symbol", symbol),
            ledger=LedgerSnapshotSchema(**result.get("ledger", {})),
            decision_v3=result.get("decision_v3", {}),
            order_request=OrderRequestSchema(**result.get("order_request", {})),
            price=result.get("price", 0.0),
            has_data=result.get("has_data", False),
        )
    except Exception as e:
        logger.error(f"Error simulating order for {symbol}: {e}", exc_info=True)
        # Return empty state on error - still 200
        return ExecutionSimulateResponseSchema(
            symbol=symbol,
            ledger=LedgerSnapshotSchema(
                symbol=symbol,
                cash=1_000_000.0,
            ),
            decision_v3={},
            order_request=OrderRequestSchema(
                symbol=symbol,
                side="HOLD",
                qty=0,
                reason=f"計算失敗：{str(e)}",
                target_position_scale=0.0,
                current_position_scale=0.0,
            ),
            price=0.0,
            has_data=False,
        )

