#!/usr/bin/env python
"""
Backfill Raw Data from FinMind

歷史資料背填腳本：抓取 FinMind 歷史資料並寫入 daily_bars 表。

Usage:
    PYTHONPATH=. python scripts/run_backfill_raw_data.py
    PYTHONPATH=. python scripts/run_backfill_raw_data.py --start-date 2024-01-01 --end-date 2024-12-31
    PYTHONPATH=. python scripts/run_backfill_raw_data.py --universe-file config/universe/tw_top50_2024.yaml
    PYTHONPATH=. python scripts/run_backfill_raw_data.py --symbols 2330,2454,2317 --start-date 2024-01-01 --end-date 2024-12-31
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date, datetime
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

import pandas as pd

from api_clients.finmind_client import FinMindClient, FinMindClientConfig
from jgod.storage.db import get_session, init_db
from jgod.storage.models import DailyBar, Stock

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Backfill raw data from FinMind")
    parser.add_argument(
        "--universe-file",
        type=str,
        default="config/universe/tw_top50_2024.yaml",
        help="Universe YAML file path",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated stock symbols, e.g. 2330,2454,2317. If provided, overrides universe-file.",
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
    return parser.parse_args()


def load_universe(universe_file: str) -> list[dict]:
    """Load universe from YAML file"""
    file_path = Path(universe_file)
    if not file_path.exists():
        raise FileNotFoundError(f"Universe file not found: {universe_file}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    return data.get("universe", [])


def sync_stocks_to_db(session, universe: list[dict]):
    """Sync universe stocks to stocks table"""
    for stock_data in universe:
        symbol = stock_data["symbol"]
        
        # Check if stock exists
        existing = session.query(Stock).filter(Stock.symbol == symbol).first()
        
        if existing:
            # Update if needed
            existing.name_zh = stock_data.get("name_zh")
            existing.name_en = stock_data.get("name_en")
            existing.sector = stock_data.get("sector_zh")  # Simplified: use sector_zh
            existing.updated_at = datetime.now()
        else:
            # Create new stock
            new_stock = Stock(
                symbol=symbol,
                name_zh=stock_data.get("name_zh"),
                name_en=stock_data.get("name_en"),
                sector=stock_data.get("sector_zh"),
                is_active=True,
            )
            session.add(new_stock)
    
    session.commit()
    logger.info(f"Synced {len(universe)} stocks to database")


def backfill_daily_bars(
    session,
    client: FinMindClient,
    symbol: str,
    start_date: date,
    end_date: date,
) -> int:
    """
    Backfill daily bars for a single symbol.
    
    Returns:
        int: Number of records inserted/updated
    """
    logger.info(f"Backfilling {symbol} from {start_date} to {end_date}...")
    
    try:
        # Fetch data from FinMind
        df = client.get_daily_price(symbol, start_date, end_date)
        
        if df.empty:
            logger.warning(f"No data for {symbol}")
            return 0
        
        # Ensure date column is datetime
        if "date" not in df.columns:
            logger.error(f"No 'date' column in data for {symbol}")
            return 0
        
        df["date"] = pd.to_datetime(df["date"]).dt.date
        
        inserted = 0
        updated = 0
        
        for _, row in df.iterrows():
            bar_date = row["date"]
            
            # Check if exists
            existing = (
                session.query(DailyBar)
                .filter(DailyBar.symbol == symbol, DailyBar.date == bar_date)
                .first()
            )
            
            if existing:
                # Update existing
                existing.open = float(row.get("open", 0.0))
                existing.high = float(row.get("high", 0.0))
                existing.low = float(row.get("low", 0.0))
                existing.close = float(row.get("close", 0.0))
                existing.volume = float(row.get("volume", 0.0))
                existing.turnover = float(row.get("turnover", 0.0)) if "turnover" in row else None
                existing.adjusted_close = float(row.get("adjusted_close", 0.0)) if "adjusted_close" in row else None
                existing.updated_at = datetime.now()
                updated += 1
            else:
                # Insert new
                new_bar = DailyBar(
                    symbol=symbol,
                    date=bar_date,
                    open=float(row.get("open", 0.0)),
                    high=float(row.get("high", 0.0)),
                    low=float(row.get("low", 0.0)),
                    close=float(row.get("close", 0.0)),
                    volume=float(row.get("volume", 0.0)),
                    turnover=float(row.get("turnover", 0.0)) if "turnover" in row else None,
                    adjusted_close=float(row.get("adjusted_close", 0.0)) if "adjusted_close" in row else None,
                    source="FinMind",
                )
                session.add(new_bar)
                inserted += 1
        
        session.commit()
        logger.info(f"  {symbol}: {inserted} inserted, {updated} updated")
        return inserted + updated
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error backfilling {symbol}: {e}", exc_info=True)
        return 0


def main():
    """Main function"""
    args = parse_args()
    
    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Determine symbol list: --symbols takes priority over --universe-file
    if args.symbols:
        # Parse symbols from CLI
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
        logger.info("Using symbols from CLI: %s", symbols)
        
        # Create simple universe list with only symbol field
        universe = [{"symbol": symbol} for symbol in symbols]
    else:
        # Load from universe file
        logger.info(f"Loading universe from {args.universe_file}...")
        universe = load_universe(args.universe_file)
        logger.info(f"Using universe file {args.universe_file} with {len(universe)} symbols")
    
    if not universe:
        logger.error("No symbols to process. Please provide --symbols or ensure universe file has symbols.")
        sys.exit(1)
    
    # Initialize FinMind client
    token = os.getenv("FINMIND_API_TOKEN")
    if not token:
        logger.error("FINMIND_API_TOKEN is not set in environment")
        sys.exit(1)
    
    client = FinMindClient(FinMindClientConfig(api_token=token))
    
    # Sync stocks to DB
    session_gen = get_session()
    session = next(session_gen)
    try:
        sync_stocks_to_db(session, universe)
        
        # Backfill daily bars for each symbol
        total_records = 0
        for stock_data in universe:
            symbol = stock_data["symbol"]
            records = backfill_daily_bars(session, client, symbol, start_date, end_date)
            total_records += records
        
        logger.info(f"✅ Backfill completed: {total_records} total records")
        
    finally:
        session.close()


if __name__ == "__main__":
    main()

