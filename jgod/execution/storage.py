"""
Execution Storage: JSONL append-only storage for ledger snapshots
"""

import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def _get_ledger_storage_path() -> Path:
    """Get path to ledger snapshots JSONL file."""
    data_dir = Path("data/execution")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "ledger_snapshots.jsonl"


def save_ledger_snapshot(snapshot: Dict) -> str:
    """
    Save ledger snapshot to JSONL file.
    
    Args:
        snapshot: Snapshot dict (must include symbol, created_at, and ledger data)
        
    Returns:
        snapshot_id (UUID string)
    """
    snapshot_id = str(uuid.uuid4())
    snapshot["snapshot_id"] = snapshot_id
    
    if "created_at" not in snapshot:
        snapshot["created_at"] = datetime.now().isoformat()
    
    path = _get_ledger_storage_path()
    
    try:
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(snapshot, ensure_ascii=False) + '\n')
        logger.info(f"Saved ledger snapshot {snapshot_id} for {snapshot.get('symbol', 'unknown')}")
    except Exception as e:
        logger.error(f"Failed to save ledger snapshot: {e}", exc_info=True)
        raise
    
    return snapshot_id


def load_latest(symbol: str) -> Optional[Dict]:
    """
    Load latest ledger snapshot for a symbol.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Latest snapshot dict or None if not found
    """
    path = _get_ledger_storage_path()
    
    if not path.exists():
        return None
    
    latest = None
    latest_time = None
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if data.get("symbol") == symbol:
                        created_at = data.get("created_at", "")
                        if isinstance(created_at, str):
                            try:
                                created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            except (ValueError, AttributeError):
                                created_at_dt = datetime.fromisoformat(created_at)
                        else:
                            created_at_dt = created_at
                        
                        if latest_time is None or created_at_dt > latest_time:
                            latest = data
                            latest_time = created_at_dt
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse ledger line: {e}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load ledger snapshot: {e}", exc_info=True)
    
    return latest


def list_latest(symbol: str, n: int = 20) -> List[Dict]:
    """
    List latest N ledger snapshots for a symbol.
    
    Args:
        symbol: Stock symbol
        n: Maximum number of snapshots to return
        
    Returns:
        List of snapshot dicts (newest first)
    """
    path = _get_ledger_storage_path()
    snapshots = []
    
    if not path.exists():
        return snapshots
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if data.get("symbol") == symbol:
                        # Parse created_at if it's a string
                        if "created_at" in data and isinstance(data["created_at"], str):
                            try:
                                data["created_at"] = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
                            except (ValueError, AttributeError):
                                try:
                                    data["created_at"] = datetime.fromisoformat(data["created_at"])
                                except:
                                    pass
                        snapshots.append(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse ledger line: {e}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load ledger snapshots: {e}", exc_info=True)
    
    # Sort by created_at (newest first) and take top N
    def get_sort_key(s: Dict) -> str:
        created_at = s.get("created_at")
        if isinstance(created_at, datetime):
            return created_at.isoformat()
        elif isinstance(created_at, str):
            return created_at
        return ""
    
    snapshots.sort(key=get_sort_key, reverse=True)
    return snapshots[:n]

