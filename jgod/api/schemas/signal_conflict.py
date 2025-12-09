"""Signal Conflict API Schemas

Pydantic models for Signal Conflict API endpoints.
"""

from typing import Dict, Optional, Literal
from pydantic import BaseModel, Field


class ConflictItem(BaseModel):
    """Conflict analysis result for a single symbol"""
    symbol: str
    name: str
    consensus_score: float = Field(..., ge=0, le=100, description="Consensus score (0-100)")
    conflict_score: float = Field(..., ge=0, le=100, description="Conflict score (0-100)")
    majority_vote: int = Field(..., description="1: long, -1: short, 0: neutral")
    strategy_votes: Dict[str, int] = Field(default_factory=dict, description="Strategy votes: {'S1': 1, 'S2': -1, ...}")
    raw_score: Optional[float] = None
    final_score: Optional[float] = None

