"""
Smoke Test for EXTREME MODE

This test verifies that EXTREME MODE can run a complete experiment
without errors, using mock data and extreme modules.

Reference: J-GOD Step 11 - EXTREME MODE Switch & Wiring
"""

from __future__ import annotations

import pytest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from jgod.experiments import ExperimentOrchestrator, ExperimentConfig
from scripts.run_jgod_experiment import build_orchestrator


class TestExperimentExtremeSmoke:
    """Smoke Test for Extreme Mode."""
    
    def test_extreme_mode_smoke(self):
        """
        Smoke Test for Extreme Mode.
        
        Verifies that:
        - Experiment can run with mode="extreme" and data_source="mock"
        - Result is not None
        - Result contains required summary metrics
        - No exceptions are raised
        """
        # Build orchestrator with EXTREME mode
        orchestrator = build_orchestrator(
            data_source="mock",
            mode="extreme"
        )
        
        # Create experiment config
        config = ExperimentConfig(
            name="extreme_smoke_test",
            start_date="2024-01-01",
            end_date="2024-01-10",
            rebalance_frequency="D",
            universe=["2330.TW", "2317.TW"],
            data_source="mock",
            notes="Smoke test for EXTREME MODE",
        )
        
        # Run experiment
        result = orchestrator.run_experiment(config)
        
        # Assertions
        assert result is not None, "Experiment result should not be None"
        assert result.config is not None, "Experiment config should be present"
        assert result.report is not None, "Experiment report should be present"
        
        # Check summary contains required metrics
        summary = result.report.summary
        assert summary is not None, "Report summary should not be None"
        
        # Check that summary contains at least total_return and sharpe
        assert "total_return" in summary or hasattr(summary, "total_return"), \
            "Summary should contain total_return"
        assert "sharpe" in summary or hasattr(summary, "sharpe"), \
            "Summary should contain sharpe"
        
        # Check artifacts
        assert result.artifacts is not None, "Artifacts should be present"
        assert result.artifacts.path_a_result is not None, \
            "Path A result should be present"
        assert result.artifacts.performance_result is not None, \
            "Performance result should be present"
        
        # Verify no exceptions were raised (if we got here, test passed)

