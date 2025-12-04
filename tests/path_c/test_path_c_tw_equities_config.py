"""
Test for Path C Taiwan Equities Configuration

This test verifies that the TW Equities experiment config JSON can be loaded
and used with Path C Engine.

Reference: docs/JGOD_PATH_C_TW_EQUITIES_EXPERIMENTS_v1.md
"""

from __future__ import annotations

import pytest
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from jgod.path_c.path_c_types import PathCScenarioConfig, PathCExperimentConfig
from jgod.path_c.path_c_engine import PathCEngine
from scripts.run_jgod_path_c import load_scenarios_from_json


class TestPathCTWEquitiesConfig:
    """Test for Path C TW Equities Configuration"""
    
    @pytest.fixture
    def config_path(self) -> Path:
        """取得配置檔案路徑"""
        return PROJECT_ROOT / "configs" / "path_c" / "path_c_tw_equities_v1.json"
    
    def test_config_json_exists(self, config_path):
        """Test that config JSON file exists"""
        assert config_path.exists(), f"Config file should exist at {config_path}"
    
    def test_config_json_valid(self, config_path):
        """Test that config JSON is valid JSON"""
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        assert "experiment_name" in config_data, "Config should have experiment_name"
        assert "scenarios" in config_data, "Config should have scenarios"
        assert isinstance(config_data["scenarios"], list), "scenarios should be a list"
    
    def test_config_experiment_name(self, config_path):
        """Test that experiment_name is correct"""
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        assert config_data["experiment_name"] == "tw_equities_v1"
    
    def test_config_scenarios_count(self, config_path):
        """Test that config has exactly 6 scenarios"""
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        scenarios = config_data.get("scenarios", [])
        assert len(scenarios) == 6, f"Should have 6 scenarios, got {len(scenarios)}"
    
    def test_config_scenarios_required_fields(self, config_path):
        """Test that all scenarios have required fields"""
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        required_fields = [
            "name",
            "mode",
            "data_source",
            "start_date",
            "end_date",
            "walkforward_window",
            "walkforward_step",
            "universe",
        ]
        
        for i, scenario_data in enumerate(config_data["scenarios"]):
            for field in required_fields:
                assert field in scenario_data, \
                    f"Scenario {i} ({scenario_data.get('name', 'unknown')}) should have {field}"
    
    def test_load_scenarios_from_json(self, config_path):
        """Test that scenarios can be loaded from JSON"""
        scenarios = load_scenarios_from_json(str(config_path))
        
        assert len(scenarios) == 6, "Should load 6 scenarios"
        
        # 檢查每個 scenario 都是 PathCScenarioConfig
        for scenario in scenarios:
            assert isinstance(scenario, PathCScenarioConfig), \
                f"All scenarios should be PathCScenarioConfig, got {type(scenario)}"
            assert scenario.name, "Scenario should have a name"
            assert scenario.mode in ["basic", "extreme"], \
                f"Scenario mode should be 'basic' or 'extreme', got {scenario.mode}"
            assert scenario.data_source == "finmind", \
                f"Scenario should use finmind data source, got {scenario.data_source}"
    
    def test_basic_scenarios_count(self, config_path):
        """Test that there are 3 basic scenarios"""
        scenarios = load_scenarios_from_json(str(config_path))
        
        basic_scenarios = [s for s in scenarios if s.mode == "basic"]
        assert len(basic_scenarios) == 3, f"Should have 3 basic scenarios, got {len(basic_scenarios)}"
    
    def test_extreme_scenarios_count(self, config_path):
        """Test that there are 3 extreme scenarios"""
        scenarios = load_scenarios_from_json(str(config_path))
        
        extreme_scenarios = [s for s in scenarios if s.mode == "extreme"]
        assert len(extreme_scenarios) == 3, f"Should have 3 extreme scenarios, got {len(extreme_scenarios)}"
    
    def test_scenario_names_unique(self, config_path):
        """Test that all scenario names are unique"""
        scenarios = load_scenarios_from_json(str(config_path))
        
        names = [s.name for s in scenarios]
        assert len(names) == len(set(names)), "All scenario names should be unique"
    
    def test_experiment_config_creation(self, config_path):
        """Test that PathCExperimentConfig can be created from loaded scenarios"""
        scenarios = load_scenarios_from_json(str(config_path))
        
        experiment_config = PathCExperimentConfig(
            name="tw_equities_v1",
            scenarios=scenarios,
            output_dir="output/path_c",
        )
        
        assert experiment_config.name == "tw_equities_v1"
        assert len(experiment_config.scenarios) == 6
        assert all(isinstance(s, PathCScenarioConfig) for s in experiment_config.scenarios)
    
    def test_path_c_engine_initialization_with_config(self, config_path):
        """Test that PathCEngine can be initialized and accept the config"""
        scenarios = load_scenarios_from_json(str(config_path))
        
        # 只取第一個 scenario 做快速測試
        test_scenario = scenarios[0]
        
        # 建立實驗配置（只用一個 scenario）
        experiment_config = PathCExperimentConfig(
            name="tw_equities_test",
            scenarios=[test_scenario],
            output_dir="output/path_c",
        )
        
        # 初始化引擎
        engine = PathCEngine()
        assert engine is not None
        
        # 注意：此測試僅檢查初始化，不實際執行（避免需要 FinMind API）
        # 實際執行測試請使用 mock data_source

