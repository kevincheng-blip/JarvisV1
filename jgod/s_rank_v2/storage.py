"""
S-Rank Engine V2 Storage

JSONL-based storage for recommendation snapshots.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, date

from jgod.s_rank_v2.models import RecommendationSnapshot, RecommendationItem, Metrics, StabilityGrade

logger = logging.getLogger(__name__)


def _snapshot_to_dict(snapshot: RecommendationSnapshot) -> dict:
    """Convert RecommendationSnapshot to dict for JSON serialization"""
    return {
        "snapshot_id": snapshot.snapshot_id,
        "created_at": snapshot.created_at.isoformat(),
        "symbol": snapshot.symbol,
        "start_date": snapshot.start_date.isoformat() if snapshot.start_date else None,
        "end_date": snapshot.end_date.isoformat() if snapshot.end_date else None,
        "items": [
            {
                "strategy": item.strategy,
                "weight": item.weight,
                "score": item.score,
            }
            for item in snapshot.items
        ],
        "weights": snapshot.weights,
        "metrics": {
            "n_points": snapshot.metrics.n_points if snapshot.metrics else 0,
            "score_std": snapshot.metrics.score_std if snapshot.metrics else 0.0,
            "max_abs_delta": snapshot.metrics.max_abs_delta if snapshot.metrics else 0.0,
            "trend_slope": snapshot.metrics.trend_slope if snapshot.metrics else 0.0,
            "stability_grade": snapshot.metrics.stability_grade.value if snapshot.metrics else "NO_DATA",
        },
        "rationale": snapshot.rationale,
    }


def _dict_to_snapshot(data: dict) -> RecommendationSnapshot:
    """Convert dict to RecommendationSnapshot"""
    items = [
        RecommendationItem(
            strategy=item["strategy"],
            weight=item["weight"],
            score=item["score"],
        )
        for item in data.get("items", [])
    ]
    
    metrics_data = data.get("metrics", {})
    metrics = Metrics(
        n_points=metrics_data.get("n_points", 0),
        score_std=metrics_data.get("score_std", 0.0),
        max_abs_delta=metrics_data.get("max_abs_delta", 0.0),
        trend_slope=metrics_data.get("trend_slope", 0.0),
        stability_grade=StabilityGrade(metrics_data.get("stability_grade", "NO_DATA")),
    ) if metrics_data else None
    
    start_date = None
    if data.get("start_date"):
        start_date = datetime.fromisoformat(data["start_date"]).date()
    
    end_date = None
    if data.get("end_date"):
        end_date = datetime.fromisoformat(data["end_date"]).date()
    
    return RecommendationSnapshot(
        snapshot_id=data["snapshot_id"],
        created_at=datetime.fromisoformat(data["created_at"]),
        symbol=data["symbol"],
        start_date=start_date,
        end_date=end_date,
        items=items,
        weights=data.get("weights", {}),
        metrics=metrics,
        rationale=data.get("rationale", {}),
    )


def _get_storage_path() -> Path:
    """Get the storage path for recommendations.jsonl"""
    project_root = Path(__file__).parent.parent.parent
    path = project_root / "data" / "s_rank_v2" / "recommendations.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_snapshot(snapshot: RecommendationSnapshot) -> None:
    """Save a snapshot to JSONL file"""
    path = _get_storage_path()
    
    # Append to file (JSONL format)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(_snapshot_to_dict(snapshot), ensure_ascii=False) + '\n')
    
    logger.info(f"Saved recommendation snapshot {snapshot.snapshot_id} for {snapshot.symbol}")


def load_latest(symbol: str) -> Optional[RecommendationSnapshot]:
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


def list_latest(n: int = 10) -> List[RecommendationSnapshot]:
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

