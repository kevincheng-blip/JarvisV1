"""
Snapshot: Data snapshot consistency for learning triggers

v0.6.9-A9: Snapshot ID generation and payload creation
"""

import hashlib
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def create_snapshot_id(
    symbol: str,
    start_date: str,
    end_date: str,
    doctrine_version: str = "v1.0",
) -> str:
    """
    Create deterministic snapshot ID.
    
    Args:
        symbol: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        doctrine_version: Doctrine version
        
    Returns:
        Snapshot ID (e.g., "SNAP-2330-20240401-20240405-v1.0-abc123")
    """
    # Create deterministic hash
    hash_input = f"{symbol}-{start_date}-{end_date}-{doctrine_version}"
    hash_bytes = hashlib.md5(hash_input.encode()).hexdigest()[:6]
    
    # Format: SNAP-{symbol}-{start}-{end}-{version}-{hash}
    snapshot_id = f"SNAP-{symbol}-{start_date.replace('-', '')}-{end_date.replace('-', '')}-{doctrine_version}-{hash_bytes}"
    
    return snapshot_id


def create_snapshot_payload(
    symbol: str,
    start_date: str,
    end_date: str,
    *,
    doctrine_version: str = "v1.0",
    feature_version: str = "v1.0",
    window: int = 5,
    layer: Optional[str] = None,
) -> Dict:
    """
    Create snapshot payload for learning trigger.
    
    Args:
        symbol: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        doctrine_version: Doctrine version
        feature_version: Feature version
        window: Analysis window (days)
        layer: Learning layer name (optional)
        
    Returns:
        Snapshot payload dict
    """
    snapshot_id = create_snapshot_id(symbol, start_date, end_date, doctrine_version)
    
    payload = {
        "snapshot_id": snapshot_id,
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "doctrine_version": doctrine_version,
        "feature_version": feature_version,
        "window": window,
        "layer": layer,
        "created_at": datetime.now().isoformat(),
    }
    
    return payload

