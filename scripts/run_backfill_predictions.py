#!/usr/bin/env python
"""
Prediction Backfill CLI for J-GOD

選股結果快照背填腳本：基於 indicator_snapshots 產生 prediction_snapshots。

Usage:
    PYTHONPATH=. python scripts/run_backfill_predictions.py
    PYTHONPATH=. python scripts/run_backfill_predictions.py --start-date 2024-01-01 --end-date 2024-12-31
    PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols 2330,2454 --force
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jgod.prediction.rules.stock_upside_filter_60_v1 import (
    IndicatorScore,
    StockUpsideFilter60V1,
    StockUpsideResult,
)
from jgod.storage.db import get_session, init_db
from jgod.storage.models import DailyBar, IndicatorSnapshot, PredictionSnapshot, Stock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Backfill prediction snapshots from indicator snapshots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default dates and all active stocks
  PYTHONPATH=. python scripts/run_backfill_predictions.py

  # Specify date range
  PYTHONPATH=. python scripts/run_backfill_predictions.py --start-date 2024-01-01 --end-date 2024-12-31

  # Specify specific symbols
  PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols 2330,2454,2317

  # Force rebuild existing predictions
  PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols 2330 --force
        """,
    )
    
    parser.add_argument(
        "--start-date",
        type=str,
        default="2024-01-01",
        help="Start date (YYYY-MM-DD), default: 2024-01-01",
    )
    
    parser.add_argument(
        "--end-date",
        type=str,
        default="2024-12-31",
        help="End date (YYYY-MM-DD), default: 2024-12-31",
    )
    
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated stock symbols (e.g. 2330,2454,2317). If not provided, uses all active stocks from database.",
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild predictions even if snapshots already exist",
    )
    
    parser.add_argument(
        "--min-indicators",
        type=int,
        default=90,
        help="Minimum number of indicators required (default: 90)",
    )
    
    return parser.parse_args()


def load_symbols_from_db(session: Session) -> List[str]:
    """Load all symbols from stocks table"""
    stocks = session.query(Stock).filter(Stock.is_active == True).all()
    return [stock.symbol for stock in stocks]


def check_data_availability(
    session: Session,
    symbol: str,
    as_of_date: date,
    min_indicators: int = 90,
) -> tuple[bool, str]:
    """
    Check if daily_bar and indicator_snapshots are available.
    
    Returns:
        (is_available, reason)
    """
    # Check daily_bar
    daily_bar = (
        session.query(DailyBar)
        .filter(DailyBar.symbol == symbol, DailyBar.date == as_of_date)
        .first()
    )
    
    if not daily_bar:
        return False, f"No daily_bar for {symbol} on {as_of_date}"
    
    # Check indicator_snapshots (at least min_indicators)
    indicator_count = (
        session.query(IndicatorSnapshot)
        .filter(
            IndicatorSnapshot.symbol == symbol,
            IndicatorSnapshot.date == as_of_date,
        )
        .count()
    )
    
    if indicator_count < min_indicators:
        return False, f"Only {indicator_count} indicators (need at least {min_indicators})"
    
    return True, "OK"


def load_indicators_from_db(
    session: Session,
    symbol: str,
    as_of_date: date,
) -> Dict[str, Any]:
    """
    Load indicators from database and convert to dict format.
    
    Returns:
        Dict[str, Any]: Indicators dict for StockUpsideFilter60V1.evaluate()
    """
    snapshots = (
        session.query(IndicatorSnapshot)
        .filter(
            IndicatorSnapshot.symbol == symbol,
            IndicatorSnapshot.date == as_of_date,
        )
        .all()
    )
    
    indicators: Dict[str, Any] = {}
    for snap in snapshots:
        # Use raw_value if available, otherwise use normalized_value * 100 as proxy
        if snap.raw_value is not None:
            indicators[snap.indicator_code] = snap.raw_value
        elif snap.normalized_value is not None:
            # Reverse normalization for filter (approximate)
            indicators[snap.indicator_code] = snap.normalized_value * 100.0
        else:
            indicators[snap.indicator_code] = 0.0
    
    return indicators


