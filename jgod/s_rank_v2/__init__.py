"""
S-Rank Engine V2

Strategy recommendation system based on prediction timeline metrics.
"""

from jgod.s_rank_v2.models import (
    RecommendationSnapshot,
    RecommendationItem,
    Metrics,
    StabilityGrade,
)
from jgod.s_rank_v2.service import (
    get_recommendation,
    recompute_and_save,
    get_latest_snapshot,
)
from jgod.s_rank_v2.recommender import recommend

__all__ = [
    "RecommendationSnapshot",
    "RecommendationItem",
    "Metrics",
    "StabilityGrade",
    "get_recommendation",
    "recompute_and_save",
    "get_latest_snapshot",
    "recommend",
]

