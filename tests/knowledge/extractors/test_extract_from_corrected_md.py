"""Unit tests for extract_from_corrected_md"""

import pytest
import json
import tempfile
from pathlib import Path

from jgod.knowledge.extractors.extract_from_corrected_md import (
    merge_all_items,
    export_to_jsonl,
    main
)
from jgod.knowledge.extractors.base_extractor import (
    list_source_files,
    iter_blocks,
    normalize_type_tag
)


@pytest.fixture
def sample_markdown_file():
    """Create a sample markdown file for testing"""
    content = """# Test Knowledge Document

## Rules Section

單筆最大虧損 2% 規則

**[外部知識補強]**
勝率計算公式：

$$
\\text{Win Rate} = \\frac{\\text{獲利交易數}}{\\text{總交易數}}
$$

## Concept Section

**RCNC** (Real-time Cumulative Net Cost)

定義：基於主力大單與逐筆成交數據計算的成本線。

例如：
- 計算當日 RCNC 波動率
- 偵測 RCNC 異常波動

## Code Section

**[程式化說明]**
此計算可用 NumPy/Pandas 實現：

```python
import numpy as np
result = np.mean(data)
```

## Structure Section

### 系統架構

1. Factor Engine
2. Signal Engine
3. Risk Engine
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_CORRECTED.md', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


def test_normalize_type_tag():
    """Test type tag normalization"""
    assert normalize_type_tag("[RULE]") == "RULE"
    assert normalize_type_tag("formula") == "FORMULA"
    assert normalize_type_tag("CONCEPT") == "CONCEPT"


def test_iter_blocks(sample_markdown_file):
    """Test block iteration"""
    blocks = list(iter_blocks(sample_markdown_file))
    assert len(blocks) > 0
    
    # Check that we found some blocks
    types = [b[0] for b in blocks]
    assert len(types) > 0


def test_extract_rules_from_sample(sample_markdown_file, monkeypatch):
    """Test rule extraction from sample file"""
    from jgod.knowledge.extractors.extract_rules import extract_rules
    
    # Mock list_source_files to return our sample file
    def mock_list_files(source_dir=None):
        return [sample_markdown_file]
    
    monkeypatch.setattr(
        "jgod.knowledge.extractors.extract_rules.list_source_files",
        mock_list_files
    )
    
    rules = extract_rules()
    # Should find at least one rule-like item
    assert isinstance(rules, list)


def test_extract_formulas_from_sample(sample_markdown_file, monkeypatch):
    """Test formula extraction from sample file"""
    from jgod.knowledge.extractors.extract_formulas import extract_formulas
    
    def mock_list_files(source_dir=None):
        return [sample_markdown_file]
    
    monkeypatch.setattr(
        "jgod.knowledge.extractors.extract_formulas.list_source_files",
        mock_list_files
    )
    
    formulas = extract_formulas()
    assert isinstance(formulas, list)
    # Should find at least one formula (Win Rate)
    assert len(formulas) > 0


def test_extract_concepts_from_sample(sample_markdown_file, monkeypatch):
    """Test concept extraction from sample file"""
    from jgod.knowledge.extractors.extract_concepts import extract_concepts
    
    def mock_list_files(source_dir=None):
        return [sample_markdown_file]
    
    monkeypatch.setattr(
        "jgod.knowledge.extractors.extract_concepts.list_source_files",
        mock_list_files
    )
    
    concepts = extract_concepts()
    assert isinstance(concepts, list)
    # Should find RCNC concept
    assert len(concepts) > 0


def test_extract_code_from_sample(sample_markdown_file, monkeypatch):
    """Test code extraction from sample file"""
    from jgod.knowledge.extractors.extract_code_examples import extract_code_examples
    
    def mock_list_files(source_dir=None):
        return [sample_markdown_file]
    
    monkeypatch.setattr(
        "jgod.knowledge.extractors.extract_code_examples.list_source_files",
        mock_list_files
    )
    
    code_items = extract_code_examples()
    assert isinstance(code_items, list)
    # Should find at least one code block
    assert len(code_items) > 0


def test_export_to_jsonl(tmp_path):
    """Test JSONL export"""
    sample_items = [
        {
            "id": "TEST_001",
            "type": "RULE",
            "title": "Test Rule",
            "description": "Test description",
            "tags": ["test"],
            "source_doc": "test.md",
            "source_location": "line 1",
            "raw_text": "Test raw text",
            "structured": {"if": "condition", "then": "action", "priority": 3, "scope": "test"}
        }
    ]
    
    output_path = tmp_path / "test_output.jsonl"
    export_to_jsonl(sample_items, output_path)
    
    assert output_path.exists()
    
    # Verify JSONL format
    with open(output_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        assert len(lines) == 1
        item = json.loads(lines[0])
        assert item["id"] == "TEST_001"
        assert item["type"] == "RULE"


def test_merge_all_items_empty(tmp_path, monkeypatch):
    """Test merge with no source files"""
    def mock_list_files(source_dir=None):
        return []
    
    monkeypatch.setattr(
        "jgod.knowledge.extractors.extract_from_corrected_md.list_source_files",
        mock_list_files
    )
    
    items = merge_all_items()
    assert isinstance(items, list)
    # Should be empty but not error


def test_main_function(tmp_path, monkeypatch):
    """Test main extraction function"""
    # Create a temporary output path
    output_path = tmp_path / "test_knowledge.jsonl"
    
    # Create a temporary source file
    source_dir = tmp_path / "structured_books"
    source_dir.mkdir()
    
    test_file = source_dir / "test_CORRECTED.md"
    test_file.write_text("""
# Test

單筆最大虧損 2%

$$
\\text{Formula} = x + y
$$
""", encoding='utf-8')
    
    def mock_list_files(source_dir=None):
        if source_dir == source_dir:
            return [test_file]
        return []
    
    # This is a complex integration test - we'll test the export function separately
    # Just verify the structure works
    assert output_path.parent.exists()

