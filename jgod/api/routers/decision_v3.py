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
from jgod.api.schemas.decision_v3_eval import (
    DecisionV3EvalSnapshotResponseSchema,
    DecisionV3EvalListResponseSchema,
    eval_snapshot_to_response_schema,
    eval_list_to_response_schema,
)
from jgod.api.schemas.decision_v3_compare import (
    CompareSnapshotResponseSchema,
    CompareListResponseSchema,
    compare_snapshot_to_response_schema,
    compare_list_to_response_schema,
)
from jgod.api.schemas.decision_v3_arena import (
    ArenaResponseSchema,
    ArenaSnapshotResponseSchema,
    ArenaListResponseSchema,
    arena_snapshot_to_response,
    arena_result_to_schema,
)
from jgod.decision_v3.engine import DecisionEngineV3
from jgod.decision_v3.service import (
    compute_decision,
    recompute_and_save,
    get_latest_snapshot,
    list_snapshots,
    recompute_evaluation_and_save,
    get_latest_evaluation,
    list_evaluation_snapshots,
    recompute_compare_and_save,
    get_latest_compare,
    list_compare_snapshots,
    recompute_arena_and_save,
    get_latest_arena,
    list_arena_snapshots as service_list_arena_snapshots,
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


# Evaluation endpoints

@router.post(
    "/eval/recompute/{symbol}",
    response_model=DecisionV3EvalSnapshotResponseSchema,
    summary="Recompute and save Decision V3 evaluation",
    description="重新計算並存檔 Decision V3 評估快照",
)
async def recompute_decision_v3_eval(
    symbol: str,
    mode: str = Query("performance", description="Decision mode: 'performance' or 'signals'"),
    limit: int = Query(60, ge=1, le=200, description="Number of timeline items to use"),
    k: int = Query(5, ge=1, le=10, description="Number of top strategies to recommend"),
    window: int = Query(20, ge=5, le=100, description="Evaluation window size"),
) -> DecisionV3EvalSnapshotResponseSchema:
    """Recompute evaluation and save as snapshot (always returns 200)"""
    try:
        snapshot = recompute_evaluation_and_save(symbol, mode, limit, k, window)
        return eval_snapshot_to_response_schema(snapshot)
    except Exception as e:
        logger.error(f"Error recomputing Decision V3 evaluation for {symbol}: {e}", exc_info=True)
        # Even on error, return a valid response (NO_DATA)
        from jgod.decision_v3.evaluation import EvaluationVerdict
        error_snapshot = {
            "eval_id": "",
            "created_at": datetime.now(),
            "symbol": symbol,
            "mode": mode,
            "limit": limit,
            "k": k,
            "window": window,
            "evaluation": {
                "symbol": symbol,
                "mode": mode,
                "limit": limit,
                "k": k,
                "window": window,
                "decision": {
                    "primary_strategy": None,
                    "risk_plan": {
                        "position_scale": 0.20,
                        "risk_state": "RISK_OFF",
                    },
                    "confidence": 0.0,
                },
                "inputs_summary": {
                    "mode": mode,
                    "limit": limit,
                    "k": k,
                    "stability_grade": "NO_DATA",
                    "perf_grade": "NO_DATA",
                },
                "metrics": {
                    "n_points": 0,
                    "hit_rate_proxy": 0.0,
                    "avg_return_proxy": 0.0,
                    "max_drawdown_proxy": 0.0,
                    "turnover_proxy": 0.0,
                    "decision_consistency": 0.0,
                    "verdict": EvaluationVerdict.NO_DATA,
                    "recommendation_next_step": f"無法為 {symbol} 產生評估：系統發生錯誤。請稍後再試。",
                },
            },
        }
        return eval_snapshot_to_response_schema(error_snapshot)


@router.get(
    "/eval/latest/{symbol}",
    response_model=DecisionV3EvalSnapshotResponseSchema,
    summary="Get latest Decision V3 evaluation for symbol",
    description="讀取最新存檔的 Decision V3 評估快照",
)
async def get_latest_decision_v3_eval(
    symbol: str,
) -> DecisionV3EvalSnapshotResponseSchema:
    """Get latest saved evaluation for a symbol (always returns 200, never 404)"""
    try:
        snapshot = get_latest_evaluation(symbol)
        
        if not snapshot:
            # Return empty snapshot (NO_DATA) - still 200
            from jgod.decision_v3.evaluation import EvaluationVerdict
            empty_snapshot = {
                "eval_id": "",
                "created_at": datetime.now(),
                "symbol": symbol,
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "window": 20,
                "evaluation": {
                    "symbol": symbol,
                    "mode": "performance",
                    "limit": 60,
                    "k": 5,
                    "window": 20,
                    "decision": {
                        "primary_strategy": None,
                        "risk_plan": {
                            "position_scale": 0.20,
                            "risk_state": "RISK_OFF",
                        },
                        "confidence": 0.0,
                    },
                    "inputs_summary": {
                        "mode": "performance",
                        "limit": 60,
                        "k": 5,
                        "stability_grade": "NO_DATA",
                        "perf_grade": "NO_DATA",
                    },
                    "metrics": {
                        "n_points": 0,
                        "hit_rate_proxy": 0.0,
                        "avg_return_proxy": 0.0,
                        "max_drawdown_proxy": 0.0,
                        "turnover_proxy": 0.0,
                        "decision_consistency": 0.0,
                        "verdict": EvaluationVerdict.NO_DATA,
                        "recommendation_next_step": f"目前 {symbol} 暫無存檔的評估快照。請使用 recompute 端點產生快照。",
                    },
                },
            }
            return eval_snapshot_to_response_schema(empty_snapshot)
        
        return eval_snapshot_to_response_schema(snapshot)
    except Exception as e:
        logger.error(f"Error getting latest Decision V3 evaluation for {symbol}: {e}", exc_info=True)
        # Even on error, return a valid response
        from jgod.decision_v3.evaluation import EvaluationVerdict
        empty_snapshot = {
            "eval_id": "",
            "created_at": datetime.now(),
            "symbol": symbol,
            "mode": "performance",
            "limit": 60,
            "k": 5,
            "window": 20,
            "evaluation": {
                "symbol": symbol,
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "window": 20,
                "decision": {
                    "primary_strategy": None,
                    "risk_plan": {
                        "position_scale": 0.20,
                        "risk_state": "RISK_OFF",
                    },
                    "confidence": 0.0,
                },
                "inputs_summary": {
                    "mode": "performance",
                    "limit": 60,
                    "k": 5,
                    "stability_grade": "NO_DATA",
                    "perf_grade": "NO_DATA",
                },
                "metrics": {
                    "n_points": 0,
                    "hit_rate_proxy": 0.0,
                    "avg_return_proxy": 0.0,
                    "max_drawdown_proxy": 0.0,
                    "turnover_proxy": 0.0,
                    "decision_consistency": 0.0,
                    "verdict": EvaluationVerdict.NO_DATA,
                    "recommendation_next_step": f"無法讀取 {symbol} 的評估快照：系統發生錯誤。",
                },
            },
        }
        return eval_snapshot_to_response_schema(empty_snapshot)


@router.get(
    "/eval/list/{symbol}",
    response_model=DecisionV3EvalListResponseSchema,
    summary="List Decision V3 evaluations for symbol",
    description="列出指定股票的 Decision V3 評估快照列表",
)
async def list_decision_v3_evaluations(
    symbol: str,
    n: int = Query(20, ge=1, le=100, description="Maximum number of evaluations to return"),
) -> DecisionV3EvalListResponseSchema:
    """List evaluations for a symbol (always returns 200, empty list if no evaluations)"""
    try:
        snapshots = list_evaluation_snapshots(symbol, n)
        return eval_list_to_response_schema(snapshots, symbol)
    except Exception as e:
        logger.error(f"Error listing Decision V3 evaluations for {symbol}: {e}", exc_info=True)
        # Even on error, return empty list - still 200
        return DecisionV3EvalListResponseSchema(
            symbol=symbol,
            items=[],
            total=0,
        )


# Compare endpoints

@router.post(
    "/compare/recompute/{symbol}",
    response_model=CompareSnapshotResponseSchema,
    summary="Recompute and save Decision V3 compare snapshot",
    description="重新計算並存檔 Decision V3 對照評估快照（V3 vs Baseline）",
)
async def recompute_decision_v3_compare(
    symbol: str,
    mode: str = Query("performance", description="Decision mode: 'performance' or 'signals'"),
    limit: int = Query(60, ge=1, le=200, description="Number of timeline items to use"),
    k: int = Query(5, ge=1, le=10, description="Number of top strategies to recommend"),
    window: int = Query(20, ge=5, le=100, description="Evaluation window size"),
) -> CompareSnapshotResponseSchema:
    """Recompute compare and save as snapshot (always returns 200)"""
    try:
        snapshot = recompute_compare_and_save(symbol, mode, limit, k, window)
        return compare_snapshot_to_response_schema(snapshot)
    except Exception as e:
        logger.error(f"Error recomputing Decision V3 compare for {symbol}: {e}", exc_info=True)
        # Even on error, return a valid response (NO_DATA)
        from jgod.decision_v3.compare import CompareWinner
        error_snapshot = {
            "compare_id": "",
            "created_at": datetime.now(),
            "symbol": symbol,
            "mode": mode,
            "limit": limit,
            "k": k,
            "window": window,
            "compare": {
                "symbol": symbol,
                "mode": mode,
                "limit": limit,
                "k": k,
                "window": window,
                "winner": CompareWinner.NO_DATA,
                "delta_metrics": {
                    "hit_rate_proxy": 0.0,
                    "avg_return_proxy": 0.0,
                    "max_drawdown_proxy": 0.0,
                    "turnover_proxy": 0.0,
                    "decision_consistency": 0.0,
                },
                "summary": f"無法為 {symbol} 產生對照評估：系統發生錯誤。請稍後再試。",
                "recommendation_next_step": "請檢查系統狀態後重試。",
            },
        }
        return compare_snapshot_to_response_schema(error_snapshot)


@router.get(
    "/compare/latest/{symbol}",
    response_model=CompareSnapshotResponseSchema,
    summary="Get latest Decision V3 compare for symbol",
    description="讀取最新存檔的 Decision V3 對照評估快照",
)
async def get_latest_decision_v3_compare(
    symbol: str,
) -> CompareSnapshotResponseSchema:
    """Get latest saved compare for a symbol (always returns 200, never 404)"""
    try:
        snapshot = get_latest_compare(symbol)
        
        if not snapshot:
            # Return empty snapshot (NO_DATA) - still 200
            from jgod.decision_v3.compare import CompareWinner
            empty_snapshot = {
                "compare_id": "",
                "created_at": datetime.now(),
                "symbol": symbol,
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "window": 20,
                "compare": {
                    "symbol": symbol,
                    "mode": "performance",
                    "limit": 60,
                    "k": 5,
                    "window": 20,
                    "winner": CompareWinner.NO_DATA,
                    "delta_metrics": {
                        "hit_rate_proxy": 0.0,
                        "avg_return_proxy": 0.0,
                        "max_drawdown_proxy": 0.0,
                        "turnover_proxy": 0.0,
                        "decision_consistency": 0.0,
                    },
                    "summary": f"目前 {symbol} 暫無存檔的對照評估快照。請使用 recompute 端點產生快照。",
                    "recommendation_next_step": "請使用 recompute 端點產生對照評估。",
                },
            }
            return compare_snapshot_to_response_schema(empty_snapshot)
        
        return compare_snapshot_to_response_schema(snapshot)
    except Exception as e:
        logger.error(f"Error getting latest Decision V3 compare for {symbol}: {e}", exc_info=True)
        # Even on error, return a valid response
        from jgod.decision_v3.compare import CompareWinner
        empty_snapshot = {
            "compare_id": "",
            "created_at": datetime.now(),
            "symbol": symbol,
            "mode": "performance",
            "limit": 60,
            "k": 5,
            "window": 20,
            "compare": {
                "symbol": symbol,
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "window": 20,
                "winner": CompareWinner.NO_DATA,
                "delta_metrics": {
                    "hit_rate_proxy": 0.0,
                    "avg_return_proxy": 0.0,
                    "max_drawdown_proxy": 0.0,
                    "turnover_proxy": 0.0,
                    "decision_consistency": 0.0,
                },
                "summary": f"無法讀取 {symbol} 的對照評估快照：系統發生錯誤。",
                "recommendation_next_step": "請檢查系統狀態後重試。",
            },
        }
        return compare_snapshot_to_response_schema(empty_snapshot)


@router.get(
    "/compare/list/{symbol}",
    response_model=CompareListResponseSchema,
    summary="List Decision V3 compares for symbol",
    description="列出指定股票的 Decision V3 對照評估快照列表",
)
async def list_decision_v3_compares(
    symbol: str,
    n: int = Query(20, ge=1, le=100, description="Maximum number of compares to return"),
) -> CompareListResponseSchema:
    """List compares for a symbol (always returns 200, empty list if no compares)"""
    try:
        snapshots = list_compare_snapshots(symbol, n)
        return compare_list_to_response_schema(snapshots, symbol)
    except Exception as e:
        logger.error(f"Error listing Decision V3 compares for {symbol}: {e}", exc_info=True)
        # Even on error, return empty list - still 200
        return CompareListResponseSchema(
            symbol=symbol,
            items=[],
            total=0,
        )


# Arena endpoints

@router.post(
    "/arena/recompute/{symbol}",
    response_model=ArenaResponseSchema,
    summary="Recompute Decision V3 Arena",
    description="Recompute arena comparison (multi-challenger + auto-tuning) for a symbol",
)
async def recompute_arena(
    symbol: str,
    mode: str = Query("performance", description="Decision mode: 'performance' or 'signals'"),
    limit: int = Query(60, ge=10, le=200, description="Number of timeline items to fetch"),
    k: int = Query(5, ge=1, le=10, description="Number of top strategies to consider"),
    window: int = Query(20, ge=5, le=60, description="Evaluation window size"),
) -> ArenaResponseSchema:
    """Recompute arena comparison and save snapshot (always returns 200)"""
    try:
        snapshot = recompute_arena_and_save(symbol, mode, limit, k, window)
        
        # Wrap for response
        arena_data = snapshot.copy()
        arena_data.pop("arena_id", None)
        arena_data.pop("created_at", None)
        
        return ArenaResponseSchema(
            arena_id=snapshot.get("arena_id", ""),
            created_at=snapshot.get("created_at", ""),
            symbol=snapshot.get("symbol", symbol),
            mode=snapshot.get("mode", mode),
            window=snapshot.get("window", window),
            limit=snapshot.get("limit", limit),
            k=snapshot.get("k", k),
            arena=arena_result_to_schema(arena_data),
        )
    except Exception as e:
        logger.error(f"Error recomputing Decision V3 arena for {symbol}: {e}", exc_info=True)
        # Return empty state on error - still 200
        return ArenaResponseSchema(
            arena_id="",
            created_at=datetime.now().isoformat(),
            symbol=symbol,
            mode=mode,
            window=window,
            limit=limit,
            k=k,
            arena=arena_result_to_schema({
                "symbol": symbol,
                "mode": mode,
                "window": window,
                "limit": limit,
                "k": k,
                "scoreboard": [],
                "winner_id": "NO_DATA",
                "is_regression": False,
                "summary": f"計算失敗：{str(e)}",
                "recommendation_next_step": "請檢查資料或稍後重試",
            }),
        )


@router.get(
    "/arena/latest/{symbol}",
    response_model=ArenaSnapshotResponseSchema,
    summary="Get Latest Decision V3 Arena",
    description="Get the latest arena snapshot for a symbol (always returns 200, empty state if no data)",
)
async def get_arena_latest(
    symbol: str,
) -> ArenaSnapshotResponseSchema:
    """Get latest arena snapshot (always returns 200, empty state if no data)"""
    try:
        snapshot = get_latest_arena(symbol)
        if not snapshot:
            # Return empty state - still 200
            return ArenaSnapshotResponseSchema(
                arena_id="",
                created_at=datetime.now().isoformat(),
                symbol=symbol,
                mode="performance",
                window=20,
                limit=60,
                k=5,
                arena=arena_result_to_schema({
                    "symbol": symbol,
                    "mode": "performance",
                    "window": 20,
                    "limit": 60,
                    "k": 5,
                    "scoreboard": [],
                    "winner_id": "NO_DATA",
                    "is_regression": False,
                    "summary": "暫無競技場資料",
                    "recommendation_next_step": "請先執行 recompute 產生競技場對照",
                }),
            )
        
        return arena_snapshot_to_response(snapshot)
    except Exception as e:
        logger.error(f"Error getting latest Decision V3 arena for {symbol}: {e}", exc_info=True)
        # Return empty state on error - still 200
        return ArenaSnapshotResponseSchema(
            arena_id="",
            created_at=datetime.now().isoformat(),
            symbol=symbol,
            mode="performance",
            window=20,
            limit=60,
            k=5,
            arena=arena_result_to_schema({
                "symbol": symbol,
                "mode": "performance",
                "window": 20,
                "limit": 60,
                "k": 5,
                "scoreboard": [],
                "winner_id": "NO_DATA",
                "is_regression": False,
                "summary": f"讀取失敗：{str(e)}",
                "recommendation_next_step": "請稍後重試",
            }),
        )


@router.get(
    "/arena/list/{symbol}",
    response_model=ArenaListResponseSchema,
    summary="List Decision V3 Arena Snapshots",
    description="List arena snapshots for a symbol (always returns 200, empty list if no data)",
)
def list_arena_snapshots(
    symbol: str,
    n: int = Query(20, ge=1, le=100, description="Maximum number of arena snapshots to return"),
) -> ArenaListResponseSchema:
    """List arena snapshots for a symbol (always returns 200, empty list if no snapshots)"""
    try:
        snapshots = service_list_arena_snapshots(symbol, n)
        
        items = []
        for snapshot in snapshots:
            created_at = snapshot.get("created_at", "")
            if isinstance(created_at, datetime):
                created_at = created_at.isoformat()
            elif not isinstance(created_at, str):
                created_at = datetime.now().isoformat()
            
            items.append({
                "arena_id": snapshot.get("arena_id", ""),
                "created_at": created_at,
                "winner_id": snapshot.get("winner_id", "NO_DATA"),
                "is_regression": snapshot.get("is_regression", False),
            })
        
        return ArenaListResponseSchema(
            symbol=symbol,
            total=len(items),
            items=items,
        )
    except Exception as e:
        logger.error(f"Error listing Decision V3 arena for {symbol}: {e}", exc_info=True)
        # Even on error, return empty list - still 200
        return ArenaListResponseSchema(
            symbol=symbol,
            items=[],
            total=0,
        )

