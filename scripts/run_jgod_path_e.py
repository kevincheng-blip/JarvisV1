#!/usr/bin/env python3
"""
Path E CLI

執行 Path E Live Trading Engine。

Usage:
    # Paper Trading Mode
    PYTHONPATH=. python3 scripts/run_jgod_path_e.py \
        --config configs/path_e/path_e_tw_paper_v1.yaml

    # Dry Run Mode
    PYTHONPATH=. python3 scripts/run_jgod_path_e.py \
        --config configs/path_e/path_e_tw_paper_v1.yaml \
        --mode DRY_RUN
"""

from __future__ import annotations

import argparse
import yaml
import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import logging

from jgod.path_e.live_types import PathEConfig
from jgod.path_e.live_data_feed import MockLiveFeed
from jgod.path_e.portfolio_state import PortfolioState
from jgod.path_e.live_signal_engine import PlaceholderSignalEngine
from jgod.path_e.risk_guard import RiskGuard
from jgod.path_e.order_planner import OrderPlanner
from jgod.path_e.broker_client import SimBrokerClient
from jgod.path_e.live_trading_engine import LiveTradingEngine

# 使用 Path A 的 Mock Data Loader 產生歷史資料
from jgod.path_a.mock_data_loader import MockPathADataLoader
from jgod.path_a.path_a_schema import PathAConfig


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """載入 YAML 配置"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def create_mock_data_feed(config: PathEConfig) -> MockLiveFeed:
    """
    建立 Mock 資料流（使用 Path A 的 Mock Data Loader）
    
    Args:
        config: Path E 配置
    
    Returns:
        MockLiveFeed 實例
    """
    # 使用 Path A 的 Mock Data Loader 產生歷史資料
    path_a_config = PathAConfig(
        start_date="2024-01-01",
        end_date="2024-03-31",  # 3 個月資料
        universe=[f"{s}.TW" for s in config.symbols],  # 轉換為 .TW 格式
        rebalance_frequency="D",
        experiment_name="path_e_data_source",
    )
    
    data_loader = MockPathADataLoader(seed=42)
    price_frame = data_loader.load_price_frame(config=path_a_config)
    
    # 轉換符號格式（從 "2330.TW" 到 "2330"）
    # 這裡簡化處理，假設 price_frame 使用 MultiIndex columns
    if isinstance(price_frame.columns, pd.MultiIndex):
        # 重新命名 symbol 部分（移除 .TW）
        new_columns = []
        for symbol, field in price_frame.columns:
            symbol_clean = symbol.replace(".TW", "")
            new_columns.append((symbol_clean, field))
        price_frame.columns = pd.MultiIndex.from_tuples(new_columns)
    
    # 轉換 symbols 列表（移除 .TW）
    symbols_clean = [s.replace(".TW", "") for s in path_a_config.universe]
    
    return MockLiveFeed(
        price_data=price_frame,
        symbols=symbols_clean,
    )


def parse_args() -> argparse.Namespace:
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description="Run Path E Live Trading Engine"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to YAML config file",
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["DRY_RUN", "PAPER"],
        default=None,
        help="Override mode from config (optional)",
    )
    
    return parser.parse_args()


def main():
    """主函數"""
    args = parse_args()
    
    # 載入配置
    config_dict = load_config(args.config)
    
    # 如果命令列指定了 mode，覆寫配置
    if args.mode:
        config_dict["mode"] = args.mode
    
    # 建立 PathEConfig
    config = PathEConfig(**config_dict)
    
    logger.info(f"Path E Live Trading Engine (mode: {config.mode})")
    logger.info(f"Symbols: {config.symbols}")
    logger.info(f"Initial Cash: {config.initial_cash:,.2f}")
    
    # 1. 建立資料流
    data_feed = create_mock_data_feed(config)
    
    # 2. 建立投資組合狀態
    portfolio_state = PortfolioState(
        cash=config.initial_cash,
        positions={},
        equity=config.initial_cash,
        pnl=0.0,
        max_drawdown=0.0,
        timestamp=pd.Timestamp("2024-01-01"),
        initial_cash=config.initial_cash,
    )
    
    # 3. 建立訊號引擎
    strategy_type = config_dict.get("strategy_params", {}).get("strategy_type", "cash_only")
    signal_engine = PlaceholderSignalEngine(strategy_type=strategy_type)
    
    # 4. 建立風險守衛
    risk_guard = RiskGuard(
        max_position_pct=config.max_position_pct,
        max_order_pct=config.max_order_pct,
    )
    
    # 5. 建立訂單規劃器
    order_planner = OrderPlanner()
    
    # 6. 建立券商客戶端
    broker_client = SimBrokerClient()
    
    # 7. 建立交易引擎
    engine = LiveTradingEngine(
        config=config,
        data_feed=data_feed,
        portfolio_state=portfolio_state,
        signal_engine=signal_engine,
        risk_guard=risk_guard,
        order_planner=order_planner,
        broker_client=broker_client,
    )
    
    # 8. 執行交易循環
    summary = engine.run_loop()
    
    # 9. 輸出摘要
    print("\n" + "="*60)
    print("Path E Execution Summary")
    print("="*60)
    print(f"Initial Cash: ${summary['initial_cash']:,.2f}")
    print(f"Final Equity: ${summary['final_equity']:,.2f}")
    print(f"P&L: ${summary['pnl']:,.2f} ({summary['pnl_pct']:.2f}%)")
    print(f"Max Drawdown: {summary['max_drawdown']:.2f}%")
    print(f"Total Bars: {summary['total_bars']}")
    print(f"Total Orders: {summary['total_orders']}")
    print(f"Total Fills: {summary['total_fills']}")
    print("="*60)
    print(f"\nLogs saved to: {config.log_dir}")
    print(f"  - Decisions: {engine.decision_log_path}")
    print(f"  - Orders: {engine.order_log_path}")
    print(f"  - Fills: {engine.fill_log_path}")


if __name__ == "__main__":
    main()

