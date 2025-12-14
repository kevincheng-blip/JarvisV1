"""
Execution Service: High-level operations for ledger and order simulation
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from jgod.execution.virtual_ledger import VirtualLedger, PositionState
from jgod.execution.order_engine import OrderGenerationEngine
from jgod.execution.storage import save_ledger_snapshot, load_latest
from jgod.decision_v3.service import compute_decision, get_latest_snapshot

logger = logging.getLogger(__name__)


def _fetch_latest_price(symbol: str, limit: int = 60) -> Optional[float]:
    """
    Fetch latest price from PredictionSnapshot timeline.
    
    Uses last timeline item's price proxy if available.
    Falls back to base_price * (1 + final_score * 0.002) if no price exists.
    
    Returns:
        Price float or None if no data
    """
    from jgod.decision_v3.service import _fetch_timeline_items
    
    timeline_items = _fetch_timeline_items(symbol, limit)
    if not timeline_items:
        return None
    
    # Use last item
    last_item = timeline_items[0]  # Already sorted newest first
    
    # Try to get price from item (if PredictionSnapshot has price field)
    # For now, use score-based proxy
    base_price = 100.0
    final_score = last_item.get("final_score", 0.0)
    daily_return_proxy = max(-0.05, min(0.05, final_score * 0.002))
    
    # Simple price proxy: assume starting from base_price and accumulate returns
    # For simplicity, use base_price * (1 + recent_return)
    price = base_price * (1 + daily_return_proxy * 10)  # Scale for visibility
    
    return price


def get_latest_ledger(symbol: str, initial_cash: float = 1_000_000.0) -> Dict:
    """
    Get latest ledger snapshot, or return default empty ledger.
    
    Args:
        symbol: Stock symbol
        initial_cash: Initial cash for default ledger
        
    Returns:
        Ledger snapshot dict with 'is_default' flag if no snapshots exist
    """
    snapshot = load_latest(symbol)
    
    if snapshot:
        return snapshot
    
    # Return default empty ledger
    ledger = VirtualLedger(symbol=symbol, cash=initial_cash)
    ledger.mark_to_market(symbol, 100.0)  # Default price
    
    return {
        "snapshot_id": "",
        "created_at": datetime.now().isoformat(),
        "symbol": symbol,
        "ledger": ledger.snapshot(symbol),
        "is_default": True,
    }


def recompute_ledger(symbol: str, initial_cash: float = 1_000_000.0) -> Dict:
    """
    Create a brand-new ledger snapshot (reset) and save.
    
    Args:
        symbol: Stock symbol
        initial_cash: Initial cash amount
        
    Returns:
        Saved snapshot dict with snapshot_id
    """
    logger.info(f"Recomputing ledger for {symbol} with initial_cash={initial_cash}")
    
    # Create fresh ledger
    ledger = VirtualLedger(symbol=symbol, cash=initial_cash)
    
    # Mark to market with default price
    price = _fetch_latest_price(symbol) or 100.0
    ledger.mark_to_market(symbol, price)
    
    # Create snapshot
    snapshot = {
        "symbol": symbol,
        "created_at": datetime.now().isoformat(),
        "ledger": ledger.snapshot(symbol),
        "is_default": False,
    }
    
    # Save
    snapshot_id = save_ledger_snapshot(snapshot)
    snapshot["snapshot_id"] = snapshot_id
    
    logger.info(f"Saved fresh ledger snapshot {snapshot_id} for {symbol}")
    return snapshot


def simulate_order_from_latest_decision(
    symbol: str,
    mode: str = "performance",
    limit: int = 60,
    k: int = 5
) -> Dict:
    """
    Simulate order from latest Decision V3 snapshot.
    
    Flow:
    1. Fetch Decision V3 latest snapshot (or compute if none)
    2. Fetch latest ledger snapshot (or default)
    3. Fetch latest price
    4. Generate order request
    
    Args:
        symbol: Stock symbol
        mode: Decision mode
        limit: Timeline limit
        k: Number of top strategies
        
    Returns:
        Dict with 'ledger', 'decision_v3', 'order_request', 'price', 'has_data'
    """
    # 1. Get Decision V3
    decision_snapshot = get_latest_snapshot(symbol)
    if not decision_snapshot:
        # Compute fresh decision
        decision_result = compute_decision(symbol, mode, limit, k)
        decision_dict = {
            "symbol": decision_result.symbol,
            "selected_primary_strategy": decision_result.selected_primary_strategy,
            "selected_secondary_strategies": decision_result.selected_secondary_strategies,
            "risk_plan": {
                "position_scale": decision_result.risk_plan.position_scale,
                "risk_state": decision_result.risk_plan.risk_state,
                "reasons": decision_result.risk_plan.reasons,
            },
            "confidence": decision_result.confidence,
            "weights": [
                {"strategy_id": w.strategy_id, "weight": w.weight}
                for w in decision_result.weights
            ],
        }
    else:
        decision_dict = decision_snapshot.get("result", {})
    
    # Convert to DecisionV3Result for order generation
    from jgod.decision_v3.models import DecisionV3Result, RiskPlan, StrategyWeight
    
    decision_result = DecisionV3Result(
        symbol=symbol,
        as_of_date=None,
        selected_primary_strategy=decision_dict.get("selected_primary_strategy", "risk_off"),
        selected_secondary_strategies=decision_dict.get("selected_secondary_strategies", []),
        weights=[
            StrategyWeight(strategy_id=w["strategy_id"], weight=w["weight"])
            for w in decision_dict.get("weights", [])
        ],
        risk_plan=RiskPlan(
            position_scale=decision_dict.get("risk_plan", {}).get("position_scale", 0.0),
            risk_state=decision_dict.get("risk_plan", {}).get("risk_state", "NO_DATA"),
            reasons=decision_dict.get("risk_plan", {}).get("reasons", []),
        ),
        confidence=decision_dict.get("confidence", 0.0),
        explain=decision_dict.get("explain", ""),
    )
    
    # 2. Get ledger
    ledger_snapshot = get_latest_ledger(symbol)
    ledger_dict = ledger_snapshot.get("ledger", {})
    
    # Reconstruct VirtualLedger
    ledger = VirtualLedger(
        symbol=symbol,
        cash=ledger_dict.get("cash", 1_000_000.0),
    )
    ledger.realized_pnl = ledger_dict.get("realized_pnl", 0.0)
    ledger.unrealized_pnl = ledger_dict.get("unrealized_pnl", 0.0)
    
    pos_dict = ledger_dict.get("position", {})
    if pos_dict.get("qty", 0) > 0:
        pos = PositionState(
            symbol=symbol,
            qty=pos_dict.get("qty", 0),
            avg_cost=pos_dict.get("avg_cost", 0.0),
        )
        ledger.positions[symbol] = pos
    
    price = ledger_dict.get("last_price", 0.0) or _fetch_latest_price(symbol) or 100.0
    ledger.mark_to_market(symbol, price)
    
    # 3. Generate order
    order_engine = OrderGenerationEngine()
    order_request = order_engine.generate_orders(decision_result, ledger, price)
    
    # 4. Return result
    return {
        "symbol": symbol,
        "ledger": ledger.snapshot(symbol),
        "decision_v3": decision_dict,
        "order_request": {
            "symbol": order_request.symbol,
            "side": order_request.side,
            "qty": order_request.qty,
            "reason": order_request.reason,
            "target_position_scale": order_request.target_position_scale,
            "current_position_scale": order_request.current_position_scale,
        },
        "price": price,
        "has_data": price > 0 and decision_dict.get("risk_plan", {}).get("position_scale", 0) > 0,
    }

