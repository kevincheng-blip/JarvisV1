#!/usr/bin/env python3
"""
Debug Decision Engine for a specific date

用途：檢查 Decision Engine 是否為指定日期產生任何部位。

檢查項目：
- Universe size
- Long positions 數量與 symbol 列表
- Short positions 數量與 symbol 列表
- 若全為 0，印出詳細原因提示
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from jgod.decision import DecisionEngineV1


def main():
    parser = argparse.ArgumentParser(
        description="Debug Decision Engine for a specific date",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        help="Long budget (default: 0.6)",
    )
    
    parser.add_argument(
        "--short-budget",
        type=float,
        default=0.2,
        help="Short budget (default: 0.2)",
    )
    
    parser.add_argument(
        "--max-weight-per-symbol",
        type=float,
        default=0.10,
        help="Max weight per symbol (default: 0.10)",
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
    
    args = parser.parse_args()
    
    # Parse date
    try:
        as_of_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print(f"❌ Error: Invalid date format '{args.date}'. Use YYYY-MM-DD")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print(f"🔍 Debug Decision Engine - {args.date}")
    print("=" * 70)
    
    # Initialize Decision Engine
    engine = DecisionEngineV1()
    
    print(f"\n參數設定:")
    print(f"  Long Budget:         {args.long_budget}")
    print(f"  Short Budget:        {args.short_budget}")
    print(f"  Max Weight/Symbol:   {args.max_weight_per_symbol}")
    print(f"  Min Score:           {args.min_score}")
    print(f"  Allow Short:         {not args.no_short}")
    
    try:
        # Generate portfolio plan
        portfolio_plan = engine.generate_portfolio_for_date(
            date=as_of_date,
            universe=None,
            long_budget=args.long_budget,
            short_budget=args.short_budget,
            max_weight_per_symbol=args.max_weight_per_symbol,
            min_score=args.min_score,
            allow_short=not args.no_short,
        )
        
        print(f"\n結果:")
        print(f"  Universe Size:      {portfolio_plan.universe_size}")
        print(f"  Long Positions:     {len([p for p in portfolio_plan.positions if p.side == 'LONG'])}")
        print(f"  Short Positions:    {len([p for p in portfolio_plan.positions if p.side == 'SHORT'])}")
        print(f"  Total Positions:    {len(portfolio_plan.positions)}")
        
        # Check summary
        summary = portfolio_plan.summary
        print(f"\nSummary:")
        print(f"  Total Long Weight:  {summary.get('total_long_weight', 0):.4f}")
        print(f"  Total Short Weight: {summary.get('total_short_weight', 0):.4f}")
        print(f"  Net Exposure:       {summary.get('net_exposure', 0):.4f}")
        
        # List positions
        long_positions = [p for p in portfolio_plan.positions if p.side == "LONG"]
        short_positions = [p for p in portfolio_plan.positions if p.side == "SHORT"]
        
        if long_positions:
            print(f"\nLong Positions ({len(long_positions)}):")
            for i, pos in enumerate(long_positions[:20], 1):
                print(f"  {i:2d}) {pos.symbol:6s} weight={pos.target_weight:7.2%} score={pos.rank_score:6.2f} risk={pos.risk_flags_summary}")
            if len(long_positions) > 20:
                print(f"  ... and {len(long_positions) - 20} more")
        else:
            print(f"\n⚠️  No Long Positions")
        
        if short_positions:
            print(f"\nShort Positions ({len(short_positions)}):")
            for i, pos in enumerate(short_positions[:20], 1):
                print(f"  {i:2d}) {pos.symbol:6s} weight={pos.target_weight:7.2%} score={pos.rank_score:6.2f} risk={pos.risk_flags_summary}")
            if len(short_positions) > 20:
                print(f"  ... and {len(short_positions) - 20} more")
        else:
            print(f"\n⚠️  No Short Positions")
        
        # Diagnostic
        print(f"\n" + "-" * 70)
        if portfolio_plan.universe_size == 0:
            print("❌ 診斷：Universe 為空（沒有 Prediction 資料）")
        elif len(portfolio_plan.positions) == 0:
            print("❌ 診斷：沒有產生任何部位")
            print("  可能原因：")
            print(f"  - Min Score 條件過嚴格（目前：{args.min_score}）")
            print(f"  - Strategy Engine 沒有產生足夠的 signals")
            print(f"  - 所有候選標的都被過濾掉")
        elif len(long_positions) == 0 and not args.no_short:
            print("⚠️  診斷：沒有 Long 部位")
            print("  可能原因：")
            print(f"  - Min Score 條件過嚴格（目前：{args.min_score}）")
            print(f"  - Long Budget 設為 0")
        elif len(short_positions) == 0 and not args.no_short:
            print("⚠️  診斷：沒有 Short 部位")
            print("  可能原因：")
            print(f"  - Short Budget 設為 0")
            print(f"  - Allow Short 為 False")
        else:
            print("✅ 診斷：Decision Engine 正常運作，有產生部位")
        print("-" * 70)
        
    except Exception as e:
        print(f"\n❌ Error:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

