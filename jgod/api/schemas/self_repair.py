"""Self-Repair API Schemas

Pydantic models for Self-Repair API endpoints.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from jgod.knowledge.self_repair.models import (
    ConsistencyIssue as ConsistencyIssueModel,
    FixProposal as FixProposalModel,
    RepairReport as RepairReportModel,
)


# Re-export models as API schemas
class ConsistencyIssue(BaseModel):
    """Consistency issue schema"""
    id: str
    issue_type: str
    doctrine_refs: List[str]
    description: str
    severity: str
    context: dict = Field(default_factory=dict)
    created_at: datetime


class FixProposal(BaseModel):
    """Fix proposal schema"""
    id: str
    issue_id: str
    proposed_text: str
    justification: str
    confidence: float
    impact: str
    clarity_score: float = 0.0
    logical_score: float = 0.0
    impact_score: float = 0.0
    doctrine_alignment_score: float = 0.0
    metadata: dict = Field(default_factory=dict)
    created_at: datetime


class RepairReport(BaseModel):
    """Repair report schema"""
    id: str
    scan_summary: List[ConsistencyIssue]
    proposals: List[FixProposal]
    created_at: datetime
    metadata: dict = Field(default_factory=dict)


class ApplyProposalRequest(BaseModel):
    """Request to apply a proposal"""
    proposal_id: str
    create_backup: bool = True

