"""Doctrine Service V2

Main service for Doctrine version control and review workflow.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json

from jgod.doctrine_v2.models import (
    DoctrineSectionV2,
    SectionRevision,
    SectionStatus,
    ChangeType,
)
from jgod.doctrine_v2.version_storage import VersionStorage

logger = logging.getLogger(__name__)


class DoctrineServiceV2:
    """Doctrine Service V2 with version control"""
    
    def __init__(self, storage: Optional[VersionStorage] = None):
        """
        Initialize Doctrine Service V2
        
        Args:
            storage: VersionStorage instance (optional)
        """
        self.storage = storage or VersionStorage()
        self._sections_cache: dict[str, DoctrineSectionV2] = {}
        self._load_sections_metadata()
    
    def _get_sections_metadata_path(self) -> Path:
        """Get path to sections metadata file"""
        return self.storage.base_path / "sections_metadata.json"
    
    def _load_sections_metadata(self) -> None:
        """Load sections metadata from disk"""
        metadata_path = self._get_sections_metadata_path()
        if not metadata_path.exists():
            return
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for section_data in data.get('sections', []):
                    section = self._dict_to_section(section_data)
                    self._sections_cache[section.section_id] = section
            logger.info(f"Loaded {len(self._sections_cache)} sections metadata")
        except Exception as e:
            logger.error(f"Failed to load sections metadata: {e}", exc_info=True)
    
    def _save_sections_metadata(self) -> None:
        """Save sections metadata to disk"""
        metadata_path = self._get_sections_metadata_path()
        try:
            data = {
                'sections': [self._section_to_dict(s) for s in self._sections_cache.values()]
            }
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            logger.debug(f"Saved {len(self._sections_cache)} sections metadata")
        except Exception as e:
            logger.error(f"Failed to save sections metadata: {e}", exc_info=True)
    
    def _dict_to_section(self, data: dict) -> DoctrineSectionV2:
        """Convert dict to DoctrineSectionV2"""
        revisions = [
            SectionRevision(
                version_id=r['version_id'],
                timestamp=datetime.fromisoformat(r['timestamp']),
                operator=r['operator'],
                change_type=ChangeType(r['change_type']),
                content=r.get('content'),
                metadata=r.get('metadata', {}),
            )
            for r in data.get('revision_history', [])
        ]
        
        return DoctrineSectionV2(
            section_id=data['section_id'],
            title=data['title'],
            current_version_id=data['current_version_id'],
            draft_version_id=data.get('draft_version_id'),
            status=SectionStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            revision_history=revisions,
            source=data.get('source', 'manual'),
            severity=data.get('severity'),
            metadata=data.get('metadata', {}),
        )
    
    def _section_to_dict(self, section: DoctrineSectionV2) -> dict:
        """Convert DoctrineSectionV2 to dict"""
        return {
            'section_id': section.section_id,
            'title': section.title,
            'current_version_id': section.current_version_id,
            'draft_version_id': section.draft_version_id,
            'status': section.status.value,
            'created_at': section.created_at.isoformat(),
            'updated_at': section.updated_at.isoformat(),
            'revision_history': [
                {
                    'version_id': r.version_id,
                    'timestamp': r.timestamp.isoformat(),
                    'operator': r.operator,
                    'change_type': r.change_type.value,
                    'content': r.content,
                    'metadata': r.metadata,
                }
                for r in section.revision_history
            ],
            'source': section.source,
            'severity': section.severity,
            'metadata': section.metadata,
        }
    
    def get_sections(
        self,
        status: Optional[SectionStatus] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[List[DoctrineSectionV2], int]:
        """
        Get sections with filtering and pagination.
        
        Args:
            status: Optional status filter
            page: Page number (1-indexed)
            page_size: Items per page
        
        Returns:
            Tuple of (sections list, total count)
        """
        all_sections = list(self._sections_cache.values())
        
        # Filter by status
        if status:
            all_sections = [s for s in all_sections if s.status == status]
        
        # Sort by updated_at (newest first)
        all_sections.sort(key=lambda s: s.updated_at, reverse=True)
        
        total = len(all_sections)
        
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        paginated = all_sections[start:end]
        
        return paginated, total
    
    def get_section(self, section_id: str) -> Optional[DoctrineSectionV2]:
        """Get a specific section"""
        return self._sections_cache.get(section_id)
    
    def get_version_content(
        self,
        section_id: str,
        version_id: str,
    ) -> Optional[str]:
        """Get content for a specific version"""
        return self.storage.load_version(section_id, version_id)
    
    def get_diff(
        self,
        section_id: str,
        from_version_id: str,
        to_version_id: str,
    ) -> Optional[str]:
        """
        Get unified diff between two versions.
        
        Args:
            section_id: Section identifier
            from_version_id: Source version ID
            to_version_id: Target version ID
        
        Returns:
            Unified diff string, or None if versions not found
        """
        from_content = self.storage.load_version(section_id, from_version_id)
        to_content = self.storage.load_version(section_id, to_version_id)
        
        if from_content is None or to_content is None:
            return None
        
        # Simple unified diff (can be enhanced with difflib)
        import difflib
        
        from_lines = from_content.splitlines(keepends=True)
        to_lines = to_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            from_lines,
            to_lines,
            fromfile=f"{section_id}/{from_version_id}",
            tofile=f"{section_id}/{to_version_id}",
            lineterm='',
        )
        
        return ''.join(diff)
    
    def create_draft(
        self,
        section_id: str,
        content: str,
        operator: str = "human",
    ) -> Optional[str]:
        """
        Create a draft version for a section.
        
        Args:
            section_id: Section identifier
            content: Draft content
            operator: Operator name ("human" or "self-repair-engine")
        
        Returns:
            Version ID if successful, None otherwise
        """
        version_id = str(uuid.uuid4())
        
        # Save version
        if not self.storage.save_version(section_id, version_id, content):
            return None
        
        # Update section metadata
        section = self._sections_cache.get(section_id)
        if not section:
            # Create new section
            section = DoctrineSectionV2(
                section_id=section_id,
                title=section_id,  # Default title, can be updated later
                current_version_id=version_id,
                status=SectionStatus.DRAFT,
            )
            section.revision_history.append(SectionRevision(
                version_id=version_id,
                timestamp=datetime.now(),
                operator=operator,
                change_type=ChangeType.CREATE,
                content=content,
            ))
        else:
            # Update existing section
            section.draft_version_id = version_id
            section.status = SectionStatus.DRAFT
            section.updated_at = datetime.now()
            section.revision_history.append(SectionRevision(
                version_id=version_id,
                timestamp=datetime.now(),
                operator=operator,
                change_type=ChangeType.UPDATE,
                content=content,
            ))
        
        self._sections_cache[section_id] = section
        self._save_sections_metadata()
        
        logger.info(f"Created draft version {version_id} for section {section_id}")
        return version_id
    
    def submit_for_review(
        self,
        section_id: str,
    ) -> bool:
        """
        Submit draft for review.
        
        Args:
            section_id: Section identifier
        
        Returns:
            True if successful
        """
        section = self._sections_cache.get(section_id)
        if not section or not section.draft_version_id:
            logger.warning(f"No draft found for section {section_id}")
            return False
        
        section.status = SectionStatus.PENDING_REVIEW
        section.updated_at = datetime.now()
        
        self._save_sections_metadata()
        logger.info(f"Submitted section {section_id} for review")
        return True
    
    def approve_version(
        self,
        section_id: str,
        version_id: str,
    ) -> bool:
        """
        Approve a version.
        
        Args:
            section_id: Section identifier
            version_id: Version ID to approve
        
        Returns:
            True if successful
        """
        section = self._sections_cache.get(section_id)
        if not section:
            logger.warning(f"Section not found: {section_id}")
            return False
        
        # Update current version
        section.current_version_id = version_id
        section.draft_version_id = None
        section.status = SectionStatus.APPROVED
        section.updated_at = datetime.now()
        
        # Add revision entry
        section.revision_history.append(SectionRevision(
            version_id=version_id,
            timestamp=datetime.now(),
            operator="human",  # Approval is always by human
            change_type=ChangeType.APPROVE,
        ))
        
        self._save_sections_metadata()
        logger.info(f"Approved version {version_id} for section {section_id}")
        return True
    
    def reject_version(
        self,
        section_id: str,
        version_id: str,
    ) -> bool:
        """
        Reject a version.
        
        Args:
            section_id: Section identifier
            version_id: Version ID to reject
        
        Returns:
            True if successful
        """
        section = self._sections_cache.get(section_id)
        if not section:
            return False
        
        # Clear draft if this was the draft
        if section.draft_version_id == version_id:
            section.draft_version_id = None
        
        section.status = SectionStatus.DRAFT  # Revert to DRAFT
        section.updated_at = datetime.now()
        
        # Add revision entry
        section.revision_history.append(SectionRevision(
            version_id=version_id,
            timestamp=datetime.now(),
            operator="human",
            change_type=ChangeType.REJECT,
        ))
        
        self._save_sections_metadata()
        logger.info(f"Rejected version {version_id} for section {section_id}")
        return True
    
    def rollback_to_version(
        self,
        section_id: str,
        target_version_id: str,
    ) -> bool:
        """
        Rollback to a previous version.
        
        Args:
            section_id: Section identifier
            target_version_id: Target version ID to rollback to
        
        Returns:
            True if successful
        """
        section = self._sections_cache.get(section_id)
        if not section:
            return False
        
        # Verify target version exists
        target_content = self.storage.load_version(section_id, target_version_id)
        if not target_content:
            logger.warning(f"Target version {target_version_id} not found")
            return False
        
        # Update current version
        section.current_version_id = target_version_id
        section.status = SectionStatus.APPROVED
        section.updated_at = datetime.now()
        
        # Add revision entry
        section.revision_history.append(SectionRevision(
            version_id=target_version_id,
            timestamp=datetime.now(),
            operator="human",
            change_type=ChangeType.ROLLBACK,
        ))
        
        self._save_sections_metadata()
        logger.info(f"Rolled back section {section_id} to version {target_version_id}")
        return True
    
    def create_from_self_repair_proposal(
        self,
        section_id: str,
        proposal_content: str,
        repair_report_id: str,
        confidence: float,
        issue_type: str,
    ) -> Optional[str]:
        """
        Create a draft version from Self-Repair Engine proposal.
        
        Args:
            section_id: Section identifier
            proposal_content: Proposed content
            repair_report_id: Self-Repair report ID
            confidence: Proposal confidence score
            issue_type: Issue type (CONFLICT, AMBIGUOUS, etc.)
        
        Returns:
            Version ID if successful, None otherwise
        """
        version_id = self.create_draft(
            section_id=section_id,
            content=proposal_content,
            operator="self-repair-engine",
        )
        
        if version_id:
            section = self._sections_cache.get(section_id)
            if section:
                section.source = "self-repair"
                section.status = SectionStatus.PENDING_REVIEW
                section.metadata = {
                    'repair_report_id': repair_report_id,
                    'confidence': confidence,
                    'issue_type': issue_type,
                }
                # Update the latest revision with metadata
                if section.revision_history:
                    section.revision_history[-1].metadata = {
                        'repair_report_id': repair_report_id,
                        'confidence': confidence,
                        'issue_type': issue_type,
                    }
                self._save_sections_metadata()
        
        return version_id

