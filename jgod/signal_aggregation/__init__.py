"""J-GOD Signal Aggregation Engine v1

Provides signal aggregation functionality to compute consensus and conflict scores
for multi-strategy signal analysis.
"""

from .models import StrategyVotesRow, ConflictItem
from .engine import SignalAggregationEngineV1
from .data_access import get_strategy_votes_for_date

__all__ = [
    "StrategyVotesRow",
    "ConflictItem",
    "SignalAggregationEngineV1",
    "get_strategy_votes_for_date",
]

