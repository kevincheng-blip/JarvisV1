#!/usr/bin/env python3
"""
Debug Path A Pipeline - Comprehensive Diagnostic

用途：自動依序檢查整個 Path A pipeline，找出問題所在。

檢查流程：
1) 檢查 Prediction DB（若無 → 回報缺資料）
2) 檢查 Strategy Engine（若空 → 回報 score/filter 條件）
3) 檢查 Decision Engine（若空 → 回報 Universe/weights/score 條件）

最後輸出診斷結論。
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
from jgod.storage.db import get_session
from jgod.storage.models import PredictionSnapshot
from jgod.strategy import StrategyEngineV1


def check_prediction_db(date):
    """檢查 Prediction DB"""
    print("\n" + "=" * 70)
    print("STEP 1: 檢查 Prediction DB")
    print("=" * 70)
    
    try:
        session_gen = get_session()
        session = next(session_gen)
        
        try:
            predictions = (
                session.query(PredictionSnapshot)
                .filter(PredictionSnapshot.date == date)
                .all()
            )
            
            if not predictions:
                print(f"❌ 沒有找到任何 Prediction 資料（日期：{date.isoformat()}）")
                return False, "no_predictions"
            
            with_score = len([p for p in predictions if p.score is not None])
            with_signal = len([p for p in predictions if p.signal])
            
            print(f"✅ 找到 {len(predictions)} 筆 Prediction 資料")
            print(f"   - 有 score: {with_score}/{len(predictions)}")
            print(f"   - 有 signal: {with_signal}/{len(predictions)}")
            
            if with_score == 0:
                return False, "no_scores"
            if with_signal == 0:
                return False, "no_signals"
            
            return True, "ok"
        
        finally:
            pass  # get_session() 使用 generator，會自動關閉
    
    except Exception as e:
        print(f"❌ 查詢 Prediction DB 時發生錯誤: {e}")
        return False, "error"


def check_strategy_engine(date, min_score=0.0):
    """檢查 Strategy Engine"""
    print("\n" + "=" * 70)
    print("STEP 2: 檢查 Strategy Engine")
    print("=" * 70)
    
    try:
        engine = StrategyEngineV1()
        signal_set = engine.generate_signals_for_date(
            date=date,
            universe=None,
            long_limit=30,
            short_limit=30,
            min_score=min_score,
            allow_short=True,
        )
        
        print(f"✅ Strategy Engine 執行成功")
        print(f"   - Universe Size: {signal_set.universe_size}")
        print(f"   - Long Candidates: {len(signal_set.long_candidates)}")
        print(f"   - Short Candidates: {len(signal_set.short_candidates)}")
        
        if signal_set.universe_size == 0:
            return False, "empty_universe"
        
        if len(signal_set.long_candidates) == 0 and len(signal_set.short_candidates) == 0:
            return False, "no_signals"
        
        if len(signal_set.long_candidates) > 0:
            print(f"   - Top Long Signal: {signal_set.long_candidates[0].symbol} "
                  f"(score={signal_set.long_candidates[0].base_score:.2f})")
        
        if len(signal_set.short_candidates) > 0:
            print(f"   - Top Short Signal: {signal_set.short_candidates[0].symbol} "
                  f"(score={signal_set.short_candidates[0].base_score:.2f})")
        
        return True, "ok"
    
    except Exception as e:
        print(f"❌ Strategy Engine 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False, "error"


def check_decision_engine(date, min_score=0.0):
    """檢查 Decision Engine"""
    print("\n" + "=" * 70)
    print("STEP 3: 檢查 Decision Engine")
    print("=" * 70)
    
    try:
        engine = DecisionEngineV1()
        portfolio_plan = engine.generate_portfolio_for_date(
            date=date,
            universe=None,
            long_budget=0.6,
            short_budget=0.2,
            max_weight_per_symbol=0.10,
            min_score=min_score,
            allow_short=True,
        )
        
        print(f"✅ Decision Engine 執行成功")
        print(f"   - Universe Size: {portfolio_plan.universe_size}")
        print(f"   - Long Positions: {len([p for p in portfolio_plan.positions if p.side == 'LONG'])}")
        print(f"   - Short Positions: {len([p for p in portfolio_plan.positions if p.side == 'SHORT'])}")
        print(f"   - Total Positions: {len(portfolio_plan.positions)}")
        
        summary = portfolio_plan.summary
        print(f"   - Total Long Weight: {summary.get('total_long_weight', 0):.4f}")
        print(f"   - Total Short Weight: {summary.get('total_short_weight', 0):.4f}")
        
        if portfolio_plan.universe_size == 0:
            return False, "empty_universe"
        
        if len(portfolio_plan.positions) == 0:
            return False, "no_positions"
        
        return True, "ok"
    
    except Exception as e:
        print(f"❌ Decision Engine 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False, "error"


def main():
    parser = argparse.ArgumentParser(
        description="Debug Path A Pipeline - Comprehensive Diagnostic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "date",
        type=str,
        help="Date in YYYY-MM-DD format",
    )
    
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum score threshold (default: 0.0)",
    )
    
    args = parser.parse_args()
    
    # Parse date
    try:
        as_of_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print(f"❌ Error: Invalid date format '{args.date}'. Use YYYY-MM-DD")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print(f"🔍 Path A Pipeline Debug - {args.date}")
    print("=" * 70)
    print(f"Min Score Threshold: {args.min_score}")
    
    # Step 1: Check Prediction DB
    pred_ok, pred_status = check_prediction_db(as_of_date)
    
    if not pred_ok:
        print("\n" + "=" * 70)
        print("📋 診斷結論")
        print("=" * 70)
        
        if pred_status == "no_predictions":
            print("❌ 沒有 Prediction 資料，Path A 無法運作")
            print(f"\n解決方案：")
            print(f"  執行 backfill_predictions 補齊該日期的預測資料")
            print(f"  範例指令：")
            print(f"    PYTHONPATH=. python scripts/backfill_predictions.py \\")
            print(f"      --start-date {args.date} --end-date {args.date}")
        elif pred_status == "no_scores":
            print("❌ Prediction 資料存在，但都沒有 score")
            print(f"\n解決方案：")
            print(f"  檢查預測引擎是否正常運作")
        elif pred_status == "no_signals":
            print("❌ Prediction 資料存在，但都沒有 signal")
            print(f"\n解決方案：")
            print(f"  檢查預測引擎的 signal 生成邏輯")
        
        print("=" * 70 + "\n")
        sys.exit(1)
    
    # Step 2: Check Strategy Engine
    strategy_ok, strategy_status = check_strategy_engine(as_of_date, min_score=args.min_score)
    
    if not strategy_ok:
        print("\n" + "=" * 70)
        print("📋 診斷結論")
        print("=" * 70)
        
        if strategy_status == "empty_universe":
            print("⚠️  Strategy Engine 的 Universe 為空")
            print(f"  可能原因：Prediction 資料存在但不符合查詢條件")
        elif strategy_status == "no_signals":
            print("⚠️  有 Prediction，但 Strategy Engine 產生 0 檔 signals")
            print(f"\n可能原因：")
            print(f"  - Min Score 條件過嚴格（目前：{args.min_score}）")
            print(f"  - 所有 Prediction 的 score 都低於門檻")
            print(f"  - Prediction 的 signal/verdict 不符合策略規則")
            print(f"\n建議：")
            print(f"  - 嘗試降低 --min-score 參數")
            print(f"  - 檢查 Strategy Engine 的 signal 映射規則")
        else:
            print("❌ Strategy Engine 執行失敗")
        
        print("=" * 70 + "\n")
        sys.exit(1)
    
    # Step 3: Check Decision Engine
    decision_ok, decision_status = check_decision_engine(as_of_date, min_score=args.min_score)
    
    # Final Conclusion
    print("\n" + "=" * 70)
    print("📋 診斷結論")
    print("=" * 70)
    
    if not decision_ok:
        if decision_status == "empty_universe":
            print("⚠️  Decision Engine 的 Universe 為空")
        elif decision_status == "no_positions":
            print("⚠️  Strategy 正常，但 Decision Engine 過濾掉全部股票")
            print(f"\n可能原因：")
            print(f"  - Min Score 條件過嚴格（目前：{args.min_score}）")
            print(f"  - Long/Short Budget 設為 0")
            print(f"  - Max Weight Per Symbol 過小，導致無法分配權重")
            print(f"\n建議：")
            print(f"  - 嘗試降低 --min-score 參數")
            print(f"  - 檢查 Decision Engine 的權重分配邏輯")
        else:
            print("❌ Decision Engine 執行失敗")
        print("=" * 70 + "\n")
        sys.exit(1)
    else:
        print("✅ 全部正常，Path A Pipeline 可以正常運作")
        print("   - Prediction DB 有資料")
        print("   - Strategy Engine 產生 signals")
        print("   - Decision Engine 產生部位")
        print("=" * 70 + "\n")
        sys.exit(0)


if __name__ == "__main__":
    main()

