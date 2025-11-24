"""
J-GOD CLI 總指揮系統
"""
import argparse
import sys
from pathlib import Path
from typing import Optional

from jgod.code_intel.scanner import scan_project, write_markdown_report
from jgod.code_intel.todo_extractor import TodoExtractor
from jgod.code_intel.insight_engine import InsightEngine
from jgod.war_room.decision_engine import DecisionEngine
from jgod.market.market_status import MarketStatus


def cmd_status(args) -> int:
    """顯示系統狀態"""
    import os
    
    print("=== J-GOD 系統狀態 ===\n")
    
    # 市場狀態
    market_status = MarketStatus()
    status = market_status.get_market_status()
    
    print("📈 市場狀態：")
    print(f"  台股：{'開盤' if status['taiwan']['is_open'] else '休市'}")
    print(f"  美股：{'開盤' if status['us']['is_open'] else '休市'}")
    print()
    
    # 模組狀態
    print("🔧 模組狀態：")
    modules = [
        ("Market Data Engine", "jgod/market"),
        ("Strategy Engine", "jgod/strategy"),
        ("Risk Engine", "jgod/risk"),
        ("Execution Engine", "jgod/execution"),
        ("War Room Engine", "jgod/war_room"),
        ("Code Intelligence", "jgod/code_intel"),
        ("Prediction Engine", "jgod/prediction"),
        ("Diagnostics", "jgod/diagnostics"),
    ]
    
    for name, path in modules:
        module_path = Path(path)
        if module_path.exists():
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name} (未找到)")
    
    print()
    
    # 環境變數檢查
    print("🔑 環境變數狀態：")
    env_vars = {
        "OPENAI_API_KEY": "OpenAI",
        "ANTHROPIC_API_KEY": "Claude",
        "GOOGLE_API_KEY": "Gemini",
        "PERPLEXITY_API_KEY": "Perplexity",
        "FINMIND_TOKEN": "FinMind",
    }
    
    for env_var, name in env_vars.items():
        exists = os.getenv(env_var) is not None and os.getenv(env_var).strip() != ""
        status_icon = "✅" if exists else "❌"
        print(f"  {status_icon} {name}: {'已設定' if exists else '未設定'}")
    
    print()
    
    # 系統地圖檢查
    print("📄 文件狀態：")
    system_map_path = Path("docs/JGOD_system_map.md")
    if system_map_path.exists():
        print(f"  ✅ 系統地圖：{system_map_path}")
    else:
        print(f"  ❌ 系統地圖：未找到")
    
    print()
    
    # 主要路徑
    print("📂 主要路徑：")
    project_root = Path.cwd()
    print(f"  專案根目錄：{project_root}")
    print(f"  Streamlit 入口：{project_root / 'jgod' / 'war_room' / 'war_room_app.py'}")
    print(f"  CLI 入口：{project_root / 'jgod' / 'cli.py'}")
    
    return 0


def cmd_scan(args) -> int:
    """掃描專案"""
    print("=== 掃描專案 ===\n")
    
    files = scan_project()
    
    print(f"總共掃描了 {len(files)} 個檔案\n")
    
    if args.write_report:
        report_path = Path(args.report_path)
        write_markdown_report(files, report_path)
        print(f"✅ 已產生系統地圖：{report_path}")
    else:
        # 顯示前 20 個檔案
        print("path ┊ ext ┊ size")
        print("-" * 60)
        
        for file_summary in files[:20]:
            size_str = f"{file_summary.size_bytes:,} B"
            print(f"{file_summary.relative_path} ┊ {file_summary.extension} ┊ {size_str}")
        
        if len(files) > 20:
            print(f"\n... 還有 {len(files) - 20} 個檔案未顯示")
    
    return 0


def cmd_trade(args) -> int:
    """交易模擬"""
    print("=== 交易模擬 ===\n")
    
    if args.action == "simulate":
        print("交易模擬功能開發中...")
        print("將整合 Strategy Engine、Risk Engine 和 Execution Engine")
    else:
        print(f"未知的交易動作：{args.action}")
        return 1
    
    return 0


