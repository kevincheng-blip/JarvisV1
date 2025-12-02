#!/usr/bin/env python
"""
Run a J-GOD Path B walk-forward analysis experiment.

This script executes Path B Engine for walk-forward analysis and governance rule simulation.

Usage example:

    python scripts/run_jgod_path_b.py \
        --name path_b_demo \
        --start-date 2024-01-01 \
        --end-date 2024-12-31 \
        --rebalance-frequency M \
        --universe "2330.TW,2317.TW" \
        --data-source mock \
        --mode basic \
        --walkforward-window 6m \
        --walkforward-step 3m

Reference:
- spec/JGOD_PathBEngine_Spec.md
- docs/JGOD_PATH_B_STANDARD_v1.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import pandas as pd

# J-GOD Path B modules
from jgod.path_b.path_b_engine import (
    PathBEngine,
    PathBConfig,
    PathBRunResult,
)


def parse_args() -> argparse.Namespace:
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description="Run a J-GOD Path B walk-forward analysis experiment."
    )
    
    # 必填參數
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Experiment name (used in output directory).",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Backtest start date (YYYY-MM-DD). This will be used as train_start.",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="Backtest end date (YYYY-MM-DD). This will be used as test_end.",
    )
    parser.add_argument(
        "--walkforward-window",
        type=str,
        required=True,
        help="Walk-forward window size (e.g., '6m' for 6 months, '1y' for 1 year).",
    )
    parser.add_argument(
        "--walkforward-step",
        type=str,
        required=True,
        help="Walk-forward step size (e.g., '1m' for 1 month, '3m' for 3 months).",
    )
    
    # 基本設定
    parser.add_argument(
        "--rebalance-frequency",
        type=str,
        default="M",
        choices=["D", "W", "M"],
        help="Rebalance frequency: D (daily), W (weekly), M (monthly). Default: M.",
    )
    parser.add_argument(
        "--universe",
        type=str,
        required=True,
        help="Comma-separated list of symbols (e.g., '2330.TW,2317.TW,2454.TW').",
    )
    parser.add_argument(
        "--data-source",
        type=str,
        default="mock",
        choices=["finmind", "mock"],
        help="Data source: finmind or mock. Default: mock.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="basic",
        choices=["basic", "extreme"],
        help="Execution mode: basic or extreme. Default: basic.",
    )
    
    # Governance 門檻（可選）
    parser.add_argument(
        "--max-drawdown-threshold",
        type=float,
        default=None,
        help="Maximum drawdown threshold (e.g., -0.15 for -15%). Default: -0.15.",
    )
    parser.add_argument(
        "--min-sharpe-threshold",
        type=float,
        default=None,
        help="Minimum Sharpe ratio threshold. Default: 2.0.",
    )
    parser.add_argument(
        "--max-te-threshold",
        type=float,
        default=None,
        help="Maximum tracking error threshold (e.g., 0.04 for 4%). Default: 0.04.",
    )
    parser.add_argument(
        "--max-turnover-threshold",
        type=float,
        default=None,
        help="Maximum turnover threshold (e.g., 1.0 for 100%). Default: 1.0.",
    )
    
    return parser.parse_args()


def build_path_b_config(args: argparse.Namespace) -> PathBConfig:
    """建立 PathBConfig 實例"""
    # 解析 universe
    universe = [s.strip() for s in args.universe.split(",") if s.strip()]
    
    # 解析 walkforward_window 來計算第一個 window 的大小
    # 簡化：將 walkforward_window 分成 train 和 test 兩部分
    # 例如 "6m" -> train 3m, test 3m
    def _parse_duration(duration_str: str) -> int:
        """Parse duration string like '6m' -> 6 months"""
        if duration_str.endswith('m'):
            return int(duration_str[:-1])
        elif duration_str.endswith('y'):
            return int(duration_str[:-1]) * 12
        else:
            raise ValueError(f"Invalid duration format: {duration_str}. Expected format: '6m' or '1y'")
    
    window_months = _parse_duration(args.walkforward_window)
    # 簡化：train 和 test 各佔一半
    train_months = window_months // 2
    test_months = window_months - train_months
    
    # 計算第一個 window 的日期
    
    train_start = args.start_date
    train_start_dt = pd.to_datetime(train_start)
    train_end_dt = train_start_dt + pd.DateOffset(months=train_months)
    train_end = train_end_dt.strftime("%Y-%m-%d")
    
    test_start_dt = train_end_dt + pd.DateOffset(days=1)
    test_start = test_start_dt.strftime("%Y-%m-%d")
    test_end_dt = test_start_dt + pd.DateOffset(months=test_months)
    test_end = test_end_dt.strftime("%Y-%m-%d")
    
    # 如果計算出的 test_end 超過了指定的 end_date，則使用 end_date
    end_date_dt = pd.to_datetime(args.end_date)
    if test_end_dt > end_date_dt:
        test_end = args.end_date
    
    # 建立配置
    config_kwargs = {
        "train_start": train_start,
        "train_end": train_end,
        "test_start": test_start,
        "test_end": test_end,
        "walkforward_window": args.walkforward_window,
        "walkforward_step": args.walkforward_step,
        "universe": universe,
        "rebalance_frequency": args.rebalance_frequency,
        "alpha_config_set": [],
        "data_source": args.data_source,
        "mode": args.mode,
        "experiment_name": args.name,
    }
    
    # 加入 Governance 門檻（如果提供）
    if args.max_drawdown_threshold is not None:
        config_kwargs["max_drawdown_threshold"] = args.max_drawdown_threshold
    if args.min_sharpe_threshold is not None:
        config_kwargs["sharpe_threshold"] = args.min_sharpe_threshold
    if args.max_te_threshold is not None:
        config_kwargs["tracking_error_max"] = args.max_te_threshold
    if args.max_turnover_threshold is not None:
        config_kwargs["turnover_max"] = args.max_turnover_threshold
    
    return PathBConfig(**config_kwargs)


def print_summary(result: PathBRunResult) -> None:
    """在 console 印出精簡總結"""
    print("\n" + "=" * 80)
    print("Path B Walk-Forward Analysis Summary")
    print("=" * 80)
    
    # 窗口數量
    num_windows = len(result.window_results)
    print(f"\n📊 窗口數量: {num_windows}")
    
    # 績效統計
    summary = result.summary
    if "avg_sharpe" in summary:
        print(f"\n📈 績效統計:")
        print(f"  - 平均 Sharpe: {summary['avg_sharpe']:.2f}")
        if "sharpe_std" in summary:
            print(f"  - Sharpe 標準差: {summary['sharpe_std']:.2f}")
        if "sharpe_min" in summary:
            print(f"  - Sharpe 最小值: {summary['sharpe_min']:.2f}")
        if "sharpe_max" in summary:
            print(f"  - Sharpe 最大值: {summary['sharpe_max']:.2f}")
    
    if "avg_max_drawdown" in summary:
        print(f"  - 平均最大回撤: {summary['avg_max_drawdown']:.2%}")
        if "worst_drawdown" in summary:
            print(f"  - 最大回撤: {summary['worst_drawdown']:.2%}")
    
    # Governance Summary
    if result.governance_summary:
        gov_summary = result.governance_summary
        print(f"\n🛡️  Governance Summary:")
        print(f"  - 總窗口數: {gov_summary.total_windows}")
        print(f"  - 觸發 breach 的窗口數: {gov_summary.windows_with_any_breach}")
        if gov_summary.windows_with_any_breach > 0:
            breach_rate = gov_summary.windows_with_any_breach / gov_summary.total_windows
            print(f"  - Breach 比例: {breach_rate:.1%}")
        print(f"  - 最多連續 breach 窗口數: {gov_summary.max_consecutive_breach_windows}")
        
        if gov_summary.rule_hit_counts:
            print(f"\n  Rule 觸發次數:")
            for rule, count in gov_summary.rule_hit_counts.items():
                print(f"    - {rule}: {count} 次")
    
    print("\n" + "=" * 80 + "\n")


def export_results(result: PathBRunResult, output_dir: Path) -> None:
    """將結果輸出到檔案"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. windows_summary.csv
    export_windows_summary(result, output_dir / "windows_summary.csv")
    
    # 2. governance_summary.json
    export_governance_summary(result, output_dir / "governance_summary.json")
    
    # 3. path_b_summary.json
    export_path_b_summary(result, output_dir / "path_b_summary.json")
    
    # 4. path_b_report.md
    export_path_b_report(result, output_dir / "path_b_report.md")


