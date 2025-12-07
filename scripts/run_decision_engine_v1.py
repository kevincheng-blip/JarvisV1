#!/usr/bin/env python3
"""
Run J-GOD Decision & Risk Engine v1

用途：在命令列產生指定日期的目標部位配置表。

使用範例：
    PYTHONPATH=. python scripts/run_decision_engine_v1.py 2024-07-01
    PYTHONPATH=. python scripts/run_decision_engine_v1.py 2024-07-01 --long-budget 0.7 --short-budget 0.15
    PYTHONPATH=. python scripts/run_decision_engine_v1.py 2024-07-01 --max-weight-per-symbol 0.15 --no-short
"""

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from jgod.decision import DecisionEngineV1


def print_portfolio_plan(portfolio_plan, max_positions: int = 20):
    """印出 PortfolioPlan 資訊"""
    print("\n" + "=" * 70)
    print(f"📊 Decision & Risk Engine v1 - Portfolio Plan")
    print("=" * 70)
    print(f"Date:           {portfolio_plan.date.isoformat()}")
    print(f"Universe Size:  {portfolio_plan.universe_size}")
    print(f"Params:         {portfolio_plan.params}")
    
    # Summary
    print("\n" + "-" * 70)
    print("Summary:")
    print("-" * 70)
    summary = portfolio_plan.summary
    print(f"  Total Long  : {summary['total_long_weight']:6.2%}")
    print(f"  Total Short : {summary['total_short_weight']:6.2%}")
    print(f"  Net Exposure: {summary['net_exposure']:6.2%}")
    print(f"  Long Count  : {summary['num_long_positions']}")
    print(f"  Short Count : {summary['num_short_positions']}")
    
    # Positions
    if not portfolio_plan.positions:
        print("\n" + "-" * 70)
        print("⚠️  No positions generated (no candidates meet the criteria)")
        print("-" * 70)
    else:
        print("\n" + "-" * 70)
        print(f"Top Positions (by |weight|, showing first {min(max_positions, len(portfolio_plan.positions))}):")
        print("-" * 70)
        
        for i, pos in enumerate(portfolio_plan.positions[:max_positions], 1):
            side_emoji = "🟢" if pos.side == "LONG" else "🔴"
            risk_emoji = "✅" if pos.risk_flags_summary == "LOW" else "⚠️" if pos.risk_flags_summary == "MEDIUM" else "❌"
            print(f"  {i:2d}) {pos.symbol:6s} {pos.side:5s} w={pos.target_weight:7.2%} score={pos.rank_score:6.2f} risk={pos.risk_flags_summary:6s} {side_emoji} {risk_emoji}")
        
        if len(portfolio_plan.positions) > max_positions:
            print(f"\n  ... and {len(portfolio_plan.positions) - max_positions} more positions")
    
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Run J-GOD Decision & Risk Engine v1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  PYTHONPATH=. python scripts/run_decision_engine_v1.py 2024-07-01
  
  # With custom budgets
  PYTHONPATH=. python scripts/run_decision_engine_v1.py 2024-07-01 --long-budget 0.7 --short-budget 0.15
  
  # With custom max weight per symbol
  PYTHONPATH=. python scripts/run_decision_engine_v1.py 2024-07-01 --max-weight-per-symbol 0.15
  
  # Disable short
  PYTHONPATH=. python scripts/run_decision_engine_v1.py 2024-07-01 --no-short
  
  # With minimum score threshold
  PYTHONPATH=. python scripts/run_decision_engine_v1.py 2024-07-01 --min-score 1.0
        """
    )
    
    parser.add_argument(
        "date",
        type=str,
        help="Date in YYYY-MM-DD format",
    )
    
    parser.add_argument(
        "--long-budget",
        type=float,
        default=0.6,
        help="Long budget (default: 0.6 = 60%%)",
    )
    
    parser.add_argument(
        "--short-budget",
        type=float,
        default=0.2,
        help="Short budget (default: 0.2 = 20%%)",
    )
    
    parser.add_argument(
        "--max-weight-per-symbol",
        type=float,
        default=0.10,
        help="Max weight per symbol (default: 0.10 = 10%%)",
    )
    
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum score threshold (default: 0.0)",
    )
    
    parser.add_argument(
        "--no-short",
        action="store_true",
        help="Disable short positions",
    )
    
    parser.add_argument(
        "--max-positions",
        type=int,
        default=20,
        help="Maximum number of positions to show (default: 20)",
    )
    
    args = parser.parse_args()
    
    # Parse date
    try:
        as_of_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print(f"❌ Error: Invalid date format '{args.date}'. Use YYYY-MM-DD")
        sys.exit(1)
    
    # Initialize Decision Engine
    engine = DecisionEngineV1()
    
    print(f"\n🔍 Generating Portfolio Plan...")
    print(f"   Date:                {args.date}")
    print(f"   Long Budget:         {args.long_budget:.1%}")
    print(f"   Short Budget:        {args.short_budget:.1%}")
    print(f"   Max Weight/Symbol:   {args.max_weight_per_symbol:.1%}")
    print(f"   Min Score:           {args.min_score}")
    print(f"   Allow Short:         {not args.no_short}")
    
    try:
        # Generate portfolio plan
        portfolio_plan = engine.generate_portfolio_for_date(
            date=as_of_date,
            universe=None,  # 取得所有有預測的股票
            long_budget=args.long_budget,
            short_budget=args.short_budget,
            max_weight_per_symbol=args.max_weight_per_symbol,
            min_score=args.min_score,
            allow_short=not args.no_short,
        )
        
        if portfolio_plan.universe_size == 0:
            print(f"\n❌ No prediction data found for {args.date}")
            print(f"   Please check if prediction_snapshots has data for this date.")
            sys.exit(1)
        
        if not portfolio_plan.positions:
            print(f"\n⚠️  No positions generated for {args.date}")
            print(f"   Possible reasons:")
            print(f"   - No candidates meet min_score threshold ({args.min_score})")
            print(f"   - All candidates have insufficient scores")
            sys.exit(0)
        
        # Print portfolio plan
        print_portfolio_plan(portfolio_plan, max_positions=args.max_positions)
        
        print("\n✅ Portfolio plan generated successfully!")
        print("=" * 70 + "\n")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

