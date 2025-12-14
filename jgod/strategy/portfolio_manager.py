"""
Portfolio Manager: Multi-symbol coordination and allocation

v0.6.10-A10: Portfolio-level walkforward with capital allocation
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from jgod.strategy.models import PortfolioConfig, AllocationResult, PortfolioDailyLog
from jgod.research.walkforward_runner import WalkForwardRunner
from jgod.data.data_service_interface import DataServiceInterface
from jgod.data.data_service import DefaultDataService
from jgod.research.storage import save_portfolio_log
from jgod.execution.virtual_ledger import VirtualLedger

logger = logging.getLogger(__name__)


class PortfolioManager:
    """
    Portfolio Manager: Coordinates multiple WalkForwardRunners.
    
    v0.6.10-A10: Multi-symbol portfolio walkforward with allocation.
    """
    
    def __init__(
        self,
        data_service: Optional[DataServiceInterface] = None,
        *,
        portfolio_autopilot_enabled: bool = False,
        portfolio_time_sync_check_enabled: bool = True,
        portfolio_parallel_enabled: bool = False,
    ):
        """
        Initialize PortfolioManager.
        
        Args:
            data_service: DataServiceInterface (if None, creates DefaultDataService)
            portfolio_autopilot_enabled: Enable autopilot for portfolio
            portfolio_time_sync_check_enabled: Enable time sync check (default True)
            portfolio_parallel_enabled: Enable parallel execution (default False, conservative)
        """
        if data_service is None:
            self.data_service = DefaultDataService(use_mock_mdts=False)
        else:
            self.data_service = data_service
        
        self.portfolio_autopilot_enabled = portfolio_autopilot_enabled
        self.portfolio_time_sync_check_enabled = portfolio_time_sync_check_enabled
        self.portfolio_parallel_enabled = portfolio_parallel_enabled
        
        # Runner instances (created per symbol)
        self.runners: Dict[str, WalkForwardRunner] = {}
        # Ledger instances (created per symbol)
        self.ledgers: Dict[str, VirtualLedger] = {}
    
    def allocate_capital(
        self,
        config: PortfolioConfig,
    ) -> AllocationResult:
        """
        Allocate capital across symbols.
        
        Args:
            config: PortfolioConfig
            
        Returns:
            AllocationResult
        """
        symbols = config.symbols
        total_cash = config.initial_cash_total
        n_symbols = len(symbols)
        
        if n_symbols == 0:
            return AllocationResult(
                per_symbol_cash={},
                weights={},
                method=config.allocation_mode,
                notes="No symbols provided",
            )
        
        if config.allocation_mode == "equal_weight":
            # Equal weight: each symbol gets total / N
            cash_per_symbol = total_cash / n_symbols
            weight_per_symbol = 1.0 / n_symbols
            
            per_symbol_cash = {symbol: cash_per_symbol for symbol in symbols}
            weights = {symbol: weight_per_symbol for symbol in symbols}
            
            return AllocationResult(
                per_symbol_cash=per_symbol_cash,
                weights=weights,
                method="equal_weight",
                notes=f"Equal weight allocation: {cash_per_symbol:.2f} per symbol",
            )
        
        elif config.allocation_mode == "vol_parity":
            # Volatility parity: weight ∝ 1/vol, normalized
            volatilities = {}
            
            # Calculate volatility for each symbol
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=config.vol_lookback)).strftime("%Y-%m-%d")
            
            for symbol in symbols:
                try:
                    # Get OHLCV range for volatility calculation
                    ohlcv_list = []
                    trading_dates = self.data_service.get_trading_dates(start_date, end_date)
                    
                    for date in trading_dates[-config.vol_lookback:]:  # Last N days
                        ohlcv = self.data_service.get_ohlcv(symbol, date)
                        if ohlcv and ohlcv.get("close"):
                            ohlcv_list.append(ohlcv["close"])
                    
                    if len(ohlcv_list) < 2:
                        # Fallback: use default volatility
                        volatilities[symbol] = 0.02  # 2% default
                        continue
                    
                    # Calculate daily returns
                    returns = []
                    for i in range(1, len(ohlcv_list)):
                        if ohlcv_list[i-1] > 0:
                            ret = (ohlcv_list[i] - ohlcv_list[i-1]) / ohlcv_list[i-1]
                            returns.append(ret)
                    
                    if not returns:
                        volatilities[symbol] = 0.02
                        continue
                    
                    # Calculate standard deviation (volatility)
                    mean_return = sum(returns) / len(returns)
                    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
                    vol = variance ** 0.5
                    
                    # Avoid division by zero
                    volatilities[symbol] = max(vol, 0.001)
                except Exception as e:
                    logger.warning(f"Failed to calculate volatility for {symbol}: {e}")
                    volatilities[symbol] = 0.02  # Default volatility
            
            # Calculate inverse volatility weights
            inv_vol_weights = {symbol: 1.0 / vol for symbol, vol in volatilities.items()}
            total_inv_vol = sum(inv_vol_weights.values())
            
            # Normalize weights
            weights = {symbol: w / total_inv_vol for symbol, w in inv_vol_weights.items()}
            
            # Allocate cash based on weights
            per_symbol_cash = {symbol: total_cash * weight for symbol, weight in weights.items()}
            
            return AllocationResult(
                per_symbol_cash=per_symbol_cash,
                weights=weights,
                method="vol_parity",
                notes=f"Volatility parity allocation (lookback={config.vol_lookback} days)",
            )
        
        else:
            # Unknown mode, fallback to equal weight
            cash_per_symbol = total_cash / n_symbols
            weight_per_symbol = 1.0 / n_symbols
            
            return AllocationResult(
                per_symbol_cash={symbol: cash_per_symbol for symbol in symbols},
                weights={symbol: weight_per_symbol for symbol in symbols},
                method="equal_weight",
                notes=f"Unknown allocation mode {config.allocation_mode}, using equal weight",
            )
    
    def run_portfolio_walkforward(
        self,
        config: PortfolioConfig,
        start_date: str,
        end_date: str,
    ) -> List[PortfolioDailyLog]:
        """
        Run portfolio walkforward for date range.
        
        Args:
            config: PortfolioConfig
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of PortfolioDailyLog entries
        """
        # Step 1: Allocate capital
        allocation = self.allocate_capital(config)
        
        # Step 2: Initialize runners and ledgers for each symbol
        for symbol in config.symbols:
            cash = allocation.per_symbol_cash.get(symbol, 0.0)
            
            # Create runner with shared data_service
            runner = WalkForwardRunner(
                use_mock_mdts=False,
                autopilot_enabled=self.portfolio_autopilot_enabled,
                autopilot_apply_only_when_status_auto=True,
                async_learning_enabled=True,
            )
            # Inject data_service (requires modification to WalkForwardRunner)
            runner.data_service = self.data_service
            
            # Create ledger with allocated cash
            ledger = VirtualLedger(symbol=symbol, cash=cash)
            
            self.runners[symbol] = runner
            self.ledgers[symbol] = ledger
        
        # Step 3: Get trading dates
        trading_dates = self.data_service.get_trading_dates(start_date, end_date)
        
        portfolio_logs = []
        
        # Step 4: Process each date
        for date_str in trading_dates:
            # Time sync check: ensure all runners use same date
            if self.portfolio_time_sync_check_enabled:
                for symbol, runner in self.runners.items():
                    # Check runner's current date (if available)
                    # For now, we'll pass date explicitly to daily_cycle
                    pass  # Time sync is enforced by passing same date to all runners
            
            # Step 5: Run daily cycle for each symbol (sequential for now)
            symbol_logs = {}
            
            for symbol in config.symbols:
                runner = self.runners[symbol]
                ledger = self.ledgers[symbol]
                
                try:
                    # Run daily cycle
                    daily_result = runner.run_daily_cycle(
                        symbol=symbol,
                        date_str=date_str,
                        doctrine_version=config.doctrine_version,
                        feature_version=config.feature_version,
                        feature_lookback=config.feature_lookback,
                    )
                    
                    # Update ledger from daily result
                    # (Runner should update ledger internally, but we track it here)
                    symbol_logs[symbol] = daily_result
                except Exception as e:
                    logger.error(f"Failed to run daily cycle for {symbol} on {date_str}: {e}", exc_info=True)
                    symbol_logs[symbol] = {
                        "symbol": symbol,
                        "date": date_str,
                        "error": str(e),
                        "nav": ledger.nav if ledger else 0.0,
                    }
            
            # Step 6: Aggregate portfolio-level metrics
            portfolio_nav = sum(
                symbol_logs.get(symbol, {}).get("nav", 0.0)
                for symbol in config.symbols
            )
            
            portfolio_cash = sum(
                self.ledgers.get(symbol, VirtualLedger(symbol=symbol, cash=0.0)).cash
                for symbol in config.symbols
            )
            
            portfolio_pnl_realized = sum(
                self.ledgers.get(symbol, VirtualLedger(symbol=symbol, cash=0.0)).realized_pnl
                for symbol in config.symbols
            )
            
            portfolio_pnl_unrealized = sum(
                self.ledgers.get(symbol, VirtualLedger(symbol=symbol, cash=0.0)).unrealized_pnl
                for symbol in config.symbols
            )
            
            per_symbol_nav = {
                symbol: symbol_logs.get(symbol, {}).get("nav", 0.0)
                for symbol in config.symbols
            }
            
            per_symbol_pnl = {
                symbol: (
                    self.ledgers.get(symbol, VirtualLedger(symbol=symbol, cash=0.0)).realized_pnl +
                    self.ledgers.get(symbol, VirtualLedger(symbol=symbol, cash=0.0)).unrealized_pnl
                )
                for symbol in config.symbols
            }
            
            per_symbol_cash = {
                symbol: self.ledgers.get(symbol, VirtualLedger(symbol=symbol, cash=0.0)).cash
                for symbol in config.symbols
            }
            
            # Step 7: Create portfolio daily log
            portfolio_log = PortfolioDailyLog(
                date=date_str,
                portfolio_nav=portfolio_nav,
                portfolio_cash=portfolio_cash,
                portfolio_pnl_realized=portfolio_pnl_realized,
                portfolio_pnl_unrealized=portfolio_pnl_unrealized,
                per_symbol_nav=per_symbol_nav,
                per_symbol_pnl=per_symbol_pnl,
                per_symbol_cash=per_symbol_cash,
                notes=f"Portfolio walkforward: {len(config.symbols)} symbols",
            )
            
            # Step 8: Save portfolio log
            save_portfolio_log({
                "date": portfolio_log.date,
                "portfolio_nav": portfolio_log.portfolio_nav,
                "portfolio_cash": portfolio_log.portfolio_cash,
                "portfolio_pnl_realized": portfolio_log.portfolio_pnl_realized,
                "portfolio_pnl_unrealized": portfolio_log.portfolio_pnl_unrealized,
                "per_symbol_nav": portfolio_log.per_symbol_nav,
                "per_symbol_pnl": portfolio_log.per_symbol_pnl,
                "per_symbol_cash": portfolio_log.per_symbol_cash,
                "notes": portfolio_log.notes,
            })
            
            portfolio_logs.append(portfolio_log)
        
        return portfolio_logs

