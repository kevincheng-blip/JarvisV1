"""
Path A v1 - Backtest Skeleton

This module defines a minimal, testable skeleton for running a
Path A experiment over a historical window.

The goal of v1 is **not** to implement all details, but to:
- Define the main control flow (data -> alpha -> risk -> optimizer -> portfolio)
- Provide clear extension points for data loading, feature building, and error handling
- Integrate with the existing AlphaEngine, RiskModel, Optimizer, and ErrorLearningEngine
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional, List

import numpy as np
import pandas as pd

from jgod.path_a.path_a_schema import (
    PathAConfig,
    PathABacktestResult,
    PathAPortfolioSnapshot,
)
# NOTE: We only import typing-level interfaces for these engines.
# Concrete implementations live in their own modules.
from jgod.alpha_engine.alpha_engine import AlphaEngine
from jgod.risk.risk_model import MultiFactorRiskModel
from jgod.optimizer.optimizer_core import OptimizerCore
from jgod.learning.error_learning_engine import ErrorLearningEngine


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# 價格欄位名稱（用於避免 feature_frame 和 price_frame 欄位重複）
PRICE_COLUMNS = ["close", "open", "high", "low", "volume"]


# ---------------------------------------------------------------------------
# Protocols for data loader & feature builder
# ---------------------------------------------------------------------------


class PathADataLoader(Protocol):
    """
    Interface for a Path A data loader.
    
    A concrete implementation (e.g. FinMind-based loader) should implement
    this protocol and provide all the required data within the experiment
    window defined by PathAConfig.
    """
    
    def load_price_frame(self, config: PathAConfig) -> pd.DataFrame:
        """
        Load price data for the entire experiment window and universe.
        
        Expected format (v1 suggestion):
            index: date
            columns: MultiIndex (symbol, field) or wide format with a naming convention.
        
        Required fields:
            - open, high, low, close, volume
        """
        ...
    
    def load_feature_frame(self, config: PathAConfig) -> pd.DataFrame:
        """
        Load or construct feature DataFrame for the entire experiment window.
        
        This should be aligned with the price_frame's index and symbol universe.
        
        The resulting DataFrame will be passed into AlphaEngine.
        """
        ...


class PathAErrorBridge(Protocol):
    """
    Interface for converting Path A outcomes into ErrorEvent objects
    consumable by ErrorLearningEngine.
    """
    
    def handle_prediction_outcome(
        self,
        date: pd.Timestamp,
        weights: pd.Series,
        realized_returns: pd.Series,
        expected_scores: pd.Series,
        error_engine: ErrorLearningEngine,
    ) -> None:
        """
        Given the portfolio decision and realized outcome for a date (or period),
        build appropriate ErrorEvent(s) and send them to the ErrorLearningEngine.
        
        Implementations may choose to aggregate or create one event per symbol,
        depending on how granular the analysis should be.
        """
        ...


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------


@dataclass
class PathARunContext:
    """
    Simple container for objects needed during a Path A run.
    
    This keeps the main function signature manageable and makes it easier
    to extend in the future (e.g. adding loggers).
    """
    
    config: PathAConfig
    data_loader: PathADataLoader
    alpha_engine: AlphaEngine
    risk_model: MultiFactorRiskModel
    optimizer: OptimizerCore
    error_engine: ErrorLearningEngine
    error_bridge: Optional[PathAErrorBridge] = None


def run_path_a_backtest(ctx: PathARunContext) -> PathABacktestResult:
    """
    Run a Path A experiment over the configured window.
    
    v1 GOAL:
    - Implement a simple, *daily* backtest loop with:
        - Monthly (or configurable) rebalancing
        - Buy at next day's open, mark-to-market at close
    - Call the ErrorBridge (if provided) after each realized period.
    
    NOTE:
    - This is intentionally a skeleton. Many parts are left as TODOs
      for future iterations.
    """
    
    config = ctx.config
    
    # ------------------------------------------------------------------
    # 1) Load data
    # ------------------------------------------------------------------
    price_frame = ctx.data_loader.load_price_frame(config=config)
    feature_frame = ctx.data_loader.load_feature_frame(config=config)
    
    # sanity checks (optional)
    # TODO: add more robust validation (align indices, missing data, etc.)
    if price_frame.empty:
        raise ValueError("price_frame is empty in Path A backtest")
    if feature_frame.empty:
        raise ValueError("feature_frame is empty in Path A backtest")
    
    # Align index and universe
    # For simplicity we assume:
    # - price_frame index: date
    # - price_frame columns: MultiIndex (symbol, field) or wide format
    # - feature_frame index: MultiIndex (date, symbol)
    all_dates = pd.to_datetime(price_frame.index.unique()).sort_values()
    
    # Build rebalance schedule
    rebalance_dates = _build_rebalance_schedule(all_dates, config)
    
    # Initialize NAV and state containers
    nav_series = pd.Series(index=all_dates, dtype=float)
    return_series = pd.Series(index=all_dates, dtype=float)
    portfolio_snapshots: list[PathAPortfolioSnapshot] = []
    
    current_nav = config.initial_nav
    current_weights = pd.Series(
        0.0, index=config.universe, dtype=float
    )  # start fully in cash
    
    # ------------------------------------------------------------------
    # 2) Main backtest loop
    # ------------------------------------------------------------------
    for i, current_date in enumerate(all_dates):
        # mark-to-market for existing positions using today's close price
        close_prices = _extract_price_for_date(
            price_frame, current_date, field="close", universe=config.universe
        )
        
        if i > 0:
            # compute daily portfolio return based on yesterday's weights
            prev_date = all_dates[i - 1]
            prev_close_prices = _extract_price_for_date(
                price_frame, prev_date, field="close", universe=config.universe
            )
            price_rel = close_prices / prev_close_prices.replace(0, np.nan)
            price_rel = price_rel.fillna(1.0)  # no price change if missing
            
            daily_ret = float((current_weights * (price_rel - 1.0)).sum())
            current_nav *= (1.0 + daily_ret)
            
            nav_series.at[current_date] = current_nav
            return_series.at[current_date] = daily_ret
        else:
            # first day: just set initial NAV
            nav_series.at[current_date] = current_nav
            return_series.at[current_date] = 0.0
        
        # Rebalance if today is a rebalance date
        if current_date in rebalance_dates:
            # ------------------------------------------------------------------
            # 2a) Prepare alpha inputs for AlphaEngine
            # ------------------------------------------------------------------
            # 使用 helper 準備 alpha input（合併 feature 和 price 資料）
            alpha_input = _prepare_alpha_input(
                feature_frame=feature_frame,
                price_frame=price_frame,
                current_date=current_date,
                universe=config.universe
            )
            
            try:
                # AlphaEngine 會自動偵測橫截面模式
                alpha_result = ctx.alpha_engine.compute_all(alpha_input)
                
                # Extract composite_alpha
                # 在橫截面模式下，alpha_result 的 index 應該是 symbol
                if isinstance(alpha_result, pd.DataFrame):
                    if 'composite_alpha' in alpha_result.columns:
                        composite_alpha = alpha_result['composite_alpha']
                    else:
                        # 如果沒有 composite_alpha 欄位，使用第一個欄位
                        composite_alpha = alpha_result.iloc[:, 0]
                elif isinstance(alpha_result, pd.Series):
                    composite_alpha = alpha_result
                else:
                    composite_alpha = pd.Series(0.0, index=config.universe)
                
                # 確保 composite_alpha 的 index 對齊 universe
                if isinstance(composite_alpha, pd.Series):
                    composite_alpha = composite_alpha.reindex(config.universe, fill_value=0.0)
                else:
                    composite_alpha = pd.Series(0.0, index=config.universe)
            except Exception as e:
                # Fallback: use zero alpha if computation fails
                print(f"Warning: AlphaEngine computation failed on {current_date}: {e}")
                composite_alpha = pd.Series(0.0, index=config.universe)
            
            # ------------------------------------------------------------------
            # 2b) Update risk model & build covariance matrix
            # ------------------------------------------------------------------
            # For v1, we assume the risk model has been pre-fitted or can update itself.
            # The risk model should already have the covariance matrix ready.
            #
            # TODO: Implement proper window selection and call risk_model.fit() if needed.
            # For now, we assume the risk_model is already fitted and can provide covariance.
            
            try:
                # 優先嘗試從 Risk Model 取得（如果已經 fit 且 symbols 對齊）
                risk_model_ready = (
                    hasattr(ctx.risk_model, 'symbols') and 
                    ctx.risk_model.symbols == list(config.universe)
                )
                
                if risk_model_ready:
                    cov_matrix = ctx.risk_model.get_covariance_matrix()
                    if cov_matrix.shape[0] == len(config.universe):
                        # Shape 正確，使用它
                        pass
                    else:
                        # Shape 不對，改用 sample covariance
                        cov_matrix = _compute_sample_covariance(
                            price_frame,
                            list(config.universe),
                            lookback_days=min(60, len(price_frame))
                        )
                else:
                    # Risk Model 還沒 fit 或 symbols 不對齊，從 price_frame 計算
                    cov_matrix = _compute_sample_covariance(
                        price_frame,
                        list(config.universe),
                        lookback_days=min(60, len(price_frame))
                    )
            except Exception as e:
                print(f"Warning: Failed to compute covariance matrix: {e}. Using identity matrix.")
                # 使用小的 identity matrix（而不是全 1）
                cov_matrix = np.eye(len(config.universe)) * 0.01
            
            # ------------------------------------------------------------------
            # 2c) Optimize portfolio weights
            # ------------------------------------------------------------------
            # Construct expected return vector mu from composite_alpha
            # Reindex to ensure alignment with universe
            mu = composite_alpha.reindex(config.universe).fillna(0.0)
            
            # Convert to pd.Series if not already
            if not isinstance(mu, pd.Series):
                mu = pd.Series(mu, index=config.universe)
            
            # OptimizerCore.optimize() requires:
            # - expected_returns: pd.Series
            # - risk_model: MultiFactorRiskModel
            # - factor_exposure: Optional[pd.DataFrame] (can be None)
            # - benchmark_weights: Optional[pd.Series] (can be None)
            # - sector_map: Optional[Dict[str, str]] (can be None)
            
            try:
                optimized = ctx.optimizer.optimize(
                    expected_returns=mu,
                    risk_model=ctx.risk_model,
                    factor_exposure=None,  # TODO: build factor exposure if available
                    benchmark_weights=None,  # TODO: load benchmark weights if configured
                    sector_map=None,  # TODO: build sector map if available
                )
                
                new_weights = optimized.weights.reindex(config.universe).fillna(0.0)
                
                # Ensure weights sum to 1 (normalize if needed)
                if new_weights.abs().sum() > 0:
                    new_weights = new_weights / new_weights.abs().sum()
                else:
                    new_weights = pd.Series(0.0, index=config.universe)
                
            except Exception as e:
                print(f"Warning: Optimizer failed on {current_date}: {e}. Using equal weights.")
                # Fallback: equal weights
                new_weights = pd.Series(1.0 / len(config.universe), index=config.universe)
            
            # ------------------------------------------------------------------
            # 2d) Record portfolio snapshot at current_date
            # ------------------------------------------------------------------
            # For simplicity, we assume the new weights apply starting *tomorrow*.
            snapshot = PathAPortfolioSnapshot(
                date=current_date,
                symbols=list(config.universe),
                weights=new_weights,
                nav=current_nav,
                portfolio_return=float(return_series.at[current_date]),
            )
            portfolio_snapshots.append(snapshot)
            
            # ------------------------------------------------------------------
            # 2e) Error bridge: compare expected vs realized (when possible)
            # ------------------------------------------------------------------
            if ctx.error_bridge is not None and i > 0:
                # We use yesterday's weights and today's realized returns
                # to construct an outcome event.
                realized_returns = price_rel - 1.0  # from earlier in the loop
                try:
                    ctx.error_bridge.handle_prediction_outcome(
                        date=current_date,
                        weights=current_weights,
                        realized_returns=realized_returns,
                        expected_scores=mu,
                        error_engine=ctx.error_engine,
                    )
                except Exception as e:
                    print(f"Warning: ErrorBridge failed on {current_date}: {e}")
            
            # Apply transaction costs (very simplified)
            turnover = (new_weights - current_weights).abs().sum()
            cost = turnover * (config.transaction_cost_bps / 1e4)
            current_nav *= (1.0 - cost)
            nav_series.at[current_date] = current_nav
            
            # Update current weights
            current_weights = new_weights
    
    # ----------------------------------------------------------------------
    # 3) Build result object
    # ----------------------------------------------------------------------
    result = PathABacktestResult(
        config=config,
        nav_series=nav_series,
        return_series=return_series,
        portfolio_snapshots=portfolio_snapshots,
        trades=None,  # TODO: implement trade bookkeeping if needed
        error_events=None,  # Error events are managed by ErrorLearningEngine
        summary_stats={},  # TODO: compute Sharpe, max drawdown, etc.
    )
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_rebalance_schedule(
    all_dates: pd.Index, config: PathAConfig
) -> list[pd.Timestamp]:
    """
    Build a list of rebalance dates based on the full trading calendar
    and the requested frequency in PathAConfig.
    
    v1 implementation:
    - If frequency == "M": pick the last trading day of each month
    - If frequency == "W": pick the last trading day of each week
    """
    dates = pd.to_datetime(all_dates).sort_values()
    
    if config.rebalance_frequency == "M":
        # group by year-month and take the last date in each group
        monthly = (
            pd.Series(1, index=dates)
            .groupby([dates.year, dates.month])
            .tail(1)
            .index.to_list()
        )
        return monthly
    
    if config.rebalance_frequency == "W":
        # group by ISO year-week and take the last date in each group
        week_index = dates.to_series()
        week_key = week_index.dt.strftime("%G-%V")
        weekly = week_index.groupby(week_key).tail(1).index.to_list()
        return weekly
    
    # fallback: rebalance every day
    return list(dates)


def _extract_price_for_date(
    price_frame: pd.DataFrame,
    date: pd.Timestamp,
    field: str,
    universe: list[str],
) -> pd.Series:
    """
    Helper for extracting a price field for a given date and universe.
    
    v1 assumes `price_frame` uses a column naming convention like:
        (symbol, field) as a MultiIndex
    or 'symbol_field' if using wide format.
    
    This helper should be adapted later once the actual data loader format
    is finalized.
    """
    if isinstance(price_frame.columns, pd.MultiIndex):
        cols = [(symbol, field) for symbol in universe]
        df_slice = price_frame.loc[date, cols]
        df_slice.index = universe
        return df_slice.astype(float)
    
    # wide format: assume columns like "2330_close"
    col_names = [f"{symbol}_{field}" for symbol in universe]
    df_slice = price_frame.loc[date, col_names]
    df_slice.index = universe
    return df_slice.astype(float)


def _prepare_alpha_input(
    feature_frame: pd.DataFrame,
    price_frame: pd.DataFrame,
    current_date: pd.Timestamp,
    universe: List[str]
) -> pd.DataFrame:
    """
    準備 AlphaEngine 的輸入資料
    
    將 feature_frame 和 price_frame 合併，產生包含所有必要欄位的 DataFrame
    
    Args:
        feature_frame: Feature frame with MultiIndex (date, symbol)
        price_frame: Price frame with index=date, columns=MultiIndex(symbol, field)
        current_date: 當前日期
        universe: 股票列表
    
    Returns:
        DataFrame with index=symbol, columns=所有 features + price fields
    """
    # 1. 從 feature_frame 提取該日期的 features
    if isinstance(feature_frame.index, pd.MultiIndex):
        date_mask = feature_frame.index.get_level_values(0) == current_date
        feature_slice = feature_frame.loc[date_mask].droplevel(0)  # drop date level
    else:
        feature_slice = feature_frame.loc[[current_date]]
    
    # 2. 從 price_frame 提取該日期的價格資料
    price_data = {}
    for symbol in universe:
        try:
            if isinstance(price_frame.columns, pd.MultiIndex):
                price_data[symbol] = {
                    'close': price_frame.loc[current_date, (symbol, 'close')],
                    'volume': price_frame.loc[current_date, (symbol, 'volume')],
                    'open': price_frame.loc[current_date, (symbol, 'open')],
                    'high': price_frame.loc[current_date, (symbol, 'high')],
                    'low': price_frame.loc[current_date, (symbol, 'low')],
                }
            else:
                # wide format fallback
                price_data[symbol] = {
                    'close': price_frame.loc[current_date, f'{symbol}_close'],
                    'volume': price_frame.loc[current_date, f'{symbol}_volume'],
                    'open': price_frame.loc[current_date, f'{symbol}_open'],
                    'high': price_frame.loc[current_date, f'{symbol}_high'],
                    'low': price_frame.loc[current_date, f'{symbol}_low'],
                }
        except (KeyError, IndexError):
            # 如果某個欄位不存在，使用 NaN
            price_data[symbol] = {
                'close': np.nan,
                'volume': np.nan,
                'open': np.nan,
                'high': np.nan,
                'low': np.nan,
            }
    
    # 3. 合併成單一 DataFrame
    price_df = pd.DataFrame(price_data).T
    price_df.index.name = None  # 移除 index name
    
    # 4. 合併 feature 和 price 資料
    if feature_slice.index.name is not None:
        feature_slice.index.name = None
    
    # 確保價格欄位只來自 price_df，避免 join 時欄位重疊
    overlap_price_cols = [c for c in feature_slice.columns if c in PRICE_COLUMNS]
    if overlap_price_cols:
        feature_slice = feature_slice.drop(columns=overlap_price_cols)
    
    # 確保 index 對齊，然後合併
    feature_slice = feature_slice.reindex(universe, fill_value=0.0)
    price_df = price_df.reindex(universe, fill_value=np.nan)
    
    # 使用 join 合併（outer join 確保所有股票都在結果中）
    alpha_input = feature_slice.join(price_df, how='outer')
    
    # 5. 確保所有 universe 的股票都在結果中
    alpha_input = alpha_input.reindex(universe, fill_value=0.0)
    
    # 6. 填充 NaN
    alpha_input = alpha_input.fillna(0.0)
    
    return alpha_input


def _compute_sample_covariance(
    price_frame: pd.DataFrame,
    universe: List[str],
    lookback_days: int = 60
) -> np.ndarray:
    """
    從 price_frame 計算 returns 和 covariance matrix
    
    Args:
        price_frame: Price frame with index=date, columns=MultiIndex(symbol, field)
        universe: 股票列表
        lookback_days: 使用的歷史天數
    
    Returns:
        Covariance matrix (n_symbols × n_symbols)，年化
    """
    # 1. 提取 close prices
    close_data = {}
    for symbol in universe:
        try:
            if isinstance(price_frame.columns, pd.MultiIndex):
                close_data[symbol] = price_frame[(symbol, 'close')]
            else:
                close_data[symbol] = price_frame[f'{symbol}_close']
        except KeyError:
            # 如果某個股票沒有資料，創建全 NaN 的 Series
            close_data[symbol] = pd.Series(np.nan, index=price_frame.index)
    
    close_df = pd.DataFrame(close_data)
    
    # 2. 使用最近 lookback_days 天
    if len(close_df) > lookback_days:
        recent_close = close_df.tail(lookback_days)
    else:
        recent_close = close_df
    
    # 3. 計算 returns
    returns = recent_close.pct_change().dropna()
    
    # 4. 如果資料不足，返回 identity matrix
    if len(returns) < 2:
        n = len(universe)
        return np.eye(n) * 0.01  # 小一點的 identity
    
    # 5. 確保所有 universe 的股票都有資料
    returns = returns.reindex(columns=universe, fill_value=0.0)
    
    # 6. 計算 covariance matrix（年化）
    cov_matrix = returns.cov().values * 252  # 年化
    
    # 7. 確保是對稱且正定
    cov_matrix = (cov_matrix + cov_matrix.T) / 2  # 確保對稱
    eigenvalues = np.linalg.eigvals(cov_matrix)
    if np.any(eigenvalues < 0):
        # 如果有負特徵值，調整
        cov_matrix = cov_matrix + np.eye(len(universe)) * 0.001
    
    return cov_matrix

