"""
Oracle Scorecard Grader (truth vs prediction).
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from jgod.oracle.schemas import Prophecy, ScorecardRow, TruthData, ForecastHorizon
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


def grade_prophecy(prophecy: Prophecy, horizon: str, governance_snapshot: Optional[Dict] = None) -> ScorecardRow:
    """
    Grade a single prophecy for a horizon.
    
    Args:
        prophecy: Prophecy object
        horizon: "T1", "T5", etc.
        governance_snapshot: Optional governance context dict
        
    Returns:
        ScorecardRow
    """
    if horizon not in prophecy.forecast_matrix:
        raise ValueError(f"Horizon {horizon} not found in prophecy forecast_matrix")
    
    forecast = prophecy.forecast_matrix[horizon]
    symbol = prophecy.t0.get("symbol")
    as_of_date = prophecy.as_of_date
    
    # Get baseline price (T0)
    t0_price, t0_source = get_baseline_price(symbol, as_of_date)
    
    # Calculate T+N date
    tN_date = calculate_horizon_date(as_of_date, horizon)
    
    # Get truth price (T+N)
    tN_price, tN_source = get_truth_price(symbol, tN_date)
    
    # Calculate realized return
    realized_return = ((tN_price - t0_price) / t0_price) * 100.0
    
    # Truth data
    truth = TruthData(
        tN_date=tN_date,
        tN_price=tN_price,
        realized_return=realized_return
    )
    
    # Metrics
    hit_direction = (
        (forecast.direction == "UP" and realized_return > 0) or
        (forecast.direction == "DOWN" and realized_return < 0) or
        (forecast.direction == "SIDE" and abs(realized_return) < 1.0)  # Within 1% = SIDE
    )
    
    abs_error = abs(forecast.target_return - realized_return)
    signed_error = forecast.target_return - realized_return
    
    metrics = {
        "hit_direction": hit_direction,
        "abs_error": round(abs_error, 3),
        "signed_error": round(signed_error, 3),
    }
    
    # Context (from governance snapshot or UNKNOWN)
    context = governance_snapshot or {
        "regime": "UNKNOWN",
        "drift_status": "UNKNOWN",
        "cluster_risk": "UNKNOWN",
        "execution_confidence": "UNKNOWN",
    }
    
    # Attribution stub
    attribution_stub = {
        "primary_driver": "UNKNOWN",  # MVP: stub
        "notes": f"T0 source: {t0_source}, T{horizon} source: {tN_source}",
    }
    
    # Generate score_id
    score_id = hashlib.sha256(f"{prophecy.prophecy_id}_{horizon}".encode()).hexdigest()[:32]
    
    return ScorecardRow(
        schema_version="or-os.v1",
        score_id=score_id,
        prophecy_id=prophecy.prophecy_id,
        as_of_date=as_of_date,
        symbol=symbol,
        horizon=horizon,
        pred={
            "direction": forecast.direction,
            "target_return": forecast.target_return,
            "star": forecast.star,
        },
        truth=truth,
        metrics=metrics,
        context=context,
        attribution_stub=attribution_stub,
    )


def grade_archive(archive_path: Path, horizon: str, output_path: Path, 
                  governance_snapshot: Optional[Dict] = None) -> List[ScorecardRow]:
    """
    Grade all prophecies in archive for a horizon.
    
    Args:
        archive_path: Path to prophecy archive JSONL
        horizon: "T1", "T5", etc.
        output_path: Output path for scorecard JSONL
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
            
            row = grade_prophecy(prophecy, horizon, governance_snapshot)
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
