"""Tests for Rule Simulation CLI script"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))


class TestRuleSimCLI:
    """Tests for run_rule_sim_experiment_v1.py CLI"""
    
    @patch("scripts.run_rule_sim_experiment_v1.RuleSimEngineV1")
    @patch("scripts.run_rule_sim_experiment_v1.RuleSimStorageV1")
    def test_basic_execution(self, mock_storage_class, mock_engine_class, tmp_path):
        """Test basic CLI execution (smoke test)"""
        # Setup mocks
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage
        
        mock_engine = MagicMock()
        mock_report = MagicMock()
        mock_report.experiment_id = "test-cli-001"
        mock_report.status.status.value = "SUCCESS"
        mock_report.recommendation = "APPROVE"
        mock_report.baseline_metrics.sharpe = 1.0
        mock_report.variant_metrics.sharpe = 1.1
        mock_report.deltas.sharpe_delta = 0.1
        mock_report.key_findings = ["Test finding"]
        mock_engine.run_experiment.return_value = mock_report
        mock_engine_class.return_value = mock_engine
        
        # Mock sys.argv
        test_args = [
            "run_rule_sim_experiment_v1.py",
            "--target-type", "doctrine_section",
            "--section-id", "B01#S12-R03",
            "--variant-version", "proposal-v1",
            "--start-date", "2024-01-01",
            "--end-date", "2024-03-31",
            "--universe", "2330,2317",
        ]
        
        with patch.object(sys, "argv", test_args):
            # Import and run main (avoid subprocess for easier testing)
            try:
                from scripts.run_rule_sim_experiment_v1 import main
                # Should complete without error
                main()
                # Verify engine was called
                mock_engine.run_experiment.assert_called_once()
            except SystemExit as e:
                # If script calls sys.exit(0), that's fine
                assert e.code == 0
    
    def test_missing_required_arguments(self):
        """Test CLI with missing required arguments"""
        # Test missing --section-id
        test_args = [
            "run_rule_sim_experiment_v1.py",
            "--target-type", "doctrine_section",
            "--variant-version", "proposal-v1",
            "--start-date", "2024-01-01",
            "--end-date", "2024-03-31",
        ]
        
        with patch.object(sys, "argv", test_args):
            from scripts.run_rule_sim_experiment_v1 import main
            # Should raise SystemExit or print error
            with pytest.raises((SystemExit, ValueError, KeyError)):
                main()
    
    def test_invalid_date_format(self):
        """Test CLI with invalid date format"""
        test_args = [
            "run_rule_sim_experiment_v1.py",
            "--target-type", "doctrine_section",
            "--section-id", "B01#S12",
            "--variant-version", "proposal-v1",
            "--start-date", "invalid-date",
            "--end-date", "2024-03-31",
        ]
        
        with patch.object(sys, "argv", test_args):
            from scripts.run_rule_sim_experiment_v1 import main
            # Should raise ValueError for invalid date
            with pytest.raises((SystemExit, ValueError)):
                main()
    
    @patch("scripts.run_rule_sim_experiment_v1.RuleSimEngineV1")
    @patch("scripts.run_rule_sim_experiment_v1.RuleSimStorageV1")
    def test_cli_with_all_arguments(self, mock_storage_class, mock_engine_class):
        """Test CLI with all arguments provided"""
        # Setup mocks
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage
        
        mock_engine = MagicMock()
        mock_report = MagicMock()
        mock_report.experiment_id = "test-full-001"
        mock_report.status.status.value = "SUCCESS"
        mock_report.recommendation = "CAUTION"
        mock_engine.run_experiment.return_value = mock_report
        mock_engine_class.return_value = mock_engine
        
        test_args = [
            "run_rule_sim_experiment_v1.py",
            "--target-type", "doctrine_section",
            "--section-id", "B01#S12-R03",
            "--baseline-version", "v1",
            "--variant-version", "proposal-v1",
            "--start-date", "2024-01-01",
            "--end-date", "2024-06-30",
            "--universe", "2330,2317,3008",
            "--path-a-config-name", "path_a_tw_basic_v1",
            "--note", "Full test experiment",
        ]
        
        with patch.object(sys, "argv", test_args):
            from scripts.run_rule_sim_experiment_v1 import main
            try:
                main()
                # Verify experiment config was created with all fields
                call_args = mock_engine.run_experiment.call_args
                config = call_args[0][0]
                assert config.experiment_id is not None
                assert config.baseline_version_id == "v1"
                assert config.variant_version_id == "proposal-v1"
                assert len(config.universe) == 3
                assert config.note == "Full test experiment"
            except SystemExit as e:
                assert e.code == 0

