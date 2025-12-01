"""Unit tests for ErrorLearningEngine"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

from jgod.learning.error_event import (
    ErrorEvent,
    ErrorAnalysisResult,
    CLASS_UTILIZATION_GAP,
    CLASS_FORM_INSUFFICIENT,
    CLASS_KNOWLEDGE_GAP,
    CLASS_UNKNOWN
)
from jgod.learning.error_learning_engine import ErrorLearningEngine
from jgod.knowledge.knowledge_brain import KnowledgeItem, KnowledgeBrain


@pytest.fixture
def mock_knowledge_brain():
    """Create a mock KnowledgeBrain for testing"""
    brain = Mock(spec=KnowledgeBrain)
    return brain


@pytest.fixture
def sample_rule_item():
    """Create a sample rule KnowledgeItem"""
    return KnowledgeItem(
        id="RULE_001",
        type="RULE",
        title="單筆最大虧損 2% 規則",
        description="單筆交易最大虧損不得超過帳戶總值的 2%",
        tags=["risk", "stop_loss"],
        source_doc="test.md",
        source_location="line 100",
        raw_text="單筆最大虧損 2%",
        structured={
            "if": "單筆交易虧損達到帳戶總值的 -2%",
            "then": "立即砍單，不准猶豫",
            "priority": 10,
            "scope": "risk"
        }
    )


@pytest.fixture
def sample_concept_item():
    """Create a sample concept KnowledgeItem"""
    return KnowledgeItem(
        id="CONCEPT_001",
        type="CONCEPT",
        title="RCNC",
        description="即時累積淨成本線",
        tags=["intraday", "capital_flow"],
        source_doc="test.md",
        source_location="line 200",
        raw_text="RCNC 是...",
        structured={
            "name": "RCNC",
            "definition": "基於主力大單與逐筆成交數據計算的成本線",
            "examples": ["計算當日 RCNC 波動率"]
        }
    )


def test_error_event_from_dict():
    """Test creating ErrorEvent from dictionary"""
    data = {
        "id": "ERR_001",
        "timestamp": "2024-01-01T10:00:00",
        "symbol": "2330",
        "timeframe": "1d",
        "side": "long",
        "predicted_outcome": "up",
        "actual_outcome": "down",
        "pnl": -1000.0,
        "error_type": "direction",
        "tags": ["risk", "prediction"],
        "used_signals": ["SIG_001"],
        "used_rules": ["RULE_001"]
    }
    
    event = ErrorEvent.from_dict(data)
    assert event.id == "ERR_001"
    assert event.symbol == "2330"
    assert event.error_type == "direction"
    assert "risk" in event.tags


def test_error_analysis_result_from_dict():
    """Test creating ErrorAnalysisResult from dictionary"""
    data = {
        "event_id": "ERR_001",
        "classification": CLASS_UTILIZATION_GAP,
        "related_items": [{"id": "RULE_001", "type": "RULE", "title": "Test"}],
        "utilization_gap_reasons": ["規則存在但未使用"],
        "raw_query": "test query"
    }
    
    result = ErrorAnalysisResult.from_dict(data)
    assert result.event_id == "ERR_001"
    assert result.classification == CLASS_UTILIZATION_GAP
    assert len(result.related_items) == 1


def test_analyze_error_utilization_gap(mock_knowledge_brain, sample_rule_item, monkeypatch):
    """Test Case A: Rules exist but weren't used (UTILIZATION_GAP)"""
    # Setup mock: return a rule that wasn't used
    mock_knowledge_brain.get_rules.return_value = [sample_rule_item]
    mock_knowledge_brain.search.return_value = []
    mock_knowledge_brain.get_formulas.return_value = []
    
    # Monkeypatch get_knowledge_brain
    def mock_get_brain():
        return mock_knowledge_brain
    
    monkeypatch.setattr(
        "jgod.learning.error_learning_engine.get_knowledge_brain",
        mock_get_brain
    )
    
    # Create error event that didn't use the rule
    event = ErrorEvent(
        id="ERR_001",
        timestamp="2024-01-01T10:00:00",
        symbol="2330",
        timeframe="1d",
        error_type="stop_loss",
        tags=["risk"],
        used_rules=[]  # Rule not used!
    )
    
    # Analyze
    engine = ErrorLearningEngine()
    engine._knowledge_brain = mock_knowledge_brain
    analysis = engine.analyze_error(event)
    
    assert analysis.classification == CLASS_UTILIZATION_GAP
    assert len(analysis.utilization_gap_reasons) > 0
    assert "RULE_001" in str(analysis.utilization_gap_reasons[0])


