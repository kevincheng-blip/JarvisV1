"""Rule Simulation API Schemas

Pydantic models for Rule Simulation API endpoints.
"""

from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field

from jgod.rule_sim.models import RuleSimTargetType, RuleSimStatus


class RuleSetRefSchema(BaseModel):
    """RuleSet reference schema"""
    id: str
    type: str  # RuleSimTargetType value
    description: Optional[str] = None
    doctrine_section_ids: Optional[List[str]] = None
    alert_config_path: Optional[str] = None


class RuleSimRunRequest(BaseModel):
    """Request to run a rule simulation experiment"""
    target_ruleset: RuleSetRefSchema
    baseline_version_id: Optional[str] = None
    variant_version_id: Optional[str] = None
    start_date: date
    end_date: date
    universe: Optional[List[str]] = None  # If None, use default Path A universe
    path_a_config_name: str = "path_a_tw_basic_v1"
    note: Optional[str] = None


class RuleSimStatusSummarySchema(BaseModel):
    """Status summary schema"""
    status: str  # RuleSimStatus value
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None


class RuleSimRunResponse(BaseModel):
    """Response for running an experiment"""
    experiment_id: str
    status: RuleSimStatusSummarySchema


class RuleSimArmMetricsSchema(BaseModel):
    """Arm metrics schema"""
    arm: str
    sharpe: float
    max_drawdown: float
    total_return: float
    win_rate: float
    turnover: float
    var_95: Optional[float] = None
    alert_trigger_count: Optional[int] = None
    doctrine_violation_count: Optional[int] = None


class RuleSimDeltaMetricsSchema(BaseModel):
    """Delta metrics schema"""
    sharpe_delta: float
    max_drawdown_delta: float
    total_return_delta: float
    win_rate_delta: float
    turnover_delta: float
    alert_trigger_delta: Optional[int] = None
    doctrine_violation_delta: Optional[int] = None


class RuleSimReportSummarySchema(BaseModel):
    """Summary schema for report list"""
    experiment_id: str
    created_at: datetime
    target_ruleset: RuleSetRefSchema
    status: str
    baseline_sharpe: float
    variant_sharpe: float
    sharpe_delta: float
    recommendation: str


class RuleSimReportSchema(BaseModel):
    """Full report schema"""
    experiment_id: str
    config: dict  # RuleSimExperimentConfig as dict
    status: RuleSimStatusSummarySchema
    baseline_metrics: RuleSimArmMetricsSchema
    variant_metrics: RuleSimArmMetricsSchema
    deltas: RuleSimDeltaMetricsSchema
    key_findings: List[str]
    recommendation: str
    created_at: datetime

