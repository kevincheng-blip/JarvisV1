"""Pytest fixtures for Rule Simulation Engine tests"""

import pytest
from pathlib import Path
from datetime import date, datetime
from typing import List
from unittest.mock import MagicMock

from jgod.rule_sim.models import (
    RuleSetRef,
    RuleSimExperimentConfig,
    RuleSimTargetType,
)


@pytest.fixture
def rule_sim_tmp_dir(tmp_path) -> Path:
    """Temporary directory for rule simulation tests"""
    rule_sim_dir = tmp_path / "rule_sim"
    rule_sim_dir.mkdir(parents=True, exist_ok=True)
    return rule_sim_dir


@pytest.fixture
def sample_universe() -> List[str]:
    """Sample stock universe for testing"""
    return ["2330", "2317", "3008", "3034"]


@pytest.fixture
def sample_ruleset_ref() -> RuleSetRef:
    """Sample ruleset reference"""
    return RuleSetRef(
        id="B01#S12-R03",
        type=RuleSimTargetType.DOCTRINE_SECTION,
        description="測試用條文",
    )


@pytest.fixture
def sample_experiment_config(sample_ruleset_ref, sample_universe) -> RuleSimExperimentConfig:
    """Sample experiment configuration"""
    return RuleSimExperimentConfig(
        experiment_id="test-exp-001",
        created_at=datetime(2024, 1, 1, 10, 0, 0),
        created_by="test",
        target_ruleset=sample_ruleset_ref,
        baseline_version_id="v1",
        variant_version_id="proposal_2024_01_10",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        universe=sample_universe,
        path_a_config_name="path_a_tw_basic_v1",
        note="Test experiment",
    )


@pytest.fixture
def mock_data_access():
    """Mock RuleSimDataAccess"""
    class FakeDataAccess:
        def __init__(self):
            self.baseline_sharpe = 1.0
            self.baseline_maxdd = 0.1
            self.baseline_return = 0.2
            self.baseline_alerts = 10
            
            self.variant_sharpe = 1.1
            self.variant_maxdd = 0.11
            self.variant_return = 0.23
            self.variant_alerts = 12
        
        def run_path_a_backtest(self, start_date, end_date, universe, path_a_config_name, sandbox_dir=None):
            """Return mock backtest result"""
            from jgod.path_a.path_a_engine_v1 import BacktestResult, PerformanceMetrics
            
            # Determine if baseline or variant based on sandbox_dir
            if sandbox_dir is None:
                # Baseline
                sharpe = self.baseline_sharpe
                maxdd = self.baseline_maxdd
                total_return = self.baseline_return
            else:
                # Variant
                sharpe = self.variant_sharpe
                maxdd = self.variant_maxdd
                total_return = self.variant_return
            
            metrics = PerformanceMetrics(
                annualized_return=total_return * 2,  # Approximate annualized
                annualized_volatility=0.15,
                sharpe_ratio=sharpe,
                max_drawdown=maxdd,
                win_rate=0.55,
                total_return=total_return,
                total_commission=1000.0,
                num_long_trades=50,
                num_short_trades=30,
            )
            
            return BacktestResult(
                start_date=start_date,
                end_date=end_date,
                initial_capital=1000000.0,
                final_capital=1000000.0 * (1 + total_return),
                metrics=metrics,
                trades=[],
                equity_curve=[],
            )
        
        def collect_alert_stats(self, start_date, end_date, universe, sandbox_dir=None):
            """Return mock alert statistics"""
            if sandbox_dir is None:
                return {
                    "alert_trigger_count": self.baseline_alerts,
                    "doctrine_violation_count": 3,
                }
            else:
                return {
                    "alert_trigger_count": self.variant_alerts,
                    "doctrine_violation_count": 4,
                }
    
    return FakeDataAccess()


@pytest.fixture
def mock_sandbox_applier(rule_sim_tmp_dir):
    """Mock RuleSandboxApplier"""
    class FakeSandboxApplier:
        def __init__(self):
            self.sandbox_base = rule_sim_tmp_dir / "sandbox"
            self.sandbox_base.mkdir(parents=True, exist_ok=True)
        
        def create_sandbox(self, experiment_config):
            """Create sandbox directory"""
            sandbox_dir = self.sandbox_base / experiment_config.experiment_id
            sandbox_dir.mkdir(parents=True, exist_ok=True)
            return sandbox_dir
    
    return FakeSandboxApplier()


@pytest.fixture
def mock_doctrine_service():
    """Mock DoctrineServiceV2"""
    class FakeDoctrineService:
        def get_version_content(self, section_id, version_id):
            """Return mock content"""
            return f"# Mock Doctrine Section {section_id}\n\nVersion: {version_id}\n\nContent here..."
    
    return FakeDoctrineService()

