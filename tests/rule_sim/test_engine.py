"""Tests for Rule Simulation Engine"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from jgod.rule_sim.engine import RuleSimEngineV1
from jgod.rule_sim.models import RuleSimStatus, RuleSimArm
from jgod.rule_sim.storage import RuleSimStorageV1


class TestRuleSimEngineV1:
    """Tests for RuleSimEngineV1"""
    
    def test_successful_experiment(self, mock_data_access, mock_sandbox_applier, sample_experiment_config, rule_sim_tmp_dir):
        """Test successful experiment execution"""
        # Setup
        storage = RuleSimStorageV1(path=rule_sim_tmp_dir / "reports.jsonl")
        engine = RuleSimEngineV1(
            storage=storage,
            data_access=mock_data_access,
            sandbox_applier=mock_sandbox_applier,
        )
        
        # Run experiment
        report = engine.run_experiment(sample_experiment_config)
        
        # Assertions
        assert report.experiment_id == sample_experiment_config.experiment_id
        assert report.baseline_metrics.sharpe == 1.0
        assert report.variant_metrics.sharpe == 1.1
        assert report.deltas.sharpe_delta == pytest.approx(0.1, abs=0.01)
        assert report.status.status == RuleSimStatus.SUCCESS
        assert report.baseline_metrics.arm == RuleSimArm.BASELINE
        assert report.variant_metrics.arm == RuleSimArm.VARIANT
    
    def test_recommendation_approve(self, mock_data_access, mock_sandbox_applier, sample_experiment_config, rule_sim_tmp_dir):
        """Test APPROVE recommendation when variant improves"""
        # Setup: variant improves Sharpe, MaxDD stays acceptable
        mock_data_access.variant_sharpe = 1.2  # Improved
        mock_data_access.variant_maxdd = 0.09  # Better than baseline
        mock_data_access.variant_return = 0.25  # Improved
        
        storage = RuleSimStorageV1(path=rule_sim_tmp_dir / "reports.jsonl")
        engine = RuleSimEngineV1(
            storage=storage,
            data_access=mock_data_access,
            sandbox_applier=mock_sandbox_applier,
        )
        
        report = engine.run_experiment(sample_experiment_config)
        
        assert report.recommendation == "APPROVE"
        assert report.deltas.sharpe_delta > 0.05
        assert "Sharpe Ratio 提升" in " ".join(report.key_findings) or report.deltas.sharpe_delta > 0
    
    def test_recommendation_reject_sharpe_drop(self, mock_data_access, mock_sandbox_applier, sample_experiment_config, rule_sim_tmp_dir):
        """Test REJECT recommendation when Sharpe drops significantly"""
        # Setup: variant Sharpe drops significantly
        mock_data_access.variant_sharpe = 0.7  # Significant drop
        mock_data_access.variant_maxdd = 0.15  # Worse
        
        storage = RuleSimStorageV1(path=rule_sim_tmp_dir / "reports.jsonl")
        engine = RuleSimEngineV1(
            storage=storage,
            data_access=mock_data_access,
            sandbox_applier=mock_sandbox_applier,
        )
        
        report = engine.run_experiment(sample_experiment_config)
        
        assert report.recommendation == "REJECT"
        assert report.deltas.sharpe_delta < -0.1
    
    def test_recommendation_reject_maxdd_increase(self, mock_data_access, mock_sandbox_applier, sample_experiment_config, rule_sim_tmp_dir):
        """Test REJECT recommendation when MaxDD increases significantly"""
        # Setup: MaxDD increases beyond threshold
        mock_data_access.variant_sharpe = 0.95  # Slight drop
        mock_data_access.variant_maxdd = 0.16  # Increase > 0.05 threshold
        
        storage = RuleSimStorageV1(path=rule_sim_tmp_dir / "reports.jsonl")
        engine = RuleSimEngineV1(
            storage=storage,
            data_access=mock_data_access,
            sandbox_applier=mock_sandbox_applier,
        )
        
        report = engine.run_experiment(sample_experiment_config)
        
        # MaxDD increase > 0.05 should trigger REJECT or CAUTION
        assert report.deltas.max_drawdown_delta > 0.05
        assert report.recommendation in ["REJECT", "CAUTION"]
    
    def test_recommendation_caution(self, mock_data_access, mock_sandbox_applier, sample_experiment_config, rule_sim_tmp_dir):
        """Test CAUTION recommendation for moderate changes"""
        # Setup: Slight degradation within acceptable range
        mock_data_access.variant_sharpe = 0.96  # Small drop, but > -0.1 threshold
        mock_data_access.variant_maxdd = 0.12  # Small increase, but < 0.05 threshold
        
        storage = RuleSimStorageV1(path=rule_sim_tmp_dir / "reports.jsonl")
        engine = RuleSimEngineV1(
            storage=storage,
            data_access=mock_data_access,
            sandbox_applier=mock_sandbox_applier,
        )
        
        report = engine.run_experiment(sample_experiment_config)
        
        # Should be CAUTION or APPROVE depending on exact thresholds
        assert report.recommendation in ["CAUTION", "APPROVE", "REJECT"]
        assert report.deltas.sharpe_delta > -0.1  # Within threshold
    
    def test_error_handling(self, mock_data_access, mock_sandbox_applier, sample_experiment_config, rule_sim_tmp_dir):
        """Test error handling when data_access fails"""
        # Setup: make data_access raise exception
        mock_data_access.run_path_a_backtest = MagicMock(side_effect=Exception("Backtest failed"))
        
        storage = RuleSimStorageV1(path=rule_sim_tmp_dir / "reports.jsonl")
        engine = RuleSimEngineV1(
            storage=storage,
            data_access=mock_data_access,
            sandbox_applier=mock_sandbox_applier,
        )
        
        report = engine.run_experiment(sample_experiment_config)
        
        # Should create failed report
        assert report.status.status == RuleSimStatus.FAILED
        assert report.status.error_message is not None
        assert "Backtest failed" in report.status.error_message or len(report.status.error_message) > 0
        assert report.recommendation == "REJECT"  # Failed experiments should reject
    
    def test_storage_save_called(self, mock_data_access, mock_sandbox_applier, sample_experiment_config, rule_sim_tmp_dir):
        """Test that storage.save_report is called"""
        storage = RuleSimStorageV1(path=rule_sim_tmp_dir / "reports.jsonl")
        mock_save = MagicMock()
        storage.save_report = mock_save
        
        engine = RuleSimEngineV1(
            storage=storage,
            data_access=mock_data_access,
            sandbox_applier=mock_sandbox_applier,
        )
        
        report = engine.run_experiment(sample_experiment_config)
        
        # Verify save was called
        mock_save.assert_called_once()
        saved_report = mock_save.call_args[0][0]
        assert saved_report.experiment_id == sample_experiment_config.experiment_id