def extract_risk_flags(result: StockUpsideResult) -> List[Dict[str, Any]]:
    """
    Extract risk flags from prediction result.
    
    Currently identifies:
    - Negative total score
    - SHORT verdict
    - AVOID verdict
    """
    flags = []
    
    if result.total_score < 0:
        flags.append({
            "type": "negative_score",
            "severity": "medium",
            "message": f"Total score is negative: {result.total_score:.2f}",
        })
    
    if result.verdict == "SHORT":
        flags.append({
            "type": "short_signal",
            "severity": "high",
            "message": "Strong sell signal detected",
        })
    
    if result.verdict == "AVOID":
        flags.append({
            "type": "avoid_signal",
            "severity": "medium",
            "message": "Avoid signal detected",
        })
    
    return flags


def extract_top_indicators(
    result: StockUpsideResult,
    top_n: int,
    positive: bool = True,
) -> List[Dict[str, Any]]:
    """Extract top N positive or negative indicators"""
    scored: List[tuple[IndicatorScore, float]] = []
    for ind in result.indicator_scores:
        weighted = ind.score * ind.weight
        scored.append((ind, weighted))
    
    if positive:
        scored = [x for x in scored if x[1] > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
    else:
        scored = [x for x in scored if x[1] < 0]
        scored.sort(key=lambda x: x[1])
    
    return [
        {
            "code": ind.code,
            "name": ind.name,
            "score": ind.score,
            "weight": ind.weight,
            "weighted_score": float(weighted),
        }
        for ind, weighted in scored[:top_n]
    ]


def serialize_result(result: StockUpsideResult) -> Dict[str, Any]:
    """Serialize StockUpsideResult to JSON-serializable dict"""
    return {
        "symbol": result.symbol,
        "total_score": result.total_score,
        "verdict": result.verdict,
        "summary": result.summary,
        "indicator_scores": [
            {
                "code": ind.code,
                "name": ind.name,
                "score": ind.score,
                "weight": ind.weight,
                "reason": ind.reason,
            }
            for ind in result.indicator_scores
        ],
    }


def backfill_prediction(
    session: Session,
    filter_instance: StockUpsideFilter60V1,
    symbol: str,
    as_of_date: date,
    force: bool = False,
    top_n: int = 10,
) -> bool:
    """
    Build and save prediction snapshot for a symbol on a specific date.
    
    Returns:
        bool: True if successful
    """
    # Check if prediction already exists
    if not force:
        existing = (
            session.query(PredictionSnapshot)
            .filter(
                PredictionSnapshot.symbol == symbol,
                PredictionSnapshot.date == as_of_date,
            )
            .first()
        )
        
        if existing:
            logger.debug(f"  {symbol} {as_of_date}: prediction exists, skip (use --force to rebuild)")
            return False
    
    try:
        # Load indicators from DB
        indicators = load_indicators_from_db(session, symbol, as_of_date)
        
        if not indicators:
            logger.warning(f"  {symbol} {as_of_date}: No indicators found")
            return False
        
        # Evaluate using filter
        result = filter_instance.evaluate(symbol, indicators)
        
        # Extract top indicators
        positive_indicators = extract_top_indicators(result, top_n, positive=True)
        negative_indicators = extract_top_indicators(result, top_n, positive=False)
        
        # Extract risk flags
        risk_flags = extract_risk_flags(result)
        
        # Serialize meta data
        meta_json = serialize_result(result)
        
        # Check if exists
        existing = (
            session.query(PredictionSnapshot)
            .filter(
                PredictionSnapshot.symbol == symbol,
                PredictionSnapshot.date == as_of_date,
            )
            .first()
        )
        
        now = datetime.now()
        
        if existing:
            # Update existing
            existing.score = result.total_score
            existing.total_score = result.total_score
            existing.signal = result.verdict
            existing.verdict = result.verdict
            existing.positive_factors_json = positive_indicators
            existing.negative_factors_json = negative_indicators
            existing.risk_flags_json = risk_flags
            existing.meta_json = meta_json
            # Backward compatibility
            existing.positive_indicators = positive_indicators
            existing.negative_indicators = negative_indicators
            existing.raw_payload = meta_json
            existing.updated_at = now
        else:
            # Insert new
            new_snapshot = PredictionSnapshot(
                symbol=symbol,
                date=as_of_date,
                score=result.total_score,
                total_score=result.total_score,
                signal=result.verdict,
                verdict=result.verdict,
                positive_factors_json=positive_indicators,
                negative_factors_json=negative_indicators,
                risk_flags_json=risk_flags,
                meta_json=meta_json,
                # Backward compatibility
                positive_indicators=positive_indicators,
                negative_indicators=negative_indicators,
                raw_payload=meta_json,
            )
            session.add(new_snapshot)
        
        session.commit()
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"  {symbol} {as_of_date}: Error building prediction: {e}", exc_info=True)
        return False


