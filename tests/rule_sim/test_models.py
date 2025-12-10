"""Tests for Rule Simulation Engine Data Models"""

import pytest
from datetime import datetime, date

from jgod.rule_sim.models import (
    RuleSetRef,
    RuleSimExperimentConfig,
    RuleSimArmMetrics,
    RuleSimDeltaMetrics,
    RuleSimStatusSummary,
    RuleSimReport,
    RuleSimStatus,
    RuleSimArm,
    RuleSimTargetType,
)


class TestRuleSetRef:
    """Tests for RuleSetRef"""
    
    def test_create_minimal(self):
        """Test creating minimal RuleSetRef"""
        ref = RuleSetRef(
            id="B01#S12",
            type=RuleSimTargetType.DOCTRINE_SECTION,
        )
        assert ref.id == "B01#S12"
        assert ref.type == RuleSimTargetType.DOCTRINE_SECTION
        assert ref.description is None
    
    def test_create_with_optional_fields(self):
        """Test creating RuleSetRef with all fields"""
        ref = RuleSetRef(
            id="B01#S12-R03",
            type=RuleSimTargetType.DOCTRINE_SECTION,
            description="Test section",
            doctrine_section_ids=["B01#S12"],
            alert_config_path="config/alerts.yaml",
        )
        assert ref.description == "Test section"
        assert ref.doctrine_section_ids == ["B01#S12"]
        assert ref.alert_config_path == "config/alerts.yaml"


class TestRuleSimExperimentConfig:
    """Tests for RuleSimExperimentConfig"""
    
    def test_create_config(self, sample_ruleset_ref, sample_universe):
        """Test creating experiment config"""
        config = RuleSimExperimentConfig(
            experiment_id="test-001",
            target_ruleset=sample_ruleset_ref,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            universe=sample_universe,
        )
        assert config.experiment_id == "test-001"
        assert config.target_ruleset.id == "B01#S12-R03"
        assert config.start_date == date(2024, 1, 1)
        assert config.universe == sample_universe
        assert config.path_a_config_name == "path_a_tw_basic_v1"  # Default


class TestRuleSimArmMetrics:
    """Tests for RuleSimArmMetrics"""
    
    def test_create_baseline_metrics(self):
        """Test creating baseline metrics"""
        metrics = RuleSimArmMetrics(
            arm=RuleSimArm.BASELINE,
            sharpe=1.0,
            max_drawdown=0.1,
            total_return=0.2,
            win_rate=0.55,
        )
        assert metrics.arm == RuleSimArm.BASELINE
        assert metrics.sharpe == 1.0
        assert metrics.max_drawdown == 0.1
        assert metrics.turnover == 0.0  # Default


class TestRuleSimDeltaMetrics:
    """Tests for RuleSimDeltaMetrics"""
    
    def test_create_delta_metrics(self):
        """Test creating delta metrics"""
        deltas = RuleSimDeltaMetrics(
            sharpe_delta=0.1,
            max_drawdown_delta=0.01,
            total_return_delta=0.03,
        )
        assert deltas.sharpe_delta == 0.1
        assert deltas.max_drawdown_delta == 0.01
        assert deltas.total_return_delta == 0.03


class TestRuleSimReport:
    """Tests for RuleSimReport"""
    
    def test_create_minimal_report(self, sample_experiment_config):
        """Test creating minimal RuleSimReport"""
        from jgod.rule_sim.models import RuleSimStatusSummary, RuleSimArmMetrics, RuleSimDeltaMetrics
        
        report = RuleSimReport(
            experiment_id="test-001",
            config=sample_experiment_config,
            status=RuleSimStatusSummary(status=RuleSimStatus.SUCCESS),
            baseline_metrics=RuleSimArmMetrics(arm=RuleSimArm.BASELINE),
            variant_metrics=RuleSimArmMetrics(arm=RuleSimArm.VARIANT),
            deltas=RuleSimDeltaMetrics(),
        )
        
        assert report.experiment_id == "test-001"
        assert report.config.experiment_id == "test-001"
        assert report.status.status == RuleSimStatus.SUCCESS
        assert report.baseline_metrics.arm == RuleSimArm.BASELINE
        assert report.variant_metrics.arm == RuleSimArm.VARIANT
        assert report.recommendation == "CAUTION"  # Default
    
    def test_report_has_dict_method(self, sample_experiment_config):
        """Test that report can be converted to dict (if using dataclass)"""
        from jgod.rule_sim.models import RuleSimStatusSummary, RuleSimArmMetrics, RuleSimDeltaMetrics
        
        report = RuleSimReport(
            experiment_id="test-001",
            config=sample_experiment_config,
            status=RuleSimStatusSummary(status=RuleSimStatus.SUCCESS),
            baseline_metrics=RuleSimArmMetrics(arm=RuleSimArm.BASELINE, sharpe=1.0),
            variant_metrics=RuleSimArmMetrics(arm=RuleSimArm.VARIANT, sharpe=1.1),
            deltas=RuleSimDeltaMetrics(sharpe_delta=0.1),
            recommendation="APPROVE",
        )
        
        # Check that we can access all fields
        assert report.experiment_id == "test-001"
        assert report.config.experiment_id == "test-001"
        assert report.baseline_metrics.sharpe == 1.0
        assert report.variant_metrics.sharpe == 1.1
        assert report.deltas.sharpe_delta == 0.1
        assert report.recommendation == "APPROVE"
        assert isinstance(report.key_findings, list)

