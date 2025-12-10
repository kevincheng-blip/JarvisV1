"""Doctrine Service V2 Data Models

Defines data structures for Doctrine version control and review workflow.
"""

from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum


class SectionStatus(str, Enum):
    """Section status"""
    APPROVED = "APPROVED"
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    DEPRECATED = "DEPRECATED"


class ChangeType(str, Enum):
    """Change type for revision history"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ROLLBACK = "ROLLBACK"


@dataclass
class SectionRevision:
    """Revision history entry"""
    version_id: str
    timestamp: datetime
    operator: str  # "human" or "self-repair-engine"
    change_type: ChangeType
    content: Optional[str] = None  # Snapshot of content at this revision
    metadata: dict = field(default_factory=dict)  # e.g., {"repair_report_id": "xxx", "confidence": 0.85}


@dataclass
class DoctrineSectionV2:
    """Doctrine Section V2 with version control"""
    section_id: str
    title: str
    current_version_id: str
    draft_version_id: Optional[str] = None
    status: SectionStatus = SectionStatus.APPROVED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    revision_history: List[SectionRevision] = field(default_factory=list)
    
    # Additional metadata
    source: str = "manual"  # "manual" or "self-repair"
    severity: Optional[str] = None  # Optional severity from Self-Repair Engine
    metadata: dict = field(default_factory=dict)  # Additional metadata

