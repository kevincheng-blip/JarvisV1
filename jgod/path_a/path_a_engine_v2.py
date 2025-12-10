"""
J-GOD Path A v2 - Backtest Engine with Decision Layer v1/v2 Support

統一入口：整合 Decision Layer v1/v2 的完整回測引擎。

核心功能：
- 從 Strategy Engine 取得 Raw Scores
- 使用 Decision Layer v1/v2 計算 Final Scores
- 生成 PortfolioPlan（基於 Final Score）
- 模擬交易執行（含交易成本與滑價）
- 計算每日 PnL 與資產淨值
- 產出核心績效指標（Sharpe Ratio、Max Drawdown 等）

設計原則：
- Path A Engine V2 整合 Decision Layer，支援版本切換（v1/v2）
- 使用 Final Score 而非 Raw Score 進行排序與權重分配
- 完全依賴 DecisionEngineUnified，支援 v1/v2 版本切換
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Literal

from jgod.decision import PortfolioPlan, PositionPlan
from jgod.decision.engine_unified import DecisionEngineUnified
from jgod.decision.models import RawScoreItem, DecisionOutput
from jgod.decision.config import DecisionConfig
from jgod.strategy import StrategyEngineV1, DailySignalSet, StrategySignal
from jgod.storage.db import get_session
from jgod.storage.models import DailyBar

# Reuse trade execution logic from V1
from jgod.path_a.path_a_engine_v1 import (
    T_COST_RATE,
    SLIPPAGE_LONG,
    SLIPPAGE_SHORT,
    TradeRecord,
    DailyPositionSnapshot,
    PerformanceMetrics,
    BacktestResult,
)


@dataclass
class PathAConfig:
    """Path A Engine V2 Configuration"""
    initial_capital: float = 1_000_000.0
    t_cost_rate: float = T_COST_RATE
    slippage_long: float = SLIPPAGE_LONG
    slippage_short: float = SLIPPAGE_SHORT
    long_budget: float = 0.8
    short_budget: float = 0.2
    max_weight_per_symbol: float = 0.10
    min_score: float = 0.0
    allow_short: bool = True
    decision_config: Optional[DecisionConfig] = None
    knowledge_brain = None


class PathAEngineV2:
    """
    Path A v2 - Backtest Engine with Decision Layer v1/v2 Support
    
    核心功能：
    - 使用 Decision Layer v1/v2 計算 Final Scores
    - 基於 Final Score 生成 PortfolioPlan
    - 模擬交易執行（含交易成本與滑價）
    - 計算每日 PnL 與資產淨值
    - 產出核心績效指標
    """
    
    def __init__(
        self,
        config: Optional[PathAConfig] = None,
        decision_version: Literal["v1", "v2"] = "v2",
    ):
        """
        初始化 Path A Engine V2
        
        Args:
            config: PathAConfig（如果為 None，使用預設配置）
            decision_version: Decision Layer 版本 ("v1" or "v2")
        """
        if config is None:
            config = PathAConfig()
        
        self.config = config
        self.decision_version = decision_version
        
        # 初始化 Decision Engine Unified（支援 v1/v2）
        self.decision_engine = DecisionEngineUnified(
            version=decision_version,
            config=config.decision_config or DecisionConfig(),
            knowledge_brain=config.knowledge_brain,
        )
        
        # 初始化 Strategy Engine
        self.strategy_engine = StrategyEngineV1()
        
        # 當前持倉狀態 {symbol: DailyPositionSnapshot}
        self.positions: Dict[str, DailyPositionSnapshot] = {}
        self.cash = config.initial_capital
        
        # 交易記錄
        self.trades: List[TradeRecord] = []
        
        # 每日淨值曲線
        self.daily_equity_curve: List[Dict] = []
    
    def _get_price(self, symbol: str, date: date) -> Optional[float]:
        """取得指定日期股票的收盤價"""
        session_gen = get_session()
        session = next(session_gen)
        try:
            bar = (
                session.query(DailyBar)
                .filter(
                    DailyBar.symbol == symbol,
                    DailyBar.date == date,
                )
                .first()
            )
            
            if bar and bar.close:
                return float(bar.close)
            return None
        finally:
            pass
    
    def _get_trading_dates(self, start_date: date, end_date: date) -> List[date]:
        """取得交易日列表"""
        session_gen = get_session()
        session = next(session_gen)
        try:
            dates_query = (
                session.query(DailyBar.date)
                .filter(
                    DailyBar.date >= start_date,
                    DailyBar.date <= end_date,
                )
                .distinct()
                .order_by(DailyBar.date)
            )
            
            dates = [row[0] for row in dates_query.all()]
            return sorted(set(dates))
        finally:
            pass
    
    def _calculate_pnl(self, date: date) -> float:
        """計算當日 PnL"""
        pnl = 0.0
        
        for symbol, position in self.positions.items():
            current_price = self._get_price(symbol, date)
            if current_price is None:
                continue
            
            old_market_value = position.market_value
            new_market_value = position.shares * current_price
            
            pnl += (new_market_value - old_market_value)
        
        return pnl
    
    def _execute_trade(
        self,
        symbol: str,
        date: date,
        target_shares: int,
        target_weight: float,
        current_price: float,
        is_long: bool,
    ) -> Optional[TradeRecord]:
        """執行交易（模擬）"""
        current_position = self.positions.get(symbol)
        current_shares = current_position.shares if current_position else 0
        
        current_shares_abs = abs(current_shares) if current_shares != 0 else 0
        target_shares_abs = abs(target_shares)
        is_current_long = (current_shares > 0) if current_shares != 0 else None
        
        if is_long == is_current_long:
            delta_shares_abs = abs(target_shares_abs - current_shares_abs)
            if delta_shares_abs == 0:
                return None
        else:
            if current_shares_abs > 0:
                delta_shares_abs = current_shares_abs
            else:
                delta_shares_abs = target_shares_abs
        
        if delta_shares_abs < 100:
            return None
        
        shares_to_trade = (delta_shares_abs // 100) * 100
        
        if is_long != is_current_long and current_shares_abs > 0:
            if is_current_long:
                side = "SELL"
            else:
                side = "BUY"
        elif is_long:
            if target_shares_abs > current_shares_abs:
                side = "BUY"
            else:
                side = "SELL"
        else:
            if target_shares_abs > current_shares_abs:
                side = "SELL"
            else:
                side = "BUY"
        
        # 計算滑價後的價格
        if side == "BUY":
            execution_price = current_price * (1 + self.config.slippage_long)
        else:
            execution_price = current_price * (1 - self.config.slippage_short)
        
        # 計算交易成本
        trade_value = execution_price * shares_to_trade
        commission = trade_value * self.config.t_cost_rate
        
        # 更新現金
        if side == "BUY":
            self.cash -= (trade_value + commission)
        else:
            self.cash += (trade_value - commission)
        
        # 更新持倉
        if side == "BUY":
            new_shares = current_shares + shares_to_trade if is_long else current_shares - shares_to_trade
        else:
            new_shares = current_shares - shares_to_trade if is_long else current_shares + shares_to_trade
        
        if new_shares == 0:
            self.positions.pop(symbol, None)
        else:
            # 更新或創建持倉
            if symbol in self.positions:
                position = self.positions[symbol]
                total_cost = position.avg_cost * abs(current_shares) + trade_value
                position.shares = new_shares
                position.avg_cost = total_cost / abs(new_shares) if new_shares != 0 else 0.0
                position.current_price = current_price
                position.market_value = abs(new_shares) * current_price
            else:
                self.positions[symbol] = DailyPositionSnapshot(
                    symbol=symbol,
                    shares=new_shares,
                    avg_cost=execution_price,
                    current_price=current_price,
                    market_value=abs(new_shares) * current_price,
                    portfolio_weight=target_weight,
                )
        
        return TradeRecord(
            symbol=symbol,
            date=date,
            side=side,
            shares=shares_to_trade,
            price=execution_price,
            commission=commission,
            slippage_amount=abs(execution_price - current_price) * shares_to_trade,
            reference_weight=target_weight,
        )
    
    def _generate_portfolio_for_date(
        self,
        date: date,
        universe: Optional[List[str]] = None,
    ) -> PortfolioPlan:
        """
        產生指定日期的目標部位配置表（使用 Decision Layer v1/v2）
        
        Args:
            date: 日期
            universe: 股票池（如果為 None，則取得所有有預測的股票）
        
        Returns:
            PortfolioPlan: 目標部位配置表（基於 Final Score）
        """
        # Step 1: 從 Strategy Engine 取得 Raw Signals
        signal_set = self.strategy_engine.generate_signals_for_date(
            date=date,
            universe=universe,
            long_limit=100,
            short_limit=100 if self.config.allow_short else 0,
            min_score=self.config.min_score,
            allow_short=self.config.allow_short,
        )
        
        # Step 2: 轉換為 RawScoreItem
        raw_items: List[RawScoreItem] = []
        
        # Long candidates
        for sig in signal_set.long_candidates:
            if sig.base_score is None or sig.base_score <= 0:
                continue
            if sig.base_score < self.config.min_score:
                continue
            
            raw_items.append(RawScoreItem(
                symbol=sig.symbol,
                date=date,
                raw_score=sig.base_score,
                strategy_scores={sig.sources[0] if sig.sources else "strategy_engine_v1": sig.base_score},
                risk_metrics={},
                context_tags=[],
            ))
        
        # Short candidates
        if self.config.allow_short:
            for sig in signal_set.short_candidates:
                if sig.base_score is None or sig.base_score >= 0:
                    continue
                if abs(sig.base_score) < self.config.min_score:
                    continue
                
                raw_items.append(RawScoreItem(
                    symbol=sig.symbol,
                    date=date,
                    raw_score=sig.base_score,
                    strategy_scores={sig.sources[0] if sig.sources else "strategy_engine_v1": sig.base_score},
                    risk_metrics={},
                    context_tags=[],
                ))
        
        if not raw_items:
            logger.debug(f"No raw items generated for date {date}")
            return PortfolioPlan(
                date=date,
                universe_size=0,
                params={},
                positions=[],
                summary={},
            )
        
        # Step 4: 使用 Decision Layer v1/v2 計算 Final Scores
        logger.debug(f"Processing {len(raw_items)} raw items through Decision Layer {self.decision_version}")
        batch_result = self.decision_engine.decide_for_batch(raw_items)
        decision_outputs = batch_result.items
        
        # Step 5: 分離 Long 和 Short，使用 Final Score 排序
        long_outputs = [
            out for out in decision_outputs
            if out.final_score > 0
        ]
        short_outputs = [
            out for out in decision_outputs
            if out.final_score < 0
        ]
        
        # 按 final_score 排序（降序 for long，升序 for short）
        long_outputs.sort(key=lambda x: x.final_score, reverse=True)
        short_outputs.sort(key=lambda x: x.final_score)
        
        # Step 6: 計算權重分配（基於 Final Score）
        positions: List[PositionPlan] = []
        
        # Long positions
        if long_outputs:
            total_long_score = sum(out.final_score for out in long_outputs)
            if total_long_score > 0:
                for out in long_outputs:
                    # 分配權重基於 final_score
                    weight = (out.final_score / total_long_score) * self.config.long_budget
                    # 應用單檔上限
                    weight = min(weight, self.config.max_weight_per_symbol)
                    
                    if weight > 0:
                        # 找到對應的原始 signal
                        orig_signal = next(
                            (sig for sig in signal_set.long_candidates if sig.symbol == out.symbol),
                            None
                        )
                        
                        positions.append(PositionPlan(
                            symbol=out.symbol,
                            date=date,
                            side="LONG",
                            target_weight=weight,
                            base_score=out.raw_score,
                            rank_score=out.final_score,  # 使用 final_score 作為 rank_score
                            risk_flags_summary="LOW",  # TODO: 從 decision_output 取得
                            source_signals=orig_signal.sources if orig_signal else ["strategy_engine_v1"],
                        ))
        
        # Short positions
        if short_outputs and self.config.allow_short:
            total_short_score = sum(abs(out.final_score) for out in short_outputs)
            if total_short_score > 0:
                for out in short_outputs:
                    # 分配權重基於 abs(final_score)
                    weight = (abs(out.final_score) / total_short_score) * self.config.short_budget
                    # 應用單檔上限
                    weight = min(weight, self.config.max_weight_per_symbol)
                    
                    if weight > 0:
                        # 找到對應的原始 signal
                        orig_signal = next(
                            (sig for sig in signal_set.short_candidates if sig.symbol == out.symbol),
                            None
                        )
                        
                        positions.append(PositionPlan(
                            symbol=out.symbol,
                            date=date,
                            side="SHORT",
                            target_weight=-weight,  # Short 為負
                            base_score=out.raw_score,
                            rank_score=abs(out.final_score),  # 使用 abs(final_score) 作為 rank_score
                            risk_flags_summary="LOW",  # TODO: 從 decision_output 取得
                            source_signals=orig_signal.sources if orig_signal else ["strategy_engine_v1"],
                        ))
        
        # 按 abs(target_weight) 排序
        positions.sort(key=lambda x: abs(x.target_weight), reverse=True)
        
        return PortfolioPlan(
            date=date,
            universe_size=len(raw_items),
            params={
                "decision_version": self.decision_version,
                "long_budget": self.config.long_budget,
                "short_budget": self.config.short_budget,
                "max_weight_per_symbol": self.config.max_weight_per_symbol,
            },
            positions=positions,
            summary={
                "num_long": len([p for p in positions if p.side == "LONG"]),
                "num_short": len([p for p in positions if p.side == "SHORT"]),
            },
        )
    
    def _rebalance_portfolio(self, portfolio_plan: PortfolioPlan, date: date, equity: float):
        """重新平衡投資組合"""
        for pos_plan in portfolio_plan.positions:
            symbol = pos_plan.symbol
            target_weight = pos_plan.target_weight
            is_long = target_weight > 0
            
            current_price = self._get_price(symbol, date)
            if current_price is None:
                continue
            
            target_market_value = equity * abs(target_weight)
            target_shares = int(target_market_value / current_price)
            
            if is_long:
                target_shares = target_shares
            else:
                target_shares = -target_shares
            
            trade = self._execute_trade(
                symbol=symbol,
                date=date,
                target_shares=target_shares,
                target_weight=abs(target_weight),
                current_price=current_price,
                is_long=is_long,
            )
            
            if trade:
                self.trades.append(trade)
    
    def _calculate_metrics(self, equity_curve: List[Dict]) -> PerformanceMetrics:
        """計算績效指標（重用 V1 邏輯）"""
        from jgod.path_a.path_a_engine_v1 import PathAEngineV1
        
        # 創建臨時 V1 引擎來重用計算邏輯
        temp_engine = PathAEngineV1()
        return temp_engine._calculate_metrics(equity_curve)
    
    def run_backtest(
        self,
        start_date: date,
        end_date: date,
    ) -> BacktestResult:
        """
        執行回測
        
        Args:
            start_date: 開始日期
            end_date: 結束日期
        
        Returns:
            BacktestResult: 回測結果
        """
        # 重置狀態
        self.positions = {}
        self.cash = self.config.initial_capital
        self.trades = []
        self.daily_equity_curve = []
        
        # 取得交易日列表
        trading_dates = self._get_trading_dates(start_date, end_date)
        
        if not trading_dates:
            # 沒有交易日，回傳空結果
            return BacktestResult(
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.config.initial_capital,
                final_capital=self.config.initial_capital,
                daily_equity_curve=[],
                metrics=PerformanceMetrics(
                    annualized_return=0.0,
                    annualized_volatility=0.0,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    win_rate=0.0,
                    total_return=0.0,
                    total_commission=sum(t.commission for t in self.trades),
                    num_long_trades=len([t for t in self.trades if t.side == "BUY"]),
                    num_short_trades=len([t for t in self.trades if t.side == "SELL"]),
                ),
            )
        
        # 逐日執行回測
        for i, trade_date in enumerate(trading_dates):
            # 如果是第一天，初始化淨值
            if i == 0:
                equity_before_rebalance = self.config.initial_capital
            else:
                # 非第一天：先更新所有持倉的當前價格，計算當日 PnL
                for symbol in list(self.positions.keys()):
                    position = self.positions[symbol]
                    current_price = self._get_price(symbol, trade_date)
                    if current_price:
                        position.current_price = current_price
                        position.market_value = abs(position.shares) * current_price
                
                # 計算當前資產淨值（未調整倉位前）
                total_market_value = sum(pos.market_value for pos in self.positions.values())
                equity_before_rebalance = total_market_value + self.cash
            
            # 取得目標部位配置表（使用 Decision Layer v1/v2）
            try:
                portfolio_plan = self._generate_portfolio_for_date(
                    date=trade_date,
                    universe=None,
                )
            except Exception as e:
                # 如果無法取得 PortfolioPlan，跳過這一天（維持現有持倉）
                portfolio_plan = None
            
            # 重新平衡投資組合（如果有目標配置）
            if portfolio_plan and portfolio_plan.positions:
                self._rebalance_portfolio(portfolio_plan, trade_date, equity_before_rebalance)
            
            # 計算最終資產淨值（調整倉位後）
            for symbol in list(self.positions.keys()):
                position = self.positions[symbol]
                current_price = self._get_price(symbol, trade_date)
                if current_price:
                    position.current_price = current_price
                    position.market_value = abs(position.shares) * current_price
            
            total_market_value = sum(pos.market_value for pos in self.positions.values())
            equity_after_rebalance = total_market_value + self.cash
            
            # 記錄每日淨值曲線
            self.daily_equity_curve.append({
                "date": trade_date.isoformat(),
                "equity_value": equity_after_rebalance,
                "cash": self.cash,
                "market_value": total_market_value,
            })
        
        # 計算最終資本
        final_capital = equity_after_rebalance if self.daily_equity_curve else self.config.initial_capital
        
        # 計算績效指標
        metrics = self._calculate_metrics(self.daily_equity_curve)
        
        # 組裝回測結果
        return BacktestResult(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.config.initial_capital,
            final_capital=final_capital,
            daily_equity_curve=self.daily_equity_curve,
            metrics=metrics,
            trades=self.trades,
        )

