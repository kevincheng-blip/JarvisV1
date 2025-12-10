"""Decision AB Test Runner

Core logic for running AB tests comparing RAW_ONLY vs DECISION_ON modes.
"""

import logging
import uuid
from datetime import date, datetime
from typing import Dict, Any, Optional

from jgod.decision_ab.models import (
    DecisionAbExperimentConfig,
    DecisionAbResult,
    ArmResult,
    ArmMetrics,
    DecisionABTestReport,
    ArmBacktestResult,
)
from jgod.decision_ab.aggregator import create_ab_result
from jgod.decision_ab.storage import AbResultStorage, DecisionAbStorageV1
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
    
    def _backtest_result_to_arm_backtest_result(
        self,
        backtest_result: BacktestResult,
        version: str,
    ) -> ArmBacktestResult:
        """Convert BacktestResult to ArmBacktestResult"""
        metrics = backtest_result.metrics
        
        # Convert equity curve format
        equity_curve = [
            {
                "date": point["date"],
                "equity": point["equity_value"],
            }
            for point in backtest_result.daily_equity_curve
        ]
        
        return ArmBacktestResult(
            version=version,
            sharpe_ratio=metrics.sharpe_ratio,
            max_drawdown=metrics.max_drawdown,
            total_return=metrics.total_return,
            volatility=metrics.annualized_volatility,
            win_rate=metrics.win_rate,
            turnover=self._calculate_turnover(backtest_result),
            equity_curve=equity_curve,
        )
    
    def _calculate_turnover(self, backtest_result: BacktestResult) -> float:
        """Calculate turnover from backtest result"""
        if backtest_result.initial_capital <= 0:
            return 0.0
        
        total_trade_value = sum(
            abs(trade.price * trade.shares) for trade in backtest_result.trades
        )
        
        # Annualized turnover
        trading_days = len(backtest_result.daily_equity_curve)
        if trading_days == 0:
            return 0.0
        
        # Simple turnover: total trade value / initial capital
        # Annualized by multiplying by (252 / trading_days)
        annualization_factor = 252.0 / trading_days if trading_days > 0 else 1.0
        turnover = (total_trade_value / backtest_result.initial_capital) * annualization_factor
        
        return turnover
    
    def _calculate_recommendation(
        self,
        baseline: ArmBacktestResult,
        variant: ArmBacktestResult,
    ) -> str:
        """
        計算推薦標籤
        
        Logic:
        - V2_PREFERRED: variant.sharpe >= baseline.sharpe + 0.1 且 variant.max_drawdown <= baseline.max_drawdown
        - V1_PREFERRED: variant.sharpe <= baseline.sharpe - 0.1
        - NO_SIGNIFICANT_CHANGE: 其他情況
        """
        sharpe_diff = variant.sharpe_ratio - baseline.sharpe_ratio
        maxdd_diff = variant.max_drawdown - baseline.max_drawdown  # max_drawdown is negative, so diff > 0 means variant is better
        
        # V2 明顯優於 V1
        if sharpe_diff >= 0.1 and maxdd_diff >= 0:  # variant.max_drawdown <= baseline.max_drawdown (風險不惡化)
            return "V2_PREFERRED"
        
        # V1 明顯優於 V2
        if sharpe_diff <= -0.1:
            return "V1_PREFERRED"
        
        # 無顯著差異
        return "NO_SIGNIFICANT_CHANGE"
    
    def run_decision_v1_vs_v2(
        self,
        start_date: date,
        end_date: date,
        capital: float,
        path_a_config_name: str,
        note: Optional[str] = None,
    ) -> DecisionABTestReport:
        """
        執行 V1 vs V2 的 AB Test 回測
        
        Args:
            start_date: 回測開始日期
            end_date: 回測結束日期
            capital: 初始資金
            path_a_config_name: Path A 配置名稱（用於記錄，實際配置從 decision_config 取得）
            note: 備註
        
        Returns:
            DecisionABTestReport
        """
        experiment_id = str(uuid.uuid4())
        logger.info(f"Starting V1 vs V2 AB Test: {experiment_id}")
        
        # Parse path_a_config_name to extract config params
        # For now, use default config if path_a_config_name is not a valid dict
        path_a_config = {
            "long_budget": 0.8,
            "short_budget": 0.2,
            "max_weight_per_symbol": 0.1,
        }
        
        # For V1 vs V2 comparison, we need to integrate Decision Layer v1/v2
        # Currently PathAEngineV1 uses Decision & Risk Engine v1 directly
        # We'll need to create a wrapper or modify PathAEngineV1 to support decision_version
        # For now, we'll use a simplified approach where we pass decision_version in config
        # and PathAEngineV1 will need to be modified to respect this (future work)
        
        # TODO: Integrate Decision Layer v1/v2 selection into PathAEngineV1
        # For now, we'll create engines with version flags in config
        
        # Run baseline (V1)
        logger.info(f"Running baseline (V1) backtest...")
        baseline_config = {
            **path_a_config,
            "decision_version": "v1",  # Signal to use Decision Layer v1
        }
        baseline_engine = PathAEngineV1(
            initial_capital=capital,
            **baseline_config
        )
        baseline_backtest = baseline_engine.run_backtest(
            start_date=start_date,
            end_date=end_date,
        )
        baseline_arm = self._backtest_result_to_arm_backtest_result(
            baseline_backtest,
            version="v1",
        )
        
        # Run variant (V2)
        logger.info(f"Running variant (V2) backtest...")
        variant_config = {
            **path_a_config,
            "decision_version": "v2",  # Signal to use Decision Layer v2
        }
        variant_engine = PathAEngineV1(
            initial_capital=capital,
            **variant_config
        )
        variant_backtest = variant_engine.run_backtest(
            start_date=start_date,
            end_date=end_date,
        )
        variant_arm = self._backtest_result_to_arm_backtest_result(
            variant_backtest,
            version="v2",
        )
        
        # Calculate deltas
        sharpe_delta = variant_arm.sharpe_ratio - baseline_arm.sharpe_ratio
        max_drawdown_delta = variant_arm.max_drawdown - baseline_arm.max_drawdown
        return_delta = variant_arm.total_return - baseline_arm.total_return
        volatility_delta = variant_arm.volatility - baseline_arm.volatility
        win_rate_delta = variant_arm.win_rate - baseline_arm.win_rate
        turnover_delta = variant_arm.turnover - baseline_arm.turnover
        
        # Calculate recommendation
        recommendation = self._calculate_recommendation(baseline_arm, variant_arm)
        
        # Build config dict
        config = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "capital": capital,
            "path_a_config_name": path_a_config_name,
        }
        
        # Create report
        report = DecisionABTestReport(
            experiment_id=experiment_id,
            created_at=datetime.now(),
            config=config,
            baseline=baseline_arm,
            variant=variant_arm,
            sharpe_delta=sharpe_delta,
            max_drawdown_delta=max_drawdown_delta,
            return_delta=return_delta,
            volatility_delta=volatility_delta,
            win_rate_delta=win_rate_delta,
            turnover_delta=turnover_delta,
            recommendation=recommendation,
            notes=note,
        )
        
        # Save to storage (if available)
        if hasattr(self.storage, 'save_decision_report'):
            self.storage.save_decision_report(report)
        else:
            # Try to save using new storage instance
            try:
                from jgod.decision_ab.storage import DecisionAbStorageV1
                v2_storage = DecisionAbStorageV1()
                v2_storage.save_decision_report(report)
            except Exception as e:
                logger.warning(f"Failed to save V1 vs V2 report: {e}")
        
        logger.info(
            f"V1 vs V2 AB Test completed: {experiment_id} | "
            f"Sharpe Delta: {sharpe_delta:+.4f}, "
            f"Return Delta: {return_delta:+.2%}, "
            f"Recommendation: {recommendation}"
        )
        
        return report

