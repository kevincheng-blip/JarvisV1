"""Knowledge Brain Observer Data Models

Pydantic models for knowledge governance monitoring.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class KnowledgeGovernanceSummary(BaseModel):
    """知識治理狀態概覽"""
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # --- Doctrine 治理狀態 ---
    total_sections: int = 0  # 條文總數
    pending_review_count: int = 0  # DMC 待審核數量
    critical_alerts_active: int = 0  # 當前 CRITICAL 警報數量
    sections_modified_last_7d: int = 0  # 過去 7 天 Doctrine 修改次數
    
    # --- Rule Simulation 狀態 ---
    simulations_last_30d: int = 0  # 過去 30 天運行模擬次數
    sim_approve_rate_30d: float = 0.0  # 30 天內 Rule Sim 的批准率 (APPROVE / SUCCESS)
    sim_maxdd_increase_rate_30d: float = 0.0  # 30 天內 MaxDD 惡化 (REJECT) 的模擬比例
    
    # --- S-Rank 穩定性 ---
    s_rank_recalculations_last_24h: int = 0  # 過去 24 小時 S-Rank 重新計算次數
    s_rank_strategy_degradation_7d: int = 0  # 過去 7 天內從 A/B 級降至 C/D 級的策略數量
    s_rank_distribution: Dict[str, int] = Field(default_factory=lambda: {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0})  # 當前 S/A/B/C/D 級別的策略數量分佈


class StabilityAlert(BaseModel):
    """穩定性警報"""
    severity: str  # "CRITICAL" | "WARNING" | "INFO"
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class SRankDistributionHistory(BaseModel):
    """S-Rank 分佈歷史數據"""
    date: str  # ISO date string
    distribution: Dict[str, int]  # S/A/B/C/D counts

