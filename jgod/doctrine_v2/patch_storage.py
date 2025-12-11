"""Doctrine Patch Storage

JSONL-based storage for Doctrine patches.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from jgod.doctrine_v2.models import (
    DoctrinePatch,
    PatchStatus,
    RuleSimStatus,
)

logger = logging.getLogger(__name__)


def _patch_to_dict(patch: DoctrinePatch) -> dict:
    """Convert DoctrinePatch to dict for JSON serialization"""
    return {
        "patch_id": patch.patch_id,
        "created_at": patch.created_at.isoformat(),
        "author_id": patch.author_id,
        "description": patch.description,
        "changes": [
            {
                "change_type": change.change_type,
                "rule_id": change.rule_id,
                "old_text": change.old_text,
                "new_text": change.new_text,
            }
            for change in patch.changes
        ],
        "status": patch.status.value,
        "rule_sim_report_id": patch.rule_sim_report_id,
        "sim_result_status": patch.sim_result_status.value,
        "deployment_version": patch.deployment_version,
        "deployed_at": patch.deployed_at.isoformat() if patch.deployed_at else None,
    }


def _dict_to_patch(data: dict) -> DoctrinePatch:
    """Convert dict to DoctrinePatch"""
    from jgod.doctrine_v2.models import DoctrineChangeItem
    
    changes = [
        DoctrineChangeItem(
            change_type=ch["change_type"],
            rule_id=ch["rule_id"],
            old_text=ch.get("old_text"),
            new_text=ch.get("new_text"),
        )
        for ch in data["changes"]
    ]
    
    return DoctrinePatch(
        patch_id=data["patch_id"],
        created_at=datetime.fromisoformat(data["created_at"]),
        author_id=data["author_id"],
        description=data["description"],
        changes=changes,
        status=PatchStatus(data["status"]),
        rule_sim_report_id=data.get("rule_sim_report_id"),
        sim_result_status=RuleSimStatus(data.get("sim_result_status", "PENDING")),
        deployment_version=data.get("deployment_version"),
        deployed_at=datetime.fromisoformat(data["deployed_at"]) if data.get("deployed_at") else None,
    )


def _get_storage_path() -> Path:
    """Get the storage path for patches.jsonl"""
    project_root = Path(__file__).parent.parent.parent
    path = project_root / "data" / "doctrine" / "patches.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_patch(patch: DoctrinePatch) -> None:
    """Save a patch to JSONL file"""
    path = _get_storage_path()
    
    # Read existing patches
    patches = _load_all_patches()
    
    # Update or append
    existing_index = None
    for i, p in enumerate(patches):
        if p.patch_id == patch.patch_id:
            existing_index = i
            break
    
    if existing_index is not None:
        patches[existing_index] = patch
    else:
        patches.append(patch)
    
    # Write all patches back
    with open(path, 'w', encoding='utf-8') as f:
        for p in patches:
            f.write(json.dumps(_patch_to_dict(p), ensure_ascii=False) + '\n')
    
    logger.info(f"Saved patch {patch.patch_id}")


def _load_all_patches() -> List[DoctrinePatch]:
    """Load all patches from JSONL file"""
    path = _get_storage_path()
    patches = []
    
    if not path.exists():
        return patches
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    patches.append(_dict_to_patch(data))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse patch line: {e}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load patches: {e}", exc_info=True)
    
    return patches


def load_patch(patch_id: str) -> Optional[DoctrinePatch]:
    """Load a specific patch by ID"""
    try:
        path = _get_storage_path()
        if not path.exists():
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                if data["patch_id"] == patch_id:
                    return _dict_to_patch(data)
        
        return None
    except Exception as e:
        logger.error(f"Failed to load patch {patch_id}: {e}", exc_info=True)
        return None


def list_patches(status: Optional[List[PatchStatus]] = None) -> List[DoctrinePatch]:
    """List patches, optionally filtered by status"""
    all_patches = _load_all_patches()
    
    if status:
        all_patches = [p for p in all_patches if p.status in status]
    
    # Sort by created_at (newest first)
    all_patches.sort(key=lambda p: p.created_at, reverse=True)
    
    return all_patches


def update_patch_status(patch_id: str, new_status: PatchStatus) -> None:
    """Update patch status"""
    patch = load_patch(patch_id)
    if not patch:
        raise ValueError(f"Patch not found: {patch_id}")
    
    patch.status = new_status
    save_patch(patch)


def update_patch_after_sim(
    patch_id: str,
    sim_status: RuleSimStatus,
    rule_sim_report_id: str,
) -> None:
    """Update patch after simulation"""
    patch = load_patch(patch_id)
    if not patch:
        raise ValueError(f"Patch not found: {patch_id}")
    
    patch.sim_result_status = sim_status
    patch.rule_sim_report_id = rule_sim_report_id
    
    # Update status based on sim result
    if sim_status == RuleSimStatus.APPROVED:
        patch.status = PatchStatus.PENDING_REVIEW
    elif sim_status == RuleSimStatus.REJECTED:
        patch.status = PatchStatus.REJECTED_BY_SIM
    
    save_patch(patch)


def update_patch_after_deploy(patch_id: str, deployment_version: int) -> None:
    """Update patch after deployment"""
    patch = load_patch(patch_id)
    if not patch:
        raise ValueError(f"Patch not found: {patch_id}")
    
    patch.deployment_version = deployment_version
    patch.deployed_at = datetime.now()
    patch.status = PatchStatus.DEPLOYED
    save_patch(patch)


def update_patch_revert(patch_id: str) -> None:
    """Update patch after revert"""
    patch = load_patch(patch_id)
    if not patch:
        raise ValueError(f"Patch not found: {patch_id}")
    
    patch.status = PatchStatus.REVERTED
    save_patch(patch)
