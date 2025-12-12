"""
Decision V3 API Router

Provides endpoints for Decision Engine V3.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from jgod.api.schemas.decision_v3 import (
    DecisionV3ResponseSchema,
    result_to_schema,
)
from jgod.api.schemas.decision_v3_snapshot import (
    DecisionV3SnapshotResponseSchema,
    DecisionV3SnapshotListResponseSchema,
    snapshot_to_response_schema,
    snapshot_list_to_response_schema,
)
from jgod.decision_v3.engine import DecisionEngineV3
from jgod.decision_v3.service import (
    compute_decision,
    recompute_and_save,
    get_latest_snapshot,
    list_snapshots,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/decide/{symbol}",
    response_model=DecisionV3ResponseSchema,
    summary="Get Decision V3 for symbol",
    description="取得 Decision V3 決策結果（Rule-based × S-Rank V2 × Performance Feed）",
)
async def get_decision_v3(
    symbol: str,
    mode: str = Query("performance", description="Decision mode: 'performance' or 'signals'"),
    limit: int = Query(60, ge=1, le=200, description="Number of timeline items to use"),
    k: int = Query(5, ge=1, le=10, description="Number of top strategies to recommend"),
) -> DecisionV3ResponseSchema:
    """Get Decision V3 for a symbol (always returns 200, never 404)"""
    try:
        engine = DecisionEngineV3()
        result = engine.decide(symbol, mode, limit, k)
        return result_to_schema(result)
    except Exception as e:
        logger.error(f"Error getting Decision V3 for {symbol}: {e}", exc_info=True)
        # Even on error, return a valid response (RISK_OFF)
        from jgod.decision_v3.models import DecisionV3Result, RiskPlan
        error_result = DecisionV3Result(
            symbol=symbol,
            risk_plan=RiskPlan(
                position_scale=0.20,
                risk_state="RISK_OFF",
                reasons=["系統錯誤"],
            ),
            confidence=0.0,
            explain=f"無法為 {symbol} 產生決策：系統發生錯誤。請稍後再試。",
        )
        return result_to_schema(error_result)


@router.post(
    "/recompute/{symbol}",
    response_model=DecisionV3SnapshotResponseSchema,
    summary="Recompute and save Decision V3 snapshot",
    description="重新計算並存檔 Decision V3 決策快照",
)
async def recompute_decision_v3(
    symbol: str,
    mode: str = Query("performance", description="Decision mode: 'performance' or 'signals'"),
    limit: int = Query(60, ge=1, le=200, description="Number of timeline items to use"),
    k: int = Query(5, ge=1, le=10, description="Number of top strategies to recommend"),
) -> DecisionV3SnapshotResponseSchema:
    """Recompute decision and save as snapshot (always returns 200)"""
    try:
        snapshot = recompute_and_save(symbol, mode, limit, k)
        return snapshot_to_response_schema(snapshot)
    except Exception as e:
        logger.error(f"Error recomputing Decision V3 for {symbol}: {e}", exc_info=True)
        # Even on error, return a valid response (empty snapshot)
        from jgod.decision_v3.models import DecisionV3Result, RiskPlan
        error_result = DecisionV3Result(
            symbol=symbol,
            risk_plan=RiskPlan(
                position_scale=0.20,
                risk_state="RISK_OFF",
                reasons=["系統錯誤"],
            ),
            confidence=0.0,
            explain=f"無法為 {symbol} 產生決策：系統發生錯誤。請稍後再試。",
        )
        error_snapshot = {
            "snapshot_id": "",
            "created_at": datetime.now(),
            "symbol": symbol,
            "mode": mode,
            "limit": limit,
            "k": k,
            "result": {
                "symbol": symbol,
                "selected_primary_strategy": None,
                "selected_secondary_strategies": [],
                "weights": [],
                "risk_plan": {
                    "position_scale": 0.20,
                    "risk_state": "RISK_OFF",
                    "reasons": ["系統錯誤"],
                },
                "confidence": 0.0,
                "explain": f"無法為 {symbol} 產生決策：系統發生錯誤。請稍後再試。",
            },
        }
        return snapshot_to_response_schema(error_snapshot)


@router.get(
    "/latest/{symbol}",
    response_model=DecisionV3SnapshotResponseSchema,
    summary="Get latest Decision V3 snapshot for symbol",
    description="讀取最新存檔的 Decision V3 決策快照",
)
async def get_latest_decision_v3(
    symbol: str,
) -> DecisionV3SnapshotResponseSchema:
    """Get latest saved snapshot for a symbol (always returns 200, never 404)"""
    try:
        snapshot = get_latest_snapshot(symbol)
        
        if not snapshot:
            # Return empty snapshot (NO_DATA) - still 200
            from jgod.decision_v3.models import DecisionV3Result, RiskPlan
            empty_result = DecisionV3Result(
                symbol=symbol,
                risk_plan=RiskPlan(
                    position_scale=0.20,
                    risk_state="RISK_OFF",
                    reasons=["暫無快照資料"],
                ),
                confidence=0.0,
                explain=f"目前 {symbol} 暫無存檔的決策快照。請使用 recompute 端點產生快照。",
            )
            empty_snapshot = {
                "snapshot_id": "",
                "created_at": datetime.now(),
                "symbol": symbol,
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "result": {
                    "symbol": symbol,
                    "selected_primary_strategy": None,
                    "selected_secondary_strategies": [],
                    "weights": [],
                    "risk_plan": {
                        "position_scale": 0.20,
                        "risk_state": "RISK_OFF",
                        "reasons": ["暫無快照資料"],
                    },
                    "confidence": 0.0,
                    "explain": f"目前 {symbol} 暫無存檔的決策快照。請使用 recompute 端點產生快照。",
                },
            }
            return snapshot_to_response_schema(empty_snapshot)
        
        return snapshot_to_response_schema(snapshot)
    except Exception as e:
        logger.error(f"Error getting latest Decision V3 snapshot for {symbol}: {e}", exc_info=True)
        # Even on error, return a valid response
        empty_snapshot = {
            "snapshot_id": "",
            "created_at": datetime.now(),
            "symbol": symbol,
            "mode": "performance",
            "limit": 60,
            "k": 5,
            "result": {
                "symbol": symbol,
                "selected_primary_strategy": None,
                "selected_secondary_strategies": [],
                "weights": [],
                "risk_plan": {
                    "position_scale": 0.20,
                    "risk_state": "RISK_OFF",
                    "reasons": ["系統錯誤"],
                },
                "confidence": 0.0,
                "explain": f"無法讀取 {symbol} 的決策快照：系統發生錯誤。",
            },
        }
        return snapshot_to_response_schema(empty_snapshot)


@router.get(
    "/list/{symbol}",
    response_model=DecisionV3SnapshotListResponseSchema,
    summary="List Decision V3 snapshots for symbol",
    description="列出指定股票的 Decision V3 決策快照列表",
)
async def list_decision_v3_snapshots(
    symbol: str,
    n: int = Query(20, ge=1, le=100, description="Maximum number of snapshots to return"),
) -> DecisionV3SnapshotListResponseSchema:
    """List snapshots for a symbol (always returns 200, empty list if no snapshots)"""
    try:
        snapshots = list_snapshots(symbol, n)
        return snapshot_list_to_response_schema(snapshots, symbol)
    except Exception as e:
        logger.error(f"Error listing Decision V3 snapshots for {symbol}: {e}", exc_info=True)
        # Even on error, return empty list - still 200
        return DecisionV3SnapshotListResponseSchema(
            symbol=symbol,
            items=[],
            total=0,
        )

