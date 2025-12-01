"""Diagnosis Engine v1

系統級診斷與修復規劃引擎。

Reference:
- docs/JGOD_DIAGNOSIS_ENGINE_STANDARD_v1.md
- spec/JGOD_DiagnosisEngine_Spec.md
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from datetime import date

from .diagnosis_types import (
    DiagnosticEvent,
    SystemHealthSnapshot,
    RepairAction,
    RepairPlan,
    DiagnosisEngineResult,
)

# Type imports（避免循環導入）
try:
    from jgod.path_a.path_a_schema import PathABacktestResult
    from jgod.performance.performance_types import PerformanceEngineResult
    from jgod.learning.error_learning_engine import ErrorLearningEngine
    from jgod.learning.error_event import ErrorEvent
except ImportError:
    # 開發階段可能無法導入，使用類型註解
    PathABacktestResult = Any
    PerformanceEngineResult = Any
    ErrorLearningEngine = Any
    ErrorEvent = Any


class DiagnosisEngine:
    """Diagnosis & Repair Engine 核心類別
    
    負責收集全系統訊號、產生診斷事件、橋接到 ErrorLearningEngine、
    並產生修復建議。
    """
    
    def __init__(
        self,
        error_learning_engine: Optional[ErrorLearningEngine] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化 Diagnosis Engine
        
        Args:
            error_learning_engine: ErrorLearningEngine 實例（可選）
            config: 配置參數（門檻值等）
        """
        self.error_learning_engine = error_learning_engine
        self.config = config or {}
        
        # 預設配置參數
        self.default_config = {
            "TE_max": 0.05,              # Tracking Error 上限（5%）
            "T_max": 0.20,               # Turnover 上限（20%）
            "max_drawdown_threshold": -0.20,  # 最大回落門檻（-20%）
            "sharpe_threshold": 0.5,     # Sharpe Ratio 門檻
            "ir_threshold": 0.2,         # Information Ratio 門檻
            "turnover_cost_threshold": 0.01,  # Turnover 成本率門檻（1%）
        }
        
        # 合併配置
        for key, value in self.default_config.items():
            if key not in self.config:
                self.config[key] = value
    
    def from_path_a_and_performance(
        self,
        backtest_result: PathABacktestResult,
        performance_result: PerformanceEngineResult,
        execution_stats: Optional[Dict[str, Any]] = None,
        optimizer_stats: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> DiagnosisEngineResult:
        """從 Path A 和 Performance 結果進行診斷
        
        Args:
            backtest_result: Path A 回測結果
            performance_result: Performance Engine 結果
            execution_stats: Execution 統計（可選）
            optimizer_stats: Optimizer 統計（可選）
            config: 配置參數（可選，會與 self.config 合併）
        
        Returns:
            DiagnosisEngineResult 物件
        """
        # 合併配置
        merged_config = self.config.copy()
        if config:
            merged_config.update(config)
        
        # Step 1: 建立 SystemHealthSnapshot
        health = self._build_health_snapshot(
            backtest_result,
            performance_result,
            execution_stats,
            optimizer_stats
        )
        
        # Step 2-4: 分析並生成 DiagnosticEvents
        diagnostic_events = []
        
        # 約束分析
        events_from_constraints = self._analyze_constraints(
            backtest_result,
            performance_result,
            execution_stats,
            optimizer_stats,
            merged_config
        )
        diagnostic_events.extend(events_from_constraints)
        
        # 績效分析
        events_from_performance = self._analyze_performance(
            performance_result,
            merged_config
        )
        diagnostic_events.extend(events_from_performance)
        
        # Step 5: 橋接到 ErrorLearningEngine
        if self.error_learning_engine:
            for event in diagnostic_events:
                if event.severity != "INFO":
                    error_event = self._bridge_to_error_engine(event)
                    if error_event:
                        # 分析錯誤（可選，如果需要）
                        # analysis = self.error_learning_engine.analyze_error(error_event)
                        event.related_error_event_id = error_event.id
        
        # Step 6: 產生 RepairPlan
        repair_plan = self._build_repair_plan(
            health,
            diagnostic_events,
            merged_config
        )
        
        return DiagnosisEngineResult(
            health=health,
            diagnostic_events=diagnostic_events,
            repair_plan=repair_plan
        )
    
    def _build_health_snapshot(
        self,
        backtest_result: PathABacktestResult,
        performance_result: PerformanceEngineResult,
        execution_stats: Optional[Dict[str, Any]],
        optimizer_stats: Optional[Dict[str, Any]]
    ) -> SystemHealthSnapshot:
        """建立系統健康快照"""
        summary = performance_result.summary
        
        # 取得實驗名稱和日期範圍
        experiment_name = backtest_result.config.experiment_name
        start_date = date.fromisoformat(backtest_result.config.start_date)
        end_date = date.fromisoformat(backtest_result.config.end_date)
        
        # 計算違反的約束
        violated_constraints = []
        if optimizer_stats and "violated_constraints" in optimizer_stats:
            violated_constraints = optimizer_stats["violated_constraints"]
        
        # 計算 Error Event 計數
        error_event_counts = {}
        if backtest_result.error_events:
            for error_event in backtest_result.error_events:
                # 假設 error_event 有 classification 屬性
                if hasattr(error_event, "classification"):
                    error_type = error_event.classification
                    error_event_counts[error_type] = error_event_counts.get(error_type, 0) + 1
        
        return SystemHealthSnapshot(
            experiment_name=experiment_name,
            start_date=start_date,
            end_date=end_date,
            total_return=summary.total_return,
            cagr=summary.cagr,
            sharpe=summary.sharpe,
            max_drawdown=summary.max_drawdown,
            tracking_error=summary.tracking_error or 0.0,
            turnover=summary.turnover_annualized,
            violated_constraints=violated_constraints,
            error_event_counts=error_event_counts,
        )
    
    def _analyze_constraints(
        self,
        backtest_result: PathABacktestResult,
        performance_result: PerformanceEngineResult,
        execution_stats: Optional[Dict[str, Any]],
        optimizer_stats: Optional[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> List[DiagnosticEvent]:
        """分析約束違反"""
        events = []
        summary = performance_result.summary
        
        # 檢查 Tracking Error
        TE_max = config.get("TE_max", 0.05)
        if summary.tracking_error and summary.tracking_error > TE_max:
            events.append(DiagnosticEvent(
                source_module="OPTIMIZER",
                issue_type="TE_EXCEEDED",
                severity="WARN",
                message=f"Tracking Error ({summary.tracking_error:.2%}) 超過上限 ({TE_max:.2%})",
                metrics_before={"TE_max": TE_max},
                metrics_after={"TE": summary.tracking_error},
                tags=["constraint", "tracking_error"],
            ))
        
        # 檢查 Turnover
        T_max = config.get("T_max", 0.20)
        if summary.turnover_annualized > T_max:
            events.append(DiagnosticEvent(
                source_module="EXECUTION",
                issue_type="TURNOVER_TOO_HIGH",
                severity="WARN",
                message=f"Turnover ({summary.turnover_annualized:.2%}) 超過上限 ({T_max:.2%})",
                metrics_before={"T_max": T_max},
                metrics_after={"turnover": summary.turnover_annualized},
                tags=["constraint", "turnover"],
            ))
        
        # 檢查 Optimizer 約束違反
        if optimizer_stats:
            infeasible_count = optimizer_stats.get("infeasible_count", 0)
            total_optimizations = optimizer_stats.get("total_optimizations", 1)
            
            if infeasible_count > 0:
                infeasible_ratio = infeasible_count / total_optimizations
                if infeasible_ratio > 0.1:  # 超過 10% 無解
                    events.append(DiagnosticEvent(
                        source_module="OPTIMIZER",
                        issue_type="OPTIMIZER_INFEASIBLE",
                        severity="WARN",
                        message=f"Optimizer 無解次數過多 ({infeasible_count}/{total_optimizations})",
                        metrics_before={},
                        metrics_after={"infeasible_ratio": infeasible_ratio},
                        tags=["optimizer", "constraint"],
                    ))
        
        return events
    
    def _analyze_performance(
        self,
        performance_result: PerformanceEngineResult,
        config: Dict[str, Any]
    ) -> List[DiagnosticEvent]:
        """分析績效問題"""
        events = []
        summary = performance_result.summary
        
        sharpe_threshold = config.get("sharpe_threshold", 0.5)
        max_drawdown_threshold = config.get("max_drawdown_threshold", -0.20)
        TE_max = config.get("TE_max", 0.05)
        ir_threshold = config.get("ir_threshold", 0.2)
        
        # Alpha 不足檢測
        if (summary.sharpe < sharpe_threshold and
            summary.max_drawdown < max_drawdown_threshold and
            (summary.tracking_error or 0) < TE_max / 2):
            events.append(DiagnosticEvent(
                source_module="PERFORMANCE",
                issue_type="ALPHA_UNDERPERFORM",
                severity="WARN",
                message=f"Sharpe Ratio 偏低 ({summary.sharpe:.2f})，可能 Alpha 不足",
                metrics_before={},
                metrics_after={
                    "sharpe": summary.sharpe,
                    "max_drawdown": summary.max_drawdown,
                    "tracking_error": summary.tracking_error or 0,
                },
                tags=["alpha", "performance"],
            ))
        
        # 最大回落超過門檻
        if summary.max_drawdown < max_drawdown_threshold:
            severity = "CRITICAL" if summary.max_drawdown < max_drawdown_threshold * 1.5 else "WARN"
            events.append(DiagnosticEvent(
                source_module="PERFORMANCE",
                issue_type="DRAWDOWN_EXCEEDED",
                severity=severity,
                message=f"最大回落 ({summary.max_drawdown:.2%}) 超過門檻 ({max_drawdown_threshold:.2%})",
                metrics_before={"threshold": max_drawdown_threshold},
                metrics_after={"max_drawdown": summary.max_drawdown},
                tags=["risk", "drawdown"],
            ))
        
        # Information Ratio 過低
        if summary.information_ratio is not None and summary.information_ratio < ir_threshold:
            events.append(DiagnosticEvent(
                source_module="PERFORMANCE",
                issue_type="ALPHA_UNDERPERFORM",
                severity="INFO",
                message=f"Information Ratio ({summary.information_ratio:.2f}) 偏低",
                metrics_before={"threshold": ir_threshold},
                metrics_after={"information_ratio": summary.information_ratio},
                tags=["alpha", "performance"],
            ))
        
        return events
    
    def _bridge_to_error_engine(
        self,
        diagnostic_event: DiagnosticEvent
    ) -> Optional[ErrorEvent]:
        """將 DiagnosticEvent 轉換為 ErrorEvent
        
        Args:
            diagnostic_event: DiagnosticEvent 物件
        
        Returns:
            ErrorEvent 物件（如果應轉換），否則返回 None
        """
        # 只有 WARN 和 CRITICAL 級別才轉換
        if diagnostic_event.severity == "INFO":
            return None
        
        try:
            from jgod.learning.error_event import ErrorEvent
            
            error_event = ErrorEvent(
                id=f"err_{diagnostic_event.id}",
                timestamp=diagnostic_event.timestamp,
                symbol=diagnostic_event.related_symbols[0] if diagnostic_event.related_symbols else "PORTFOLIO",
                timeframe="1d",
                predicted_outcome=diagnostic_event.message,
                actual_outcome="",
                error_type=diagnostic_event.issue_type,
                tags=diagnostic_event.tags,
                context={
                    "source_module": diagnostic_event.source_module,
                    "severity": diagnostic_event.severity,
                },
            )
            
            return error_event
        except ImportError:
            # 如果無法導入 ErrorEvent，返回 None
            return None
    
    def _build_repair_plan(
        self,
        health: SystemHealthSnapshot,
        diagnostic_events: List[DiagnosticEvent],
        config: Dict[str, Any]
    ) -> RepairPlan:
        """建立修復計畫"""
        actions = []
        
        # 根據診斷事件產生修復行動
        for event in diagnostic_events:
            if event.severity == "CRITICAL":
                priority = "HIGH"
            elif event.severity == "WARN":
                priority = "MEDIUM"
            else:
                priority = "LOW"
            
            if event.issue_type == "TE_EXCEEDED":
                # 建議調整 TE_max 或檢討策略
                actions.append(RepairAction(
                    action_type="TUNE_CONFIG",
                    target_module="OPTIMIZER",
                    description=f"調整 Tracking Error 上限或檢討策略（當前 TE: {event.metrics_after.get('TE', 0):.2%}）",
                    proposed_changes={"optimizer.params.TE_max": event.metrics_after.get("TE", 0) * 1.1},
                    priority=priority,
                ))
            
            elif event.issue_type == "TURNOVER_TOO_HIGH":
                # 建議降低換手率
                actions.append(RepairAction(
                    action_type="TUNE_CONFIG",
                    target_module="OPTIMIZER",
                    description=f"降低換手率上限或調整再平衡頻率",
                    proposed_changes={"optimizer.params.T_max": event.metrics_before.get("T_max", 0.20) * 0.9},
                    priority=priority,
                ))
            
            elif event.issue_type == "ALPHA_UNDERPERFORM":
                # 建議檢討 Alpha Engine
                actions.append(RepairAction(
                    action_type="REVIEW_RULES",
                    target_module="ALPHA_ENGINE",
                    description="檢討 Alpha 因子選擇和權重，考慮增加新的 Alpha 因子",
                    proposed_changes={},
                    priority=priority,
                ))
            
            elif event.issue_type == "DRAWDOWN_EXCEEDED":
                # 建議加強風險控制
                actions.append(RepairAction(
                    action_type="REVIEW_RULES",
                    target_module="RISK_MODEL",
                    description="加強風險控制規則，檢討停損機制",
                    proposed_changes={},
                    priority="HIGH",  # 風險問題優先級高
                ))
        
        # 產生摘要
        summary_parts = []
        if health.sharpe < config.get("sharpe_threshold", 0.5):
            summary_parts.append("Sharpe Ratio 偏低")
        if health.max_drawdown < config.get("max_drawdown_threshold", -0.20):
            summary_parts.append("最大回落超過門檻")
        if health.tracking_error > config.get("TE_max", 0.05):
            summary_parts.append("Tracking Error 超過上限")
        
        summary = "; ".join(summary_parts) if summary_parts else "系統健康狀況良好"
        
        return RepairPlan(
            experiment_name=health.experiment_name,
            summary=summary,
            actions=actions
        )

