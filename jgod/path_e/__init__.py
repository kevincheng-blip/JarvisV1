"""
Path E v1 - Live Trading Engine

Path E 是 J-GOD 系統中的即時交易引擎，負責在「現在」執行策略決策並管理實際的投資組合。

v1 特點：
- 支援 DRY_RUN 和 PAPER 模式
- 使用 MockLiveFeed 從歷史資料 replay
- 使用 SimBrokerClient 模擬交易執行
- 簡單 placeholder 策略（尚未整合 Path D policy）

Reference:
- spec/JGOD_PathEEngine_Spec.md
"""

from jgod.path_e.live_types import (
    LiveBar,
    LiveDecision,
    PlannedOrder,
    PathEConfig,
)
from jgod.path_e.portfolio_state import PortfolioState
from jgod.path_e.live_data_feed import LiveDataFeed, MockLiveFeed
from jgod.path_e.live_signal_engine import LiveSignalEngine
from jgod.path_e.risk_guard import RiskGuard
from jgod.path_e.order_planner import OrderPlanner
from jgod.path_e.broker_client import BrokerClient, SimBrokerClient
from jgod.path_e.live_trading_engine import LiveTradingEngine

__all__ = [
    "LiveBar",
    "LiveDecision",
    "PlannedOrder",
    "PathEConfig",
    "PortfolioState",
    "LiveDataFeed",
    "MockLiveFeed",
    "LiveSignalEngine",
    "RiskGuard",
    "OrderPlanner",
    "BrokerClient",
    "SimBrokerClient",
    "LiveTradingEngine",
]

