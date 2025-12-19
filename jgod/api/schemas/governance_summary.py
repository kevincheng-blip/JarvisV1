"""
Governance summary schemas (Pydantic v2 friendly).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class GovernanceModuleStatus(BaseModel):
    status: str = "UNKNOWN"
    score: Optional[float] = None
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    is_stub: bool = True
    reasons: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class GovernanceSummary(BaseModel):
    drift_status: str = "UNKNOWN"
    execution_confidence: GovernanceModuleStatus = Field(default_factory=GovernanceModuleStatus)
    cluster_risk: GovernanceModuleStatus = Field(default_factory=GovernanceModuleStatus)
    regime: GovernanceModuleStatus = Field(default_factory=GovernanceModuleStatus)
    market_complexity: Union[str, float] = "UNKNOWN"
    ai_action: str = "OBSERVE_ONLY"
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    is_stub: bool = True
    reasons: List[str] = Field(default_factory=list)
    primary_reason_code: str = "ALL_CLEAR"
    human_sentence: str = "AI outputs are allowed."
    recommended_human_action: str = "Proceed with AI recommendations."
    action_confidence: str = "MEDIUM"
    explain: Optional[dict] = None
    recommended_ops: Dict[str, Any] = Field(default_factory=dict)
    guardrails: Dict[str, Any] = Field(default_factory=dict)
    decision_context: Optional[Dict[str, Any]] = Field(default_factory=dict)


