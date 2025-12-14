"""
Decision V3 Evaluation

Evaluates Decision V3 decisions by replaying prediction timeline and computing metrics.
Pure Python implementation (no external dependencies).

v0.6.5-A6: Added VirtualLedger-based P&L evaluation for execution grounding.
v0.6.6-A7: Added BacktestCore-based evaluation (OHLCV + Fill Engine) for realism.
"""

import math
import logging
from typing import List, Dict, Literal, Optional
from datetime import date

from jgod.observer.prediction_stability import TimelineItem

logger = logging.getLogger(__name__)

# v0.6.6-A7: Import BacktestEngine for realism
try:
    from jgod.research.backtest_engine import BacktestEngine, BacktestConfig as BTConfig
    BACKTEST_AVAILABLE = True
except ImportError:
    BACKTEST_AVAILABLE = False
    BTConfig = None
    logger.warning("BacktestEngine not available, falling back to proxy evaluation")


class EvaluationVerdict:
    """Evaluation verdict types"""
    IMPROVED = "IMPROVED"
    NEUTRAL = "NEUTRAL"
    REGRESSED = "REGRESSED"
    NO_DATA = "NO_DATA"


def _calculate_equity_curve(returns: List[float], initial: float = 1.0) -> List[float]:
    """Calculate equity curve from returns"""
    equity = [initial]
    for ret in returns:
        equity.append(equity[-1] * (1.0 + ret))
    return equity


def _calculate_max_drawdown(equity_curve: List[float]) -> float:
    """Calculate maximum drawdown from equity curve"""
    if not equity_curve:
        return 0.0
    
    peak = equity_curve[0]
    max_dd = 0.0
    
    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    
    return max_dd


def _calculate_decision_consistency(
    timeline_items: List[TimelineItem],
    primary_strategy: Optional[str],
    window: int = 5,
) -> float:
    """
    Calculate decision consistency proxy.
    
    Uses signal stability from timeline as a proxy for decision consistency.
    """
    if not timeline_items or len(timeline_items) < window:
        return 0.0
    
    # Use last N items
    recent_items = timeline_items[:window]
    
    # Extract signals (if available) or use score direction
    signals = []
    for item in recent_items:
        # Use signal if available, otherwise infer from score direction
        signal = item.get("signal", "UNKNOWN")
        if signal == "UNKNOWN":
            # Infer from score: positive = LONG, negative = SHORT
            score = item.get("final_score", 0.0)
            signal = "LONG" if score > 0 else "SHORT"
        signals.append(signal)
    
    # Count consistent signals (same as most common)
    if not signals:
        return 0.0
    
    # Count occurrences
    signal_counts = {}
    for s in signals:
        signal_counts[s] = signal_counts.get(s, 0) + 1
    
    # Most common signal count
    max_count = max(signal_counts.values())
    consistency = max_count / len(signals)
    
    return consistency


