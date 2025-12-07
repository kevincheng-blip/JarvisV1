#!/usr/bin/env python3
"""
Debug Script for J-GOD Feature Store v1

用途：在命令列測試 Feature Store 是否正常運作。

使用範例：
    PYTHONPATH=. python scripts/debug_feature_store.py 2330 2024-07-01
    PYTHONPATH=. python scripts/debug_feature_store.py 2330 2024-07-01 --min-count 95
    PYTHONPATH=. python scripts/debug_feature_store.py 2330 2024-07-01 --strict
"""

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from jgod.feature_store import FeatureStore, FeatureStoreError, InsufficientCoverageError


def print_feature_set(feature_set, show_indicators: int = 5):
    """印出 Feature Set 資訊"""
    print("\n" + "=" * 70)
    print(f"📊 Feature Store v1 - Feature Set")
    print("=" * 70)
    print(f"Symbol:     {feature_set.symbol}")
    print(f"Date:       {feature_set.date.isoformat()}")
    print(f"Total:      {feature_set.total_indicators} (expected)")
    print(f"Available:  {feature_set.available_indicators}")
    print(f"Coverage:   {feature_set.coverage_ratio:.2%}")
    
    if feature_set.coverage_warning:
        print(f"⚠️  WARNING: Coverage below minimum threshold!")
    else:
        print(f"✅ Coverage OK")
    
    print("\n" + "-" * 70)
    print(f"Sample Indicators (showing first {show_indicators}):")
    print("-" * 70)
    
    # 顯示前 N 個指標
    for i, ind in enumerate(feature_set.indicators[:show_indicators], 1):
        status_emoji = "✅" if ind.status == "OK" else "❌"
        print(f"\n{i}. {status_emoji} {ind.indicator_code} ({ind.category})")
        print(f"   Status:       {ind.status}")
        if ind.raw_value is not None:
            print(f"   Raw Value:    {ind.raw_value:.6f}")
        if ind.normalized_value is not None:
            print(f"   Normalized:   {ind.normalized_value:.6f}")
        if ind.weight is not None:
            print(f"   Weight:       {ind.weight:.6f}")
    
    if len(feature_set.indicators) > show_indicators:
        print(f"\n... and {len(feature_set.indicators) - show_indicators} more indicators")
    
    # 統計各狀態的指標數
    status_counts = {}
    for ind in feature_set.indicators:
        status = ind.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\n" + "-" * 70)
    print("Status Summary:")
    print("-" * 70)
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="Debug J-GOD Feature Store v1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  PYTHONPATH=. python scripts/debug_feature_store.py 2330 2024-07-01
  
  # With minimum indicator count
  PYTHONPATH=. python scripts/debug_feature_store.py 2330 2024-07-01 --min-count 95
  
  # Strict mode (fail if coverage insufficient)
  PYTHONPATH=. python scripts/debug_feature_store.py 2330 2024-07-01 --strict
  
  # Show more indicators
  PYTHONPATH=. python scripts/debug_feature_store.py 2330 2024-07-01 --show 10
        """
    )
    
    parser.add_argument(
        "symbol",
        type=str,
        help="Stock symbol (e.g., 2330, 2303)",
    )
    
    parser.add_argument(
        "date",
        type=str,
        help="Date in YYYY-MM-DD format",
    )
    
    parser.add_argument(
        "--min-count",
        type=int,
        default=90,
        help="Minimum indicator count (default: 90)",
    )
    
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: fail if coverage < min_count",
    )
    
    parser.add_argument(
        "--show",
        type=int,
        default=5,
        help="Number of sample indicators to show (default: 5)",
    )
    
    args = parser.parse_args()
    
    # Parse date
    try:
        as_of_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print(f"❌ Error: Invalid date format '{args.date}'. Use YYYY-MM-DD")
        sys.exit(1)
    
    # Initialize Feature Store
    feature_store = FeatureStore()
    
    print(f"\n🔍 Querying Feature Store...")
    print(f"   Symbol: {args.symbol}")
    print(f"   Date:   {args.date}")
    print(f"   Min Count: {args.min_count}")
    print(f"   Strict Mode: {args.strict}")
    
    try:
        # Get features
        feature_set = feature_store.get_features(
            symbol=args.symbol,
            date=as_of_date,
            min_indicator_count=args.min_count,
            strict=args.strict,
        )
        
        if feature_set is None:
            print(f"\n❌ No features found for {args.symbol} on {args.date}")
            sys.exit(1)
        
        # Print feature set
        print_feature_set(feature_set, show_indicators=args.show)
        
        # Coverage warning
        if feature_set.coverage_warning:
            print("\n" + "⚠️ " * 35)
            print(f"⚠️  WARNING: Coverage {feature_set.coverage_ratio:.2%} is below minimum {args.min_count} indicators!")
            print(f"⚠️  Available: {feature_set.available_indicators} / {feature_set.total_indicators}")
            print("⚠️ " * 35)
            sys.exit(1)
        else:
            print("\n" + "=" * 70)
            print("✅ Feature Store query successful!")
            print("=" * 70 + "\n")
            sys.exit(0)
        
    except InsufficientCoverageError as e:
        print(f"\n❌ Insufficient Coverage Error:")
        print(f"   {str(e)}")
        sys.exit(1)
    except FeatureStoreError as e:
        print(f"\n❌ Feature Store Error:")
        print(f"   {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected Error:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

