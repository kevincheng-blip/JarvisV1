"""
Smoke test for API main module import.

This test ensures that all imports in jgod.api.main are valid and do not
raise ImportError at import time. This catches import issues early before
they surface during runtime.
"""


def test_import_api_main():
    """確認 FastAPI app 可以被匯入，而不會噴 ImportError"""
    from jgod.api.main import app
    assert app is not None


def test_import_decision_models():
    """確認 Decision models 可以被匯入"""
    from jgod.decision.models import PortfolioPlan, PositionPlan
    assert PortfolioPlan is not None
    assert PositionPlan is not None


def test_import_path_a_engine():
    """確認 PathAEngineV1 可以正確匯入相關 models"""
    from jgod.path_a.path_a_engine_v1 import PathAEngineV1
    from jgod.decision.models import PortfolioPlan, PositionPlan
    assert PathAEngineV1 is not None
    assert PortfolioPlan is not None
    assert PositionPlan is not None
