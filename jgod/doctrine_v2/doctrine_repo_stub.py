"""Doctrine Repository Stub

Lightweight stub for Doctrine version storage and change application.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from jgod.doctrine_v2.models import DoctrinePatch

logger = logging.getLogger(__name__)

_VERSION_FILE = "doctrine_version.json"


def _get_version_path() -> Path:
    """Get the path to version file"""
    project_root = Path(__file__).parent.parent.parent
    path = project_root / "data" / "doctrine" / _VERSION_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_current_version() -> int:
    """Get current doctrine version number"""
    version_path = _get_version_path()
    
    if not version_path.exists():
        # Initialize with version 1
        data = {"version": 1}
        with open(version_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return 1
    
    try:
        with open(version_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("version", 1)
    except Exception as e:
        logger.error(f"Failed to load doctrine version: {e}", exc_info=True)
        return 1


def save_new_version(version: int) -> None:
    """Save new doctrine version number"""
    version_path = _get_version_path()
    
    try:
        data = {"version": version}
        with open(version_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        logger.info(f"Saved doctrine version {version}")
    except Exception as e:
        logger.error(f"Failed to save doctrine version: {e}", exc_info=True)
        raise


def apply_changes_stub(patch: DoctrinePatch) -> None:
    """
    Apply patch changes to doctrine (stub implementation)
    
    In real implementation, this would modify actual doctrine rules.
    
    Args:
        patch: DoctrinePatch to apply
    """
    logger.info(f"Applying patch {patch.patch_id} with {len(patch.changes)} changes (stub)")
    
    for change in patch.changes:
        logger.debug(
            f"Change: {change.change_type} rule_id={change.rule_id} "
            f"(old_text length={len(change.old_text) if change.old_text else 0}, "
            f"new_text length={len(change.new_text) if change.new_text else 0})"
        )
    
    # Stub: Just log the changes, don't actually modify doctrine
    logger.info(f"Patch {patch.patch_id} changes applied (stub mode)")
