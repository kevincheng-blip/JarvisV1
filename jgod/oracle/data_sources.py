"""
Data sources for baseline/truth prices (SQLite-first with stub fallback).
Enhanced with column mapping, date format detection, and proper fallback.
"""
from typing import Optional, Tuple, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import logging
import re

logger = logging.getLogger(__name__)


def _list_tables(conn: sqlite3.Connection) -> List[str]:
    """List all tables in database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [row[0] for row in cursor.fetchall()]


def _table_columns(conn: sqlite3.Connection, table: str) -> Dict[str, str]:
    """Get column names for a table (lowercase -> actual name mapping)."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = {}
    for row in cursor.fetchall():
        actual_name = row[1]
        columns[actual_name.lower()] = actual_name
    return columns


def _pick_column(columns: Dict[str, str], candidates: List[str]) -> Optional[str]:
    """
    Pick the first matching column from candidates.
    
    Args:
        columns: Dict of lowercase -> actual column name
        candidates: List of candidate names (lowercase)
        
    Returns:
        Actual column name or None
    """
    for candidate in candidates:
        if candidate.lower() in columns:
            return columns[candidate.lower()]
    return None


def _normalize_date(date_str: str) -> Dict[str, str]:
    """
    Normalize date string to multiple formats for querying.
    
    Args:
        date_str: Date string (YYYY-MM-DD or other formats)
        
    Returns:
        Dict with normalized formats: {yyyymmdd, yyyy_mm_dd, yyyy_mm_dd_slash}
    """
    # Try to parse the input date
    formats = [
        "%Y-%m-%d",
        "%Y%m%d",
        "%Y/%m/%d",
    ]
    
    date_obj = None
    for fmt in formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            break
        except ValueError:
            continue
    
    if date_obj is None:
        # Fallback: try to extract YYYY-MM-DD pattern
        match = re.search(r'(\d{4})[-/]?(\d{2})[-/]?(\d{2})', date_str)
        if match:
            year, month, day = match.groups()
            date_obj = datetime(int(year), int(month), int(day))
        else:
            raise ValueError(f"Cannot parse date: {date_str}")
    
    return {
        "yyyymmdd": date_obj.strftime("%Y%m%d"),
        "yyyy_mm_dd": date_obj.strftime("%Y-%m-%d"),
        "yyyy_mm_dd_slash": date_obj.strftime("%Y/%m/%d"),
    }


