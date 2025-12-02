"""
FinMind Data Loader for Path A v1

This module provides a complete implementation of PathADataLoader protocol
using FinMind API as the data source. It includes:
- API caching to avoid redundant calls
- Fallback to mock data when FinMind data is missing
- Format conversion from FinMind to J-GOD internal format
- Comprehensive feature calculation

Reference: docs/JGOD_FINMIND_LOADER_STANDARD_v1.md
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Optional, Dict, Sequence
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from jgod.path_a.path_a_schema import PathAConfig
from jgod.path_a.path_a_backtest import PathADataLoader
from jgod.path_a.mock_data_loader import MockPathADataLoader, MockConfig

try:
    from api_clients.finmind_client import FinMindClient
    FINMIND_AVAILABLE = True
except ImportError:
    FINMIND_AVAILABLE = False
    FinMindClient = None


@dataclass
class FinMindLoaderConfig:
    """Configuration for FinMind data loader."""
    
    # Cache settings
    cache_enabled: bool = True
    cache_dir: Path = field(default_factory=lambda: Path("data_cache/finmind"))
    
    # Fallback settings
    fallback_to_mock: bool = True
    mock_config: Optional[MockConfig] = None
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    
    # Data validation
    min_data_days: int = 1  # Minimum days required
    max_price_change: float = 0.20  # Reject if price changes > 20% in one day


class FinMindPathADataLoader(PathADataLoader):
    """
    PathADataLoader implementation using FinMind API.
    
    Features:
    - API caching to reduce redundant calls
    - Automatic fallback to mock data when FinMind data is missing
    - Format conversion from FinMind to J-GOD internal format
    - Comprehensive feature calculation
    """
    
    def __init__(
        self,
        client: Optional[FinMindClient] = None,
        config: Optional[FinMindLoaderConfig] = None,
    ):
        """
        Initialize FinMind data loader.
        
        Args:
            client: FinMindClient instance. If None, will create one (requires FINMIND_TOKEN).
            config: Loader configuration. If None, uses default config.
        """
        if not FINMIND_AVAILABLE:
            raise ImportError(
                "FinMind client not available. "
                "Please install required packages or use mock data source."
            )
        
        self.config = config or FinMindLoaderConfig()
        
        # Initialize FinMind client
        if client is None:
            try:
                self.client = FinMindClient()
            except ValueError as e:
                if self.config.fallback_to_mock:
                    print(f"Warning: FinMind client initialization failed: {e}. Using mock fallback.")
                    self.client = None
                else:
                    raise
        else:
            self.client = client
        
        # Initialize cache directory
        if self.config.cache_enabled:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize mock loader for fallback
        self.mock_loader: Optional[MockPathADataLoader] = None
        if self.config.fallback_to_mock:
            mock_config = self.config.mock_config or MockConfig(seed=999)
            self.mock_loader = MockPathADataLoader(config=mock_config)
    
    def _get_cache_path(self, symbol: str, start_date: str, end_date: str) -> Path:
        """Get cache file path for a symbol and date range."""
        cache_key = f"{symbol}_{start_date}_{end_date}.pkl"
        return self.config.cache_dir / cache_key
    
    def _load_from_cache(self, cache_path: Path) -> Optional[pd.DataFrame]:
        """Load data from cache if available."""
        if not self.config.cache_enabled or not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cache {cache_path}: {e}")
            return None
    
    def _save_to_cache(self, data: pd.DataFrame, cache_path: Path) -> None:
        """Save data to cache."""
        if not self.config.cache_enabled:
            return
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Warning: Failed to save cache {cache_path}: {e}")
    
    def _fetch_finmind_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data from FinMind API with retry logic.
        
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
            Returns None if fetch fails after retries
        """
        if self.client is None:
            return None
        
        # Check cache first
        cache_path = self._get_cache_path(symbol, start_date, end_date)
        cached_data = self._load_from_cache(cache_path)
        if cached_data is not None:
            return cached_data
        
        # Extract stock_id from symbol (e.g., "2330.TW" -> "2330")
        stock_id = symbol.split('.')[0] if '.' in symbol else symbol
        
        # Fetch with retry
        for attempt in range(self.config.max_retries):
            try:
                df = self.client.get_stock_daily(
                    stock_id=stock_id,
                    start_date=start_date,
                    end_date=end_date,
                )
                
                if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                    if attempt < self.config.max_retries - 1:
                        continue
                    return None
                
                # Ensure DataFrame
                if not isinstance(df, pd.DataFrame):
                    df = pd.DataFrame(df)
                
                # Save to cache
                self._save_to_cache(df, cache_path)
                
                return df
                
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    import time
                    time.sleep(self.config.retry_delay)
                    continue
                else:
                    print(f"Warning: Failed to fetch FinMind data for {symbol}: {e}")
                    return None
        
        return None
    
    def _normalize_finmind_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Normalize FinMind DataFrame to J-GOD internal format.
        
        Required columns: date, open, high, low, close, volume, symbol
        
        Args:
            df: Raw FinMind DataFrame
            symbol: Symbol identifier (e.g., "2330.TW")
        
        Returns:
            Normalized DataFrame with required columns
        """
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Ensure date column exists and is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        elif df.index.name == 'date' or isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            if 'date' not in df.columns:
                df['date'] = df.index
        
        # Normalize column names (handle different FinMind formats)
        column_mapping = {
            'Open': 'open',
            'open': 'open',
            'High': 'high',
            'high': 'high',
            'max': 'high',
            'Low': 'low',
            'low': 'low',
            'min': 'low',
            'Close': 'close',
            'close': 'close',
            'Trading_Volume': 'volume',
            'volume': 'volume',
            'TradingVolume': 'volume',
            'volume_traded': 'volume',
        }
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                if col == 'volume':
                    # Try alternative volume column names
                    for alt in ['Trading_Volume', 'TradingVolume', 'volume_traded']:
                        if alt in df.columns:
                            df['volume'] = df[alt]
                            break
                    if 'volume' not in df.columns:
                        df['volume'] = 0.0
                else:
                    print(f"Warning: Missing column {col} for {symbol}. Filling with NaN.")
                    df[col] = np.nan
        
        # Add symbol column
        df['symbol'] = symbol
        
        # Select and reorder columns
        df = df[['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
        
        # Validate data
        df = self._validate_and_clean_data(df, symbol)
        
        return df
    
    def _validate_and_clean_data(
        self,
        df: pd.DataFrame,
        symbol: str,
    ) -> pd.DataFrame:
        """
        Validate and clean data, removing anomalies.
        
        - Remove rows with missing required fields
        - Remove rows with invalid price relationships
        - Remove rows with extreme price changes
        """
        # Remove rows with missing dates
        df = df.dropna(subset=['date'])
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Validate price relationships
        valid_mask = (
            (df['open'] > 0) &
            (df['high'] > 0) &
            (df['low'] > 0) &
            (df['close'] > 0) &
            (df['high'] >= df[['open', 'close']].max(axis=1)) &
            (df['low'] <= df[['open', 'close']].min(axis=1)) &
            (df['volume'] >= 0)
        )
        
        # Check for extreme price changes
        if len(df) > 1:
            price_change = df['close'].pct_change().abs()
            valid_mask = valid_mask & (price_change <= self.config.max_price_change)
        
        invalid_count = (~valid_mask).sum()
        if invalid_count > 0:
            print(f"Warning: Removed {invalid_count} invalid rows for {symbol}")
        
        df = df[valid_mask].copy()
        
        return df
    
    def _fill_missing_dates(
        self,
        df: pd.DataFrame,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        Fill missing dates with forward-filled data.
        
        Creates a complete date range and forward-fills missing values.
        """
        if df.empty:
            return df
        
        # Create full date range (business days)
        date_range = pd.date_range(
            start=start_date,
            end=end_date,
            freq='B'
        )
        
        # Set date as index
        df_indexed = df.set_index('date').reindex(date_range)
        
        # Forward fill missing values
        df_indexed = df_indexed.fillna(method='ffill')
        
        # Backward fill if still missing (for first few dates)
        df_indexed = df_indexed.fillna(method='bfill')
        
        # Reset index
        df_indexed = df_indexed.reset_index()
        df_indexed = df_indexed.rename(columns={'index': 'date'})
        
        # Restore symbol column if missing
        if 'symbol' not in df_indexed.columns and 'symbol' in df.columns:
            symbol = df['symbol'].iloc[0]
            df_indexed['symbol'] = symbol
        
        return df_indexed
    
    def load_raw_finmind(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> Optional[pd.DataFrame]:
        """
        Load raw FinMind data for a single symbol.
        
        This is a lower-level API that returns the normalized DataFrame
        before conversion to Path A format.
        
        Args:
            symbol: Symbol identifier (e.g., "2330.TW")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            DataFrame with columns: date, symbol, open, high, low, close, volume
            Returns None if data cannot be fetched
        """
        # Fetch from FinMind
        raw_df = self._fetch_finmind_data(symbol, start_date, end_date)
        
        if raw_df is None or raw_df.empty:
            return None
        
        # Normalize format
        normalized_df = self._normalize_finmind_data(raw_df, symbol)
        
        if normalized_df.empty:
            return None
        
        # Fill missing dates
        filled_df = self._fill_missing_dates(normalized_df, start_date, end_date)
        
        return filled_df
    
    def load_price_frame(self, config: PathAConfig) -> pd.DataFrame:
        """
        Load price frame for the entire universe.
        
        Format:
            index: date (DatetimeIndex)
            columns: MultiIndex (symbol, field)
                fields: open, high, low, close, volume
        
        If FinMind data is missing for any symbol, falls back to mock data.
        """
        dates = pd.date_range(
            start=config.start_date,
            end=config.end_date,
            freq='B'
        )
        
        symbols: Sequence[str] = config.universe
        
        # Collect data for all symbols
        all_data: Dict[str, pd.DataFrame] = {}
        missing_symbols: list[str] = []
        
        for symbol in symbols:
            raw_data = self.load_raw_finmind(
                symbol,
                config.start_date,
                config.end_date,
            )
            
            if raw_data is None or raw_data.empty:
                missing_symbols.append(symbol)
            else:
                all_data[symbol] = raw_data
        
        # Fallback to mock for missing symbols
        if missing_symbols and self.mock_loader is not None:
            print(f"Warning: Missing FinMind data for {missing_symbols}. Using mock fallback.")
            
            # Create a config with only missing symbols
            mock_config = PathAConfig(
                start_date=config.start_date,
                end_date=config.end_date,
                universe=missing_symbols,
                rebalance_frequency=config.rebalance_frequency,
            )
            
            mock_price_frame = self.mock_loader.load_price_frame(mock_config)
            
            # Extract mock data for missing symbols
            for symbol in missing_symbols:
                if isinstance(mock_price_frame.columns, pd.MultiIndex):
                    symbol_cols = [col for col in mock_price_frame.columns if col[0] == symbol]
                    if symbol_cols:
                        # Convert to raw format for merging
                        symbol_df = mock_price_frame[symbol_cols].copy()
                        symbol_df.columns = [col[1] for col in symbol_cols]
                        
                        # Create DataFrame with date and symbol
                        raw_df = pd.DataFrame(index=symbol_df.index)
                        raw_df['date'] = symbol_df.index
                        raw_df['symbol'] = symbol
                        raw_df['open'] = symbol_df['open']
                        raw_df['high'] = symbol_df['high']
                        raw_df['low'] = symbol_df['low']
                        raw_df['close'] = symbol_df['close']
                        raw_df['volume'] = symbol_df['volume']
                        
                        all_data[symbol] = raw_df.reset_index(drop=True)
        
        # Build MultiIndex DataFrame
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
        
        # Create unified date index
        for date in dates:
            row_data = []
            for symbol in symbols:
                if symbol in all_data:
                    symbol_df = all_data[symbol]
                    date_data = symbol_df[symbol_df['date'] == date]
                    
                    if not date_data.empty:
                        row_data.extend([
                            float(date_data['open'].iloc[0]),
                            float(date_data['high'].iloc[0]),
                            float(date_data['low'].iloc[0]),
                            float(date_data['close'].iloc[0]),
                            float(date_data['volume'].iloc[0]),
                        ])
                    else:
                        # Forward fill from previous date
                        prev_data = symbol_df[symbol_df['date'] < date]
                        if not prev_data.empty:
                            last_row = prev_data.iloc[-1]
                            row_data.extend([
                                float(last_row['open']),
                                float(last_row['high']),
                                float(last_row['low']),
                                float(last_row['close']),
                                float(last_row['volume']),
                            ])
                        else:
                            row_data.extend([np.nan] * 5)
                else:
                    row_data.extend([np.nan] * 5)
            
            data_rows.append(row_data)
        
        columns = pd.MultiIndex.from_tuples(arrays, names=["symbol", "field"])
        price_frame = pd.DataFrame(data_rows, index=dates, columns=columns)
        
        # Forward fill NaN values
        price_frame = price_frame.fillna(method='ffill').fillna(method='bfill')
        
        return price_frame.astype(float)
    
    def load_feature_frame(self, config: PathAConfig) -> pd.DataFrame:
        """
        Load feature frame for the entire universe.
        
        Features:
            - daily_return_1d: Daily return (pct_change)
            - rolling_vol_5d: 5-day rolling volatility
            - rolling_vol_20d: 20-day rolling volatility
            - momentum_5d: 5-day momentum
            - momentum_20d: 20-day momentum
            - turnover_rate: volume / market_cap (estimated)
        
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
            # Fallback for wide format
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
        
        # Compute features
        returns = close_df.pct_change().fillna(0.0)
        rolling_vol_5d = returns.rolling(window=5, min_periods=1).std().fillna(0.0)
        rolling_vol_20d = returns.rolling(window=20, min_periods=1).std().fillna(0.0)
        
        # Momentum
        momentum_5d = (close_df / close_df.shift(5) - 1).fillna(0.0)
        momentum_20d = (close_df / close_df.shift(20) - 1).fillna(0.0)
        
        # Turnover rate: volume / market_cap
        # Estimate market_cap from price and volume patterns
        turnover_rate = pd.DataFrame(index=dates, columns=symbols)
        for symbol in symbols:
            # Simple estimate: market_cap ≈ price * typical_volume * multiplier
            avg_price = close_df[symbol].mean()
            avg_volume = volume_df[symbol].mean()
            # Rough estimate for market cap (can be improved)
            estimated_market_cap = avg_price * avg_volume * 100  # Rough multiplier
            turnover_rate[symbol] = volume_df[symbol] / max(estimated_market_cap, 1.0)
        
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

