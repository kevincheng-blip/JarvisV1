"""
Mock Data Loader Extreme - Professional Quant Fund Grade

This module provides an extreme-level mock implementation with:
- Realistic market behavior (OU process, volatility regimes)
- Realistic volume patterns (Gamma distribution)
- Price shocks and event simulation
- Comprehensive feature set (VWAP, ATR, skewness, kurtosis)
- Configurable via MockConfigExtreme
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, Dict, Literal
from enum import Enum

import numpy as np
import pandas as pd

from jgod.path_a.path_a_schema import PathAConfig
from jgod.path_a.path_a_backtest import PathADataLoader


class VolatilityRegime(str, Enum):
    """Volatility regime types."""
    LOW = "low"
    MID = "mid"
    HIGH = "high"


@dataclass
class MockConfigExtreme:
    """
    Extreme configuration for professional-grade mock data generation.
    
    All parameters are tuned for realistic market simulation.
    """
    # Random seed for reproducibility
    seed: int = 42
    
    # OU Process parameters (Ornstein-Uhlenbeck for mean reversion)
    ou_theta: float = 0.1  # Mean reversion speed
    ou_mu: float = 0.0005  # Long-term mean return
    ou_sigma_min: float = 0.01  # Minimum volatility (1%)
    ou_sigma_max: float = 0.04  # Maximum volatility (4%)
    
    # Volatility regime
    volatility_regime: VolatilityRegime = VolatilityRegime.MID
    
    # Price shock parameters
    allow_shocks: bool = True
    shock_probability: float = 0.02  # 2% chance per day
    shock_magnitude: float = 0.05  # ±5% shock
    
    # Volume simulation parameters
    volume_base_multiplier: Dict[str, float] = field(default_factory=lambda: {
        "2330.TW": 50.0,
        "2317.TW": 30.0,
        "2303.TW": 10.0,
    })
    volume_base_min: float = 1000.0
    volume_base_max: float = 10000.0
    volume_gamma_shape: float = 2.0  # Gamma distribution shape
    volume_gamma_scale: float = 1.0  # Gamma distribution scale
    
    # Market cap simulation (for turnover rate)
    market_cap_base: Dict[str, float] = field(default_factory=lambda: {
        "2330.TW": 15_000_000_000_000,
        "2317.TW": 3_000_000_000_000,
        "2303.TW": 500_000_000_000,
    })
    
    # Base prices
    base_prices: Dict[str, float] = field(default_factory=lambda: {
        "2330.TW": 550.0,
        "2317.TW": 120.0,
        "2303.TW": 50.0,
    })


@dataclass
class MockPathADataLoaderExtreme(PathADataLoader):
    """
    Extreme mock implementation with professional-grade market simulation.
    
    Features:
    - OU process for price generation (mean reversion)
    - Stochastic volatility (1-4%)
    - Realistic volume patterns (Gamma distribution)
    - Price shocks simulation
    - Comprehensive features (VWAP, ATR, skewness, kurtosis)
    """
    
    config: MockConfigExtreme = field(default_factory=MockConfigExtreme)
    
    def _get_volatility_regime_value(self) -> float:
        """Get volatility based on regime."""
        regime_map = {
            VolatilityRegime.LOW: 0.5,
            VolatilityRegime.MID: 1.0,
            VolatilityRegime.HIGH: 1.5,
        }
        multiplier = regime_map.get(self.config.volatility_regime, 1.0)
        base_vol = (self.config.ou_sigma_min + self.config.ou_sigma_max) / 2
        return base_vol * multiplier
    
    def _build_date_index(self, config: PathAConfig) -> pd.DatetimeIndex:
        """Build a business-day date index."""
        dates = pd.date_range(
            start=config.start_date,
            end=config.end_date,
            freq="B",
        )
        if len(dates) == 0:
            raise ValueError("MockPathADataLoaderExtreme: empty date range")
        return dates
    
    def _simulate_ou_process(
        self,
        rng: np.random.Generator,
        dates: pd.DatetimeIndex,
        base_price: float,
    ) -> pd.Series:
        """
        Simulate price using Ornstein-Uhlenbeck process.
        
        dX = θ(μ - X)dt + σ dW
        
        Returns:
            Series of close prices
        """
        n_days = len(dates)
        prices = np.zeros(n_days)
        prices[0] = base_price
        
        # Stochastic volatility
        vol_base = self._get_volatility_regime_value()
        
        for t in range(1, n_days):
            # Random volatility between min and max
            current_vol = rng.uniform(
                self.config.ou_sigma_min,
                self.config.ou_sigma_max
            )
            current_vol *= vol_base / ((self.config.ou_sigma_min + self.config.ou_sigma_max) / 2)
            
            # OU process step
            dt = 1.0  # Daily step
            drift = self.config.ou_theta * (self.config.ou_mu - np.log(prices[t-1] / base_price)) * dt
            diffusion = current_vol * np.sqrt(dt) * rng.normal(0, 1)
            
            log_return = drift + diffusion
            prices[t] = prices[t-1] * np.exp(log_return)
        
        return pd.Series(prices, index=dates)
    
    def _apply_price_shocks(
        self,
        rng: np.random.Generator,
        prices: pd.Series,
        dates: pd.DatetimeIndex,
    ) -> pd.Series:
        """Apply random price shocks."""
        if not self.config.allow_shocks:
            return prices
        
        prices = prices.copy()
        n_days = len(dates)
        
        for t in range(1, n_days):
            if rng.random() < self.config.shock_probability:
                # Random shock direction
                shock_sign = rng.choice([-1, 1])
                shock_magnitude = rng.uniform(
                    self.config.shock_magnitude * 0.5,
                    self.config.shock_magnitude
                )
                
                shock = 1.0 + (shock_sign * shock_magnitude)
                prices.iloc[t] = prices.iloc[t] * shock
        
        return prices
    
    def _build_ohlcv_from_close_extreme(
        self,
        rng: np.random.Generator,
        close_prices: pd.Series,
        dates: pd.DatetimeIndex,
    ) -> Dict[str, pd.Series]:
        """
        Build OHLCV with extreme realism.
        
        Ensures:
        - high >= max(open, close)
        - low <= min(open, close)
        - Realistic intraday ranges
        """
        n_days = len(close_prices)
        
        open_prices = np.zeros(n_days)
        high_prices = np.zeros(n_days)
        low_prices = np.zeros(n_days)
        
        for t in range(n_days):
            close = close_prices.iloc[t]
            
            # Generate open (previous close + small gap)
            if t == 0:
                open_p = close
            else:
                gap_factor = rng.uniform(0.995, 1.005)
                open_p = close_prices.iloc[t - 1] * gap_factor
            
            # Generate high/low with realistic ranges
            # High is typically 1-3% above max(open, close)
            # Low is typically 1-3% below min(open, close)
            max_price = max(open_p, close)
            min_price = min(open_p, close)
            
            high_range = rng.uniform(0.001, 0.03)  # 0.1% to 3%
            low_range = rng.uniform(0.001, 0.03)
            
            high_p = max_price * (1.0 + high_range)
            low_p = min_price * (1.0 - low_range)
            
            # Final validation
            high_p = max(high_p, max_price, close * 1.001)
            low_p = min(low_p, min_price, close * 0.999)
            
            open_prices[t] = open_p
            high_prices[t] = high_p
            low_prices[t] = low_p
        
        return {
            "open": pd.Series(open_prices, index=dates),
            "high": pd.Series(high_prices, index=dates),
            "low": pd.Series(low_prices, index=dates),
            "close": close_prices,
        }
    
    def _simulate_volumes_extreme(
        self,
        rng: np.random.Generator,
        dates: pd.DatetimeIndex,
        symbol: str,
    ) -> pd.Series:
        """
        Simulate realistic volumes using Gamma distribution.
        
        Process:
        1. Generate base volume (symbol-specific)
        2. Apply intraday noise
        3. Sample from Gamma distribution
        """
        multiplier = self.config.volume_base_multiplier.get(symbol, 10.0)
        base_volume = rng.uniform(
            self.config.volume_base_min,
            self.config.volume_base_max
        )
        
        n_days = len(dates)
        volumes = np.zeros(n_days)
        
        # Generate base volume series with trend
        base_series = np.full(n_days, base_volume * multiplier)
        
        # Add intraday noise (Gamma distribution)
        for t in range(n_days):
            gamma_sample = rng.gamma(
                self.config.volume_gamma_shape,
                self.config.volume_gamma_scale
            )
            volumes[t] = base_series[t] * gamma_sample
        
        # Ensure positive
        volumes = np.maximum(volumes, 100.0)
        
        return pd.Series(volumes, index=dates)
    
    def load_price_frame(self, config: PathAConfig) -> pd.DataFrame:
        """
        Generate extreme-realistic price frame.
        
        Format:
            index: date (DatetimeIndex)
            columns: MultiIndex (symbol, field)
        """
        rng = np.random.default_rng(self.config.seed)
        dates = self._build_date_index(config)
        symbols: Sequence[str] = config.universe
        
        # Step 1: Simulate prices using OU process
        close_prices_dict = {}
        for symbol in symbols:
            base_price = self.config.base_prices.get(symbol, 100.0)
            close_series = self._simulate_ou_process(rng, dates, base_price)
            
            # Apply price shocks
            close_series = self._apply_price_shocks(rng, close_series, dates)
            
            close_prices_dict[symbol] = close_series
        
        # Step 2: Build OHLC from close prices
        ohlcv_dict = {}
        for symbol in symbols:
            ohlcv_dict[symbol] = self._build_ohlcv_from_close_extreme(
                rng,
                close_prices_dict[symbol],
                dates
            )
        
        # Step 3: Simulate volumes
        volumes_dict = {}
        for symbol in symbols:
            volumes_dict[symbol] = self._simulate_volumes_extreme(
                rng,
                dates,
                symbol
            )
        
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
                    ohlcv_dict[symbol]["open"].loc[date],
                    ohlcv_dict[symbol]["high"].loc[date],
                    ohlcv_dict[symbol]["low"].loc[date],
                    ohlcv_dict[symbol]["close"].loc[date],
                    volumes_dict[symbol].loc[date],
                ])
            data_rows.append(row_data)
        
        columns = pd.MultiIndex.from_tuples(arrays, names=["symbol", "field"])
        price_frame = pd.DataFrame(data_rows, index=dates, columns=columns)
        
        return price_frame.astype(float)
    
    def load_feature_frame(self, config: PathAConfig) -> pd.DataFrame:
        """
        Generate comprehensive feature frame with extreme features.
        
        Features:
            - daily_return_1d
            - rolling_vol_5d, rolling_vol_20d
            - rolling_momentum_3d, 5d, 10d
            - ATR_14 (Average True Range)
            - rolling_skew, rolling_kurtosis
            - VWAP (Volume Weighted Average Price)
            - turnover_rate
        """
        price_frame = self.load_price_frame(config)
        dates = price_frame.index
        symbols: Sequence[str] = config.universe
        
        # Extract price fields
        if isinstance(price_frame.columns, pd.MultiIndex):
            close_cols = [(symbol, "close") for symbol in symbols]
            volume_cols = [(symbol, "volume") for symbol in symbols]
            open_cols = [(symbol, "open") for symbol in symbols]
            high_cols = [(symbol, "high") for symbol in symbols]
            low_cols = [(symbol, "low") for symbol in symbols]
            
            close_df = price_frame[close_cols]
            close_df.columns = list(symbols)
            volume_df = price_frame[volume_cols]
            volume_df.columns = list(symbols)
            open_df = price_frame[open_cols]
            open_df.columns = list(symbols)
            high_df = price_frame[high_cols]
            high_df.columns = list(symbols)
            low_df = price_frame[low_cols]
            low_df.columns = list(symbols)
        else:
            # Fallback
            close_cols = [f"{symbol}_close" for symbol in symbols]
            volume_cols = [f"{symbol}_volume" for symbol in symbols]
            open_cols = [f"{symbol}_open" for symbol in symbols]
            high_cols = [f"{symbol}_high" for symbol in symbols]
            low_cols = [f"{symbol}_low" for symbol in symbols]
            
            close_df = price_frame[close_cols]
            close_df.columns = list(symbols)
            volume_df = price_frame[volume_cols]
            volume_df.columns = list(symbols)
            open_df = price_frame[open_cols]
            open_df.columns = list(symbols)
            high_df = price_frame[high_cols]
            high_df.columns = list(symbols)
            low_df = price_frame[low_cols]
            low_df.columns = list(symbols)
        
        # Basic features
        returns = close_df.pct_change().fillna(0.0)
        rolling_vol_5d = returns.rolling(window=5, min_periods=1).std().fillna(0.0)
        rolling_vol_20d = returns.rolling(window=20, min_periods=1).std().fillna(0.0)
        
        # Momentum features
        momentum_3d = (close_df / close_df.shift(3) - 1).fillna(0.0)
        momentum_5d = (close_df / close_df.shift(5) - 1).fillna(0.0)
        momentum_10d = (close_df / close_df.shift(10) - 1).fillna(0.0)
        
        # ATR (Average True Range) 14
        true_range = pd.DataFrame(index=dates, columns=symbols)
        for symbol in symbols:
            high_low = high_df[symbol] - low_df[symbol]
            high_close = (high_df[symbol] - close_df[symbol].shift(1)).abs()
            low_close = (low_df[symbol] - close_df[symbol].shift(1)).abs()
            true_range[symbol] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        atr_14 = true_range.rolling(window=14, min_periods=1).mean().fillna(0.0)
        
        # Rolling skewness and kurtosis
        rolling_skew = returns.rolling(window=20, min_periods=5).skew().fillna(0.0)
        # pandas Rolling 沒有 kurtosis()，使用 kurt() 取得樣本峰度
        rolling_kurtosis = returns.rolling(window=20, min_periods=5).kurt().fillna(0.0)
        
        # VWAP (Volume Weighted Average Price) - 14-day
        vwap_14 = pd.DataFrame(index=dates, columns=symbols)
        for symbol in symbols:
            typical_price = (high_df[symbol] + low_df[symbol] + close_df[symbol]) / 3
            pv = typical_price * volume_df[symbol]
            vwap_14[symbol] = pv.rolling(window=14, min_periods=1).sum() / volume_df[symbol].rolling(window=14, min_periods=1).sum()
        vwap_14 = vwap_14.fillna(close_df)
        
        # Turnover rate
        turnover_rate = pd.DataFrame(index=dates, columns=symbols)
        for symbol in symbols:
            market_cap = self.config.market_cap_base.get(symbol, 100_000_000_000)
            turnover_rate[symbol] = volume_df[symbol] / market_cap
        turnover_rate = turnover_rate.fillna(0.0)
        
        # Build MultiIndex index
        multi_index = pd.MultiIndex.from_product(
            [dates, symbols], names=["date", "symbol"]
        )
        
        # Collect all feature data
        feature_data = {
            "daily_return_1d": [],
            "rolling_vol_5d": [],
            "rolling_vol_20d": [],
            "rolling_momentum_3d": [],
            "rolling_momentum_5d": [],
            "rolling_momentum_10d": [],
            "ATR_14": [],
            "rolling_skew": [],
            "rolling_kurtosis": [],
            "VWAP_14": [],
            "turnover_rate": [],
            # Price fields
            "close": [],
            "volume": [],
            "open": [],
            "high": [],
            "low": [],
        }
        
        for date in dates:
            for symbol in symbols:
                feature_data["daily_return_1d"].append(returns.loc[date, symbol])
                feature_data["rolling_vol_5d"].append(rolling_vol_5d.loc[date, symbol])
                feature_data["rolling_vol_20d"].append(rolling_vol_20d.loc[date, symbol])
                feature_data["rolling_momentum_3d"].append(momentum_3d.loc[date, symbol])
                feature_data["rolling_momentum_5d"].append(momentum_5d.loc[date, symbol])
                feature_data["rolling_momentum_10d"].append(momentum_10d.loc[date, symbol])
                feature_data["ATR_14"].append(atr_14.loc[date, symbol])
                feature_data["rolling_skew"].append(rolling_skew.loc[date, symbol])
                feature_data["rolling_kurtosis"].append(rolling_kurtosis.loc[date, symbol])
                feature_data["VWAP_14"].append(vwap_14.loc[date, symbol])
                feature_data["turnover_rate"].append(turnover_rate.loc[date, symbol])
                
                # Price fields
                feature_data["close"].append(close_df.loc[date, symbol])
                feature_data["volume"].append(volume_df.loc[date, symbol])
                feature_data["open"].append(open_df.loc[date, symbol])
                feature_data["high"].append(high_df.loc[date, symbol])
                feature_data["low"].append(low_df.loc[date, symbol])
        
        feature_frame = pd.DataFrame(feature_data, index=multi_index)
        
        return feature_frame

