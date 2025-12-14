"""
Feature Models: Schema definitions for Feature DB

v0.6.7-A7.5: Feature DB/Cache schema
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class FeatureSchema:
    """
    Feature schema for Feature DB.
    
    Key: (symbol, date, version)
    - symbol: Stock symbol (e.g., "2330")
    - date: Date string (YYYY-MM-DD)
    - version: Feature computation version (e.g., "v1.0")
    
    Note: Currently features dict contains minimal set (SMA/RSI/RET/VOL).
    Future: Will expand to 50+10 factors, either as dict keys or typed fields.
    """
    symbol: str
    date: str  # YYYY-MM-DD
    version: str = "v1.0"
    ohlcv: Dict = field(default_factory=dict)  # {open, high, low, close, volume}
    features: Dict = field(default_factory=dict)  # Factor values (minimal set for M2)
    meta: Dict = field(default_factory=dict)  # Source, computation time, warnings, etc.
    
    def to_dict(self) -> Dict:
        """Convert to dict for JSONL storage."""
        return {
            "symbol": self.symbol,
            "date": self.date,
            "version": self.version,
            "ohlcv": self.ohlcv,
            "features": self.features,
            "meta": self.meta,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "FeatureSchema":
        """Create from dict (for JSONL loading)."""
        return cls(
            symbol=data.get("symbol", ""),
            date=data.get("date", ""),
            version=data.get("version", "v1.0"),
            ohlcv=data.get("ohlcv", {}),
            features=data.get("features", {}),
            meta=data.get("meta", {}),
        )

