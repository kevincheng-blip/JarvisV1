"""
Data Service Interface: Abstract data access layer

v0.6.10-A10: Data decoupling for portfolio scaling
Provides unified interface for feature and OHLCV data access.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class DataServiceInterface(ABC):
    """
    Abstract interface for data access.
    
    v0.6.10-A10: Decouples data access from WalkForwardRunner,
    enabling portfolio-level coordination and future real-time data integration.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass

