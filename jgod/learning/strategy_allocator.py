"""
Strategy Allocator: Strategy Layer (quarterly strategy allocation)

v0.6.8-A8: Analyzes regime changes and recommends strategy allocation
v0.6.9-A9: Inherits BaseLayer, computes quality_score, supports auto-apply
Only generates suggestions, never auto-applies directly.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from jgod.learning.models import StrategyAllocation, PatchStatus
from jgod.learning.base_layer import BaseLayer
from jgod.research.storage import load_daily_logs

logger = logging.getLogger(__name__)


def analyze_and_suggest_allocation(
    symbol: str,
    date_str: str,
    window: int = 60,
    snapshot_id: str = "",
) -> Optional[StrategyAllocation]:
    """
    Analyze regime changes and recommend strategy allocation.
    
    Args:
        symbol: Stock symbol
        date_str: Current date (YYYY-MM-DD)
        window: Analysis window (default 60 days, quarterly)
        
    Returns:
        StrategyAllocation suggestion or None if insufficient data
    """
    # Step 1: Load recent daily logs
    end_date = date_str
    start_date = (datetime.strptime(date_str, "%Y-%m-%d").date() - timedelta(days=window)).strftime("%Y-%m-%d")
    
    logs = load_daily_logs(symbol, start_date, end_date, limit=window)
    
    if len(logs) < window:
        logger.warning(f"Insufficient logs for {symbol} from {start_date} to {end_date}")
        return None
    
    # Step 2: Analyze strategy performance
    strategy_performance = {}
    
    for log in logs:
        decision = log.get("decision", {})
        primary_strategy = decision.get("primary_strategy")
        
        if not primary_strategy:
            continue
        
        if primary_strategy not in strategy_performance:
            strategy_performance[primary_strategy] = {
                "count": 0,
                "total_nav_change": 0.0,
                "positive_days": 0,
            }
        
        # Calculate NAV change for this day
        nav = log.get("nav", 0.0)
        prev_nav = logs[logs.index(log) - 1].get("nav", nav) if logs.index(log) > 0 else nav
        
        if prev_nav > 0:
            nav_change = (nav - prev_nav) / prev_nav
            strategy_performance[primary_strategy]["total_nav_change"] += nav_change
            if nav_change > 0:
                strategy_performance[primary_strategy]["positive_days"] += 1
        
        strategy_performance[primary_strategy]["count"] += 1
    
    if not strategy_performance:
        return None
    
    # Step 3: Calculate average return and hit rate for each strategy
    strategy_scores = {}
    for strategy, perf in strategy_performance.items():
        if perf["count"] == 0:
            continue
        
        avg_return = perf["total_nav_change"] / perf["count"]
        hit_rate = perf["positive_days"] / perf["count"] if perf["count"] > 0 else 0.0
        
        # Composite score: avg_return + 0.3 * hit_rate
        composite_score = avg_return + 0.3 * hit_rate
        strategy_scores[strategy] = {
            "avg_return": avg_return,
            "hit_rate": hit_rate,
            "composite_score": composite_score,
            "count": perf["count"],
        }
    
    if not strategy_scores:
        return None
    
    # Step 4: Find best performing strategy
    best_strategy = max(strategy_scores.items(), key=lambda x: x[1]["composite_score"])
    best_strategy_name = best_strategy[0]
    best_score = best_strategy[1]
    
    # Step 5: Get current primary strategy (most recent)
    current_strategy = logs[-1].get("decision", {}).get("primary_strategy")
    
    # Step 6: Generate suggestion if best is different from current
    if best_strategy_name != current_strategy:
        reason_parts = []
        reason_parts.append(f"基於最近 {window} 日表現分析：")
        reason_parts.append(f"- 當前策略：{current_strategy}")
        reason_parts.append(f"- 最佳策略：{best_strategy_name}（複合分數 {best_score['composite_score']:.4f}）")
        reason_parts.append(f"- 平均報酬：{best_score['avg_return']:.2%}，命中率：{best_score['hit_rate']:.2%}")
        reason_parts.append(f"建議切換至 {best_strategy_name}。")
        
        # Secondary strategies: top 2-3 by score
        sorted_strategies = sorted(
            strategy_scores.items(),
            key=lambda x: x[1]["composite_score"],
            reverse=True
        )
        secondary_strategies = [s[0] for s in sorted_strategies[1:3] if s[0] != best_strategy_name]
        
        # v0.6.9-A9: Compute quality score and status
        base_layer = BaseLayer("strategy")
        evidence_dict = {
            "strategy_scores": {
                k: {
                    "avg_return": round(v["avg_return"], 4),
                    "hit_rate": round(v["hit_rate"], 4),
                    "composite_score": round(v["composite_score"], 4),
                }
                for k, v in strategy_scores.items()
            },
            "window": window,
            "current_strategy": current_strategy,
        }
        quality_score = base_layer.compute_quality_score({
            "evidence": evidence_dict
        })
        status = base_layer.finalize_status(quality_score)
        
        return StrategyAllocation(
            date=date_str,
            symbol=symbol,
            recommended_primary_strategy=best_strategy_name,
            recommended_secondary_strategies=secondary_strategies,
            reason="\n".join(reason_parts),
            evidence=evidence_dict,
            quality_score=quality_score,
            status=status,
            snapshot_id=snapshot_id,
        )
    
    # No change needed
    return None


def save_strategy_allocation(allocation: StrategyAllocation) -> None:
    """
    Save strategy allocation suggestion to storage.
    
    Args:
        allocation: StrategyAllocation to save
    """
    from pathlib import Path
    import json
    
    project_root = Path(__file__).resolve().parents[2]
    learning_dir = project_root / "data" / "learning"
    learning_dir.mkdir(parents=True, exist_ok=True)
    storage_path = learning_dir / "strategy_log.jsonl"
    
    try:
        with open(storage_path, "a", encoding="utf-8") as f:
            json.dump({
                "date": allocation.date,
                "symbol": allocation.symbol,
                "recommended_primary_strategy": allocation.recommended_primary_strategy,
                "recommended_secondary_strategies": allocation.recommended_secondary_strategies,
                "reason": allocation.reason,
                "evidence": allocation.evidence,
                "status": allocation.status,
            }, f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        logger.error(f"Failed to save strategy allocation for {allocation.symbol}: {e}", exc_info=True)
        raise

