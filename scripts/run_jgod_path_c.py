#!/usr/bin/env python
"""
Run a J-GOD Path C validation lab experiment.

This script executes Path C Engine for batch scenario validation by calling
Path B Engine multiple times with different configurations.

Usage example:

    # 使用預設 scenarios
    python scripts/run_jgod_path_c.py \
        --name demo_path_c \
        --output-dir output/path_c

    # 使用自訂 config JSON
    python scripts/run_jgod_path_c.py \
        --name custom_experiment \
        --config path/to/scenarios.json \
        --output-dir output/path_c

Reference:
- spec/JGOD_PathCEngine_Spec.md
- docs/JGOD_PATH_C_STANDARD_v1.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional
import sys

# 確保專案根目錄在 Python 路徑中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from jgod.path_c.path_c_engine import PathCEngine
from jgod.path_c.path_c_types import (
    PathCExperimentConfig,
    PathCScenarioConfig,
)
from jgod.path_c.scenario_presets import (
    get_default_scenarios_for_taiwan_equities,
)


def parse_args() -> argparse.Namespace:
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description="Run a J-GOD Path C validation lab experiment."
    )
    
    # 必填參數
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Experiment name (e.g., 'demo_path_c')",
    )
    
    # 可選參數
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to JSON config file defining scenarios (optional, uses defaults if not provided)",
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/path_c",
        help="Output directory (default: output/path_c)",
    )
    
    return parser.parse_args()


def load_scenarios_from_json(config_path: str) -> List[PathCScenarioConfig]:
    """
    從 JSON 檔案載入 scenarios
    
    Args:
        config_path: JSON 檔案路徑
    
    Returns:
        Scenario 配置列表
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_file, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    
    scenarios = []
    for scenario_data in config_data.get("scenarios", []):
        scenario = PathCScenarioConfig(
            name=scenario_data["name"],
            description=scenario_data.get("description", ""),
            start_date=scenario_data["start_date"],
            end_date=scenario_data["end_date"],
            rebalance_frequency=scenario_data.get("rebalance_frequency", "M"),
            universe=scenario_data["universe"],
            walkforward_window=scenario_data["walkforward_window"],
            walkforward_step=scenario_data["walkforward_step"],
            data_source=scenario_data.get("data_source", "mock"),
            mode=scenario_data.get("mode", "basic"),
            max_drawdown_limit=scenario_data.get("max_drawdown_limit"),
            min_sharpe=scenario_data.get("min_sharpe"),
            max_tracking_error=scenario_data.get("max_tracking_error"),
            max_turnover=scenario_data.get("max_turnover"),
            regime_tag=scenario_data.get("regime_tag"),
            metadata=scenario_data.get("metadata", {}),
        )
        scenarios.append(scenario)
    
    return scenarios


def main():
    """主函數"""
    args = parse_args()
    
    print(f"=== J-GOD Path C Validation Lab ===")
    print(f"Experiment name: {args.name}")
    
    # 載入 scenarios
    if args.config:
        print(f"Loading scenarios from: {args.config}")
        scenarios = load_scenarios_from_json(args.config)
    else:
        print("Using default scenarios")
        scenarios = get_default_scenarios_for_taiwan_equities()
    
    print(f"Total scenarios: {len(scenarios)}")
    
    # 建立實驗配置
    experiment_config = PathCExperimentConfig(
        name=args.name,
        scenarios=scenarios,
        output_dir=args.output_dir,
    )
    
    # 初始化引擎
    engine = PathCEngine()
    
    # 執行實驗
    print("\nStarting experiment...")
    try:
        summary = engine.run_experiment(experiment_config)
        
        # 輸出結果摘要
        print("\n=== Experiment Results ===")
        print(f"Total scenarios: {summary.total_scenarios}")
        print(f"Successful: {summary.successful_scenarios}")
        print(f"Failed: {summary.failed_scenarios}")
        
        if summary.best_scenarios:
            print(f"\nTop 3 scenarios:")
            for i, scenario_name in enumerate(summary.best_scenarios, 1):
                scenario_result = next(
                    (s for s in summary.scenarios if s.scenario.name == scenario_name),
                    None,
                )
                if scenario_result:
                    print(
                        f"  {i}. {scenario_name}: "
                        f"Sharpe={scenario_result.sharpe:.3f}, "
                        f"MaxDD={scenario_result.max_drawdown:.2%}, "
                        f"Breach={scenario_result.governance_breach_ratio:.1%}"
                    )
        
        print(f"\nOutput files:")
        for output_file in summary.output_files:
            print(f"  - {output_file}")
        
        print("\n✅ Experiment completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Experiment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

