"""Rule Simulation Engine Data Models

Defines data structures for rule simulation experiments and reports.
"""

from datetime import datetime, date
from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum


class RuleSimTargetType(str, Enum):
    """Target type for rule simulation"""
    DOCTRINE_SECTION = "doctrine_section"
    DOCTRINE_FILE = "doctrine_file"
    ALERT_RULES_YAML = "alert_rules_yaml"


class RuleSimStatus(str, Enum):
    """Experiment status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class RuleSimArm(str, Enum):
    """Test arm"""
    BASELINE = "BASELINE"
    VARIANT = "VARIANT"


@dataclass
class RuleSetRef:
    """Reference to a ruleset"""
    id: str  # e.g. "B01#S12-R03" or "alert_rules_v1"
    type: RuleSimTargetType
    description: Optional[str] = None
    doctrine_section_ids: Optional[List[str]] = None  # For partial Doctrine testing
    alert_config_path: Optional[str] = None  # Original alert YAML path


@dataclass
class RuleSimExperimentConfig:
    """Configuration for a rule simulation experiment"""
    experiment_id: str  # UUID
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "user"  # "user" or "DMC"
    target_ruleset: Optional[RuleSetRef] = None
    baseline_version_id: Optional[str] = None  # Doctrine baseline / alert baseline
    variant_version_id: Optional[str] = None  # Draft or proposal version
    start_date: date = field(default_factory=date.today)
    end_date: date = field(default_factory=date.today)
    universe: List[str] = field(default_factory=list)  # Test stock universe
    path_a_config_name: str = "path_a_tw_basic_v1"
    note: Optional[str] = None


@dataclass
class RuleSimArmMetrics:
    """Performance metrics for a test arm"""
    arm: RuleSimArm
    sharpe: float = 0.0
    max_drawdown: float = 0.0
    total_return: float = 0.0
    win_rate: float = 0.0
    turnover: float = 0.0
    var_95: Optional[float] = None
    alert_trigger_count: Optional[int] = None  # New rule trigger count
    doctrine_violation_count: Optional[int] = None


@dataclass
class RuleSimDeltaMetrics:
    """Delta metrics between baseline and variant"""
    sharpe_delta: float = 0.0
    max_drawdown_delta: float = 0.0
    total_return_delta: float = 0.0
    win_rate_delta: float = 0.0
    turnover_delta: float = 0.0
    alert_trigger_delta: Optional[int] = None
    doctrine_violation_delta: Optional[int] = None


@dataclass
class RuleSimStatusSummary:
    """Status summary for an experiment"""
    status: RuleSimStatus = RuleSimStatus.PENDING
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class RuleSimReport:
    """Complete rule simulation report"""
    experiment_id: str
    config: RuleSimExperimentConfig
    status: RuleSimStatusSummary
    baseline_metrics: RuleSimArmMetrics
    variant_metrics: RuleSimArmMetrics
    deltas: RuleSimDeltaMetrics
    key_findings: List[str] = field(default_factory=list)
    recommendation: str = "CAUTION"  # "APPROVE", "CAUTION", "REJECT"
    created_at: datetime = field(default_factory=datetime.now)

