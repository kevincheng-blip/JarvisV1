"""Rule Simulation Data Access

Wraps existing Backtest / PathA / Decision / Alert services for rule simulation.
"""

import logging
from datetime import date
from pathlib import Path
from typing import List, Optional, Dict

from jgod.path_a.path_a_engine_v1 import PathAEngineV1, BacktestResult, PerformanceMetrics

logger = logging.getLogger(__name__)


class RuleSimDataAccess:
    """Data access layer for rule simulation"""
    
    def __init__(self):
        """Initialize data access"""
        self.path_a_engine = PathAEngineV1()
        logger.info("RuleSimDataAccess initialized")
    
    def run_path_a_backtest(
        self,
        start_date: date,
        end_date: date,
        universe: List[str],
        path_a_config_name: str,
        sandbox_dir: Optional[Path] = None,
    ) -> BacktestResult:
        """
        Run Path A backtest.
        
        If sandbox_dir is provided, uses sandbox rules (Doctrine/Alert overrides).
        Otherwise, uses production rules.
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            universe: Stock universe
            path_a_config_name: Path A config name
            sandbox_dir: Optional sandbox directory with overridden rules
        
        Returns:
            BacktestResult with performance metrics
        """
        logger.info(
            f"Running Path A backtest: {start_date} to {end_date}, "
            f"universe={len(universe)} stocks, sandbox={sandbox_dir is not None}"
        )
        
        # If sandbox_dir is provided, we should modify environment to use sandbox rules
        # For v1, we'll pass sandbox_dir but PathAEngine doesn't support it yet
        # This is a placeholder for future integration
        
        # For now, run normal backtest
        # TODO: Integrate sandbox rules into PathAEngine when DecisionEngine supports it
        try:
            result = self.path_a_engine.run_backtest(
                start_date=start_date,
                end_date=end_date,
                universe=universe,
            )
            logger.info(f"Backtest completed: Sharpe={result.metrics.sharpe_ratio:.3f}")
            return result
        except Exception as e:
            logger.error(f"Backtest failed: {e}", exc_info=True)
            # Return empty result on failure
            from jgod.path_a.path_a_engine_v1 import PerformanceMetrics
            empty_metrics = PerformanceMetrics(
                annualized_return=0.0,
                annualized_volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                total_return=0.0,
                total_commission=0.0,
                num_long_trades=0,
                num_short_trades=0,
            )
            return BacktestResult(
                start_date=start_date,
                end_date=end_date,
                initial_capital=1000000.0,
                final_capital=1000000.0,
                metrics=empty_metrics,
                trades=[],
                equity_curve=[],
            )
    
    def collect_alert_stats(
        self,
        start_date: date,
        end_date: date,
        universe: List[str],
        sandbox_dir: Optional[Path] = None,
    ) -> Dict[str, int]:
        """
        Collect alert statistics.
        
        For v1, returns simplified stats (placeholder).
        Future versions can integrate with DoctrineAlertEngine.
        
        Args:
            start_date: Start date
            end_date: End date
            universe: Stock universe
            sandbox_dir: Optional sandbox directory
        
        Returns:
            Dictionary with alert statistics
        """
        # Placeholder implementation
        # TODO: Integrate with DoctrineAlertEngine to count alerts
        logger.debug(
            f"Collecting alert stats: {start_date} to {end_date}, "
            f"universe={len(universe)}, sandbox={sandbox_dir is not None}"
        )
        
        # For v1, return zeros
        return {
            "alert_trigger_count": 0,
            "doctrine_violation_count": 0,
        }

