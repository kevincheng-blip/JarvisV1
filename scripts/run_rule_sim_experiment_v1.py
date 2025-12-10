#!/usr/bin/env python3
"""
Rule Simulation Experiment CLI

Run a rule simulation experiment from command line.
"""

import argparse
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jgod.rule_sim.engine import RuleSimEngineV1
from jgod.rule_sim.storage import RuleSimStorageV1
from jgod.rule_sim.models import (
    RuleSimExperimentConfig,
    RuleSetRef,
    RuleSimTargetType,
)


def main():
    parser = argparse.ArgumentParser(description="Run Rule Simulation Experiment")
    parser.add_argument(
        "--target-type",
        type=str,
        required=True,
        choices=["doctrine_section", "doctrine_file", "alert_rules_yaml"],
        help="Target ruleset type",
    )
    parser.add_argument(
        "--section-id",
        type=str,
        help="Section ID (for doctrine_section)",
    )
    parser.add_argument(
        "--ruleset-id",
        type=str,
        help="Ruleset ID (alternative to section-id)",
    )
    parser.add_argument(
        "--baseline-version",
        type=str,
        help="Baseline version ID",
    )
    parser.add_argument(
        "--variant-version",
        type=str,
        required=True,
        help="Variant version ID (proposal or draft)",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--universe",
        type=str,
        help="Comma-separated list of stock symbols (e.g., '2330,2317,3034')",
    )
    parser.add_argument(
        "--path-a-config-name",
        type=str,
        default="path_a_tw_basic_v1",
        help="Path A config name",
    )
    parser.add_argument(
        "--note",
        type=str,
        help="Optional note for the experiment",
    )
    
    args = parser.parse_args()
    
    # Parse dates
    try:
        start_date = date.fromisoformat(args.start_date)
        end_date = date.fromisoformat(args.end_date)
    except ValueError as e:
        print(f"Error: Invalid date format: {e}")
        sys.exit(1)
    
    # Parse universe
    universe = []
    if args.universe:
        universe = [s.strip() for s in args.universe.split(",") if s.strip()]
    
    # Determine ruleset ID
    ruleset_id = args.ruleset_id or args.section_id
    if not ruleset_id:
        print("Error: Either --section-id or --ruleset-id must be provided")
        sys.exit(1)
    
    # Create ruleset reference
    target_type = RuleSimTargetType(args.target_type)
    ruleset_ref = RuleSetRef(
        id=ruleset_id,
        type=target_type,
    )
    
    # Create experiment config
    from uuid import uuid4
    experiment_id = str(uuid4())
    
    config = RuleSimExperimentConfig(
        experiment_id=experiment_id,
        created_at=datetime.now(),
        created_by="CLI",
        target_ruleset=ruleset_ref,
        baseline_version_id=args.baseline_version,
        variant_version_id=args.variant_version,
        start_date=start_date,
        end_date=end_date,
        universe=universe,
        path_a_config_name=args.path_a_config_name,
        note=args.note,
    )
    
    # Run experiment
    print(f"Starting rule simulation experiment: {experiment_id}")
    print(f"  Target: {ruleset_id} ({target_type.value})")
    print(f"  Baseline: {args.baseline_version or 'production'}")
    print(f"  Variant: {args.variant_version}")
    print(f"  Period: {start_date} to {end_date}")
    print(f"  Universe: {len(universe)} stocks" if universe else "  Universe: default")
    print()
    
    storage = RuleSimStorageV1()
    engine = RuleSimEngineV1(storage=storage)
    
    try:
        report = engine.run_experiment(config)
        
        print("=" * 60)
        print("Experiment Results")
        print("=" * 60)
        print(f"Status: {report.status.status.value}")
        print(f"Recommendation: {report.recommendation}")
        print()
        print("Baseline Metrics:")
        print(f"  Sharpe: {report.baseline_metrics.sharpe:.3f}")
        print(f"  Max Drawdown: {report.baseline_metrics.max_drawdown:.2%}")
        print(f"  Total Return: {report.baseline_metrics.total_return:.2%}")
        print()
        print("Variant Metrics:")
        print(f"  Sharpe: {report.variant_metrics.sharpe:.3f}")
        print(f"  Max Drawdown: {report.variant_metrics.max_drawdown:.2%}")
        print(f"  Total Return: {report.variant_metrics.total_return:.2%}")
        print()
        print("Deltas:")
        print(f"  Sharpe Delta: {report.deltas.sharpe_delta:+.3f}")
        print(f"  Max Drawdown Delta: {report.deltas.max_drawdown_delta:+.2%}")
        print(f"  Total Return Delta: {report.deltas.total_return_delta:+.2%}")
        print()
        print("Key Findings:")
        for finding in report.key_findings:
            print(f"  - {finding}")
        print()
        print(f"Report saved: {experiment_id}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

