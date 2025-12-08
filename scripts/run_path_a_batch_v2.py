#!/usr/bin/env python3
"""
Run J-GOD Path A v1 Backtest - Batch Mode v2

用途：批次執行多個 Path A 回測實驗，從配置檔讀取實驗參數。

使用範例：
    PYTHONPATH=. python scripts/run_path_a_batch_v2.py
    PYTHONPATH=. python scripts/run_path_a_batch_v2.py --config-file config/path_a_experiments_v1.json --tag "policy_v2_round1"
"""

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from jgod.config.experiment_config_loader import load_experiment_config
from jgod.path_a.path_a_engine_v1 import PathAEngineV1


def run_single_experiment(
    experiment: dict,
    start_date: date,
    end_date: date,
    capital: float,
    tag: Optional[str] = None,
) -> dict:
    """執行單一 Path A 回測實驗"""
    
    # 構建 Decision Config
    decision_config = {
        "long_budget": experiment["long_budget"],
        "short_budget": experiment["short_budget"],
        "max_weight_per_symbol": experiment["max_weight_per_symbol"],
        "min_score": experiment["min_score"],
        "allow_short": experiment["allow_short"],
    }
    
    # 初始化 Path A Engine
    engine = PathAEngineV1(
        initial_capital=capital,
        **decision_config
    )
    
    # 執行回測
    try:
        result = engine.run_backtest(start_date=start_date, end_date=end_date)
        
        # 準備結果摘要
        summary = {
            "name": experiment["name"],
            "run_id": None,  # 會在寫入 log 時產生
            "success": True,
            "result": result,
            "config": decision_config,
        }
        
        return summary
    
    except Exception as e:
        return {
            "name": experiment["name"],
            "run_id": None,
            "success": False,
            "error": str(e),
            "config": decision_config,
        }


def print_experiment_summary(summary: dict, index: int, total: int):
    """印出單一實驗的摘要"""
    name = summary["name"]
    config = summary["config"]
    
    if not summary["success"]:
        print(f"\n  [{index}/{total}] ❌ {name}")
        print(f"      Error: {summary.get('error', 'Unknown error')}")
        return
    
    result = summary["result"]
    metrics = result.metrics
    
    print(f"\n  [{index}/{total}] ✅ {name}")
    print(f"      Config: Long={config['long_budget']:.2f}, Short={config['short_budget']:.2f}, "
          f"MaxW={config['max_weight_per_symbol']:.2f}, MinS={config['min_score']:.2f}")
    print(f"      Sharpe: {metrics.sharpe_ratio:8.4f} | MaxDD: {metrics.max_drawdown:8.2%} | "
          f"Return: {metrics.total_return:8.2%} | WinRate: {metrics.win_rate:8.2%}")
    print(f"      Trades: {metrics.num_long_trades + metrics.num_short_trades} | "
          f"Days: {len(result.daily_equity_curve)}")


def main():
    parser = argparse.ArgumentParser(
        description="Run J-GOD Path A v1 Backtest - Batch Mode v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--config-file",
        type=str,
        default="config/path_a_experiments_v1.json",
        help="Path to experiment config file (default: config/path_a_experiments_v1.json)",
    )
    
    parser.add_argument(
        "--tag",
        type=str,
        help="Experiment tag (optional, for marking this batch)",
    )
    
    args = parser.parse_args()
    
    # 載入配置檔
    try:
        config = load_experiment_config(args.config_file)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error: Invalid config file format: {e}")
        sys.exit(1)
    
    # 解析日期
    try:
        start_date = datetime.strptime(config["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(config["end_date"], "%Y-%m-%d").date()
    except (ValueError, KeyError) as e:
        print(f"❌ Error: Invalid date format in config: {e}")
        sys.exit(1)
    
    capital = float(config.get("capital", 1_000_000))
    experiments = config.get("experiments", [])
    
    if not experiments:
        print("❌ Error: No experiments found in config file")
        sys.exit(1)
    
    # 顯示設定摘要
    print("\n" + "=" * 70)
    print("🔬 J-GOD Path A v1 - Batch Experiment Runner v2")
    print("=" * 70)
    print(f"Config File:    {args.config_file}")
    if args.tag:
        print(f"Experiment Tag: {args.tag}")
    print(f"Date Range:     {config['start_date']} ~ {config['end_date']}")
    print(f"Capital:        {capital:,.2f}")
    print(f"Experiments:    {len(experiments)}")
    print("=" * 70)
    
    # 執行所有實驗
    results = []
    for i, exp in enumerate(experiments, 1):
        print(f"\n[{i}/{len(experiments)}] Running experiment: {exp['name']}...")
        
        summary = run_single_experiment(
            experiment=exp,
            start_date=start_date,
            end_date=end_date,
            capital=capital,
            tag=args.tag,
        )
        
        # 如果是成功的實驗，需要寫入 log（PathAEngineV1 會自動處理）
        # 但我們需要在這裡產生 run_id 並更新 summary
        
        if summary["success"]:
            # 準備 config_params 用於 log（PathAEngineV1 內部會處理）
            # 這裡我們只需要確保引擎已經寫入 log
            pass
        
        results.append(summary)
        print_experiment_summary(summary, i, len(experiments))
    
    # 最終總結
    print("\n" + "=" * 70)
    print("📊 Batch Experiment Summary")
    print("=" * 70)
    
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print(f"Total Experiments: {len(results)}")
    print(f"Successful:        {successful}")
    print(f"Failed:            {failed}")
    
    if successful > 0:
        print("\nSuccessful Experiments:")
        for result in results:
            if result["success"]:
                metrics = result["result"].metrics
                print(f"  ✅ {result['name']}: "
                      f"Sharpe={metrics.sharpe_ratio:.4f}, "
                      f"MaxDD={metrics.max_drawdown:.2%}, "
                      f"Return={metrics.total_return:.2%}")
    
    print("\n" + "=" * 70)
    print("✅ All experiments completed. Logs written to data/path_a_backtest_logs.jsonl")
    print("=" * 70 + "\n")
    
    # 如果有失敗的實驗，返回非零退出碼
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

