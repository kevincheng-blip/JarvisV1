#!/usr/bin/env python3
"""
Debug Prediction DB for a specific date

用途：檢查 Prediction DB 是否有指定日期的預測資料。

檢查項目：
- 從 prediction_snapshots 讀取資料
- 印出前 20 筆
- 若為空，印出「需要 backfill prediction」提示
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from jgod.storage.db import get_session
from jgod.storage.models import PredictionSnapshot


def main():
    parser = argparse.ArgumentParser(
        description="Debug Prediction DB for a specific date",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "date",
        type=str,
        help="Date in YYYY-MM-DD format",
    )
    
    args = parser.parse_args()
    
    # Parse date
    try:
        as_of_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print(f"❌ Error: Invalid date format '{args.date}'. Use YYYY-MM-DD")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print(f"🔍 Debug Prediction DB - {args.date}")
    print("=" * 70)
    
    try:
        # Query prediction_snapshots
        session_gen = get_session()
        session = next(session_gen)
        
        try:
            predictions = (
                session.query(PredictionSnapshot)
                .filter(PredictionSnapshot.date == as_of_date)
                .order_by(PredictionSnapshot.symbol)
                .all()
            )
            
            print(f"\n結果:")
            print(f"  Total Records:      {len(predictions)}")
            
            if predictions:
                print(f"\n前 {min(20, len(predictions))} 筆預測資料:")
                print(f"{'Symbol':<8} {'Score':<10} {'Signal':<15} {'Verdict':<15} {'Risk Flags':<20}")
                print("-" * 70)
                
                for i, pred in enumerate(predictions[:20], 1):
                    risk_flags_str = "None"
                    if pred.risk_flags_json:
                        risk_flags_str = str(pred.risk_flags_json)[:18] + "..."
                    elif isinstance(pred.risk_flags_json, dict):
                        risk_flags_str = f"{len(pred.risk_flags_json)} flags"
                    
                    print(f"{pred.symbol:<8} "
                          f"{pred.score or 'N/A':<10} "
                          f"{pred.signal or 'N/A':<15} "
                          f"{pred.verdict or 'N/A':<15} "
                          f"{risk_flags_str:<20}")
                
                if len(predictions) > 20:
                    print(f"\n... and {len(predictions) - 20} more records")
                
                # Statistics
                with_score = len([p for p in predictions if p.score is not None])
                with_signal = len([p for p in predictions if p.signal])
                with_verdict = len([p for p in predictions if p.verdict])
                
                print(f"\n統計:")
                print(f"  Records with score:    {with_score}/{len(predictions)}")
                print(f"  Records with signal:   {with_signal}/{len(predictions)}")
                print(f"  Records with verdict:  {with_verdict}/{len(predictions)}")
                
                # Signal distribution
                if with_signal:
                    signal_counts = {}
                    for pred in predictions:
                        if pred.signal:
                            signal_counts[pred.signal] = signal_counts.get(pred.signal, 0) + 1
                    
                    print(f"\nSignal 分布:")
                    for signal, count in sorted(signal_counts.items(), key=lambda x: x[1], reverse=True):
                        print(f"  {signal:<15} : {count}")
                
                # Diagnostic
                print(f"\n" + "-" * 70)
                if with_score == 0:
                    print("❌ 診斷：所有 Prediction 都沒有 score")
                    print("  解決方案：檢查預測引擎是否正常運作")
                elif with_signal == 0:
                    print("❌ 診斷：所有 Prediction 都沒有 signal")
                    print("  解決方案：檢查預測引擎的 signal 生成邏輯")
                else:
                    print("✅ 診斷：Prediction DB 有資料")
                    if with_score < len(predictions) * 0.5:
                        print(f"  ⚠️  但只有 {with_score}/{len(predictions)} 筆有 score，可能影響 Strategy Engine")
                print("-" * 70)
            else:
                print(f"\n❌ 診斷：沒有找到任何預測資料")
                print(f"  日期：{args.date}")
                print(f"  解決方案：執行 backfill_predictions 補齊該日期的預測資料")
                print(f"  範例指令：")
                print(f"    PYTHONPATH=. python scripts/backfill_predictions.py --start-date {args.date} --end-date {args.date}")
        
        finally:
            pass  # get_session() 使用 generator，會自動關閉
        
    except Exception as e:
        print(f"\n❌ Error:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

