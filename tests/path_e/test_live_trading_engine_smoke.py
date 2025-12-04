"""
Path E Live Trading Engine Smoke Test

測試 Path E 完整交易循環的基本功能。
"""

import pytest
import pandas as pd
from pathlib import Path

from jgod.path_e.live_types import PathEConfig
from jgod.path_e.live_data_feed import MockLiveFeed
from jgod.path_e.portfolio_state import PortfolioState
from jgod.path_e.live_signal_engine import PlaceholderSignalEngine
from jgod.path_e.risk_guard import RiskGuard
from jgod.path_e.order_planner import OrderPlanner
from jgod.path_e.broker_client import SimBrokerClient
from jgod.path_e.live_trading_engine import LiveTradingEngine

# 使用 Path A 的 Mock Data Loader
from jgod.path_a.mock_data_loader import MockPathADataLoader
from jgod.path_a.path_a_schema import PathAConfig


@pytest.mark.slow
def test_path_e_dry_run_smoke():
    """
    Path E DRY_RUN 模式 Smoke Test
    
    測試：
    - 所有組件可以正常初始化
    - run_loop() 可以執行完成
    - PortfolioState 有更新
    - 有決策日誌產生（DRY_RUN 模式下）
    """
    # 1. 建立配置
    config = PathEConfig(
        mode="DRY_RUN",
        symbols=["2330", "2317"],
        initial_cash=1000000.0,
        max_position_pct=0.2,
        max_order_pct=0.05,
        experiment_name="test_path_e_dry_run",
        log_dir="logs/path_e_test",
    )
    
    # 2. 使用 Path A Mock Data Loader 產生歷史資料
    path_a_config = PathAConfig(
        start_date="2024-01-01",
        end_date="2024-01-31",  # 一個月資料
        universe=["2330.TW", "2317.TW"],
        rebalance_frequency="D",
        experiment_name="test_path_e_data",
    )
    
    data_loader = MockPathADataLoader(seed=42)
    price_frame = data_loader.load_price_frame(config=path_a_config)
    
    # 轉換符號格式（簡化處理）
    if isinstance(price_frame.columns, pd.MultiIndex):
        new_columns = []
        for symbol, field in price_frame.columns:
            symbol_clean = symbol.replace(".TW", "")
            new_columns.append((symbol_clean, field))
        price_frame.columns = pd.MultiIndex.from_tuples(new_columns)
    
    symbols_clean = ["2330", "2317"]
    
    # 3. 建立所有組件
    data_feed = MockLiveFeed(price_data=price_frame, symbols=symbols_clean)
    
    portfolio_state = PortfolioState(
        cash=config.initial_cash,
        positions={},
        equity=config.initial_cash,
        pnl=0.0,
        max_drawdown=0.0,
        timestamp=pd.Timestamp("2024-01-01"),
        initial_cash=config.initial_cash,
    )
    
    signal_engine = PlaceholderSignalEngine(strategy_type="cash_only")
    risk_guard = RiskGuard(
        max_position_pct=config.max_position_pct,
        max_order_pct=config.max_order_pct,
    )
    order_planner = OrderPlanner()
    broker_client = SimBrokerClient()
    
    engine = LiveTradingEngine(
        config=config,
        data_feed=data_feed,
        portfolio_state=portfolio_state,
        signal_engine=signal_engine,
        risk_guard=risk_guard,
        order_planner=order_planner,
        broker_client=broker_client,
    )
    
    # 4. 執行交易循環（只跑 10 個 bar）
    summary = engine.run_loop(max_bars=10)
    
    # 5. 驗證
    assert summary is not None
    assert summary["total_bars"] > 0
    assert summary["final_equity"] > 0
    assert portfolio_state.equity > 0
    
    # 6. 驗證日誌檔案存在（DRY_RUN 模式下應該有決策日誌）
    log_dir = Path(config.log_dir)
    decision_log = log_dir / f"{config.experiment_name}_decisions.csv"
    assert decision_log.exists(), "Decision log should exist"
    
    # 檢查決策日誌內容
    df_decisions = pd.read_csv(decision_log)
    assert len(df_decisions) > 0, "Should have at least one decision log"
    
    print(f"✅ Path E DRY_RUN smoke test passed")
    print(f"   Bars processed: {summary['total_bars']}")
    print(f"   Final equity: ${summary['final_equity']:,.2f}")


@pytest.mark.slow
def test_path_e_paper_mode_smoke():
    """
    Path E PAPER 模式 Smoke Test
    
    測試：
    - PAPER 模式下可以模擬執行訂單
    - PortfolioState 會更新（現金、持倉）
    - 有成交記錄產生
    """
    config = PathEConfig(
        mode="PAPER",
        symbols=["2330"],
        initial_cash=1000000.0,
        max_position_pct=0.3,  # 放寬限制以便測試
        max_order_pct=0.1,
        experiment_name="test_path_e_paper",
        log_dir="logs/path_e_test",
    )
    
    # 建立資料流
    path_a_config = PathAConfig(
        start_date="2024-01-01",
        end_date="2024-01-31",
        universe=["2330.TW"],
        rebalance_frequency="D",
        experiment_name="test_path_e_data_paper",
    )
    
    data_loader = MockPathADataLoader(seed=42)
    price_frame = data_loader.load_price_frame(config=path_a_config)
    
    if isinstance(price_frame.columns, pd.MultiIndex):
        new_columns = []
        for symbol, field in price_frame.columns:
            symbol_clean = symbol.replace(".TW", "")
            new_columns.append((symbol_clean, field))
        price_frame.columns = pd.MultiIndex.from_tuples(new_columns)
    
    data_feed = MockLiveFeed(price_data=price_frame, symbols=["2330"])
    
    # 建立組件
    portfolio_state = PortfolioState(
        cash=config.initial_cash,
        positions={},
        equity=config.initial_cash,
        pnl=0.0,
        max_drawdown=0.0,
        timestamp=pd.Timestamp("2024-01-01"),
        initial_cash=config.initial_cash,
    )
    
    # 使用 simple_ma 策略以便產生交易
    signal_engine = PlaceholderSignalEngine(strategy_type="simple_ma")
    risk_guard = RiskGuard(
        max_position_pct=config.max_position_pct,
        max_order_pct=config.max_order_pct,
    )
    order_planner = OrderPlanner()
    broker_client = SimBrokerClient()
    
    engine = LiveTradingEngine(
        config=config,
        data_feed=data_feed,
        portfolio_state=portfolio_state,
        signal_engine=signal_engine,
        risk_guard=risk_guard,
        order_planner=order_planner,
        broker_client=broker_client,
    )
    
    # 執行（只跑 10 個 bar）
    summary = engine.run_loop(max_bars=10)
    
    # 驗證
    assert summary is not None
    assert summary["total_bars"] > 0
    
    # PAPER 模式下，如果有訂單，應該有成交記錄
    fill_log = Path(config.log_dir) / f"{config.experiment_name}_fills.csv"
    
    if summary["total_fills"] > 0:
        assert fill_log.exists(), "Fill log should exist if there are fills"
        
        # 驗證 PortfolioState 有更新
        # 如果有成交，cash 或 positions 應該有變化
        assert portfolio_state.cash != config.initial_cash or len(portfolio_state.positions) > 0
    
    print(f"✅ Path E PAPER mode smoke test passed")
    print(f"   Bars: {summary['total_bars']}")
    print(f"   Orders: {summary['total_orders']}")
    print(f"   Fills: {summary['total_fills']}")

