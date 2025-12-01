"""
系統診斷模組

包含健康檢查和診斷引擎功能。

Reference:
- docs/JGOD_DIAGNOSIS_ENGINE_STANDARD_v1.md (v1)
"""

# Legacy exports (v0)
from .health_check import HealthChecker, check_all_providers

# Diagnosis Engine v1
from .diagnosis_types import (
    DiagnosticEvent,
    SystemHealthSnapshot,
    RepairAction,
    RepairPlan,
    DiagnosisEngineResult,
)
from .diagnosis_engine import DiagnosisEngine

__all__ = [
    # Legacy exports (v0)
    "HealthChecker",
    "check_all_providers",
    # Diagnosis Engine v1 exports
    "DiagnosticEvent",
    "SystemHealthSnapshot",
    "RepairAction",
    "RepairPlan",
    "DiagnosisEngineResult",
    "DiagnosisEngine",
]

