"""
Signal Drift Score v1 - Method Layer Drift Detection

Detects "learning decay" in the Method Layer by calculating drift_score (0-1)
and drift_level (LOW/MEDIUM/HIGH).

v1 Algorithm: Mean Absolute Relative Shift (MARS)
- Simple, stable, deterministic, explainable
- No external dependencies (standard library only)
"""

from typing import Dict, List, Literal, Optional
from datetime import datetime


def compute_drift_score_v1(
    baseline: Dict[str, float],
    current: Dict[str, float],
    eps: float = 1e-6,
) -> Dict:
    """
    Compute drift score using Mean Absolute Relative Shift (MARS).
    
    Args:
        baseline: Baseline feature distribution (dict[str, float] = mean values)
        current: Current feature distribution (dict[str, float] = mean values)
        eps: Small epsilon to avoid division by zero
    
    Returns:
        Dict with:
            - drift_score: float in [0, 1]
            - drift_level: "LOW" | "MEDIUM" | "HIGH"
            - features_used: List[str] (intersection of baseline and current keys)
            - notes: Optional[str] (warnings if < 3 features)
    """
    # Find intersection of features
    baseline_keys = set(baseline.keys())
    current_keys = set(current.keys())
    common_features = list(baseline_keys & current_keys)
    
    # If too few common features, return low drift
    if len(common_features) < 3:
        return {
            "drift_score": 0.0,
            "drift_level": "LOW",
            "features_used": common_features,
            "notes": f"Insufficient common features ({len(common_features)} < 3), cannot compute reliable drift",
        }
    
    # Calculate relative shift for each feature
    rel_shifts = []
    for feature in common_features:
        base_val = baseline[feature]
        curr_val = current[feature]
        
        # Relative shift: abs(curr - base) / max(abs(base), eps)
        # Clip to [0, 5] to avoid extreme outliers
        denominator = max(abs(base_val), eps)
        rel_shift = abs(curr_val - base_val) / denominator
        rel_shift = min(rel_shift, 5.0)  # Clip to 5
        rel_shifts.append(rel_shift)
    
    # Mean of relative shifts
    raw_score = sum(rel_shifts) / len(rel_shifts) if rel_shifts else 0.0
    
    # Normalize to [0, 1]: raw >= 1.0 is considered high drift
    drift_score = min(raw_score / 1.0, 1.0)
    
    # Determine drift level
    if drift_score < 0.3:
        drift_level: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"
    elif drift_score < 0.7:
        drift_level = "MEDIUM"
    else:
        drift_level = "HIGH"
    
    return {
        "drift_score": round(drift_score, 4),
        "drift_level": drift_level,
        "features_used": common_features,
        "notes": None if len(common_features) >= 3 else f"Only {len(common_features)} common features",
    }

