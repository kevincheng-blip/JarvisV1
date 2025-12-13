"""
Decision V3 Arena API Schemas

Pydantic schemas for Decision V3 Arena API responses.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class ChallengerScoreSchema(BaseModel):
    """Schema for a challenger score in the arena."""
    challenger_id: str = Field(..., description="Challenger identifier")
    composite_score: float = Field(..., description="Composite score")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Performance metrics")
    pareto_dominated: bool = Field(default=False, description="Whether this challenger is Pareto dominated")


class VariantConfigSchema(BaseModel):
    """Schema for a variant configuration."""
    risk_mapping: Optional[Dict[str, float]] = Field(None, description="Risk mapping (STABLE/WATCH/VOLATILE -> position_scale)")
    composite_weights: Optional[Dict[str, float]] = Field(None, description="Composite score weights")


class VariantScoreSchema(BaseModel):
    """Schema for a variant with its score."""
    config: VariantConfigSchema = Field(..., description="Variant configuration")
    score: float = Field(..., description="Variant composite score")


class AutoTuningResultSchema(BaseModel):
    """Schema for auto-tuning result."""
    best_config: Optional[VariantConfigSchema] = Field(None, description="Best variant configuration")
    top_variants: List[VariantScoreSchema] = Field(default_factory=list, description="Top 5 variants")
    notes: str = Field(default="", description="Auto-tuning notes (Traditional Chinese)")


class ArenaResultSchema(BaseModel):
    """Schema for arena result."""
    symbol: str = Field(..., description="Stock symbol")
    mode: str = Field(..., description="Decision mode")
    window: int = Field(..., description="Evaluation window size")
    limit: int = Field(..., description="Timeline limit")
    k: int = Field(..., description="Number of top strategies")
    scoreboard: List[ChallengerScoreSchema] = Field(default_factory=list, description="Challenger scores")
    winner_id: str = Field(..., description="Winner challenger ID")
    is_regression: bool = Field(default=False, description="Whether V3 is regressed")
    auto_tuning: Optional[AutoTuningResultSchema] = Field(None, description="Auto-tuning result")
    summary: str = Field(default="", description="Arena summary (Traditional Chinese)")
    recommendation_next_step: str = Field(default="", description="Recommendation next step (Traditional Chinese)")


class ArenaResponseSchema(BaseModel):
    """Response schema for arena recompute endpoint."""
    arena_id: str = Field(..., description="Arena snapshot ID")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    symbol: str = Field(..., description="Stock symbol")
    mode: str = Field(..., description="Decision mode")
    window: int = Field(..., description="Evaluation window size")
    limit: int = Field(..., description="Timeline limit")
    k: int = Field(..., description="Number of top strategies")
    arena: ArenaResultSchema = Field(..., description="Arena result")


class ArenaSnapshotResponseSchema(BaseModel):
    """Response schema for arena latest endpoint."""
    arena_id: str = Field(..., description="Arena snapshot ID")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    symbol: str = Field(..., description="Stock symbol")
    mode: str = Field(..., description="Decision mode")
    window: int = Field(..., description="Evaluation window size")
    limit: int = Field(..., description="Timeline limit")
    k: int = Field(..., description="Number of top strategies")
    arena: ArenaResultSchema = Field(..., description="Arena result")


class ArenaListItemSchema(BaseModel):
    """Schema for an arena list item."""
    arena_id: str = Field(..., description="Arena snapshot ID")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    winner_id: str = Field(..., description="Winner challenger ID")
    is_regression: bool = Field(default=False, description="Whether V3 is regressed")


class ArenaListResponseSchema(BaseModel):
    """Response schema for arena list endpoint."""
    symbol: str = Field(..., description="Stock symbol")
    total: int = Field(..., description="Total number of arena snapshots")
    items: List[ArenaListItemSchema] = Field(default_factory=list, description="List of arena snapshots")


def arena_result_to_schema(arena_dict: Dict) -> ArenaResultSchema:
    """Convert arena result dict to Pydantic schema."""
    return ArenaResultSchema(
        symbol=arena_dict.get("symbol", ""),
        mode=arena_dict.get("mode", "performance"),
        window=arena_dict.get("window", 20),
        limit=arena_dict.get("limit", 60),
        k=arena_dict.get("k", 5),
        scoreboard=[
            ChallengerScoreSchema(
                challenger_id=score.get("challenger_id", ""),
                composite_score=score.get("composite_score", 0.0),
                metrics=score.get("metrics", {}),
                pareto_dominated=score.get("pareto_dominated", False),
            )
            for score in arena_dict.get("scoreboard", [])
        ],
        winner_id=arena_dict.get("winner_id", "NO_DATA"),
        is_regression=arena_dict.get("is_regression", False),
        auto_tuning=AutoTuningResultSchema(
            best_config=VariantConfigSchema(
                risk_mapping=arena_dict.get("auto_tuning", {}).get("best_config", {}).get("risk_mapping"),
                composite_weights=arena_dict.get("auto_tuning", {}).get("best_config", {}).get("composite_weights"),
            ) if arena_dict.get("auto_tuning", {}).get("best_config") else None,
            top_variants=[
                VariantScoreSchema(
                    config=VariantConfigSchema(
                        risk_mapping=variant.get("config", {}).get("risk_mapping"),
                        composite_weights=variant.get("config", {}).get("composite_weights"),
                    ),
                    score=variant.get("score", 0.0),
                )
                for variant in arena_dict.get("auto_tuning", {}).get("top_variants", [])
            ],
            notes=arena_dict.get("auto_tuning", {}).get("notes", ""),
        ) if arena_dict.get("auto_tuning") else None,
        summary=arena_dict.get("summary", ""),
        recommendation_next_step=arena_dict.get("recommendation_next_step", ""),
    )


def arena_snapshot_to_response(snapshot: Dict) -> ArenaSnapshotResponseSchema:
    """Convert arena snapshot dict to response schema."""
    # Snapshot already contains all arena fields at top level
    created_at = snapshot.get("created_at", "")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    elif not isinstance(created_at, str):
        created_at = datetime.now().isoformat()
    
    return ArenaSnapshotResponseSchema(
        arena_id=snapshot.get("arena_id", ""),
        created_at=created_at,
        symbol=snapshot.get("symbol", ""),
        mode=snapshot.get("mode", "performance"),
        window=snapshot.get("window", 20),
        limit=snapshot.get("limit", 60),
        k=snapshot.get("k", 5),
        arena=arena_result_to_schema(snapshot),
    )

