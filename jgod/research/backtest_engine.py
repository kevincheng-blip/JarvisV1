"""
Backtest Engine: Deterministic backtesting with OHLCV + Fill Engine

v0.6.6-A7: Realism Foundation
v0.6.7-A7.5: Decoupled from feature computation (uses FeatureService)

Provides the only true research foundation for A8 Walk-Forward.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta

from jgod.data.market_data_service import MarketDataService, OHLCVSnapshot
from jgod.data.feature_service import FeatureService
from jgod.execution.virtual_ledger import VirtualLedger
from jgod.execution.order_engine import OrderGenerationEngine
from jgod.execution.fill_engine import FillEngine
from jgod.decision_v3.engine import DecisionEngineV3
from jgod.decision_v3.models import DecisionV3Result

logger = logging.getLogger(__name__)


@dataclass
class DailyLog:
    """Daily log entry for backtest."""
    date: str
    nav: float
    position: Dict
    realized_pnl: float
    unrealized_pnl: float
    ohlcv: Dict  # v0.6.7-A7.5: Added OHLCV snapshot
    features_summary: Dict  # v0.6.7-A7.5: Added features summary (key features only)
    decision: Dict
    order: Dict
    fill: Dict


@dataclass
class BacktestMetrics:
    """Backtest performance metrics."""
    total_return: float
    avg_daily_return: float
    max_drawdown: float
    sharpe_ratio: float  # Simplified (no risk-free rate)
    hit_rate: float  # Percentage of positive daily returns
    turnover: float  # Total notional traded / average NAV


@dataclass
class BacktestReport:
    """Complete backtest report."""
    symbol: str
    start_date: str
    end_date: str
    initial_cash: float
    final_nav: float
    metrics: BacktestMetrics
    daily_log: List[DailyLog]


@dataclass
class BacktestConfig:
    """Backtest configuration."""
    initial_cash: float = 1_000_000.0
    mode: str = "performance"  # "performance" or "signals"
    limit: int = 60  # Timeline limit for decision
    k: int = 5  # Top strategies
    slippage_rate_buy: float = 0.001  # 0.1%
    slippage_rate_sell: float = 0.0005  # 0.05%
    feature_version: str = "v1.0"  # v0.6.7-A7.5: Feature version
    feature_lookback: int = 60  # v0.6.7-A7.5: Feature lookback days


class BacktestEngine:
    """Engine for running deterministic backtests."""
    
    def __init__(self, use_mock_mdts: bool = False):
        """
        Initialize BacktestEngine.
        
        Args:
            use_mock_mdts: If True, use mock MDTS (for testing)
        """
        self.mdts = MarketDataService(use_mock=use_mock_mdts)
        self.feature_service = FeatureService(use_mock_mdts=use_mock_mdts)
        self.decision_engine = DecisionEngineV3()
    
    def run(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        config: Optional[BacktestConfig] = None,
    ) -> BacktestReport:
        """
        Run backtest for date range.
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            config: Backtest configuration
            
        Returns:
            BacktestReport
        """
        if config is None:
            config = BacktestConfig()
        
        # Initialize ledger
        ledger = VirtualLedger(symbol=symbol, cash=config.initial_cash)
        
        # Fetch OHLCV range
        ohlcv_snapshots = self.mdts.fetch_ohlcv_range(symbol, start_date, end_date)
        
        if not ohlcv_snapshots:
            logger.warning(f"No OHLCV data for {symbol} from {start_date} to {end_date}")
            # Return empty report
            return BacktestReport(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_cash=config.initial_cash,
                final_nav=config.initial_cash,
                metrics=BacktestMetrics(
                    total_return=0.0,
                    avg_daily_return=0.0,
                    max_drawdown=0.0,
                    sharpe_ratio=0.0,
                    hit_rate=0.0,
                    turnover=0.0,
                ),
                daily_log=[],
            )
        
        daily_logs = []
        nav_history = [config.initial_cash]
        daily_returns = []
        total_notional_traded = 0.0
        
        # Process each day
        for ohlcv in ohlcv_snapshots:
            date_str = ohlcv.date
            
            # Mark to market
            ledger.mark_to_market(symbol, ohlcv.close)
            
            # v0.6.7-A7.5: Get features from FeatureService (decoupled from computation)
            feature_schema = self.feature_service.get_feature(
                symbol=symbol,
                date=date_str,
                version=config.feature_version,
                lookback=config.feature_lookback,
            )
            
            # Extract features summary (key features only for daily_log)
            features_summary = {
                "SMA_5": feature_schema.features.get("SMA_5"),
                "SMA_20": feature_schema.features.get("SMA_20"),
                "RSI_14": feature_schema.features.get("RSI_14"),
                "RET_1D": feature_schema.features.get("RET_1D"),
            }
            
            # Compute decision
            # Note: DecisionEngineV3.decide() currently doesn't accept features parameter
            # Features are recorded in daily_log for A8 integration
            # In A8, DecisionEngineV3 will use features from FeatureService
            try:
                decision_result = self.decision_engine.decide(
                    symbol=symbol,
                    mode=config.mode,
                    limit=config.limit,
                    k=config.k,
                )
            except Exception as e:
                logger.warning(f"Failed to compute decision for {symbol} on {date_str}: {e}")
                # Use HOLD decision
                decision_result = DecisionV3Result(
                    symbol=symbol,
                    as_of_date=date.fromisoformat(date_str),
                    selected_primary_strategy="risk_off",
                    selected_secondary_strategies=[],
                    weights=[],
                    risk_plan=None,
                    confidence=0.0,
                    explain="決策計算失敗，使用 HOLD"
                )
            
            # Generate order
            order = OrderGenerationEngine.generate_orders(
                decision=decision_result,
                ledger=ledger,
                price=ohlcv.close,
            )
            
            # Execute fill
            fill = FillEngine.execute(
                order=order,
                ohlcv=ohlcv,
                slippage_rate_buy=config.slippage_rate_buy,
                slippage_rate_sell=config.slippage_rate_sell,
            )
            
            # Apply fill to ledger
            ledger.apply_fill(fill)
            
            # Mark to market again (after fill)
            ledger.mark_to_market(symbol, ohlcv.close)
            
            # Record daily log
            pos = ledger.positions.get(symbol)
            daily_logs.append(DailyLog(
                date=date_str,
                nav=ledger.nav,
                position={
                    "qty": pos.qty if pos else 0,
                    "avg_cost": pos.avg_cost if pos else 0.0,
                },
                realized_pnl=ledger.realized_pnl,
                unrealized_pnl=ledger.unrealized_pnl,
                ohlcv={
                    "open": ohlcv.open,
                    "high": ohlcv.high,
                    "low": ohlcv.low,
                    "close": ohlcv.close,
                    "volume": ohlcv.volume,
                },
                features_summary=features_summary,
                decision={
                    "primary_strategy": decision_result.selected_primary_strategy,
                    "position_scale": decision_result.risk_plan.position_scale if decision_result.risk_plan else 0.0,
                    "confidence": decision_result.confidence,
                },
                order={
                    "side": order.side,
                    "qty": order.qty,
                    "reason": order.reason,
                },
                fill={
                    "qty_executed": fill.qty_executed,
                    "fill_price": fill.fill_price,
                    "fee": fill.fee,
                    "tax": fill.tax,
                    "slippage": fill.slippage,
                },
            ))
            
            # Track metrics
            nav_history.append(ledger.nav)
            if len(nav_history) > 1:
                prev_nav = nav_history[-2]
                if prev_nav > 0:
                    daily_return = (ledger.nav - prev_nav) / prev_nav
                    daily_returns.append(daily_return)
            
            # Track turnover
            if fill.qty_executed > 0:
                total_notional_traded += fill.qty_executed * fill.fill_price
        
        # Calculate metrics
        metrics = self._calculate_metrics(
            initial_cash=config.initial_cash,
            final_nav=ledger.nav,
            nav_history=nav_history,
            daily_returns=daily_returns,
            total_notional_traded=total_notional_traded,
        )
        
        return BacktestReport(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_cash=config.initial_cash,
            final_nav=ledger.nav,
            metrics=metrics,
            daily_log=daily_logs,
        )
    
    def _calculate_metrics(
        self,
        initial_cash: float,
        final_nav: float,
        nav_history: List[float],
        daily_returns: List[float],
        total_notional_traded: float,
    ) -> BacktestMetrics:
        """Calculate backtest metrics."""
        # Total return
        total_return = (final_nav - initial_cash) / initial_cash if initial_cash > 0 else 0.0
        
        # Average daily return
        avg_daily_return = sum(daily_returns) / len(daily_returns) if daily_returns else 0.0
        
        # Max drawdown
        max_drawdown = self._calculate_max_drawdown(nav_history)
        
        # Sharpe ratio (simplified, no risk-free rate)
        if daily_returns:
            return_std = self._calculate_std(daily_returns)
            sharpe_ratio = (avg_daily_return / return_std) if return_std > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        
        # Hit rate
        hits = sum(1 for r in daily_returns if r > 0)
        hit_rate = hits / len(daily_returns) if daily_returns else 0.0
        
        # Turnover
        avg_nav = sum(nav_history) / len(nav_history) if nav_history else 1.0
        turnover = total_notional_traded / avg_nav if avg_nav > 0 else 0.0
        
        return BacktestMetrics(
            total_return=round(total_return, 4),
            avg_daily_return=round(avg_daily_return, 4),
            max_drawdown=round(max_drawdown, 4),
            sharpe_ratio=round(sharpe_ratio, 4),
            hit_rate=round(hit_rate, 4),
            turnover=round(turnover, 4),
        )
    
    def _calculate_max_drawdown(self, nav_history: List[float]) -> float:
        """Calculate maximum drawdown from NAV history."""
        if not nav_history:
            return 0.0
        
        peak = nav_history[0]
        max_dd = 0.0
        
        for nav in nav_history:
            if nav > peak:
                peak = nav
            dd = (peak - nav) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation (pure Python)."""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

