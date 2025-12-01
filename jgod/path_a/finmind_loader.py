"""
FinMind-based implementation of PathADataLoader for Path A v1.

This loader is responsible for:

- Fetching daily OHLCV data from a FinMind-like client

- Mapping FinMind fields to the Path A price_frame standard

- Building a basic feature_frame (daily_return_1d, rolling_vol_5d)

It does NOT:

- Perform any alpha / risk / optimizer logic

- Touch ErrorLearningEngine
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

import numpy as np
import pandas as pd

from jgod.path_a.path_a_schema import PathAConfig
from jgod.path_a.path_a_backtest import PathADataLoader


class FinMindClient(Protocol):
    """
    Minimal protocol for a FinMind-like client.
    
    This is intentionally small so that:
    - The real implementation can be backed by FinMind.DataLoader
    - Tests can inject a dummy client with the same method signature
    """
    
    def taiwan_stock_daily(
        self,
        stock_id: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        Expected columns (at least):
            - date
            - stock_id
            - open
            - max
            - min
            - close
            - Trading_Volume
        """
        ...


@dataclass
class FinMindPathADataLoader(PathADataLoader):
    """
    Path A data loader implementation backed by a FinMind client.
    
    Note:
    - This class does NOT manage API keys or rate limits; those should be
      configured on the `client` side.
    """
    
    client: FinMindClient
    
    # ------------------------------------------------------------------
    # PathADataLoader protocol implementation
    # ------------------------------------------------------------------
    
    def load_price_frame(self, config: PathAConfig) -> pd.DataFrame:
        """
        Load price data for the entire experiment window and universe
        using the FinMind client.
        
        Output format:
            index: date (DatetimeIndex)
            columns: MultiIndex (symbol, field)
                field in {"open", "high", "low", "close", "volume"}
        """
        universe: Sequence[str] = config.universe
        
        # build a unified date index from the union of all stock data
        all_frames: list[pd.DataFrame] = []
        
        for symbol in universe:
            stock_id = self._symbol_to_stock_id(symbol)
            df = self.client.taiwan_stock_daily(
                stock_id=stock_id,
                start_date=config.start_date,
                end_date=config.end_date,
            )
            
            if df.empty:
                continue
            
            # normalize columns
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"])
            
            # Map FinMind fields to Path A standard
            df = df.set_index("date")
            
            # Some FinMind variations may use slightly different column names;
            # we handle the common ones here and leave room for extension.
            col_map = {
                "open": "open",
                "max": "high",
                "min": "low",
                "close": "close",
                "Trading_Volume": "volume",
            }
            
            renamed = {}
            for src, dst in col_map.items():
                if src in df.columns:
                    renamed[dst] = df[src]
                else:
                    # if missing, fill with NaN
                    renamed[dst] = pd.Series(np.nan, index=df.index)
            
            symbol_cols = pd.concat(renamed, axis=1)
            symbol_cols.columns = pd.MultiIndex.from_product(
                [[symbol], symbol_cols.columns],
                names=["symbol", "field"],
            )
            
            all_frames.append(symbol_cols)
        
        if not all_frames:
            raise ValueError("FinMindPathADataLoader: no data loaded for any symbol")
        
        # Align all frames to a unified date index (outer join)
        price_frame = pd.concat(all_frames, axis=1, join="outer").sort_index()
        
        # Ensure date index is DatetimeIndex
        price_frame.index = pd.to_datetime(price_frame.index)
        
        return price_frame
    
    def load_feature_frame(self, config: PathAConfig) -> pd.DataFrame:
        """
        Build a basic feature frame from the price_frame.
        
        Features:
            - daily_return_1d
            - rolling_vol_5d
        
        Output format:
            index: MultiIndex (date, symbol)
            columns: feature names
        """
        price_frame = self.load_price_frame(config)
        symbols: Sequence[str] = config.universe
        
        # extract close prices into (date x symbol) DataFrame
        if isinstance(price_frame.columns, pd.MultiIndex):
            close_cols = [(symbol, "close") for symbol in symbols]
            close_df = price_frame[close_cols]
            close_df.columns = list(symbols)
        else:
            # fallback: wide format naming "2330.TW_close"
            close_cols = [f"{symbol}_close" for symbol in symbols]
            close_df = price_frame[close_cols]
            close_df.columns = list(symbols)
        
        close_df = close_df.sort_index()
        
        # daily returns and rolling vol
        returns = close_df.pct_change().fillna(0.0)
        rolling_vol = returns.rolling(window=5, min_periods=1).std().fillna(0.0)
        
        dates = close_df.index
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
    
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    
    @staticmethod
    def _symbol_to_stock_id(symbol: str) -> str:
        """
        Convert an internal symbol string (e.g. '2330.TW') to a FinMind stock_id
        (e.g. '2330').
        """
        return symbol.split(".")[0]

