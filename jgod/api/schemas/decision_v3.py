"""
Decision V3 API Schemas

Pydantic models for Decision V3 API endpoints.
"""

from datetime import date
from typing import List, Optional, Dict
from pydantic import BaseModel

from jgod.decision_v3.models import DecisionV3Result, StrategyWeight, RiskPlan


class StrategyWeightSchema(BaseModel):
    """Strategy weight schema"""
    strategy_id: str
    weight: float
    grade: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    rationale: Optional[str] = None

    class Config:
        from_attributes = True


class RiskPlanSchema(BaseModel):
    """Risk plan schema"""
    position_scale: float
    risk_state: str  # "RISK_ON" | "RISK_OFF" | "CAUTION"
    reasons: List[str]

    class Config:
        from_attributes = True


class DecisionV3ResponseSchema(BaseModel):
    """Response schema for Decision V3 endpoint"""
    symbol: str
    as_of_date: Optional[str] = None
    selected_primary_strategy: Optional[str] = None
    selected_secondary_strategies: List[str]
    weights: List[StrategyWeightSchema]
    risk_plan: RiskPlanSchema
    confidence: float
    explain: str

    class Config:
        from_attributes = True


def result_to_schema(result: DecisionV3Result) -> DecisionV3ResponseSchema:
    """Convert DecisionV3Result to response schema"""
    return DecisionV3ResponseSchema(
        symbol=result.symbol,
        as_of_date=result.as_of_date.isoformat() if result.as_of_date else None,
        selected_primary_strategy=result.selected_primary_strategy,
        selected_secondary_strategies=result.selected_secondary_strategies,
        weights=[
            StrategyWeightSchema(
                strategy_id=sw.strategy_id,
                weight=sw.weight,
                grade=sw.grade,
                metrics=sw.metrics,
                rationale=sw.rationale,
            )
            for sw in result.weights
        ],
        risk_plan=RiskPlanSchema(
            position_scale=result.risk_plan.position_scale,
            risk_state=result.risk_plan.risk_state,
            reasons=result.risk_plan.reasons,
        ),
        confidence=result.confidence,
        explain=result.explain,
    )

