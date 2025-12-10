"""Knowledge Brain Observer API Schemas

Pydantic models for Observer API endpoints.
"""

from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel


class KnowledgeGovernanceSummarySchema(BaseModel):
    """知識治理狀態概覽 Schema"""
    timestamp: datetime
    total_sections: int = 0
    pending_review_count: int = 0
    critical_alerts_active: int = 0
    sections_modified_last_7d: int = 0
    simulations_last_30d: int = 0
    sim_approve_rate_30d: float = 0.0
    sim_maxdd_increase_rate_30d: float = 0.0
    s_rank_recalculations_last_24h: int = 0
    s_rank_strategy_degradation_7d: int = 0
    s_rank_distribution: Dict[str, int] = {}


class StabilityAlertSchema(BaseModel):
    """穩定性警報 Schema"""
    severity: str  # "CRITICAL" | "WARNING" | "INFO"
    message: str
    timestamp: datetime


class SRankDistributionHistorySchema(BaseModel):
    """S-Rank 分佈歷史數據 Schema"""
    date: str  # ISO date string
    distribution: Dict[str, int]  # S/A/B/C/D counts

