#!/usr/bin/env python3
"""
Run J-GOD Decision AB Test Batch v1

用途：批次執行 Decision Layer AB Test 實驗

使用範例：
    PYTHONPATH=. python scripts/run_decision_ab_batch_v1.py --config config/decision_ab_experiments_v1.json
    PYTHONPATH=. python scripts/run_decision_ab_batch_v1.py --config config/decision_ab_experiments_v1.json --limit 10
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from jgod.decision_ab.runner import DecisionAbRunnerV1
from jgod.decision_ab.models import DecisionAbExperimentConfig
from jgod.decision_ab.storage import AbResultStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_experiment_summary(ab_result):
    """Print summary of an AB experiment result"""
    print(f"\n{ab_result.experiment_id}:")
    print(f"  Sharpe: RAW={ab_result.raw_only.metrics.sharpe:+.4f} | "
          f"DECISION={ab_result.decision_on.metrics.sharpe:+.4f} | "
          f"Delta={ab_result.delta_sharpe:+.4f}")
    print(f"  MaxDD: RAW={ab_result.raw_only.metrics.max_drawdown:.2%} | "
          f"DECISION={ab_result.decision_on.metrics.max_drawdown:.2%} | "
          f"Delta={ab_result.delta_max_drawdown:+.2%}")
    print(f"  Total Return: RAW={ab_result.raw_only.metrics.total_return:.2%} | "
          f"DECISION={ab_result.decision_on.metrics.total_return:.2%} | "
          f"Delta={ab_result.delta_total_return:+.2%}")


def main():
    parser = argparse.ArgumentParser(
        description="Run J-GOD Decision AB Test Batch v1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all experiments from config
  PYTHONPATH=. python scripts/run_decision_ab_batch_v1.py --config config/decision_ab_experiments_v1.json
  
  # Limit to first 10 experiments
  PYTHONPATH=. python scripts/run_decision_ab_batch_v1.py --config config/decision_ab_experiments_v1.json --limit 10
        """
    )
    
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to experiment config JSON file",
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of experiments to run (default: all)",
    )
    
    parser.add_argument(
        "--capital",
        type=float,
        default=1_000_000.0,
        help="Initial capital for backtests (default: 1,000,000)",
    )
    
    args = parser.parse_args()
    
    # Load config file
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_list = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config file: {e}")
        sys.exit(1)
    
    # Parse experiments
    experiments = []
    for exp_dict in config_list:
        try:
            # Parse dates
            exp_dict['start_date'] = exp_dict['start_date']  # Keep as string, Pydantic will parse
            exp_dict['end_date'] = exp_dict['end_date']
            
            exp_config = DecisionAbExperimentConfig(**exp_dict)
            experiments.append(exp_config)
        except Exception as e:
            logger.warning(f"Failed to parse experiment config: {exp_dict.get('experiment_id', 'unknown')}: {e}")
            continue
    
    if not experiments:
        logger.error("No valid experiments found in config file")
        sys.exit(1)
    
    # Apply limit
    if args.limit:
        experiments = experiments[:args.limit]
    
    logger.info(f"Found {len(experiments)} experiments to run")
    
    # Initialize runner
    runner = DecisionAbRunnerV1(initial_capital=args.capital)
    
    # Run experiments
    print("\n" + "=" * 70)
    print("J-GOD Decision AB Test Batch v1")
    print("=" * 70)
    
    results = []
    for i, exp_config in enumerate(experiments, 1):
        print(f"\n[{i}/{len(experiments)}] Running experiment: {exp_config.experiment_id}")
        print(f"  Description: {exp_config.description}")
        print(f"  Period: {exp_config.start_date} to {exp_config.end_date}")
        
        try:
            ab_result = runner.run_experiment(exp_config)
            results.append(ab_result)
            print_experiment_summary(ab_result)
        except Exception as e:
            logger.error(f"Failed to run experiment {exp_config.experiment_id}: {e}", exc_info=True)
            print(f"  ❌ Error: {e}")
            continue
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total experiments: {len(experiments)}")
    print(f"Successful: {len(results)}")
    print(f"Failed: {len(experiments) - len(results)}")
    
    if results:
        print("\nResults summary:")
        for ab_result in results:
            print_experiment_summary(ab_result)
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()

