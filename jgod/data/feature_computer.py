"""
Feature Computer: Deterministic feature computation

v0.6.7-A7.5: Minimal feature set (SMA/RSI/RET/VOL)
Future: Expand to 50+10 factors
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def compute_features(
    ohlcv_series: List[Dict],
    *,
    version: str = "v1.0"
) -> Dict:
    """
    Compute features from OHLCV series.
    
    Args:
        ohlcv_series: List of OHLCV dicts (chronological order, oldest first)
            Each dict must have: date, open, high, low, close, volume
        version: Feature computation version (default "v1.0")
        
    Returns:
        Dict with feature values:
        - SMA_5, SMA_20 (Simple Moving Average of close)
        - RSI_14 (Relative Strength Index)
        - VOL_MEAN_20 (Volume rolling mean)
        - RET_1D (1-day return: close[t] / close[t-1] - 1)
        
    Note: All calculations are deterministic (pure Python, no numpy).
    Missing window data returns None or 0 (consistent).
    """
    if not ohlcv_series:
        return {}
    
    # Extract close prices and volumes
    closes = [item.get("close", 0.0) for item in ohlcv_series]
    volumes = [item.get("volume", 0.0) for item in ohlcv_series]
    
    n = len(closes)
    features = {}
    
    # SMA_5 (Simple Moving Average, window=5)
    if n >= 5:
        sma_5 = sum(closes[-5:]) / 5.0
        features["SMA_5"] = round(sma_5, 2)
    else:
        features["SMA_5"] = None
    
    # SMA_20 (Simple Moving Average, window=20)
    if n >= 20:
        sma_20 = sum(closes[-20:]) / 20.0
        features["SMA_20"] = round(sma_20, 2)
    else:
        features["SMA_20"] = None
    
    # RSI_14 (Relative Strength Index, window=14)
    if n >= 15:  # Need at least 14 previous days + current day
        rsi_14 = _calculate_rsi(closes, window=14)
        features["RSI_14"] = round(rsi_14, 2) if rsi_14 is not None else None
    else:
        features["RSI_14"] = None
    
    # VOL_MEAN_20 (Volume rolling mean, window=20)
    if n >= 20:
        vol_mean_20 = sum(volumes[-20:]) / 20.0
        features["VOL_MEAN_20"] = round(vol_mean_20, 0)
    else:
        features["VOL_MEAN_20"] = None
    
    # RET_1D (1-day return)
    if n >= 2:
        prev_close = closes[-2]
        curr_close = closes[-1]
        if prev_close > 0:
            ret_1d = (curr_close / prev_close) - 1.0
            features["RET_1D"] = round(ret_1d, 4)
        else:
            features["RET_1D"] = None
    else:
        features["RET_1D"] = None
    
    return features


def _calculate_rsi(prices: List[float], window: int = 14) -> Optional[float]:
    """
    Calculate RSI (Relative Strength Index).
    
    Args:
        prices: List of close prices (chronological order)
        window: RSI window (default 14)
        
    Returns:
        RSI value (0-100) or None if insufficient data
    """
    if len(prices) < window + 1:
        return None
    
    # Calculate price changes
    changes = []
    for i in range(len(prices) - window, len(prices)):
        if i > 0:
            change = prices[i] - prices[i - 1]
            changes.append(change)
    
    if not changes:
        return None
    
    # Separate gains and losses
    gains = [c if c > 0 else 0.0 for c in changes]
    losses = [-c if c < 0 else 0.0 for c in changes]
    
    avg_gain = sum(gains) / len(gains)
    avg_loss = sum(losses) / len(losses)
    
    if avg_loss == 0:
        return 100.0  # All gains, RSI = 100
    
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    return rsi

