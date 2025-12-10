"""Rule Simulation Engine

Core engine for running rule simulation experiments.
"""

import logging
import uuid
from datetime import datetime, date
from typing import Optional

from jgod.rule_sim.models import (
    RuleSimExperimentConfig,
    RuleSimReport,
    RuleSimStatusSummary,
    RuleSimStatus,
    RuleSimArmMetrics,
    RuleSimDeltaMetrics,
    RuleSimArm,
)
from jgod.rule_sim.storage import RuleSimStorageV1
from jgod.rule_sim.data_access import RuleSimDataAccess
from jgod.rule_sim.sandbox_applier import RuleSandboxApplier
from jgod.rule_sim.config import MAX_SHARPE_DROP, MAX_MAXDD_INCREASE, MAX_ALERT_INCREASE

logger = logging.getLogger(__name__)


class RuleSimEngineV1:
    """Rule Simulation Engine v1"""
    
    def __init__(
        self,
        storage: Optional[RuleSimStorageV1] = None,
        data_access: Optional[RuleSimDataAccess] = None,
        sandbox_applier: Optional[RuleSandboxApplier] = None,
    ):
        """
        Initialize rule simulation engine
        
        Args:
            storage: Storage instance (optional)
            data_access: Data access instance (optional)
            sandbox_applier: Sandbox applier instance (optional)
        """
        self.storage = storage or RuleSimStorageV1()
        self.data_access = data_access or RuleSimDataAccess()
        self.sandbox_applier = sandbox_applier or RuleSandboxApplier()
        logger.info("RuleSimEngineV1 initialized")
    
    def run_experiment(self, config: RuleSimExperimentConfig) -> RuleSimReport:
        """
        Run a complete rule simulation experiment.
        
        Steps:
        1. Create sandbox (variant)
        2. Run BASELINE (production rules)
        3. Run VARIANT (sandbox rules)
        4. Collect metrics and compute deltas
        5. Generate recommendation
        6. Save report
        
        Args:
            config: Experiment configuration
        
        Returns:
            RuleSimReport with results
        """
        experiment_id = config.experiment_id
        logger.info(f"Starting rule simulation experiment: {experiment_id}")
        
        status = RuleSimStatusSummary(
            status=RuleSimStatus.RUNNING,
            started_at=datetime.now(),
        )
        
        try:
            # Step 1: Create sandbox
            logger.info("Step 1: Creating sandbox...")
            sandbox_dir = self.sandbox_applier.create_sandbox(config)
            
            # Step 2: Run BASELINE backtest (production rules)
            logger.info("Step 2: Running BASELINE backtest...")
            baseline_result = self.data_access.run_path_a_backtest(
                start_date=config.start_date,
                end_date=config.end_date,
                universe=config.universe,
                path_a_config_name=config.path_a_config_name,
                sandbox_dir=None,  # Production rules
            )
            
            baseline_alert_stats = self.data_access.collect_alert_stats(
                start_date=config.start_date,
                end_date=config.end_date,
                universe=config.universe,
                sandbox_dir=None,
            )
            
            baseline_metrics = self._convert_to_arm_metrics(
                baseline_result.metrics,
                RuleSimArm.BASELINE,
                baseline_alert_stats,
            )
            
            # Step 3: Run VARIANT backtest (sandbox rules)
            logger.info("Step 3: Running VARIANT backtest...")
            variant_result = self.data_access.run_path_a_backtest(
                start_date=config.start_date,
                end_date=config.end_date,
                universe=config.universe,
                path_a_config_name=config.path_a_config_name,
                sandbox_dir=sandbox_dir,  # Sandbox rules
            )
            
            variant_alert_stats = self.data_access.collect_alert_stats(
                start_date=config.start_date,
                end_date=config.end_date,
                universe=config.universe,
                sandbox_dir=sandbox_dir,
            )
            
            variant_metrics = self._convert_to_arm_metrics(
                variant_result.metrics,
                RuleSimArm.VARIANT,
                variant_alert_stats,
            )
            
            # Step 4: Compute deltas
            logger.info("Step 4: Computing deltas...")
            deltas = self._compute_deltas(baseline_metrics, variant_metrics)
            
            # Step 5: Generate recommendation and findings
            logger.info("Step 5: Generating recommendation...")
            recommendation, key_findings = self._generate_recommendation(
                baseline_metrics,
                variant_metrics,
                deltas,
            )
            
            # Step 6: Create report
            status.status = RuleSimStatus.SUCCESS
            status.finished_at = datetime.now()
            
            report = RuleSimReport(
                experiment_id=experiment_id,
                config=config,
                status=status,
                baseline_metrics=baseline_metrics,
                variant_metrics=variant_metrics,
                deltas=deltas,
                key_findings=key_findings,
                recommendation=recommendation,
            )
            
            # Save report
            self.storage.save_report(report)
            logger.info(f"Experiment completed: {experiment_id}, recommendation: {recommendation}")
            
            return report
            
        except Exception as e:
            logger.error(f"Experiment failed: {e}", exc_info=True)
            status.status = RuleSimStatus.FAILED
            status.finished_at = datetime.now()
            status.error_message = str(e)
            
            # Create failed report
            report = RuleSimReport(
                experiment_id=experiment_id,
                config=config,
                status=status,
                baseline_metrics=RuleSimArmMetrics(arm=RuleSimArm.BASELINE),
                variant_metrics=RuleSimArmMetrics(arm=RuleSimArm.VARIANT),
                deltas=RuleSimDeltaMetrics(),
                key_findings=[],
                recommendation="REJECT",
            )
            
            self.storage.save_report(report)
            return report
    
    def _convert_to_arm_metrics(
        self,
        performance_metrics,
        arm: RuleSimArm,
        alert_stats: dict,
    ) -> RuleSimArmMetrics:
        """Convert PerformanceMetrics to RuleSimArmMetrics"""
        return RuleSimArmMetrics(
            arm=arm,
            sharpe=performance_metrics.sharpe_ratio,
            max_drawdown=performance_metrics.max_drawdown,
            total_return=performance_metrics.total_return,
            win_rate=performance_metrics.win_rate,
            turnover=0.0,  # TODO: Calculate turnover if available
            var_95=None,  # TODO: Calculate VaR if available
            alert_trigger_count=alert_stats.get("alert_trigger_count", 0),
            doctrine_violation_count=alert_stats.get("doctrine_violation_count", 0),
        )
    
    def _compute_deltas(
        self,
        baseline: RuleSimArmMetrics,
        variant: RuleSimArmMetrics,
    ) -> RuleSimDeltaMetrics:
        """Compute delta metrics"""
        return RuleSimDeltaMetrics(
            sharpe_delta=variant.sharpe - baseline.sharpe,
            max_drawdown_delta=variant.max_drawdown - baseline.max_drawdown,
            total_return_delta=variant.total_return - baseline.total_return,
            win_rate_delta=variant.win_rate - baseline.win_rate,
            turnover_delta=variant.turnover - baseline.turnover,
            alert_trigger_delta=(
                variant.alert_trigger_count - baseline.alert_trigger_count
                if variant.alert_trigger_count is not None and baseline.alert_trigger_count is not None
                else None
            ),
            doctrine_violation_delta=(
                variant.doctrine_violation_count - baseline.doctrine_violation_count
                if variant.doctrine_violation_count is not None and baseline.doctrine_violation_count is not None
                else None
            ),
        )
    
    def _generate_recommendation(
        self,
        baseline: RuleSimArmMetrics,
        variant: RuleSimArmMetrics,
        deltas: RuleSimDeltaMetrics,
    ) -> tuple[str, list[str]]:
        """
        Generate recommendation and key findings.
        
        Logic:
        - If Sharpe improves, MaxDD not worse, alerts not increased much → "APPROVE"
        - If Sharpe slightly drops or MaxDD increases in acceptable range → "CAUTION"
        - If Sharpe drops significantly or MaxDD worsens or alerts surge → "REJECT"
        
        Returns:
            Tuple of (recommendation, key_findings)
        """
        findings = []
        recommendation = "CAUTION"
        
        # Sharpe analysis
        if deltas.sharpe_delta > 0.05:
            findings.append(f"Sharpe Ratio 提升 {deltas.sharpe_delta:.3f} (Baseline: {baseline.sharpe:.3f} → Variant: {variant.sharpe:.3f})")
            recommendation = "APPROVE"
        elif deltas.sharpe_delta < MAX_SHARPE_DROP:
            findings.append(f"⚠️ Sharpe Ratio 下降 {abs(deltas.sharpe_delta):.3f} (超過警戒值 {abs(MAX_SHARPE_DROP)})")
            recommendation = "REJECT"
        elif deltas.sharpe_delta < 0:
            findings.append(f"Sharpe Ratio 下降 {abs(deltas.sharpe_delta):.3f} (Baseline: {baseline.sharpe:.3f} → Variant: {variant.sharpe:.3f})")
            recommendation = "CAUTION"
        
        # Max Drawdown analysis
        if deltas.max_drawdown_delta > MAX_MAXDD_INCREASE:
            findings.append(f"⚠️ Max Drawdown 增加 {deltas.max_drawdown_delta:.2%} (超過警戒值 {MAX_MAXDD_INCREASE:.2%})")
            if recommendation == "APPROVE":
                recommendation = "CAUTION"
            else:
                recommendation = "REJECT"
        elif deltas.max_drawdown_delta < 0:
            findings.append(f"Max Drawdown 改善 {abs(deltas.max_drawdown_delta):.2%} (Baseline: {baseline.max_drawdown:.2%} → Variant: {variant.max_drawdown:.2%})")
            if recommendation == "CAUTION":
                recommendation = "APPROVE"
        
        # Total Return analysis
        if deltas.total_return_delta > 0.05:
            findings.append(f"總報酬率提升 {deltas.total_return_delta:.2%}")
        elif deltas.total_return_delta < -0.05:
            findings.append(f"總報酬率下降 {abs(deltas.total_return_delta):.2%}")
        
        # Alert analysis
        if deltas.alert_trigger_delta is not None:
            if deltas.alert_trigger_delta > MAX_ALERT_INCREASE:
                findings.append(f"⚠️ Alert 觸發次數增加 {deltas.alert_trigger_delta} 次 (超過警戒值 {MAX_ALERT_INCREASE})")
                recommendation = "REJECT"
            elif deltas.alert_trigger_delta > 0:
                findings.append(f"Alert 觸發次數增加 {deltas.alert_trigger_delta} 次")
            elif deltas.alert_trigger_delta < 0:
                findings.append(f"Alert 觸發次數減少 {abs(deltas.alert_trigger_delta)} 次")
        
        # Win Rate analysis
        if abs(deltas.win_rate_delta) > 0.05:
            findings.append(f"勝率變化 {deltas.win_rate_delta:+.2%} (Baseline: {baseline.win_rate:.2%} → Variant: {variant.win_rate:.2%})")
        
        # Default findings if empty
        if not findings:
            findings.append("指標變化在可接受範圍內")
        
        return recommendation, findings

