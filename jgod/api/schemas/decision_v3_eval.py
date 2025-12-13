"""
Decision V3 Evaluation API Schemas

Pydantic schemas for Decision V3 evaluation endpoints.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class DecisionV3EvalMetricsSchema(BaseModel):
    """Evaluation metrics"""
    n_points: int
    hit_rate_proxy: float
    avg_return_proxy: float
    max_drawdown_proxy: float
    turnover_proxy: float
    decision_consistency: float
    verdict: str  # IMPROVED | NEUTRAL | REGRESSED | NO_DATA
    recommendation_next_step: str

    class Config:
        json_schema_extra = {
            "example": {
                "n_points": 45,
                "hit_rate_proxy": 0.58,
                "avg_return_proxy": 0.012,
                "max_drawdown_proxy": 0.15,
                "turnover_proxy": 0.08,
                "decision_consistency": 0.75,
                "verdict": "IMPROVED",
                "recommendation_next_step": "決策表現良好，建議維持當前策略配置。",
            }
        }


class DecisionV3EvalResponseSchema(BaseModel):
    """Evaluation response schema"""
    symbol: str
    mode: str
    limit: int
    k: int
    window: int
    decision: dict
    inputs_summary: dict
    metrics: DecisionV3EvalMetricsSchema

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "2330",
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "window": 20,
                "decision": {
                    "primary_strategy": "trend_follow",
                    "risk_plan": {
                        "position_scale": 0.80,
                        "risk_state": "RISK_ON",
                    },
                    "confidence": 0.75,
                },
                "inputs_summary": {
                    "mode": "performance",
                    "limit": 60,
                    "k": 5,
                    "stability_grade": "STABLE",
                    "perf_grade": "GOOD",
                },
                "metrics": {
                    "n_points": 45,
                    "hit_rate_proxy": 0.58,
                    "avg_return_proxy": 0.012,
                    "max_drawdown_proxy": 0.15,
                    "turnover_proxy": 0.08,
                    "decision_consistency": 0.75,
                    "verdict": "IMPROVED",
                    "recommendation_next_step": "決策表現良好，建議維持當前策略配置。",
                },
            }
        }


class DecisionV3EvalSnapshotResponseSchema(BaseModel):
    """Evaluation snapshot response schema"""
    eval_id: str
    created_at: str
    symbol: str
    mode: str
    limit: int
    k: int
    window: int
    evaluation: DecisionV3EvalResponseSchema

    class Config:
        json_schema_extra = {
            "example": {
                "eval_id": "abc-123-def",
                "created_at": "2025-12-13T10:00:00",
                "symbol": "2330",
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "window": 20,
                "evaluation": {
                    "symbol": "2330",
                    "mode": "performance",
                    "limit": 60,
                    "k": 5,
                    "window": 20,
                    "decision": {},
                    "inputs_summary": {},
                    "metrics": {},
                },
            }
        }


class DecisionV3EvalListItemSchema(BaseModel):
    """Evaluation list item schema"""
    eval_id: str
    created_at: str
    symbol: str
    verdict: str
    metrics_summary: dict

    class Config:
        json_schema_extra = {
            "example": {
                "eval_id": "abc-123-def",
                "created_at": "2025-12-13T10:00:00",
                "symbol": "2330",
                "verdict": "IMPROVED",
                "metrics_summary": {
                    "hit_rate_proxy": 0.58,
                    "avg_return_proxy": 0.012,
                },
            }
        }


class DecisionV3EvalListResponseSchema(BaseModel):
    """Evaluation list response schema"""
    symbol: str
    items: List[DecisionV3EvalListItemSchema]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "2330",
                "items": [],
                "total": 0,
            }
        }


def evaluation_to_response_schema(evaluation: dict) -> DecisionV3EvalResponseSchema:
    """Convert evaluation dict to response schema"""
    return DecisionV3EvalResponseSchema(
        symbol=evaluation["symbol"],
        mode=evaluation["mode"],
        limit=evaluation["limit"],
        k=evaluation["k"],
        window=evaluation["window"],
        decision=evaluation["decision"],
        inputs_summary=evaluation["inputs_summary"],
        metrics=DecisionV3EvalMetricsSchema(**evaluation["metrics"]),
    )


def eval_snapshot_to_response_schema(snapshot: dict) -> DecisionV3EvalSnapshotResponseSchema:
    """Convert evaluation snapshot dict to response schema"""
    created_at = snapshot.get("created_at")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    elif not isinstance(created_at, str):
        created_at = datetime.now().isoformat()
    
    return DecisionV3EvalSnapshotResponseSchema(
        eval_id=snapshot.get("eval_id", ""),
        created_at=created_at,
        symbol=snapshot["symbol"],
        mode=snapshot["mode"],
        limit=snapshot["limit"],
        k=snapshot["k"],
        window=snapshot["window"],
        evaluation=evaluation_to_response_schema(snapshot["evaluation"]),
    )


def eval_list_to_response_schema(snapshots: List[dict], symbol: str) -> DecisionV3EvalListResponseSchema:
    """Convert evaluation snapshot list to response schema"""
    items = []
    for snapshot in snapshots:
        created_at = snapshot.get("created_at")
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        elif not isinstance(created_at, str):
            created_at = datetime.now().isoformat()
        
        eval_data = snapshot.get("evaluation", {})
        metrics = eval_data.get("metrics", {})
        
        items.append(DecisionV3EvalListItemSchema(
            eval_id=snapshot.get("eval_id", ""),
            created_at=created_at,
            symbol=snapshot.get("symbol", symbol),
            verdict=metrics.get("verdict", "NO_DATA"),
            metrics_summary={
                "hit_rate_proxy": metrics.get("hit_rate_proxy", 0.0),
                "avg_return_proxy": metrics.get("avg_return_proxy", 0.0),
                "max_drawdown_proxy": metrics.get("max_drawdown_proxy", 0.0),
            },
        ))
    
    return DecisionV3EvalListResponseSchema(
        symbol=symbol,
        items=items,
        total=len(items),
    )

