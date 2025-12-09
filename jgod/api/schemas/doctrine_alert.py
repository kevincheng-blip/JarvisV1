"""Doctrine Alert API Schemas

Pydantic models for Doctrine Alert API endpoints.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from jgod.doctrine_alert.models import (
    DoctrineAlertSeverity,
    DoctrineAlertSource,
    DoctrineRef,
    DoctrineAlertItem as DoctrineAlertItemModel,
)


# Re-export models as API schemas
DoctrineAlertItem = DoctrineAlertItemModel


class DoctrineAlertSummary(BaseModel):
    """Summary of Doctrine alerts"""
    total_by_severity: dict[str, int] = Field(default_factory=dict)  # {"critical": 5, "warning": 10, "info": 2}
    total_by_source: dict[str, int] = Field(default_factory=dict)  # {"position": 3, "prediction": 5, "conflict": 9}
    total: int = 0

