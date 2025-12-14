"""
Tuning Advisor: Thought Layer (5-day parameter tuning)

v0.6.8-A8: Produces DoctrinePatch suggestions based on Arena results
v0.6.9-A9: Inherits BaseLayer, computes quality_score, supports auto-apply
Only generates suggestions, never auto-applies directly.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from jgod.learning.models import TuningPatch, PatchStatus
from jgod.learning.base_layer import BaseLayer
from jgod.research.storage import load_daily_logs
from jgod.config.doctrine import load_doctrine, DoctrineConfig

logger = logging.getLogger(__name__)


def analyze_and_suggest_patch(
    symbol: str,
    date_str: str,
    window: int = 5,
) -> Optional[TuningPatch]:
    """
    Analyze recent P&L and Arena results, produce tuning patch suggestion.
    
    Args:
        symbol: Stock symbol
        date_str: Current date (YYYY-MM-DD)
        window: Analysis window (default 5 days)
        
    Returns:
        TuningPatch suggestion or None if insufficient data
    """
    # Step 1: Load recent daily logs (last N days)
    end_date = date_str
    start_date = (datetime.strptime(date_str, "%Y-%m-%d").date() - timedelta(days=window)).strftime("%Y-%m-%d")
    
    logs = load_daily_logs(symbol, start_date, end_date, limit=window)
    
    if len(logs) < window:
        logger.warning(f"Insufficient logs for {symbol} from {start_date} to {end_date}")
        return None
    
    # Step 2: Calculate P&L metrics from logs
    nav_history = [log.get("nav", 0.0) for log in logs]
    if not nav_history or nav_history[0] == 0:
        return None
    
    initial_nav = nav_history[0]
    final_nav = nav_history[-1]
    total_return = (final_nav - initial_nav) / initial_nav if initial_nav > 0 else 0.0
    
    # Calculate max drawdown
    peak = initial_nav
    max_dd = 0.0
    for nav in nav_history:
        if nav > peak:
            peak = nav
        dd = (peak - nav) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    
    # Step 3: Run Arena to get challenger comparison
    try:
        from jgod.decision_v3.arena import compute_arena, ArenaResult, AutoTuningResult, VariantConfig
        
        arena_result = compute_arena(
            symbol=symbol,
            mode="performance",
            limit=60,
            k=5,
            window=window,
        )
    except Exception as e:
        logger.error(f"Failed to run arena for {symbol}: {e}", exc_info=True)
        return None
    
    if not arena_result or arena_result.winner_id == "NO_DATA":
        return None
    
    # Step 4: Analyze Arena results
    current_doctrine = load_doctrine("v1.0")
    if current_doctrine is None:
        current_doctrine = DoctrineConfig(version="v1.0")
    
    # Check if winner is not V3 and has significant advantage
    if arena_result.winner_id != "V3" and arena_result.is_regression:
        # Generate patch suggestion to adopt winner's configuration
        winner_score = next(
            (s.composite_score for s in arena_result.scoreboard if s.challenger_id == arena_result.winner_id),
            0.0
        )
        v3_score = next(
            (s.composite_score for s in arena_result.scoreboard if s.challenger_id == "V3"),
            0.0
        )
        
        score_delta = winner_score - v3_score
        
        # Generate patch based on auto_tuning results if available
        if arena_result.auto_tuning and arena_result.auto_tuning.best_config:
            best_config = arena_result.auto_tuning.best_config
            
            # Create risk_mapping changes
            risk_mapping_changes = {}
            for grade, scale in best_config.risk_mapping.items():
                current_scale = current_doctrine.risk_mapping.get(grade, 0.0)
                if abs(scale - current_scale) > 0.05:  # Significant change
                    risk_mapping_changes[grade] = scale
            
            if risk_mapping_changes:
                patch_id = f"TUNE-{date_str.replace('-', '')}-001"
                
                # v0.6.9-A9: Compute quality score and status
                base_layer = BaseLayer("thought")
                evidence_dict = {
                    "pnl_delta": round(total_return, 4),
                    "mdd_change": round(max_dd, 4),
                    "winner_id": arena_result.winner_id,
                    "score_delta": round(score_delta, 4),
                    "arena_summary": arena_result.summary,
                }
                quality_score = base_layer.compute_quality_score({
                    "evidence": evidence_dict
                })
                status = base_layer.finalize_status(quality_score)
                
                return TuningPatch(
                    patch_id=patch_id,
                    date=date_str,
                    symbol=symbol,
                    target="risk_mapping",
                    changes=risk_mapping_changes,
                    reason=f"Arena 顯示 {arena_result.winner_id} 優於 V3（分數差距 {score_delta:.4f}），建議調整風險映射",
                    evidence=evidence_dict,
                    quality_score=quality_score,
                    status=status,
                    snapshot_id=snapshot_id,
                )
    
    # Step 5: Check auto_tuning suggestions
    if arena_result.auto_tuning and arena_result.auto_tuning.best_config:
        best_config = arena_result.auto_tuning.best_config
        top_variants = arena_result.auto_tuning.top_variants
        
        if top_variants:
            best_score = top_variants[0][1] if isinstance(top_variants[0], tuple) else 0.0
            v3_score = next(
                (s.composite_score for s in arena_result.scoreboard if s.challenger_id == "V3"),
                0.0
            )
            
            if best_score > v3_score + 0.02:  # Significant improvement
                # Generate composite_weights patch
                composite_changes = {}
                for key, value in best_config.composite_weights.items():
                    current_value = current_doctrine.composite_weights.get(key, 0.0)
                    if abs(value - current_value) > 0.01:  # Significant change
                        composite_changes[key] = value
                
                if composite_changes:
                    patch_id = f"TUNE-{date_str.replace('-', '')}-002"
                    
                    # v0.6.9-A9: Compute quality score and status
                    base_layer = BaseLayer("thought")
                    evidence_dict = {
                        "pnl_delta": round(total_return, 4),
                        "mdd_change": round(max_dd, 4),
                        "best_score": round(best_score, 4),
                        "v3_score": round(v3_score, 4),
                        "score_delta": round(best_score - v3_score, 4),
                        "auto_tuning_notes": arena_result.auto_tuning.notes,
                    }
                    quality_score = base_layer.compute_quality_score({
                        "evidence": evidence_dict
                    })
                    status = base_layer.finalize_status(quality_score)
                    
                    return TuningPatch(
                        patch_id=patch_id,
                        date=date_str,
                        symbol=symbol,
                        target="composite_weights",
                        changes=composite_changes,
                        reason=f"自動調參發現更優配置（分數提升 {best_score - v3_score:.4f}），建議更新複合權重",
                        evidence=evidence_dict,
                        quality_score=quality_score,
                        status=status,
                        snapshot_id=snapshot_id,
                    )
    
    # No significant improvement found
    return None


def save_tuning_patch(patch: TuningPatch) -> None:
    """
    Save tuning patch suggestion to storage.
    
    Args:
        patch: TuningPatch to save
    """
    from pathlib import Path
    import json
    
    project_root = Path(__file__).resolve().parents[2]
    learning_dir = project_root / "data" / "learning"
    learning_dir.mkdir(parents=True, exist_ok=True)
    storage_path = learning_dir / "thought_log.jsonl"
    
    try:
        with open(storage_path, "a", encoding="utf-8") as f:
            json.dump({
                "patch_id": patch.patch_id,
                "date": patch.date,
                "symbol": patch.symbol,
                "target": patch.target,
                "changes": patch.changes,
                "reason": patch.reason,
                "evidence": patch.evidence,
                "status": patch.status,
            }, f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        logger.error(f"Failed to save tuning patch {patch.patch_id}: {e}", exc_info=True)
        raise

