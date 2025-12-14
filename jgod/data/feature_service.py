"""
Feature Service: Unified entry point for Feature DB

v0.6.7-A7.5: Feature DB service layer (cache hit → miss → compute → save → return)
"""

import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

from jgod.data.feature_models import FeatureSchema
from jgod.data.feature_storage import save_feature, load_feature, has_feature
from jgod.data.feature_computer import compute_features
from jgod.data.market_data_service import MarketDataService, OHLCVSnapshot

logger = logging.getLogger(__name__)


class FeatureService:
    """Unified entry point for Feature DB (avoids recomputation)."""
    
    def __init__(
        self,
        market_data_service: Optional[MarketDataService] = None,
        use_mock_mdts: bool = False
    ):
        """
        Initialize FeatureService.
        
        Args:
            market_data_service: MarketDataService instance (if None, creates new)
            use_mock_mdts: If True, use mock MDTS (for testing)
        """
        if market_data_service is None:
            self.mdts = MarketDataService(use_mock=use_mock_mdts)
        else:
            self.mdts = market_data_service
    
    def get_feature(
        self,
        symbol: str,
        date: str,
        *,
        version: str = "v1.0",
        lookback: int = 60
    ) -> FeatureSchema:
        """
        Get feature (cache hit → miss → compute → save → return).
        
        Args:
            symbol: Stock symbol
            date: Date string (YYYY-MM-DD)
            version: Feature version
            lookback: Number of days to look back for feature computation
            
        Returns:
            FeatureSchema (always returns, computes if cache miss)
        """
        # Step 1: Try cache hit
        cached = load_feature(symbol, date, version)
        if cached is not None:
            logger.debug(f"Cache hit: {symbol}/{date}/{version}")
            return cached
        
        # Step 2: Cache miss → fetch OHLCV series
        logger.debug(f"Cache miss: {symbol}/{date}/{version}, computing...")
        
        # Calculate date range (date - lookback to date)
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        start_date = (target_date - timedelta(days=lookback)).strftime("%Y-%m-%d")
        
        ohlcv_snapshots = self.mdts.fetch_ohlcv_range(symbol, start_date, date)
        
        if not ohlcv_snapshots:
            logger.warning(f"No OHLCV data for {symbol} from {start_date} to {date}")
            # Return empty feature schema
            return FeatureSchema(
                symbol=symbol,
                date=date,
                version=version,
                ohlcv={},
                features={},
                meta={"error": "No OHLCV data available"},
            )
        
        # Step 3: Get current date's OHLCV snapshot
        current_ohlcv = None
        for snapshot in ohlcv_snapshots:
            if snapshot.date == date:
                current_ohlcv = snapshot
                break
        
        if current_ohlcv is None:
            logger.warning(f"No OHLCV data for {symbol} on {date}")
            return FeatureSchema(
                symbol=symbol,
                date=date,
                version=version,
                ohlcv={},
                features={},
                meta={"error": f"No OHLCV data for date {date}"},
            )
        
        # Step 4: Convert OHLCV snapshots to series format
        ohlcv_series = [
            {
                "date": s.date,
                "open": s.open,
                "high": s.high,
                "low": s.low,
                "close": s.close,
                "volume": s.volume,
            }
            for s in ohlcv_snapshots
        ]
        
        # Step 5: Compute features
        features = compute_features(ohlcv_series, version=version)
        
        # Step 6: Create FeatureSchema
        feature_schema = FeatureSchema(
            symbol=symbol,
            date=date,
            version=version,
            ohlcv={
                "open": current_ohlcv.open,
                "high": current_ohlcv.high,
                "low": current_ohlcv.low,
                "close": current_ohlcv.close,
                "volume": current_ohlcv.volume,
            },
            features=features,
            meta={
                "computed_at": datetime.now().isoformat(),
                "lookback": lookback,
                "ohlcv_count": len(ohlcv_snapshots),
            },
        )
        
        # Step 7: Save to storage
        try:
            save_feature(feature_schema)
            logger.debug(f"Saved feature: {symbol}/{date}/{version}")
        except Exception as e:
            logger.error(f"Failed to save feature {symbol}/{date}/{version}: {e}", exc_info=True)
        
        return feature_schema
    
    def recompute_range(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        version: str = "v1.0",
        lookback: int = 60,
        force: bool = False
    ) -> Dict:
        """
        Recompute features for a date range.
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            version: Feature version
            lookback: Number of days to look back for feature computation
            force: If True, recompute even if feature exists
            
        Returns:
            Dict with statistics: {computed_count, skipped_count, errors}
        """
        computed_count = 0
        skipped_count = 0
        errors = []
        
        # Generate date range
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            
            # Check if already exists
            if not force and has_feature(symbol, date_str, version):
                skipped_count += 1
                current += timedelta(days=1)
                continue
            
            # Compute feature
            try:
                self.get_feature(symbol, date_str, version=version, lookback=lookback)
                computed_count += 1
            except Exception as e:
                error_msg = f"Failed to compute {symbol}/{date_str}/{version}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
            
            current += timedelta(days=1)
        
        return {
            "computed_count": computed_count,
            "skipped_count": skipped_count,
            "errors": errors,
        }

