"""
Live Trading Engine for Path E

協調所有模組，執行完整的即時交易循環。
"""

from __future__ import annotations

from typing import Dict, List, Optional
import pandas as pd
import logging
from pathlib import Path
import csv

from jgod.path_e.live_types import PathEConfig, LiveBar, LiveDecision, PlannedOrder, Fill
from jgod.path_e.live_data_feed import LiveDataFeed
from jgod.path_e.portfolio_state import PortfolioState
from jgod.path_e.live_signal_engine import LiveSignalEngine
from jgod.path_e.risk_guard import RiskGuard
from jgod.path_e.order_planner import OrderPlanner
from jgod.path_e.broker_client import BrokerClient


logger = logging.getLogger(__name__)


class LiveTradingEngine:
    """
    即時交易引擎
    
    協調所有模組，執行完整的即時交易循環。
    """
    
    def __init__(
        self,
        config: PathEConfig,
        data_feed: LiveDataFeed,
        portfolio_state: PortfolioState,
        signal_engine: LiveSignalEngine,
        risk_guard: RiskGuard,
        order_planner: OrderPlanner,
        broker_client: BrokerClient,
    ):
        """
        初始化 Live Trading Engine
        
        Args:
            config: Path E 配置
            data_feed: 資料流
            portfolio_state: 投資組合狀態
            signal_engine: 訊號引擎
            risk_guard: 風險守衛
            order_planner: 訂單規劃器
            broker_client: 券商客戶端
        """
        self.config = config
        self.data_feed = data_feed
        self.portfolio_state = portfolio_state
        self.signal_engine = signal_engine
        self.risk_guard = risk_guard
        self.order_planner = order_planner
        self.broker_client = broker_client
        
        # 日誌檔案
        self.log_dir = Path(config.log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化日誌檔案
        self.decision_log_path = self.log_dir / f"{config.experiment_name}_decisions.csv"
        self.order_log_path = self.log_dir / f"{config.experiment_name}_orders.csv"
        self.fill_log_path = self.log_dir / f"{config.experiment_name}_fills.csv"
        
        self._init_log_files()
    
    def _init_log_files(self) -> None:
        """初始化日誌檔案（寫入 header）"""
        # Decision log
        with open(self.decision_log_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "symbol", "target_weight", "strategy_type", "equity"
            ])
        
        # Order log
        with open(self.order_log_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "symbol", "side", "qty", "price_type", "status"
            ])
        
        # Fill log
        with open(self.fill_log_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "symbol", "side", "qty", "fill_price", "slippage", "commission"
            ])
    
    def _log_decision(self, decision: LiveDecision) -> None:
        """記錄決策"""
        with open(self.decision_log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            timestamp = self.portfolio_state.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            strategy_type = decision.meta.get("strategy_type", "unknown")
            
            for symbol, weight in decision.target_weights.items():
                writer.writerow([
                    timestamp,
                    symbol,
                    f"{weight:.4f}",
                    strategy_type,
                    f"{self.portfolio_state.equity:.2f}",
                ])
            
            # 如果沒有目標權重（全部現金），也要記錄一行
            if not decision.target_weights:
                writer.writerow([
                    timestamp,
                    "CASH",
                    "1.0",
                    strategy_type,
                    f"{self.portfolio_state.equity:.2f}",
                ])
    
    def _log_order(self, order: PlannedOrder, status: str) -> None:
        """記錄訂單"""
        with open(self.order_log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                order.ts.strftime("%Y-%m-%d %H:%M:%S"),
                order.symbol,
                order.side,
                order.qty,
                order.price_type,
                status,
            ])
    
    def _log_fill(self, fill: Fill) -> None:
        """記錄成交"""
        with open(self.fill_log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                fill.filled_time.strftime("%Y-%m-%d %H:%M:%S"),
                fill.order.symbol,
                fill.order.side,
                fill.filled_quantity,
                f"{fill.filled_price:.2f}",
                f"{fill.slippage:.2f}",
                f"{fill.commission:.2f}",
            ])
    
    def run_loop(self, max_bars: Optional[int] = None) -> Dict[str, float]:
        """
        執行主要交易循環
        
        Args:
            max_bars: 最大執行 bar 數（None 表示執行到資料結束）
        
        Returns:
            執行摘要統計 {equity, pnl, max_drawdown, total_trades, ...}
        """
        bar_count = 0
        total_orders = 0
        total_fills = 0
        
        logger.info(f"Starting Live Trading Engine (mode: {self.config.mode})")
        
        while self.data_feed.has_next_any():
            if max_bars is not None and bar_count >= max_bars:
                break
            
            # 1. 從資料流取得最新 bar（所有標的）
            latest_bars = self.data_feed.get_latest_bars()
            
            if not latest_bars:
                # 沒有更多資料
                break
            
            # 更新時間戳記（使用第一個 bar 的時間）
            first_bar = next(iter(latest_bars.values()))
            self.portfolio_state.timestamp = first_bar.ts
            
            # 2. 更新 PortfolioState 市值（用最新價格）
            latest_prices = {symbol: bar.close for symbol, bar in latest_bars.items()}
            self.portfolio_state.revalue(latest_prices)
            
            logger.info(
                f"Bar {bar_count + 1}: {first_bar.ts.strftime('%Y-%m-%d')} "
                f"Equity: {self.portfolio_state.equity:.2f}"
            )
            
            # 3. 生成決策
            decision = self.signal_engine.generate_decision(
                portfolio_state=self.portfolio_state,
                latest_bars=latest_bars,
            )
            
            # 記錄決策
            self._log_decision(decision)
            
            # 4. 規劃訂單
            proposed_orders = self.order_planner.plan_orders(
                portfolio_state=self.portfolio_state,
                target_weights=decision.target_weights,
                latest_prices=latest_prices,
            )
            
            # 5. 風險過濾
            filtered_orders = self.risk_guard.filter_orders(
                portfolio_state=self.portfolio_state,
                proposed_orders=proposed_orders,
                latest_prices=latest_prices,
            )
            
            total_orders += len(filtered_orders)
            
            # 6. 執行訂單
            if self.config.mode == "DRY_RUN":
                # DRY_RUN 模式：只記錄，不執行
                for order in filtered_orders:
                    self._log_order(order, "DRY_RUN")
                logger.info(f"DRY_RUN: {len(filtered_orders)} orders planned (not executed)")
            
            elif self.config.mode == "PAPER":
                # PAPER 模式：模擬執行
                for order in filtered_orders:
                    self._log_order(order, "PLANNED")
                    
                    # 取得當前價格
                    current_price = latest_prices.get(order.symbol)
                    if current_price is None:
                        logger.warning(f"Price not found for {order.symbol}, skipping order")
                        continue
                    
                    # 提交訂單（模擬）
                    fill = self.broker_client.submit_order(order, current_price)
                    if fill:
                        # 更新 PortfolioState
                        self.portfolio_state.update_from_fill(
                            order=order,
                            fill_price=fill.filled_price,
                            commission=fill.commission,
                        )
                        
                        # 記錄成交
                        self._log_fill(fill)
                        total_fills += 1
                
                logger.info(f"PAPER: {len(filtered_orders)} orders executed")
            else:
                logger.warning(f"Unknown mode: {self.config.mode}, skipping order execution")
            
            bar_count += 1
        
        # 最終更新淨值
        if latest_bars:
            latest_prices = {symbol: bar.close for symbol, bar in latest_bars.items()}
            self.portfolio_state.revalue(latest_prices)
        
        logger.info(f"Live Trading Engine completed: {bar_count} bars processed")
        
        # 返回摘要統計
        return {
            "final_equity": self.portfolio_state.equity,
            "initial_cash": self.portfolio_state.initial_cash,
            "pnl": self.portfolio_state.pnl,
            "pnl_pct": (self.portfolio_state.pnl / self.portfolio_state.initial_cash) * 100.0,
            "max_drawdown": self.portfolio_state.max_drawdown * 100.0,  # 轉為百分比
            "total_bars": bar_count,
            "total_orders": total_orders,
            "total_fills": total_fills,
        }

