#!/usr/bin/env python3
"""
Policy Reward Adapter v1 CLI

用途：從 Path A 回測日誌載入 reward samples，供 RL 模組使用。

使用範例：
    PYTHONPATH=. python scripts/run_policy_reward_adapter_v1.py
    PYTHONPATH=. python scripts/run_policy_reward_adapter_v1.py --start-date 2024-01-01 --end-date 2024-06-30
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from jgod.policy import PolicyScoreConfig, PolicyRewardAdapterV1


def main():
    parser = argparse.ArgumentParser(
        description="Policy Reward Adapter v1 - Load reward samples from Path A backtest logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD)",
    )
    
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date (YYYY-MM-DD)",
    )
    
    parser.add_argument(
        "--min-days",
        type=int,
        help="Minimum number of trading days (overrides default)",
    )
    
    parser.add_argument(
        "--min-trades",
        type=int,
        help="Minimum number of trades (overrides default)",
    )
    
    parser.add_argument(
        "--sharpe-weight",
        type=float,
        default=0.7,
        help="Weight for Sharpe ratio in reward calculation (default: 0.7)",
    )
    
    parser.add_argument(
        "--maxdd-weight",
        type=float,
        default=0.3,
        help="Weight for Max Drawdown in reward calculation (default: 0.3)",
    )
    
    parser.add_argument(
        "--log-path",
        type=str,
        default="data/path_a_backtest_logs.jsonl",
        help="Path to backtest log file (default: data/path_a_backtest_logs.jsonl)",
    )
    
    args = parser.parse_args()
    
    # 構建 PolicyScoreConfig
    score_config = PolicyScoreConfig(
        sharpe_weight=args.sharpe_weight,
        max_dd_weight=args.maxdd_weight,
    )
    
    # 構建 PolicyRewardAdapterV1
    adapter = PolicyRewardAdapterV1(
        log_path=args.log_path,
        score_config=score_config,
    )
    
    print("\n" + "=" * 70)
    print("🎯 Policy Reward Adapter v1")
    print("=" * 70)
    print(f"Log Path:       {args.log_path}")
    if args.start_date:
        print(f"Start Date:     {args.start_date}")
    if args.end_date:
        print(f"End Date:       {args.end_date}")
    print(f"Sharpe Weight:  {args.sharpe_weight}")
    print(f"MaxDD Weight:   {args.maxdd_weight}")
    if args.min_days:
        print(f"Min Days:       {args.min_days}")
    if args.min_trades:
        print(f"Min Trades:     {args.min_trades}")
    print("=" * 70)
    
    try:
        # 載入 samples
        samples = adapter.load_samples(
            start_date=args.start_date,
            end_date=args.end_date,
            min_days=args.min_days,
            min_trades=args.min_trades,
        )
        
        print(f"\n✅ Loaded {len(samples)} reward samples")
        
        if not samples:
            print("\n⚠️  No valid samples found.")
            print("   - Check if log file exists and has valid experiments")
            print("   - Try relaxing --min-days and --min-trades filters")
            sys.exit(0)
        
        # 找出最佳 sample
        best = adapter.find_best_reward(
            start_date=args.start_date,
            end_date=args.end_date,
            min_days=args.min_days,
            min_trades=args.min_trades,
        )
        
        if best:
            print("\n" + "=" * 70)
            print("🏆 Best Reward Sample")
            print("=" * 70)
            print(f"Run ID:                  {best.run_id}")
            print(f"Reward:                  {best.reward:.6f}")
            print(f"\nPerformance Metrics:")
            print(f"  Sharpe Ratio:          {best.sharpe_ratio:.4f}")
            print(f"  Max Drawdown:          {best.max_drawdown:.4f}")
            print(f"  Total Return:          {best.total_return:.4f}")
            print(f"  Win Rate:              {best.win_rate:.4f}")
            print(f"  Days:                  {best.num_days}")
            print(f"  Trades:                {best.num_trades}")
            print(f"\nRisk Config:")
            print(f"  Long Budget:           {best.long_budget:.2f}")
            print(f"  Short Budget:          {best.short_budget:.2f}")
            print(f"  Max Weight/Symbol:     {best.max_weight_per_symbol:.2f}")
            print(f"  Min Score:             {best.min_score:.2f}")
            print(f"  Allow Short:           {best.allow_short}")
            print("=" * 70)
        
        # 顯示前 5 個 samples 的統計
        print(f"\n📊 Top 5 Reward Samples:")
        print("-" * 70)
        print(f"{'Rank':<6} {'Reward':<12} {'Sharpe':<10} {'MaxDD':<10} {'Return':<10} {'Run ID':<20}")
        print("-" * 70)
        for i, sample in enumerate(samples[:5], 1):
            print(
                f"{i:<6} "
                f"{sample.reward:<12.6f} "
                f"{sample.sharpe_ratio:<10.4f} "
                f"{sample.max_drawdown:<10.4f} "
                f"{sample.total_return:<10.4f} "
                f"{sample.run_id:<20}"
            )
        print("=" * 70 + "\n")
        
        print("💡 RL Integration Hint:")
        print("   RL agents can use the 'reward' field from PolicyRewardSample")
        print("   as the fitness value for a given RiskConfig combination.")
        print("   This enables hyperparameter search and policy optimization.")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

