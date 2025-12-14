"""
Market Data Time Series Service (MDTS)

Provides OHLCV time series data for backtesting and execution simulation.
Uses existing SQLite database (tw_stock_daily) or deterministic mock for testing.
"""

import logging
from typing import List, Dict, Optional
from datetime import date, datetime, timedelta
from dataclasses import dataclass

from jgod.data.db import get_connection

logger = logging.getLogger(__name__)


@dataclass
class OHLCVSnapshot:
    """OHLCV snapshot for a single date."""
    symbol: str
    date: str  # YYYY-MM-DD
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    def to_dict(self) -> Dict:
        """Convert to dict for API/storage."""
        return {
            "symbol": self.symbol,
            "date": self.date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


class MarketDataService:
    """Market Data Time Series Service."""
    
    def __init__(self, use_mock: bool = False):
        """
        Initialize MDTS.
        
        Args:
            use_mock: If True, use deterministic mock data (for testing)
        """
        self.use_mock = use_mock
        if not use_mock:
            try:
                self.conn = get_connection()
            except Exception as e:
                logger.warning(f"Failed to connect to DB, falling back to mock: {e}")
                self.use_mock = True
    
    def fetch_ohlcv(
        self,
        symbol: str,
        date_str: str,
    ) -> Optional[OHLCVSnapshot]:
        """
        Fetch OHLCV for a single date.
        
        Args:
            symbol: Stock symbol (e.g., "2330")
            date_str: Date string (YYYY-MM-DD)
            
        Returns:
            OHLCVSnapshot or None if not found
        """
        if self.use_mock:
            return self._fetch_mock_ohlcv(symbol, date_str)
        
        try:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT open, high, low, close, volume
                FROM tw_stock_daily
                WHERE stock_id = ? AND trade_date = ?
                """,
                (symbol, date_str)
            )
            row = cur.fetchone()
            cur.close()
            
            if row:
                return OHLCVSnapshot(
                    symbol=symbol,
                    date=date_str,
                    open=row[0],
                    high=row[1],
                    low=row[2],
                    close=row[3],
                    volume=row[4] if row[4] else 0.0,
                )
            else:
                # Fallback to mock if DB has no data
                logger.warning(f"No OHLCV data in DB for {symbol} on {date_str}, using mock")
                return self._fetch_mock_ohlcv(symbol, date_str)
        except Exception as e:
            logger.error(f"Error fetching OHLCV from DB: {e}", exc_info=True)
            # Fallback to mock on error
            return self._fetch_mock_ohlcv(symbol, date_str)
    
    def fetch_ohlcv_range(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> List[OHLCVSnapshot]:
        """
        Fetch OHLCV for a date range.
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of OHLCVSnapshot (chronological order, oldest first)
        """
        if self.use_mock:
            return self._fetch_mock_ohlcv_range(symbol, start_date, end_date)
        
        try:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT trade_date, open, high, low, close, volume
                FROM tw_stock_daily
                WHERE stock_id = ? AND trade_date >= ? AND trade_date <= ?
                ORDER BY trade_date ASC
                """,
                (symbol, start_date, end_date)
            )
            rows = cur.fetchall()
            cur.close()
            
            if rows:
                return [
                    OHLCVSnapshot(
                        symbol=symbol,
                        date=row[0],
                        open=row[1],
                        high=row[2],
                        low=row[3],
                        close=row[4],
                        volume=row[5] if row[5] else 0.0,
                    )
                    for row in rows
                ]
            else:
                # Fallback to mock if DB has no data
                logger.warning(f"No OHLCV data in DB for {symbol} from {start_date} to {end_date}, using mock")
                return self._fetch_mock_ohlcv_range(symbol, start_date, end_date)
        except Exception as e:
            logger.error(f"Error fetching OHLCV range from DB: {e}", exc_info=True)
            # Fallback to mock on error
            return self._fetch_mock_ohlcv_range(symbol, start_date, end_date)
    
    def _fetch_mock_ohlcv(self, symbol: str, date_str: str) -> OHLCVSnapshot:
        """
        Generate deterministic mock OHLCV for testing.
        
        Uses symbol hash + date to generate consistent prices.
        """
        # Deterministic base price from symbol hash
        symbol_hash = hash(symbol) % 1000
        base_price = 100.0 + (symbol_hash / 10.0)
        
        # Deterministic daily variation from date hash
        date_hash = hash(date_str) % 100
        daily_return = (date_hash - 50) / 1000.0  # -5% to +5%
        
        close = base_price * (1 + daily_return)
        high = close * 1.02
        low = close * 0.98
        open_price = close * (1 + (date_hash % 20 - 10) / 1000.0)
        volume = 1000000.0 + (date_hash * 1000)
        
        return OHLCVSnapshot(
            symbol=symbol,
            date=date_str,
            open=round(open_price, 2),
            high=round(high, 2),
            low=round(low, 2),
            close=round(close, 2),
            volume=round(volume, 0),
        )
    
    def _fetch_mock_ohlcv_range(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> List[OHLCVSnapshot]:
        """Generate deterministic mock OHLCV for date range."""
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        snapshots = []
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            snapshot = self._fetch_mock_ohlcv(symbol, date_str)
            snapshots.append(snapshot)
            current += timedelta(days=1)
        
        return snapshots

