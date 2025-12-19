"""
Data sources for baseline/truth prices (MVP: stub → real).
"""
from typing import Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def get_baseline_price(symbol: str, date: str) -> Tuple[float, str]:
    """
    Get baseline price (T0) for a symbol on a date.
    
    Args:
        symbol: Stock symbol
        date: YYYY-MM-DD
        
    Returns:
        Tuple of (price, source) where source is "close"|"intraday"|"stub"
    """
    # MVP: Try SQLite first, then stub
    try:
        from jgod.storage.db import get_db
        db = get_db()
        if db:
            # Try to read from daily bars table (adjust table name as needed)
            cursor = db.cursor()
            cursor.execute(
                "SELECT close FROM daily_bars WHERE symbol = ? AND date = ? LIMIT 1",
                (symbol, date)
            )
            row = cursor.fetchone()
            if row:
                return (float(row[0]), "close")
    except Exception as e:
        logger.debug(f"Could not read from DB for {symbol} on {date}: {e}")
    
    # Stub: Generate deterministic price based on symbol hash
    stub_price = _generate_stub_price(symbol, date)
    return (stub_price, "stub")


def get_truth_price(symbol: str, date: str) -> Tuple[float, str]:
    """
    Get truth price (T+N) for a symbol on a date.
    
    Args:
        symbol: Stock symbol
        date: YYYY-MM-DD
        
    Returns:
        Tuple of (price, source) where source is "close"|"stub"
    """
    # MVP: Try SQLite first, then stub
    try:
        from jgod.storage.db import get_db
        db = get_db()
        if db:
            cursor = db.cursor()
            cursor.execute(
                "SELECT close FROM daily_bars WHERE symbol = ? AND date = ? LIMIT 1",
                (symbol, date)
            )
            row = cursor.fetchone()
            if row:
                return (float(row[0]), "close")
    except Exception as e:
        logger.debug(f"Could not read truth price from DB for {symbol} on {date}: {e}")
    
    # Stub: Generate deterministic price
    stub_price = _generate_stub_price(symbol, date)
    return (stub_price, "stub")


def _generate_stub_price(symbol: str, date: str) -> float:
    """
    Generate deterministic stub price based on symbol and date.
    This ensures same symbol+date always gets same price (for testing).
    """
    # Simple hash-based price generation
    hash_val = hash(f"{symbol}_{date}") % 10000
    base_price = 50.0 + (hash_val / 100.0)  # Price between 50-150
    return round(base_price, 2)
