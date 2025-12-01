"""
Path A v1 - Error Bridge

This module provides a bridge between Path A backtest results and
the Error Learning Engine. It converts prediction outcomes into
ErrorEvent objects that can be analyzed by ErrorLearningEngine.
"""

from __future__ import annotations

from typing import Optional
import pandas as pd

from jgod.learning.error_learning_engine import ErrorLearningEngine
from jgod.learning.error_event import ErrorEvent, CLASS_UTILIZATION_GAP, CLASS_FORM_INSUFFICIENT, CLASS_KNOWLEDGE_GAP


class PathAErrorBridge:
    """
    Bridge between Path A backtest outcomes and Error Learning Engine.
    
    This class converts portfolio prediction outcomes (expected vs realized)
    into ErrorEvent objects that can be analyzed by ErrorLearningEngine.
    
    v1 implementation is a skeleton - many details are left as TODOs.
    """
    
    def __init__(self):
        """Initialize PathAErrorBridge"""
        pass
    
    def handle_prediction_outcome(
        self,
        date: pd.Timestamp,
        weights: pd.Series,
        realized_returns: pd.Series,
        expected_scores: pd.Series,
        error_engine: ErrorLearningEngine,
    ) -> None:
        """
        Given the portfolio decision and realized outcome for a date (or period),
        build appropriate ErrorEvent(s) and send them to the ErrorLearningEngine.
        
        Args:
            date: Date of the prediction/outcome
            weights: Portfolio weights that were held
            realized_returns: Actual realized returns for each symbol
            expected_scores: Expected scores (e.g. composite_alpha) for each symbol
            error_engine: ErrorLearningEngine instance to process errors
        
        v1 Implementation:
        - Creates a single aggregated ErrorEvent for the portfolio-level outcome
        - Future versions may create per-symbol events for granular analysis
        """
        
        # Calculate portfolio-level metrics
        portfolio_expected_return = float((weights * expected_scores).sum())
        portfolio_realized_return = float((weights * realized_returns).sum())
        
        # Calculate prediction error
        prediction_error = portfolio_expected_return - portfolio_realized_return
        
        # Only create error event if error is significant
        # TODO: Make threshold configurable
        error_threshold = 0.01  # 1% error threshold
        if abs(prediction_error) < error_threshold:
            return  # Skip small errors
        
        # Build error event
        # TODO: Enhance ErrorEvent creation with more context:
        # - Market regime information
        # - Risk factor exposures
        # - Alpha factor contributions
        # - Transaction costs
        
        error_event = ErrorEvent(
            id=f"PATH_A_{date.strftime('%Y%m%d')}_{id(date)}",
            timestamp=date.isoformat(),
            symbol="PORTFOLIO",  # Portfolio-level event
            timeframe="1d",
            side=None,
            predicted_outcome="up" if portfolio_expected_return > 0 else "down",
            actual_outcome="up" if portfolio_realized_return > 0 else "down",
            pnl=portfolio_realized_return,
            error_type="direction" if (
                (portfolio_expected_return > 0) != (portfolio_realized_return > 0)
            ) else "magnitude",
            tags=["path_a", "portfolio_level"],
            used_signals=list(expected_scores.index[:5]),  # Top 5 signals
            used_rules=[],  # TODO: Track which rules were used
            regime=None,  # TODO: Add regime information
            context={
                "expected_return": portfolio_expected_return,
                "realized_return": portfolio_realized_return,
                "prediction_error": prediction_error,
                "portfolio_size": len(weights[weights.abs() > 0.01]),
            },
            notes=f"Path A backtest prediction error on {date.strftime('%Y-%m-%d')}",
        )
        
        # Process error through ErrorLearningEngine
        try:
            error_engine.process_and_report(error_event)
        except Exception as e:
            print(f"Warning: Failed to process error event: {e}")
            # Continue execution even if error processing fails


# Convenience function for creating a default error bridge
def create_default_error_bridge() -> PathAErrorBridge:
    """Create a default PathAErrorBridge instance"""
    return PathAErrorBridge()

