"""Doctrine Service V2 API Schemas

Pydantic models for Doctrine Management Console API endpoints.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from jgod.doctrine_v2.models import SectionStatus


class SectionRevisionSchema(BaseModel):
    """Section revision schema"""
    version_id: str
    timestamp: datetime
    operator: str
    change_type: str
    content: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class DoctrineSectionSchema(BaseModel):
    """Doctrine section schema"""
    section_id: str
    title: str
    current_version_id: str
    draft_version_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    revision_history: List[SectionRevisionSchema] = Field(default_factory=list)
    source: str = "manual"
    severity: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class CreateDraftRequest(BaseModel):
    """Request to create a draft"""
    content: str


class DiffResponse(BaseModel):
    """Diff response"""
    diff: str
    from_version_id: str
    to_version_id: str


class BulkActionRequest(BaseModel):
    """Request for bulk actions"""
    section_ids: List[str]
    action: str  # "approve" or "reject"