class SQLitePriceSource:
    """SQLite-first price source with defensive table discovery and column mapping."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SQLite price source.
        
        Args:
            db_path: Path to SQLite database (default: data/jgod_tw_stock.db)
        """
        if db_path is None:
            project_root = Path(__file__).resolve().parents[2]
            db_path = str(project_root / "data" / "jgod_tw_stock.db")
        
        self.db_path = Path(db_path)
        self._table_info = None  # Cache table discovery
    
    def _discover_table(self) -> Optional[Dict[str, str]]:
        """
        Discover price table and column names with flexible mapping.
        
        Returns:
            Dict with table_name, date_col, symbol_col, price_col, or None if not found
        """
        if self._table_info is not None:
            return self._table_info
        
        if not self.db_path.exists():
            logger.debug(f"Database not found: {self.db_path}")
            return None
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            
            # Get all tables
            tables = _list_tables(conn)
            
            # Priority: tw_stock_daily first, then any table with daily/price/stock
            priority_tables = []
            other_tables = []
            
            for table in tables:
                if "tw_stock_daily" in table.lower():
                    priority_tables.insert(0, table)
                elif any(keyword in table.lower() for keyword in ["daily", "price", "stock", "bar"]):
                    priority_tables.append(table)
                else:
                    other_tables.append(table)
            
            # Try priority tables first
            for table_name in priority_tables + other_tables:
                columns = _table_columns(conn, table_name)
                
                # Find date column
                date_col = _pick_column(columns, ["trade_date", "date", "tradedate", "as_of_date", "time", "Time"])
                if not date_col:
                    continue
                
                # Find symbol column
                symbol_col = _pick_column(columns, ["stock_id", "symbol", "ticker", "stock", "sid", "code"])
                if not symbol_col:
                    continue
                
                # Find price column
                price_col = _pick_column(columns, ["close", "close_price", "Close", "adj_close", "price"])
                if not price_col:
                    continue
                
                # Found valid table
                self._table_info = {
                    'table_name': table_name,
                    'date_col': date_col,
                    'symbol_col': symbol_col,
                    'price_col': price_col,
                }
                conn.close()
                logger.info(f"Discovered price table: {table_name} (date={date_col}, symbol={symbol_col}, price={price_col})")
                return self._table_info
            
            conn.close()
            return None
        except Exception as e:
            logger.debug(f"Error discovering table: {e}")
            return None
    
    def _query_close(
        self,
        conn: sqlite3.Connection,
        table: str,
        col_date: str,
        col_symbol: str,
        col_close: str,
        date_formats: Dict[str, str],
        symbol: str,
        lookback_days: int = 7
    ) -> Tuple[Optional[float], Optional[str], Optional[int], Optional[str]]:
        """
        Query close price with date format flexibility and lookback.
        
        Returns:
            Tuple of (price, date_format_used, lookback_days, used_date)
        """
        # Try each date format
        for fmt_name, date_value in date_formats.items():
            # Try exact match first
            query = f"""
                SELECT {col_close}, {col_date}
                FROM {table}
                WHERE {col_symbol} = ?
                AND {col_date} = ?
                ORDER BY {col_date} DESC
                LIMIT 1
            """
            cursor = conn.cursor()
            cursor.execute(query, (symbol, date_value))
            row = cursor.fetchone()
            
            if row and row[0] is not None:
                return (float(row[0]), fmt_name, 0, row[1])
        
        # Fallback: look back using <= date query (works for any format)
        date_obj = datetime.strptime(date_formats["yyyy_mm_dd"], "%Y-%m-%d")
        
        for i in range(1, lookback_days + 1):
            lookback_date = (date_obj - timedelta(days=i))
            
            # Try all formats for lookback date
            lookback_formats = {
                "yyyymmdd": lookback_date.strftime("%Y%m%d"),
                "yyyy_mm_dd": lookback_date.strftime("%Y-%m-%d"),
                "yyyy_mm_dd_slash": lookback_date.strftime("%Y/%m/%d"),
            }
            
            for fmt_name, date_value in lookback_formats.items():
                query = f"""
                    SELECT {col_close}, {col_date}
                    FROM {table}
                    WHERE {col_symbol} = ?
                    AND {col_date} <= ?
                    ORDER BY {col_date} DESC
                    LIMIT 1
                """
                cursor.execute(query, (symbol, date_value))
                row = cursor.fetchone()
                
                if row and row[0] is not None:
                    return (float(row[0]), fmt_name, i, row[1])
        
        return (None, None, None, None)
    
    def get_close(
        self, 
        symbol: str, 
        date: str,
        max_lookback_days: int = 7
    ) -> Tuple[Optional[float], str, Dict]:
        """
        Get close price for symbol on date (with fallback to recent trading days).
        
        Args:
            symbol: Stock symbol
            date: YYYY-MM-DD (or other formats)
            max_lookback_days: Maximum days to look back for missing date
            
        Returns:
            Tuple of (price, source, meta_dict)
            - price: float or None if not found
            - source: "sqlite" or "none"
            - meta: dict with table, columns, date_format_used, used_date, lookback_days, etc.
        """
        table_info = self._discover_table()
        if not table_info:
            return (None, "none", {"reason": "no_table_found"})
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            
            # Normalize date to multiple formats
            try:
                date_formats = _normalize_date(date)
            except ValueError as e:
                conn.close()
                return (None, "none", {"reason": f"invalid_date_format: {e}"})
            
            # Query with format flexibility and lookback
            price, date_format_used, lookback_days, used_date = self._query_close(
                conn=conn,
                table=table_info['table_name'],
                col_date=table_info['date_col'],
                col_symbol=table_info['symbol_col'],
                col_close=table_info['price_col'],
                date_formats=date_formats,
                symbol=symbol,
                lookback_days=max_lookback_days
            )
            
            conn.close()
            
            if price is not None:
                meta = {
                    "table": table_info['table_name'],
                    "col_date": table_info['date_col'],
                    "col_symbol": table_info['symbol_col'],
                    "col_close": table_info['price_col'],
                    "date_format_used": date_format_used,
                    "used_date": used_date,
                    "exact_match": lookback_days == 0,
                }
                if lookback_days > 0:
                    meta["lookback_days"] = lookback_days
                return (price, "sqlite", meta)
            
            return (None, "none", {
                "reason": "no_data_found",
                "table": table_info['table_name'],
                "date_formats_tried": list(date_formats.values()),
            })
        except Exception as e:
            logger.debug(f"Error querying SQLite for {symbol} on {date}: {e}")
            return (None, "none", {"reason": str(e)})


