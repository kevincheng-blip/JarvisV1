"""Signal Aggregation Data Models

Defines data structures for signal aggregation and conflict analysis.
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, Optional


@dataclass
class StrategyVotesRow:
    """Single row of strategy votes for a symbol
    
    Represents all strategy votes (S1 ~ S10) for a single stock on a specific date.
    """
    symbol: str
    name: str
    date: date
    raw_score: float
    final_score: Optional[float] = None
    strategy_votes: Dict[str, int] = None  # {"S1": 1, "S2": -1, "S3": 0, ...}
    
    def __post_init__(self):
        if self.strategy_votes is None:
            self.strategy_votes = {}


@dataclass
class ConflictItem:
    """Conflict analysis result for a single symbol
    
    Contains consensus score, conflict score, majority vote, and strategy votes.
    """
    symbol: str
    name: str
    consensus_score: float  # 0-100
    conflict_score: float  # 0-100
    majority_vote: int  # 1: long, -1: short, 0: neutral
    strategy_votes: Dict[str, int]  # {"S1": 1, "S2": -1, ...}
    raw_score: Optional[float] = None
    final_score: Optional[float] = None
    
    def __post_init__(self):
        if self.strategy_votes is None:
            self.strategy_votes = {}

