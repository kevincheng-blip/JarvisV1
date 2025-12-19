"""
Oracle Scorecard Grader (truth vs prediction) - Multi-horizon support.
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from jgod.oracle.schemas import Prophecy, ScorecardRow, ForecastHorizon
from jgod.oracle.data_sources import get_baseline_price, get_truth_price
from jgod.oracle.archive_writer import load_prophecy_archive
import hashlib
import logging

logger = logging.getLogger(__name__)


def calculate_horizon_date(as_of_date: str, horizon: str) -> str:
    """
    Calculate target date for horizon.
    
    Args:
        as_of_date: YYYY-MM-DD (T0)
        horizon: "T1", "T5", "T10", "T20", "TM"
        
    Returns:
        YYYY-MM-DD (T+N date)
    """
    t0 = datetime.strptime(as_of_date, "%Y-%m-%d")
    
    if horizon == "T1":
        tN = t0 + timedelta(days=1)
    elif horizon == "T5":
        tN = t0 + timedelta(days=5)
    elif horizon == "T10":
        tN = t0 + timedelta(days=10)
    elif horizon == "T20":
        tN = t0 + timedelta(days=20)
    elif horizon == "TM":
        # Approximate month (30 days)
        tN = t0 + timedelta(days=30)
    else:
        raise ValueError(f"Unknown horizon: {horizon}")
    
    return tN.strftime("%Y-%m-%d")


def grade_prophecy(
    prophecy: Prophecy, 
    horizon: str, 
    db_path: Optional[str] = None,
    governance_snapshot: Optional[Dict] = None
) -> ScorecardRow:
    """
    Grade a single prophecy for a horizon.
    
    Args:
        prophecy: Prophecy object
        horizon: "T1", "T5", etc.
        db_path: Optional SQLite database path
        governance_snapshot: Optional governance context dict
        
    Returns:
        ScorecardRow
    """
    if horizon not in prophecy.forecast_matrix:
        raise ValueError(f"Horizon {horizon} not found in prophecy forecast_matrix")
    
    forecast = prophecy.forecast_matrix[horizon]
    symbol = prophecy.symbol  # Use normalized symbol
    as_of_date = prophecy.as_of_date
    
    # Get baseline price (T0) - returns (price, source, explain)
    t0_price, t0_source, t0_explain = get_baseline_price(symbol, as_of_date, db_path)
    
    # Calculate T+N date
    tN_date = calculate_horizon_date(as_of_date, horizon)
    
    # Get truth price (T+N) - returns (price, source, explain)
    tN_price, tN_source, tN_explain = get_truth_price(symbol, tN_date, db_path)
    
    # Initialize explain dict first (before any conditional logic)
    explain = {
        "baseline_date_used": t0_explain.get("date_used", as_of_date),
        "baseline_exact_match": t0_explain.get("exact_match", True),
        "truth_date_used": tN_explain.get("date_used", tN_date),
        "truth_exact_match": tN_explain.get("exact_match", True),
    }
    if "lookback_days" in t0_explain:
        explain["baseline_lookback_days"] = t0_explain["lookback_days"]
    if "lookback_days" in tN_explain:
        explain["truth_lookback_days"] = tN_explain["lookback_days"]
    
    # Calculate realized return (percentage) - ensure both prices are valid
    # Note: t0_price and tN_price are already floats (not None) from get_baseline_price/get_truth_price
    # They return stub price if SQLite fails, so we check for valid positive values
    if t0_price is None or t0_price <= 0 or tN_price is None or tN_price <= 0:
        # Invalid prices - set realized_return to None and flag in explain
        realized_return = None
    else:
        # Realized return in percentage: ((p_target / p0) - 1) * 100
        realized_return = ((tN_price / t0_price) - 1.0) * 100.0
        realized_return = round(realized_return, 4)  # Round to 4 decimal places
    
    # Metrics (only if realized_return is valid)
    pred_target = forecast.target_return  # Initialize pred_target for ScorecardRow
    
    if realized_return is None:
        hit_direction = False
        abs_error = None
        signed_error = None
    else:
        hit_direction = (
            (forecast.direction == "UP" and realized_return > 0) or
            (forecast.direction == "DOWN" and realized_return < 0) or
            (forecast.direction == "SIDE" and abs(realized_return) < 1.0)  # Within 1% = SIDE
        )
        
        # pred_target_return should already be in percentage from forecast
        # Scale check: If pred_target looks like decimal (abs <= 1.5 and star >= 3), convert to percentage
        # This is for backward compat only - new prophecies should already be in percentage
        if abs(pred_target) <= 1.5 and forecast.star >= 3:
            pred_target = pred_target * 100.0
            explain["scale_fix_applied"] = True
        
        abs_error = abs(pred_target - realized_return)
        signed_error = pred_target - realized_return
        abs_error = round(abs_error, 4)
        signed_error = round(signed_error, 4)
    
    # Context (from governance snapshot or UNKNOWN)
    context = governance_snapshot or {
        "regime_status": "UNKNOWN",
        "cluster_status": "UNKNOWN",
        "drift_status": "UNKNOWN",
        "execution_confidence": "UNKNOWN",
    }
    
    # Attribution stub
    attribution_stub = {
        "primary_driver": "UNKNOWN",  # MVP: stub
        "notes": f"T0 source: {t0_source}, T{horizon} source: {tN_source}",
    }
    
    # Generate score_id (64 hex)
    score_id = hashlib.sha256(f"{prophecy.prophecy_id}_{horizon}".encode()).hexdigest()
    
    return ScorecardRow(
        schema_version="or-os.v1",
        score_id=score_id,
        prophecy_id=prophecy.prophecy_id,
        as_of_date=as_of_date,
        symbol=symbol,
        top_bucket=prophecy.top_bucket,
        rank_in_bucket=prophecy.rank_in_bucket,
        horizon=horizon,
        baseline_price=t0_price if t0_price is not None else 0.0,
        baseline_source=t0_source,
        truth_price=tN_price if tN_price is not None else 0.0,
        truth_source=tN_source,
        pred_direction=forecast.direction,
        pred_target_return=pred_target,  # Use potentially scaled pred_target
        pred_star=forecast.star,
        pred_confidence=forecast.confidence,
        realized_return=realized_return,
        hit_direction=hit_direction,
        abs_error=abs_error,
        signed_error=signed_error,
        context=context,
        explain=explain,
        attribution_stub=attribution_stub,
    )


def grade_archive(
    archive_path: Path, 
    horizon: str, 
    output_path: Path,
    db_path: Optional[str] = None,
    governance_snapshot: Optional[Dict] = None
) -> List[ScorecardRow]:
    """
    Grade all prophecies in archive for a horizon.
    
    Args:
        archive_path: Path to prophecy archive JSONL
        horizon: "T1", "T5", etc.
        output_path: Output path for scorecard JSONL
        db_path: Optional SQLite database path
        governance_snapshot: Optional governance context
        
    Returns:
        List of ScorecardRow
    """
    prophecies = load_prophecy_archive(archive_path)
    scorecard_rows = []
    
    for prophecy in prophecies:
        try:
            if horizon not in prophecy.forecast_matrix:
                logger.warning(f"Prophecy {prophecy.prophecy_id} missing horizon {horizon}, skipping")
                continue
            
            row = grade_prophecy(prophecy, horizon, db_path, governance_snapshot)
            if row:  # Only append if row is valid
                scorecard_rows.append(row)
        except Exception as e:
            logger.error(f"Error grading prophecy {prophecy.prophecy_id}: {e}", exc_info=True)
            continue
    
    # Write scorecard
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for row in scorecard_rows:
            f.write(row.model_dump_json() + '\n')
    
    return scorecard_rows


def grade_archive_multi_horizon(
    archive_path: Path,
    horizons: List[str],
    output_dir: Path,
    db_path: Optional[str] = None,
    governance_snapshot: Optional[Dict] = None
) -> Dict[str, List[ScorecardRow]]:
    """
    Grade archive for multiple horizons.
    
    Args:
        archive_path: Path to prophecy archive JSONL
        horizons: List of horizons (e.g., ["T1", "T5", "T10"])
        output_dir: Output directory
        db_path: Optional SQLite database path
        governance_snapshot: Optional governance context
        
    Returns:
        Dict mapping horizon -> List[ScorecardRow]
    """
    results = {}
    as_of_date = archive_path.stem.split("_")[-1] if "_" in archive_path.stem else "unknown"
    
    for horizon in horizons:
        output_path = output_dir / f"scorecard_{as_of_date}_{horizon}.jsonl"
        rows = grade_archive(archive_path, horizon, output_path, db_path, governance_snapshot)
        results[horizon] = rows
        logger.info(f"Graded {len(rows)} prophecies for horizon {horizon}")
    
    return results
