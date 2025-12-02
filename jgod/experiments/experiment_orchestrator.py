"""Experiment Orchestrator v1

實驗編排器，整合所有模組執行完整實驗流程。

Reference:
- docs/JGOD_EXPERIMENT_ORCHESTRATOR_STANDARD_v1.md
- spec/JGOD_ExperimentOrchestrator_Spec.md
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from .experiment_types import (
    ExperimentConfig,
    ExperimentArtifacts,
    ExperimentReport,
    ExperimentRunResult,
)

# Performance 模組直接導入，不設 fallback
from jgod.performance import PerformanceEngine, PerformanceEngineRequest, PerformanceEngineResult

# Type imports（避免循環導入）
try:
    from jgod.path_a.path_a_schema import PathAConfig, PathABacktestResult, PathADataLoader
    from jgod.diagnostics.diagnosis_engine import DiagnosisEngine
    from jgod.alpha_engine.alpha_engine import AlphaEngine
    from jgod.risk.risk_model import MultiFactorRiskModel
    from jgod.optimizer.optimizer_core_v2 import OptimizerCoreV2
    from jgod.execution.execution_engine import ExecutionEngine
    from jgod.knowledge.knowledge_brain import KnowledgeBrain
    from jgod.learning.error_learning_engine import ErrorLearningEngine
except ImportError:
    # 開發階段可能無法導入，使用類型註解
    PathADataLoader = Any
    AlphaEngine = Any
    MultiFactorRiskModel = Any
    OptimizerCoreV2 = Any
    ExecutionEngine = Any
    DiagnosisEngine = Any
    KnowledgeBrain = Any
    ErrorLearningEngine = Any


class ExperimentOrchestrator:
    """Experiment Orchestrator 核心類別
    
    負責編排整個實驗流程，整合所有模組。
    """
    
    def __init__(
        self,
        data_loader: PathADataLoader,
        alpha_engine: AlphaEngine,
        risk_model: MultiFactorRiskModel,
        optimizer: OptimizerCoreV2,
        execution_engine: ExecutionEngine,
        performance_engine: PerformanceEngine,
        diagnosis_engine: DiagnosisEngine,
        knowledge_brain: KnowledgeBrain,
        error_learning_engine: ErrorLearningEngine,
    ):
        """初始化 Experiment Orchestrator
        
        Args:
            data_loader: 資料載入器
            alpha_engine: Alpha Engine
            risk_model: Risk Model
            optimizer: Optimizer Core v2
            execution_engine: Execution Engine
            performance_engine: Performance Engine
            diagnosis_engine: Diagnosis Engine
            knowledge_brain: Knowledge Brain
            error_learning_engine: Error Learning Engine
        """
        self.data_loader = data_loader
        self.alpha_engine = alpha_engine
        self.risk_model = risk_model
        self.optimizer = optimizer
        self.execution_engine = execution_engine
        self.performance_engine = performance_engine
        self.diagnosis_engine = diagnosis_engine
        self.knowledge_brain = knowledge_brain
        self.error_learning_engine = error_learning_engine
    
    def run_experiment(
        self,
        config: ExperimentConfig
    ) -> ExperimentRunResult:
        """執行完整實驗
        
        Args:
            config: 實驗設定
        
        Returns:
            ExperimentRunResult 物件
        """
        # 驗證設定
        config.validate()
        
        # Step 1: Load Data
        path_a_config = self._build_path_a_config(config)
        
        # Step 2: Run Path A Backtest
        path_a_result = self._run_path_a_backtest(path_a_config)
        
        # Step 3: Analyze Performance
        performance_result = self._analyze_performance(path_a_result, config)
        
        # Step 4: Run Diagnosis
        diagnosis_result = self._run_diagnosis(
            path_a_result,
            performance_result,
            config
        )
        
        # Step 5: Build Report
        artifacts = ExperimentArtifacts(
            path_a_result=path_a_result,
            performance_result=performance_result,
            diagnosis_result=diagnosis_result,
            execution_stats={},  # TODO: 從 execution_result 提取
            optimizer_stats={},  # TODO: 從 optimizer 提取
        )
        
        report = self._build_report(artifacts, config)
        
        # Step 6: Persist Outputs
        files_generated = self._persist_outputs(
            config.name,
            artifacts,
            report
        )
        
        # 更新報告中的檔案清單
        report.files_generated = files_generated
        
        return ExperimentRunResult(
            config=config,
            artifacts=artifacts,
            report=report
        )
    
    def _build_path_a_config(
        self,
        config: ExperimentConfig
    ) -> PathAConfig:
        """從 ExperimentConfig 建立 PathAConfig"""
        from jgod.path_a.path_a_schema import PathAConfig
        
        return PathAConfig(
            start_date=config.start_date,
            end_date=config.end_date,
            universe=config.universe,
            rebalance_frequency=config.rebalance_frequency,
            experiment_name=config.name,
            transaction_cost_bps=config.execution_params.get("transaction_cost_bps", 5.0),
            slippage_bps=config.execution_params.get("slippage_bps", 0.0),
        )
    
    def _run_path_a_backtest(
        self,
        path_a_config: PathAConfig
    ) -> PathABacktestResult:
        """執行 Path A 回測
        
        執行流程：
        - 使用 DataLoader 載入價格與特徵
        - 建立 PathARunContext
        - 呼叫 run_path_a_backtest
        """
        # 為了避免 top-level import 失敗，改成在這裡 local import
        from jgod.path_a.path_a_backtest import PathARunContext, run_path_a_backtest
        
        # 建立 PathARunContext
        context = PathARunContext(
            config=path_a_config,
            data_loader=self.data_loader,
            alpha_engine=self.alpha_engine,
            risk_model=self.risk_model,
            optimizer=self.optimizer,
            error_engine=self.error_learning_engine,
            error_bridge=None,  # TODO: 實作 ErrorBridge
        )
        
        # 執行回測
        return run_path_a_backtest(context)
    
    def _analyze_performance(
        self,
        path_a_result: PathABacktestResult,
        config: ExperimentConfig
    ) -> PerformanceEngineResult:
        """分析績效"""
        # 建立 PerformanceEngineRequest
        request = PerformanceEngineRequest.from_path_a_result(
            path_a_result,
            benchmark_returns=None,  # TODO: 支援 benchmark
            factor_returns=None,     # TODO: 從 RiskModel 取得
            sector_map=None,         # TODO: 支援 sector mapping
        )
        
        # 計算績效
        return self.performance_engine.compute_full_report(request)
    
    def _run_diagnosis(
        self,
        path_a_result: PathABacktestResult,
        performance_result: PerformanceEngineResult,
        config: ExperimentConfig
    ) -> DiagnosisEngineResult:
        """執行診斷"""
        # 合併診斷參數
        diagnosis_config = config.diagnosis_params.copy()
        
        # 執行診斷
        return self.diagnosis_engine.from_path_a_and_performance(
            backtest_result=path_a_result,
            performance_result=performance_result,
            execution_stats={},  # TODO: 從 execution_result 提取
            optimizer_stats={},  # TODO: 從 optimizer 提取
            config=diagnosis_config,
        )
    
    def _build_report(
        self,
        artifacts: ExperimentArtifacts,
        config: ExperimentConfig
    ) -> ExperimentReport:
        """建立報告"""
        summary = artifacts.performance_result.summary.to_dict()
        
        # 生成亮點摘要
        highlights = self._generate_highlights(artifacts)
        
        # 診斷摘要
        diagnosis_summary = self._generate_diagnosis_summary(artifacts.diagnosis_result)
        
        # 修復行動
        repair_actions = artifacts.diagnosis_result.repair_plan.actions
        
        return ExperimentReport(
            summary=summary,
            highlights=highlights,
            diagnosis_summary=diagnosis_summary,
            repair_actions=repair_actions,
            files_generated=[],  # 將在 _persist_outputs 中填入
        )
    
    def _generate_highlights(
        self,
        artifacts: ExperimentArtifacts
    ) -> List[str]:
        """生成亮點摘要"""
        highlights = []
        summary = artifacts.performance_result.summary
        
        # Sharpe Ratio
        if summary.sharpe > 1.0:
            highlights.append(f"Sharpe Ratio 表現優異 ({summary.sharpe:.2f})")
        elif summary.sharpe < 0.5:
            highlights.append(f"Sharpe Ratio 偏低 ({summary.sharpe:.2f})，需要檢討策略")
        
        # Total Return
        if summary.total_return > 0.20:
            highlights.append(f"累積報酬率良好 ({summary.total_return:.2%})")
        elif summary.total_return < 0:
            highlights.append(f"累積報酬為負 ({summary.total_return:.2%})，需要檢討策略")
        
        # Max Drawdown
        if summary.max_drawdown < -0.20:
            highlights.append(f"最大回落超過 20% ({summary.max_drawdown:.2%})，風險控制需要加強")
        
        # Tracking Error
        if summary.tracking_error and summary.tracking_error > 0.05:
            highlights.append(f"Tracking Error 超過上限 ({summary.tracking_error:.2%})")
        
        return highlights if highlights else ["實驗完成，請檢視詳細報告"]
    
    def _generate_diagnosis_summary(
        self,
        diagnosis_result: DiagnosisEngineResult
    ) -> str:
        """生成診斷摘要"""
        num_events = len(diagnosis_result.diagnostic_events)
        num_critical = sum(1 for e in diagnosis_result.diagnostic_events if e.severity == "CRITICAL")
        num_warn = sum(1 for e in diagnosis_result.diagnostic_events if e.severity == "WARN")
        
        summary_parts = [
            f"共檢測到 {num_events} 個診斷事件",
            f"其中 CRITICAL: {num_critical} 個，WARN: {num_warn} 個",
        ]
        
        if num_critical > 0:
            summary_parts.append("⚠️ 存在嚴重問題，請優先處理")
        
        return "; ".join(summary_parts)
    
    def _persist_outputs(
        self,
        experiment_name: str,
        artifacts: ExperimentArtifacts,
        report: ExperimentReport
    ) -> List[str]:
        """持久化輸出檔案"""
        output_dir = Path("output") / "experiments" / experiment_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        files_generated = []
        
        # NAV CSV
        nav_file = output_dir / "nav.csv"
        artifacts.path_a_result.nav_series.to_csv(nav_file)
        files_generated.append(str(nav_file))
        
        # Returns CSV
        returns_file = output_dir / "returns.csv"
        artifacts.path_a_result.return_series.to_csv(returns_file)
        files_generated.append(str(returns_file))
        
        # Performance Summary JSON
        perf_file = output_dir / "performance_summary.json"
        with open(perf_file, "w") as f:
            json.dump(report.summary, f, indent=2)
        files_generated.append(str(perf_file))
        
        # Performance Report MD
        perf_report_file = output_dir / "performance_report.md"
        self._write_performance_report(perf_report_file, artifacts.performance_result)
        files_generated.append(str(perf_report_file))
        
        # Diagnosis Report MD
        diag_report_file = output_dir / "diagnosis_report.md"
        self._write_diagnosis_report(diag_report_file, artifacts.diagnosis_result)
        files_generated.append(str(diag_report_file))
        
        # Repair Plan MD
        repair_file = output_dir / "repair_plan.md"
        self._write_repair_plan(repair_file, artifacts.diagnosis_result.repair_plan)
        files_generated.append(str(repair_file))
        
        # Config JSON
        config_file = output_dir / "config.json"
        with open(config_file, "w") as f:
            json.dump(artifacts.path_a_result.config.__dict__, f, indent=2, default=str)
        files_generated.append(str(config_file))
        
        return files_generated
    
    def _write_performance_report(
        self,
        file_path: Path,
        performance_result: PerformanceEngineResult
    ) -> None:
        """寫入績效報告（Markdown）"""
        summary = performance_result.summary
        attribution = performance_result.attribution
        
        with open(file_path, "w") as f:
            f.write("# Performance Report\n\n")
            f.write("## Summary\n\n")
            f.write(f"- Total Return: {summary.total_return:.2%}\n")
            f.write(f"- CAGR: {summary.cagr:.2%}\n")
            f.write(f"- Sharpe Ratio: {summary.sharpe:.2f}\n")
            f.write(f"- Max Drawdown: {summary.max_drawdown:.2%}\n")
            if summary.tracking_error:
                f.write(f"- Tracking Error: {summary.tracking_error:.2%}\n")
            if summary.information_ratio:
                f.write(f"- Information Ratio: {summary.information_ratio:.2f}\n")
            f.write(f"- Turnover: {summary.turnover_annualized:.2%}\n\n")
            
            f.write("## Attribution\n\n")
            if not attribution.by_symbol.empty:
                f.write("### Symbol Attribution\n\n")
                f.write(attribution.by_symbol.to_markdown())
                f.write("\n\n")
    
    def _write_diagnosis_report(
        self,
        file_path: Path,
        diagnosis_result: DiagnosisEngineResult
    ) -> None:
        """寫入診斷報告（Markdown）"""
        health = diagnosis_result.health
        events = diagnosis_result.diagnostic_events
        
        with open(file_path, "w") as f:
            f.write("# Diagnosis Report\n\n")
            f.write("## System Health\n\n")
            f.write(f"- Experiment: {health.experiment_name}\n")
            f.write(f"- Period: {health.start_date} to {health.end_date}\n")
            f.write(f"- Sharpe Ratio: {health.sharpe:.2f}\n")
            f.write(f"- Max Drawdown: {health.max_drawdown:.2%}\n\n")
            
            f.write("## Diagnostic Events\n\n")
            for event in events:
                f.write(f"### [{event.severity}] {event.issue_type}\n\n")
                f.write(f"{event.message}\n\n")
    
    def _write_repair_plan(
        self,
        file_path: Path,
        repair_plan: Any  # RepairPlan
    ) -> None:
        """寫入修復計畫（Markdown）"""
        with open(file_path, "w") as f:
            f.write("# Repair Plan\n\n")
            f.write(f"## Summary\n\n{repair_plan.summary}\n\n")
            f.write("## Actions\n\n")
            
            for action in repair_plan.actions:
                f.write(f"### [{action.priority}] {action.action_type}\n\n")
                f.write(f"**Target Module**: {action.target_module}\n\n")
                f.write(f"**Description**: {action.description}\n\n")
                if action.proposed_changes:
                    f.write(f"**Proposed Changes**:\n\n")
                    for key, value in action.proposed_changes.items():
                        f.write(f"- `{key}`: {value}\n")
                f.write("\n")

