"""
Oracle Scorecard Summary Calculator.
"""
from typing import Dict, List, Optional
from pathlib import Path
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def calculate_spearman_rank_ic(pred_values: List[float], realized_values: List[float]) -> float:
    """
    Calculate Spearman rank correlation (Rank IC).
    
    Args:
        pred_values: List of predicted values
        realized_values: List of realized values
        
    Returns:
        Spearman correlation coefficient (-1 to 1)
    """
    if len(pred_values) != len(realized_values) or len(pred_values) < 2:
        return 0.0
    
    # Rank the values
    def rank_data(data):
        sorted_data = sorted(enumerate(data), key=lambda x: x[1])
        ranks = [0] * len(data)
        for rank, (idx, _) in enumerate(sorted_data, start=1):
            ranks[idx] = rank
        return ranks
    
    pred_ranks = rank_data(pred_values)
    realized_ranks = rank_data(realized_values)
    
    # Calculate Pearson correlation of ranks
    n = len(pred_ranks)
    pred_mean = sum(pred_ranks) / n
    realized_mean = sum(realized_ranks) / n
    
    numerator = sum((pred_ranks[i] - pred_mean) * (realized_ranks[i] - realized_mean) for i in range(n))
    pred_var = sum((pred_ranks[i] - pred_mean) ** 2 for i in range(n))
    realized_var = sum((realized_ranks[i] - realized_mean) ** 2 for i in range(n))
    
    if pred_var == 0 or realized_var == 0:
        return 0.0
    
    return numerator / (pred_var ** 0.5 * realized_var ** 0.5)


def calculate_star_reliability_index(star_calibration: List[Dict]) -> float:
    """
    Calculate star reliability index.
    
    Args:
        star_calibration: List of {star, count, hit_rate, mae}
        
    Returns:
        Reliability index (0-1)
    """
    if len(star_calibration) < 2:
        return 0.0
    
    # Sort by star
    sorted_cal = sorted(star_calibration, key=lambda x: x["star"])
    
    # Check if hit_rate is monotonically non-decreasing
    violations = 0
    for i in range(1, len(sorted_cal)):
        if sorted_cal[i]["hit_rate"] < sorted_cal[i-1]["hit_rate"]:
            violations += 1
    
    reliability = max(0.0, 1.0 - (violations * 0.25))
    return round(reliability, 3)


