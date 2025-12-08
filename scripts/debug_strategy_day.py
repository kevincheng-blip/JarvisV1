#!/usr/bin/env python3
"""
Debug Strategy Engine for a specific date

用途：檢查 Strategy Engine 是否為指定日期產生任何 signals。

檢查項目：
- Universe size
- Long signals 前 10 檔（symbol, score）
- Short signals 前 10 檔（symbol, score）
- 若皆為空，印出詳細原因提示
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from jgod.strategy import StrategyEngineV1


def main():
    parser = argparse.ArgumentParser(
        description="Debug Strategy Engine for a specific date",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        help="Maximum number of long candidates (default: 30)",
    )
    
    parser.add_argument(
        "--short-limit",
        type=int,
        default=30,
        help="Maximum number of short candidates (default: 30)",
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
        help="Disable short signals",
    )
    
    args = parser.parse_args()
    
    # Parse date
    try:
        as_of_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print(f"❌ Error: Invalid date format '{args.date}'. Use YYYY-MM-DD")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print(f"🔍 Debug Strategy Engine - {args.date}")
    print("=" * 70)
    
    # Initialize Strategy Engine
    engine = StrategyEngineV1()
    
    print(f"\n參數設定:")
    print(f"  Long Limit:          {args.long_limit}")
    print(f"  Short Limit:         {args.short_limit}")
    print(f"  Min Score:           {args.min_score}")
    print(f"  Allow Short:         {not args.no_short}")
    
    try:
        # Generate signals
        signal_set = engine.generate_signals_for_date(
            date=as_of_date,
            universe=None,
            long_limit=args.long_limit,
            short_limit=args.short_limit,
            min_score=args.min_score,
            allow_short=not args.no_short,
        )
        
        print(f"\n結果:")
        print(f"  Universe Size:      {signal_set.universe_size}")
        print(f"  Long Candidates:    {len(signal_set.long_candidates)}")
        print(f"  Short Candidates:   {len(signal_set.short_candidates)}")
        
        # List long signals
        if signal_set.long_candidates:
            print(f"\nLong Signals (前 {min(10, len(signal_set.long_candidates))} 檔):")
            for i, sig in enumerate(signal_set.long_candidates[:10], 1):
                print(f"  {i:2d}) {sig.symbol:6s} score={sig.base_score:6.2f} rank={sig.rank_score:6.2f} "
                      f"side={sig.side:5s} risk={sig.risk_flags_summary}")
            if len(signal_set.long_candidates) > 10:
                print(f"  ... and {len(signal_set.long_candidates) - 10} more")
        else:
            print(f"\n⚠️  No Long Signals")
        
        # List short signals
        if signal_set.short_candidates:
            print(f"\nShort Signals (前 {min(10, len(signal_set.short_candidates))} 檔):")
            for i, sig in enumerate(signal_set.short_candidates[:10], 1):
                print(f"  {i:2d}) {sig.symbol:6s} score={sig.base_score:6.2f} rank={sig.rank_score:6.2f} "
                      f"side={sig.side:5s} risk={sig.risk_flags_summary}")
            if len(signal_set.short_candidates) > 10:
                print(f"  ... and {len(signal_set.short_candidates) - 10} more")
        else:
            print(f"\n⚠️  No Short Signals")
        
        # Diagnostic
        print(f"\n" + "-" * 70)
        if signal_set.universe_size == 0:
            print("❌ 診斷：Universe 為空（沒有 Prediction 資料）")
            print("  解決方案：執行 backfill_predictions 補齊該日期的預測資料")
        elif len(signal_set.long_candidates) == 0 and len(signal_set.short_candidates) == 0:
            print("❌ 診斷：Strategy Engine 沒有產生任何 signals")
            print("  可能原因：")
            print(f"  - Min Score 條件過嚴格（目前：{args.min_score}）")
            print(f"  - 所有 Prediction 的 score 都低於門檻")
            print(f"  - Prediction 資料存在但 signal/verdict 不符合策略規則")
        elif len(signal_set.long_candidates) == 0:
            print("⚠️  診斷：沒有 Long Signals")
            print("  可能原因：")
            print(f"  - Min Score 條件過嚴格（目前：{args.min_score}）")
            print(f"  - 所有 Prediction 的 signal 都不是 BUY/STRONG_BUY")
        elif len(signal_set.short_candidates) == 0 and not args.no_short:
            print("⚠️  診斷：沒有 Short Signals")
            print("  可能原因：")
            print(f"  - 所有 Prediction 的 signal 都不是 SHORT")
            print(f"  - Allow Short 為 False")
        else:
            print("✅ 診斷：Strategy Engine 正常運作，有產生 signals")
        print("-" * 70)
        
    except Exception as e:
        print(f"\n❌ Error:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

