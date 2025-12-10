"""Doctrine Version Storage

Manages Doctrine section versions in filesystem structure.
"""

import logging
from pathlib import Path
from typing import Optional
import json

logger = logging.getLogger(__name__)


class VersionStorage:
    """Storage for Doctrine section versions"""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize version storage
        
        Args:
            base_path: Base path for version storage (default: data/doctrine_versions/)
        """
        if base_path is None:
            project_root = Path(__file__).parent.parent.parent
            base_path = project_root / "data" / "doctrine_versions"
        
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"VersionStorage initialized at: {self.base_path}")
    
    def get_version_path(self, section_id: str, version_id: str) -> Path:
        """Get path for a specific version file"""
        section_dir = self.base_path / section_id
        section_dir.mkdir(parents=True, exist_ok=True)
        return section_dir / f"{version_id}.md"
    
    def save_version(
        self,
        section_id: str,
        version_id: str,
        content: str,
    ) -> bool:
        """
        Save a version of a section.
        
        Args:
            section_id: Section identifier
            version_id: Version identifier
            content: Markdown content
        
        Returns:
            True if successful
        """
        try:
            version_path = self.get_version_path(section_id, version_id)
            version_path.write_text(content, encoding='utf-8')
            logger.info(f"Saved version {version_id} for section {section_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save version {version_id} for section {section_id}: {e}", exc_info=True)
            return False
    
    def load_version(
        self,
        section_id: str,
        version_id: str,
    ) -> Optional[str]:
        """
        Load a version of a section.
        
        Args:
            section_id: Section identifier
            version_id: Version identifier
        
        Returns:
            Content string if found, None otherwise
        """
        try:
            version_path = self.get_version_path(section_id, version_id)
            if not version_path.exists():
                return None
            return version_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to load version {version_id} for section {section_id}: {e}", exc_info=True)
            return None
    
    def list_versions(self, section_id: str) -> List[str]:
        """
        List all versions for a section.
        
        Args:
            section_id: Section identifier
        
        Returns:
            List of version IDs
        """
        try:
            section_dir = self.base_path / section_id
            if not section_dir.exists():
                return []
            
            versions = []
            for version_file in section_dir.glob("*.md"):
                version_id = version_file.stem
                versions.append(version_id)
            
            return sorted(versions)
        except Exception as e:
            logger.error(f"Failed to list versions for section {section_id}: {e}", exc_info=True)
            return []
    
    def delete_version(
        self,
        section_id: str,
        version_id: str,
    ) -> bool:
        """
        Delete a version (soft delete - rename to .deleted).
        
        Args:
            section_id: Section identifier
            version_id: Version identifier
        
        Returns:
            True if successful
        """
        try:
            version_path = self.get_version_path(section_id, version_id)
            if version_path.exists():
                deleted_path = version_path.with_suffix('.md.deleted')
                version_path.rename(deleted_path)
                logger.info(f"Deleted version {version_id} for section {section_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete version {version_id} for section {section_id}: {e}", exc_info=True)
            return False

