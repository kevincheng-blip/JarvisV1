"""Predictions V2 API Schemas

Pydantic models for Predictions V2 API endpoints.
"""

from datetime import date
from typing import List, Optional
from pydantic import BaseModel


class FinalScoreRequest(BaseModel):
    """Request for final score calculation"""
    symbol: str
    date: date
    version: str = "v2"  # "v1" or "v2"


class DoctrineFlagSchema(BaseModel):
    """Doctrine flag schema"""
    code: str
    severity: str
    message: str
    doctrine_refs: List[str] = []


class FinalScoreItem(BaseModel):
    """Final score item response"""
    symbol: str
    date: date
    raw_score: float
    final_score: float
    correction_factor: float
    doctrine_flags: List[DoctrineFlagSchema] = []
    adjustment_reason: str = ""
    llm_model: str = ""
    version: str = "v2"

