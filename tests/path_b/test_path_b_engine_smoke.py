"""
Smoke Test for Path B Engine

This test verifies that Path B Engine can be initialized and run basic
operations without errors.

Reference: J-GOD Path B Engine Step B1
"""

from __future__ import annotations

import pytest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from jgod.path_b.path_b_engine import (
    PathBEngine,
    PathBConfig,
    PathBRunResult,
    PathBWindowResult,
)


class TestPathBEngineSmoke:
    """Smoke Test for Path B Engine"""
    
    def test_path_b_engine_initialization(self):
        """Test that PathBEngine can be initialized"""
        engine = PathBEngine()
        
        assert engine is not None
        assert engine.data_loader is None  # Default is None
    
    def test_path_b_config_creation(self):
        """Test that PathBConfig can be created"""
        config = PathBConfig(
            train_start="2023-01-01",
            train_end="2023-06-30",
            test_start="2023-07-01",
            test_end="2023-12-31",
            walkforward_window="6m",
            walkforward_step="1m",
            universe=["2330.TW", "2317.TW"],
            rebalance_frequency="M",
            alpha_config_set=[
                {"name": "strategy_1", "alpha_config": {}}
            ],
        )
        
        assert config is not None
        assert config.train_start == "2023-01-01"
        assert config.train_end == "2023-06-30"
        assert config.test_start == "2023-07-01"
        assert config.test_end == "2023-12-31"
        assert len(config.universe) == 2
    
    def test_path_b_engine_run_skeleton(self):
        """
        Test that PathBEngine.run() can be called without errors.
        Minimal walk-forward test with mock data.
        """
        engine = PathBEngine()
        
        config = PathBConfig(
            train_start="2024-01-01",
            train_end="2024-01-15",
            test_start="2024-01-16",
            test_end="2024-01-20",
            walkforward_window="1m",  # Small window for quick test
            walkforward_step="1m",
            universe=["2330.TW", "2317.TW"],
            rebalance_frequency="D",
            alpha_config_set=[
                {"name": "strategy_1", "alpha_config": {}}
            ],
            data_source="mock",
            mode="basic",
        )
        
        # Run should not raise exception
        result = engine.run(config)
        
        # Verify result structure
        assert result is not None, "Result should not be None"
        assert isinstance(result, PathBRunResult), "Result should be PathBRunResult"
        assert result.config == config, "Result config should match input"
        assert isinstance(result.window_results, list), "Window results should be a list"
        assert len(result.window_results) >= 1, "Should have at least 1 window"
        assert isinstance(result.summary, dict), "Summary should be a dict"
        assert isinstance(result.governance_analysis, dict), "Governance analysis should be a dict"
        
        # Check each window result
        for window_result in result.window_results:
            assert window_result.window_id > 0, "Window ID should be positive"
            assert window_result.train_start is not None, "Train start should be set"
            assert window_result.train_end is not None, "Train end should be set"
            assert window_result.test_start is not None, "Test start should be set"
            assert window_result.test_end is not None, "Test end should be set"
            
            # Check performance metrics exist (can be float, including 0.0)
            assert isinstance(window_result.sharpe_ratio, (float, int)), \
                f"Sharpe ratio should be numeric, got {type(window_result.sharpe_ratio)}"
            assert isinstance(window_result.max_drawdown, (float, int)), \
                f"Max drawdown should be numeric, got {type(window_result.max_drawdown)}"
            assert isinstance(window_result.total_return, (float, int)), \
                f"Total return should be numeric, got {type(window_result.total_return)}"
            assert isinstance(window_result.turnover_rate, (float, int)), \
                f"Turnover rate should be numeric, got {type(window_result.turnover_rate)}"
            
            # Check test_result exists
            assert window_result.test_result is not None, "Test result should not be None"
        
        # Check summary contains basic metrics
        assert "num_windows" in result.summary, "Summary should contain num_windows"
        assert result.summary["num_windows"] >= 1, "Should have at least 1 window"
    
    def test_path_b_window_result_structure(self):
        """Test PathBWindowResult data structure"""
        from jgod.path_a.path_a_schema import PathABacktestResult
        
        # Create placeholder test result
        # Note: This is a minimal structure check
        window_result = PathBWindowResult(
            window_id=1,
            train_start="2023-01-01",
            train_end="2023-06-30",
            test_start="2023-07-01",
            test_end="2023-12-31",
            train_result=None,
            test_result=None,  # TODO: Create actual PathABacktestResult
            governance_events=[],
            sharpe_ratio=1.0,
            max_drawdown=-0.15,
            total_return=0.18,
            turnover_rate=0.45,
            tracking_error=None,
            information_ratio=None,
            factor_attribution=None,
        )
        
        assert window_result.window_id == 1
        assert window_result.sharpe_ratio == 1.0
        assert window_result.max_drawdown == -0.15
        assert isinstance(window_result.governance_events, list)
    
    def test_path_b_run_result_structure(self):
        """Test PathBRunResult data structure"""
        config = PathBConfig(
            train_start="2023-01-01",
            train_end="2023-06-30",
            test_start="2023-07-01",
            test_end="2023-12-31",
            walkforward_window="6m",
            walkforward_step="1m",
            universe=["2330.TW"],
            rebalance_frequency="M",
            alpha_config_set=[],
        )
        
        result = PathBRunResult(
            config=config,
            window_results=[],
            summary={},
            governance_analysis={},
            output_files=[],
        )
        
        assert result.config == config
        assert isinstance(result.window_results, list)
        assert isinstance(result.summary, dict)
        assert isinstance(result.governance_analysis, dict)
        assert isinstance(result.output_files, list)

