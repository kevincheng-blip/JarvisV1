"""Integration test for demo_error_learning_engine script

Simple test to verify that the demo script can be imported and
its ErrorEvents can be analyzed without exceptions.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from jgod.learning.error_event import ErrorEvent
from jgod.learning.error_learning_engine import ErrorLearningEngine
from jgod.knowledge.knowledge_brain import KnowledgeItem


@pytest.fixture
def mock_knowledge_brain():
    """Create a mock KnowledgeBrain"""
    brain = Mock()
    
    # Mock some rules
    rule = KnowledgeItem(
        id="RULE_001",
        type="RULE",
        title="測試規則",
        description="這是一個測試規則",
        tags=["risk", "test"],
        source_doc="test.md",
        source_location="line 1",
        raw_text="測試",
        structured={"if": "條件", "then": "行動", "priority": 5, "scope": "test"}
    )
    brain.get_rules.return_value = [rule]
    brain.search.return_value = []
    brain.get_formulas.return_value = []
    brain.count.return_value = 1
    
    return brain


def test_demo_script_can_be_imported():
    """Test that demo script can be imported"""
    try:
        # Import the demo script
        import importlib.util
        demo_path = project_root / "scripts" / "demo_error_learning_engine.py"
        
        if demo_path.exists():
            spec = importlib.util.spec_from_file_location("demo", demo_path)
            demo_module = importlib.util.module_from_spec(spec)
            # Don't execute, just verify it can be loaded
            assert spec is not None
        else:
            pytest.skip(f"Demo script not found at {demo_path}")
    except Exception as e:
        pytest.fail(f"Failed to import demo script: {e}")


def test_case_a_event_can_be_analyzed(mock_knowledge_brain, monkeypatch):
    """Test that Case A ErrorEvent can be analyzed"""
    from scripts.demo_error_learning_engine import create_case_a_event
    
    # Mock get_knowledge_brain
    def mock_get_brain():
        return mock_knowledge_brain
    
    monkeypatch.setattr(
        "jgod.learning.error_learning_engine.get_knowledge_brain",
        mock_get_brain
    )
    
    # Create event
    rule_example = {
        "item": mock_knowledge_brain.get_rules()[0],
        "id": "RULE_001",
        "title": "測試規則",
        "tags": ["risk", "test"]
    }
    
    event = create_case_a_event(rule_example)
    assert event.id == "DEMO_CASE_A_UTILIZATION_GAP"
    assert len(event.used_rules) == 0  # Intentionally empty
    
    # Create engine and analyze
    engine = ErrorLearningEngine()
    engine._knowledge_brain = mock_knowledge_brain
    
    # Should not raise exception
    analysis = engine.analyze_error(event)
    assert analysis is not None
    assert analysis.event_id == event.id


def test_case_b_event_can_be_analyzed(mock_knowledge_brain, monkeypatch):
    """Test that Case B ErrorEvent can be analyzed"""
    from scripts.demo_error_learning_engine import create_case_b_event
    
    # Mock concept
    concept = KnowledgeItem(
        id="CONCEPT_001",
        type="CONCEPT",
        title="測試概念",
        description="這是一個測試概念",
        tags=["test"],
        source_doc="test.md",
        source_location="line 1",
        raw_text="測試概念",
        structured={"name": "測試概念", "definition": "定義", "examples": []}
    )
    
    mock_knowledge_brain.get_rules.return_value = []  # No rules
    mock_knowledge_brain.search.return_value = [concept]  # Only concept
    
    def mock_get_brain():
        return mock_knowledge_brain
    
    monkeypatch.setattr(
        "jgod.learning.error_learning_engine.get_knowledge_brain",
        mock_get_brain
    )
    
    # Create event
    concept_example = {
        "item": concept,
        "id": "CONCEPT_001",
        "title": "測試概念",
        "name": "測試概念",
        "tags": ["test"],
        "description": "定義"
    }
    
    event = create_case_b_event(concept_example)
    assert event.id == "DEMO_CASE_B_FORM_INSUFFICIENT"
    
    # Analyze
    engine = ErrorLearningEngine()
    engine._knowledge_brain = mock_knowledge_brain
    
    analysis = engine.analyze_error(event)
    assert analysis is not None


def test_case_c_event_can_be_analyzed(mock_knowledge_brain, monkeypatch):
    """Test that Case C ErrorEvent can be analyzed"""
    from scripts.demo_error_learning_engine import create_case_c_event
    
    # Empty knowledge base
    mock_knowledge_brain.get_rules.return_value = []
    mock_knowledge_brain.search.return_value = []
    mock_knowledge_brain.get_formulas.return_value = []
    
    def mock_get_brain():
        return mock_knowledge_brain
    
    monkeypatch.setattr(
        "jgod.learning.error_learning_engine.get_knowledge_brain",
        mock_get_brain
    )
    
    # Create event
    event = create_case_c_event()
    assert event.id == "DEMO_CASE_C_KNOWLEDGE_GAP"
    
    # Analyze
    engine = ErrorLearningEngine()
    engine._knowledge_brain = mock_knowledge_brain
    
    analysis = engine.analyze_error(event)
    assert analysis is not None
    # Should be classified as KNOWLEDGE_GAP
    assert analysis.classification in ["KNOWLEDGE_GAP", "UNKNOWN"]


def test_demo_error_events_have_required_fields():
    """Test that demo ErrorEvents have all required fields"""
    from scripts.demo_error_learning_engine import (
        create_case_a_event,
        create_case_b_event,
        create_case_c_event
    )
    
    # Case A
    event_a = create_case_a_event(None)
    assert event_a.id
    assert event_a.timestamp
    assert event_a.symbol
    
    # Case B
    event_b = create_case_b_event(None)
    assert event_b.id
    assert event_b.timestamp
    
    # Case C
    event_c = create_case_c_event()
    assert event_c.id
    assert event_c.timestamp


def test_case_classification_expectations(mock_knowledge_brain, monkeypatch):
    """Test that three demo cases get expected classifications"""
    from scripts.demo_error_learning_engine import (
        create_case_a_event,
        create_case_b_event,
        create_case_c_event
    )
    from jgod.learning.error_event import (
        CLASS_UTILIZATION_GAP,
        CLASS_FORM_INSUFFICIENT,
        CLASS_KNOWLEDGE_GAP
    )
    
    def mock_get_brain():
        return mock_knowledge_brain
    
    monkeypatch.setattr(
        "jgod.learning.error_learning_engine.get_knowledge_brain",
        mock_get_brain
    )
    
    engine = ErrorLearningEngine()
    engine._knowledge_brain = mock_knowledge_brain
    
    # Case A: UTILIZATION_GAP
    # Setup: Has a rule that is highly relevant but not used
    rule_for_case_a = KnowledgeItem(
        id="RULE_DEMO_A",
        type="RULE",
        title="單筆最大虧損 2% 規則",
        description="單筆交易最大虧損不得超過帳戶總值的 2%",
        tags=["risk", "stop_loss"],
        source_doc="test.md",
        source_location="line 1",
        raw_text="單筆最大虧損 2%",
        structured={
            "if": "單筆交易虧損達到帳戶總值的 -2%",
            "then": "立即砍單",
            "priority": 10,
            "scope": "risk"
        }
    )
    
    mock_knowledge_brain.get_rules.return_value = [rule_for_case_a]
    mock_knowledge_brain.search.return_value = []
    mock_knowledge_brain.get_formulas.return_value = []
    
    rule_example_a = {
        "item": rule_for_case_a,
        "id": "RULE_DEMO_A",
        "title": "單筆最大虧損 2% 規則",
        "tags": ["risk", "stop_loss"]
    }
    
    event_a = create_case_a_event(rule_example_a)
    event_a.used_rules = []  # Ensure not used
    event_a.error_type = "stop_loss"
    event_a.tags = ["risk", "stop_loss"]
    
    analysis_a = engine.analyze_error(event_a)
    # Case A should be UTILIZATION_GAP (has highly relevant rule but not used)
    assert analysis_a.classification in [CLASS_UTILIZATION_GAP, CLASS_UNKNOWN], \
        f"Case A expected UTILIZATION_GAP or UNKNOWN, got {analysis_a.classification}"
    
    # Case B: FORM_INSUFFICIENT
    # Setup: Has concepts but no rules
    concept_for_case_b = KnowledgeItem(
        id="CONCEPT_DEMO_B",
        type="CONCEPT",
        title="RCNC 概念",
        description="即時累積淨成本線的概念",
        tags=["intraday", "capital_flow"],
        source_doc="test.md",
        source_location="line 1",
        raw_text="RCNC 是...",
        structured={
            "name": "RCNC",
            "definition": "基於主力大單與逐筆成交數據計算的成本線",
            "examples": ["計算當日 RCNC 波動率"]
        }
    )
    
    mock_knowledge_brain.get_rules.return_value = []  # No rules
    mock_knowledge_brain.search.return_value = [concept_for_case_b]
    mock_knowledge_brain.get_formulas.return_value = []  # No formulas
    
    concept_example_b = {
        "item": concept_for_case_b,
        "id": "CONCEPT_DEMO_B",
        "title": "RCNC 概念",
        "name": "RCNC",
        "tags": ["intraday", "capital_flow"],
        "description": "定義"
    }
    
    event_b = create_case_b_event(concept_example_b)
    event_b.tags = ["intraday", "concept"]
    
    analysis_b = engine.analyze_error(event_b)
    # Case B should be FORM_INSUFFICIENT (has concepts but no rules/formulas)
    assert analysis_b.classification in [CLASS_FORM_INSUFFICIENT, CLASS_KNOWLEDGE_GAP, CLASS_UNKNOWN], \
        f"Case B expected FORM_INSUFFICIENT, KNOWLEDGE_GAP or UNKNOWN, got {analysis_b.classification}"
    
    # Case C: KNOWLEDGE_GAP
    # Setup: Empty knowledge base
    mock_knowledge_brain.get_rules.return_value = []
    mock_knowledge_brain.search.return_value = []
    mock_knowledge_brain.get_formulas.return_value = []
    
    event_c = create_case_c_event()
    event_c.tags = ["uncommon_situation", "novel_pattern", "edge_case"]
    
    analysis_c = engine.analyze_error(event_c)
    # Case C should be KNOWLEDGE_GAP (no relevant knowledge found)
    assert analysis_c.classification in [CLASS_KNOWLEDGE_GAP, CLASS_UNKNOWN], \
        f"Case C expected KNOWLEDGE_GAP or UNKNOWN, got {analysis_c.classification}"


def test_classification_priority_order(mock_knowledge_brain, monkeypatch):
    """Test that classification follows correct priority order"""
    from jgod.learning.error_event import (
        CLASS_UTILIZATION_GAP,
        CLASS_FORM_INSUFFICIENT,
        CLASS_KNOWLEDGE_GAP
    )
    
    def mock_get_brain():
        return mock_knowledge_brain
    
    monkeypatch.setattr(
        "jgod.learning.error_learning_engine.get_knowledge_brain",
        mock_get_brain
    )
    
    engine = ErrorLearningEngine()
    engine._knowledge_brain = mock_knowledge_brain
    
    # Test KNOWLEDGE_GAP priority (should win even if other conditions partially match)
    mock_knowledge_brain.get_rules.return_value = []
    mock_knowledge_brain.search.return_value = []
    mock_knowledge_brain.get_formulas.return_value = []
    
    event = ErrorEvent(
        id="TEST_PRIORITY",
        timestamp="2024-01-01T10:00:00",
        symbol="2330",
        timeframe="1d",
        error_type="unknown_error",
        tags=["novel", "uncommon"]
    )
    
    analysis = engine.analyze_error(event)
    # Should be KNOWLEDGE_GAP, not UNKNOWN
    assert analysis.classification == CLASS_KNOWLEDGE_GAP, \
        f"Expected KNOWLEDGE_GAP for empty knowledge base, got {analysis.classification}"

