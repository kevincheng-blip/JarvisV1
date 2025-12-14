"""
Feature Storage: JSONL append-only storage for Feature DB

v0.6.7-A7.5: Feature DB storage layer
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from jgod.data.feature_models import FeatureSchema

logger = logging.getLogger(__name__)


def _get_storage_path() -> Path:
    """Get storage file path."""
    # Project root is jgod's parent's parent
    project_root = Path(__file__).resolve().parents[2]
    features_dir = project_root / "data" / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    return features_dir / "features.jsonl"


def save_feature(item: FeatureSchema) -> None:
    """
    Save feature to JSONL (append-only).
    
    Args:
        item: FeatureSchema to save
    """
    storage_path = _get_storage_path()
    
    try:
        with open(storage_path, "a", encoding="utf-8") as f:
            json.dump(item.to_dict(), f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        logger.error(f"Failed to save feature {item.symbol}/{item.date}/{item.version}: {e}", exc_info=True)
        raise


def load_feature(
    symbol: str,
    date: str,
    version: str = "v1.0"
) -> Optional[FeatureSchema]:
    """
    Load feature by key (symbol, date, version).
    
    Args:
        symbol: Stock symbol
        date: Date string (YYYY-MM-DD)
        version: Feature version
        
    Returns:
        FeatureSchema or None if not found
        
    Note: Uses "last one wins" strategy (append-only, same key takes last entry).
    """
    storage_path = _get_storage_path()
    
    if not storage_path.exists():
        return None
    
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
                    if (data.get("symbol") == symbol and
                        data.get("date") == date and
                        data.get("version") == version):
                        result = FeatureSchema.from_dict(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON line in {storage_path}: {line}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load feature {symbol}/{date}/{version}: {e}", exc_info=True)
        return None
    
    return result


def has_feature(
    symbol: str,
    date: str,
    version: str = "v1.0"
) -> bool:
    """
    Check if feature exists.
    
    Args:
        symbol: Stock symbol
        date: Date string (YYYY-MM-DD)
        version: Feature version
        
    Returns:
        True if feature exists, False otherwise
    """
    return load_feature(symbol, date, version) is not None


def list_features(
    symbol: str,
    n: int = 50,
    version: str = "v1.0"
) -> List[FeatureSchema]:
    """
    List latest N features for a symbol (by date, descending).
    
    Args:
        symbol: Stock symbol
        n: Maximum number of features to return
        version: Feature version
        
    Returns:
        List of FeatureSchema (sorted by date descending, newest first)
    """
    storage_path = _get_storage_path()
    
    if not storage_path.exists():
        return []
    
    features = []
    try:
        with open(storage_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if (data.get("symbol") == symbol and
                        data.get("version") == version):
                        features.append(FeatureSchema.from_dict(data))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON line in {storage_path}: {line}")
                    continue
    except Exception as e:
        logger.error(f"Failed to list features for {symbol}/{version}: {e}", exc_info=True)
        return []
    
    # Sort by date descending (newest first), then take last N
    # Use "last one wins" for same date
    seen_dates = {}
    for feature in features:
        date_key = feature.date
        if date_key not in seen_dates:
            seen_dates[date_key] = feature
        else:
            # Keep the last one (already in list, so this one wins)
            seen_dates[date_key] = feature
    
    unique_features = list(seen_dates.values())
    unique_features.sort(key=lambda x: x.date, reverse=True)
    
    return unique_features[:n]