def test_analyze_error_form_insufficient(mock_knowledge_brain, sample_concept_item, monkeypatch):
    """Test Case B: Only concepts exist, no executable rules (FORM_INSUFFICIENT)"""
    # Setup mock: return only concept, no rules
    mock_knowledge_brain.get_rules.return_value = []
    mock_knowledge_brain.search.return_value = [sample_concept_item]
    mock_knowledge_brain.get_formulas.return_value = []
    
    # Monkeypatch
    def mock_get_brain():
        return mock_knowledge_brain
    
    monkeypatch.setattr(
        "jgod.learning.error_learning_engine.get_knowledge_brain",
        mock_get_brain
    )
    
    # Create error event
    event = ErrorEvent(
        id="ERR_002",
        timestamp="2024-01-01T10:00:00",
        symbol="2330",
        timeframe="1d",
        error_type="timing",
        tags=["intraday"]
    )
    
    # Analyze
    engine = ErrorLearningEngine()
    engine._knowledge_brain = mock_knowledge_brain
    analysis = engine.analyze_error(event)
    
    assert analysis.classification == CLASS_FORM_INSUFFICIENT
    assert len(analysis.draft_rule_suggestions) > 0


def test_analyze_error_knowledge_gap(mock_knowledge_brain, monkeypatch):
    """Test Case C: No relevant knowledge found (KNOWLEDGE_GAP)"""
    # Setup mock: return empty results
    mock_knowledge_brain.get_rules.return_value = []
    mock_knowledge_brain.search.return_value = []
    mock_knowledge_brain.get_formulas.return_value = []
    
    # Monkeypatch
    def mock_get_brain():
        return mock_knowledge_brain
    
    monkeypatch.setattr(
        "jgod.learning.error_learning_engine.get_knowledge_brain",
        mock_get_brain
    )
    
    # Create error event
    event = ErrorEvent(
        id="ERR_003",
        timestamp="2024-01-01T10:00:00",
        symbol="2330",
        timeframe="1d",
        error_type="unknown_error",
        tags=["new_situation"]
    )
    
    # Analyze
    engine = ErrorLearningEngine()
    engine._knowledge_brain = mock_knowledge_brain
    analysis = engine.analyze_error(event)
    
    assert analysis.classification == CLASS_KNOWLEDGE_GAP
    assert len(analysis.knowledge_gap_notes) > 0
    assert len(analysis.draft_rule_suggestions) > 0
    assert len(analysis.draft_concept_suggestions) > 0


def test_save_drafts(tmp_path, mock_knowledge_brain, sample_concept_item, monkeypatch):
    """Test saving draft suggestions"""
    # Setup mock
    mock_knowledge_brain.get_rules.return_value = []
    mock_knowledge_brain.search.return_value = [sample_concept_item]
    mock_knowledge_brain.get_formulas.return_value = []
    
    def mock_get_brain():
        return mock_knowledge_brain
    
    monkeypatch.setattr(
        "jgod.learning.error_learning_engine.get_knowledge_brain",
        mock_get_brain
    )
    
    # Create engine with temp paths
    draft_path = tmp_path / "drafts.jsonl"
    engine = ErrorLearningEngine(
        draft_output_path=draft_path,
        report_output_dir=tmp_path / "reports"
    )
    engine._knowledge_brain = mock_knowledge_brain
    
    # Create error event
    event = ErrorEvent(
        id="ERR_004",
        timestamp="2024-01-01T10:00:00",
        symbol="2330",
        timeframe="1d",
        error_type="timing",
        tags=["intraday"]
    )
    
    # Analyze and save drafts
    analysis = engine.analyze_error(event)
    engine.save_drafts(analysis)
    
    # Check draft file was created
    assert draft_path.exists()
    
    # Verify content
    with open(draft_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        assert len(lines) > 0
        
        # Parse first draft
        draft_data = json.loads(lines[0])
        assert draft_data["type"] in ["RULE", "CONCEPT"]
        assert draft_data["id"].startswith("DRAFT_")


def test_save_report(tmp_path, mock_knowledge_brain, sample_rule_item, monkeypatch):
    """Test saving analysis report"""
    # Setup mock
    mock_knowledge_brain.get_rules.return_value = [sample_rule_item]
    mock_knowledge_brain.search.return_value = []
    mock_knowledge_brain.get_formulas.return_value = []
    
    def mock_get_brain():
        return mock_knowledge_brain
    
    monkeypatch.setattr(
        "jgod.learning.error_learning_engine.get_knowledge_brain",
        mock_get_brain
    )
    
    # Create engine
    report_dir = tmp_path / "reports"
    engine = ErrorLearningEngine(
        report_output_dir=report_dir
    )
    engine._knowledge_brain = mock_knowledge_brain
    
    # Create error event
    event = ErrorEvent(
        id="ERR_005",
        timestamp="2024-01-01T10:00:00",
        symbol="2330",
        timeframe="1d",
        predicted_outcome="up",
        actual_outcome="down",
        error_type="direction",
        tags=["prediction"]
    )
    
    # Analyze and save report
    analysis = engine.analyze_error(event)
    report_path = engine.save_report(event, analysis)
    
    # Check report was created
    assert report_path.exists()
    assert report_path.suffix == ".md"
    
    # Verify content
    content = report_path.read_text(encoding='utf-8')
    assert "錯誤分析報告" in content
    assert event.id in content
    assert analysis.classification in content


def test_process_and_report(tmp_path, mock_knowledge_brain, sample_rule_item, monkeypatch):
    """Test complete process_and_report workflow"""
    # Setup mock
    mock_knowledge_brain.get_rules.return_value = []
    mock_knowledge_brain.search.return_value = []
    mock_knowledge_brain.get_formulas.return_value = []
    
    def mock_get_brain():
        return mock_knowledge_brain
    
    monkeypatch.setattr(
        "jgod.learning.error_learning_engine.get_knowledge_brain",
        mock_get_brain
    )
    
    # Create engine
    engine = ErrorLearningEngine(
        draft_output_path=tmp_path / "drafts.jsonl",
        report_output_dir=tmp_path / "reports"
    )
    engine._knowledge_brain = mock_knowledge_brain
    
    # Create error event
    event = ErrorEvent(
        id="ERR_006",
        timestamp="2024-01-01T10:00:00",
        symbol="2330",
        timeframe="1d",
        error_type="unknown",
        tags=["test"]
    )
    
    # Process and report
    analysis = engine.process_and_report(event)
    
    # Verify analysis result
    assert analysis.event_id == event.id
    assert analysis.classification in [CLASS_UTILIZATION_GAP, CLASS_FORM_INSUFFICIENT, CLASS_KNOWLEDGE_GAP, CLASS_UNKNOWN]
    
    # Verify report was created
    report_files = list((tmp_path / "reports").glob(f"*_{event.id}.md"))
    assert len(report_files) > 0


def test_build_query_from_event():
    """Test query building from error event"""
    engine = ErrorLearningEngine()
    
    event = ErrorEvent(
        id="ERR_007",
        timestamp="2024-01-01T10:00:00",
        symbol="2330",
        timeframe="1d",
        error_type="direction",
        tags=["risk", "prediction"],
        notes="Market moved opposite direction"
    )
    
    query = engine._build_query_from_event(event)
    
    assert "direction" in query
    assert "risk" in query or "prediction" in query
    assert "2330" in query


def test_summarize_items(sample_rule_item, sample_concept_item):
    """Test summarizing KnowledgeItems"""
    engine = ErrorLearningEngine()
    
    items = [sample_rule_item, sample_concept_item]
    summarized = engine._summarize_items(items)
    
    assert len(summarized) == 2
    assert summarized[0]["id"] == "RULE_001"
    assert summarized[0]["type"] == "RULE"
    assert "title" in summarized[0]
    assert "tags" in summarized[0]