def evaluate_decision_v3_grounded(
    timeline_items: List[TimelineItem],
    decision_result: Dict,
    window: int = 20,
    initial_cash: float = 1_000_000.0,
    use_ledger: bool = True,
) -> Dict:
    """
    Evaluate Decision V3 using VirtualLedger P&L (execution grounding).
    
    For each step in timeline window:
    - mark_to_market with current price (derived from score if no price exists)
    - use fixed decision per window (deterministic)
    - generate order request and apply buy/sell to ledger
    
    Metrics computed from ledger history:
    - realized_pnl, unrealized_pnl, nav_series
    - avg_return_proxy becomes avg_daily_nav_return
    - max_drawdown_proxy from nav curve
    - turnover_proxy from notional traded / nav
    - hit_rate_proxy from positive daily nav returns ratio
    """
    from jgod.execution.virtual_ledger import VirtualLedger
    from jgod.execution.order_engine import OrderGenerationEngine
    from jgod.decision_v3.models import DecisionV3Result, RiskPlan, StrategyWeight
    
    n_points = len(timeline_items)
    
    # NO_DATA check
    if n_points < 5:  # Stricter for ledger-based
        return {
            "n_points": n_points,
            "hit_rate_proxy": 0.0,
            "avg_return_proxy": 0.0,
            "max_drawdown_proxy": 0.0,
            "turnover_proxy": 0.0,
            "decision_consistency": 0.0,
            "verdict": EvaluationVerdict.NO_DATA,
            "recommendation_next_step": "資料點不足（<5），無法進行執行層評估。請等待更多預測資料。",
        }
    
    if not use_ledger:
        # Fallback to proxy-based evaluation
        return evaluate_decision_v3(timeline_items, decision_result, window)
    
    # Reverse to chronological order (oldest first)
    items_chrono = list(reversed(timeline_items))
    
    # Create ledger
    symbol = decision_result.get("symbol", "UNKNOWN")
    ledger = VirtualLedger(symbol=symbol, cash=initial_cash)
    
    # Convert decision_result to DecisionV3Result for order generation
    decision_v3_result = DecisionV3Result(
        symbol=symbol,
        as_of_date=None,
        selected_primary_strategy=decision_result.get("selected_primary_strategy", "risk_off"),
        selected_secondary_strategies=decision_result.get("selected_secondary_strategies", []),
        weights=[
            StrategyWeight(strategy_id=w.get("strategy_id", ""), weight=w.get("weight", 0.0))
            for w in decision_result.get("weights", [])
        ],
        risk_plan=RiskPlan(
            position_scale=decision_result.get("risk_plan", {}).get("position_scale", 0.0),
            risk_state=decision_result.get("risk_plan", {}).get("risk_state", "NO_DATA"),
            reasons=decision_result.get("risk_plan", {}).get("reasons", []),
        ),
        confidence=decision_result.get("confidence", 0.0),
        explain=decision_result.get("explain", ""),
    )
    
    # Price proxy: base_price * (1 + cumulative_return)
    base_price = 100.0
    prices = []
    nav_series = []
    notional_traded = 0.0
    
    # Process each step
    order_engine = OrderGenerationEngine()
    
    for i, item in enumerate(items_chrono):
        # Derive price from score
        final_score = item.get("final_score", 0.0)
        daily_return_proxy = max(-0.05, min(0.05, final_score * 0.002))
        
        if i == 0:
            price = base_price
        else:
            price = prices[-1] * (1 + daily_return_proxy)
        
        prices.append(price)
        
        # Mark to market
        ledger.mark_to_market(symbol, price)
        
        # Generate order (use fixed decision for entire window)
        order_request = order_engine.generate_orders(decision_v3_result, ledger, price)
        
        # Execute order
        if order_request.side == "BUY" and order_request.qty > 0:
            result = ledger.buy(symbol, order_request.qty, price)
            if result["success"]:
                notional_traded += order_request.qty * price
        elif order_request.side == "SELL" and order_request.qty > 0:
            result = ledger.sell(symbol, order_request.qty, price)
            if result["success"]:
                notional_traded += order_request.qty * price
        
        # Record NAV
        nav_series.append(ledger.nav)
    
    # Calculate metrics from ledger
    if len(nav_series) < 2:
        return {
            "n_points": n_points,
            "hit_rate_proxy": 0.0,
            "avg_return_proxy": 0.0,
            "max_drawdown_proxy": 0.0,
            "turnover_proxy": 0.0,
            "decision_consistency": 0.0,
            "verdict": EvaluationVerdict.NO_DATA,
            "recommendation_next_step": "無法計算 NAV 序列。請確認預測資料完整性。",
        }
    
    # NAV returns
    nav_returns = []
    for i in range(1, len(nav_series)):
        if nav_series[i-1] > 0:
            ret = (nav_series[i] - nav_series[i-1]) / nav_series[i-1]
            nav_returns.append(ret)
    
    if not nav_returns:
        return {
            "n_points": n_points,
            "hit_rate_proxy": 0.0,
            "avg_return_proxy": 0.0,
            "max_drawdown_proxy": 0.0,
            "turnover_proxy": 0.0,
            "decision_consistency": 0.0,
            "verdict": EvaluationVerdict.NO_DATA,
            "recommendation_next_step": "無法計算 NAV 報酬率。請確認預測資料完整性。",
        }
    
    # Metrics
    n_returns = len(nav_returns)
    avg_return_proxy = sum(nav_returns) / n_returns  # avg_daily_nav_return
    
    # Hit rate: positive daily nav returns ratio
    hits = sum(1 for r in nav_returns if r > 0)
    hit_rate_proxy = hits / n_returns if n_returns > 0 else 0.0
    
    # Max drawdown from NAV curve
    max_drawdown_proxy = _calculate_max_drawdown(nav_series)
    
    # Turnover: notional traded / average nav
    avg_nav = sum(nav_series) / len(nav_series) if nav_series else initial_cash
    turnover_proxy = notional_traded / avg_nav if avg_nav > 0 else 0.0
    
    # Decision consistency (unchanged)
    primary_strategy = decision_result.get("selected_primary_strategy")
    decision_consistency = _calculate_decision_consistency(
        timeline_items,
        primary_strategy,
        window=min(5, n_points),
    )
    
    # Determine verdict (unchanged logic)
    if avg_return_proxy > 0 and hit_rate_proxy >= 0.55 and max_drawdown_proxy <= 0.18:
        verdict = EvaluationVerdict.IMPROVED
    elif avg_return_proxy < 0 and max_drawdown_proxy > 0.25:
        verdict = EvaluationVerdict.REGRESSED
    else:
        verdict = EvaluationVerdict.NEUTRAL
    
    # Generate recommendation
    recommendation_parts = []
    
    if verdict == EvaluationVerdict.IMPROVED:
        recommendation_parts.append("執行層表現良好（基於虛擬帳本），建議維持當前策略配置。")
        if decision_consistency < 0.6:
            recommendation_parts.append("注意：決策一致性偏低，建議檢視策略選擇邏輯。")
    elif verdict == EvaluationVerdict.REGRESSED:
        recommendation_parts.append("執行層表現下滑（基於虛擬帳本），建議：")
        recommendation_parts.append("1. 檢視風險控制參數（max_drawdown 偏高）")
        recommendation_parts.append("2. 考慮切換至備選策略或降低倉位")
        if hit_rate_proxy < 0.45:
            recommendation_parts.append("3. 命中率偏低，建議重新評估策略適用性")
    else:  # NEUTRAL
        recommendation_parts.append("執行層表現中性（基於虛擬帳本），建議：")
        recommendation_parts.append("1. 持續監控關鍵指標（hit_rate, max_drawdown）")
        recommendation_parts.append("2. 若趨勢持續，考慮調整策略權重")
    
    recommendation_next_step = "\n".join(recommendation_parts[:6])  # Max 6 lines
    
    return {
        "n_points": n_points,
        "hit_rate_proxy": round(hit_rate_proxy, 4),
        "avg_return_proxy": round(avg_return_proxy, 4),
        "max_drawdown_proxy": round(max_drawdown_proxy, 4),
        "turnover_proxy": round(turnover_proxy, 4),
        "decision_consistency": round(decision_consistency, 4),
        "verdict": verdict,
        "recommendation_next_step": recommendation_next_step,
        "ledger_metrics": {
            "realized_pnl": round(ledger.realized_pnl, 2),
            "unrealized_pnl": round(ledger.unrealized_pnl, 2),
            "final_nav": round(ledger.nav, 2),
            "notional_traded": round(notional_traded, 2),
        },
    }


