"""
Strategy Performance Feed Storage

JSONL-based storage for performance snapshots.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, date

from jgod.strategy_perf.models import PerformanceSnapshot, StrategyPerformanceMetrics, PerformanceGrade

logger = logging.getLogger(__name__)


def _snapshot_to_dict(snapshot: PerformanceSnapshot) -> dict:
    """Convert PerformanceSnapshot to dict for JSON serialization"""
    return {
        "snapshot_id": snapshot.snapshot_id,
        "created_at": snapshot.created_at.isoformat(),
        "symbol": snapshot.symbol,
        "limit": snapshot.limit,
        "window": snapshot.window,
        "items": [
            {
                "strategy_id": item.strategy_id,
                "n_points": item.n_points,
                "avg_return_proxy": item.avg_return_proxy,
                "sharpe_proxy": item.sharpe_proxy,
                "max_drawdown_proxy": item.max_drawdown_proxy,
                "turnover_proxy": item.turnover_proxy,
                "decay_slope": item.decay_slope,
                "grade": item.grade.value,
            }
            for item in snapshot.items
        ],
    }


def _dict_to_snapshot(data: dict) -> PerformanceSnapshot:
    """Convert dict to PerformanceSnapshot"""
    items = [
        StrategyPerformanceMetrics(
            strategy_id=item["strategy_id"],
            n_points=item["n_points"],
            avg_return_proxy=item["avg_return_proxy"],
            sharpe_proxy=item["sharpe_proxy"],
            max_drawdown_proxy=item["max_drawdown_proxy"],
            turnover_proxy=item["turnover_proxy"],
            decay_slope=item["decay_slope"],
            grade=PerformanceGrade(item["grade"]),
        )
        for item in data.get("items", [])
    ]
    
    return PerformanceSnapshot(
        snapshot_id=data["snapshot_id"],
        created_at=datetime.fromisoformat(data["created_at"]),
        symbol=data["symbol"],
        limit=data.get("limit", 60),
        window=data.get("window", 20),
        items=items,
    )


def _get_storage_path() -> Path:
    """Get the storage path for perf_snapshots.jsonl"""
    project_root = Path(__file__).parent.parent.parent
    path = project_root / "data" / "strategy_perf" / "perf_snapshots.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_snapshot(snapshot: PerformanceSnapshot) -> None:
    """Save a snapshot to JSONL file"""
    path = _get_storage_path()
    
    # Append to file (JSONL format)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(_snapshot_to_dict(snapshot), ensure_ascii=False) + '\n')
    
    logger.info(f"Saved performance snapshot {snapshot.snapshot_id} for {snapshot.symbol}")


def load_latest(symbol: str) -> Optional[PerformanceSnapshot]:
    """Load the latest snapshot for a symbol"""
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
                    if data["symbol"] == symbol:
                        snapshot = _dict_to_snapshot(data)
                        if latest_time is None or snapshot.created_at > latest_time:
                            latest_snapshot = snapshot
                            latest_time = snapshot.created_at
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse snapshot line: {e}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load snapshots: {e}", exc_info=True)
    
    return latest_snapshot


def list_latest(n: int = 10) -> List[PerformanceSnapshot]:
    """List the latest N snapshots (across all symbols)"""
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
                    snapshots.append(_dict_to_snapshot(data))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse snapshot line: {e}")
                    continue
    except Exception as e:
        logger.error(f"Failed to load snapshots: {e}", exc_info=True)
    
    # Sort by created_at (newest first) and take top N
    snapshots.sort(key=lambda s: s.created_at, reverse=True)
    return snapshots[:n]