def export_windows_summary(result: PathBRunResult, filepath: Path) -> None:
    """輸出 windows_summary.csv"""
    
    rows = []
    for window_result in result.window_results:
        # 找到對應的 governance result
        governance_result = None
        if result.windows_governance:
            for gov in result.windows_governance:
                if gov.window_id == window_result.window_id:
                    governance_result = gov
                    break
        
        # 建立 breach 標記
        has_max_dd_breach = 0
        has_sharpe_low = 0
        has_te_breach = 0
        has_turnover_high = 0
        
        if governance_result:
            if "MAX_DRAWDOWN_BREACH" in governance_result.rules_triggered:
                has_max_dd_breach = 1
            if "SHARPE_TOO_LOW" in governance_result.rules_triggered:
                has_sharpe_low = 1
            if "TE_BREACH" in governance_result.rules_triggered:
                has_te_breach = 1
            if "TURNOVER_TOO_HIGH" in governance_result.rules_triggered:
                has_turnover_high = 1
        
        row = {
            "window_id": window_result.window_id,
            "train_start": window_result.train_start,
            "train_end": window_result.train_end,
            "test_start": window_result.test_start,
            "test_end": window_result.test_end,
            "sharpe": window_result.sharpe_ratio,
            "max_drawdown": window_result.max_drawdown,
            "total_return": window_result.total_return,
            "turnover": window_result.turnover_rate,
            "tracking_error": window_result.tracking_error or 0.0,
            "has_max_dd_breach": has_max_dd_breach,
            "has_sharpe_low": has_sharpe_low,
            "has_te_breach": has_te_breach,
            "has_turnover_high": has_turnover_high,
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(filepath, index=False)
    print(f"✅ Exported windows_summary.csv to {filepath}")


def export_governance_summary(result: PathBRunResult, filepath: Path) -> None:
    """輸出 governance_summary.json"""
    if not result.governance_summary:
        # 如果沒有 governance summary，輸出空結構
        data = {
            "total_windows": len(result.window_results),
            "rule_hit_counts": {},
            "windows_with_any_breach": 0,
            "max_consecutive_breach_windows": 0,
            "global_metrics": {},
        }
    else:
        gov_summary = result.governance_summary
        data = {
            "total_windows": gov_summary.total_windows,
            "rule_hit_counts": gov_summary.rule_hit_counts,
            "windows_with_any_breach": gov_summary.windows_with_any_breach,
            "max_consecutive_breach_windows": gov_summary.max_consecutive_breach_windows,
            "global_metrics": gov_summary.global_metrics,
        }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Exported governance_summary.json to {filepath}")


def export_path_b_summary(result: PathBRunResult, filepath: Path) -> None:
    """輸出 path_b_summary.json"""
    data = {
        "experiment_name": result.config.experiment_name,
        "num_windows": len(result.window_results),
        "summary": result.summary,
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Exported path_b_summary.json to {filepath}")


def export_path_b_report(result: PathBRunResult, filepath: Path) -> None:
    """輸出 path_b_report.md"""
    config = result.config
    summary = result.summary
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Path B Walk-Forward Analysis Report\n\n")
        
        # 實驗基本資訊
        f.write("## 實驗基本資訊\n\n")
        f.write(f"- **實驗名稱**: {config.experiment_name}\n")
        f.write(f"- **Train 起始日**: {config.train_start}\n")
        f.write(f"- **Train 結束日**: {config.train_end}\n")
        f.write(f"- **Test 起始日**: {config.test_start}\n")
        f.write(f"- **Test 結束日**: {config.test_end}\n")
        f.write(f"- **Walk-Forward Window**: {config.walkforward_window}\n")
        f.write(f"- **Walk-Forward Step**: {config.walkforward_step}\n")
        f.write(f"- **Universe**: {', '.join(config.universe)}\n")
        f.write(f"- **Data Source**: {config.data_source}\n")
        f.write(f"- **Mode**: {config.mode}\n")
        f.write(f"- **Rebalance Frequency**: {config.rebalance_frequency}\n")
        f.write("\n")
        
        # 績效統計
        f.write("## 績效統計\n\n")
        f.write(f"**總窗口數**: {summary.get('num_windows', 0)}\n\n")
        
        if "avg_sharpe" in summary:
            f.write("### Sharpe Ratio\n\n")
            f.write(f"- **平均**: {summary['avg_sharpe']:.2f}\n")
            if "sharpe_std" in summary:
                f.write(f"- **標準差**: {summary['sharpe_std']:.2f}\n")
            if "sharpe_min" in summary:
                f.write(f"- **最小值**: {summary['sharpe_min']:.2f}\n")
            if "sharpe_max" in summary:
                f.write(f"- **最大值**: {summary['sharpe_max']:.2f}\n")
            f.write("\n")
        
        if "avg_max_drawdown" in summary:
            f.write("### Maximum Drawdown\n\n")
            f.write(f"- **平均**: {summary['avg_max_drawdown']:.2%}\n")
            if "worst_drawdown" in summary:
                f.write(f"- **最大值**: {summary['worst_drawdown']:.2%}\n")
            f.write("\n")
        
        # Governance Summary
        if result.governance_summary:
            gov_summary = result.governance_summary
            f.write("## Governance Summary\n\n")
            f.write(f"**總窗口數**: {gov_summary.total_windows}\n")
            f.write(f"**觸發 breach 的窗口數**: {gov_summary.windows_with_any_breach}\n")
            if gov_summary.windows_with_any_breach > 0:
                breach_rate = gov_summary.windows_with_any_breach / gov_summary.total_windows
                f.write(f"**Breach 比例**: {breach_rate:.1%}\n")
            f.write(f"**最多連續 breach 窗口數**: {gov_summary.max_consecutive_breach_windows}\n\n")
            
            if gov_summary.rule_hit_counts:
                f.write("### Rule 觸發統計\n\n")
                for rule, count in sorted(gov_summary.rule_hit_counts.items()):
                    rate = count / gov_summary.total_windows
                    f.write(f"- **{rule}**: {count} 次 ({rate:.1%})\n")
                f.write("\n")
    
    print(f"✅ Exported path_b_report.md to {filepath}")


def main() -> None:
    """主函數"""
    args = parse_args()
    
    print(f"Path B Experiment: {args.name}")
    print(f"Mode: {args.mode}")
    print(f"Data Source: {args.data_source}")
    print(f"Walk-Forward Window: {args.walkforward_window}, Step: {args.walkforward_step}")
    
    # 建立配置
    config = build_path_b_config(args)
    
    # 建立 Path B Engine（使用預設的 data loader 和 engines）
    engine = PathBEngine(
        data_source=config.data_source,
        mode=config.mode,
    )
    
    # 執行 Path B 分析
    print("\n執行 Path B Walk-Forward Analysis...")
    result = engine.run(config)
    
    # 印出精簡總結
    print_summary(result)
    
    # 輸出檔案
    output_dir = Path("output") / "path_b" / args.name
    print(f"輸出結果到: {output_dir}")
    export_results(result, output_dir)
    
    print(f"\n✅ Path B 實驗完成！結果已輸出到: {output_dir}")


if __name__ == "__main__":
    main()

