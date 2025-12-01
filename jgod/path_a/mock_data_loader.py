"""
Mock data loader for Path A v1.

This module provides a very simple, fully in-memory implementation of
the PathADataLoader protocol so that we can run the Path A backtest
skeleton without relying on external data sources (e.g. FinMind).

The goal is NOT to simulate realistic market dynamics, but to:
- Provide consistent OHLCV data over a small date range
- Provide a feature frame with a few simple features
- Allow the Path A pipeline to be exercised end-to-end in tests
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd

from jgod.path_a.path_a_schema import PathAConfig
from jgod.path_a.path_a_backtest import PathADataLoader


@dataclass
class MockPathADataLoader(PathADataLoader):
    """
    Very simple mock implementation of PathADataLoader.
    
    It generates:
    - A small date range from config.start_date to config.end_date
    - Random-walk prices for each symbol
    - Constant volume
    - A feature frame with:
        - daily_return_1d
        - rolling_vol_5d
    """
    
    seed: int = 42
    
    def _build_date_index(self, config: PathAConfig) -> pd.DatetimeIndex:
        """Build a business-day date index within the config window."""
        dates = pd.date_range(
            start=config.start_date,
            end=config.end_date,
            freq="B",  # business days
        )
        if len(dates) == 0:
            raise ValueError("MockPathADataLoader: empty date range")
        return dates
    
    # ------------------------------------------------------------------
    # PathADataLoader protocol implementation
    # ------------------------------------------------------------------
    
    def load_price_frame(self, config: PathAConfig) -> pd.DataFrame:
        """
        Generate a simple random-walk price frame for the given universe.
        
        Format:
            index: date
            columns: MultiIndex (symbol, field)
        """
        rng = np.random.default_rng(self.seed)
        dates = self._build_date_index(config)
        symbols: Sequence[str] = config.universe
        
        # base price for each symbol
        base_prices = {symbol: float(100 + 10 * i) for i, symbol in enumerate(symbols)}
        
        # random walk: daily return ~ N(0, 1%) for simplicity
        n_days = len(dates)
        n_symbols = len(symbols)
        
        daily_returns = rng.normal(loc=0.0005, scale=0.01, size=(n_days, n_symbols))
        prices = np.zeros_like(daily_returns)
        
        for j, symbol in enumerate(symbols):
            prices[0, j] = base_prices[symbol]
            for t in range(1, n_days):
                prices[t, j] = prices[t - 1, j] * (1.0 + daily_returns[t, j])
        
        # Build OHLCV with simple assumptions
        # open/close: use price; high/low: +/- small noise
        volume = rng.integers(low=1_000, high=10_000, size=(n_days, n_symbols))
        
        arrays = []
        data = []
        
        for j, symbol in enumerate(symbols):
            arrays.extend(
                [
                    (symbol, "open"),
                    (symbol, "high"),
                    (symbol, "low"),
                    (symbol, "close"),
                    (symbol, "volume"),
                ]
            )
            for t in range(n_days):
                p = prices[t, j]
                # small range for high/low
                high = p * (1.0 + rng.normal(0.0005, 0.002))
                low = p * (1.0 - rng.normal(0.0005, 0.002))
                # open/close share the same base price
                row = [p, high, low, p, volume[t, j]]
                data.append(row)
        
        # We built data in row-major order; reshape accordingly
        # There are len(symbols) * 5 columns.
        data_arr = np.array(data).reshape(len(dates), len(symbols) * 5)
        
        columns = pd.MultiIndex.from_tuples(arrays, names=["symbol", "field"])
        price_frame = pd.DataFrame(data_arr, index=dates, columns=columns)
        
        return price_frame.astype(float)
    
    def load_feature_frame(self, config: PathAConfig) -> pd.DataFrame:
        """
        Generate a feature frame aligned with the price frame.
        
        Features:
            - daily_return_1d
            - rolling_vol_5d
        
        Index:
            MultiIndex (date, symbol)
        """
        price_frame = self.load_price_frame(config)
        dates = price_frame.index
        symbols: Sequence[str] = config.universe
        
        # extract close prices into a (date x symbol) DataFrame
        if isinstance(price_frame.columns, pd.MultiIndex):
            close_cols = [(symbol, "close") for symbol in symbols]
            close_df = price_frame[close_cols]
            close_df.columns = list(symbols)
        else:
            # unlikely for this mock, but we keep a fallback
            close_cols = [f"{symbol}_close" for symbol in symbols]
            close_df = price_frame[close_cols]
            close_df.columns = list(symbols)
        
        # compute daily returns and rolling vol
        returns = close_df.pct_change().fillna(0.0)
        rolling_vol = returns.rolling(window=5, min_periods=1).std().fillna(0.0)
        
        # build MultiIndex index (date, symbol)
        multi_index = pd.MultiIndex.from_product(
            [dates, symbols], names=["date", "symbol"]
        )
        
        feature_data = {
            "daily_return_1d": [],
            "rolling_vol_5d": [],
        }
        
        for date in dates:
            for symbol in symbols:
                feature_data["daily_return_1d"].append(returns.loc[date, symbol])
                feature_data["rolling_vol_5d"].append(rolling_vol.loc[date, symbol])
        
        feature_frame = pd.DataFrame(feature_data, index=multi_index)
        
        return feature_frame

