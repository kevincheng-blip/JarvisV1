"""Self-Repair Engine Data Models

Defines data structures for self-repair scanning, proposals, and reports.
"""

from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum


class IssueType(str, Enum):
    """Type of consistency issue"""
    CONFLICT = "CONFLICT"  # 規則矛盾
    AMBIGUOUS = "AMBIGUOUS"  # 定義模糊
    GAP = "GAP"  # 缺少操作條款
    DUPLICATE = "DUPLICATE"  # 規則重複
    OUTDATED = "OUTDATED"  # 過時條文


class IssueSeverity(str, Enum):
    """Severity level of an issue"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class DoctrineSection:
    """Represents a section from a Doctrine book"""
    id: str  # Unique identifier (e.g., "B01#S12")
    text: str  # Section content
    tags: List[str] = field(default_factory=list)
    source: str = ""  # Book ID (e.g., "B01")
    section_id: str = ""  # Section ID (e.g., "S12")
    metadata: dict = field(default_factory=dict)


@dataclass
class ConsistencyIssue:
    """Represents a consistency issue found during scanning"""
    id: str  # UUID v4
    issue_type: IssueType
    doctrine_refs: List[str]  # References to affected sections (e.g., ["B01#S12", "B02#S05"])
    description: str  # Human-readable description
    severity: IssueSeverity
    context: dict = field(default_factory=dict)  # Additional context data
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FixProposal:
    """Represents a proposed fix for a consistency issue"""
    id: str  # UUID v4
    issue_id: str  # Reference to ConsistencyIssue
    proposed_text: str  # Proposed new/updated text
    justification: str  # Reason for this proposal
    confidence: float = 0.0  # Confidence score (0.0 - 1.0)
    impact: str = ""  # Impact description (e.g., "risk-reduction", "rule-clarity")
    
    # Evaluation scores (set by evaluator)
    clarity_score: float = 0.0
    logical_score: float = 0.0
    impact_score: float = 0.0
    doctrine_alignment_score: float = 0.0
    
    # Metadata
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RepairReport:
    """Complete self-repair analysis report"""
    id: str  # UUID v4
    scan_summary: List[ConsistencyIssue]
    proposals: List[FixProposal]
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)  # Scan parameters, LLM model used, etc.
    
    def get_total_issues(self) -> int:
        """Get total number of issues found"""
        return len(self.scan_summary)
    
    def get_issues_by_severity(self, severity: IssueSeverity) -> List[ConsistencyIssue]:
        """Get issues filtered by severity"""
        return [issue for issue in self.scan_summary if issue.severity == severity]
    
    def get_proposals_for_issue(self, issue_id: str) -> List[FixProposal]:
        """Get all proposals for a specific issue"""
        return [p for p in self.proposals if p.issue_id == issue_id]
    
    def get_high_confidence_proposals(self, threshold: float = 0.6) -> List[FixProposal]:
        """Get proposals with confidence above threshold"""
        return [p for p in self.proposals if p.confidence >= threshold]

