"""
Learning Base Layer: Guard Rails Core

v0.6.9-A9: Abstract base for quality scoring and auto-apply thresholds
"""

import logging
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class PatchStatus(str, Enum):
    """Patch status enum."""
    PENDING_APPROVAL = "PENDING_APPROVAL"
    AUTO_APPLY = "AUTO_APPLY"
    REJECTED = "REJECTED"


class BaseLayer:
    """
    Abstract base class for Learning Layers.
    
    Provides quality scoring and auto-apply threshold logic.
    """
    
    # Threshold constants (can be made configurable later)
    THOUGHT_THRESHOLD = 0.15  # For tuning_advisor
    METHOD_THRESHOLD = 0.12   # For feature_selector
    STRATEGY_THRESHOLD = 0.10  # For strategy_allocator
    
    def __init__(self, layer_name: str, threshold: Optional[float] = None):
        """
        Initialize BaseLayer.
        
        Args:
            layer_name: Layer name ("thought", "method", "strategy")
            threshold: Custom threshold (if None, uses default)
        """
        self.layer_name = layer_name
        self.threshold = threshold or self._get_default_threshold()
    
    def _get_default_threshold(self) -> float:
        """Get default threshold based on layer name."""
        if self.layer_name == "thought":
            return self.THOUGHT_THRESHOLD
        elif self.layer_name == "method":
            return self.METHOD_THRESHOLD
        elif self.layer_name == "strategy":
            return self.STRATEGY_THRESHOLD
        else:
            return 0.10  # Default
    
    def compute_quality_score(self, output_dict: Dict) -> float:
        """
        Compute quality score for learning output.
        
        Args:
            output_dict: Output dict from learning layer
            
        Returns:
            Quality score (0.0 ~ 1.0)
        """
        if self.layer_name == "thought":
            return self._compute_thought_score(output_dict)
        elif self.layer_name == "method":
            return self._compute_method_score(output_dict)
        elif self.layer_name == "strategy":
            return self._compute_strategy_score(output_dict)
        else:
            return 0.0
    
    def _compute_thought_score(self, output_dict: Dict) -> float:
        """
        Compute quality score for Thought Layer (tuning_advisor).
        
        Based on: score_delta, pnl_delta, mdd_change
        """
        evidence = output_dict.get("evidence", {})
        
        # Extract metrics
        score_delta = abs(evidence.get("score_delta", 0.0))
        pnl_delta = abs(evidence.get("pnl_delta", 0.0))
        mdd_change = evidence.get("mdd_change", 0.0)
        
        # Normalize and combine
        score_component = min(score_delta / 0.5, 1.0)  # Normalize to [0, 1]
        pnl_component = min(pnl_delta / 0.1, 1.0)  # 10% return = max score
        mdd_component = max(0.0, 1.0 - (mdd_change / 0.3))  # Lower MDD is better
        
        # Weighted combination
        quality_score = (
            0.4 * score_component +
            0.4 * pnl_component +
            0.2 * mdd_component
        )
        
        return round(quality_score, 4)
    
    def _compute_method_score(self, output_dict: Dict) -> float:
        """
        Compute quality score for Method Layer (feature_selector).
        
        Based on: top_feature_score_mean, improvement proxy
        """
        evidence = output_dict.get("evidence", {})
        feature_scores = evidence.get("feature_scores", {})
        
        if not feature_scores:
            return 0.0
        
        # Get top feature scores
        scores = list(feature_scores.values())
        if not scores:
            return 0.0
        
        # Average of top 3 features
        top_scores = sorted(scores, reverse=True)[:3]
        mean_score = sum(top_scores) / len(top_scores) if top_scores else 0.0
        
        # Normalize (correlation > 0.5 is good)
        quality_score = min(mean_score / 0.7, 1.0)  # 0.7 correlation = max score
        
        return round(quality_score, 4)
    
    def _compute_strategy_score(self, output_dict: Dict) -> float:
        """
        Compute quality score for Strategy Layer (strategy_allocator).
        
        Based on: composite_score_delta
        """
        evidence = output_dict.get("evidence", {})
        strategy_scores = evidence.get("strategy_scores", {})
        
        if not strategy_scores:
            return 0.0
        
        # Get current and recommended strategy scores
        current_strategy = evidence.get("current_strategy")
        if not current_strategy:
            return 0.0
        
        current_score = strategy_scores.get(current_strategy, {}).get("composite_score", 0.0)
        
        # Find best strategy score
        best_score = max(
            (s.get("composite_score", 0.0) for s in strategy_scores.values()),
            default=0.0
        )
        
        score_delta = best_score - current_score
        
        # Normalize (positive delta is improvement)
        quality_score = min(max(score_delta / 0.2, 0.0), 1.0)  # 0.2 delta = max score
        
        return round(quality_score, 4)
    
    def auto_apply_threshold(self) -> float:
        """Get auto-apply threshold for this layer."""
        return self.threshold
    
    def should_auto_apply(self, score: float) -> bool:
        """
        Check if score exceeds auto-apply threshold.
        
        Args:
            score: Quality score
            
        Returns:
            True if should auto-apply
        """
        return score >= self.threshold
    
    def finalize_status(self, score: float) -> PatchStatus:
        """
        Finalize patch status based on quality score.
        
        Args:
            score: Quality score
            
        Returns:
            PatchStatus
        """
        if score >= self.threshold:
            return PatchStatus.AUTO_APPLY
        elif score >= self.threshold * 0.5:  # Half threshold = pending
            return PatchStatus.PENDING_APPROVAL
        else:
            return PatchStatus.REJECTED

