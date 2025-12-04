"""
Smoke Test for Path C Engine

This test verifies that Path C Engine can be initialized and run basic
operations without errors.

Reference: J-GOD Path C Engine
"""

from __future__ import annotations

import pytest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from jgod.path_c.path_c_engine import PathCEngine
from jgod.path_c.path_c_types import (
    PathCScenarioConfig,
    PathCScenarioResult,
    PathCExperimentConfig,
    PathCRunSummary,
)


class TestPathCEngineSmoke:
    """Smoke Test for Path C Engine"""
    
    def test_path_c_engine_initialization(self):
        """Test that PathCEngine can be initialized"""
        engine = PathCEngine()
        
        assert engine is not None
        assert engine.path_b_engine is None  # Default is None
    
    def test_path_c_scenario_config_creation(self):
        """Test that PathCScenarioConfig can be created"""
        scenario = PathCScenarioConfig(
            name="test_scenario",
            description="Test scenario",
            start_date="2023-01-01",
            end_date="2023-12-31",
            rebalance_frequency="M",
            universe=["2330.TW", "2317.TW"],
            walkforward_window="6m",
            walkforward_step="1m",
        )
        
        assert scenario.name == "test_scenario"
        assert scenario.start_date == "2023-01-01"
        assert len(scenario.universe) == 2
    
    def test_path_c_experiment_config_creation(self):
        """Test that PathCExperimentConfig can be created"""
        scenario = PathCScenarioConfig(
            name="test_scenario",
            description="Test scenario",
            start_date="2023-01-01",
            end_date="2023-12-31",
            rebalance_frequency="M",
            universe=["2330.TW"],
            walkforward_window="6m",
            walkforward_step="1m",
        )
        
        experiment_config = PathCExperimentConfig(
            name="test_experiment",
            scenarios=[scenario],
        )
        
        assert experiment_config.name == "test_experiment"
        assert len(experiment_config.scenarios) == 1
    
    def test_path_c_engine_run_smoke(self):
        """
        Test that PathCEngine.run_experiment() can be called without errors.
        Minimal test with mock data.
        """
        engine = PathCEngine()
        
        # 建立最小可用 scenario
        scenario = PathCScenarioConfig(
            name="smoke_test_scenario",
            description="Smoke test scenario",
            start_date="2024-01-01",
            end_date="2024-01-20",  # 很短的日期範圍以加快測試
            rebalance_frequency="D",
            universe=["2330.TW", "2317.TW"],
            walkforward_window="1m",  # 很小的 window
            walkforward_step="1m",
            data_source="mock",
            mode="basic",
        )
        
        experiment_config = PathCExperimentConfig(
            name="smoke_test_experiment",
            scenarios=[scenario],
            output_dir="output/path_c",
        )
        
        # Run should not raise exception
        summary = engine.run_experiment(experiment_config)
        
        # Verify result structure
        assert summary is not None, "Summary should not be None"
        assert isinstance(summary, PathCRunSummary), "Summary should be PathCRunSummary"
        assert summary.experiment_name == "smoke_test_experiment"
        assert isinstance(summary.scenarios, list), "Scenarios should be a list"
        assert len(summary.scenarios) >= 1, "Should have at least 1 scenario result"
        assert isinstance(summary.ranking_table, list), "Ranking table should be a list"
        assert summary.total_scenarios >= 1, "Should have at least 1 total scenario"
    
    def test_path_c_ranking_table_structure(self):
        """Test ranking table structure"""
        engine = PathCEngine()
        
        # 建立 2 個 scenarios
        scenarios = [
            PathCScenarioConfig(
                name="scenario_1",
                description="Scenario 1",
                start_date="2024-01-01",
                end_date="2024-01-15",
                rebalance_frequency="D",
                universe=["2330.TW"],
                walkforward_window="1m",
                walkforward_step="1m",
                data_source="mock",
                mode="basic",
            ),
            PathCScenarioConfig(
                name="scenario_2",
                description="Scenario 2",
                start_date="2024-01-01",
                end_date="2024-01-15",
                rebalance_frequency="D",
                universe=["2317.TW"],
                walkforward_window="1m",
                walkforward_step="1m",
                data_source="mock",
                mode="basic",
            ),
        ]
        
        experiment_config = PathCExperimentConfig(
            name="ranking_test_experiment",
            scenarios=scenarios,
            output_dir="output/path_c",
        )
        
        summary = engine.run_experiment(experiment_config)
        
        # 檢查 ranking_table
        assert len(summary.ranking_table) >= 2, "Should have ranking for at least 2 scenarios"
        
        # 檢查排名表結構
        if summary.ranking_table:
            first_row = summary.ranking_table[0]
            assert "rank" in first_row, "Ranking table should have 'rank' column"
            assert "scenario_name" in first_row, "Ranking table should have 'scenario_name' column"
            assert "sharpe" in first_row, "Ranking table should have 'sharpe' column"