def evaluate_decision_v3(
    timeline_items: List[TimelineItem],
    decision_result: Dict,
    window: int = 20,
    use_ledger: bool = True,
) -> Dict:
    """
    Evaluate Decision V3 decision by replaying timeline.
    
    v0.6.5-A6: Now supports ledger-based evaluation (use_ledger=True).
    Falls back to proxy-based evaluation if use_ledger=False or insufficient data.
    
    Args:
        timeline_items: List of timeline items (chronological order, newest first)
        decision_result: Decision V3 result dict (from service)
        window: Evaluation window size
        use_ledger: Whether to use VirtualLedger P&L (default True)
    
    Returns:
        Evaluation metrics dict with:
        - n_points: int
        - hit_rate_proxy: float
        - avg_return_proxy: float (NAV return if ledger-based)
        - max_drawdown_proxy: float
        - turnover_proxy: float
        - decision_consistency: float
        - verdict: IMPROVED | NEUTRAL | REGRESSED | NO_DATA
        - recommendation_next_step: str (Traditional Chinese)
        - ledger_metrics: dict (if ledger-based, contains realized_pnl, unrealized_pnl, etc.)
    """
    # Try ledger-based evaluation first if enabled
    if use_ledger:
        try:
            return evaluate_decision_v3_grounded(timeline_items, decision_result, window, use_ledger=True)
        except Exception as e:
            logger.warning(f"Ledger-based evaluation failed, falling back to proxy: {e}")
            # Fall through to proxy-based
    
    # Proxy-based evaluation (original implementation)
    n_points = len(timeline_items)
    
    # NO_DATA check
    if n_points < 10:
        return {
            "n_points": n_points,
            "hit_rate_proxy": 0.0,
            "avg_return_proxy": 0.0,
            "max_drawdown_proxy": 0.0,
            "turnover_proxy": 0.0,
            "decision_consistency": 0.0,
            "verdict": EvaluationVerdict.NO_DATA,
            "recommendation_next_step": "資料點不足（<10），無法進行評估。請等待更多預測資料。",
        }
    
    # Reverse to chronological order (oldest first)
    items_chrono = list(reversed(timeline_items))
    
    # Extract scores
    scores = [item.get("final_score", 0.0) for item in items_chrono]
    
    # Get primary strategy from decision
    primary_strategy = decision_result.get("selected_primary_strategy")
    
    # Calculate return proxy: delta(final_score)
    returns = []
    for i in range(1, len(scores)):
        delta = scores[i] - scores[i - 1]
        returns.append(delta)
    
    if not returns:
        return {
            "n_points": n_points,
            "hit_rate_proxy": 0.0,
            "avg_return_proxy": 0.0,
            "max_drawdown_proxy": 0.0,
            "turnover_proxy": 0.0,
            "decision_consistency": 0.0,
            "verdict": EvaluationVerdict.NO_DATA,
            "recommendation_next_step": "無法計算報酬率代理指標。請確認預測資料完整性。",
        }
    
    # Calculate metrics
    n_returns = len(returns)
    avg_return_proxy = sum(returns) / n_returns
    
    # Hit rate proxy: depends on primary strategy
    # For trend_follow/breakout/momentum: positive delta is good
    # For mean_reversion: negative delta is good
    if primary_strategy in ["trend_follow", "breakout", "momentum"]:
        # Positive delta = hit
        hits = sum(1 for r in returns if r > 0)
    elif primary_strategy == "mean_reversion":
        # Negative delta = hit (contrarian)
        hits = sum(1 for r in returns if r < 0)
    else:
        # Default: positive delta
        hits = sum(1 for r in returns if r > 0)
    
    hit_rate_proxy = hits / n_returns if n_returns > 0 else 0.0
    
    # Max drawdown proxy: from equity curve
    equity_curve = _calculate_equity_curve(returns)
    max_drawdown_proxy = _calculate_max_drawdown(equity_curve)
    
    # Turnover proxy: abs(delta(final_score)) average
    turnover_proxy = sum(abs(r) for r in returns) / n_returns if n_returns > 0 else 0.0
    
    # Decision consistency
    decision_consistency = _calculate_decision_consistency(
        timeline_items,
        primary_strategy,
        window=min(5, n_points),
    )
    
    # Determine verdict
    if avg_return_proxy > 0 and hit_rate_proxy >= 0.55 and max_drawdown_proxy <= 0.18:
        verdict = EvaluationVerdict.IMPROVED
    elif avg_return_proxy < 0 and max_drawdown_proxy > 0.25:
        verdict = EvaluationVerdict.REGRESSED
    else:
        verdict = EvaluationVerdict.NEUTRAL
    
    # Generate recommendation
    recommendation_parts = []
    
    if verdict == EvaluationVerdict.IMPROVED:
        recommendation_parts.append("決策表現良好，建議維持當前策略配置。")
        if decision_consistency < 0.6:
            recommendation_parts.append("注意：決策一致性偏低，建議檢視策略選擇邏輯。")
    elif verdict == EvaluationVerdict.REGRESSED:
        recommendation_parts.append("決策表現下滑，建議：")
        recommendation_parts.append("1. 檢視風險控制參數（max_drawdown 偏高）")
        recommendation_parts.append("2. 考慮切換至備選策略或降低倉位")
        if hit_rate_proxy < 0.45:
            recommendation_parts.append("3. 命中率偏低，建議重新評估策略適用性")
    else:  # NEUTRAL
        recommendation_parts.append("決策表現中性，建議：")
        recommendation_parts.append("1. 持續監控關鍵指標（hit_rate, max_drawdown）")
        recommendation_parts.append("2. 若趨勢持續，考慮調整策略權重")
    
    recommendation_next_step = "\n".join(recommendation_parts[:6])  # Max 6 lines
    
    return {
        "n_points": n_points,
        "hit_rate_proxy": round(hit_rate_proxy, 4),
        "avg_return_proxy": round(avg_return_proxy, 4),
        "max_drawdown_proxy": round(max_drawdown_proxy, 4),
        "turnover_proxy": round(turnover_proxy, 4),
        "decision_consistency": round(decision_consistency, 4),
        "verdict": verdict,
        "recommendation_next_step": recommendation_next_step,
    }


