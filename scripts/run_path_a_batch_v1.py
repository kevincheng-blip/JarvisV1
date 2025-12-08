#!/usr/bin/env python3
"""
Run J-GOD Path A v1 Backtest - Batch Mode

用途：批次執行多個 Path A 回測實驗，測試不同的風險參數組合。

使用範例：
    PYTHONPATH=. python scripts/run_path_a_batch_v1.py
    PYTHONPATH=. python scripts/run_path_a_batch_v1.py --start-date 2024-01-01 --end-date 2024-06-30
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def run_path_a_backtest(start_date: str, end_date: str, long_budget: float, short_budget: float):
    """執行單一 Path A 回測實驗"""
    cmd = [
        sys.executable,
        str(project_root / "scripts" / "run_path_a_v1.py"),
        start_date,
        end_date,
        "--long-budget", str(long_budget),
        "--short-budget", str(short_budget),
    ]
    
    print(f"\n{'='*70}")
    print(f"執行回測: Long Budget={long_budget:.2f}, Short Budget={short_budget:.2f}")
    print(f"{'='*70}\n")
    
    try:
        result = subprocess.run(cmd, cwd=str(project_root), check=False, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run J-GOD Path A v1 Backtest - Batch Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--start-date",
        type=str,
        default="2024-01-01",
        help="Start date (default: 2024-01-01)",
    )
    
    parser.add_argument(
        "--end-date",
        type=str,
        default="2024-06-30",
        help="End date (default: 2024-06-30)",
    )
    
    args = parser.parse_args()
    
    # 定義多個參數組合
    parameter_combinations = [
        {"lb": 0.5, "sb": 0.10},
        {"lb": 0.6, "sb": 0.15},
        {"lb": 0.7, "sb": 0.15},
        {"lb": 0.8, "sb": 0.20},
    ]
    
    print("\n" + "=" * 70)
    print("🔬 J-GOD Path A v1 - Batch Experiment Runner")
    print("=" * 70)
    print(f"日期範圍: {args.start_date} ~ {args.end_date}")
    print(f"參數組合數: {len(parameter_combinations)}")
    print("=" * 70)
    
    # 執行所有組合
    results = []
    for i, combo in enumerate(parameter_combinations, 1):
        print(f"\n[{i}/{len(parameter_combinations)}] 執行實驗組合...")
        
        success = run_path_a_backtest(
            start_date=args.start_date,
            end_date=args.end_date,
            long_budget=combo["lb"],
            short_budget=combo["sb"],
        )
        
        results.append({
            "combo": combo,
            "success": success,
        })
    
    # 總結
    print("\n" + "=" * 70)
    print("📊 Batch Experiment Summary")
    print("=" * 70)
    
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print(f"總實驗數: {len(results)}")
    print(f"成功: {successful}")
    print(f"失敗: {failed}")
    
    print(f"\n實驗組合:")
    for i, result in enumerate(results, 1):
        status = "✅" if result["success"] else "❌"
        combo = result["combo"]
        print(f"  {i}. {status} Long={combo['lb']:.2f}, Short={combo['sb']:.2f}")
    
    print("\n" + "=" * 70)
    print("✅ Batch complete. Use run_policy_log_reader_v1.py to rank experiments.")
    print("=" * 70 + "\n")
    
    # 如果有失敗的實驗，返回非零退出碼
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

