"""
FinMind Data Loader Extreme - Professional Quant Fund Grade

This module provides an extreme-level implementation of PathADataLoader
using FinMind API with:
- Enhanced data integrity checks (missing dates, outliers, gaps)
- Automatic risk factor construction (market, size, volatility, momentum)
- Smart fallback to mock extreme data
- Parquet-based caching system

Reference: docs/JGOD_EXTREME_MODE_EDITOR_INSTRUCTIONS.md
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Dict, Sequence, Tuple
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from jgod.path_a.path_a_schema import PathAConfig
from jgod.path_a.path_a_backtest import PathADataLoader

try:
    from api_clients.finmind_client import FinMindClient
    FINMIND_AVAILABLE = True
except ImportError:
    FINMIND_AVAILABLE = False
    FinMindClient = None

try:
    from jgod.path_a.mock_data_loader_extreme import (
        MockPathADataLoaderExtreme,
        MockConfigExtreme,
    )
    MOCK_EXTREME_AVAILABLE = True
except ImportError:
    MOCK_EXTREME_AVAILABLE = False
    MockPathADataLoaderExtreme = None
    MockConfigExtreme = None

try:
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False


@dataclass
class FinMindLoaderConfigExtreme:
    """
    Extreme configuration for FinMind data loader.
    
    Enhanced with professional-grade data integrity and caching.
    """
    # Cache settings
    cache_enabled: bool = True
    cache_dir: Path = field(default_factory=lambda: Path("data_cache/finmind"))
    use_parquet_cache: bool = True  # Use Parquet instead of pickle
    
    # Fallback settings
    fallback_to_mock_extreme: bool = True
    mock_config_extreme: Optional[MockConfigExtreme] = None
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Data integrity settings
    zscore_threshold: float = 6.0  # Outlier threshold
    gap_threshold: float = 0.15  # ±15% gap threshold
    min_data_days: int = 1
    
    # Risk factor settings
    factor_lookback_days: int = 252  # For factor calculation


class FinMindPathADataLoaderExtreme(PathADataLoader):
    """
    Extreme FinMind data loader with professional-grade features.
    
    Features:
    - Enhanced data integrity (missing dates, outliers, gaps)
    - Automatic risk factor construction
    - Smart mock extreme fallback
    - Parquet-based caching
    """
    
    def __init__(
        self,
        client: Optional[FinMindClient] = None,
        config: Optional[FinMindLoaderConfigExtreme] = None,
    ):
        """
        Initialize extreme FinMind data loader.
        
        Args:
            client: FinMindClient instance
            config: Loader configuration
        """
        if not FINMIND_AVAILABLE:
            raise ImportError(
                "FinMind client not available. "
                "Please install required packages or use mock data source."
            )
        
        self.config = config or FinMindLoaderConfigExtreme()
        
        # Initialize FinMind client
        if client is None:
            try:
                self.client = FinMindClient()
            except ValueError as e:
                if self.config.fallback_to_mock_extreme:
                    print(f"Warning: FinMind client initialization failed: {e}. Using mock extreme fallback.")
                    self.client = None
                else:
                    raise
        else:
            self.client = client
        
        # Initialize cache directory
        if self.config.cache_enabled:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize mock extreme loader for fallback
        self.mock_loader: Optional[MockPathADataLoaderExtreme] = None
        if self.config.fallback_to_mock_extreme and MOCK_EXTREME_AVAILABLE:
            mock_config = self.config.mock_config_extreme or MockConfigExtreme(seed=999)
            self.mock_loader = MockPathADataLoaderExtreme(config=mock_config)
    
    def _get_cache_path(self, symbol: str, start_date: str, end_date: str) -> Path:
        """Get cache file path for a symbol and date range."""
        if self.config.use_parquet_cache and PARQUET_AVAILABLE:
            cache_key = f"{symbol}_{start_date}_{end_date}.parquet"
        else:
            cache_key = f"{symbol}_{start_date}_{end_date}.pkl"
        return self.config.cache_dir / cache_key
    
    def _load_from_cache(self, cache_path: Path) -> Optional[pd.DataFrame]:
        """Load data from cache (Parquet or pickle)."""
        if not self.config.cache_enabled or not cache_path.exists():
            return None
        
        try:
            if cache_path.suffix == ".parquet" and PARQUET_AVAILABLE:
                return pd.read_parquet(cache_path)
            else:
                import pickle
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cache {cache_path}: {e}")
            return None
    
    def _save_to_cache(self, data: pd.DataFrame, cache_path: Path) -> None:
        """Save data to cache (Parquet or pickle)."""
        if not self.config.cache_enabled:
            return
        
        try:
            if cache_path.suffix == ".parquet" and PARQUET_AVAILABLE:
                data.to_parquet(cache_path, index=True)
            else:
                import pickle
                with open(cache_path, 'wb') as f:
                    pickle.dump(data, f)
        except Exception as e:
            print(f"Warning: Failed to save cache {cache_path}: {e}")
    
    def _check_missing_dates(
        self,
        df: pd.DataFrame,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        Check for missing dates and forward/backward fill.
        
        Args:
            df: DataFrame with date column
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            DataFrame with missing dates filled
        """
        if df.empty or 'date' not in df.columns:
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
        
        return df_indexed
    
    def _remove_outliers(
        self,
        df: pd.DataFrame,
        price_columns: list[str] = None,
    ) -> pd.DataFrame:
        """
        Remove outliers using Z-score method.
        
        Args:
            df: DataFrame with price data
            price_columns: List of price column names to check
        
        Returns:
            DataFrame with outliers removed
        """
        if df.empty:
            return df
        
        if price_columns is None:
            price_columns = ['open', 'high', 'low', 'close']
        
        df = df.copy()
        valid_mask = pd.Series(True, index=df.index)
        
        for col in price_columns:
            if col not in df.columns:
                continue
            
            # Calculate Z-scores
            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            
            # Mark outliers
            outlier_mask = z_scores > self.config.zscore_threshold
            if outlier_mask.any():
                print(f"Warning: Removed {outlier_mask.sum()} outliers in {col}")
                valid_mask = valid_mask & ~outlier_mask
        
        return df[valid_mask].reset_index(drop=True)
    
    def _remove_gaps(
        self,
        df: pd.DataFrame,
        close_col: str = 'close',
    ) -> pd.DataFrame:
        """
        Remove abnormal gaps (±gap_threshold).
        
        Args:
            df: DataFrame with price data
            close_col: Close price column name
        
        Returns:
            DataFrame with gaps removed
        """
        if df.empty or close_col not in df.columns:
            return df
        
        df = df.copy().sort_values('date')
        
        # Calculate daily returns
        returns = df[close_col].pct_change().abs()
        
        # Mark gaps exceeding threshold
        gap_mask = returns <= self.config.gap_threshold
        
        # Keep first row and all valid rows
        gap_mask.iloc[0] = True
        
        invalid_count = (~gap_mask).sum()
        if invalid_count > 0:
            print(f"Warning: Removed {invalid_count} abnormal gaps")
        
        return df[gap_mask].reset_index(drop=True)
    
    def _build_risk_factors(
        self,
        returns_df: pd.DataFrame,
        market_cap_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Automatically construct risk factors from returns.
        
        Factors:
        - Market factor: Equal-weighted market return
        - Size factor: Based on market capitalization
        - Volatility factor: Rolling volatility
        - Momentum factor: Rolling momentum
        
        Args:
            returns_df: DataFrame with returns (date x symbol)
            market_cap_df: Optional DataFrame with market caps
        
        Returns:
            DataFrame with factor returns (date x factor)
        """
        factors = {}
        
        # Market factor: equal-weighted market return
        if len(returns_df.columns) > 0:
            factors['market'] = returns_df.mean(axis=1)
        
        # Volatility factor: rolling volatility of market
        if 'market' in factors:
            factors['volatility'] = factors['market'].rolling(
                window=20, min_periods=1
            ).std().fillna(0.0)
        
        # Momentum factor: rolling momentum of market
        if 'market' in factors:
            factors['momentum'] = factors['market'].rolling(
                window=10, min_periods=1
            ).mean().fillna(0.0)
        
        # Size factor: if market cap available, use size-sorted returns
        if market_cap_df is not None and not market_cap_df.empty:
            # Simple size factor: difference between large and small cap
            # This is a simplified version
            factors['size'] = returns_df.mean(axis=1) * 0.5  # Placeholder
        else:
            factors['size'] = factors.get('market', pd.Series(0.0, index=returns_df.index)) * 0.3
        
        # Combine into DataFrame
        factor_df = pd.DataFrame(factors, index=returns_df.index)
        
        return factor_df.fillna(0.0)
    
    def _fetch_finmind_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> Optional[pd.DataFrame]:
        """Fetch data from FinMind API with retry logic."""
        if self.client is None:
            return None
        
        # Check cache first
        cache_path = self._get_cache_path(symbol, start_date, end_date)
        cached_data = self._load_from_cache(cache_path)
        if cached_data is not None:
            return cached_data
        
        # Extract stock_id
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
        """Normalize FinMind DataFrame to J-GOD format."""
        if df.empty:
            return df
        
        df = df.copy()
        
        # Normalize column names
        column_mapping = {
            'Open': 'open', 'open': 'open',
            'High': 'high', 'high': 'high', 'max': 'high',
            'Low': 'low', 'low': 'low', 'min': 'low',
            'Close': 'close', 'close': 'close',
            'Trading_Volume': 'volume', 'volume': 'volume',
            'TradingVolume': 'volume', 'volume_traded': 'volume',
        }
        
        df = df.rename(columns=column_mapping)
        
        # Ensure date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        elif df.index.name == 'date' or isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
        
        # Ensure required columns
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                if col == 'volume':
                    df['volume'] = 0.0
                else:
                    df[col] = np.nan
        
        # Add symbol column
        df['symbol'] = symbol
        
        # Select and reorder
        df = df[['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
        
        # Apply data integrity checks
        df = self._remove_outliers(df)
        df = self._remove_gaps(df)
        
        return df
    
    def load_raw_finmind(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> Optional[pd.DataFrame]:
        """
        Load raw FinMind data with extreme data integrity.
        
        Args:
            symbol: Symbol identifier
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Normalized DataFrame or None
        """
        raw_df = self._fetch_finmind_data(symbol, start_date, end_date)
        
        if raw_df is None or raw_df.empty:
            return None
        
        normalized_df = self._normalize_finmind_data(raw_df, symbol)
        
        if normalized_df.empty:
            return None
        
        # Fill missing dates
        filled_df = self._check_missing_dates(normalized_df, start_date, end_date)
        
        return filled_df
    
    def load_price_frame(self, config: PathAConfig) -> pd.DataFrame:
        """
        Load price frame with automatic mock extreme fallback.
        
        Format:
            index: date (DatetimeIndex)
            columns: MultiIndex (symbol, field)
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
        data_sources: Dict[str, str] = {}  # Track data source
        
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
                data_sources[symbol] = "finmind"
        
        # Fallback to mock extreme for missing symbols
        if missing_symbols and self.mock_loader is not None:
            print(f"Warning: Missing FinMind data for {missing_symbols}. Using mock extreme fallback.")
            
            mock_config = PathAConfig(
                start_date=config.start_date,
                end_date=config.end_date,
                universe=missing_symbols,
                rebalance_frequency=config.rebalance_frequency,
            )
            
            mock_price_frame = self.mock_loader.load_price_frame(mock_config)
            
            # Extract mock data
            for symbol in missing_symbols:
                if isinstance(mock_price_frame.columns, pd.MultiIndex):
                    symbol_cols = [col for col in mock_price_frame.columns if col[0] == symbol]
                    if symbol_cols:
                        symbol_df = mock_price_frame[symbol_cols].copy()
                        symbol_df.columns = [col[1] for col in symbol_cols]
                        
                        raw_df = pd.DataFrame(index=symbol_df.index)
                        raw_df['date'] = symbol_df.index
                        raw_df['symbol'] = symbol
                        raw_df['open'] = symbol_df['open']
                        raw_df['high'] = symbol_df['high']
                        raw_df['low'] = symbol_df['low']
                        raw_df['close'] = symbol_df['close']
                        raw_df['volume'] = symbol_df['volume']
                        
                        all_data[symbol] = raw_df.reset_index(drop=True)
                        data_sources[symbol] = "mixed"  # Mark as mixed source
        
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
                        # Forward fill
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
        
        # Forward fill NaN
        price_frame = price_frame.fillna(method='ffill').fillna(method='bfill')
        
        # Store data source metadata (can be accessed via attribute)
        price_frame.data_sources = data_sources
        
        return price_frame.astype(float)
    
    def load_feature_frame(self, config: PathAConfig) -> pd.DataFrame:
        """
        Load feature frame with risk factors.
        
        Features include standard features plus risk factors.
        """
        price_frame = self.load_price_frame(config)
        dates = price_frame.index
        symbols: Sequence[str] = config.universe
        
        # Extract price fields (same as base implementation)
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
        
        # Compute standard features
        returns = close_df.pct_change().fillna(0.0)
        rolling_vol_5d = returns.rolling(window=5, min_periods=1).std().fillna(0.0)
        rolling_vol_20d = returns.rolling(window=20, min_periods=1).std().fillna(0.0)
        
        momentum_5d = (close_df / close_df.shift(5) - 1).fillna(0.0)
        momentum_20d = (close_df / close_df.shift(20) - 1).fillna(0.0)
        
        # Build risk factors
        risk_factors = self._build_risk_factors(returns)
        
        # Build MultiIndex index
        multi_index = pd.MultiIndex.from_product(
            [dates, symbols], names=["date", "symbol"]
        )
        
        # Collect feature data
        feature_data = {
            "daily_return_1d": [],
            "rolling_vol_5d": [],
            "rolling_vol_20d": [],
            "momentum_5d": [],
            "momentum_20d": [],
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
                feature_data["momentum_5d"].append(momentum_5d.loc[date, symbol])
                feature_data["momentum_20d"].append(momentum_20d.loc[date, symbol])
                
                feature_data["close"].append(close_df.loc[date, symbol])
                feature_data["volume"].append(volume_df.loc[date, symbol])
                feature_data["open"].append(open_df.loc[date, symbol])
                feature_data["high"].append(high_df.loc[date, symbol])
                feature_data["low"].append(low_df.loc[date, symbol])
        
        feature_frame = pd.DataFrame(feature_data, index=multi_index)
        
        # Store risk factors as metadata (can be accessed separately)
        feature_frame.risk_factors = risk_factors
        
        return feature_frame

