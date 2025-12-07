#!/usr/bin/env python
"""
Backfill 100 Indicators

100 指標建構背填腳本：為每個 symbol × date 建立 100 指標快照。

Usage:
    PYTHONPATH=. python scripts/run_backfill_indicators_100.py
    PYTHONPATH=. python scripts/run_backfill_indicators_100.py --start-date 2024-01-01 --end-date 2024-12-31
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from jgod.prediction.data.indicator_builder_100 import StockIndicatorBuilder100
from jgod.storage.db import get_session, init_db
from jgod.storage.models import IndicatorSnapshot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Backfill 100 indicators")
    parser.add_argument(
        "--universe-file",
        type=str,
        default="config/universe/tw_top50_2024.yaml",
        help="Universe YAML file path",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2024-01-01",
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2024-12-31",
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated stock symbols to backfill (e.g. 2330,2454,2317). Overrides universe file.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild indicators even if snapshots already exist.",
    )
    return parser.parse_args()


def load_universe(universe_file: str) -> list[dict]:
    """Load universe from YAML file"""
    file_path = Path(universe_file)
    if not file_path.exists():
        raise FileNotFoundError(f"Universe file not found: {universe_file}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    return data.get("universe", [])


def get_category_from_code(code: str) -> str:
    """Get category from indicator code"""
    if code.startswith("P"):
        return "Price"
    elif code.startswith("C"):
        return "Capital"
    elif code.startswith("F"):
        return "Fundamental"
    elif code.startswith("K"):
        return "Catalyst"
    elif code.startswith("S"):
        return "Sentiment"
    elif code.startswith("Q"):
        return "Quant"
    elif code.startswith("X"):
        return "X"
    elif code.startswith("M"):
        return "M"
    else:
        return "Unknown"


def determine_status(value: any) -> str:
    """Determine indicator status"""
    if value is None or value == 0.0:
        return "missing"
    # Placeholder indicators (K/S/X/M series are mostly placeholder in v1)
    # This is a simplified check, can be enhanced later
    return "ok"


def backfill_indicators(
    session,
    builder: StockIndicatorBuilder100,
    symbol: str,
    as_of_date: date,
    force: bool = False,
) -> int:
    """
    Build and save 100 indicators for a symbol on a specific date.
    
    Args:
        session: Database session
        builder: StockIndicatorBuilder100 instance
        symbol: Stock symbol
        as_of_date: Date for indicators
        force: If True, rebuild even if snapshots already exist
    
    Returns:
        int: Number of indicators saved
    """
    # 1) 若已存在完整資料且沒有 force，就直接跳過
    if not force:
        existing_count = (
            session.query(IndicatorSnapshot)
            .filter(
                IndicatorSnapshot.symbol == symbol,
                IndicatorSnapshot.date == as_of_date,
            )
            .count()
        )
        # 假設一個完整快照會有 100 個指標，90 以上就當作夠用了
        if existing_count >= 90:
            logger.info(
                "  %s %s: existing %s indicator snapshots, skip (use --force to rebuild)",
                symbol,
                as_of_date,
                existing_count,
            )
            return 0

    try:
        # Build indicators
        indicators = builder.build_indicators(symbol, as_of_date)
        
        saved = 0
        
        # Get filter to access weights
        from jgod.prediction.rules.stock_upside_filter_60_v1 import StockUpsideFilter60V1
        filter_instance = StockUpsideFilter60V1()
        
        for code, raw_value in indicators.items():
            # Get weight from filter
            weight = filter_instance.weights.get(code, 1.0)
            
            # Normalize value (simplified: use builder's normalize logic if needed)
            # For now, we'll store raw_value and let the filter handle normalization
            normalized_value = None
            if isinstance(raw_value, (int, float)):
                if raw_value == 0:
                    normalized_value = 0.0
                else:
                    # Use similar normalization as filter
                    norm = raw_value / 100.0
                    normalized_value = max(-1.0, min(1.0, norm))
            elif isinstance(raw_value, bool):
                normalized_value = 1.0 if raw_value else -1.0
            else:
                normalized_value = 0.0
            
            category = get_category_from_code(code)
            status = determine_status(raw_value)
            
            # Check if exists
            existing = (
                session.query(IndicatorSnapshot)
                .filter(
                    IndicatorSnapshot.symbol == symbol,
                    IndicatorSnapshot.date == as_of_date,
                    IndicatorSnapshot.indicator_code == code,
                )
                .first()
            )
            
            if existing:
                # Update existing
                existing.raw_value = float(raw_value) if isinstance(raw_value, (int, float)) else None
                existing.normalized_value = normalized_value
                existing.weight = float(weight)
                existing.category = category
                existing.status = status
                existing.updated_at = datetime.now()
            else:
                # Insert new
                new_snapshot = IndicatorSnapshot(
                    symbol=symbol,
                    date=as_of_date,
                    indicator_code=code,
                    raw_value=float(raw_value) if isinstance(raw_value, (int, float)) else None,
                    normalized_value=normalized_value,
                    weight=float(weight),
                    category=category,
                    data_source="FinMind",  # Simplified
                    status=status,
                )
                session.add(new_snapshot)
            
            saved += 1
        
        session.commit()
        return saved
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error building indicators for {symbol} on {as_of_date}: {e}", exc_info=True)
        return 0


def generate_date_range(start_date: date, end_date: date) -> list[date]:
    """Generate list of trading dates (excluding weekends for now)"""
    dates = []
    current = start_date
    while current <= end_date:
        # Skip weekends (simplified, can enhance with holiday calendar)
        if current.weekday() < 5:  # Monday = 0, Friday = 4
            dates.append(current)
        current += timedelta(days=1)
    return dates


def main():
    """Main function"""
    args = parse_args()
    
    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Load universe
    logger.info(f"Loading universe from {args.universe_file}...")
    universe = load_universe(args.universe_file)
    logger.info(f"Loaded {len(universe)} stocks from universe")
    
    # Handle --symbols override
    if args.symbols:
        user_symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
        universe_symbols = [s["symbol"] for s in universe]
        final_symbols = [s for s in user_symbols if s in universe_symbols]
        
        if not final_symbols:
            raise ValueError(
                f"None of the provided symbols ({user_symbols}) were found in universe. "
                f"Available symbols: {universe_symbols[:10]}{'...' if len(universe_symbols) > 10 else ''}"
            )
        
        logger.info(f"Overriding universe symbols: {final_symbols}")
        universe = [s for s in universe if s["symbol"] in final_symbols]
        logger.info(f"Filtered to {len(universe)} stocks")
    
    # Initialize indicator builder
    token = os.getenv("FINMIND_API_TOKEN")
    if not token:
        logger.error("FINMIND_API_TOKEN is not set in environment")
        sys.exit(1)
    
    builder = StockIndicatorBuilder100(finmind_token=token)
    
    # Generate date range
    dates = generate_date_range(start_date, end_date)
    logger.info(f"Processing {len(dates)} dates from {start_date} to {end_date}")
    
    # Process each symbol × date
    session_gen = get_session()
    session = next(session_gen)
    try:
        total_indicators = 0
        total_combinations = len(universe) * len(dates)
        current = 0
        
        for stock_data in universe:
            symbol = stock_data["symbol"]
            for as_of_date in dates:
                current += 1
                if current % 10 == 0:
                    logger.info(f"Progress: {current}/{total_combinations} ({current*100//total_combinations}%)")
                
                saved = backfill_indicators(session, builder, symbol, as_of_date, force=args.force)
                total_indicators += saved
        
        logger.info(f"✅ Backfill completed: {total_indicators} indicator snapshots saved")
        
    finally:
        session.close()


if __name__ == "__main__":
    main()

