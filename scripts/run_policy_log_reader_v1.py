#!/usr/bin/env python3
"""
Run J-GOD Policy Log Reader v1

用途：分析 Path A 回測 Log，排名最佳實驗。

這是「AI Policy Service v1 的實驗分析組件」：
- 只負責「讀回測 Log + 排名 + 輸出」
- 未來 AI Policy Service 可以直接讀 JSON Lines 或呼叫這個模組做自動調參

使用範例：
    PYTHONPATH=. python scripts/run_policy_log_reader_v1.py
    PYTHONPATH=. python scripts/run_policy_log_reader_v1.py --start-date 2024-01-01 --end-date 2024-12-31 --top-n 30
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from jgod.policy import PolicyLogReaderV1, PolicyScoreConfig


def format_config_string(summary) -> str:
    """格式化 Config 字串"""
    parts = []
    if summary.long_budget is not None:
        parts.append(f"LB={summary.long_budget:.2f}")
    if summary.short_budget is not None:
        parts.append(f"SB={summary.short_budget:.2f}")
    if summary.max_weight_per_symbol is not None:
        parts.append(f"MW={summary.max_weight_per_symbol:.2f}")
    if summary.min_score is not None:
        parts.append(f"MS={summary.min_score:.2f}")
    if summary.allow_short is not None:
        parts.append(f"SHORT={'Y' if summary.allow_short else 'N'}")
    return " ".join(parts) if parts else "-"


def print_results(reader: PolicyLogReaderV1, summaries: list, config: PolicyScoreConfig, args):
    """印出分析結果"""
    print("\n" + "=" * 100)
    print("J-GOD Policy Log Reader v1")
    print("=" * 100)
    
    # 設定摘要
    print(f"\n設定摘要:")
    print(f"  Log Path      : {reader.log_path}")
    
    period_str = "全部期間"
    if args.start_date or args.end_date:
        start = args.start_date or "最早"
        end = args.end_date or "最新"
        period_str = f"{start} ~ {end}"
    print(f"  Period        : {period_str}")
    
    print(f"  Top N         : {args.top_n}")
    print(f"  Min Days      : {config.min_days}")
    print(f"  Min Trades    : {config.min_trades}")
    print(f"  Score Weights : Sharpe={config.sharpe_weight:.2f}, MaxDD={config.max_dd_weight:.2f}")
    
    # 結果列表
    if not summaries:
        print(f"\n" + "-" * 100)
        print("No valid backtest experiments found.")
        print("  - Check if data/path_a_backtest_logs.jsonl exists")
        print("  - Or run Path A v1 first to generate logs.")
        print("-" * 100)
        return
    
    print(f"\n找到 {len(summaries)} 筆有效實驗 (Top {args.top_n}):")
    print("-" * 100)
    
    # 表頭
    header = (
        f"{'Rank':<6} "
        f"{'RunID':<13} "
        f"{'Sharpe':<8} "
        f"{'MaxDD':<8} "
        f"{'TotalRet':<10} "
        f"{'WinRate':<8} "
        f"{'Days':<6} "
        f"{'Trades':<8} "
        f"{'Score':<8} "
        f"{'Config':<40}"
    )
    print(header)
    print("-" * 100)
    
    # 資料行
    for i, summary in enumerate(summaries, 1):
        run_id_short = summary.run_id[:11] + "..." if len(summary.run_id) > 11 else summary.run_id
        config_str = format_config_string(summary)
        
        row = (
            f"{i:<6} "
            f"{run_id_short:<13} "
            f"{summary.sharpe_ratio:>7.4f} "
            f"{summary.max_drawdown:>7.2%} "
            f"{summary.total_return:>9.2%} "
            f"{summary.win_rate:>7.2%} "
            f"{summary.num_days:>5} "
            f"{summary.num_long_trades + summary.num_short_trades:>7} "
            f"{summary.score:>7.4f} "
            f"{config_str:<40}"
        )
        print(row)
    
    print("-" * 100)
    print(f"\n說明：")
    print(f"  - Rank: 依綜合分數排序（Sharpe={config.sharpe_weight:.2f}, MaxDD={config.max_dd_weight:.2f}）")
    print(f"  - Config: LB=Long Budget, SB=Short Budget, MW=Max Weight, MS=Min Score, SHORT=Allow Short")
    print("=" * 100 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run J-GOD Policy Log Reader v1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (view all recent experiments with default settings)
  PYTHONPATH=. python scripts/run_policy_log_reader_v1.py
  
  # Filter by date range and adjust criteria
  PYTHONPATH=. python scripts/run_policy_log_reader_v1.py \\
    --start-date 2024-01-01 \\
    --end-date 2024-12-31 \\
    --top-n 30 \\
    --min-days 120 \\
    --min-trades 50 \\
    --sharpe-weight 0.8 \\
    --maxdd-weight 0.2
        """
    )
    
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date filter (YYYY-MM-DD)",
    )
    
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date filter (YYYY-MM-DD)",
    )
    
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Top N experiments to show (default: 20)",
    )
    
    parser.add_argument(
        "--min-days",
        type=int,
        default=60,
        help="Minimum trading days (default: 60)",
    )
    
    parser.add_argument(
        "--min-trades",
        type=int,
        default=30,
        help="Minimum total trades (default: 30)",
    )
    
    parser.add_argument(
        "--sharpe-weight",
        type=float,
        default=0.7,
        help="Sharpe Ratio weight in score (default: 0.7)",
    )
    
    parser.add_argument(
        "--maxdd-weight",
        type=float,
        default=0.3,
        help="Max Drawdown weight in score (default: 0.3)",
    )
    
    parser.add_argument(
        "--log-path",
        type=str,
        default="data/path_a_backtest_logs.jsonl",
        help="Path to backtest log file (default: data/path_a_backtest_logs.jsonl)",
    )
    
    args = parser.parse_args()
    
    # 驗證日期格式（如果提供）
    if args.start_date:
        try:
            from datetime import datetime
            datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            print(f"❌ Error: Invalid start-date format '{args.start_date}'. Use YYYY-MM-DD")
            sys.exit(1)
    
    if args.end_date:
        try:
            from datetime import datetime
            datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError:
            print(f"❌ Error: Invalid end-date format '{args.end_date}'. Use YYYY-MM-DD")
            sys.exit(1)
    
    # 建立 PolicyScoreConfig
    score_config = PolicyScoreConfig(
        sharpe_weight=args.sharpe_weight,
        max_dd_weight=args.maxdd_weight,
        min_days=args.min_days,
        min_trades=args.min_trades,
    )
    
    # 建立 PolicyLogReaderV1
    try:
        reader = PolicyLogReaderV1(
            log_path=args.log_path,
            score_config=score_config,
        )
    except Exception as e:
        print(f"❌ Error: Failed to initialize PolicyLogReaderV1: {e}")
        sys.exit(1)
    
    print(f"\n🔍 Analyzing Path A Backtest Logs...")
    print(f"   Log Path:     {args.log_path}")
    print(f"   Start Date:   {args.start_date or 'None'}")
    print(f"   End Date:     {args.end_date or 'None'}")
    print(f"   Top N:        {args.top_n}")
    print(f"   Min Days:     {args.min_days}")
    print(f"   Min Trades:   {args.min_trades}")
    print(f"   Score Weights: Sharpe={args.sharpe_weight:.2f}, MaxDD={args.maxdd_weight:.2f}")
    
    try:
        # 執行過濾與排序
        summaries = reader.filter_and_rank(
            start_date=args.start_date,
            end_date=args.end_date,
            top_n=args.top_n,
        )
        
        # 印出結果
        print_results(reader, summaries, score_config, args)
        
        print("✅ Analysis completed successfully!")
        sys.exit(0)
        
    except FileNotFoundError:
        print(f"\n❌ Error: Log file not found: {args.log_path}")
        print(f"   Please run Path A v1 first to generate logs.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

