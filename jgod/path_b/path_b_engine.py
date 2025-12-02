"""
Path B v1 - Walk-Forward Analysis Engine

This module provides the Path B Engine for executing In-Sample / Out-of-Sample
testing and Walk-Forward Analysis to validate strategy stability.

Path B is responsible for:
- Splitting data into train/test windows
- Executing walk-forward analysis
- Collecting performance metrics across windows
- Simulating governance rules (Alpha Sunset, Regime Switch, Kill Switch)
- Generating stability reports

Reference:
- spec/JGOD_PathBEngine_Spec.md
- docs/JGOD_PATH_B_STANDARD_v1.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple, Any, Callable
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from jgod.path_a.path_a_schema import PathABacktestResult
from jgod.path_a.path_a_backtest import PathADataLoader


# ---------------------------------------------------------------------------
# Configuration & Data Structures
# ---------------------------------------------------------------------------


@dataclass
class PathBConfig:
    """Path B Engine 配置"""
    
    # Window 設定
    train_start: str  # "YYYY-MM-DD"
    train_end: str    # "YYYY-MM-DD"
    test_start: str   # "YYYY-MM-DD"
    test_end: str     # "YYYY-MM-DD"
    
    # Walk-Forward 參數
    walkforward_window: str  # 例如 "6m" (6 months), "12m"
    walkforward_step: str    # 例如 "1m" (1 month), "3m"
    
    # 基本設定
    universe: Sequence[str]
    rebalance_frequency: str  # "D", "W", "M"
    
    # 多策略配置
    alpha_config_set: List[Dict[str, Any]]  # 多組 alpha engine 配置
    # 例如：
    # [
    #     {"name": "strategy_1", "alpha_config": {...}},
    #     {"name": "strategy_2", "alpha_config": {...}},
    # ]
    
    # Governance Rules
    governance_rules: Optional[Dict[str, Any]] = None
    # 例如：
    # {
    #     "alpha_sunset": {"threshold": 0.5, "lookback": 60},
    #     "kill_switch": {"max_drawdown": -0.20, "sharpe_threshold": 0.0},
    #     "regime_manager": {"enabled": True}
    # }
    
    # 其他設定
    data_source: str = "mock"  # "mock", "finmind"
    mode: str = "basic"  # "basic", "extreme"
    initial_nav: float = 100.0
    transaction_cost_bps: float = 5.0
    slippage_bps: float = 0.0
    
    # 實驗名稱
    experiment_name: str = "path_b_experiment"


@dataclass
class PathBWindowResult:
    """單一 Window 的測試結果"""
    
    window_id: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    
    # Train 階段結果
    train_result: Optional[PathABacktestResult] = None
    
    # Test 階段結果
    test_result: PathABacktestResult
    
    # Governance Rule 觸發紀錄
    governance_events: List[Dict[str, Any]] = field(default_factory=list)
    # 例如：
    # [
    #     {"rule": "alpha_sunset", "triggered": True, "date": "2024-03-15"},
    #     {"rule": "kill_switch", "triggered": False}
    # ]
    
    # 績效統計（Test 階段）
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    turnover_rate: float
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None
    
    # 因子歸因
    factor_attribution: Optional[Dict[str, float]] = None


@dataclass
class PathBRunResult:
    """完整的 Path B 執行結果"""
    
    config: PathBConfig
    
    # 所有 Window 結果
    window_results: List[PathBWindowResult]
    
    # 彙總統計
    summary: Dict[str, Any] = field(default_factory=dict)
    # 包含：
    # - 所有 window 的平均 Sharpe
    # - 所有 window 的平均 Max Drawdown
    # - Window 間一致性（Sharpe 標準差）
    # - Alpha Stability Score
    
    # Governance 分析
    governance_analysis: Dict[str, Any] = field(default_factory=dict)
    # 包含：
    # - 每個 rule 的觸發次數
    # - 觸發時的市場環境特徵
    
    # 輸出檔案路徑
    output_files: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Path B Engine
# ---------------------------------------------------------------------------


class PathBEngine:
    """Path B Engine 主類別"""
    
    def __init__(
        self,
        data_loader: Optional[PathADataLoader] = None,
        alpha_engine_factory: Optional[Callable] = None,
        risk_model_factory: Optional[Callable] = None,
        optimizer_factory: Optional[Callable] = None,
        execution_engine_factory: Optional[Callable] = None,
        data_source: str = "mock",
        mode: str = "basic",
    ):
        """
        初始化 Path B Engine
        
        Args:
            data_loader: Path A Data Loader 實例（可選，若為 None 則在 run() 時根據 config 建立）
            alpha_engine_factory: Alpha Engine 工廠函數
            risk_model_factory: Risk Model 工廠函數
            optimizer_factory: Optimizer 工廠函數
            execution_engine_factory: Execution Engine 工廠函數
            data_source: 資料來源（"mock" 或 "finmind"）
            mode: 執行模式（"basic" 或 "extreme"）
        """
        self.data_loader = data_loader
        self.alpha_engine_factory = alpha_engine_factory
        self.risk_model_factory = risk_model_factory
        self.optimizer_factory = optimizer_factory
        self.execution_engine_factory = execution_engine_factory
        self.data_source = data_source
        self.mode = mode
        self.base_universe: Optional[Sequence[str]] = None
        
        # TODO: integrate AlphaHealthMonitor
        # TODO: integrate RegimeManager
        # TODO: integrate KillSwitchController
    
    def run(self, config: PathBConfig) -> PathBRunResult:
        """
        執行完整的 Path B 分析
        
        Args:
            config: Path B 配置
        
        Returns:
            PathBRunResult 物件
        """
        # Step 1: Window 切割
        windows = self._generate_windows(config)
        
        # Step 2-4: 執行每個 window
        window_results = []
        for window_id, (train_start, train_end, test_start, test_end) in enumerate(windows, 1):
            window_result = self._run_single_window(
                window_id=window_id,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                config=config
            )
            window_results.append(window_result)
        
        # Step 5: Combine & Export
        summary = self._compute_summary(window_results)
        governance_analysis = self._analyze_governance(window_results, config)
        
        result = PathBRunResult(
            config=config,
            window_results=window_results,
            summary=summary,
            governance_analysis=governance_analysis,
        )
        
        # TODO: Export results to files
        # result.output_files = self._export_results(result)
        
        return result
    
    def _generate_windows(
        self,
        config: PathBConfig
    ) -> List[Tuple[str, str, str, str]]:
        """
        根據 walkforward 參數生成所有 window
        
        Args:
            config: Path B 配置
        
        Returns:
            List of (train_start, train_end, test_start, test_end) tuples
        """
        def _parse_duration(duration_str: str) -> int:
            """Parse duration string like '6m' -> 6 months"""
            if duration_str.endswith('m'):
                return int(duration_str[:-1])
            elif duration_str.endswith('y'):
                return int(duration_str[:-1]) * 12
            else:
                raise ValueError(f"Invalid duration format: {duration_str}. Expected format: '6m' or '1y'")
        
        # Parse walkforward parameters
        window_months = _parse_duration(config.walkforward_window)
        step_months = _parse_duration(config.walkforward_step)
        
        # Convert date strings to datetime
        first_train_start = pd.to_datetime(config.train_start)
        first_train_end = pd.to_datetime(config.train_end)
        first_test_start = pd.to_datetime(config.test_start)
        first_test_end = pd.to_datetime(config.test_end)
        
        # Calculate train and test durations in months
        train_duration_months = (first_train_end.year - first_train_start.year) * 12 + \
                                (first_train_end.month - first_train_start.month)
        test_duration_months = (first_test_end.year - first_test_start.year) * 12 + \
                               (first_test_end.month - first_test_start.month)
        
        # Generate windows
        windows = []
        current_train_start = first_train_start
        window_id = 0
        
        while True:
            # Calculate train end
            train_end = current_train_start + pd.DateOffset(months=train_duration_months)
            
            # Calculate test start (immediately after train end)
            test_start = train_end + pd.DateOffset(days=1)
            test_end = test_start + pd.DateOffset(months=test_duration_months)
            
            # Check if test_end exceeds the global end date
            if test_end > first_test_end:
                # Check if we have at least one complete window
                if window_id == 0:
                    # Use the first window as-is (as specified in config)
                    windows.append((
                        config.train_start,
                        config.train_end,
                        config.test_start,
                        config.test_end
                    ))
                break
            
            windows.append((
                current_train_start.strftime("%Y-%m-%d"),
                train_end.strftime("%Y-%m-%d"),
                test_start.strftime("%Y-%m-%d"),
                test_end.strftime("%Y-%m-%d"),
            ))
            
            # Move to next window
            current_train_start = current_train_start + pd.DateOffset(months=step_months)
            window_id += 1
        
        # Ensure at least one window is returned
        if not windows:
            windows.append((
                config.train_start,
                config.train_end,
                config.test_start,
                config.test_end
            ))
        
        return windows
    
    def _run_single_window(
        self,
        window_id: int,
        train_start: str,
        train_end: str,
        test_start: str,
        test_end: str,
        config: PathBConfig
    ) -> PathBWindowResult:
        """
        執行單一 window 的訓練與測試（最小可用版本）
        
        Args:
            window_id: Window ID
            train_start: Train 階段開始日期
            train_end: Train 階段結束日期
            test_start: Test 階段開始日期
            test_end: Test 階段結束日期
            config: Path B 配置
        
        Returns:
            PathBWindowResult 物件
        """
        # Step 2 - Train 模式（IS）- 目前簡化為不做訓練，直接使用預設參數
        train_result = None
        
        # Step 3 - Test 模式（OOS）
        # 建立 Path A 設定（使用 test 期間）
        from jgod.path_a.path_a_schema import PathAConfig
        
        path_a_config = PathAConfig(
            start_date=test_start,
            end_date=test_end,
            universe=list(config.universe),
            rebalance_frequency=config.rebalance_frequency,
            initial_nav=config.initial_nav,
            transaction_cost_bps=config.transaction_cost_bps,
            slippage_bps=config.slippage_bps,
            experiment_name=f"{config.experiment_name}_window_{window_id}",
        )
        
        # 建立或取得 data loader
        data_loader = self._get_or_create_data_loader(config)
        
        # 建立引擎（如果沒有提供 factory，使用 build_orchestrator 的邏輯）
        alpha_engine, risk_model, optimizer = self._get_or_create_engines(config)
        
        # 執行 Path A backtest
        from jgod.path_a.path_a_backtest import PathARunContext, run_path_a_backtest
        from jgod.learning.error_learning_engine import ErrorLearningEngine
        
        error_engine = ErrorLearningEngine(
            draft_output_path="knowledge_base/jgod_knowledge_drafts.jsonl",
            report_output_dir="error_logs/reports"
        )
        
        context = PathARunContext(
            config=path_a_config,
            data_loader=data_loader,
            alpha_engine=alpha_engine,
            risk_model=risk_model,
            optimizer=optimizer,
            error_engine=error_engine,
            error_bridge=None,
        )
        
        test_result = run_path_a_backtest(context)
        
        # 計算績效指標
        from jgod.performance.attribution_engine import PerformanceEngine
        from jgod.performance.performance_types import PerformanceEngineRequest
        
        performance_engine = PerformanceEngine(periods_per_year=252, risk_free_rate=0.0)
        perf_request = PerformanceEngineRequest.from_path_a_result(
            test_result,
            benchmark_returns=None,
            factor_returns=None,
            sector_map=None,
        )
        perf_result = performance_engine.compute_full_report(perf_request)
        
        # 提取績效指標
        summary = perf_result.summary
        sharpe_ratio = summary.sharpe
        max_drawdown = summary.max_drawdown
        total_return = summary.total_return
        turnover_rate = summary.turnover_annualized
        tracking_error = summary.tracking_error
        information_ratio = summary.information_ratio
        
        # Step 4 - Apply Governance Rules (簡化版，目前返回空列表)
        governance_events = self._apply_governance_rules(
            window_result=None,  # TODO: pass actual window_result in Step B3
            config=config
        )
        
        return PathBWindowResult(
            window_id=window_id,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
            train_result=train_result,
            test_result=test_result,
            governance_events=governance_events,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            total_return=total_return,
            turnover_rate=turnover_rate,
            tracking_error=tracking_error,
            information_ratio=information_ratio,
            factor_attribution=None,  # TODO: extract factor attribution in future
        )
    
    def _get_or_create_data_loader(self, config: PathBConfig) -> PathADataLoader:
        """取得或建立 data loader"""
        if self.data_loader is not None:
            return self.data_loader
        
        # 根據 config 建立 data loader（重用 build_orchestrator 的邏輯，但避免循環導入）
        # 直接複製 build_orchestrator 中的 data loader 建立邏輯
        if config.mode == "basic":
            if config.data_source == "mock":
                from jgod.path_a.mock_data_loader import MockConfig, MockPathADataLoader
                mock_config = MockConfig(seed=123)
                return MockPathADataLoader(config=mock_config)
            elif config.data_source == "finmind":
                from jgod.path_a.finmind_data_loader import FinMindPathADataLoader
                return FinMindPathADataLoader()
        elif config.mode == "extreme":
            if config.data_source == "mock":
                from jgod.path_a.mock_data_loader_extreme import (
                    MockPathADataLoaderExtreme,
                    MockConfigExtreme,
                )
                mock_config_extreme = MockConfigExtreme(seed=123)
                return MockPathADataLoaderExtreme(config=mock_config_extreme)
            elif config.data_source == "finmind":
                from jgod.path_a.finmind_data_loader_extreme import (
                    FinMindPathADataLoaderExtreme,
                    FinMindLoaderConfigExtreme,
                )
                config_extreme = FinMindLoaderConfigExtreme(
                    cache_enabled=True,
                    use_parquet_cache=True,
                    fallback_to_mock_extreme=True,
                )
                return FinMindPathADataLoaderExtreme(config=config_extreme)
        
        raise ValueError(f"Unsupported data_source or mode: {config.data_source}, {config.mode}")
    
    def _get_or_create_engines(self, config: PathBConfig) -> Tuple:
        """取得或建立 alpha engine, risk model, optimizer"""
        # 如果提供了 factory，使用 factory
        if self.alpha_engine_factory and self.risk_model_factory and self.optimizer_factory:
            alpha_engine = self.alpha_engine_factory()
            risk_model = self.risk_model_factory()
            optimizer = self.optimizer_factory()
            return alpha_engine, risk_model, optimizer
        
        # 否則，根據 mode 建立引擎（直接複製 build_orchestrator 的邏輯）
        from jgod.alpha_engine.alpha_engine import AlphaEngine
        from jgod.risk.risk_model import MultiFactorRiskModel
        from jgod.optimizer.optimizer_core import OptimizerCore
        from jgod.optimizer.optimizer_config import OptimizerConfig
        
        if config.mode == "basic":
            alpha_engine = AlphaEngine(
                enable_micro_momentum=False,
                factor_weights=None
            )
            risk_model = MultiFactorRiskModel(factor_names=None)
        elif config.mode == "extreme":
            from jgod.alpha_engine.alpha_engine_extreme import AlphaEngineExtreme, AlphaEngineExtremeConfig
            from jgod.risk.risk_model_extreme import MultiFactorRiskModelExtreme, RiskModelExtremeConfig
            
            alpha_engine = AlphaEngineExtreme(config=AlphaEngineExtremeConfig())
            risk_model = MultiFactorRiskModelExtreme(config=RiskModelExtremeConfig())
        else:
            raise ValueError(f"Unsupported mode: {config.mode}")
        
        optimizer = OptimizerCore(config=OptimizerConfig())
        
        return alpha_engine, risk_model, optimizer
    
    def _apply_governance_rules(
        self,
        window_result: Optional[PathBWindowResult],
        config: PathBConfig
    ) -> List[Dict[str, Any]]:
        """
        套用 Governance Rules 並記錄觸發事件
        
        Args:
            window_result: Window 結果（可選，用於分析）
            config: Path B 配置
        
        Returns:
            List of governance events
        """
        governance_events = []
        
        if not config.governance_rules:
            return governance_events
        
        # TODO: Check Alpha Sunset
        # if "alpha_sunset" in config.governance_rules:
        #     ...
        
        # TODO: Check Kill Switch
        # if "kill_switch" in config.governance_rules:
        #     ...
        
        # TODO: Check Regime Switch
        # if "regime_manager" in config.governance_rules:
        #     ...
        
        return governance_events
    
    def _compute_summary(
        self,
        window_results: List[PathBWindowResult]
    ) -> Dict[str, Any]:
        """
        計算彙總統計
        
        Args:
            window_results: 所有 window 結果
        
        Returns:
            彙總統計字典
        """
        if not window_results:
            return {
                "num_windows": 0,
            }
        
        # Extract metrics
        sharpe_ratios = [w.sharpe_ratio for w in window_results if pd.notna(w.sharpe_ratio)]
        max_drawdowns = [w.max_drawdown for w in window_results if pd.notna(w.max_drawdown)]
        total_returns = [w.total_return for w in window_results if pd.notna(w.total_return)]
        turnover_rates = [w.turnover_rate for w in window_results if pd.notna(w.turnover_rate)]
        
        summary = {
            "num_windows": len(window_results),
        }
        
        # Average metrics
        if sharpe_ratios:
            summary["avg_sharpe"] = float(np.mean(sharpe_ratios))
            summary["sharpe_std"] = float(np.std(sharpe_ratios))
            summary["sharpe_min"] = float(np.min(sharpe_ratios))
            summary["sharpe_max"] = float(np.max(sharpe_ratios))
        
        if max_drawdowns:
            summary["avg_max_drawdown"] = float(np.mean(max_drawdowns))
            summary["worst_drawdown"] = float(np.min(max_drawdowns))
        
        if total_returns:
            summary["avg_total_return"] = float(np.mean(total_returns))
        
        if turnover_rates:
            summary["avg_turnover_rate"] = float(np.mean(turnover_rates))
        
        # TODO: Add more summary statistics
        # - Alpha Stability Score
        # - Window consistency metrics
        
        return summary
    
    def _analyze_governance(
        self,
        window_results: List[PathBWindowResult],
        config: PathBConfig
    ) -> Dict[str, Any]:
        """
        分析 Governance Rules 觸發模式
        
        Args:
            window_results: 所有 window 結果
            config: Path B 配置
        
        Returns:
            Governance 分析字典
        """
        # TODO: Analyze governance rule triggers
        # - Count triggers per rule
        # - Analyze market conditions when triggered
        # - Evaluate rule effectiveness
        
        return {
            # TODO: Add governance analysis
        }
    
    def _export_results(
        self,
        result: PathBRunResult
    ) -> List[str]:
        """
        匯出結果檔案
        
        Args:
            result: Path B 執行結果
        
        Returns:
            輸出檔案路徑列表
        """
        # TODO: Export results to files
        # - window_results.csv
        # - governance_events.csv
        # - alpha_stability_report.md
        # - regime_analysis.csv
        # - slippage_beta_analysis.csv
        
        return []

