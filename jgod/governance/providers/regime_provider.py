"""Regime Detection Provider

Computes market regime using Efficiency Ratio (ER) proxy.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Callable, List, Tuple
import numpy as np

from jgod.api.schemas.governance_summary import GovernanceModuleStatus

logger = logging.getLogger(__name__)


def _generate_mock_ohlc(bars: int = 100, volatility: float = 0.02) -> List[Tuple[float, float, float, float]]:
    """
    Generate mock OHLC data for regime detection.
    
    Args:
        bars: Number of bars to generate
        volatility: Volatility factor (higher = more noise)
    
    Returns:
        List of (open, high, low, close) tuples
    """
    np.random.seed(42)  # For reproducibility
    base_price = 100.0
    prices = [base_price]
    
    for _ in range(bars - 1):
        # Random walk with drift
        change = np.random.normal(0, volatility * base_price)
        new_price = prices[-1] + change
        prices.append(max(new_price, 1.0))  # Ensure positive
    
    # Convert to OHLC
    ohlc = []
    for i, close in enumerate(prices):
        open_price = prices[i-1] if i > 0 else close
        high = max(open_price, close) * (1 + abs(np.random.normal(0, volatility * 0.5)))
        low = min(open_price, close) * (1 - abs(np.random.normal(0, volatility * 0.5)))
        ohlc.append((open_price, high, low, close))
    
    return ohlc


def _compute_efficiency_ratio(prices: List[float]) -> float:
    """
    Compute Efficiency Ratio (ER).
    
    ER = abs(price[-1] - price[0]) / sum(abs(diff(price)))
    
    Args:
        prices: List of closing prices
    
    Returns:
        Efficiency Ratio (0.0 ~ 1.0+)
    """
    if len(prices) < 2:
        return 0.0
    
    # Net change
    net_change = abs(prices[-1] - prices[0])
    
    if net_change == 0:
        return 0.0
    
    # Sum of absolute changes
    diffs = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
    sum_abs_changes = sum(diffs)
    
    if sum_abs_changes == 0:
        return 0.0
    
    er = net_change / sum_abs_changes
    return float(er)


def get_regime_status(
    data_provider: Optional[Callable[[], List[Tuple[float, float, float, float]]]] = None,
) -> Tuple[GovernanceModuleStatus, str]:
    """
    Compute market regime using Efficiency Ratio.
    
    Args:
        data_provider: Optional callable that returns OHLC data.
                      If None, uses mock data generator.
    
    Returns:
        Tuple of (GovernanceModuleStatus, market_complexity)
    """
    # Get OHLC data
    ohlc_data: List[Tuple[float, float, float, float]] = []
    
    if data_provider:
        try:
            ohlc_data = data_provider()
        except Exception as e:
            logger.warning(f"Data provider failed: {e}", exc_info=False)
            ohlc_data = []
    else:
        # Use mock generator
        try:
            ohlc_data = _generate_mock_ohlc(bars=100)
        except Exception as e:
            logger.warning(f"Mock data generation failed: {e}", exc_info=False)
            ohlc_data = []
    
    if not ohlc_data:
        # Defensive: return UNKNOWN
        return (
            GovernanceModuleStatus(
                status="UNKNOWN",
                score=None,
                updated_at=datetime.utcnow().isoformat(),
                is_stub=True,
                reasons=["REGIME_STUB"],
                metrics={},
            ),
            "MEDIUM",
        )
    
    # Extract closing prices
    closes = [ohlc[3] for ohlc in ohlc_data]  # close is index 3
    
    # Compute Efficiency Ratio
    er = _compute_efficiency_ratio(closes)
    
    # Determine status
    if er < 0.2:
        status = "CHAOS"
        reason_code = "REGIME_CHAOS"
        market_complexity = "HIGH"
    elif er < 0.5:
        status = "COMPLEX"
        reason_code = "REGIME_COMPLEX"
        market_complexity = "MEDIUM"
    else:
        status = "STABLE"
        reason_code = "REGIME_STABLE"
        market_complexity = "LOW"
    
    return (
        GovernanceModuleStatus(
            status=status,
            score=er,
            updated_at=datetime.utcnow().isoformat(),
            is_stub=False,  # Real calculation
            reasons=[reason_code],
            metrics={
                "er": er,
                "bars": len(ohlc_data),
            },
        ),
        market_complexity,
    )
