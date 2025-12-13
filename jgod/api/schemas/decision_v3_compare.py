"""
Decision V3 Compare API Schemas

Pydantic schemas for Decision V3 compare endpoints.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class DeltaMetricsSchema(BaseModel):
    """Delta metrics schema (v3 - baseline)"""
    hit_rate_proxy: float
    avg_return_proxy: float
    max_drawdown_proxy: float
    turnover_proxy: float
    decision_consistency: float

    class Config:
        json_schema_extra = {
            "example": {
                "hit_rate_proxy": 0.05,
                "avg_return_proxy": 0.01,
                "max_drawdown_proxy": -0.03,
                "turnover_proxy": 0.02,
                "decision_consistency": 0.10,
            }
        }


class CompareResultSchema(BaseModel):
    """Compare result schema"""
    winner: str  # V3 | BASELINE | TIE | NO_DATA
    delta_metrics: DeltaMetricsSchema
    summary: str
    recommendation_next_step: str

    class Config:
        json_schema_extra = {
            "example": {
                "winner": "V3",
                "delta_metrics": {
                    "hit_rate_proxy": 0.05,
                    "avg_return_proxy": 0.01,
                    "max_drawdown_proxy": -0.03,
                    "turnover_proxy": 0.02,
                    "decision_consistency": 0.10,
                },
                "summary": "Decision V3 表現優於 Baseline。",
                "recommendation_next_step": "建議：維持 Decision V3 當前配置。",
            }
        }


class CompareResponseSchema(BaseModel):
    """Compare response schema"""
    symbol: str
    mode: str
    limit: int
    k: int
    window: int
    compare: CompareResultSchema

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "2330",
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "window": 20,
                "compare": {
                    "winner": "V3",
                    "delta_metrics": {},
                    "summary": "",
                    "recommendation_next_step": "",
                },
            }
        }


class CompareSnapshotResponseSchema(BaseModel):
    """Compare snapshot response schema"""
    compare_id: str
    created_at: str
    symbol: str
    mode: str
    limit: int
    k: int
    window: int
    compare: CompareResponseSchema

    class Config:
        json_schema_extra = {
            "example": {
                "compare_id": "abc-123-def",
                "created_at": "2025-12-13T10:00:00",
                "symbol": "2330",
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "window": 20,
                "compare": {
                    "symbol": "2330",
                    "mode": "performance",
                    "limit": 60,
                    "k": 5,
                    "window": 20,
                    "compare": {
                        "winner": "V3",
                        "delta_metrics": {},
                        "summary": "",
                        "recommendation_next_step": "",
                    },
                },
            }
        }


class CompareListItemSchema(BaseModel):
    """Compare list item schema"""
    compare_id: str
    created_at: str
    symbol: str
    winner: str
    summary_short: str

    class Config:
        json_schema_extra = {
            "example": {
                "compare_id": "abc-123-def",
                "created_at": "2025-12-13T10:00:00",
                "symbol": "2330",
                "winner": "V3",
                "summary_short": "Decision V3 表現優於 Baseline。",
            }
        }


class CompareListResponseSchema(BaseModel):
    """Compare list response schema"""
    symbol: str
    items: List[CompareListItemSchema]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "2330",
                "items": [],
                "total": 0,
            }
        }


def compare_to_response_schema(compare: dict) -> CompareResponseSchema:
    """Convert compare dict to response schema"""
    return CompareResponseSchema(
        symbol=compare["symbol"],
        mode=compare["mode"],
        limit=compare["limit"],
        k=compare["k"],
        window=compare["window"],
        compare=CompareResultSchema(
            winner=compare["winner"],
            delta_metrics=DeltaMetricsSchema(**compare["delta_metrics"]),
            summary=compare["summary"],
            recommendation_next_step=compare["recommendation_next_step"],
        ),
    )


def compare_snapshot_to_response_schema(snapshot: dict) -> CompareSnapshotResponseSchema:
    """Convert compare snapshot dict to response schema"""
    created_at = snapshot.get("created_at")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    elif not isinstance(created_at, str):
        created_at = datetime.now().isoformat()
    
    compare_data = snapshot.get("compare", {})
    
    return CompareSnapshotResponseSchema(
        compare_id=snapshot.get("compare_id", ""),
        created_at=created_at,
        symbol=snapshot.get("symbol", ""),
        mode=snapshot.get("mode", "performance"),
        limit=snapshot.get("limit", 60),
        k=snapshot.get("k", 5),
        window=snapshot.get("window", 20),
        compare=compare_to_response_schema(compare_data),
    )


def compare_list_to_response_schema(snapshots: List[dict], symbol: str) -> CompareListResponseSchema:
    """Convert compare snapshot list to response schema"""
    items = []
    for snapshot in snapshots:
        created_at = snapshot.get("created_at")
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        elif not isinstance(created_at, str):
            created_at = datetime.now().isoformat()
        
        compare_data = snapshot.get("compare", {})
        summary = compare_data.get("summary", "")
        # Get first line of summary as short summary
        summary_short = summary.split("\n")[0] if summary else ""
        
        items.append(CompareListItemSchema(
            compare_id=snapshot.get("compare_id", ""),
            created_at=created_at,
            symbol=snapshot.get("symbol", symbol),
            winner=compare_data.get("winner", "NO_DATA"),
            summary_short=summary_short,
        ))
    
    return CompareListResponseSchema(
        symbol=symbol,
        items=items,
        total=len(items),
    )