def generate_date_range(start_date: date, end_date: date) -> List[date]:
    """Generate list of trading dates (excluding weekends)"""
    dates = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Skip weekends (Monday=0, Friday=4)
            dates.append(current)
        current += timedelta(days=1)
    return dates


def main():
    """Main function"""
    args = parse_args()
    
    # Parse dates
    try:
        start_date_obj = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        logger.error("Date format must be YYYY-MM-DD (e.g. 2024-01-01)")
        sys.exit(1)
    
    if start_date_obj > end_date_obj:
        logger.error(f"Start date ({args.start_date}) must be before end date ({args.end_date})")
        sys.exit(1)
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Get symbol list
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        if args.symbols:
            # Parse user-provided symbols
            symbol_list = [s.strip() for s in args.symbols.split(",") if s.strip()]
            logger.info(f"Using provided symbols: {symbol_list}")
        else:
            # Load from database
            symbol_list = load_symbols_from_db(session)
            logger.info(f"Loaded {len(symbol_list)} active stocks from database")
            
            if not symbol_list:
                logger.warning("No active stocks found in database. Please ensure stocks table is populated.")
                return
        
        # Initialize filter
        filter_instance = StockUpsideFilter60V1()
        
        # Generate date range
        dates = generate_date_range(start_date_obj, end_date_obj)
        logger.info(f"Processing {len(dates)} dates from {start_date_obj} to {end_date_obj}")
        
        # Process each symbol × date
        total_predictions = 0
        total_skipped_data = 0
        total_skipped_exists = 0
        total_errors = 0
        total_combinations = len(symbol_list) * len(dates)
        current = 0
        
        logger.info(f"Starting backfill for {len(symbol_list)} symbols × {len(dates)} dates = {total_combinations} combinations")
        
        for symbol in symbol_list:
            for as_of_date in dates:
                current += 1
                
                if current % 50 == 0:
                    logger.info(
                        f"Progress: {current}/{total_combinations} "
                        f"({current*100//total_combinations}%) - "
                        f"Saved: {total_predictions}, Skipped (data): {total_skipped_data}, "
                        f"Skipped (exists): {total_skipped_exists}, Errors: {total_errors}"
                    )
                
                # Check data availability
                is_available, reason = check_data_availability(
                    session, symbol, as_of_date, min_indicators=args.min_indicators
                )
                
                if not is_available:
                    logger.debug(f"  {symbol} {as_of_date}: {reason}")
                    total_skipped_data += 1
                    continue
                
                # Build and save prediction
                success = backfill_prediction(
                    session,
                    filter_instance,
                    symbol,
                    as_of_date,
                    force=args.force,
                )
                
                if success:
                    total_predictions += 1
                else:
                    # Check if it was skipped due to existing prediction
                    existing = (
                        session.query(PredictionSnapshot)
                        .filter(
                            PredictionSnapshot.symbol == symbol,
                            PredictionSnapshot.date == as_of_date,
                        )
                        .first()
                    )
                    if existing and not args.force:
                        total_skipped_exists += 1
                    else:
                        total_errors += 1
        
        logger.info("=" * 70)
        logger.info("✅ Backfill completed!")
        logger.info(f"  Total combinations processed: {total_combinations}")
        logger.info(f"  ✅ Predictions saved: {total_predictions}")
        logger.info(f"  ⏭️  Skipped (insufficient data): {total_skipped_data}")
        logger.info(f"  ⏭️  Skipped (already exists): {total_skipped_exists}")
        logger.info(f"  ❌ Errors: {total_errors}")
        logger.info("=" * 70)
        
    finally:
        session.close()


if __name__ == "__main__":
    main()
