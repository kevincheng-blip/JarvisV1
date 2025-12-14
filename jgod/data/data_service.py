"""
Default Data Service: Implementation of DataServiceInterface

v0.6.10-A10: Default implementation using FeatureService and MarketDataService
"""

import logging
from typing import Dict, List, Optional

from jgod.data.data_service_interface import DataServiceInterface
from jgod.data.feature_service import FeatureService
from jgod.data.market_data_service import MarketDataService, OHLCVSnapshot

logger = logging.getLogger(__name__)


class DefaultDataService(DataServiceInterface):
    """
    Default implementation of DataServiceInterface.
    
    Uses existing FeatureService and MarketDataService.
    """
    
    def __init__(self, use_mock_mdts: bool = False):
        """
        Initialize DefaultDataService.
        
        Args:
            use_mock_mdts: If True, use mock MDTS (for testing)
        """
        self.feature_service = FeatureService(use_mock_mdts=use_mock_mdts)
        self.mdts = MarketDataService(use_mock=use_mock_mdts)
    
    def get_features(
        self,
        symbol: str,
        date: str,
        *,
        version: str = "v1.0",
        lookback: int = 60,
    ) -> Dict:
        """
        Get features for a symbol and date.
        
        Args:
            symbol: Stock symbol
            date: Date string (YYYY-MM-DD)
            version: Feature version
            lookback: Feature lookback days
            
        Returns:
            Dict with features (from FeatureSchema.features)
        """
        try:
            feature_schema = self.feature_service.get_feature(
                symbol=symbol,
                date=date,
                version=version,
                lookback=lookback,
            )
            return feature_schema.features
        except Exception as e:
            logger.error(f"Failed to get features for {symbol} on {date}: {e}", exc_info=True)
            return {}
    
    def get_ohlcv(
        self,
        symbol: str,
        date: str,
    ) -> Optional[Dict]:
        """
        Get OHLCV data for a symbol and date.
        
        Args:
            symbol: Stock symbol
            date: Date string (YYYY-MM-DD)
            
        Returns:
            Dict with {open, high, low, close, volume} or None if not found
        """
        try:
            ohlcv = self.mdts.fetch_ohlcv(symbol, date)
            if ohlcv is None:
                return None
            
            return {
                "open": ohlcv.open,
                "high": ohlcv.high,
                "low": ohlcv.low,
                "close": ohlcv.close,
                "volume": ohlcv.volume,
                "date": ohlcv.date,
            }
        except Exception as e:
            logger.error(f"Failed to get OHLCV for {symbol} on {date}: {e}", exc_info=True)
            return None
    
    def get_latest_data(
        self,
        symbol: str,
        now: datetime,
    ) -> Optional[Dict]:
        """
        Get latest data for a symbol (real-time).
        
        v0.6.11-A11: Real-time data access for ExecutionEngine.
        v0.6.12-A12: Returns None on error (no exception) for resilience.
        
        Args:
            symbol: Stock symbol
            now: Current datetime
            
        Returns:
            Dict with features (from FeatureSchema.features) or None if error
        """
        date_str = now.strftime("%Y-%m-%d")
        
        try:
            # Get features for current date
            features = self.get_features(
                symbol=symbol,
                date=date_str,
                version="v1.0",
                lookback=60,
            )
            
            # Return None if empty (v0.6.12-A12: graceful failure)
            if not features:
                return None
            
            return features
        except Exception as e:
            logger.error(f"Failed to get latest data for {symbol}: {e}", exc_info=True)
            return None  # v0.6.12-A12: Return None instead of raising
    
    def get_trading_dates(
        self,
        start_date: str,
        end_date: str,
    ) -> List[str]:
        """
        Get list of trading dates in range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of date strings (YYYY-MM-DD) in chronological order
        """
        try:
            # Use MDTS to fetch OHLCV range and extract dates
            ohlcv_snapshots = self.mdts.fetch_ohlcv_range(
                symbol="2330",  # Use a common symbol to get trading dates
                start_date=start_date,
                end_date=end_date,
            )
            
            if not ohlcv_snapshots:
                # Fallback: generate date range (simplified, assumes all dates are trading days)
                from datetime import datetime, timedelta
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                dates = []
                current = start
                while current <= end:
                    dates.append(current.strftime("%Y-%m-%d"))
                    current += timedelta(days=1)
                return dates
            
            # Extract unique dates and sort
            dates = sorted(set(snapshot.date for snapshot in ohlcv_snapshots))
            return dates
        except Exception as e:
            logger.error(f"Failed to get trading dates from {start_date} to {end_date}: {e}", exc_info=True)
            # Fallback: generate date range
            from datetime import datetime, timedelta
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            dates = []
            current = start
            while current <= end:
                dates.append(current.strftime("%Y-%m-%d"))
                current += timedelta(days=1)
            return dates

