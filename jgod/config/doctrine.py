"""
Doctrine Configuration: Versioned doctrine management

v0.6.8-A8: Doctrine versioning, patch application, and rollback
"""

import logging
import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class DoctrineConfig:
    """Doctrine configuration with version."""
    version: str = "v1.0"
    risk_mapping: Dict[str, float] = field(default_factory=lambda: {
        "STABLE": 0.70,
        "WATCH": 0.45,
        "VOLATILE": 0.25,
        "NO_DATA": 0.20,
    })
    composite_weights: Dict[str, float] = field(default_factory=lambda: {
        "avg_return_proxy": 1.0,
        "max_drawdown_proxy": -0.9,
        "hit_rate_proxy": 0.15,
        "turnover_proxy": -0.12,
        "decision_consistency": 0.08,
    })
    meta: Dict = field(default_factory=dict)  # Created_at, applied_patches, etc.
    
    def to_dict(self) -> Dict:
        """Convert to dict for storage."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DoctrineConfig":
        """Create from dict."""
        return cls(
            version=data.get("version", "v1.0"),
            risk_mapping=data.get("risk_mapping", {}),
            composite_weights=data.get("composite_weights", {}),
            meta=data.get("meta", {}),
        )


def _get_doctrine_storage_path() -> Path:
    """Get doctrine storage file path."""
    project_root = Path(__file__).resolve().parents[2]
    config_dir = project_root / "data" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "doctrine.jsonl"


def load_doctrine(version: str = "v1.0") -> Optional[DoctrineConfig]:
    """
    Load doctrine configuration by version.
    
    Args:
        version: Doctrine version
        
    Returns:
        DoctrineConfig or None if not found
    """
    storage_path = _get_doctrine_storage_path()
    
    if not storage_path.exists():
        # Return default if no storage
        return DoctrineConfig(version=version)
    
    # Linear scan (last one wins)
    result = None
    try:
        with open(storage_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("version") == version:
                        result = DoctrineConfig.from_dict(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON line in {storage_path}: {line}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load doctrine {version}: {e}", exc_info=True)
        return None
    
    if result is None:
        # Return default if version not found
        return DoctrineConfig(version=version)
    
    return result


def save_doctrine(config: DoctrineConfig) -> None:
    """
    Save doctrine configuration (append-only).
    
    Args:
        config: DoctrineConfig to save
    """
    storage_path = _get_doctrine_storage_path()
    
    # Add metadata
    if "created_at" not in config.meta:
        config.meta["created_at"] = datetime.now().isoformat()
    
    try:
        with open(storage_path, "a", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        logger.error(f"Failed to save doctrine {config.version}: {e}", exc_info=True)
        raise


def list_doctrine_versions() -> List[str]:
    """
    List all available doctrine versions.
    
    Returns:
        List of version strings
    """
    storage_path = _get_doctrine_storage_path()
    
    if not storage_path.exists():
        return ["v1.0"]  # Default version
    
    versions = set()
    try:
        with open(storage_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    version = data.get("version")
                    if version:
                        versions.add(version)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Failed to list doctrine versions: {e}", exc_info=True)
        return ["v1.0"]
    
    if not versions:
        return ["v1.0"]
    
    return sorted(list(versions))


def apply_patch(
    base_version: str,
    patch: Dict,
    new_version: str,
    *,
    patch_id: Optional[str] = None,
    snapshot_id: Optional[str] = None,
    layer: Optional[str] = None,
) -> DoctrineConfig:
    """
    Apply patch to create new doctrine version.
    
    v0.6.9-A9: Supports auto-apply from Runner.
    
    Args:
        base_version: Base doctrine version
        patch: Patch dict (from TuningPatch or manual)
        new_version: New version name
        patch_id: Optional patch ID (for tracking)
        snapshot_id: Optional snapshot ID (for consistency)
        layer: Optional layer name (thought/method/strategy)
        
    Returns:
        New DoctrineConfig
    """
    base_config = load_doctrine(base_version)
    if base_config is None:
        raise ValueError(f"Base doctrine version {base_version} not found")
    
    # Create new config
    meta = {
        "base_version": base_version,
        "applied_patch": patch,
        "created_at": datetime.now().isoformat(),
    }
    
    if patch_id:
        meta["patch_id"] = patch_id
    if snapshot_id:
        meta["snapshot_id"] = snapshot_id
    if layer:
        meta["layer"] = layer
    
    new_config = DoctrineConfig(
        version=new_version,
        risk_mapping=base_config.risk_mapping.copy(),
        composite_weights=base_config.composite_weights.copy(),
        meta=meta,
    )
    
    # Apply patch changes
    target = patch.get("target", "")
    changes = patch.get("changes", {})
    
    if target == "risk_mapping":
        new_config.risk_mapping.update(changes)
    elif target == "composite_weights":
        new_config.composite_weights.update(changes)
    else:
        # Generic update
        if target in new_config.meta:
            new_config.meta[target].update(changes)
        else:
            new_config.meta[target] = changes
    
    # Save new version
    save_doctrine(new_config)
    
    return new_config


def rollback_to_version(version: str) -> DoctrineConfig:
    """
    Rollback to a previous doctrine version.
    
    Args:
        version: Target version to rollback to
        
    Returns:
        DoctrineConfig (loaded from storage)
    """
    config = load_doctrine(version)
    if config is None:
        raise ValueError(f"Doctrine version {version} not found")
    
    # Create a new version with rollback marker
    rollback_version = f"{version}-rollback-{datetime.now().strftime('%Y%m%d')}"
    rollback_config = DoctrineConfig(
        version=rollback_version,
        risk_mapping=config.risk_mapping.copy(),
        composite_weights=config.composite_weights.copy(),
        meta={
            "rollback_from": "current",
            "rollback_to": version,
            "created_at": datetime.now().isoformat(),
        },
    )
    
    save_doctrine(rollback_config)
    
    return rollback_config

