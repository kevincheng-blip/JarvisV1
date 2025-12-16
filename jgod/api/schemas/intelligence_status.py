"""
Intelligence Status API Schemas

v0.6.13-P1.1: Added method layer drift score fields
"""

from pydantic import BaseModel
from typing import Optional, Literal


class IntelligenceStatusSchema(BaseModel):
    """Intelligence status response schema."""
    
    # Method Layer Drift (v0.6.13-P1.1)
    method_layer_drift_score: float = 0.0
    method_layer_drift_status: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"
    method_layer_drift_updated_at: Optional[str] = None
    
    # Other intelligence fields (can be extended later)
    health_flags: dict = {}
    activities: list = []
    created_at: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "method_layer_drift_score": 0.37,
                "method_layer_drift_status": "MEDIUM",
                "method_layer_drift_updated_at": "2025-12-16T10:30:00",
                "health_flags": {},
                "activities": [],
                "created_at": "2025-12-16T10:30:00",
            }
        }

