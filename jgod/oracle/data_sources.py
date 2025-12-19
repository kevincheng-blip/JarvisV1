"""
Data sources for baseline/truth prices (SQLite-first with stub fallback).
"""
from typing import Optional, Tuple, Dict
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import logging

logger = logging.getLogger(__name__)


class SQLitePriceSource:
    """SQLite-first price source with defensive table discovery."""
    
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
        Discover price table and column names.
        
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
            cursor = conn.cursor()
            
            # Query sqlite_master for table names
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND (
                    name LIKE '%daily%' OR 
                    name LIKE '%price%' OR 
                    name LIKE '%bar%' OR
                    name LIKE '%stock%'
                )
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Try common table patterns
            for table_name in tables:
                # Get column names
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = {row[1].lower(): row[1] for row in cursor.fetchall()}
                
                # Check if it has required columns
                date_col = None
                symbol_col = None
                price_col = None
                
                # Date column patterns
                for pattern in ['trade_date', 'date', 'tradedate', 'as_of_date']:
                    if pattern in columns:
                        date_col = columns[pattern]
                        break
                
                # Symbol column patterns
                for pattern in ['stock_id', 'symbol', 'stockid', 'code']:
                    if pattern in columns:
                        symbol_col = columns[pattern]
                        break
                
                # Price column patterns
                for pattern in ['close', 'closing_price', 'price']:
                    if pattern in columns:
                        price_col = columns[pattern]
                        break
                
                if date_col and symbol_col and price_col:
                    self._table_info = {
                        'table_name': table_name,
                        'date_col': date_col,
                        'symbol_col': symbol_col,
                        'price_col': price_col,
                    }
                    conn.close()
                    logger.info(f"Discovered price table: {table_name}")
                    return self._table_info
            
            conn.close()
            return None
        except Exception as e:
            logger.debug(f"Error discovering table: {e}")
            return None
    
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
            date: YYYY-MM-DD
            max_lookback_days: Maximum days to look back for missing date
            
        Returns:
            Tuple of (price, source, explain_dict)
            - price: float or None if not found
            - source: "sqlite" or "none"
            - explain: dict with asof_date_used, table_name, etc.
        """
        table_info = self._discover_table()
        if not table_info:
            return (None, "none", {"reason": "no_table_found"})
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Try exact date first
            query = f"""
                SELECT {table_info['price_col']}, {table_info['date_col']}
                FROM {table_info['table_name']}
                WHERE {table_info['symbol_col']} = ? 
                AND {table_info['date_col']} = ?
                LIMIT 1
            """
            cursor.execute(query, (symbol, date))
            row = cursor.fetchone()
            
            if row and row[0] is not None:
                conn.close()
                return (
                    float(row[0]), 
                    "sqlite",
                    {
                        "table": table_info['table_name'],
                        "date_used": date,
                        "exact_match": True,
                    }
                )
            
            # Fallback: look back up to max_lookback_days
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            for i in range(1, max_lookback_days + 1):
                lookback_date = (date_obj - timedelta(days=i)).strftime("%Y-%m-%d")
                cursor.execute(query, (symbol, lookback_date))
                row = cursor.fetchone()
                
                if row and row[0] is not None:
                    conn.close()
                    return (
                        float(row[0]),
                        "sqlite",
                        {
                            "table": table_info['table_name'],
                            "date_used": lookback_date,
                            "exact_match": False,
                            "lookback_days": i,
                        }
                    )
            
            conn.close()
            return (None, "none", {"reason": "no_data_found", "table": table_info['table_name']})
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
    Get baseline price (T0) for a symbol on a date.
    
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
    
    # Fallback to stub
    stub_price = _generate_stub_price(symbol, date)
    fallback_explain = dict(explain) if explain else {}
    fallback_explain["reason"] = "sqlite_fallback"
    return (stub_price, "stub", fallback_explain)


def get_truth_price(symbol: str, date: str, db_path: Optional[str] = None) -> Tuple[float, str, Dict]:
    """
    Get truth price (T+N) for a symbol on a date.
    
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
    
    # Fallback to stub
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
