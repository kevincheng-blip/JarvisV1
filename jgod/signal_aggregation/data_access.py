"""Signal Aggregation Data Access Layer

Functions to retrieve strategy votes and signals from various data sources.
"""

import logging
from datetime import date
from typing import List, Optional, Dict

from jgod.signal_aggregation.models import StrategyVotesRow
from jgod.storage.db import get_session
from jgod.storage.models import PredictionSnapshot, Stock

logger = logging.getLogger(__name__)


def get_strategy_votes_for_date(
    trade_date: date,
    limit: Optional[int] = None,
    db_session=None,
) -> List[StrategyVotesRow]:
    """
    Get strategy votes for all symbols on a specific date.
    
    This function retrieves prediction snapshots and extracts strategy-level
    signals. In v1, we simulate strategy votes based on PredictionSnapshot data.
    Future versions may read from a dedicated strategy_signals table.
    
    Args:
        trade_date: Target date
        limit: Maximum number of symbols to return (None = all)
        db_session: SQLAlchemy session (optional)
    
    Returns:
        List of StrategyVotesRow objects
    """
    if db_session is None:
        session_gen = get_session()
        db_session = next(session_gen)
    
    try:
        # Query prediction snapshots for the date
        predictions = db_session.query(PredictionSnapshot).filter(
            PredictionSnapshot.date == trade_date
        ).all()
        
        if not predictions:
            logger.info(f"No predictions found for date {trade_date}")
            return []
        
        # Get stock names mapping
        symbols = [pred.symbol for pred in predictions]
        stocks = db_session.query(Stock).filter(Stock.symbol.in_(symbols)).all()
        name_map = {stock.symbol: (stock.name_zh or stock.name_en or stock.symbol) for stock in stocks}
        
        # Convert predictions to StrategyVotesRow
        votes_rows = []
        
        for pred in predictions:
            # Get raw_score
            raw_score = pred.score or pred.total_score or 0.0
            
            # Get final_score (if available from Decision Layer)
            final_score = None
            # Note: In v1, final_score might not be stored in PredictionSnapshot yet
            # Future: Read from DecisionOutput table or similar
            
            # Simulate strategy votes based on prediction data
            # In v1, we create mock votes based on the prediction score
            # Future: Read from actual strategy_signals table
            strategy_votes = _simulate_strategy_votes(pred, raw_score)
            
            votes_row = StrategyVotesRow(
                symbol=pred.symbol,
                name=name_map.get(pred.symbol, pred.symbol),
                date=trade_date,
                raw_score=float(raw_score),
                final_score=float(final_score) if final_score is not None else None,
                strategy_votes=strategy_votes,
            )
            votes_rows.append(votes_row)
        
        # Apply limit
        if limit:
            votes_rows = votes_rows[:limit]
        
        logger.info(f"Retrieved {len(votes_rows)} strategy votes for date {trade_date}")
        return votes_rows
    
    except Exception as e:
        logger.error(f"Error retrieving strategy votes: {e}", exc_info=True)
        return []


def _simulate_strategy_votes(prediction: PredictionSnapshot, raw_score: float) -> Dict[str, int]:
    """
    Simulate strategy votes based on prediction data.
    
    In v1, we generate mock strategy votes (S1 ~ S10) based on the prediction.
    This is a placeholder until actual strategy signals are available.
    
    Strategy votes are extracted from positive_factors_json and negative_factors_json
    to simulate individual strategy opinions. If those fields are not available,
    we generate votes based on raw_score with some variance.
    
    Args:
        prediction: PredictionSnapshot object
        raw_score: Raw prediction score
    
    Returns:
        Dictionary mapping strategy IDs to votes: {"S1": 1, "S2": -1, ...}
    """
    strategy_votes = {}
    
    # Try to extract strategy signals from prediction metadata
    # In future, this should read from a dedicated strategy_signals table
    
    # Check if we have indicator-level data that could represent strategies
    positive_factors = getattr(prediction, 'positive_factors_json', None) or getattr(prediction, 'positive_indicators', None)
    negative_factors = getattr(prediction, 'negative_factors_json', None) or getattr(prediction, 'negative_indicators', None)
    
    if positive_factors or negative_factors:
        # Use factors as proxy for strategy votes
        # Map top positive factors to bullish votes, negative to bearish
        strategy_idx = 1
        
        if positive_factors:
            for factor in positive_factors[:5]:  # Use top 5 positive
                strategy_votes[f"S{strategy_idx}"] = 1
                strategy_idx += 1
        
        if negative_factors:
            for factor in negative_factors[:5]:  # Use top 5 negative
                strategy_votes[f"S{strategy_idx}"] = -1
                strategy_idx += 1
        
        # Fill remaining strategies as neutral or based on raw_score
        while strategy_idx <= 10:
            if raw_score > 0.2:
                strategy_votes[f"S{strategy_idx}"] = 1
            elif raw_score < -0.2:
                strategy_votes[f"S{strategy_idx}"] = -1
            else:
                strategy_votes[f"S{strategy_idx}"] = 0
            strategy_idx += 1
    else:
        # Fallback: Generate votes based on raw_score with variance
        import random
        
        # Set seed based on symbol + date for consistency
        random.seed(hash(f"{prediction.symbol}_{prediction.date}"))
        
        # Determine base direction from raw_score
        if raw_score > 0.3:
            base_direction = 1  # Generally bullish
        elif raw_score < -0.3:
            base_direction = -1  # Generally bearish
        else:
            base_direction = 0  # Neutral
        
        # Generate votes with some consensus but also some disagreement
        num_strategies = 10
        consensus_level = 0.7  # 70% consensus
        
        for i in range(1, num_strategies + 1):
            strategy_id = f"S{i}"
            
            # Most strategies agree with base direction
            if random.random() < consensus_level:
                vote = base_direction
            else:
                # Some strategies disagree
                if base_direction == 1:
                    vote = random.choice([-1, 0])
                elif base_direction == -1:
                    vote = random.choice([1, 0])
                else:
                    vote = random.choice([-1, 0, 1])
            
            strategy_votes[strategy_id] = vote
    
    return strategy_votes