def cmd_warroom(args) -> int:
    """戰情室"""
    print("=== AI 戰情室 ===\n")
    
    if not args.question:
        print("請提供問題（使用 --question 參數）")
        return 1
    
    decision_engine = DecisionEngine()
    
    print(f"問題：{args.question}\n")
    print("正在諮詢 AI 幕僚...\n")
    
    consensus = decision_engine.make_decision(
        question=args.question,
        stock_id=args.stock_id,
        selected_providers=args.providers.split(",") if args.providers else None,
    )
    
    print("=== 共識決策 ===")
    print(f"方向：{consensus.direction}")
    print(f"信心度：{consensus.confidence:.2%}")
    print(f"\n推理：\n{consensus.reasoning}")
    print(f"\n支持意見：{len(consensus.supporting_opinions)}")
    print(f"反對意見：{len(consensus.opposing_opinions)}")
    
    return 0


def cmd_todo(args) -> int:
    """提取 TODO"""
    print("=== 提取 TODO ===\n")
    
    extractor = TodoExtractor()
    root = Path(".") if args.root is None else Path(args.root)
    
    todos = extractor.extract_from_directory(root)
    
    if args.output:
        output_path = Path(args.output)
        content = extractor.generate_todo_list(todos)
        output_path.write_text(content, encoding="utf-8")
        print(f"✅ 已寫入 TODO 清單：{output_path}")
    else:
        print(extractor.generate_todo_list(todos))
    
    return 0


def cmd_insight(args) -> int:
    """系統洞察"""
    print("=== 系統洞察 ===\n")
    
    engine = InsightEngine()
    root = Path(".") if args.root is None else Path(args.root)
    
    if args.output:
        output_path = Path(args.output)
        report = engine.generate_insight_report(root)
        output_path.write_text(report, encoding="utf-8")
        print(f"✅ 已寫入洞察報告：{output_path}")
    else:
        print(engine.generate_insight_report(root))
    
    return 0


def main():
    """主函式"""
    parser = argparse.ArgumentParser(
        description="J-GOD 股神作戰系統 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # status 命令
    status_parser = subparsers.add_parser("status", help="顯示系統狀態")
    status_parser.set_defaults(func=cmd_status)
    
    # scan 命令
    scan_parser = subparsers.add_parser("scan", help="掃描專案")
    scan_parser.add_argument("--write-report", action="store_true", help="產生系統地圖")
    scan_parser.add_argument("--report-path", default="docs/JGOD_system_map.md", help="報告路徑")
    scan_parser.set_defaults(func=cmd_scan)
    
    # trade 命令
    trade_parser = subparsers.add_parser("trade", help="交易模擬")
    trade_parser.add_argument("action", choices=["simulate"], help="交易動作")
    trade_parser.set_defaults(func=cmd_trade)
    
    # warroom 命令
    warroom_parser = subparsers.add_parser("warroom", help="AI 戰情室")
    warroom_parser.add_argument("--question", required=True, help="問題")
    warroom_parser.add_argument("--stock-id", help="股票代號")
    warroom_parser.add_argument("--providers", help="AI 提供者（逗號分隔，例如：gpt,claude）")
    warroom_parser.set_defaults(func=cmd_warroom)
    
    # todo 命令
    todo_parser = subparsers.add_parser("todo", help="提取 TODO")
    todo_parser.add_argument("--root", help="專案根目錄")
    todo_parser.add_argument("--output", help="輸出路徑")
    todo_parser.set_defaults(func=cmd_todo)
    
    # insight 命令
    insight_parser = subparsers.add_parser("insight", help="系統洞察")
    insight_parser.add_argument("--root", help="專案根目錄")
    insight_parser.add_argument("--output", help="輸出路徑")
    insight_parser.set_defaults(func=cmd_insight)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        return args.func(args)
    except Exception as e:
        print(f"錯誤：{e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

