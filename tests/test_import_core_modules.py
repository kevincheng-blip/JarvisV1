"""
J-GOD Core Modules Import Test

Tests that critical backend modules can be imported without side effects.
This ensures the codebase is "agent-loop safe" - modules can be imported
without triggering heavy initialization or external service calls.

The test must be fast and must not require external services.
"""


def test_import_api_main():
    """Test that jgod.api.main can be imported"""
    import jgod.api.main
    assert jgod.api.main.app is not None


def test_import_api_routers_predictions():
    """Test that predictions router can be imported"""
    from jgod.api.routers import predictions
    assert predictions.router is not None


def test_import_doctrine_v2_patch_service():
    """Test that doctrine_v2 patch service can be imported"""
    from jgod.doctrine_v2 import patch_service
    assert patch_service is not None


def test_import_observer():
    """Test that observer module can be imported"""
    from jgod.observer import collector
    assert collector is not None


def test_import_decision():
    """Test that decision module can be imported"""
    from jgod.decision import decision_engine_v1
    assert decision_engine_v1 is not None
    # Also test the public interface
    from jgod.decision import DecisionEngineV1
    assert DecisionEngineV1 is not None

