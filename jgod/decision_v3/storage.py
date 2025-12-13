"""
Decision V3 Snapshot Storage

JSONL-based storage for Decision V3 snapshots.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


def _get_storage_path() -> Path:
    """Get the storage path for snapshots.jsonl"""
    project_root = Path(__file__).parent.parent.parent
    path = project_root / "data" / "decision_v3" / "snapshots.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_snapshot(snapshot: Dict) -> str:
    """
    Save a snapshot to JSONL file.
    
    Args:
        snapshot: Snapshot dict (must contain snapshot_id or will generate one)
        
    Returns:
        snapshot_id (str)
    """
    path = _get_storage_path()
    
    # Generate snapshot_id if not present
    if "snapshot_id" not in snapshot:
        snapshot["snapshot_id"] = str(uuid.uuid4())
    
    # Ensure created_at is ISO format string
    if "created_at" in snapshot and isinstance(snapshot["created_at"], datetime):
        snapshot["created_at"] = snapshot["created_at"].isoformat()
    elif "created_at" not in snapshot:
        snapshot["created_at"] = datetime.now().isoformat()
    
    # Append to file (JSONL format)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(snapshot, ensure_ascii=False, default=str) + '\n')
    
    logger.info(f"Saved Decision V3 snapshot {snapshot['snapshot_id']} for {snapshot.get('symbol', 'unknown')}")
    return snapshot["snapshot_id"]


def load_latest(symbol: str) -> Optional[Dict]:
    """
    Load the latest snapshot for a symbol.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Snapshot dict if found, None otherwise
    """
    path = _get_storage_path()
    
    if not path.exists():
        return None
    
    latest_snapshot = None
    latest_time = None
    
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
                                data["created_at"] = datetime.fromisoformat(data["created_at"])
                            except (ValueError, AttributeError):
                                pass  # Keep as string if parsing fails
                        
                        if latest_time is None or (
                            isinstance(data.get("created_at"), datetime) and
                            (latest_time is None or data["created_at"] > latest_time)
                        ) or (
                            isinstance(data.get("created_at"), str) and
                            (latest_time is None or data["created_at"] > latest_time)
                        ):
                            latest_snapshot = data
                            if isinstance(data.get("created_at"), datetime):
                                latest_time = data["created_at"]
                            elif isinstance(data.get("created_at"), str):
                                latest_time = data["created_at"]
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse snapshot line: {e}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load snapshots: {e}", exc_info=True)
    
    return latest_snapshot


def list_latest(symbol: str, n: int = 20) -> List[Dict]:
    """
    List the latest N snapshots for a symbol.
    
    Args:
        symbol: Stock symbol
        n: Maximum number of snapshots to return
        
    Returns:
        List of snapshot dicts (newest first)
    """
    path = _get_storage_path()
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
                                data["created_at"] = datetime.fromisoformat(data["created_at"])
                            except (ValueError, AttributeError):
                                pass
                        snapshots.append(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse snapshot line: {e}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load snapshots: {e}", exc_info=True)
    
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


# Evaluation storage functions

def _get_eval_storage_path() -> Path:
    """Get the storage path for evaluations.jsonl"""
    project_root = Path(__file__).parent.parent.parent
    path = project_root / "data" / "decision_v3" / "evaluations.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_evaluation(evaluation: Dict) -> str:
    """
    Save an evaluation to JSONL file.
    
    Args:
        evaluation: Evaluation dict (must contain eval_id or will generate one)
        
    Returns:
        eval_id (str)
    """
    path = _get_eval_storage_path()
    
    # Generate eval_id if not present
    if "eval_id" not in evaluation:
        evaluation["eval_id"] = str(uuid.uuid4())
    
    # Ensure created_at is ISO format string
    if "created_at" in evaluation and isinstance(evaluation["created_at"], datetime):
        evaluation["created_at"] = evaluation["created_at"].isoformat()
    elif "created_at" not in evaluation:
        evaluation["created_at"] = datetime.now().isoformat()
    
    # Append to file (JSONL format)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(evaluation, ensure_ascii=False, default=str) + '\n')
    
    logger.info(f"Saved Decision V3 evaluation {evaluation['eval_id']} for {evaluation.get('symbol', 'unknown')}")
    return evaluation["eval_id"]


def load_latest_evaluation(symbol: str) -> Optional[Dict]:
    """
    Load the latest evaluation for a symbol.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Evaluation dict if found, None otherwise
    """
    path = _get_eval_storage_path()
    
    if not path.exists():
        return None
    
    latest_eval = None
    latest_time = None
    
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
                                data["created_at"] = datetime.fromisoformat(data["created_at"])
                            except (ValueError, AttributeError):
                                pass
                        
                        if latest_time is None or (
                            isinstance(data.get("created_at"), datetime) and
                            (latest_time is None or data["created_at"] > latest_time)
                        ) or (
                            isinstance(data.get("created_at"), str) and
                            (latest_time is None or data["created_at"] > latest_time)
                        ):
                            latest_eval = data
                            if isinstance(data.get("created_at"), datetime):
                                latest_time = data["created_at"]
                            elif isinstance(data.get("created_at"), str):
                                latest_time = data["created_at"]
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse evaluation line: {e}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load evaluations: {e}", exc_info=True)
    
    return latest_eval


def list_evaluations(symbol: str, n: int = 20) -> List[Dict]:
    """
    List the latest N evaluations for a symbol.
    
    Args:
        symbol: Stock symbol
        n: Maximum number of evaluations to return
        
    Returns:
        List of evaluation dicts (newest first)
    """
    path = _get_eval_storage_path()
    evaluations = []
    
    if not path.exists():
        return evaluations
    
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
                                data["created_at"] = datetime.fromisoformat(data["created_at"])
                            except (ValueError, AttributeError):
                                pass
                        evaluations.append(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse evaluation line: {e}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load evaluations: {e}", exc_info=True)
    
    # Sort by created_at (newest first) and take top N
    def get_sort_key(e: Dict) -> str:
        created_at = e.get("created_at")
        if isinstance(created_at, datetime):
            return created_at.isoformat()
        elif isinstance(created_at, str):
            return created_at
        return ""
    
    evaluations.sort(key=get_sort_key, reverse=True)
    return evaluations[:n]


# Compare storage functions

def _get_compare_storage_path() -> Path:
    """Get the storage path for compare.jsonl"""
    project_root = Path(__file__).parent.parent.parent
    path = project_root / "data" / "decision_v3" / "compare.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_compare(compare: Dict) -> str:
    """
    Save a compare snapshot to JSONL file.
    
    Args:
        compare: Compare dict (must contain compare_id or will generate one)
        
    Returns:
        compare_id (str)
    """
    path = _get_compare_storage_path()
    
    # Generate compare_id if not present
    if "compare_id" not in compare:
        compare["compare_id"] = str(uuid.uuid4())
    
    # Ensure created_at is ISO format string
    if "created_at" in compare and isinstance(compare["created_at"], datetime):
        compare["created_at"] = compare["created_at"].isoformat()
    elif "created_at" not in compare:
        compare["created_at"] = datetime.now().isoformat()
    
    # Append to file (JSONL format)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(compare, ensure_ascii=False, default=str) + '\n')
    
    logger.info(f"Saved Decision V3 compare {compare['compare_id']} for {compare.get('symbol', 'unknown')}")
    return compare["compare_id"]


def load_latest_compare(symbol: str) -> Optional[Dict]:
    """
    Load the latest compare snapshot for a symbol.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Compare dict if found, None otherwise
    """
    path = _get_compare_storage_path()
    
    if not path.exists():
        return None
    
    latest_compare = None
    latest_time = None
    
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
                                data["created_at"] = datetime.fromisoformat(data["created_at"])
                            except (ValueError, AttributeError):
                                pass
                        
                        if latest_time is None or (
                            isinstance(data.get("created_at"), datetime) and
                            (latest_time is None or data["created_at"] > latest_time)
                        ) or (
                            isinstance(data.get("created_at"), str) and
                            (latest_time is None or data["created_at"] > latest_time)
                        ):
                            latest_compare = data
                            if isinstance(data.get("created_at"), datetime):
                                latest_time = data["created_at"]
                            elif isinstance(data.get("created_at"), str):
                                latest_time = data["created_at"]
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse compare line: {e}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load compares: {e}", exc_info=True)
    
    return latest_compare


def list_compares(symbol: str, n: int = 20) -> List[Dict]:
    """
    List the latest N compare snapshots for a symbol.
    
    Args:
        symbol: Stock symbol
        n: Maximum number of compares to return
        
    Returns:
        List of compare dicts (newest first)
    """
    path = _get_compare_storage_path()
    compares = []
    
    if not path.exists():
        return compares
    
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
                                data["created_at"] = datetime.fromisoformat(data["created_at"])
                            except (ValueError, AttributeError):
                                pass
                        compares.append(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse compare line: {e}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load compares: {e}", exc_info=True)
    
    # Sort by created_at (newest first) and take top N
    def get_sort_key(c: Dict) -> str:
        created_at = c.get("created_at")
        if isinstance(created_at, datetime):
            return created_at.isoformat()
        elif isinstance(created_at, str):
            return created_at
        return ""
    
    compares.sort(key=get_sort_key, reverse=True)
    return compares[:n]

