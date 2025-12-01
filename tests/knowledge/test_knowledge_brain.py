"""Unit tests for KnowledgeBrain

Tests for loading, searching, and querying knowledge items.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path

from jgod.knowledge.knowledge_brain import KnowledgeBrain, KnowledgeItem


@pytest.fixture
def sample_knowledge_items():
    """Sample knowledge items for testing"""
    return [
        {
            "id": "formula_sharpe_001",
            "type": "FORMULA",
            "title": "Sharpe Ratio",
            "description": "Risk-adjusted return metric",
            "tags": ["risk", "performance", "sharpe"],
            "source_doc": "test_doc.md",
            "source_location": "Chapter 1",
            "raw_text": "Sharpe = (R_p - R_f) / σ_p",
            "structured": {
                "expression": "Sharpe = (R_p - R_f) / σ_p",
                "variables": {
                    "R_p": "Portfolio return",
                    "R_f": "Risk-free rate",
                    "σ_p": "Portfolio standard deviation"
                },
                "notes": "Annualized Sharpe = Daily Sharpe × √252"
            }
        },
        {
            "id": "rule_stop_loss_001",
            "type": "RULE",
            "title": "Single Trade Max Loss 2%",
            "description": "Maximum loss per trade cannot exceed 2% of account value",
            "tags": ["risk", "stop_loss", "position_sizing"],
            "source_doc": "test_doc.md",
            "source_location": "Risk Engine",
            "raw_text": "Max loss per trade: 2%",
            "structured": {
                "if": "Trade loss reaches -2% of account value",
                "then": "Immediately exit, no hesitation",
                "priority": 10,
                "scope": "risk"
            }
        },
        {
            "id": "concept_rcnc_001",
            "type": "CONCEPT",
            "title": "RCNC (Real-time Cumulative Net Cost)",
            "description": "Dynamic cost line calculated from major orders and tick data",
            "tags": ["intraday", "capital_flow", "cost"],
            "source_doc": "test_doc.md",
            "source_location": "Intraday Engine",
            "raw_text": "RCNC is calculated using Pandas cumsum",
            "structured": {
                "name": "RCNC",
                "definition": "Real-time Cumulative Net Cost line for detecting major order flow",
                "examples": [
                    "Calculate daily RCNC volatility as input factor",
                    "Detect RCNC anomalies to identify major flow"
                ]
            }
        },
        {
            "id": "rule_entry_001",
            "type": "RULE",
            "title": "Mainstream Breakthrough Entry",
            "description": "Entry conditions for mainstream breakthrough strategy",
            "tags": ["strategy", "entry", "breakthrough"],
            "source_doc": "test_doc.md",
            "source_location": "Strategy Engine",
            "raw_text": "Entry: above quarterly MA, break resistance, volume-price sync",
            "structured": {
                "if": "Price above quarterly MA, breaks resistance, volume increases",
                "then": "Enter long position",
                "priority": 5,
                "scope": "entry"
            }
        }
    ]


@pytest.fixture
def temp_jsonl_file(sample_knowledge_items):
    """Create temporary JSONL file with sample data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
        for item in sample_knowledge_items:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def test_knowledge_item_from_dict():
    """Test creating KnowledgeItem from dictionary"""
    data = {
        "id": "test_001",
        "type": "FORMULA",
        "title": "Test Formula",
        "description": "Test description",
        "tags": ["test"],
        "source_doc": "test.md",
        "source_location": "Section 1",
        "raw_text": "Test text",
        "structured": {"expression": "x + y"}
    }
    
    item = KnowledgeItem.from_dict(data)
    assert item.id == "test_001"
    assert item.type == "FORMULA"
    assert item.title == "Test Formula"
    assert item.tags == ["test"]
    assert item.structured == {"expression": "x + y"}


def test_knowledge_item_to_dict():
    """Test converting KnowledgeItem to dictionary"""
    item = KnowledgeItem(
        id="test_001",
        type="FORMULA",
        title="Test Formula",
        description="Test description",
        tags=["test"],
        structured={"expression": "x + y"}
    )
    
    data = item.to_dict()
    assert data["id"] == "test_001"
    assert data["type"] == "FORMULA"
    assert data["structured"] == {"expression": "x + y"}


def test_load_from_existing_file(temp_jsonl_file):
    """Test loading knowledge items from existing JSONL file"""
    brain = KnowledgeBrain(path=temp_jsonl_file)
    brain.load()
    
    assert brain.count() == 4
    assert brain._loaded is True


