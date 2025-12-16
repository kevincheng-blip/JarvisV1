"""
Walk-Forward Storage: JSONL append-only storage for Walk-Forward logs

v0.6.8-A8: Storage for daily logs and learning layer outputs
v0.6.9-A9: Added snapshot and notification storage
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def _get_walkforward_log_path() -> Path:
    """Get walkforward log file path."""
    project_root = Path(__file__).resolve().parents[2]
    research_dir = project_root / "data" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    return research_dir / "walkforward_logs.jsonl"


def _get_drift_events_path() -> Path:
    """Get drift events file path."""
    project_root = Path(__file__).resolve().parents[2]
    research_dir = project_root / "data" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    return research_dir / "drift_events.jsonl"


def save_daily_log(log_entry: Dict) -> None:
    """
    Save daily walkforward log entry (append-only).
    
    Args:
        log_entry: Dict with symbol, date, nav, decision, order, fill, etc.
    """
    storage_path = _get_walkforward_log_path()
    
    # Add timestamp if not present
    if "logged_at" not in log_entry:
        log_entry["logged_at"] = datetime.now().isoformat()
    
    try:
        with open(storage_path, "a", encoding="utf-8") as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        logger.error(f"Failed to save daily log: {e}", exc_info=True)
        raise


def load_daily_logs(
    symbol: str,
    start_date: str,
    end_date: str,
    limit: int = 1000
) -> List[Dict]:
    """
    Load daily logs for a symbol and date range.
    
    Args:
        symbol: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Maximum number of logs to return
        
    Returns:
        List of log dicts (chronological order, oldest first)
    """
    storage_path = _get_walkforward_log_path()
    
    if not storage_path.exists():
        return []
    
    logs = []
    try:
        with open(storage_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if (data.get("symbol") == symbol and
                        data.get("date") >= start_date and
                        data.get("date") <= end_date):
                        logs.append(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON line in {storage_path}: {line}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load daily logs for {symbol}: {e}", exc_info=True)
        return []
    
    # Sort by date ascending
    logs.sort(key=lambda x: x.get("date", ""))
    
    return logs[:limit]


def _get_snapshot_storage_path() -> Path:
    """Get snapshot storage file path."""
    project_root = Path(__file__).resolve().parents[2]
    research_dir = project_root / "data" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    return research_dir / "snapshots.jsonl"


def save_snapshot(snapshot_payload: Dict) -> None:
    """
    Save snapshot payload (append-only).
    
    Args:
        snapshot_payload: Snapshot payload dict
    """
    storage_path = _get_snapshot_storage_path()
    
    try:
        with open(storage_path, "a", encoding="utf-8") as f:
            json.dump(snapshot_payload, f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        logger.error(f"Failed to save snapshot: {e}", exc_info=True)
        raise


def load_snapshot(snapshot_id: str) -> Optional[Dict]:
    """
    Load snapshot by ID.
    
    Args:
        snapshot_id: Snapshot ID
        
    Returns:
        Snapshot payload or None if not found
    """
    storage_path = _get_snapshot_storage_path()
    
    if not storage_path.exists():
        return None
    
    try:
        with open(storage_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("snapshot_id") == snapshot_id:
                        return data
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Failed to load snapshot {snapshot_id}: {e}", exc_info=True)
        return None
    
    return None


def _get_notification_storage_path() -> Path:
    """Get notification storage file path."""
    project_root = Path(__file__).resolve().parents[2]
    research_dir = project_root / "data" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    return research_dir / "notifications.jsonl"


def save_notification(event: Dict) -> None:
    """
    Save notification event (append-only).
    
    Args:
        event: Notification event dict
    """
    storage_path = _get_notification_storage_path()
    
    # Add timestamp if not present
    if "created_at" not in event:
        event["created_at"] = datetime.now().isoformat()
    
    try:
        with open(storage_path, "a", encoding="utf-8") as f:
            json.dump(event, f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        logger.error(f"Failed to save notification: {e}", exc_info=True)
        raise


def list_notifications(n: int = 50) -> List[Dict]:
    """
    List latest N notifications.
    
    Args:
        n: Maximum number of notifications to return
        
    Returns:
        List of notification dicts (newest first)
    """
    storage_path = _get_notification_storage_path()
    
    if not storage_path.exists():
        return []
    
    notifications = []
    try:
        with open(storage_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    notifications.append(data)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Failed to list notifications: {e}", exc_info=True)
        return []
    
    # Sort by created_at descending (newest first)
    notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return notifications[:n]


def latest_notification() -> Optional[Dict]:
    """
    Get latest notification.
    
    Returns:
        Latest notification dict or None
    """
    notifications = list_notifications(n=1)
    return notifications[0] if notifications else None


def _get_portfolio_log_path() -> Path:
    """Get portfolio log file path."""
    project_root = Path(__file__).resolve().parents[2]
    research_dir = project_root / "data" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    return research_dir / "portfolio_logs.jsonl"


def save_portfolio_log(log_entry: Dict) -> None:
    """
    Save portfolio daily log entry (append-only).
    
    Args:
        log_entry: Dict with date, portfolio_nav, per_symbol_nav, etc.
    """
    storage_path = _get_portfolio_log_path()
    
    # Add timestamp if not present
    if "logged_at" not in log_entry:
        log_entry["logged_at"] = datetime.now().isoformat()
    
    try:
        with open(storage_path, "a", encoding="utf-8") as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        logger.error(f"Failed to save portfolio log: {e}", exc_info=True)
        raise


def latest_portfolio_report() -> Dict:
    """
    Get latest portfolio report.
    
    Returns:
        Latest portfolio log dict or default empty report
    """
    storage_path = _get_portfolio_log_path()
    
    if not storage_path.exists():
        return {
            "date": "",
            "portfolio_nav": 0.0,
            "portfolio_cash": 0.0,
            "portfolio_pnl_realized": 0.0,
            "portfolio_pnl_unrealized": 0.0,
            "per_symbol_nav": {},
            "per_symbol_pnl": {},
            "per_symbol_cash": {},
            "notes": "No portfolio data available",
        }
    
    # Read last line (most recent)
    try:
        with open(storage_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1].strip()
                if last_line:
                    return json.loads(last_line)
    except Exception as e:
        logger.error(f"Failed to load latest portfolio report: {e}", exc_info=True)
    
    return {
        "date": "",
        "portfolio_nav": 0.0,
        "portfolio_cash": 0.0,
        "portfolio_pnl_realized": 0.0,
        "portfolio_pnl_unrealized": 0.0,
        "per_symbol_nav": {},
        "per_symbol_pnl": {},
        "per_symbol_cash": {},
        "notes": "Failed to load portfolio data",
    }


def list_portfolio_logs(n: int = 20) -> List[Dict]:
    """
    List latest N portfolio logs.
    
    Args:
        n: Maximum number of logs to return
        
    Returns:
        List of portfolio log dicts (newest first)
    """
    storage_path = _get_portfolio_log_path()
    
    if not storage_path.exists():
        return []
    
    logs = []
    try:
        with open(storage_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    logs.append(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON line in {storage_path}: {line}")
                    continue
    except Exception as e:
        logger.error(f"Failed to list portfolio logs: {e}", exc_info=True)
        return []
    
    # Sort by date descending (newest first)
    logs.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    return logs[:n]


def _get_intelligence_status_path() -> Path:
    """Get intelligence status storage file path."""
    project_root = Path(__file__).resolve().parents[2]
    research_dir = project_root / "data" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    return research_dir / "intelligence_status.jsonl"


def save_intelligence_status(snapshot: Dict) -> None:
    """
    Save intelligence status snapshot (append-only).
    
    Args:
        snapshot: IntelligenceStatusSnapshot as dict
    """
    storage_path = _get_intelligence_status_path()
    
    # Add timestamp if not present
    if "created_at" not in snapshot:
        snapshot["created_at"] = datetime.now().isoformat()
    
    try:
        with open(storage_path, "a", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        logger.error(f"Failed to save intelligence status: {e}", exc_info=True)
        raise


def latest_intelligence_status() -> Dict:
    """
    Get latest intelligence status snapshot.
    
    Returns:
        Latest snapshot dict or default empty state
    """
    storage_path = _get_intelligence_status_path()
    
    if not storage_path.exists():
        return _get_default_intelligence_status()
    
    # Read last line (most recent)
    try:
        with open(storage_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1].strip()
                if last_line:
                    return json.loads(last_line)
    except Exception as e:
        logger.error(f"Failed to load latest intelligence status: {e}", exc_info=True)
    
    return _get_default_intelligence_status()


def _get_default_intelligence_status() -> Dict:
    """Get default empty intelligence status."""
    return {
        "evolution": [
            {"layer": "strategy", "progress": 0, "status": "STABLE", "last_updated": "", "details": {}},
            {"layer": "thought", "progress": 0, "status": "STABLE", "last_updated": "", "details": {}},
            {"layer": "method", "progress": 0, "status": "STABLE", "last_updated": "", "details": {}},
        ],
        "activities": [],
        "recent_events": [],
        "health_flags": {},
        "snapshot_id": "",
        "created_at": datetime.now().isoformat(),
    }


def append_evolution_event(event: Dict) -> None:
    """
    Append evolution event (append-only).
    
    Args:
        event: EvolutionEvent as dict
    """
    storage_path = _get_intelligence_status_path()
    
    # Add timestamp if not present
    if "created_at" not in event:
        event["created_at"] = datetime.now().isoformat()
    
    try:
        with open(storage_path, "a", encoding="utf-8") as f:
            json.dump({"type": "event", "event": event}, f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        logger.error(f"Failed to append evolution event: {e}", exc_info=True)
        raise


def list_evolution_events(n: int = 50) -> List[Dict]:
    """
    List latest N evolution events.
    
    Args:
        n: Maximum number of events to return
        
    Returns:
        List of event dicts (newest first)
    """
    storage_path = _get_intelligence_status_path()
    
    if not storage_path.exists():
        return []
    
    events = []
    try:
        with open(storage_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("type") == "event" and "event" in data:
                        events.append(data["event"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON line in {storage_path}: {line}")
                    continue
    except Exception as e:
        logger.error(f"Failed to list evolution events: {e}", exc_info=True)
        return []
    
    # Sort by created_at descending (newest first)
    events.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return events[:n]


# ============================================================================
# Drift Events Storage (v0.6.13-P1.1)
# ============================================================================

def save_drift_event(event: Dict) -> None:
    """
    Save drift event (append-only).
    
    Args:
        event: Dict with symbol, date, method_version, baseline_window,
               current_window, drift_score, features_used, created_at
    """
    storage_path = _get_drift_events_path()
    
    # Add timestamp if not present
    if "created_at" not in event:
        event["created_at"] = datetime.now().isoformat()
    
    try:
        with open(storage_path, "a", encoding="utf-8") as f:
            json.dump(event, f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        logger.error(f"Failed to save drift event: {e}", exc_info=True)
        raise


def latest_drift_event(symbol: Optional[str] = None) -> Optional[Dict]:
    """
    Get latest drift event for a symbol (or any symbol if symbol is None).
    
    Args:
        symbol: Optional symbol filter
    
    Returns:
        Latest drift event dict, or None if no data
    """
    storage_path = _get_drift_events_path()
    
    if not storage_path.exists():
        return None
    
    latest = None
    latest_time = ""
    
    try:
        with open(storage_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    # Filter by symbol if provided
                    if symbol and event.get("symbol") != symbol:
                        continue
                    # Track latest by created_at
                    event_time = event.get("created_at", "")
                    if event_time > latest_time:
                        latest_time = event_time
                        latest = event
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON line in {storage_path}: {line}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load latest drift event: {e}", exc_info=True)
        return None
    
    return latest

