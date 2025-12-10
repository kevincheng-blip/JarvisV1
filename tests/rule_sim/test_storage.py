"""Tests for Rule Simulation Storage"""

import pytest
import json
from pathlib import Path
from datetime import datetime, date

from jgod.rule_sim.storage import RuleSimStorageV1
from jgod.rule_sim.models import (
    RuleSimReport,
    RuleSimExperimentConfig,
    RuleSimStatusSummary,
    RuleSimStatus,
    RuleSimArmMetrics,
    RuleSimDeltaMetrics,
    RuleSimArm,
    RuleSetRef,
    RuleSimTargetType,
)


@pytest.fixture
def storage_path(rule_sim_tmp_dir) -> Path:
    """Storage JSONL file path"""
    return rule_sim_tmp_dir / "reports.jsonl"


@pytest.fixture
def storage(storage_path) -> RuleSimStorageV1:
    """Storage instance with custom path"""
    return RuleSimStorageV1(path=storage_path)


@pytest.fixture
def sample_report(storage_path) -> RuleSimReport:
    """Sample report for testing"""
    config = RuleSimExperimentConfig(
        experiment_id="exp-001",
        created_at=datetime(2024, 1, 1, 10, 0, 0),
        target_ruleset=RuleSetRef(
            id="B01#S12",
            type=RuleSimTargetType.DOCTRINE_SECTION,
        ),
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        universe=["2330", "2317"],
    )
    
    return RuleSimReport(
        experiment_id="exp-001",
        config=config,
        status=RuleSimStatusSummary(
            status=RuleSimStatus.SUCCESS,
            started_at=datetime(2024, 1, 1, 10, 0, 0),
            finished_at=datetime(2024, 1, 1, 10, 5, 0),
        ),
        baseline_metrics=RuleSimArmMetrics(
            arm=RuleSimArm.BASELINE,
            sharpe=1.0,
            max_drawdown=0.1,
            total_return=0.2,
            win_rate=0.55,
        ),
        variant_metrics=RuleSimArmMetrics(
            arm=RuleSimArm.VARIANT,
            sharpe=1.1,
            max_drawdown=0.11,
            total_return=0.23,
            win_rate=0.56,
        ),
        deltas=RuleSimDeltaMetrics(
            sharpe_delta=0.1,
            max_drawdown_delta=0.01,
            total_return_delta=0.03,
            win_rate_delta=0.01,
        ),
        recommendation="APPROVE",
        created_at=datetime(2024, 1, 1, 10, 5, 0),
    )


class TestRuleSimStorageV1:
    """Tests for RuleSimStorageV1"""
    
    def test_save_and_load_recent(self, storage, sample_report):
        """Test saving and loading reports"""
        # Save first report
        storage.save_report(sample_report)
        
        # Create and save second report
        report2 = RuleSimReport(
            experiment_id="exp-002",
            config=RuleSimExperimentConfig(
                experiment_id="exp-002",
                created_at=datetime(2024, 1, 2, 10, 0, 0),
                target_ruleset=RuleSetRef(
                    id="B02#S05",
                    type=RuleSimTargetType.DOCTRINE_SECTION,
                ),
                start_date=date(2024, 1, 1),
                end_date=date(2024, 3, 31),
            ),
            status=RuleSimStatusSummary(status=RuleSimStatus.SUCCESS),
            baseline_metrics=RuleSimArmMetrics(arm=RuleSimArm.BASELINE),
            variant_metrics=RuleSimArmMetrics(arm=RuleSimArm.VARIANT),
            deltas=RuleSimDeltaMetrics(),
            created_at=datetime(2024, 1, 2, 10, 5, 0),
        )
        storage.save_report(report2)
        
        # Load recent reports
        reports = storage.load_recent(limit=10)
        
        assert len(reports) == 2
        # Should be sorted by created_at descending (newest first)
        assert reports[0].experiment_id == "exp-002"
        assert reports[1].experiment_id == "exp-001"
    
    def test_load_recent_with_limit(self, storage, sample_report):
        """Test loading with limit"""
        # Save multiple reports
        for i in range(5):
            report = RuleSimReport(
                experiment_id=f"exp-{i:03d}",
                config=RuleSimExperimentConfig(
                    experiment_id=f"exp-{i:03d}",
                    created_at=datetime(2024, 1, i+1, 10, 0, 0),
                    target_ruleset=RuleSetRef(
                        id=f"B{i:02d}#S01",
                        type=RuleSimTargetType.DOCTRINE_SECTION,
                    ),
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 3, 31),
                ),
                status=RuleSimStatusSummary(status=RuleSimStatus.SUCCESS),
                baseline_metrics=RuleSimArmMetrics(arm=RuleSimArm.BASELINE),
                variant_metrics=RuleSimArmMetrics(arm=RuleSimArm.VARIANT),
                deltas=RuleSimDeltaMetrics(),
                created_at=datetime(2024, 1, i+1, 10, 5, 0),
            )
            storage.save_report(report)
        
        # Load with limit
        reports = storage.load_recent(limit=3)
        assert len(reports) == 3
    
    def test_load_by_id_found(self, storage, sample_report):
        """Test loading by ID when report exists"""
        storage.save_report(sample_report)
        
        loaded = storage.load_by_id("exp-001")
        assert loaded is not None
        assert loaded.experiment_id == "exp-001"
        assert loaded.recommendation == "APPROVE"
    
    def test_load_by_id_not_found(self, storage):
        """Test loading by ID when report doesn't exist"""
        loaded = storage.load_by_id("nonexistent")
        assert loaded is None
    
    def test_load_recent_empty_file(self, storage):
        """Test loading from empty file"""
        reports = storage.load_recent(limit=10)
        assert len(reports) == 0
    
    def test_json_error_handling(self, storage, storage_path, sample_report):
        """Test handling invalid JSON lines"""
        # Save a valid report first
        storage.save_report(sample_report)
        
        # Append invalid JSON line
        with open(storage_path, "a", encoding="utf-8") as f:
            f.write("invalid json line\n")
            f.write("{ invalid json }\n")
        
        # Should not crash, should skip invalid lines
        reports = storage.load_recent(limit=10)
        # Should still have the valid report
        assert len(reports) >= 1
        assert any(r.experiment_id == "exp-001" for r in reports)

