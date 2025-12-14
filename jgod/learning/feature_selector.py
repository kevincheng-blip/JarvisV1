"""
Feature Selector: Method Layer (10/20-day feature selection)

v0.6.8-A8: Analyzes feature contribution and recommends feature subset
v0.6.9-A9: Inherits BaseLayer, computes quality_score, supports auto-apply
Only generates suggestions, never auto-applies directly.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from jgod.learning.models import FeatureSubset, PatchStatus
from jgod.learning.base_layer import BaseLayer
from jgod.research.backtest_engine import BacktestEngine, BacktestConfig
from jgod.research.storage import load_daily_logs

logger = logging.getLogger(__name__)


def analyze_and_suggest_subset(
    symbol: str,
    date_str: str,
    window: int = 20,
    snapshot_id: str = "",
) -> Optional[FeatureSubset]:
    """
    Analyze feature contribution and recommend feature subset.
    
    Args:
        symbol: Stock symbol
        date_str: Current date (YYYY-MM-DD)
        window: Analysis window (10 or 20 days)
        
    Returns:
        FeatureSubset suggestion or None if insufficient data
    """
    # Step 1: Load recent daily logs
    end_date = date_str
    start_date = (datetime.strptime(date_str, "%Y-%m-%d").date() - timedelta(days=window)).strftime("%Y-%m-%d")
    
    logs = load_daily_logs(symbol, start_date, end_date, limit=window)
    
    if len(logs) < window:
        logger.warning(f"Insufficient logs for {symbol} from {start_date} to {end_date}")
        return None
    
    # Step 2: Extract features from logs
    all_features = set()
    for log in logs:
        features_summary = log.get("features_summary", {})
        all_features.update(features_summary.keys())
    
    if not all_features:
        return None
    
    # Step 3: Simple correlation analysis (simplified for M3)
    # Compare P&L with feature values
    feature_scores = {}
    
    for feature_name in all_features:
        if feature_name is None:
            continue
        
        # Extract feature values and NAV changes
        feature_values = []
        nav_changes = []
        
        for i in range(1, len(logs)):
            prev_log = logs[i-1]
            curr_log = logs[i]
            
            feature_val = curr_log.get("features_summary", {}).get(feature_name)
            if feature_val is None:
                continue
            
            prev_nav = prev_log.get("nav", 0.0)
            curr_nav = curr_log.get("nav", 0.0)
            
            if prev_nav > 0:
                nav_change = (curr_nav - prev_nav) / prev_nav
                feature_values.append(feature_val)
                nav_changes.append(nav_change)
        
        if len(feature_values) < 5:
            continue
        
        # Simple correlation (sign-based)
        # Count how often feature direction matches NAV direction
        matches = 0
        for j in range(len(feature_values)):
            if j == 0:
                continue
            feature_dir = 1 if feature_values[j] > feature_values[j-1] else -1
            nav_dir = 1 if nav_changes[j] > 0 else -1
            if feature_dir == nav_dir:
                matches += 1
        
        correlation_score = matches / len(feature_values) if feature_values else 0.0
        feature_scores[feature_name] = correlation_score
    
    # Step 4: Select top features (correlation > 0.5)
    recommended_features = [
        feat for feat, score in feature_scores.items()
        if score > 0.5
    ]
    
    # If no features pass threshold, use all
    if not recommended_features:
        recommended_features = list(all_features)
    
    # Sort by score descending
    recommended_features.sort(key=lambda x: feature_scores.get(x, 0.0), reverse=True)
    
    # Step 5: Generate suggestion
    reason_parts = []
    reason_parts.append(f"基於最近 {window} 日資料分析，以下因子與 P&L 相關性較高：")
    for feat in recommended_features[:5]:  # Top 5
        score = feature_scores.get(feat, 0.0)
        reason_parts.append(f"- {feat}: 相關性 {score:.2%}")
    
    # v0.6.9-A9: Compute quality score and status
    base_layer = BaseLayer("method")
    evidence_dict = {
        "feature_scores": {k: round(v, 4) for k, v in feature_scores.items()},
        "window": window,
        "total_features": len(all_features),
    }
    quality_score = base_layer.compute_quality_score({
        "evidence": evidence_dict
    })
    status = base_layer.finalize_status(quality_score)
    
    return FeatureSubset(
        date=date_str,
        symbol=symbol,
        recommended_features=recommended_features,
        reason="\n".join(reason_parts),
        evidence=evidence_dict,
        quality_score=quality_score,
        status=status,
        snapshot_id=snapshot_id,
    )


def select_global_features(
    symbols: List[str],
    start_date: str,
    end_date: str,
    *,
    window: int = 20,
    snapshot_id: str = "",
) -> Optional[FeatureSubset]:
    """
    Select global feature subset across multiple symbols.
    
    v0.6.10-A10: Multi-symbol feature selection.
    
    Args:
        symbols: List of stock symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        window: Analysis window (days)
        snapshot_id: Snapshot ID for consistency
        
    Returns:
        FeatureSubset with scope="global" or None if insufficient data
    """
    from jgod.research.storage import load_daily_logs
    
    # Step 1: Load logs for all symbols
    all_symbol_scores = {}
    
    for symbol in symbols:
        logs = load_daily_logs(symbol, start_date, end_date, limit=window)
        
        if len(logs) < window:
            logger.warning(f"Insufficient logs for {symbol} from {start_date} to {end_date}")
            continue
        
        # Extract features and calculate scores (same logic as single-symbol)
        all_features = set()
        for log in logs:
            features_summary = log.get("features_summary", {})
            all_features.update(features_summary.keys())
        
        if not all_features:
            continue
        
        # Calculate feature scores for this symbol
        feature_scores = {}
        
        for feature_name in all_features:
            if feature_name is None:
                continue
            
            feature_values = []
            nav_changes = []
            
            for i in range(1, len(logs)):
                prev_log = logs[i-1]
                curr_log = logs[i]
                
                feature_val = curr_log.get("features_summary", {}).get(feature_name)
                if feature_val is None:
                    continue
                
                prev_nav = prev_log.get("nav", 0.0)
                curr_nav = curr_log.get("nav", 0.0)
                
                if prev_nav > 0:
                    nav_change = (curr_nav - prev_nav) / prev_nav
                    feature_values.append(feature_val)
                    nav_changes.append(nav_change)
            
            if len(feature_values) < 5:
                continue
            
            # Simple correlation (sign-based)
            matches = 0
            for j in range(len(feature_values)):
                if j == 0:
                    continue
                feature_dir = 1 if feature_values[j] > feature_values[j-1] else -1
                nav_dir = 1 if nav_changes[j] > 0 else -1
                if feature_dir == nav_dir:
                    matches += 1
            
            correlation_score = matches / len(feature_values) if feature_values else 0.0
            feature_scores[feature_name] = correlation_score
        
        all_symbol_scores[symbol] = feature_scores
    
    if not all_symbol_scores:
        return None
    
    # Step 2: Aggregate scores across symbols (mean)
    global_scores = {}
    all_feature_names = set()
    for scores in all_symbol_scores.values():
        all_feature_names.update(scores.keys())
    
    for feature_name in all_feature_names:
        symbol_scores = [
            scores.get(feature_name, 0.0)
            for scores in all_symbol_scores.values()
        ]
        if symbol_scores:
            global_scores[feature_name] = sum(symbol_scores) / len(symbol_scores)
    
    # Step 3: Select top features
    recommended_features = [
        feat for feat, score in global_scores.items()
        if score > 0.5
    ]
    
    if not recommended_features:
        recommended_features = list(all_feature_names)
    
    recommended_features.sort(key=lambda x: global_scores.get(x, 0.0), reverse=True)
    
    # Step 4: Generate suggestion
    reason_parts = []
    reason_parts.append(f"基於 {len(symbols)} 個標的、最近 {window} 日資料的全局分析：")
    for feat in recommended_features[:5]:  # Top 5
        score = global_scores.get(feat, 0.0)
        reason_parts.append(f"- {feat}: 全局相關性 {score:.2%}")
    
    # v0.6.10-A10: Compute quality score and status (use global scores)
    base_layer = BaseLayer("method")
    evidence_dict = {
        "feature_scores": {k: round(v, 4) for k, v in global_scores.items()},
        "window": window,
        "total_features": len(all_feature_names),
        "symbol_count": len(symbols),
    }
    quality_score = base_layer.compute_quality_score({
        "evidence": evidence_dict
    })
    status = base_layer.finalize_status(quality_score)
    
    return FeatureSubset(
        date=end_date,
        symbol=None,  # Global scope
        recommended_features=recommended_features,
        reason="\n".join(reason_parts),
        evidence=evidence_dict,
        quality_score=quality_score,
        status=status,
        snapshot_id=snapshot_id,
        scope="global",
        target_symbols=symbols,
    )


def save_feature_subset(subset: FeatureSubset) -> None:
    """
    Save feature subset suggestion to storage.
    
    Args:
        subset: FeatureSubset to save
    """
    from pathlib import Path
    import json
    
    project_root = Path(__file__).resolve().parents[2]
    learning_dir = project_root / "data" / "learning"
    learning_dir.mkdir(parents=True, exist_ok=True)
    storage_path = learning_dir / "method_log.jsonl"
    
    try:
        with open(storage_path, "a", encoding="utf-8") as f:
            json.dump({
                "date": subset.date,
                "symbol": subset.symbol,
                "recommended_features": subset.recommended_features,
                "reason": subset.reason,
                "evidence": subset.evidence,
                "status": subset.status,
            }, f, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        logger.error(f"Failed to save feature subset for {subset.symbol}: {e}", exc_info=True)
        raise

