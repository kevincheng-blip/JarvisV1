"""
Mock data loader for Path A v1 - Enhanced Version

This module provides a comprehensive, realistic mock implementation of
the PathADataLoader protocol. It generates fully consistent OHLCV data
with proper price relationships, realistic volume patterns, and complete
feature frames.

Key improvements:
- All prices are consistent (high >= max(open, close), low <= min(open, close))
- Volume follows realistic patterns with different scales per symbol
- Daily returns are capped at ±3%
- Comprehensive feature set (daily_return, rolling_vol, momentum, turnover_rate)
- Configurable via MockConfig dataclass
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, Dict

import numpy as np
import pandas as pd

from jgod.path_a.path_a_schema import PathAConfig
from jgod.path_a.path_a_backtest import PathADataLoader


@dataclass
class MockConfig:
    """
    Configuration for mock data generation.
    
    All magic numbers are centralized here for easy adjustment.
    """
    # Random seed for reproducibility
    seed: int = 42
    
    # Price simulation parameters
    max_daily_return: float = 0.03  # Maximum daily return (±3%)
    daily_return_mean: float = 0.0005  # Mean daily return (0.05%)
    daily_return_std: float = 0.005  # Daily return volatility (0.5%)
    min_price_gap: float = 0.001  # Minimum price gap (high - low)
    
    # Volume simulation parameters
    volume_base_multiplier: Dict[str, float] = field(default_factory=lambda: {
        "2330.TW": 50.0,  # TSMC: highest volume
        "2317.TW": 30.0,  # Foxconn: medium-high volume
        "2303.TW": 10.0,  # UMC: medium volume
    })
    volume_base_min: float = 1000.0
    volume_base_max: float = 10000.0
    volume_volatility: float = 0.3  # Volume volatility factor
    
    # Market cap simulation (for turnover rate calculation)
    market_cap_base: Dict[str, float] = field(default_factory=lambda: {
        "2330.TW": 15_000_000_000_000,  # TSMC: ~15 trillion
        "2317.TW": 3_000_000_000_000,   # Foxconn: ~3 trillion
        "2303.TW": 500_000_000_000,     # UMC: ~500 billion
    })
    
    # Base prices for different symbols
    base_prices: Dict[str, float] = field(default_factory=lambda: {
        "2330.TW": 550.0,
        "2317.TW": 120.0,
        "2303.TW": 50.0,
    })


@dataclass
class MockPathADataLoader(PathADataLoader):
    """
    Enhanced mock implementation of PathADataLoader.
    
    Generates realistic OHLCV data with:
    - Consistent price relationships (high >= max(open, close), etc.)
    - Realistic volume patterns with symbol-specific scales
    - Bounded daily returns (±max_daily_return)
    - Complete feature set for AlphaEngine
    """
    
    config: MockConfig = field(default_factory=MockConfig)
    
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
    
    def _get_base_price(self, symbol: str) -> float:
        """Get base price for a symbol, with fallback."""
        return self.config.base_prices.get(symbol, 100.0)
    
    def _get_volume_multiplier(self, symbol: str) -> float:
        """Get volume multiplier for a symbol, with fallback."""
        return self.config.volume_base_multiplier.get(symbol, 10.0)
    
    def _get_market_cap(self, symbol: str) -> float:
        """Get market cap for a symbol, with fallback."""
        return self.config.market_cap_base.get(symbol, 100_000_000_000)
    
    def _simulate_prices(
        self,
        rng: np.random.Generator,
        dates: pd.DatetimeIndex,
        symbols: Sequence[str],
    ) -> Dict[str, pd.Series]:
        """
        Simulate close prices using random walk with bounded returns.
        
        Returns:
            Dictionary mapping symbol -> Series of close prices
        """
        n_days = len(dates)
        close_prices: Dict[str, pd.Series] = {}
        
        for symbol in symbols:
            base_price = self._get_base_price(symbol)
            close_series = np.zeros(n_days)
            close_series[0] = base_price
            
            # Generate daily returns with bounds
            for t in range(1, n_days):
                # Generate return with normal distribution
                daily_return = rng.normal(
                    loc=self.config.daily_return_mean,
                    scale=self.config.daily_return_std
                )
                
                # Clip to max_daily_return
                daily_return = np.clip(
                    daily_return,
                    -self.config.max_daily_return,
                    self.config.max_daily_return
                )
                
                # Apply random walk
                close_series[t] = close_series[t - 1] * (1.0 + daily_return)
            
            close_prices[symbol] = pd.Series(close_series, index=dates)
        
        return close_prices
    
    def _build_ohlcv_from_close(
        self,
        rng: np.random.Generator,
        close_prices: Dict[str, pd.Series],
        dates: pd.DatetimeIndex,
    ) -> Dict[str, Dict[str, pd.Series]]:
        """
        Build OHLCV from close prices with proper relationships.
        
        Ensures:
        - high >= max(open, close)
        - low <= min(open, close)
        - high - low >= min_price_gap
        
        Returns:
            Dictionary mapping symbol -> {field: Series}
        """
        ohlcv: Dict[str, Dict[str, pd.Series]] = {}
        
        for symbol, close_series in close_prices.items():
            n_days = len(close_series)
            
            open_prices = np.zeros(n_days)
            high_prices = np.zeros(n_days)
            low_prices = np.zeros(n_days)
            
            for t in range(n_days):
                close = close_series.iloc[t]
                
                # Generate open price (previous close with small gap)
                if t == 0:
                    open_p = close
                else:
                    gap = rng.normal(0, close * 0.002)  # Small gap
                    open_p = close_series.iloc[t - 1] + gap
                
                # Ensure high >= max(open, close) and low <= min(open, close)
                min_price = min(open_p, close)
                max_price = max(open_p, close)
                
                # Generate high/low with proper bounds
                price_range = max(
                    max_price - min_price,
                    close * self.config.min_price_gap
                )
                
                # High is above max(open, close)
                high_p = max_price + rng.uniform(0, price_range * 0.3)
                
                # Low is below min(open, close)
                low_p = min_price - rng.uniform(0, price_range * 0.3)
                
                # Final validation
                high_p = max(high_p, max_price, close * (1 + self.config.min_price_gap))
                low_p = min(low_p, min_price, close * (1 - self.config.min_price_gap))
                
                open_prices[t] = open_p
                high_prices[t] = high_p
                low_prices[t] = low_p
            
            ohlcv[symbol] = {
                "open": pd.Series(open_prices, index=dates),
                "high": pd.Series(high_prices, index=dates),
                "low": pd.Series(low_prices, index=dates),
                "close": close_series,
            }
        
        return ohlcv
    
    def _simulate_volumes(
        self,
        rng: np.random.Generator,
        dates: pd.DatetimeIndex,
        symbols: Sequence[str],
    ) -> Dict[str, pd.Series]:
        """
        Simulate realistic volume patterns with symbol-specific scales.
        
        Uses incremental/fluctuating model rather than pure random.
        """
        volumes: Dict[str, pd.Series] = {}
        
        for symbol in symbols:
            multiplier = self._get_volume_multiplier(symbol)
            base_volume = rng.uniform(
                self.config.volume_base_min,
                self.config.volume_base_max
            )
            
            n_days = len(dates)
            volume_series = np.zeros(n_days)
            
            # Start with base volume
            current_volume = base_volume * multiplier
            
            for t in range(n_days):
                # Add random fluctuation
                fluctuation = rng.normal(1.0, self.config.volume_volatility)
                current_volume = current_volume * max(0.1, fluctuation)
                
                # Ensure volume is positive
                volume_series[t] = max(100.0, current_volume)
            
            volumes[symbol] = pd.Series(volume_series, index=dates)
        
        return volumes
    
    # ------------------------------------------------------------------
    # PathADataLoader protocol implementation
    # ------------------------------------------------------------------
    
    def load_price_frame(self, config: PathAConfig) -> pd.DataFrame:
        """
        Generate a realistic price frame for the given universe.
        
        Format:
            index: date (DatetimeIndex)
            columns: MultiIndex (symbol, field)
                fields: open, high, low, close, volume
        
        All prices are consistent:
        - high >= max(open, close)
        - low <= min(open, close)
        - high - low >= min_price_gap
        """
        rng = np.random.default_rng(self.config.seed)
        dates = self._build_date_index(config)
        symbols: Sequence[str] = config.universe
        
        # Step 1: Simulate close prices
        close_prices = self._simulate_prices(rng, dates, symbols)
        
        # Step 2: Build OHLC from close prices
        ohlcv = self._build_ohlcv_from_close(rng, close_prices, dates)
        
        # Step 3: Simulate volumes
        volumes = self._simulate_volumes(rng, dates, symbols)
        
        # Step 4: Build MultiIndex DataFrame
        arrays = []
        data_rows = []
        
        for symbol in symbols:
            arrays.extend([
                (symbol, "open"),
                (symbol, "high"),
                (symbol, "low"),
                (symbol, "close"),
                (symbol, "volume"),
            ])
        
        for date in dates:
            row_data = []
            for symbol in symbols:
                row_data.extend([
                    ohlcv[symbol]["open"].loc[date],
                    ohlcv[symbol]["high"].loc[date],
                    ohlcv[symbol]["low"].loc[date],
                    ohlcv[symbol]["close"].loc[date],
                    volumes[symbol].loc[date],
                ])
            data_rows.append(row_data)
        
        columns = pd.MultiIndex.from_tuples(arrays, names=["symbol", "field"])
        price_frame = pd.DataFrame(data_rows, index=dates, columns=columns)
        
        return price_frame.astype(float)
    
    def load_feature_frame(self, config: PathAConfig) -> pd.DataFrame:
        """
        Generate a comprehensive feature frame aligned with the price frame.
        
        Features:
            - daily_return_1d: Daily return (pct_change)
            - rolling_vol_5d: 5-day rolling volatility
            - rolling_vol_20d: 20-day rolling volatility
            - momentum_5d: 5-day momentum (close[t] / close[t-5] - 1)
            - momentum_20d: 20-day momentum (close[t] / close[t-20] - 1)
            - turnover_rate: volume / market_cap (simulated)
        
        Index:
            MultiIndex (date, symbol)
        """
        price_frame = self.load_price_frame(config)
        dates = price_frame.index
        symbols: Sequence[str] = config.universe
        
        # Extract price fields into DataFrames (date x symbol)
        if isinstance(price_frame.columns, pd.MultiIndex):
            close_cols = [(symbol, "close") for symbol in symbols]
            volume_cols = [(symbol, "volume") for symbol in symbols]
            
            close_df = price_frame[close_cols]
            close_df.columns = list(symbols)
            volume_df = price_frame[volume_cols]
            volume_df.columns = list(symbols)
        else:
            # Fallback for wide format
            close_cols = [f"{symbol}_close" for symbol in symbols]
            volume_cols = [f"{symbol}_volume" for symbol in symbols]
            
            close_df = price_frame[close_cols]
            close_df.columns = list(symbols)
            volume_df = price_frame[volume_cols]
            volume_df.columns = list(symbols)
        
        # Compute features
        returns = close_df.pct_change().fillna(0.0)
        rolling_vol_5d = returns.rolling(window=5, min_periods=1).std().fillna(0.0)
        rolling_vol_20d = returns.rolling(window=20, min_periods=1).std().fillna(0.0)
        
        # Momentum: close[t] / close[t-n] - 1
        momentum_5d = (close_df / close_df.shift(5) - 1).fillna(0.0)
        momentum_20d = (close_df / close_df.shift(20) - 1).fillna(0.0)
        
        # Turnover rate: volume / market_cap
        turnover_rate = pd.DataFrame(index=dates, columns=symbols)
        for symbol in symbols:
            market_cap = self._get_market_cap(symbol)
            turnover_rate[symbol] = volume_df[symbol] / market_cap
        
        turnover_rate = turnover_rate.fillna(0.0)
        
        # Build MultiIndex index (date, symbol)
        multi_index = pd.MultiIndex.from_product(
            [dates, symbols], names=["date", "symbol"]
        )
        
        # Collect all feature data
        feature_data = {
            "daily_return_1d": [],
            "rolling_vol_5d": [],
            "rolling_vol_20d": [],
            "momentum_5d": [],
            "momentum_20d": [],
            "turnover_rate": [],
            # Also include price fields for AlphaEngine
            "close": [],
            "volume": [],
            "open": [],
            "high": [],
            "low": [],
        }
        
        # Extract open/high/low for feature frame
        if isinstance(price_frame.columns, pd.MultiIndex):
            open_cols = [(symbol, "open") for symbol in symbols]
            high_cols = [(symbol, "high") for symbol in symbols]
            low_cols = [(symbol, "low") for symbol in symbols]
            
            open_df = price_frame[open_cols]
            open_df.columns = list(symbols)
            high_df = price_frame[high_cols]
            high_df.columns = list(symbols)
            low_df = price_frame[low_cols]
            low_df.columns = list(symbols)
        
        for date in dates:
            for symbol in symbols:
                feature_data["daily_return_1d"].append(returns.loc[date, symbol])
                feature_data["rolling_vol_5d"].append(rolling_vol_5d.loc[date, symbol])
                feature_data["rolling_vol_20d"].append(rolling_vol_20d.loc[date, symbol])
                feature_data["momentum_5d"].append(momentum_5d.loc[date, symbol])
                feature_data["momentum_20d"].append(momentum_20d.loc[date, symbol])
                feature_data["turnover_rate"].append(turnover_rate.loc[date, symbol])
                
                # Price fields
                feature_data["close"].append(close_df.loc[date, symbol])
                feature_data["volume"].append(volume_df.loc[date, symbol])
                feature_data["open"].append(open_df.loc[date, symbol])
                feature_data["high"].append(high_df.loc[date, symbol])
                feature_data["low"].append(low_df.loc[date, symbol])
        
        feature_frame = pd.DataFrame(feature_data, index=multi_index)
        
        return feature_frame
