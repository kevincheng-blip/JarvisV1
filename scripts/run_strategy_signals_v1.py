#!/usr/bin/env python3
"""
Run J-GOD Strategy & Signal Engine v1

用途：在命令列產生指定日期的多空信號清單。

使用範例：
    PYTHONPATH=. python scripts/run_strategy_signals_v1.py 2024-07-01
    PYTHONPATH=. python scripts/run_strategy_signals_v1.py 2024-07-01 --long-limit 50 --short-limit 20
    PYTHONPATH=. python scripts/run_strategy_signals_v1.py 2024-07-01 --min-score 1.0 --no-short
"""

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from jgod.strategy import StrategyEngineV1


def print_signal_set(signal_set):
    """印出 DailySignalSet 資訊"""
    print("\n" + "=" * 70)
    print(f"📊 Strategy & Signal Engine v1 - Daily Signal Set")
    print("=" * 70)
    print(f"Date:           {signal_set.date.isoformat()}")
    print(f"Universe Size:  {signal_set.universe_size}")
    print(f"Params:         {signal_set.params}")
    
    # Long 清單
    print("\n" + "-" * 70)
    print(f"🟢 Long Top {len(signal_set.long_candidates)} (ranked by score):")
    print("-" * 70)
    
    if not signal_set.long_candidates:
        print("  (No long candidates)")
    else:
        for i, sig in enumerate(signal_set.long_candidates, 1):
            risk_emoji = "✅" if sig.risk_flags_summary == "LOW" else "⚠️" if sig.risk_flags_summary == "MEDIUM" else "❌"
            print(f"  {i:2d}) {sig.symbol:6s} {sig.side:5s} score={sig.rank_score:6.2f} risk={sig.risk_flags_summary:6s} {risk_emoji}")
            print(f"      raw_signal={sig.raw_signal}")
    
    # Short 清單
    if signal_set.params.get("allow_short", True):
        print("\n" + "-" * 70)
        print(f"🔴 Short Top {len(signal_set.short_candidates)} (ranked by score):")
        print("-" * 70)
        
        if not signal_set.short_candidates:
            print("  (No short candidates)")
        else:
            for i, sig in enumerate(signal_set.short_candidates, 1):
                risk_emoji = "✅" if sig.risk_flags_summary == "LOW" else "⚠️" if sig.risk_flags_summary == "MEDIUM" else "❌"
                print(f"  {i:2d}) {sig.symbol:6s} {sig.side:5s} score={sig.rank_score:6.2f} risk={sig.risk_flags_summary:6s} {risk_emoji}")
                print(f"      raw_signal={sig.raw_signal}")
    
    # Summary
    print("\n" + "-" * 70)
    print("Summary Statistics:")
    print("-" * 70)
    
    long_summary = signal_set.get_long_summary()
    print(f"\n  Long:")
    print(f"    Count:     {long_summary['count']}")
    if long_summary['count'] > 0:
        print(f"    Avg Score: {long_summary['avg_score']:.2f}")
        print(f"    Max Score: {long_summary['max_score']:.2f}")
        print(f"    Min Score: {long_summary['min_score']:.2f}")
    
    if signal_set.params.get("allow_short", True):
        short_summary = signal_set.get_short_summary()
        print(f"\n  Short:")
        print(f"    Count:     {short_summary['count']}")
        if short_summary['count'] > 0:
            print(f"    Avg Score: {short_summary['avg_score']:.2f}")
            print(f"    Max Score: {short_summary['max_score']:.2f}")
            print(f"    Min Score: {short_summary['min_score']:.2f}")
    
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Run J-GOD Strategy & Signal Engine v1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  PYTHONPATH=. python scripts/run_strategy_signals_v1.py 2024-07-01
  
  # With custom limits
  PYTHONPATH=. python scripts/run_strategy_signals_v1.py 2024-07-01 --long-limit 50 --short-limit 20
  
  # With minimum score threshold
  PYTHONPATH=. python scripts/run_strategy_signals_v1.py 2024-07-01 --min-score 1.0
  
  # Disable short list
  PYTHONPATH=. python scripts/run_strategy_signals_v1.py 2024-07-01 --no-short
        """
    )
    
    parser.add_argument(
        "date",
        type=str,
        help="Date in YYYY-MM-DD format",
    )
    
    parser.add_argument(
        "--long-limit",
        type=int,
        default=30,
        help="Long candidates limit (default: 30)",
    )
    
    parser.add_argument(
        "--short-limit",
        type=int,
        default=30,
        help="Short candidates limit (default: 30)",
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
        help="Disable short list generation",
    )
    
    args = parser.parse_args()
    
    # Parse date
    try:
        as_of_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print(f"❌ Error: Invalid date format '{args.date}'. Use YYYY-MM-DD")
        sys.exit(1)
    
    # Initialize Strategy Engine
    engine = StrategyEngineV1()
    
    print(f"\n🔍 Generating Strategy Signals...")
    print(f"   Date:       {args.date}")
    print(f"   Long Limit: {args.long_limit}")
    print(f"   Short Limit: {args.short_limit}")
    print(f"   Min Score:  {args.min_score}")
    print(f"   Allow Short: {not args.no_short}")
    
    try:
        # Generate signals
        signal_set = engine.generate_signals_for_date(
            date=as_of_date,
            universe=None,  # 取得所有有預測的股票
            long_limit=args.long_limit,
            short_limit=args.short_limit,
            min_score=args.min_score,
            allow_short=not args.no_short,
        )
        
        if signal_set.universe_size == 0:
            print(f"\n❌ No prediction data found for {args.date}")
            print(f"   Please check if prediction_snapshots has data for this date.")
            sys.exit(1)
        
        # Print signal set
        print_signal_set(signal_set)
        
        print("\n✅ Strategy signals generated successfully!")
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

