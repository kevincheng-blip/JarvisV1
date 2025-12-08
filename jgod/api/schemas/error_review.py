"""
Error Review API Schemas

Pydantic models for Error Review API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DoctrineHitLite(BaseModel):
    """Lightweight Doctrine hit for table display
    
    Simplified version of DoctrineHit for API responses.
    """
    book_id: str = Field(..., description="Book ID (e.g., 'book_07')")
    section_id: str = Field(..., description="Section ID within the book")
    summary: Optional[str] = Field(None, description="Summary from Doctrine's ai_summary")
    core_principles: Optional[List[str]] = Field(None, description="Core principles from Doctrine")
    risk_rules: Optional[List[str]] = Field(None, description="Risk rules from Doctrine")
    tags: Optional[List[str]] = Field(None, description="Tags from the doctrine entry")


class ErrorReviewItem(BaseModel):
    """Error review item for API response
    
    Represents a single error analysis result with Doctrine suggestions.
    """
    id: str = Field(..., description="Unique error event ID")
    timestamp: datetime = Field(..., description="When the error occurred")
    symbol: str = Field(..., description="Stock symbol (e.g., '2330')")
    error_type: Optional[str] = Field(None, description="Type of error (e.g., 'STOP_LOSS_TOO_LATE')")
    pnl_impact: Optional[float] = Field(None, description="Profit/loss impact of this error")
    human_summary: Optional[str] = Field(None, description="Human or AI-written error summary")
    doctrine_hits: List[DoctrineHitLite] = Field(default_factory=list, description="Doctrine suggestions for this error")
    classification: str = Field(..., description="Error classification (UTILIZATION_GAP, FORM_INSUFFICIENT, etc.)")
    timeframe: Optional[str] = Field(None, description="Trading timeframe")
    side: Optional[str] = Field(None, description="Trade direction (long/short)")
    predicted_outcome: Optional[str] = Field(None, description="What was predicted")
    actual_outcome: Optional[str] = Field(None, description="What actually happened")