def evaluate_decision_v3_with_backtest(
    symbol: str,
    decision_result: Dict,
    start_date: str,
    end_date: str,
    window: int = 20,
    config: Optional[BTConfig] = None,
) -> Dict:
    """
    Evaluate Decision V3 using BacktestCore (OHLCV + Fill Engine).
    
    v0.6.6-A7: New method using BacktestEngine for realistic P&L.
    
    Args:
        symbol: Stock symbol
        decision_result: Decision V3 result dict
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        window: Evaluation window size (not used in backtest, kept for compatibility)
        config: Backtest configuration
        
    Returns:
        Evaluation metrics dict (same format as evaluate_decision_v3)
    """
    if not BACKTEST_AVAILABLE:
        logger.warning("BacktestEngine not available, falling back to proxy evaluation")
        return {
            "n_points": 0,
            "hit_rate_proxy": 0.0,
            "avg_return_proxy": 0.0,
            "max_drawdown_proxy": 0.0,
            "turnover_proxy": 0.0,
            "decision_consistency": 0.0,
            "verdict": EvaluationVerdict.NO_DATA,
            "recommendation_next_step": "BacktestEngine 不可用，無法進行真實性評估",
        }
    
    try:
        from jgod.research.backtest_engine import BacktestEngine, BacktestConfig as BTConfig
        
        # Create backtest engine
        engine = BacktestEngine(use_mock_mdts=False)  # Use real DB if available
        
        if config is None:
            config = BTConfig(
                initial_cash=1_000_000.0,
                mode=decision_result.get("mode", "performance"),
                limit=decision_result.get("limit", 60),
                k=decision_result.get("k", 5),
            )
        
        # Run backtest
        report = engine.run(symbol, start_date, end_date, config)
        
        # Extract metrics
        n_points = len(report.daily_log)
        
        if n_points < 10:
            return {
                "n_points": n_points,
                "hit_rate_proxy": 0.0,
                "avg_return_proxy": 0.0,
                "max_drawdown_proxy": 0.0,
                "turnover_proxy": 0.0,
                "decision_consistency": 0.0,
                "verdict": EvaluationVerdict.NO_DATA,
                "recommendation_next_step": "資料點不足（< 10），無法進行評估",
            }
        
        # Use backtest metrics
        avg_return_proxy = report.metrics.avg_daily_return
        max_drawdown_proxy = report.metrics.max_drawdown
        turnover_proxy = report.metrics.turnover
        hit_rate_proxy = report.metrics.hit_rate
        
        # Decision consistency (simplified: based on primary strategy consistency)
        # TODO: In A8, this will be computed from daily_log decision history
        decision_consistency = 0.5  # Placeholder
        
        # Verdict logic (same as original)
        if avg_return_proxy > 0 and hit_rate_proxy >= 0.55 and max_drawdown_proxy <= 0.18:
            verdict = EvaluationVerdict.IMPROVED
            recommendation_next_step = "表現優異，建議維持當前配置並持續監控。"
        elif avg_return_proxy < 0 and max_drawdown_proxy > 0.25:
            verdict = EvaluationVerdict.REGRESSED
            recommendation_next_step = "表現不佳，建議檢視決策邏輯與風險參數。"
        else:
            verdict = EvaluationVerdict.NEUTRAL
            recommendation_next_step = "表現中性，建議持續觀察並適時調整。"
        
        return {
            "n_points": n_points,
            "hit_rate_proxy": round(hit_rate_proxy, 4),
            "avg_return_proxy": round(avg_return_proxy, 4),
            "max_drawdown_proxy": round(max_drawdown_proxy, 4),
            "turnover_proxy": round(turnover_proxy, 4),
            "decision_consistency": round(decision_consistency, 4),
            "verdict": verdict,
            "recommendation_next_step": recommendation_next_step,
            "backtest_report": {
                "final_nav": report.final_nav,
                "total_return": report.metrics.total_return,
                "sharpe_ratio": report.metrics.sharpe_ratio,
            },
        }
    except Exception as e:
        logger.error(f"Backtest evaluation failed: {e}", exc_info=True)
        return {
            "n_points": 0,
            "hit_rate_proxy": 0.0,
            "avg_return_proxy": 0.0,
            "max_drawdown_proxy": 0.0,
            "turnover_proxy": 0.0,
            "decision_consistency": 0.0,
            "verdict": EvaluationVerdict.NO_DATA,
            "recommendation_next_step": f"回測評估失敗：{str(e)}",
        }

