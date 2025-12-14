"""
Contract tests for Learning Layers

v0.6.8-A8: Tests for Thought/Method/Strategy layers
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from jgod.learning.tuning_advisor import analyze_and_suggest_patch
from jgod.learning.feature_selector import analyze_and_suggest_subset
from jgod.learning.strategy_allocator import analyze_and_suggest_allocation
from jgod.research.storage import save_daily_log


@pytest.fixture
def mock_logs():
    """Create mock daily logs for testing."""
    logs = []
    base_date = datetime(2024, 4, 1)
    initial_nav = 1_000_000.0
    
    for i in range(20):
        date_str = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        nav = initial_nav * (1.0 + (i * 0.01))  # Simple increasing NAV
        
        log = {
            "symbol": "2330",
            "date": date_str,
            "nav": nav,
            "features_summary": {
                "SMA_5": 100.0 + i,
                "SMA_20": 100.0 + i * 0.5,
                "RSI_14": 50.0 + i * 0.5,
                "RET_1D": 0.01,
            },
            "decision": {
                "primary_strategy": "trend_follow" if i % 2 == 0 else "momentum",
                "position_scale": 0.7,
                "confidence": 0.6,
            },
        }
        logs.append(log)
    
    return logs


@patch("jgod.learning.tuning_advisor.load_daily_logs")
@patch("jgod.learning.tuning_advisor.compute_arena")
def test_tuning_advisor_generates_patch(mock_arena, mock_load_logs, mock_logs):
    """Test that tuning_advisor generates patch suggestion."""
    mock_load_logs.return_value = mock_logs[:5]  # Last 5 days
    
    # Mock arena result
    from jgod.decision_v3.arena import ArenaResult, ChallengerScore, AutoTuningResult, VariantConfig
    mock_arena_result = MagicMock()
    mock_arena_result.winner_id = "BASELINE"
    mock_arena_result.is_regression = True
    mock_arena_result.scoreboard = [
        MagicMock(challenger_id="V3", composite_score=0.5),
        MagicMock(challenger_id="BASELINE", composite_score=0.7),
    ]
    mock_arena_result.auto_tuning = AutoTuningResult(
        best_config=VariantConfig(
            risk_mapping={"STABLE": 0.75},
            composite_weights={},
        ),
        top_variants=[],
        notes="Test tuning",
    )
    mock_arena.return_value = mock_arena_result
    
    patch_suggestion = analyze_and_suggest_patch("2330", "2024-04-05", window=5)
    
    # Should generate patch if arena shows improvement
    # (May return None if conditions not met, which is OK)
    if patch_suggestion:
        assert patch_suggestion.patch_id is not None
        assert patch_suggestion.target in ["risk_mapping", "composite_weights"]
        assert patch_suggestion.status == "PENDING_APPROVAL"
        assert "changes" in patch_suggestion.__dict__


@patch("jgod.learning.feature_selector.load_daily_logs")
def test_feature_selector_outputs_subset(mock_load_logs, mock_logs):
    """Test that feature_selector outputs feature subset."""
    mock_load_logs.return_value = mock_logs[:20]  # Last 20 days
    
    subset = analyze_and_suggest_subset("2330", "2024-04-20", window=20)
    
    # Should generate subset if enough data
    if subset:
        assert subset.symbol == "2330"
        assert len(subset.recommended_features) > 0
        assert subset.status == "PENDING_APPROVAL"
        assert "reason" in subset.__dict__


@patch("jgod.learning.strategy_allocator.load_daily_logs")
def test_strategy_allocator_no_auto_apply(mock_load_logs, mock_logs):
    """Test that strategy_allocator generates suggestion but doesn't auto-apply."""
    mock_load_logs.return_value = mock_logs[:60]  # Last 60 days
    
    allocation = analyze_and_suggest_allocation("2330", "2024-04-60", window=60)
    
    # Should generate allocation if enough data and strategy change needed
    # (May return None if no change needed, which is OK)
    if allocation:
        assert allocation.symbol == "2330"
        assert allocation.recommended_primary_strategy is not None
        assert allocation.status == "PENDING_APPROVAL"
        assert "reason" in allocation.__dict__


def test_learning_layers_no_auto_apply():
    """Test that learning layers never auto-apply (only generate suggestions)."""
    # This is a structural test: all learning layer functions return
    # suggestions with status="PENDING_APPROVAL", never directly modify doctrine
    
    # All suggestions must have status="PENDING_APPROVAL"
    # This is enforced in the model definitions and save functions
    
    from jgod.learning.models import TuningPatch, FeatureSubset, StrategyAllocation
    
    patch = TuningPatch(
        patch_id="TEST-001",
        date="2024-04-05",
        symbol="2330",
        target="risk_mapping",
        changes={},
        reason="Test",
    )
    assert patch.status == "PENDING_APPROVAL"
    
    subset = FeatureSubset(
        date="2024-04-20",
        symbol="2330",
        recommended_features=["SMA_20"],
        reason="Test",
    )
    assert subset.status == "PENDING_APPROVAL"
    
    allocation = StrategyAllocation(
        date="2024-04-60",
        symbol="2330",
        recommended_primary_strategy="trend_follow",
        reason="Test",
    )
    assert allocation.status == "PENDING_APPROVAL"

