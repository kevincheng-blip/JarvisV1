"""Signal Aggregation Engine v1

Core engine for computing consensus and conflict scores from multi-strategy signals.
"""

import logging
from datetime import date
from typing import List, Optional, Literal

from jgod.signal_aggregation.models import StrategyVotesRow, ConflictItem
from jgod.signal_aggregation.data_access import get_strategy_votes_for_date

logger = logging.getLogger(__name__)


class SignalAggregationEngineV1:
    """Signal Aggregation Engine v1
    
    Computes consensus and conflict scores from multi-strategy votes.
    """
    
    def __init__(self, db_session=None):
        """
        Initialize Signal Aggregation Engine
        
        Args:
            db_session: SQLAlchemy database session (optional)
        """
        self.db_session = db_session
    
    def _compute_consensus_score(self, votes: List[int]) -> float:
        """Compute consensus score from strategy votes
        
        Consensus Score = |sum(Vi)| / N_eff * 100
        
        Args:
            votes: List of votes (1, -1, or 0)
        
        Returns:
            Consensus score (0-100)
        """
        if not votes:
            return 0.0
        
        n_eff = len(votes)
        if n_eff == 0:
            return 0.0
        
        vote_sum = sum(votes)
        consensus = abs(vote_sum) / n_eff * 100.0
        
        # Ensure range [0, 100]
        return min(100.0, max(0.0, consensus))
    
    def _compute_conflict_score(self, votes: List[int]) -> tuple[float, int]:
        """Compute conflict score and majority vote from strategy votes
        
        Conflict Score = opposite_votes / floor(N_eff/2) * 100
        
        Args:
            votes: List of votes (1, -1, or 0)
        
        Returns:
            Tuple of (conflict_score: float, majority_vote: int)
            majority_vote: 1 (long), -1 (short), 0 (neutral)
        """
        if not votes:
            return 0.0, 0
        
        n_eff = len(votes)
        if n_eff < 2:
            # Not enough strategies to compute conflict
            return 0.0, 0
        
        vote_sum = sum(votes)
        
        # Determine majority vote
        if vote_sum > 0:
            majority_vote = 1  # Long
        elif vote_sum < 0:
            majority_vote = -1  # Short
        else:
            majority_vote = 0  # Neutral (tie or all zero)
        
        # If no clear majority, conflict score is 0
        if majority_vote == 0:
            return 0.0, 0
        
        # Count opposite votes (votes that disagree with majority)
        opposite_votes = sum(1 for v in votes if v * majority_vote < 0)
        
        # Calculate conflict score
        # Formula: opposite_votes / floor(N_eff/2) * 100
        denominator = max(1, n_eff // 2)
        conflict = (opposite_votes / denominator) * 100.0
        
        # Cap at 100
        conflict = min(100.0, conflict)
        
        return conflict, majority_vote
    
    def get_conflicts_for_date(
        self,
        trade_date: date,
        limit: Optional[int] = 50,
        side: Optional[Literal["long", "short", "all"]] = "all",
        db_session=None,
    ) -> List[ConflictItem]:
        """
        Get conflict items for a specific date.
        
        Args:
            trade_date: Target date
            limit: Maximum number of items to return
            side: Filter by side ("long", "short", "all")
            db_session: Database session (optional)
        
        Returns:
            List of ConflictItem objects, sorted by conflict_score (descending)
        """
        # Get strategy votes
        votes_rows = get_strategy_votes_for_date(
            trade_date=trade_date,
            limit=None,  # Get all first, then filter and limit
            db_session=db_session or self.db_session,
        )
        
        if not votes_rows:
            logger.info(f"No strategy votes found for date {trade_date}")
            return []
        
        # Process each row to compute conflict items
        conflict_items = []
        
        for votes_row in votes_rows:
            # Extract votes list
            votes_list = list(votes_row.strategy_votes.values())
            
            # Filter out None values (missing strategies)
            valid_votes = [v for v in votes_list if v is not None]
            
            # Need at least 2 valid votes to compute conflict
            if len(valid_votes) < 2:
                # Use default values for insufficient data
                consensus_score = 0.0
                conflict_score = 0.0
                majority_vote = 0
            else:
                # Compute consensus and conflict
                consensus_score = self._compute_consensus_score(valid_votes)
                conflict_score, majority_vote = self._compute_conflict_score(valid_votes)
            
            # Filter by side if specified
            if side == "long" and majority_vote != 1:
                continue
            elif side == "short" and majority_vote != -1:
                continue
            
            conflict_item = ConflictItem(
                symbol=votes_row.symbol,
                name=votes_row.name,
                consensus_score=consensus_score,
                conflict_score=conflict_score,
                majority_vote=majority_vote,
                strategy_votes=votes_row.strategy_votes,
                raw_score=votes_row.raw_score,
                final_score=votes_row.final_score,
            )
            
            conflict_items.append(conflict_item)
        
        # Sort by conflict_score (descending) - most conflicted first
        conflict_items.sort(key=lambda x: x.conflict_score, reverse=True)
        
        # --- normalize limit ---
        DEFAULT_LIMIT = 50
        MAX_LIMIT = 500

        if limit is None:
            limit_i = DEFAULT_LIMIT
        else:
            try:
                # allow "60", 60.0, etc.
                limit_i = int(float(limit))
            except (TypeError, ValueError):
                limit_i = DEFAULT_LIMIT

        # clamp
        if limit_i < 1:
            limit_i = 1
        if limit_i > MAX_LIMIT:
            limit_i = MAX_LIMIT

        # apply slice
        if limit_i < len(conflict_items):
            conflict_items = conflict_items[:limit_i]
        
        logger.info(
            f"Generated {len(conflict_items)} conflict items for date {trade_date} "
            f"(side={side}, limit={limit})"
        )
        
        return conflict_items

