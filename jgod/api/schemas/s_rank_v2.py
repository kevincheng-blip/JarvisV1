"""
S-Rank Engine V2 API Schemas

Pydantic models for S-Rank V2 API endpoints.
"""

from datetime import datetime, date
from typing import List, Optional, Dict
from pydantic import BaseModel

from jgod.s_rank_v2.models import RecommendationSnapshot, RecommendationItem, Metrics, StabilityGrade


class MetricsSchema(BaseModel):
    """Metrics schema"""
    n_points: int
    score_std: float
    max_abs_delta: float
    trend_slope: float
    stability_grade: str  # "NO_DATA" | "STABLE" | "WATCH" | "VOLATILE"

    class Config:
        from_attributes = True


class RecommendationItemSchema(BaseModel):
    """Recommendation item schema"""
    strategy: str
    weight: float
    score: float

    class Config:
        from_attributes = True


class RecommendationResponseSchema(BaseModel):
    """Response schema for recommendation endpoint"""
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    metrics: MetricsSchema
    items: List[RecommendationItemSchema]
    weights: Dict[str, float]
    rationale: Dict[str, str]

    class Config:
        from_attributes = True


class RecommendationSnapshotResponseSchema(BaseModel):
    """Response schema for snapshot (with snapshot_id)"""
    snapshot_id: str
    created_at: datetime
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    metrics: MetricsSchema
    items: List[RecommendationItemSchema]
    weights: Dict[str, float]
    rationale: Dict[str, str]

    class Config:
        from_attributes = True


def snapshot_to_response_schema(snapshot: RecommendationSnapshot) -> RecommendationResponseSchema:
    """Convert RecommendationSnapshot to response schema"""
    return RecommendationResponseSchema(
        symbol=snapshot.symbol,
        start_date=snapshot.start_date.isoformat() if snapshot.start_date else None,
        end_date=snapshot.end_date.isoformat() if snapshot.end_date else None,
        metrics=MetricsSchema(
            n_points=snapshot.metrics.n_points if snapshot.metrics else 0,
            score_std=snapshot.metrics.score_std if snapshot.metrics else 0.0,
            max_abs_delta=snapshot.metrics.max_abs_delta if snapshot.metrics else 0.0,
            trend_slope=snapshot.metrics.trend_slope if snapshot.metrics else 0.0,
            stability_grade=snapshot.metrics.stability_grade.value if snapshot.metrics else "NO_DATA",
        ),
        items=[
            RecommendationItemSchema(
                strategy=item.strategy,
                weight=item.weight,
                score=item.score,
            )
            for item in snapshot.items
        ],
        weights=snapshot.weights,
        rationale=snapshot.rationale,
    )


def snapshot_to_snapshot_response_schema(snapshot: RecommendationSnapshot) -> RecommendationSnapshotResponseSchema:
    """Convert RecommendationSnapshot to snapshot response schema (with snapshot_id)"""
    base = snapshot_to_response_schema(snapshot)
    base_dict = base.model_dump() if hasattr(base, 'model_dump') else base.dict()
    return RecommendationSnapshotResponseSchema(
        snapshot_id=snapshot.snapshot_id,
        created_at=snapshot.created_at,
        **base_dict,
    )

