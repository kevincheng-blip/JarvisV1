#!/usr/bin/env python
"""
Run a complete J-GOD experiment (Path A + Performance + Diagnosis).

Usage example:

    python scripts/run_jgod_experiment.py \
        --name demo_2024H1 \
        --start-date 2024-01-01 \
        --end-date 2024-06-30 \
        --rebalance-frequency M \
        --universe 2330.TW,2317.TW,2454.TW \
        --data-source finmind

This script uses ExperimentOrchestrator to run a complete experiment pipeline.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

# J-GOD modules
from jgod.experiments import ExperimentOrchestrator, ExperimentConfig

# Data loaders
from jgod.path_a.mock_data_loader import MockPathADataLoader
# TODO: 之後接 FinMindPathADataLoader
# from jgod.path_a.finmind_loader import FinMindPathADataLoader
# from FinMind.data import DataLoader as FinMindClient

# Core engines
from jgod.alpha_engine.alpha_engine import AlphaEngine
from jgod.risk.risk_model import MultiFactorRiskModel
# Path A backtest 目前使用 OptimizerCore v1，所以我們先用 v1
from jgod.optimizer.optimizer_core import OptimizerCore
from jgod.optimizer.optimizer_config import OptimizerConfig
# TODO: 未來升級到 OptimizerCoreV2
# from jgod.optimizer.optimizer_core_v2 import OptimizerCoreV2
from jgod.execution.execution_engine import ExecutionEngine
from jgod.execution.execution_models import FixedSlippageModel
from jgod.execution.cost_model import DefaultCostModel
from jgod.performance.attribution_engine import PerformanceEngine
from jgod.diagnostics.diagnosis_engine import DiagnosisEngine

# Knowledge & Learning
from jgod.knowledge.knowledge_brain import KnowledgeBrain
from jgod.learning.error_learning_engine import ErrorLearningEngine


def parse_args() -> argparse.Namespace:
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description="Run a complete J-GOD experiment (Path A + Performance + Diagnosis)."
    )
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Experiment name (used in output directory).",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Experiment start date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="Experiment end date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--rebalance-frequency",
        type=str,
        default="M",
        choices=["D", "W", "M"],
        help="Rebalance frequency: D (daily), W (weekly), M (monthly). Default: M.",
    )
    parser.add_argument(
        "--universe",
        type=str,
        required=True,
        help="Comma-separated list of symbols (e.g., '2330.TW,2317.TW,2454.TW').",
    )
    parser.add_argument(
        "--data-source",
        type=str,
        default="finmind",
        choices=["finmind", "mock"],
        help="Data source: finmind or mock. Default: finmind.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="basic",
        choices=["basic", "extreme"],
        help="Execution mode: basic (standard modules) or extreme (professional-grade modules). Default: basic.",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default=None,
        help="Experiment notes (optional).",
    )
    return parser.parse_args()


def build_orchestrator(data_source: str = "mock", mode: str = "basic") -> ExperimentOrchestrator:
    """建立 ExperimentOrchestrator 實例
    
    Args:
        data_source: 資料來源，"mock" 或 "finmind"
        mode: 執行模式，"basic" 或 "extreme"
    
    Returns:
        ExperimentOrchestrator 實例
    
    Raises:
        ValueError: 如果 data_source 或 mode 不支援
    """
    # =================================================================
    # (A) 選擇 DataLoader
    # =================================================================
    if mode == "basic":
        if data_source == "mock":
            from jgod.path_a.mock_data_loader import MockConfig
            mock_config = MockConfig(seed=123)
            data_loader = MockPathADataLoader(config=mock_config)
        elif data_source == "finmind":
            from jgod.path_a.finmind_data_loader import FinMindPathADataLoader
            
            try:
                data_loader = FinMindPathADataLoader()
            except Exception as e:
                raise ValueError(
                    f"Failed to initialize FinMind data loader: {e}. "
                    "Please ensure FINMIND_TOKEN is set in environment variables, "
                    "or use --data-source mock for testing."
                )
        else:
            raise ValueError(
                f"Unsupported data_source: {data_source}. "
                "Must be 'mock' or 'finmind'."
            )
    elif mode == "extreme":
        if data_source == "mock":
            from jgod.path_a.mock_data_loader_extreme import (
                MockPathADataLoaderExtreme,
                MockConfigExtreme,
                VolatilityRegime,
            )
            mock_config_extreme = MockConfigExtreme(seed=123)
            data_loader = MockPathADataLoaderExtreme(config=mock_config_extreme)
        elif data_source == "finmind":
            from jgod.path_a.finmind_data_loader_extreme import (
                FinMindPathADataLoaderExtreme,
                FinMindLoaderConfigExtreme,
            )
            
            try:
                config_extreme = FinMindLoaderConfigExtreme(
                    cache_enabled=True,
                    use_parquet_cache=True,
                    fallback_to_mock_extreme=True,
                )
                data_loader = FinMindPathADataLoaderExtreme(config=config_extreme)
            except Exception as e:
                raise ValueError(
                    f"Failed to initialize FinMind Extreme data loader: {e}. "
                    "Please ensure FINMIND_TOKEN is set in environment variables, "
                    "or use --data-source mock for testing."
                )
        else:
            raise NotImplementedError(
                f"EXTREME mode currently supports only 'mock' or 'finmind' data sources, "
                f"got: {data_source}"
            )
    else:
        raise ValueError(
            f"Unsupported mode: {mode}. Must be 'basic' or 'extreme'."
        )
    
    # =================================================================
    # (B) 初始化 Knowledge + Error Engine
    # =================================================================
    knowledge_brain = KnowledgeBrain(
        path="knowledge_base/jgod_knowledge_v1.jsonl"
    )
    
    error_learning_engine = ErrorLearningEngine(
        draft_output_path="knowledge_base/jgod_knowledge_drafts.jsonl",
        report_output_dir="error_logs/reports"
    )
    
    # =================================================================
    # (C) 初始化 Alpha / Risk / Optimizer
    # =================================================================
    if mode == "basic":
        alpha_engine = AlphaEngine(
            enable_micro_momentum=False,
            factor_weights=None
        )
    elif mode == "extreme":
        from jgod.alpha_engine.alpha_engine_extreme import (
            AlphaEngineExtreme,
            AlphaEngineExtremeConfig,
        )
        alpha_engine = AlphaEngineExtreme(
            config=AlphaEngineExtremeConfig()
        )
    
    if mode == "basic":
        risk_model = MultiFactorRiskModel(
            factor_names=None  # 使用預設標準因子
        )
    elif mode == "extreme":
        from jgod.risk.risk_model_extreme import (
            MultiFactorRiskModelExtreme,
            RiskModelExtremeConfig,
        )
        risk_model = MultiFactorRiskModelExtreme(
            config=RiskModelExtremeConfig()
        )
    
    # Path A backtest 目前使用 OptimizerCore v1
    optimizer = OptimizerCore(
        config=OptimizerConfig()
    )
    # TODO: 未來升級到 OptimizerCoreV2
    # optimizer = OptimizerCoreV2(
    #     solver="OSQP",
    #     verbose=False
    # )
    
    # =================================================================
    # (D) 初始化 Execution Engine
    # =================================================================
    if mode == "basic":
        execution_model = FixedSlippageModel(slippage=0.001)
        cost_model = DefaultCostModel(
            commission_rate=0.001425,
            min_commission=20.0,
            tax_rate=0.003
        )
        
        execution_engine = ExecutionEngine(
            execution_model=execution_model,
            cost_model=cost_model,
            broker_adapter=None,  # 使用預設 MockBrokerAdapter
            min_trade_threshold=0.001
        )
    elif mode == "extreme":
        from jgod.execution.execution_engine_extreme import (
            ExecutionEngineExtreme,
            ExecutionEngineExtremeConfig,
        )
        from jgod.execution.cost_model import DefaultCostModel
        
        cost_model = DefaultCostModel(
            commission_rate=0.001425,
            min_commission=20.0,
            tax_rate=0.003
        )
        
        execution_config = ExecutionEngineExtremeConfig(
            damp_threshold=0.1,
            slippage_k=0.001,
            slippage_alpha=0.5,
        )
        
        execution_engine = ExecutionEngineExtreme(
            cost_model=cost_model,
            config=execution_config,
        )
    
    # =================================================================
    # (E) 初始化 Performance Engine
    # =================================================================
    performance_engine = PerformanceEngine(
        periods_per_year=252,
        risk_free_rate=0.0
    )
    
    # =================================================================
    # (F) 初始化 Diagnosis Engine
    # =================================================================
    diagnosis_engine = DiagnosisEngine(
        error_learning_engine=error_learning_engine,
        config={
            "TE_max": 0.05,
            "T_max": 0.20,
            "max_drawdown_threshold": -0.20,
            "sharpe_threshold": 0.5,
            "ir_threshold": 0.2,
        }
    )
    
    # =================================================================
    # (G) 建立 ExperimentOrchestrator
    # =================================================================
    orchestrator = ExperimentOrchestrator(
        data_loader=data_loader,
        alpha_engine=alpha_engine,
        risk_model=risk_model,
        optimizer=optimizer,
        execution_engine=execution_engine,
        performance_engine=performance_engine,
        diagnosis_engine=diagnosis_engine,
        knowledge_brain=knowledge_brain,
        error_learning_engine=error_learning_engine,
    )
    
    return orchestrator


def main() -> None:
    """主函數"""
    args = parse_args()
    
    # 解析 universe
    universe = [s.strip() for s in args.universe.split(",")]
    
    # 建立實驗設定
    config = ExperimentConfig(
        name=args.name,
        start_date=args.start_date,
        end_date=args.end_date,
        rebalance_frequency=args.rebalance_frequency,
        universe=universe,
        data_source=args.data_source,
        notes=args.notes,
    )
    
    # 建立 Orchestrator
    orchestrator = build_orchestrator(data_source=config.data_source, mode=args.mode)
    
    # 執行實驗
    print(f"Starting experiment: {config.name}")
    print(f"Mode: {args.mode}")
    print(f"Period: {config.start_date} to {config.end_date}")
    print(f"Universe: {len(universe)} symbols")
    print()
    
    result = orchestrator.run_experiment(config)
    
    # 輸出摘要
    print("=" * 60)
    print("Experiment Complete!")
    print("=" * 60)
    print()
    
    print("Performance Summary:")
    summary = result.report.summary
    print(f"  Total Return: {summary.get('total_return', 0):.2%}")
    print(f"  CAGR: {summary.get('cagr', 0):.2%}")
    print(f"  Sharpe Ratio: {summary.get('sharpe', 0):.2f}")
    print(f"  Max Drawdown: {summary.get('max_drawdown', 0):.2%}")
    print()
    
    print("Highlights:")
    for highlight in result.report.highlights:
        print(f"  • {highlight}")
    print()
    
    print(f"Files generated: {len(result.report.files_generated)}")
    for file_path in result.report.files_generated:
        print(f"  - {file_path}")
    print()


if __name__ == "__main__":
    main()

