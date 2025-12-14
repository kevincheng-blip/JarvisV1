"""
Config API Router

v0.6.8-A8: Doctrine configuration and patch management API
"""

import logging
from fastapi import APIRouter, Query, Body
from typing import Dict, List

from jgod.config.doctrine import (
    load_doctrine,
    save_doctrine,
    list_doctrine_versions,
    apply_patch,
    rollback_to_version,
    DoctrineConfig,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/doctrine/{version}")
async def get_doctrine(version: str = "v1.0") -> dict:
    """
    Get doctrine configuration by version.
    
    Returns default if version not found.
    """
    config = load_doctrine(version)
    if config is None:
        config = DoctrineConfig(version=version)
    
    return config.to_dict()


@router.get("/doctrine/versions")
async def list_versions() -> dict:
    """List all available doctrine versions."""
    versions = list_doctrine_versions()
    return {
        "versions": versions,
        "default": "v1.0",
    }


@router.post("/doctrine/apply-patch")
async def apply_doctrine_patch(
    base_version: str = Body(..., description="Base doctrine version"),
    patch: Dict = Body(..., description="Patch dict (target, changes)"),
    new_version: str = Body(..., description="New version name"),
) -> dict:
    """
    Apply patch to create new doctrine version.
    
    Requires manual approval (no auto-apply).
    """
    try:
        new_config = apply_patch(base_version, patch, new_version)
        return {
            "success": True,
            "new_version": new_version,
            "config": new_config.to_dict(),
        }
    except Exception as e:
        logger.error(f"Failed to apply patch: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/doctrine/rollback/{version}")
async def rollback_doctrine(version: str) -> dict:
    """
    Rollback to a previous doctrine version.
    
    Creates a new version with rollback marker.
    """
    try:
        rollback_config = rollback_to_version(version)
        return {
            "success": True,
            "rollback_version": rollback_config.version,
            "config": rollback_config.to_dict(),
        }
    except Exception as e:
        logger.error(f"Failed to rollback to {version}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }

