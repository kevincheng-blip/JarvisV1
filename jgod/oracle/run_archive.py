"""
CLI: Run Prophecy Archive generation.
"""
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from jgod.oracle.schemas import Prophecy, ForecastHorizon, DecisionFootprint
from jgod.oracle.universe import load_universe
from jgod.oracle.data_sources import get_baseline_price
from jgod.oracle.resonance import calculate_conflict_score, calculate_resonance_tag
from jgod.oracle.archive_writer import generate_prophecy_id, write_prophecy_archive, compute_immutable_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_forecast_matrix(symbol: str, raw_score: float) -> Dict[str, ForecastHorizon]:
    """
    Generate forecast matrix from raw score (MVP stub logic).
    
    Args:
        symbol: Stock symbol
        raw_score: Raw score from B toolset
        
    Returns:
        Dict of horizon -> ForecastHorizon
    """
    # MVP: Simple mapping from score to forecasts
    direction = "UP" if raw_score > 0 else "DOWN" if raw_score < 0 else "SIDE"
    abs_score = abs(raw_score)
    
    # Map score magnitude to target returns and stars
    if abs_score > 0.8:
        target_t1 = 3.0
        target_t5 = 5.0
        target_t10 = 8.0
        target_t20 = 12.0
        target_tm = 15.0
        star = 5
        confidence = "HIGH"
    elif abs_score > 0.5:
        target_t1 = 2.0
        target_t5 = 3.5
        target_t10 = 5.0
        target_t20 = 7.0
        target_tm = 9.0
        star = 4
        confidence = "MED"
    elif abs_score > 0.2:
        target_t1 = 1.0
        target_t5 = 2.0
        target_t10 = 3.0
        target_t20 = 4.0
        target_tm = 5.0
        star = 3
        confidence = "MED"
    else:
        target_t1 = 0.5
        target_t5 = 1.0
        target_t10 = 1.5
        target_t20 = 2.0
        target_tm = 2.5
        star = 2
        confidence = "LOW"
    
    if direction == "DOWN":
        target_t1 = -target_t1
        target_t5 = -target_t5
        target_t10 = -target_t10
        target_t20 = -target_t20
        target_tm = -target_tm
    
    return {
        "T1": ForecastHorizon(direction=direction, target_return=target_t1, star=star, confidence=confidence),
        "T5": ForecastHorizon(direction=direction, target_return=target_t5, star=star, confidence=confidence),
        "T10": ForecastHorizon(direction=direction, target_return=target_t10, star=star, confidence=confidence),
        "T20": ForecastHorizon(direction=direction, target_return=target_t20, star=star, confidence=confidence),
        "TM": ForecastHorizon(direction=direction, target_return=target_tm, star=star, confidence=confidence),
    }


def get_raw_score(symbol: str, date: str) -> float:
    """
    Get raw score for symbol (MVP: stub generator).
    
    Args:
        symbol: Stock symbol
        date: YYYY-MM-DD
        
    Returns:
        Raw score (-1.0 to 1.0)
    """
    # MVP: Deterministic stub based on symbol+date hash
    hash_val = hash(f"{symbol}_{date}") % 200
    # Map to -1.0 to 1.0 range
    score = (hash_val - 100) / 100.0
    return round(score, 3)


def run_archive(date: str, universe: str, output_dir: Path) -> None:
    """
    Generate prophecy archive for a date.
    
    Args:
        date: YYYY-MM-DD
        universe: Universe name (e.g., "top50")
        output_dir: Output directory
    """
    logger.info(f"Generating prophecy archive for {date}, universe={universe}")
    
    # Load universe
    symbols = load_universe(universe)
    logger.info(f"Loaded {len(symbols)} symbols from universe {universe}")
    
    # Get raw scores for all symbols
    symbol_scores = []
    for symbol in symbols:
        raw_score = get_raw_score(symbol, date)
        symbol_scores.append((symbol, raw_score))
    
    # Sort by absolute score
    symbol_scores.sort(key=lambda x: abs(x[1]), reverse=True)
    
    # Split into UP and DOWN pools
    up_pool = [(s, sc) for s, sc in symbol_scores if sc > 0]
    down_pool = [(s, sc) for s, sc in symbol_scores if sc < 0]
    
    # Ensure we have at least 50 in each pool by splitting if needed
    if len(up_pool) < 50:
        # Take from down_pool and invert scores
        needed = 50 - len(up_pool)
        for symbol, score in down_pool[len(down_pool) - needed:]:
            up_pool.append((symbol, abs(score)))  # Use absolute value for UP
    
    if len(down_pool) < 50:
        # Take from up_pool and invert scores
        needed = 50 - len(down_pool)
        for symbol, score in up_pool[len(up_pool) - needed:]:
            down_pool.append((symbol, -abs(score)))  # Use negative absolute for DOWN
    
    # Take top 50 from each
    top50_up = sorted(up_pool, key=lambda x: abs(x[1]), reverse=True)[:50]
    top50_down = sorted(down_pool, key=lambda x: abs(x[1]), reverse=True)[:50]
    
    # Final check: if still insufficient, generate synthetic scores
    if len(top50_up) < 50:
        used_symbols = {s for s, _ in top50_up + top50_down}
        remaining = [s for s in symbols if s not in used_symbols]
        for i, symbol in enumerate(remaining[:50 - len(top50_up)]):
            top50_up.append((symbol, 0.1 + i * 0.01))
    
    if len(top50_down) < 50:
        used_symbols = {s for s, _ in top50_up + top50_down}
        remaining = [s for s in symbols if s not in used_symbols]
        for i, symbol in enumerate(remaining[:50 - len(top50_down)]):
            top50_down.append((symbol, -0.1 - i * 0.01))
    
    logger.info(f"Top50Up: {len(top50_up)} symbols, Top50Down: {len(top50_down)} symbols")
    
    # Generate prophecies
    prophecies: List[Prophecy] = []
    
    for rank, (symbol, raw_score) in enumerate(top50_up, start=1):
        prophecy = create_prophecy(symbol, date, "UP", rank, raw_score)
        prophecies.append(prophecy)
    
    for rank, (symbol, raw_score) in enumerate(top50_down, start=1):
        prophecy = create_prophecy(symbol, date, "DOWN", rank, raw_score)
        prophecies.append(prophecy)
    
    # Write archive
    output_path = output_dir / f"prophecies_{date}.jsonl"
    write_prophecy_archive(prophecies, output_path)
    
    logger.info(f"Wrote {len(prophecies)} prophecies to {output_path}")


def create_prophecy(symbol: str, date: str, bucket: str, rank: int, raw_score: float) -> Prophecy:
    """Create a Prophecy object."""
    # Get baseline price
    baseline_price, baseline_source = get_baseline_price(symbol, date)
    
    # Generate forecast matrix
    forecast_matrix = generate_forecast_matrix(symbol, raw_score)
    
    # Calculate resonance and conflict
    resonance_tag = calculate_resonance_tag(forecast_matrix)
    conflict_score = calculate_conflict_score(forecast_matrix)
    
    # Generate prophecy_id
    prophecy_id = generate_prophecy_id(date, symbol)
    
    # T0 data
    t0 = {
        "timestamp": f"{date}T14:00:00+08:00",
        "baseline_price": baseline_price,
        "baseline_source": baseline_source,
        "symbol": symbol,
        "universe": "TOP50",
    }
    
    # Decision footprint (MVP stub)
    decision_footprint = DecisionFootprint(
        B={"raw_score": raw_score, "signals_used": []},
        C={"tags": [], "blocked": False, "reasons": []},
        D={"event_tags": [], "impact_vector": {}},
        A={"mutual_answer_summary": f"Score-based prediction for {symbol}", "key_conflicts": []},
    )
    
    # Versions
    versions = {
        "oracle_core_version": "v1",
        "toolset_version": "v1",
        "doctrine_version": "v2",
        "governance_version": "v1",
    }
    
    # Create prophecy dict (without hash first)
    prophecy_dict = {
        "schema_version": "or-os.v1",
        "prophecy_id": prophecy_id,
        "as_of_date": date,
        "t0": t0,
        "top_bucket": bucket,
        "rank_in_bucket": rank,
        "resonance_tag": resonance_tag,
        "conflict_score": conflict_score,
        "forecast_matrix": {k: v.model_dump() for k, v in forecast_matrix.items()},
        "decision_footprint": decision_footprint.model_dump(),
        "versions": versions,
    }
    
    # Compute immutable hash
    immutable_hash = compute_immutable_hash(prophecy_dict)
    prophecy_dict["immutable_hash"] = immutable_hash
    
    return Prophecy(**prophecy_dict)


def main():
    parser = argparse.ArgumentParser(description="Generate Prophecy Archive")
    parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    parser.add_argument("--universe", default="top50", help="Universe name (default: top50)")
    parser.add_argument("--out", required=True, help="Output directory")
    
    args = parser.parse_args()
    
    output_dir = Path(args.out)
    run_archive(args.date, args.universe, output_dir)


if __name__ == "__main__":
    main()