# Global SQLite source instance (lazy init)
_sqlite_source: Optional[SQLitePriceSource] = None


def get_sqlite_source(db_path: Optional[str] = None) -> SQLitePriceSource:
    """Get or create global SQLite source."""
    global _sqlite_source
    if _sqlite_source is None or (db_path and _sqlite_source.db_path != Path(db_path)):
        _sqlite_source = SQLitePriceSource(db_path)
    return _sqlite_source


def get_baseline_price(symbol: str, date: str, db_path: Optional[str] = None) -> Tuple[float, str, Dict]:
    """
    Get baseline price (T0) for a symbol on a date (SQLite-first).
    
    Args:
        symbol: Stock symbol
        date: YYYY-MM-DD
        db_path: Optional SQLite database path
        
    Returns:
        Tuple of (price, source, explain) where:
        - source is "sqlite"|"stub"|"none"
        - explain is dict with metadata
    """
    # Try SQLite first
    sqlite_source = get_sqlite_source(db_path)
    price, source, explain = sqlite_source.get_close(symbol, date)
    
    if price is not None and source == "sqlite":
        return (price, source, explain)
    
    # Fallback to stub (always return a valid price, never None)
    stub_price = _generate_stub_price(symbol, date)
    fallback_explain = dict(explain) if explain else {}
    fallback_explain["reason"] = "sqlite_fallback"
    return (stub_price, "stub", fallback_explain)


def get_truth_price(symbol: str, date: str, db_path: Optional[str] = None) -> Tuple[float, str, Dict]:
    """
    Get truth price (T+N) for a symbol on a date (SQLite-first).
    
    Args:
        symbol: Stock symbol
        date: YYYY-MM-DD
        db_path: Optional SQLite database path
        
    Returns:
        Tuple of (price, source, explain) where:
        - source is "sqlite"|"stub"|"none"
        - explain is dict with metadata
    """
    # Try SQLite first
    sqlite_source = get_sqlite_source(db_path)
    price, source, explain = sqlite_source.get_close(symbol, date)
    
    if price is not None and source == "sqlite":
        return (price, source, explain)
    
    # Fallback to stub (always return a valid price, never None)
    stub_price = _generate_stub_price(symbol, date)
    fallback_explain = dict(explain) if explain else {}
    fallback_explain["reason"] = "sqlite_fallback"
    return (stub_price, "stub", fallback_explain)


def _generate_stub_price(symbol: str, date: str) -> float:
    """
    Generate deterministic stub price based on symbol and date.
    This ensures same symbol+date always gets same price (for testing).
    """
    # Simple hash-based price generation
    hash_val = hash(f"{symbol}_{date}") % 10000
    base_price = 50.0 + (hash_val / 100.0)  # Price between 50-150
    return round(base_price, 2)
