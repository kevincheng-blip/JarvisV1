"""
J-GOD Path A v1 - Backtest Engine

統一入口：讀取 DecisionEngineV1 產出的 PortfolioPlan，模擬交易、產出核心績效報告。

核心功能：
- 讀取 DecisionEngineV1 產出的 PortfolioPlan
- 模擬交易執行（含交易成本與滑價）
- 計算每日 PnL 與資產淨值
- 產出核心績效指標（Sharpe Ratio、Max Drawdown 等）

設計原則：
- Path A Engine 本身不進行任何選股或權重計算，只負責模擬執行、計算 PnL、計算績效指標
- 完全依賴 DecisionEngineV1，不直接查詢 Feature Store / Strategy Engine
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd

from jgod.decision import DecisionEngineV1, PortfolioPlan, PositionPlan
from jgod.storage.db import get_session
from jgod.storage.models import DailyBar


# ============================================================================
# 交易成本與滑價模型
# ============================================================================

# 交易成本：單邊手續費與交易稅合計 (0.1425%)
T_COST_RATE = 0.001425

# 滑價：Long 單在收盤價基礎上增加成本 (5 bps)
SLIPPAGE_LONG = 0.0005

# 滑價：Short 單在收盤價基礎上減少收益 (5 bps)
SLIPPAGE_SHORT = 0.0005


@dataclass
class TradeRecord:
    """單筆交易記錄"""
    symbol: str
    date: date
    side: str  # "BUY" / "SELL"
    shares: int  # 交易股數（正數）
    price: float  # 成交價格（含滑價）
    commission: float  # 交易佣金/稅費總額（正數）
    slippage_amount: float  # 滑價影響金額（正數）
    reference_weight: float  # 該筆交易對應的目標權重
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            "symbol": self.symbol,
            "date": self.date.isoformat(),
            "side": self.side,
            "shares": self.shares,
            "price": self.price,
            "commission": self.commission,
            "slippage_amount": self.slippage_amount,
            "reference_weight": self.reference_weight,
        }


@dataclass
class DailyPositionSnapshot:
    """每日持倉快照"""
    symbol: str
    shares: int  # 持有股數
    avg_cost: float  # 平均成本
    current_price: float  # 當日收盤價
    market_value: float  # 當日市值
    portfolio_weight: float  # 當日佔總資產比例（實際部位）
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            "symbol": self.symbol,
            "shares": self.shares,
            "avg_cost": self.avg_cost,
            "current_price": self.current_price,
            "market_value": self.market_value,
            "portfolio_weight": self.portfolio_weight,
        }


@dataclass
class PerformanceMetrics:
    """核心績效指標"""
    annualized_return: float  # 年化報酬率 (APR)
    annualized_volatility: float  # 年化波動率 (Vol)
    sharpe_ratio: float  # Sharpe Ratio (假設無風險利率為 0)
    max_drawdown: float  # 最大回撤 (Max Drawdown)
    win_rate: float  # 日級勝率 (Daily PnL > 0 的交易日比例)
    total_return: float  # 總報酬率
    total_commission: float  # 總交易成本
    num_long_trades: int  # 總 Long 交易次數
    num_short_trades: int  # 總 Short 交易次數
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            "annualized_return": round(self.annualized_return, 4),
            "annualized_volatility": round(self.annualized_volatility, 4),
            "sharpe_ratio": round(self.sharpe_ratio, 4),
            "max_drawdown": round(self.max_drawdown, 4),
            "win_rate": round(self.win_rate, 4),
            "total_return": round(self.total_return, 4),
            "total_commission": round(self.total_commission, 2),
            "num_long_trades": self.num_long_trades,
            "num_short_trades": self.num_short_trades,
        }


@dataclass
class BacktestResult:
    """回測報告總體"""
    start_date: date
    end_date: date
    initial_capital: float
    final_capital: float
    daily_equity_curve: List[Dict]  # 每日淨值曲線
    metrics: PerformanceMetrics
    trades: List[TradeRecord] = field(default_factory=list)  # 所有交易記錄（可選）
    
    def to_dict(self, include_trades: bool = False) -> Dict:
        """轉換為字典"""
        result = {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
            "daily_equity_curve": self.daily_equity_curve,
            "metrics": self.metrics.to_dict(),
        }
        if include_trades:
            result["trades"] = [t.to_dict() for t in self.trades]
        return result


class PathAEngineV1:
    """
    Path A v1 - Backtest Engine
    
    核心功能：
    - 讀取 DecisionEngineV1 產出的 PortfolioPlan
    - 模擬交易執行（含交易成本與滑價）
    - 計算每日 PnL 與資產淨值
    - 產出核心績效指標
    """
    
    def __init__(
        self,
        initial_capital: float = 1_000_000.0,
        t_cost_rate: float = T_COST_RATE,
        slippage_long: float = SLIPPAGE_LONG,
        slippage_short: float = SLIPPAGE_SHORT,
        **decision_config
    ):
        """
        初始化 Path A Engine
        
        Args:
            initial_capital: 初始資金
            t_cost_rate: 交易成本率（單邊）
            slippage_long: Long 滑價率
            slippage_short: Short 滑價率
            **decision_config: 傳給 DecisionEngineV1 的參數
        """
        self.initial_capital = initial_capital
        self.t_cost_rate = t_cost_rate
        self.slippage_long = slippage_long
        self.slippage_short = slippage_short
        
        # 初始化 Decision Engine（如果 decision_config 有提供，會傳給 DecisionEngine）
        # DecisionEngineV1 現在支援從 risk_config_dict 載入參數
        self.decision_engine = DecisionEngineV1(risk_config_dict=decision_config)
        self.decision_config = decision_config
        
        # 當前持倉狀態 {symbol: DailyPositionSnapshot}
        self.positions: Dict[str, DailyPositionSnapshot] = {}
        self.cash = initial_capital
        
        # 交易記錄
        self.trades: List[TradeRecord] = []
        
        # 每日淨值曲線
        self.daily_equity_curve: List[Dict] = []
    
    def _get_price(self, symbol: str, date: date) -> Optional[float]:
        """
        取得指定日期股票的收盤價
        
        Args:
            symbol: 股票代號
            date: 日期
        
        Returns:
            收盤價，如果找不到則回傳 None
        """
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
            pass  # get_session() 使用 generator，會自動關閉
    
    def _get_trading_dates(self, start_date: date, end_date: date) -> List[date]:
        """
        取得交易日列表（從資料庫查詢實際有資料的日期）
        
        Args:
            start_date: 開始日期
            end_date: 結束日期
        
        Returns:
            交易日列表（排序後的唯一日期）
        """
        session_gen = get_session()
        session = next(session_gen)
        try:
            # 從 daily_bars 查詢實際有資料的日期
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
            return sorted(set(dates))  # 確保唯一且排序
        finally:
            pass  # get_session() 使用 generator，會自動關閉
    
    def _calculate_pnl(self, date: date) -> float:
        """
        計算當日 PnL（基於前一日持倉在今日的價格變化）
        
        Args:
            date: 日期
        
        Returns:
            當日 PnL
        """
        pnl = 0.0
        
        for symbol, position in self.positions.items():
            current_price = self._get_price(symbol, date)
            if current_price is None:
                continue
            
            # 計算市值變化
            old_market_value = position.market_value
            new_market_value = position.shares * current_price
            
            # PnL = 市值變化
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
        """
        執行交易（模擬）
        
        Args:
            symbol: 股票代號
            date: 日期
            target_shares: 目標股數（Long 為正，Short 為負）
            target_weight: 目標權重
            current_price: 當前價格
            is_long: 是否為 Long 部位
        
        Returns:
            TradeRecord，如果不需要交易則回傳 None
        """
        # 取得當前持倉
        current_position = self.positions.get(symbol)
        current_shares = current_position.shares if current_position else 0
        
        # 統一處理：在 DailyPositionSnapshot 中，Long 用正數 shares，Short 用負數 shares
        # 但在計算交易時，統一用絕對值處理
        current_shares_abs = abs(current_shares) if current_shares != 0 else 0
        target_shares_abs = abs(target_shares)
        is_current_long = (current_shares > 0) if current_shares != 0 else None
        
        # 如果方向不同，需要先平倉再開倉（簡化版：直接當作需要交易）
        # 如果方向相同，計算股數差異
        if is_long == is_current_long:
            # 方向相同，只計算差異
            delta_shares_abs = abs(target_shares_abs - current_shares_abs)
            if delta_shares_abs == 0:
                return None  # 不需要交易
        else:
            # 方向不同，需要完全換倉（簡化版：先平倉，再開新倉）
            # 這裡先只處理平倉，開新倉會在下一輪處理（簡化實作）
            if current_shares_abs > 0:
                # 需要先平倉
                delta_shares_abs = current_shares_abs
            else:
                # 直接開新倉
                delta_shares_abs = target_shares_abs
        
        # 向下取整至 100 股（整數股）
        if delta_shares_abs < 100:
            # 如果變動量小於 100 股，不執行交易
            return None
        
        shares_to_trade = (delta_shares_abs // 100) * 100
        
        # 決定交易方向
        # 如果方向不同，先平倉
        if is_long != is_current_long and current_shares_abs > 0:
            # 方向轉換：先平倉
            if is_current_long:
                side = "SELL"  # Long 平倉
            else:
                side = "BUY"  # Short 平倉
        elif is_long:
            # Long 部位
            if target_shares_abs > current_shares_abs:
                side = "BUY"  # 增加 Long 部位
            else:
                side = "SELL"  # 減少 Long 部位
        else:
            # Short 部位
            if target_shares_abs > current_shares_abs:
                side = "SELL"  # 增加空單（借券賣出）
            else:
                side = "BUY"  # 減少空單（買回平倉）
        
        # 計算成交價格（含滑價）
        if is_long:
            if side == "BUY":
                # Long 買入：價格上漲（增加成本）
                execution_price = current_price * (1 + self.slippage_long)
            else:
                # Long 賣出：價格下跌（減少收益）
                execution_price = current_price * (1 - self.slippage_long)
        else:
            # Short 部位
            if side == "SELL":
                # Short 賣出（借券）：價格下跌（減少收益）
                execution_price = current_price * (1 - self.slippage_short)
            else:
                # Short 買回（平倉）：價格上漲（增加成本）
                execution_price = current_price * (1 + self.slippage_short)
        
        # 計算交易金額
        trade_value = execution_price * shares_to_trade
        
        # 計算佣金（雙邊：買入 + 賣出各一次）
        commission = trade_value * self.t_cost_rate * 2
        
        # 計算滑價影響金額
        slippage_amount = abs(trade_value - (current_price * shares_to_trade))
        
        # 更新現金
        # Long BUY → 支付現金
        # Long SELL → 收到現金
        # Short SELL (借券賣出) → 收到現金（借券保證金暫不考慮）
        # Short BUY (買回平倉) → 支付現金
        if side == "BUY":
            self.cash -= (trade_value + commission)
        else:  # SELL
            self.cash += (trade_value - commission)
        
        # 更新持倉
        # 統一用正數 shares 儲存，但 Long 為正，Short 為負（在 DailyPositionSnapshot 中）
        if is_long:
            # Long 部位
            if side == "BUY":
                # 買入：增加持倉
                if current_position:
                    total_shares = current_shares_abs + shares_to_trade
                    total_cost = (current_position.avg_cost * current_shares_abs) + trade_value
                    avg_cost = total_cost / total_shares if total_shares > 0 else 0
                else:
                    total_shares = shares_to_trade
                    avg_cost = execution_price
            else:
                # 賣出：減少持倉
                total_shares = max(0, current_shares_abs - shares_to_trade)
                avg_cost = current_position.avg_cost if current_position else execution_price
            final_shares = total_shares  # Long 為正
        else:
            # Short 部位
            if side == "SELL":
                # 借券賣出：增加空單
                if current_position:
                    total_shares_abs_new = current_shares_abs + shares_to_trade
                    # Short 的平均成本計算（以借券價格為準）
                    total_cost = (current_position.avg_cost * current_shares_abs) + trade_value
                    avg_cost = total_cost / total_shares_abs_new if total_shares_abs_new > 0 else 0
                else:
                    total_shares_abs_new = shares_to_trade
                    avg_cost = execution_price
            else:
                # 買回平倉：減少空單
                total_shares_abs_new = max(0, current_shares_abs - shares_to_trade)
                avg_cost = current_position.avg_cost if current_position else execution_price
            final_shares = -total_shares_abs_new  # Short 為負
        
        # 更新或刪除持倉
        if final_shares != 0:
            # 計算市值（用絕對值）
            final_shares_abs = abs(final_shares)
            self.positions[symbol] = DailyPositionSnapshot(
                symbol=symbol,
                shares=final_shares,  # 保留符號
                avg_cost=avg_cost,
                current_price=current_price,
                market_value=final_shares_abs * current_price,  # 市值用絕對值
                portfolio_weight=0.0,  # 稍後計算
            )
        else:
            # 持倉歸零，刪除
            if symbol in self.positions:
                del self.positions[symbol]
        
        # 建立交易記錄
        trade_record = TradeRecord(
            symbol=symbol,
            date=date,
            side=side,
            shares=shares_to_trade,
            price=execution_price,
            commission=commission,
            slippage_amount=slippage_amount,
            reference_weight=target_weight,
        )
        
        self.trades.append(trade_record)
        return trade_record
    
    def _rebalance_portfolio(self, portfolio_plan: PortfolioPlan, date: date, equity: float):
        """
        重新平衡投資組合（執行交易）
        
        Args:
            portfolio_plan: 目標部位配置表
            date: 日期
            equity: 當前資產淨值
        """
        # 將目標權重轉換為目標股數
        for position_plan in portfolio_plan.positions:
            symbol = position_plan.symbol
            target_weight = position_plan.target_weight
            is_long = position_plan.side == "LONG"
            
            # 取得當前價格
            current_price = self._get_price(symbol, date)
            if current_price is None or current_price <= 0:
                continue
            
            # 計算目標市值
            target_market_value = equity * abs(target_weight)
            
            # 計算目標股數（向下取整至 100 股）
            target_shares = int(target_market_value / current_price)
            target_shares = (target_shares // 100) * 100
            
            # 如果是 Short，股數為負
            if not is_long:
                target_shares = -target_shares
            
            # 執行交易
            self._execute_trade(
                symbol=symbol,
                date=date,
                target_shares=target_shares,
                target_weight=target_weight,
                current_price=current_price,
                is_long=is_long,
            )
        
        # 更新所有持倉的 portfolio_weight
        total_market_value = sum(pos.market_value for pos in self.positions.values())
        if total_market_value > 0:
            for symbol in self.positions:
                position = self.positions[symbol]
                position.portfolio_weight = position.market_value / (total_market_value + self.cash)
    
    def _calculate_metrics(self, equity_curve: List[Dict]) -> PerformanceMetrics:
        """
        計算核心績效指標
        
        Args:
            equity_curve: 每日淨值曲線
        
        Returns:
            PerformanceMetrics
        """
        if len(equity_curve) < 2:
            return PerformanceMetrics(
                annualized_return=0.0,
                annualized_volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                total_return=0.0,
                total_commission=sum(t.commission for t in self.trades),
                num_long_trades=len([t for t in self.trades if t.side == "BUY"]),
                num_short_trades=len([t for t in self.trades if t.side == "SELL"]),
            )
        
        # 提取淨值序列
        equity_values = [d["equity_value"] for d in equity_curve]
        dates = [d["date"] for d in equity_curve]
        
        # 計算日報酬率
        daily_returns = []
        for i in range(1, len(equity_values)):
            if equity_values[i-1] > 0:
                daily_return = (equity_values[i] - equity_values[i-1]) / equity_values[i-1]
                daily_returns.append(daily_return)
        
        if not daily_returns:
            return PerformanceMetrics(
                annualized_return=0.0,
                annualized_volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                total_return=0.0,
                total_commission=sum(t.commission for t in self.trades),
                num_long_trades=len([t for t in self.trades if t.side == "BUY"]),
                num_short_trades=len([t for t in self.trades if t.side == "SELL"]),
            )
        
        # 總報酬率
        initial_value = equity_values[0]
        final_value = equity_values[-1]
        total_return = (final_value - initial_value) / initial_value if initial_value > 0 else 0.0
        
        # 計算交易日數
        start_date = date.fromisoformat(dates[0])
        end_date = date.fromisoformat(dates[-1])
        trading_days = len(equity_curve)
        
        # 年化報酬率（假設一年 252 個交易日）
        if trading_days > 0:
            annualized_return = (1 + total_return) ** (252 / trading_days) - 1
        else:
            annualized_return = 0.0
        
        # 年化波動率
        import numpy as np
        daily_returns_array = np.array(daily_returns)
        annualized_volatility = np.std(daily_returns_array) * np.sqrt(252)
        
        # Sharpe Ratio（假設無風險利率為 0）
        sharpe_ratio = (annualized_return / annualized_volatility) if annualized_volatility > 0 else 0.0
        
        # 最大回撤
        peak = initial_value
        max_drawdown = 0.0
        for value in equity_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak > 0 else 0.0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 日級勝率
        positive_days = sum(1 for r in daily_returns if r > 0)
        win_rate = positive_days / len(daily_returns) if daily_returns else 0.0
        
        # 交易統計
        num_long_trades = len([t for t in self.trades if t.side == "BUY"])
        num_short_trades = len([t for t in self.trades if t.side == "SELL"])
        total_commission = sum(t.commission for t in self.trades)
        
        return PerformanceMetrics(
            annualized_return=annualized_return,
            annualized_volatility=annualized_volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_return=total_return,
            total_commission=total_commission,
            num_long_trades=num_long_trades,
            num_short_trades=num_short_trades,
        )
    
    def run_backtest(
        self,
        start_date: date,
        end_date: date,
    ) -> BacktestResult:
        """
        執行回測
        
        Args:
            start_date: 回測開始日期
            end_date: 回測結束日期
        
        Returns:
            BacktestResult: 回測結果
        """
        # 重置狀態
        self.positions = {}
        self.cash = self.initial_capital
        self.trades = []
        self.daily_equity_curve = []
        
        # 取得交易日列表
        trading_dates = self._get_trading_dates(start_date, end_date)
        
        if not trading_dates:
            # 沒有交易日，回傳空結果
            return BacktestResult(
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.initial_capital,
                final_capital=self.initial_capital,
                daily_equity_curve=[],
                metrics=PerformanceMetrics(
                    annualized_return=0.0,
                    annualized_volatility=0.0,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    win_rate=0.0,
                    total_return=0.0,
                    total_commission=0.0,
                    num_long_trades=0,
                    num_short_trades=0,
                ),
            )
        
        # 逐日執行回測
        for i, trade_date in enumerate(trading_dates):
            # 如果是第一天，初始化淨值
            if i == 0:
                equity_before_rebalance = self.initial_capital
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
            
            # 取得目標部位配置表
            try:
                portfolio_plan = self.decision_engine.generate_portfolio_for_date(
                    date=trade_date,
                    **self.decision_config
                )
            except Exception as e:
                # 如果無法取得 PortfolioPlan，跳過這一天（維持現有持倉）
                portfolio_plan = None
            
            # 重新平衡投資組合（如果有目標配置）
            if portfolio_plan and portfolio_plan.positions:
                self._rebalance_portfolio(portfolio_plan, trade_date, equity_before_rebalance)
            
            # 計算最終資產淨值（調整倉位後）
            # 再次更新所有持倉價格（交易後的最新價格）
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
        final_capital = equity_after_rebalance if self.daily_equity_curve else self.initial_capital
        
        # 計算績效指標
        metrics = self._calculate_metrics(self.daily_equity_curve)
        
        # 組裝回測結果
        return BacktestResult(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            daily_equity_curve=self.daily_equity_curve,
            metrics=metrics,
            trades=self.trades,
        )
    
    def generate_log_record(
        self,
        run_id: str,
        config_params: Dict,
        backtest_result: BacktestResult,
    ) -> Dict:
        """
        產生回測實驗 Log Record（扁平化的 dict，用於 JSON Lines 寫檔）
        
        Args:
            run_id: 每次回測的唯一 ID
            config_params: 這次回測用到的設定參數（例如 capital, long_budget 等）
            backtest_result: BacktestResult 物件
        
        Returns:
            Dict: 扁平化的 log record，可直接用 json.dumps() 寫入檔案
        """
        # 基礎資訊
        log_record = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "start_date": backtest_result.start_date.isoformat(),
            "end_date": backtest_result.end_date.isoformat(),
        }
        
        # Decision / 回測設定（從 config_params 填入）
        log_record.update({
            "initial_capital": config_params.get("initial_capital", self.initial_capital),
            "long_budget": config_params.get("long_budget"),
            "short_budget": config_params.get("short_budget"),
            "max_weight_per_symbol": config_params.get("max_weight_per_symbol"),
            "min_score": config_params.get("min_score"),
            "allow_short": config_params.get("allow_short"),
        })
        
        # 績效結果（從 backtest_result.metrics 取值）
        log_record.update({
            "total_return": backtest_result.metrics.total_return,
            "annualized_return": backtest_result.metrics.annualized_return,
            "annualized_volatility": backtest_result.metrics.annualized_volatility,
            "sharpe_ratio": backtest_result.metrics.sharpe_ratio,
            "max_drawdown": backtest_result.metrics.max_drawdown,
            "win_rate": backtest_result.metrics.win_rate,
            "total_commission": backtest_result.metrics.total_commission,
            "num_long_trades": backtest_result.metrics.num_long_trades,
            "num_short_trades": backtest_result.metrics.num_short_trades,
        })
        
        # 輔助欄位
        log_record["num_days"] = len(backtest_result.daily_equity_curve)
        log_record["final_capital"] = backtest_result.final_capital
        
        return log_record

