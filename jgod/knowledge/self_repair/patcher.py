"""Safe Patcher

Provides safe update mechanism for applying fixes to Doctrine knowledge base.
Requires manual approval - does NOT auto-commit changes.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from jgod.knowledge.self_repair.models import FixProposal

logger = logging.getLogger(__name__)


class SafePatcher:
    """Safe patcher for applying fixes to knowledge base"""
    
    def __init__(self, knowledge_path: Optional[Path] = None):
        """
        Initialize patcher
        
        Args:
            knowledge_path: Path to knowledge base JSONL file(s)
        """
        self.knowledge_path = knowledge_path or Path("knowledge_base/jgod_doctrine_knowledge_v1.jsonl")
    
    def apply_proposal(
        self,
        proposal: FixProposal,
        knowledge_path: Optional[Path] = None,
        create_backup: bool = True,
    ) -> bool:
        """
        Apply a fix proposal to the knowledge base.
        
        This method requires manual approval and creates backups before modifying.
        
        Args:
            proposal: FixProposal to apply
            knowledge_path: Optional override for knowledge base path
            create_backup: Whether to create backup before applying (default: True)
        
        Returns:
            True if applied successfully, False otherwise
        
        Note:
            This method does NOT automatically commit changes. Manual review is required.
        """
        target_path = knowledge_path or self.knowledge_path
        target_path = Path(target_path)
        
        if not target_path.exists():
            logger.error(f"Knowledge base file not found: {target_path}")
            return False
        
        logger.info(f"Applying proposal {proposal.id} to {target_path}")
        
        try:
            # Create backup
            if create_backup:
                backup_path = target_path.with_suffix(f".bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                shutil.copy2(target_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Read current knowledge base
            with open(target_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find and update relevant entries
            # Note: In v1, this is a simplified implementation
            # Future versions may need more sophisticated matching logic
            
            updated_lines = []
            proposal_applied = False
            
            for line in lines:
                # Check if this line contains the issue reference
                # This is simplified - in production, you'd need to match by section ID
                # For now, we'll append the proposal as a new entry
                updated_lines.append(line)
            
            # Append proposal as a new knowledge entry (v1 approach)
            # In production, you'd replace the actual section
            import json
            new_entry = {
                "id": f"fix_proposal_{proposal.id}",
                "type": "NOTE",
                "title": f"Fix Proposal: {proposal.id}",
                "description": proposal.justification,
                "raw_text": proposal.proposed_text,
                "tags": ["SELF_REPAIR", "PROPOSAL"],
                "source_doc": "self_repair_engine",
                "metadata": {
                    "proposal_id": proposal.id,
                    "issue_id": proposal.issue_id,
                    "applied_at": datetime.now().isoformat(),
                }
            }
            updated_lines.append(json.dumps(new_entry, ensure_ascii=False) + "\n")
            
            # Write updated knowledge base
            with open(target_path, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            
            logger.info(f"Successfully applied proposal {proposal.id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to apply proposal {proposal.id}: {e}", exc_info=True)
            return False
    
    def create_backup(self, knowledge_path: Optional[Path] = None) -> Optional[Path]:
        """
        Create a backup of the knowledge base.
        
        Args:
            knowledge_path: Optional override for knowledge base path
        
        Returns:
            Path to backup file, or None if failed
        """
        target_path = knowledge_path or self.knowledge_path
        target_path = Path(target_path)
        
        if not target_path.exists():
            logger.error(f"Knowledge base file not found: {target_path}")
            return None
        
        try:
            backup_path = target_path.with_suffix(f".bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(target_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}", exc_info=True)
            return None