def calculate_summary(
    scorecard_paths: Dict[str, Path],
    as_of_date: str,
    universe: str = "TOP50"
) -> Dict:
    """
    Calculate Oracle Scorecard Summary.
    
    Args:
        scorecard_paths: Dict mapping horizon -> Path to scorecard JSONL
        as_of_date: YYYY-MM-DD
        universe: Universe name
        
    Returns:
        Summary dict
    """
    # Load all scorecards
    all_rows_by_horizon = {}
    for horizon, path in scorecard_paths.items():
        if not path.exists():
            logger.warning(f"Scorecard not found: {path}")
            continue
        
        rows = []
        with open(path, 'r') as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
        all_rows_by_horizon[horizon] = rows
    
    if not all_rows_by_horizon:
        raise ValueError("No scorecard data found")
    
    # Data quality statistics
    baseline_source_counts = defaultdict(int)
    truth_source_counts_by_horizon = {}
    missing_truth_symbols_by_horizon = {}
    
    for horizon, rows in all_rows_by_horizon.items():
        truth_sources = defaultdict(int)
        missing_symbols = []
        
        for row in rows:
            baseline_source_counts[row.get("baseline_source", "unknown")] += 1
            truth_source = row.get("truth_source", "unknown")
            truth_sources[truth_source] += 1
            
            if truth_source == "none":
                missing_symbols.append(row["symbol"])
        
        truth_source_counts_by_horizon[horizon] = dict(truth_sources)
        missing_truth_symbols_by_horizon[horizon] = missing_symbols[:20]  # Top 20
    
    # Forecast quality by horizon
    forecast_quality_by_horizon = {}
    
    for horizon, rows in all_rows_by_horizon.items():
        if not rows:
            continue
        
        # Overall metrics
        total = len(rows)
        hit_count = sum(1 for r in rows if r.get("hit_direction", False))
        hit_rate = hit_count / total if total > 0 else 0.0
        
        abs_errors = [r.get("abs_error", 0.0) for r in rows]
        mae = sum(abs_errors) / len(abs_errors) if abs_errors else 0.0
        rmse = (sum(e ** 2 for e in abs_errors) / len(abs_errors)) ** 0.5 if abs_errors else 0.0
        
        # By bucket
        up_rows = [r for r in rows if r.get("top_bucket") == "UP"]
        down_rows = [r for r in rows if r.get("top_bucket") == "DOWN"]
        
        up_hit_rate = sum(1 for r in up_rows if r.get("hit_direction", False)) / len(up_rows) if up_rows else 0.0
        down_hit_rate = sum(1 for r in down_rows if r.get("hit_direction", False)) / len(down_rows) if down_rows else 0.0
        
        up_mae = sum(r.get("abs_error", 0.0) for r in up_rows) / len(up_rows) if up_rows else 0.0
        down_mae = sum(r.get("abs_error", 0.0) for r in down_rows) / len(down_rows) if down_rows else 0.0
        
        # Rank IC
        pred_returns = [r.get("pred_target_return", 0.0) for r in rows]
        realized_returns = [r.get("realized_return", 0.0) for r in rows]
        rank_ic_overall = calculate_spearman_rank_ic(pred_returns, realized_returns)
        
        up_pred = [r.get("pred_target_return", 0.0) for r in up_rows]
        up_realized = [r.get("realized_return", 0.0) for r in up_rows]
        rank_ic_up = calculate_spearman_rank_ic(up_pred, up_realized) if up_rows else 0.0
        
        down_pred = [r.get("pred_target_return", 0.0) for r in down_rows]
        down_realized = [r.get("realized_return", 0.0) for r in down_rows]
        rank_ic_down = calculate_spearman_rank_ic(down_pred, down_realized) if down_rows else 0.0
        
        # Star calibration
        star_stats = defaultdict(lambda: {"count": 0, "hits": 0, "abs_errors": []})
        for row in rows:
            star = row.get("pred_star", 0)
            if star > 0:
                star_stats[star]["count"] += 1
                if row.get("hit_direction", False):
                    star_stats[star]["hits"] += 1
                star_stats[star]["abs_errors"].append(row.get("abs_error", 0.0))
        
        star_calibration = []
        for star in sorted(star_stats.keys()):
            stats = star_stats[star]
            star_calibration.append({
                "star": star,
                "count": stats["count"],
                "hit_rate": stats["hits"] / stats["count"] if stats["count"] > 0 else 0.0,
                "mae": sum(stats["abs_errors"]) / len(stats["abs_errors"]) if stats["abs_errors"] else 0.0,
            })
        
        star_reliability = calculate_star_reliability_index(star_calibration)
        
        # Context attribution
        context_buckets = defaultdict(lambda: {"count": 0, "hits": 0, "abs_errors": []})
        for row in rows:
            context = row.get("context", {})
            regime = context.get("regime_status", "UNKNOWN")
            cluster = context.get("cluster_status", "UNKNOWN")
            drift = context.get("drift_status", "UNKNOWN")
            bucket_key = f"{regime}|{cluster}|{drift}"
            
            context_buckets[bucket_key]["count"] += 1
            if row.get("hit_direction", False):
                context_buckets[bucket_key]["hits"] += 1
            context_buckets[bucket_key]["abs_errors"].append(row.get("abs_error", 0.0))
        
        # Top 10 context buckets
        sorted_buckets = sorted(context_buckets.items(), key=lambda x: x[1]["count"], reverse=True)
        context_attribution = []
        for bucket_key, stats in sorted_buckets[:10]:
            parts = bucket_key.split("|")
            context_attribution.append({
                "regime": parts[0],
                "cluster": parts[1],
                "drift": parts[2],
                "count": stats["count"],
                "hit_rate": stats["hits"] / stats["count"] if stats["count"] > 0 else 0.0,
                "mae": sum(stats["abs_errors"]) / len(stats["abs_errors"]) if stats["abs_errors"] else 0.0,
            })
        
        forecast_quality_by_horizon[horizon] = {
            "hit_rate": round(hit_rate, 3),
            "hit_rate_by_bucket": {
                "UP": round(up_hit_rate, 3),
                "DOWN": round(down_hit_rate, 3),
            },
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "mae_by_bucket": {
                "UP": round(up_mae, 3),
                "DOWN": round(down_mae, 3),
            },
            "rank_ic_overall": round(rank_ic_overall, 3),
            "rank_ic_up_bucket": round(rank_ic_up, 3),
            "rank_ic_down_bucket": round(rank_ic_down, 3),
            "star_calibration": star_calibration,
            "star_reliability_index": star_reliability,
            "context_attribution": context_attribution,
        }
    
    # Build summary
    summary = {
        "schema_version": "or-os.v1",
        "as_of_date": as_of_date,
        "universe": universe,
        "rows": sum(len(rows) for rows in all_rows_by_horizon.values()) // len(all_rows_by_horizon) if all_rows_by_horizon else 0,
        "horizons": list(all_rows_by_horizon.keys()),
        "data_quality": {
            "baseline_source_counts": dict(baseline_source_counts),
            "truth_source_counts_by_horizon": truth_source_counts_by_horizon,
            "missing_truth_symbols_by_horizon": missing_truth_symbols_by_horizon,
        },
        "forecast_quality_by_horizon": forecast_quality_by_horizon,
    }
    
    return summary
