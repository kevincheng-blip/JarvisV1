"""Decision AB Test Runner

Core logic for running AB tests comparing RAW_ONLY vs DECISION_ON modes.
"""

import logging
from datetime import date
from typing import Dict, Any, Optional

from jgod.decision_ab.models import (
    DecisionAbExperimentConfig,
    DecisionAbResult,
    ArmResult,
    ArmMetrics,
)
from jgod.decision_ab.aggregator import create_ab_result
from jgod.decision_ab.storage import AbResultStorage
from jgod.decision.config import DecisionConfig
from jgod.path_a.path_a_engine_v1 import PathAEngineV1, BacktestResult

logger = logging.getLogger(__name__)


class DecisionAbRunnerV1:
    """Decision AB Test Runner v1
    
    Runs AB tests to compare RAW_ONLY vs DECISION_ON modes in Path A backtests.
    """
    
    def __init__(
        self,
        storage: Optional[AbResultStorage] = None,
        initial_capital: float = 1_000_000.0,
    ):
        """
        Initialize AB test runner
        
        Args:
            storage: Storage instance for saving results (optional)
            initial_capital: Initial capital for backtests
        """
        self.storage = storage or AbResultStorage()
        self.initial_capital = initial_capital
    
    def _convert_backtest_metrics_to_arm_metrics(
        self,
        backtest_result: BacktestResult,
    ) -> ArmMetrics:
        """Convert BacktestResult metrics to ArmMetrics
        
        Args:
            backtest_result: BacktestResult from Path A Engine
        
        Returns:
            ArmMetrics object
        """
        metrics = backtest_result.metrics
        
        # Calculate average trade return (simplified)
        num_trades = metrics.num_long_trades + metrics.num_short_trades
        avg_trade_return = metrics.total_return / num_trades if num_trades > 0 else 0.0
        
        # Calculate turnover (simplified: sum of all trade values / initial capital)
        # Trade value approximation: price * quantity for each trade
        total_trade_value = sum(abs(trade.price * trade.shares) for trade in backtest_result.trades)
        turnover = total_trade_value / backtest_result.initial_capital if backtest_result.initial_capital > 0 else 0.0
        
        return ArmMetrics(
            sharpe=metrics.sharpe_ratio,
            max_drawdown=metrics.max_drawdown,
            total_return=metrics.total_return,
            win_rate=metrics.win_rate,
            avg_trade_return=avg_trade_return,
            num_trades=num_trades,
            turnover=turnover,
            vol_annualized=metrics.annualized_volatility,
        )
    
    def _run_single_arm(
        self,
        experiment_config: DecisionAbExperimentConfig,
        mode: str,
        path_a_config: Dict[str, Any],
    ) -> ArmResult:
        """Run a single arm (mode) of the AB test
        
        Args:
            experiment_config: Experiment configuration
            mode: "RAW_ONLY" or "DECISION_ON"
            path_a_config: Path A configuration dict
        
        Returns:
            ArmResult for this mode
        """
        logger.info(f"Running arm: {mode} for experiment {experiment_config.experiment_id}")
        
        # For AB test, we need to control Decision Layer usage at a higher level
        # Currently, PathAEngineV1 uses Decision & Risk Engine v1 (not Decision Layer v1)
        # So we pass enable_llm and enable_doctrine as part of the config
        # These will be used by Decision Layer v1 integration (if available)
        
        # Note: PathAEngineV1's DecisionEngineV1 is actually Decision & Risk Engine v1
        # The Decision Layer v1 integration happens at a higher level in the prediction/ranking phase
        # For now, we pass these flags for future integration
        
        decision_config_dict = {}
        if mode == "RAW_ONLY":
            # Disable Decision Layer
            decision_config_dict.update({
                "enable_llm": False,
                "enable_doctrine": False,
                "use_final_score": False,  # Use raw_score instead of final_score
            })
        elif mode == "DECISION_ON":
            # Enable Decision Layer
            decision_config_dict.update({
                "enable_llm": True,
                "enable_doctrine": True,
                "use_final_score": True,  # Use final_score from Decision Layer v1
            })
        
        # Merge path_a_config with decision_config_dict
        full_config = {**path_a_config, **decision_config_dict}
        
        # Create Path A Engine with the config
        engine = PathAEngineV1(
            initial_capital=self.initial_capital,
            **full_config
        )
        
        # Run backtest
        backtest_result = engine.run_backtest(
            start_date=experiment_config.start_date,
            end_date=experiment_config.end_date,
        )
        
        # Convert metrics
        arm_metrics = self._convert_backtest_metrics_to_arm_metrics(backtest_result)
        
        # Create ArmResult
        arm_result = ArmResult(
            experiment_id=experiment_config.experiment_id,
            mode=mode,
            path_a_config_id=experiment_config.path_a_config_id,
            decision_config_id=experiment_config.decision_config_id,
            start_date=experiment_config.start_date,
            end_date=experiment_config.end_date,
            metrics=arm_metrics,
        )
        
        logger.info(
            f"Arm {mode} completed: Sharpe={arm_metrics.sharpe:.4f}, "
            f"MaxDD={arm_metrics.max_drawdown:.2%}, Return={arm_metrics.total_return:.2%}"
        )
        
        return arm_result
    
    def run_experiment(
        self,
        experiment_config: DecisionAbExperimentConfig,
        path_a_config: Optional[Dict[str, Any]] = None,
    ) -> DecisionAbResult:
        """Run a complete AB experiment
        
        Args:
            experiment_config: Experiment configuration
            path_a_config: Path A configuration dict (e.g., long_budget, short_budget)
                         If None, uses defaults
        
        Returns:
            DecisionAbResult with both arms' results
        """
        logger.info(f"Starting AB experiment: {experiment_config.experiment_id}")
        
        # Default Path A config
        if path_a_config is None:
            path_a_config = {
                "long_budget": 0.8,
                "short_budget": 0.2,
                "max_weight_per_symbol": 0.1,
            }
        
        # Run both arms
        raw_only_result = None
        decision_on_result = None
        
        if "RAW_ONLY" in experiment_config.run_modes:
            raw_only_result = self._run_single_arm(
                experiment_config,
                mode="RAW_ONLY",
                path_a_config=path_a_config,
            )
        
        if "DECISION_ON" in experiment_config.run_modes:
            decision_on_result = self._run_single_arm(
                experiment_config,
                mode="DECISION_ON",
                path_a_config=path_a_config,
            )
        
        # Ensure we have both results
        if raw_only_result is None or decision_on_result is None:
            raise ValueError(
                f"Both RAW_ONLY and DECISION_ON results are required. "
                f"Got: RAW_ONLY={raw_only_result is not None}, "
                f"DECISION_ON={decision_on_result is not None}"
            )
        
        # Aggregate results
        ab_result = create_ab_result(
            experiment_id=experiment_config.experiment_id,
            raw_only=raw_only_result,
            decision_on=decision_on_result,
        )
        
        # Save to storage
        self.storage.save(ab_result)
        
        logger.info(
            f"AB experiment completed: {experiment_config.experiment_id} | "
            f"Delta Sharpe: {ab_result.delta_sharpe:+.4f}, "
            f"Delta MaxDD: {ab_result.delta_max_drawdown:+.2%}, "
            f"Delta Return: {ab_result.delta_total_return:+.2%}"
        )
        
        return ab_result

