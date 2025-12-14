"""
Walk-Forward Notifications Schemas

v0.6.9-A9: Pydantic schemas for notifications and shadow reports
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class NotificationSchema(BaseModel):
    """Notification event schema."""
    event: str  # "AUTO_APPLY", "PENDING", "REJECTED"
    layer: str  # "thought", "method", "strategy"
    patch_id: Optional[str] = None
    snapshot_id: str
    quality_score: Optional[float] = None
    new_version: Optional[str] = None
    symbol: str
    date: str
    created_at: str


class NotificationListSchema(BaseModel):
    """Notification list response schema."""
    notifications: List[NotificationSchema]
    total: int


class ShadowReportSchema(BaseModel):
    """Shadow report schema."""
    symbol: str
    start_date: str
    end_date: str
    baseline_mode: str
    autopilot_final_nav: float
    baseline_final_nav: float
    initial_nav: float
    final_nav_delta: float
    pnl_delta: float
    number_of_patches_auto_applied: int
    created_at: str

