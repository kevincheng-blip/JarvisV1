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


# ============================================================================
# Doctrine Patch Models
# ============================================================================

class PatchStatus(str, Enum):
    """Patch status"""
    PENDING_SIMULATION = "PENDING_SIMULATION"
    REJECTED_BY_SIM = "REJECTED_BY_SIM"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    DEPLOYED = "DEPLOYED"
    REVERTED = "REVERTED"


class RuleSimStatus(str, Enum):
    """Rule Sim status for patches"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass
class DoctrineChangeItem:
    """代表一個 Doctrine 條文的變更單元"""
    change_type: str  # "add", "modify", "delete"
    rule_id: str
    old_text: Optional[str] = None
    new_text: Optional[str] = None


@dataclass
class DoctrinePatch:
    """Doctrine Patch with full lifecycle tracking"""
    patch_id: str
    created_at: datetime
    author_id: str
    description: str
    changes: List[DoctrineChangeItem]
    status: PatchStatus
    rule_sim_report_id: Optional[str] = None
    sim_result_status: RuleSimStatus = RuleSimStatus.PENDING
    deployment_version: Optional[int] = None
    deployed_at: Optional[datetime] = None

