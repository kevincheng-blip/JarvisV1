"""
Decision V3 Snapshot API Schemas

Pydantic models for Decision V3 snapshot endpoints.
"""

from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel

from jgod.api.schemas.decision_v3 import DecisionV3ResponseSchema


class DecisionV3SnapshotResponseSchema(BaseModel):
    """Response schema for a single Decision V3 snapshot"""
    snapshot_id: str
    created_at: str  # ISO format datetime string
    symbol: str
    mode: str
    limit: int
    k: int
    result: DecisionV3ResponseSchema

    class Config:
        from_attributes = True


class DecisionV3SnapshotListItemSchema(BaseModel):
    """Schema for a snapshot list item (metadata only)"""
    snapshot_id: str
    created_at: str
    symbol: str
    mode: str
    primary_strategy: Optional[str] = None
    confidence: float = 0.0
    risk_state: str = "RISK_OFF"

    class Config:
        from_attributes = True


class DecisionV3SnapshotListResponseSchema(BaseModel):
    """Response schema for Decision V3 snapshot list"""
    symbol: str
    items: List[DecisionV3SnapshotListItemSchema]
    total: int

    class Config:
        from_attributes = True


def snapshot_to_response_schema(snapshot: dict) -> DecisionV3SnapshotResponseSchema:
    """Convert snapshot dict to response schema"""
    from jgod.api.schemas.decision_v3 import result_to_schema
    from jgod.decision_v3.models import DecisionV3Result, StrategyWeight, RiskPlan
    
    # Convert result dict back to DecisionV3Result for schema conversion
    result_dict = snapshot.get("result", {})
    weights = [
        StrategyWeight(
            strategy_id=w.get("strategy_id", ""),
            weight=w.get("weight", 0.0),
            grade=w.get("grade"),
            metrics=w.get("metrics"),
            rationale=w.get("rationale"),
        )
        for w in result_dict.get("weights", [])
    ]
    
    risk_plan_dict = result_dict.get("risk_plan", {})
    risk_plan = RiskPlan(
        position_scale=risk_plan_dict.get("position_scale", 0.0),
        risk_state=risk_plan_dict.get("risk_state", "RISK_OFF"),
        reasons=risk_plan_dict.get("reasons", []),
    )
    
    result = DecisionV3Result(
        symbol=result_dict.get("symbol", ""),
        as_of_date=datetime.fromisoformat(result_dict["as_of_date"]) if result_dict.get("as_of_date") else None,
        selected_primary_strategy=result_dict.get("selected_primary_strategy"),
        selected_secondary_strategies=result_dict.get("selected_secondary_strategies", []),
        weights=weights,
        risk_plan=risk_plan,
        confidence=result_dict.get("confidence", 0.0),
        explain=result_dict.get("explain", ""),
    )
    
    result_schema = result_to_schema(result)
    
    # Format created_at
    created_at = snapshot.get("created_at")
    if isinstance(created_at, datetime):
        created_at_str = created_at.isoformat()
    elif isinstance(created_at, str):
        created_at_str = created_at
    else:
        created_at_str = datetime.now().isoformat()
    
    return DecisionV3SnapshotResponseSchema(
        snapshot_id=snapshot.get("snapshot_id", ""),
        created_at=created_at_str,
        symbol=snapshot.get("symbol", ""),
        mode=snapshot.get("mode", "performance"),
        limit=snapshot.get("limit", 60),
        k=snapshot.get("k", 5),
        result=result_schema,
    )


def snapshot_list_to_response_schema(snapshots: List[dict], symbol: str) -> DecisionV3SnapshotListResponseSchema:
    """Convert snapshot list to response schema"""
    items = []
    for snapshot in snapshots:
        result = snapshot.get("result", {})
        items.append(
            DecisionV3SnapshotListItemSchema(
                snapshot_id=snapshot.get("snapshot_id", ""),
                created_at=snapshot.get("created_at").isoformat() if isinstance(snapshot.get("created_at"), datetime) else str(snapshot.get("created_at", "")),
                symbol=snapshot.get("symbol", symbol),
                mode=snapshot.get("mode", "performance"),
                primary_strategy=result.get("selected_primary_strategy"),
                confidence=result.get("confidence", 0.0),
                risk_state=result.get("risk_plan", {}).get("risk_state", "RISK_OFF"),
            )
        )
    
    return DecisionV3SnapshotListResponseSchema(
        symbol=symbol,
        items=items,
        total=len(items),
    )

