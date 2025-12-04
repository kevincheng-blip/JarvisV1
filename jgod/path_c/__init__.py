"""
Path C - Validation Lab / Scenario Engine

This module provides the Path C Engine for executing batch scenario validation
by calling Path B Engine multiple times with different configurations.

Reference:
- spec/JGOD_PathCEngine_Spec.md
- docs/JGOD_PATH_C_STANDARD_v1.md
"""

from jgod.path_c.path_c_types import (
    PathCScenarioConfig,
    PathCScenarioResult,
    PathCExperimentConfig,
    PathCRunSummary,
    ModeType,
    DataSourceType,
)

from jgod.path_c.path_c_engine import PathCEngine

from jgod.path_c.scenario_presets import (
    get_default_scenarios_for_taiwan_equities,
)

__all__ = [
    "PathCScenarioConfig",
    "PathCScenarioResult",
    "PathCExperimentConfig",
    "PathCRunSummary",
    "PathCEngine",
    "ModeType",
    "DataSourceType",
    "get_default_scenarios_for_taiwan_equities",
]