def test_load_from_nonexistent_file():
    """Test loading from nonexistent file (should create empty file)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "nonexistent.jsonl"
        brain = KnowledgeBrain(path=temp_path)
        brain.load()
        
        assert brain.count() == 0
        assert temp_path.exists()
        assert brain._loaded is True


def test_search_by_query(temp_jsonl_file):
    """Test searching by query keyword"""
    brain = KnowledgeBrain(path=temp_jsonl_file)
    brain.load()
    
    results = brain.search(query="Sharpe")
    assert len(results) == 1
    assert results[0].id == "formula_sharpe_001"
    
    results = brain.search(query="loss")
    assert len(results) >= 1
    assert any(r.id == "rule_stop_loss_001" for r in results)


def test_search_by_type(temp_jsonl_file):
    """Test searching by type"""
    brain = KnowledgeBrain(path=temp_jsonl_file)
    brain.load()
    
    rules = brain.search(type="RULE")
    assert len(rules) == 2
    assert all(r.type == "RULE" for r in rules)
    
    formulas = brain.search(type="FORMULA")
    assert len(formulas) == 1
    assert formulas[0].id == "formula_sharpe_001"


def test_search_by_tags(temp_jsonl_file):
    """Test searching by tags"""
    brain = KnowledgeBrain(path=temp_jsonl_file)
    brain.load()
    
    risk_items = brain.search(tags=["risk"])
    assert len(risk_items) >= 2
    assert any(r.id == "formula_sharpe_001" for r in risk_items)
    assert any(r.id == "rule_stop_loss_001" for r in risk_items)
    
    entry_items = brain.search(tags=["entry"])
    assert len(entry_items) == 1
    assert entry_items[0].id == "rule_entry_001"


def test_search_multiple_filters(temp_jsonl_file):
    """Test searching with multiple filters"""
    brain = KnowledgeBrain(path=temp_jsonl_file)
    brain.load()
    
    # Search for risk-related rules
    results = brain.search(type="RULE", tags=["risk"])
    assert len(results) == 1
    assert results[0].id == "rule_stop_loss_001"
    
    # Search for performance formulas
    results = brain.search(type="FORMULA", tags=["performance"])
    assert len(results) == 1
    assert results[0].id == "formula_sharpe_001"


def test_search_limit(temp_jsonl_file):
    """Test search result limit"""
    brain = KnowledgeBrain(path=temp_jsonl_file)
    brain.load()
    
    results = brain.search(limit=2)
    assert len(results) <= 2


def test_get_by_id(temp_jsonl_file):
    """Test getting knowledge item by ID"""
    brain = KnowledgeBrain(path=temp_jsonl_file)
    brain.load()
    
    item = brain.get_by_id("formula_sharpe_001")
    assert item is not None
    assert item.id == "formula_sharpe_001"
    assert item.type == "FORMULA"
    
    item = brain.get_by_id("nonexistent_id")
    assert item is None


def test_get_rules(temp_jsonl_file):
    """Test getting all rules"""
    brain = KnowledgeBrain(path=temp_jsonl_file)
    brain.load()
    
    rules = brain.get_rules()
    assert len(rules) == 2
    assert all(r.type == "RULE" for r in rules)
    
    risk_rules = brain.get_rules(tag="risk")
    assert len(risk_rules) == 1
    assert risk_rules[0].id == "rule_stop_loss_001"


def test_get_formulas(temp_jsonl_file):
    """Test getting all formulas"""
    brain = KnowledgeBrain(path=temp_jsonl_file)
    brain.load()
    
    formulas = brain.get_formulas()
    assert len(formulas) == 1
    assert formulas[0].id == "formula_sharpe_001"
    
    performance_formulas = brain.get_formulas(tag="performance")
    assert len(performance_formulas) == 1
    assert performance_formulas[0].id == "formula_sharpe_001"
    
    # No formulas with tag "nonexistent"
    nonexistent_formulas = brain.get_formulas(tag="nonexistent")
    assert len(nonexistent_formulas) == 0


def test_explain_concept(temp_jsonl_file):
    """Test explaining a concept by name"""
    brain = KnowledgeBrain(path=temp_jsonl_file)
    brain.load()
    
    # Search by title
    rcnc = brain.explain_concept("RCNC")
    assert rcnc is not None
    assert rcnc.id == "concept_rcnc_001"
    assert rcnc.type == "CONCEPT"
    
    # Search by structured.name
    rcnc2 = brain.explain_concept("Real-time Cumulative Net Cost")
    assert rcnc2 is not None
    assert rcnc2.id == "concept_rcnc_001"
    
    # Non-existent concept
    nonexistent = brain.explain_concept("Nonexistent Concept")
    assert nonexistent is None


def test_get_all(temp_jsonl_file):
    """Test getting all knowledge items"""
    brain = KnowledgeBrain(path=temp_jsonl_file)
    brain.load()
    
    all_items = brain.get_all()
    assert len(all_items) == 4


def test_count(temp_jsonl_file):
    """Test counting knowledge items"""
    brain = KnowledgeBrain(path=temp_jsonl_file)
    brain.load()
    
    assert brain.count() == 4


def test_reload(temp_jsonl_file):
    """Test reloading knowledge items"""
    brain = KnowledgeBrain(path=temp_jsonl_file)
    brain.load()
    
    initial_count = brain.count()
    brain.reload()
    assert brain.count() == initial_count


def test_invalid_json_line_handling():
    """Test handling invalid JSON lines"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
        f.write('{"valid": "json"}\n')
        f.write('invalid json line\n')
        f.write('{"another": "valid"}\n')
        temp_path = f.name
    
    try:
        brain = KnowledgeBrain(path=temp_path)
        brain.load()
        # Should load 2 valid items and skip the invalid line
        assert brain.count() == 2
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

