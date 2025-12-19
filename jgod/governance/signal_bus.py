"""Signal Bus Interface

Governance data bus for standardized signal access.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TypedDict, List, Optional, Callable

logger = logging.getLogger(__name__)


class SignalPayload(TypedDict):
    """Standardized governance signal payload"""
    id: str              # Unique identifier
    family: str          # e.g. "M50", "Execution", "RegimeProxy"
    value: float         # -1.0 ~ 1.0
    weight: float        # 0~1
    timestamp: datetime


class SignalBus:
    """Governance signal bus for standardized signal access"""
    
    def __init__(
        self,
        discovery_provider: Optional[Callable[[str], List[SignalPayload]]] = None,
        mock_provider: Optional[Callable[[str], List[SignalPayload]]] = None,
        cache_ttl_seconds: int = 60,
    ):
        """
        Initialize signal bus
        
        Args:
            discovery_provider: Optional callable to discover signals from existing system
            mock_provider: Optional callable to generate mock signals
            cache_ttl_seconds: Cache TTL in seconds
        """
        self.discovery_provider = discovery_provider
        self.mock_provider = mock_provider or self._default_mock_provider
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, tuple[List[SignalPayload], datetime]] = {}
        logger.info("SignalBus initialized")
    
    def _default_mock_provider(self, family: str) -> List[SignalPayload]:
        """Default mock provider for testing"""
        if family == "M50":
            # Generate synthetic M50 signals: 10 positive, 3 negative
            signals = []
            base_time = datetime.utcnow()
            for i in range(10):
                signals.append(SignalPayload(
                    id=f"m50_pos_{i}",
                    family="M50",
                    value=0.5 + (i * 0.05),
                    weight=1.0,
                    timestamp=base_time - timedelta(seconds=i),
                ))
            for i in range(3):
                signals.append(SignalPayload(
                    id=f"m50_neg_{i}",
                    family="M50",
                    value=-0.4 - (i * 0.1),
                    weight=1.0,
                    timestamp=base_time - timedelta(seconds=10 + i),
                ))
            return signals
        return []
    
    def _try_discovery(self, family: str) -> Optional[List[SignalPayload]]:
        """Try to discover signals from existing system"""
        if not self.discovery_provider:
            return None
        
        try:
            signals = self.discovery_provider(family)
            if signals and isinstance(signals, list):
                return signals
        except Exception as e:
            logger.debug(f"Discovery provider failed for {family}: {e}", exc_info=False)
        
        return None
    
    def _is_cache_valid(self, cache_entry: tuple[List[SignalPayload], datetime]) -> bool:
        """Check if cache entry is still valid"""
        _, cached_time = cache_entry
        age = (datetime.utcnow() - cached_time).total_seconds()
        return age < self.cache_ttl_seconds
    
    def get_latest_signals(self, family: Optional[str] = None) -> List[SignalPayload]:
        """
        Get latest signals from bus
        
        Priority:
        1. Memory cache (if valid)
        2. Discovery provider
        3. Mock provider
        4. Empty list (defensive)
        
        Args:
            family: Optional signal family filter (e.g. "M50")
        
        Returns:
            List of SignalPayload (never None, may be empty)
        """
        cache_key = family or "all"
        
        # Check cache first
        if cache_key in self._cache:
            cached_signals, cached_time = self._cache[cache_key]
            if self._is_cache_valid((cached_signals, cached_time)):
                logger.debug(f"Returning cached signals for {cache_key}")
                return cached_signals
            else:
                # Cache expired, remove it
                del self._cache[cache_key]
        
        # Try discovery
        if family:
            discovered = self._try_discovery(family)
            if discovered:
                # Cache the result
                self._cache[cache_key] = (discovered, datetime.utcnow())
                return discovered
        
        # Fall back to mock provider
        try:
            mock_signals = self.mock_provider(family or "M50")
            if mock_signals:
                # Cache the result
                self._cache[cache_key] = (mock_signals, datetime.utcnow())
                return mock_signals
        except Exception as e:
            logger.warning(f"Mock provider failed: {e}", exc_info=False)
        
        # Defensive: return empty list
        logger.debug(f"No signals found for {family}, returning empty list")
        return []


# Global singleton instance
_signal_bus: Optional[SignalBus] = None


def get_signal_bus() -> SignalBus:
    """Get global signal bus instance"""
    global _signal_bus
    if _signal_bus is None:
        _signal_bus = SignalBus()
    return _signal_bus
