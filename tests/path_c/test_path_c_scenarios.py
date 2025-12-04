"""
Test for Path C Scenario Presets

This test verifies that scenario presets are correctly defined.
"""

from __future__ import annotations

import pytest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from jgod.path_c.scenario_presets import get_default_scenarios_for_taiwan_equities
from jgod.path_c.path_c_types import PathCScenarioConfig


class TestPathCScenarios:
    """Test for Path C Scenario Presets"""
    
    def test_default_scenarios_not_empty(self):
        """Test that default scenarios list is not empty"""
        scenarios = get_default_scenarios_for_taiwan_equities()
        
        assert len(scenarios) > 0, "Should have at least one default scenario"
    
    def test_default_scenarios_type(self):
        """Test that all default scenarios are PathCScenarioConfig instances"""
        scenarios = get_default_scenarios_for_taiwan_equities()
        
        for scenario in scenarios:
            assert isinstance(scenario, PathCScenarioConfig), \
                f"All scenarios should be PathCScenarioConfig, got {type(scenario)}"
    
    def test_default_scenarios_required_fields(self):
        """Test that all default scenarios have required fields"""
        scenarios = get_default_scenarios_for_taiwan_equities()
        
        for scenario in scenarios:
            assert scenario.name, "Scenario should have a name"
            assert scenario.start_date, "Scenario should have start_date"
            assert scenario.end_date, "Scenario should have end_date"
            assert scenario.walkforward_window, "Scenario should have walkforward_window"
            assert scenario.mode in ["basic", "extreme"], \
                f"Scenario mode should be 'basic' or 'extreme', got {scenario.mode}"
            assert len(scenario.universe) > 0, "Scenario should have at least one stock in universe"
    
    def test_scenario_name_uniqueness(self):
        """Test that all scenario names are unique"""
        scenarios = get_default_scenarios_for_taiwan_equities()
        
        names = [s.name for s in scenarios]
        assert len(names) == len(set(names)), "All scenario names should be unique"

