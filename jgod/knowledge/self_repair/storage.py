"""Repair Report Storage

Stores and retrieves repair reports in JSONL format.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from jgod.knowledge.self_repair.models import RepairReport

logger = logging.getLogger(__name__)


class RepairReportStorage:
    """Storage for repair reports"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize storage
        
        Args:
            storage_path: Path to JSONL storage file
        """
        if storage_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            storage_path = project_root / "data" / "knowledge_self_repair" / "repair_reports.jsonl"
        
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"RepairReportStorage initialized at: {self.storage_path}")
    
    def save(self, report: RepairReport) -> None:
        """
        Save a repair report to JSONL file.
        
        Args:
            report: RepairReport to save
        """
        try:
            # Convert to dict
            report_dict = {
                "id": report.id,
                "created_at": report.created_at.isoformat(),
                "scan_summary": [
                    {
                        "id": issue.id,
                        "issue_type": issue.issue_type.value,
                        "doctrine_refs": issue.doctrine_refs,
                        "description": issue.description,
                        "severity": issue.severity.value,
                        "context": issue.context,
                        "created_at": issue.created_at.isoformat(),
                    }
                    for issue in report.scan_summary
                ],
                "proposals": [
                    {
                        "id": prop.id,
                        "issue_id": prop.issue_id,
                        "proposed_text": prop.proposed_text,
                        "justification": prop.justification,
                        "confidence": prop.confidence,
                        "impact": prop.impact,
                        "clarity_score": prop.clarity_score,
                        "logical_score": prop.logical_score,
                        "impact_score": prop.impact_score,
                        "doctrine_alignment_score": prop.doctrine_alignment_score,
                        "metadata": prop.metadata,
                        "created_at": prop.created_at.isoformat(),
                    }
                    for prop in report.proposals
                ],
                "metadata": report.metadata,
            }
            
            # Append to JSONL file
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(report_dict, ensure_ascii=False) + "\n")
            
            logger.info(f"Saved repair report: {report.id}")
        
        except Exception as e:
            logger.error(f"Failed to save repair report: {e}", exc_info=True)
            raise
    
    def load_all(self) -> List[RepairReport]:
        """
        Load all repair reports from storage.
        
        Returns:
            List of RepairReport objects
        """
        if not self.storage_path.exists():
            return []
        
        reports = []
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line)
                        report = self._dict_to_report(data)
                        reports.append(report)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSONL line {line_num}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to load repair reports: {e}", exc_info=True)
        
        return reports
    
    def load_recent(self, limit: int = 10) -> List[RepairReport]:
        """
        Load recent repair reports.
        
        Args:
            limit: Maximum number of reports to return
        
        Returns:
            List of RepairReport objects, sorted by created_at (newest first)
        """
        all_reports = self.load_all()
        all_reports.sort(key=lambda r: r.created_at, reverse=True)
        return all_reports[:limit]
    
    def load_by_id(self, report_id: str) -> Optional[RepairReport]:
        """
        Load a specific report by ID.
        
        Args:
            report_id: Report ID
        
        Returns:
            RepairReport if found, None otherwise
        """
        all_reports = self.load_all()
        for report in all_reports:
            if report.id == report_id:
                return report
        return None
    
    def _dict_to_report(self, data: dict) -> RepairReport:
        """Convert dict to RepairReport"""
        from jgod.knowledge.self_repair.models import (
            ConsistencyIssue,
            FixProposal,
            IssueType,
            IssueSeverity,
        )
        
        issues = [
            ConsistencyIssue(
                id=issue_data["id"],
                issue_type=IssueType(issue_data["issue_type"]),
                doctrine_refs=issue_data["doctrine_refs"],
                description=issue_data["description"],
                severity=IssueSeverity(issue_data["severity"]),
                context=issue_data.get("context", {}),
                created_at=datetime.fromisoformat(issue_data["created_at"]),
            )
            for issue_data in data.get("scan_summary", [])
        ]
        
        proposals = [
            FixProposal(
                id=prop_data["id"],
                issue_id=prop_data["issue_id"],
                proposed_text=prop_data["proposed_text"],
                justification=prop_data["justification"],
                confidence=prop_data.get("confidence", 0.0),
                impact=prop_data.get("impact", ""),
                clarity_score=prop_data.get("clarity_score", 0.0),
                logical_score=prop_data.get("logical_score", 0.0),
                impact_score=prop_data.get("impact_score", 0.0),
                doctrine_alignment_score=prop_data.get("doctrine_alignment_score", 0.0),
                metadata=prop_data.get("metadata", {}),
                created_at=datetime.fromisoformat(prop_data["created_at"]),
            )
            for prop_data in data.get("proposals", [])
        ]
        
        return RepairReport(
            id=data["id"],
            scan_summary=issues,
            proposals=proposals,
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
        )

