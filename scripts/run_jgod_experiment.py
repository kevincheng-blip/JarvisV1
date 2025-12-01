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

# TODO: Import all required modules for initialization
# from jgod.path_a.finmind_loader import FinMindPathADataLoader
# from jgod.alpha_engine.alpha_engine import AlphaEngine
# ... etc


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
        "--notes",
        type=str,
        default=None,
        help="Experiment notes (optional).",
    )
    return parser.parse_args()


def build_orchestrator() -> ExperimentOrchestrator:
    """建立 ExperimentOrchestrator 實例"""
    # TODO: 初始化所有模組
    # 這裡先留骨架，實際實作時需要初始化所有依賴
    
    raise NotImplementedError(
        "build_orchestrator() needs to be implemented with all module dependencies"
    )


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
    orchestrator = build_orchestrator()
    
    # 執行實驗
    print(f"Starting experiment: {config.name}")
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

