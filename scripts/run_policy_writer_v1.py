#!/usr/bin/env python3
"""
Run J-GOD Policy Writer v1

用途：從 Path A 回測 Log 中選出最佳實驗，產生建議版 RiskConfig 檔案。

這是「AI Policy Service v1 的 Policy Writer 組件」：
- 讀取回測實驗結果（透過 PolicyLogReaderV1）
- 選出最佳實驗（v1 版本直接取 Top 1）
- 產生建議版 RiskConfig 檔案（YAML 格式）

使用範例：
    PYTHONPATH=. python scripts/run_policy_writer_v1.py
    PYTHONPATH=. python scripts/run_policy_writer_v1.py --start-date 2024-01-01 --end-date 2024-12-31
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from jgod.policy import PolicyScoreConfig, PolicyWriterV1


def print_suggestion_summary(writer: PolicyWriterV1, suggestion, output_path: str, args):
    """印出建議摘要"""
    print("\n" + "=" * 100)
    print("J-GOD Policy Writer v1 - Suggested RiskConfig")
    print("=" * 100)
    
    # 設定摘要
    print(f"\n設定摘要:")
    print(f"  Log Path     : {writer.reader.log_path}")
    
    period_str = "全部期間"
    if args.start_date or args.end_date:
        start = args.start_date or "最早"
        end = args.end_date or "最新"
        period_str = f"{start} ~ {end}"
    print(f"  Period       : {period_str}")
    print(f"  TopK Search  : {args.top_k}")
    print(f"  Output File  : {output_path}")
    
    # 最佳實驗資訊
    print(f"\n最佳實驗:")
    print(f"  RunID        : {suggestion.run_id}")
    print(f"  Sharpe       : {suggestion.sharpe_ratio:>8.4f}")
    print(f"  Max Drawdown : {suggestion.max_drawdown:>7.2%}")
    print(f"  Total Return : {suggestion.total_return:>7.2%}")
    print(f"  Win Rate     : {suggestion.win_rate:>7.2%}")
    print(f"  Days         : {suggestion.num_days:>6}")
    print(f"  Trades       : {suggestion.num_trades:>6}")
    print(f"  Score        : {suggestion.score:>8.4f}")
    
    # 建議的風控參數
    print(f"\n建議的風控參數:")
    print(f"  long_budget          : {suggestion.long_budget:.2f}")
    print(f"  short_budget         : {suggestion.short_budget:.2f}")
    print(f"  max_weight_per_stock : {suggestion.max_weight_per_symbol:.2f}")
    print(f"  min_score            : {suggestion.min_score:.2f}")
    print(f"  allow_short          : {suggestion.allow_short}")
    
    print("\n" + "=" * 100)
    print(f"✅ 已產生建議風控配置檔案：{output_path}")
    print("=" * 100 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run J-GOD Policy Writer v1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (use default settings)
  PYTHONPATH=. python scripts/run_policy_writer_v1.py
  
  # Specify date range, adjust weights, custom file name
  PYTHONPATH=. python scripts/run_policy_writer_v1.py \\
    --start-date 2024-01-01 \\
    --end-date 2024-12-31 \\
    --sharpe-weight 0.8 \\
    --maxdd-weight 0.2 \\
    --output-dir policy \\
    --file-name risk_config_suggested_2024.yaml
        """
    )
    
    parser.add_argument(
        "--log-path",
        type=str,
        default="data/path_a_backtest_logs.jsonl",
        help="Path to backtest log file (default: data/path_a_backtest_logs.jsonl)",
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
        "--top-k",
        type=int,
        default=3,
        help="Search top K experiments (v1 uses Top 1 only, default: 3)",
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
        "--output-dir",
        type=str,
        default="policy",
        help="Output directory for risk config file (default: policy)",
    )
    
    parser.add_argument(
        "--file-name",
        type=str,
        help="Output file name (default: risk_config_suggested_v1.yaml)",
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
    
    # 建 PolicyScoreConfig
    score_config = PolicyScoreConfig(
        sharpe_weight=args.sharpe_weight,
        max_dd_weight=args.maxdd_weight,
        min_days=args.min_days,
        min_trades=args.min_trades,
    )
    
    # 建 PolicyWriterV1
    try:
        writer = PolicyWriterV1(
            log_path=args.log_path,
            score_config=score_config,
            min_days=args.min_days,
            min_trades=args.min_trades,
        )
    except Exception as e:
        print(f"❌ Error: Failed to initialize PolicyWriterV1: {e}")
        sys.exit(1)
    
    print(f"\n🔍 Generating Policy Suggestion...")
    print(f"   Log Path:     {args.log_path}")
    print(f"   Start Date:   {args.start_date or 'None'}")
    print(f"   End Date:     {args.end_date or 'None'}")
    print(f"   Top K:        {args.top_k}")
    print(f"   Min Days:     {args.min_days}")
    print(f"   Min Trades:   {args.min_trades}")
    print(f"   Score Weights: Sharpe={args.sharpe_weight:.2f}, MaxDD={args.maxdd_weight:.2f}")
    print(f"   Output Dir:   {args.output_dir}")
    print(f"   File Name:    {args.file_name or 'risk_config_suggested_v1.yaml'}")
    
    try:
        # 產生建議
        suggestion = writer.generate_suggestion(
            start_date=args.start_date,
            end_date=args.end_date,
            top_k=args.top_k,
        )
        
        if suggestion is None:
            print(f"\n" + "-" * 100)
            print("No valid backtest experiments found.")
            print("  - Check if data/path_a_backtest_logs.jsonl exists")
            print("  - Or run Path A v1 first to generate logs.")
            print("  - Or adjust --min-days / --min-trades / date filters.")
            print("-" * 100 + "\n")
            sys.exit(1)
        
        # 寫檔
        output_path = writer.write_risk_config_file(
            suggestion,
            output_dir=args.output_dir,
            file_name=args.file_name,
        )
        
        # 印出摘要
        print_suggestion_summary(writer, suggestion, output_path, args)
        
        print("✅ Policy suggestion generated successfully!")
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

