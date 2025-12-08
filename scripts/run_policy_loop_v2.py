#!/usr/bin/env python3
"""
J-GOD Policy Loop v2 - 自動化完整閉環

用途：一鍵完成「自動實驗 + 自動產生建議 RiskConfig + 自動驗證」的完整 Policy Loop。

使用範例：
    PYTHONPATH=. python scripts/run_policy_loop_v2.py
    PYTHONPATH=. python scripts/run_policy_loop_v2.py --config-file config/path_a_experiments_v1.json --sharpe-weight 0.8
"""

import argparse
import json
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from jgod.config.experiment_config_loader import load_experiment_config
from jgod.decision.risk_config_loader import load_risk_config
from jgod.path_a.path_a_engine_v1 import PathAEngineV1
from jgod.policy import PolicyScoreConfig, PolicyWriterV1
from typing import Optional


def print_section_header(title: str, width: int = 70):
    """印出區塊標題"""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_key_value(key: str, value, indent: int = 0):
    """印出鍵值對"""
    spaces = " " * indent
    print(f"{spaces}{key:<25} {value}")


def run_path_a_backtest(
    start_date: date,
    end_date: date,
    capital: float,
    decision_config: dict,
) -> dict:
    """執行單一 Path A 回測"""
    engine = PathAEngineV1(initial_capital=capital, **decision_config)
    result = engine.run_backtest(start_date=start_date, end_date=end_date)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="J-GOD Policy Loop v2 - Automated Policy Loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--config-file",
        type=str,
        default="config/path_a_experiments_v1.json",
        help="Path to experiment config file (default: config/path_a_experiments_v1.json)",
    )
    
    parser.add_argument(
        "--log-path",
        type=str,
        default="data/path_a_backtest_logs.jsonl",
        help="Path to backtest log file (default: data/path_a_backtest_logs.jsonl)",
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="policy",
        help="Output directory for suggested config (default: policy)",
    )
    
    parser.add_argument(
        "--file-name",
        type=str,
        default="risk_config_suggested_auto_v2.yaml",
        help="Output filename for suggested config (default: risk_config_suggested_auto_v2.yaml)",
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
        default=10,
        help="Minimum trades (default: 10)",
    )
    
    parser.add_argument(
        "--sharpe-weight",
        type=float,
        default=0.7,
        help="Sharpe ratio weight (default: 0.7)",
    )
    
    parser.add_argument(
        "--maxdd-weight",
        type=float,
        default=0.3,
        help="Max drawdown weight (default: 0.3)",
    )
    
    parser.add_argument(
        "--final-backtest-start",
        type=str,
        help="Final backtest start date (YYYY-MM-DD). If not provided, uses config start_date.",
    )
    
    parser.add_argument(
        "--final-backtest-end",
        type=str,
        help="Final backtest end date (YYYY-MM-DD). If not provided, uses config end_date.",
    )
    
    args = parser.parse_args()
    
    # ============================================================
    # 步驟 1: 載入配置檔
    # ============================================================
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
    
    # Final backtest 日期（如果指定）
    final_start_date = start_date
    final_end_date = end_date
    if args.final_backtest_start:
        final_start_date = datetime.strptime(args.final_backtest_start, "%Y-%m-%d").date()
    if args.final_backtest_end:
        final_end_date = datetime.strptime(args.final_backtest_end, "%Y-%m-%d").date()
    
    # ============================================================
    # 區塊 1: Policy Loop v2 設定摘要
    # ============================================================
    print_section_header("Policy Loop v2 - Configuration Summary")
    print_key_value("Config File:", args.config_file)
    print_key_value("Log Path:", args.log_path)
    print_key_value("Output Directory:", args.output_dir)
    print_key_value("Output Filename:", args.file_name)
    print_key_value("Date Range:", f"{config['start_date']} ~ {config['end_date']}")
    print_key_value("Capital:", f"{capital:,.2f}")
    print_key_value("Experiments Count:", len(experiments))
    print_key_value("Min Days:", args.min_days)
    print_key_value("Min Trades:", args.min_trades)
    print_key_value("Sharpe Weight:", args.sharpe_weight)
    print_key_value("MaxDD Weight:", args.maxdd_weight)
    
    # ============================================================
    # 步驟 2: 執行批次回測
    # ============================================================
    print_section_header(f"Step 1: Running {len(experiments)} Experiments")
    
    results = []
    for i, exp in enumerate(experiments, 1):
        print(f"\n[{i}/{len(experiments)}] Running: {exp['name']}...")
        
        decision_config = {
            "long_budget": exp["long_budget"],
            "short_budget": exp["short_budget"],
            "max_weight_per_symbol": exp["max_weight_per_symbol"],
            "min_score": exp["min_score"],
            "allow_short": exp["allow_short"],
        }
        
        try:
            result = run_path_a_backtest(
                start_date=start_date,
                end_date=end_date,
                capital=capital,
                decision_config=decision_config,
            )
            
            # 寫入 log（模擬 run_path_a_v1.py 的邏輯）
            config_params = {
                "initial_capital": capital,
                "long_budget": decision_config["long_budget"],
                "short_budget": decision_config["short_budget"],
                "max_weight_per_symbol": decision_config["max_weight_per_symbol"],
                "min_score": decision_config["min_score"],
                "allow_short": decision_config["allow_short"],
            }
            
            run_id = uuid.uuid4().hex
            log_record = PathAEngineV1().generate_log_record(
                run_id=run_id,
                config_params=config_params,
                backtest_result=result,
            )
            
            # 寫入 JSON Lines 檔案
            log_file_path = project_root / args.log_path
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file_path, "a", encoding="utf-8") as f:
                json_line = json.dumps(log_record, ensure_ascii=False)
                f.write(json_line + "\n")
            
            results.append({
                "name": exp["name"],
                "result": result,
                "run_id": run_id,
            })
            
            print(f"      ✅ Completed: Sharpe={result.metrics.sharpe_ratio:.4f}, "
                  f"MaxDD={result.metrics.max_drawdown:.2%}, Return={result.metrics.total_return:.2%}")
        
        except Exception as e:
            print(f"      ❌ Failed: {e}")
            continue
    
    # ============================================================
    # 區塊 2: 本次實驗總覽
    # ============================================================
    print_section_header("Step 2: Experiment Summary")
    print_key_value("Total Experiments:", len(results))
    print_key_value("Log File:", args.log_path)
    
    if results:
        print("\nExperiment Results:")
        for r in results:
            metrics = r["result"].metrics
            print(f"  - {r['name']}: Sharpe={metrics.sharpe_ratio:.4f}, "
                  f"MaxDD={metrics.max_drawdown:.2%}, Return={metrics.total_return:.2%}, "
                  f"Trades={metrics.num_long_trades + metrics.num_short_trades}")
    
    # ============================================================
    # 步驟 3: Policy 分析與建議
    # ============================================================
    print_section_header("Step 3: Policy Analysis & Suggestion")
    
    # 構建 PolicyScoreConfig
    score_config = PolicyScoreConfig(
        sharpe_weight=args.sharpe_weight,
        max_dd_weight=args.maxdd_weight,
        min_days=args.min_days,
        min_trades=args.min_trades,
    )
    
    # 構建 PolicyWriterV1
    writer = PolicyWriterV1(
        log_path=args.log_path,
        score_config=score_config,
        min_days=args.min_days,
        min_trades=args.min_trades,
    )
    
    # 產生建議
    suggestion = writer.generate_suggestion(
        start_date=config["start_date"],
        end_date=config["end_date"],
        top_k=3,
    )
    
    if suggestion is None:
        print("\n❌ No valid experiments found.")
        print("   - Check if log file has valid experiments")
        print("   - Try relaxing --min-days and --min-trades filters")
        sys.exit(1)
    
    # ============================================================
    # 區塊 3: 最佳實驗摘要
    # ============================================================
    print_section_header("Step 4: Best Experiment Summary")
    print_key_value("Run ID:", suggestion.run_id)
    print_key_value("Score:", f"{suggestion.score:.6f}")
    print_key_value("Sharpe Ratio:", f"{suggestion.sharpe_ratio:.4f}")
    print_key_value("Max Drawdown:", f"{suggestion.max_drawdown:.4f} ({suggestion.max_drawdown*100:.2f}%)")
    print_key_value("Total Return:", f"{suggestion.total_return:.4f} ({suggestion.total_return*100:.2f}%)")
    print_key_value("Win Rate:", f"{suggestion.win_rate:.4f} ({suggestion.win_rate*100:.2f}%)")
    print_key_value("Days:", suggestion.num_days)
    print_key_value("Trades:", suggestion.num_trades)
    print("\nSuggested Risk Config:")
    print_key_value("  Long Budget:", f"{suggestion.long_budget:.2f}", indent=2)
    print_key_value("  Short Budget:", f"{suggestion.short_budget:.2f}", indent=2)
    print_key_value("  Max Weight/Symbol:", f"{suggestion.max_weight_per_symbol:.2f}", indent=2)
    print_key_value("  Min Score:", f"{suggestion.min_score:.2f}", indent=2)
    print_key_value("  Allow Short:", suggestion.allow_short, indent=2)
    
    # ============================================================
    # 步驟 4: 寫出建議 RiskConfig
    # ============================================================
    output_path = writer.write_risk_config_file(
        suggestion=suggestion,
        output_dir=args.output_dir,
        file_name=args.file_name,
    )
    
    # ============================================================
    # 區塊 4: 產生的 YAML 檔案路徑
    # ============================================================
    print_section_header("Step 5: Generated RiskConfig File")
    print_key_value("Output Path:", output_path)
    print_key_value("File Name:", args.file_name)
    
    # ============================================================
    # 步驟 5: Final Backtest 驗證
    # ============================================================
    print_section_header("Step 6: Final Backtest Verification")
    print(f"\nRunning final backtest with suggested config...")
    print(f"  Date Range: {final_start_date} ~ {final_end_date}")
    print(f"  Config File: {output_path}")
    
    # 載入建議的 RiskConfig
    try:
        risk_config = load_risk_config(output_path)
    except Exception as e:
        print(f"\n❌ Error loading RiskConfig: {e}")
        sys.exit(1)
    
    # 執行 Final Backtest
    try:
        final_result = run_path_a_backtest(
            start_date=final_start_date,
            end_date=final_end_date,
            capital=capital,
            decision_config=risk_config,
        )
        
        # ============================================================
        # 區塊 5: Final Backtest 結果
        # ============================================================
        print_section_header("Final Backtest Results")
        
        metrics = final_result.metrics
        
        print("\n📊 Performance Metrics:")
        print_key_value("Total Return:", f"{metrics.total_return:8.2%}")
        print_key_value("Annualized Return:", f"{metrics.annualized_return:8.2%}")
        print_key_value("Annualized Volatility:", f"{metrics.annualized_volatility:8.2%}")
        print_key_value("Sharpe Ratio:", f"{metrics.sharpe_ratio:8.4f}")
        print_key_value("Max Drawdown:", f"{metrics.max_drawdown:8.2%}")
        print_key_value("Win Rate:", f"{metrics.win_rate:8.2%}")
        
        print("\n💰 Capital:")
        print_key_value("Initial Capital:", f"{final_result.initial_capital:,.2f}")
        print_key_value("Final Capital:", f"{final_result.final_capital:,.2f}")
        
        print("\n📈 Trading:")
        print_key_value("Total Commission:", f"{metrics.total_commission:,.2f}")
        print_key_value("Long Trades:", metrics.num_long_trades)
        print_key_value("Short Trades:", metrics.num_short_trades)
        print_key_value("Total Trades:", metrics.num_long_trades + metrics.num_short_trades)
        print_key_value("Trading Days:", len(final_result.daily_equity_curve))
        
        print("\n" + "=" * 70)
        print("✅ Policy Loop v2 completed successfully!")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running final backtest: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

