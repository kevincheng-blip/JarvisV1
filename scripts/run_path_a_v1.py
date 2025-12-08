#!/usr/bin/env python3
"""
Run J-GOD Path A v1 Backtest Engine

用途：在命令列執行回測，並看到績效報告。

使用範例：
    PYTHONPATH=. python scripts/run_path_a_v1.py 2024-01-01 2024-12-31
    PYTHONPATH=. python scripts/run_path_a_v1.py 2024-01-01 2024-12-31 --capital 2000000 --long-budget 0.7
"""

import argparse
import json
import logging
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from jgod.decision.risk_config_loader import load_risk_config
from jgod.path_a.path_a_engine_v1 import PathAEngineV1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_backtest_result(result, show_equity_curve_sample: int = 5):
    """印出回測結果"""
    print("\n" + "=" * 70)
    print(f"📊 Path A v1 - Backtest Result")
    print("=" * 70)
    
    # 回測範圍
    print(f"\n回測範圍:")
    print(f"  開始日期:  {result.start_date.isoformat()}")
    print(f"  結束日期:  {result.end_date.isoformat()}")
    print(f"  初始資金:  {result.initial_capital:,.2f}")
    print(f"  最終淨值:  {result.final_capital:,.2f}")
    print(f"  總報酬率:  {result.metrics.total_return:8.2%}")
    
    # 核心績效
    print(f"\n核心績效:")
    print(f"  年化報酬:  {result.metrics.annualized_return:8.2%}")
    print(f"  年化波動:  {result.metrics.annualized_volatility:8.2%}")
    print(f"  Sharpe Ratio: {result.metrics.sharpe_ratio:8.4f}")
    print(f"  最大回撤:  {result.metrics.max_drawdown:8.2%}")
    
    # 風控摘要
    print(f"\n風控摘要:")
    print(f"  總交易成本: {result.metrics.total_commission:,.2f}")
    print(f"  日級勝率:   {result.metrics.win_rate:8.2%}")
    print(f"  Long 交易次數: {result.metrics.num_long_trades}")
    print(f"  Short 交易次數: {result.metrics.num_short_trades}")
    
    # Equity Curve 樣本
    if result.daily_equity_curve:
        print(f"\nEquity Curve (前 {min(show_equity_curve_sample, len(result.daily_equity_curve))} 筆):")
        for i, daily in enumerate(result.daily_equity_curve[:show_equity_curve_sample], 1):
            print(f"  {i}) {daily['date']}: {daily['equity_value']:,.2f} "
                  f"(cash: {daily['cash']:,.2f}, market: {daily['market_value']:,.2f})")
        
        if len(result.daily_equity_curve) > show_equity_curve_sample:
            print(f"\n  ... 共 {len(result.daily_equity_curve)} 個交易日")
    
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Run J-GOD Path A v1 Backtest Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  PYTHONPATH=. python scripts/run_path_a_v1.py 2024-01-01 2024-12-31
  
  # With custom capital
  PYTHONPATH=. python scripts/run_path_a_v1.py 2024-01-01 2024-12-31 --capital 2000000
  
  # With decision engine parameters
  PYTHONPATH=. python scripts/run_path_a_v1.py 2024-01-01 2024-12-31 --long-budget 0.7 --short-budget 0.15
        """
    )
    
    parser.add_argument(
        "start_date",
        type=str,
        help="Start date in YYYY-MM-DD format",
    )
    
    parser.add_argument(
        "end_date",
        type=str,
        help="End date in YYYY-MM-DD format",
    )
    
    parser.add_argument(
        "--capital",
        type=float,
        default=1_000_000.0,
        help="Initial capital (default: 1,000,000)",
    )
    
    # Decision Engine 參數
    parser.add_argument(
        "--long-budget",
        type=float,
        default=0.6,
        help="Long budget (default: 0.6 = 60%%)",
    )
    
    parser.add_argument(
        "--short-budget",
        type=float,
        default=0.2,
        help="Short budget (default: 0.2 = 20%%)",
    )
    
    parser.add_argument(
        "--max-weight-per-symbol",
        type=float,
        default=0.10,
        help="Max weight per symbol (default: 0.10 = 10%%)",
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
        help="Disable short positions",
    )
    
    parser.add_argument(
        "--risk-config-file",
        type=str,
        help="Path to RiskConfig YAML file (overrides other risk parameters)",
    )
    
    args = parser.parse_args()
    
    # Parse dates
    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    except ValueError:
        print(f"❌ Error: Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    if start_date >= end_date:
        print(f"❌ Error: start_date must be before end_date")
        sys.exit(1)
    
    # 載入 RiskConfig（如果提供）
    risk_config_dict = None
    if args.risk_config_file:
        try:
            risk_config_dict = load_risk_config(args.risk_config_file)
            if risk_config_dict:
                logger.info(f"RiskConfig loaded from YAML: {args.risk_config_file}")
                # YAML 值會覆蓋 CLI 參數
                args.long_budget = risk_config_dict.get("long_budget", args.long_budget)
                args.short_budget = risk_config_dict.get("short_budget", args.short_budget)
                args.max_weight_per_symbol = risk_config_dict.get("max_weight_per_symbol", args.max_weight_per_symbol)
                args.min_score = risk_config_dict.get("min_score", args.min_score)
                if "allow_short" in risk_config_dict:
                    args.no_short = not risk_config_dict["allow_short"]
        except FileNotFoundError:
            logger.error(f"RiskConfig file not found: {args.risk_config_file}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load RiskConfig: {e}")
            sys.exit(1)
    
    # Initialize Path A Engine
    decision_config = {
        "long_budget": args.long_budget,
        "short_budget": args.short_budget,
        "max_weight_per_symbol": args.max_weight_per_symbol,
        "min_score": args.min_score,
        "allow_short": not args.no_short,
    }
    
    engine = PathAEngineV1(
        initial_capital=args.capital,
        **decision_config
    )
    
    print(f"\n🔍 Running Path A v1 Backtest...")
    print(f"   Start Date:  {args.start_date}")
    print(f"   End Date:    {args.end_date}")
    print(f"   Capital:     {args.capital:,.2f}")
    print(f"   Long Budget: {args.long_budget:.1%}")
    print(f"   Short Budget: {args.short_budget:.1%}")
    print(f"   Max Weight:  {args.max_weight_per_symbol:.1%}")
    print(f"   Min Score:   {args.min_score}")
    print(f"   Allow Short: {not args.no_short}")
    
    try:
        # Run backtest
        result = engine.run_backtest(start_date=start_date, end_date=end_date)
        
        if not result.daily_equity_curve:
            print(f"\n❌ No trading dates found in the range {args.start_date} to {args.end_date}")
            print(f"   Please check if daily_bars has data for this date range.")
            sys.exit(1)
        
        # Print result
        print_backtest_result(result)
        
        # 準備 config_params（用於 log）
        config_params = {
            "initial_capital": args.capital,
            "long_budget": args.long_budget,
            "short_budget": args.short_budget,
            "max_weight_per_symbol": args.max_weight_per_symbol,
            "min_score": args.min_score,
            "allow_short": not args.no_short,
        }
        
        # 產生 run_id
        run_id = uuid.uuid4().hex
        
        # 產生 log record
        log_record = engine.generate_log_record(
            run_id=run_id,
            config_params=config_params,
            backtest_result=result,
        )
        
        # 寫入 JSON Lines 檔案
        log_file_path = project_root / "data" / "path_a_backtest_logs.jsonl"
        
        # 確保 data 目錄存在
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 追加寫入（append mode）
        with open(log_file_path, "a", encoding="utf-8") as f:
            json_line = json.dumps(log_record, ensure_ascii=False)
            f.write(json_line + "\n")
        
        print("\n✅ Backtest completed successfully!")
        print(f"已儲存 Path A 回測紀錄，run_id={run_id}，檔案：{log_file_path.relative_to(project_root)}")
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

