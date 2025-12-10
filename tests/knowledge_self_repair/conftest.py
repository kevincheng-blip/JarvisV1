"""Pytest fixtures for Self-Repair Engine tests"""

import pytest
from datetime import datetime
from typing import List

from jgod.knowledge.self_repair.models import (
    DoctrineSection,
    ConsistencyIssue,
    FixProposal,
    IssueType,
    IssueSeverity,
)


@pytest.fixture
def sample_doctrine_sections() -> List[DoctrineSection]:
    """Sample Doctrine sections for testing"""
    return [
        DoctrineSection(
            id="B01#S12",
            text="單一持股權重不得超過 15%。超過時應減倉至 15% 以下。",
            tags=["position", "risk", "concentration"],
            source="B01",
            section_id="S12",
        ),
        DoctrineSection(
            id="B02#S05",
            text="當策略衝突分數 >= 70 時，應暫停下單並重新評估。",
            tags=["conflict", "risk", "strategy"],
            source="B02",
            section_id="S05",
        ),
        DoctrineSection(
            id="B03#S08",
            text="最大回撤不得超過 20%。接近時應減倉。",
            tags=["drawdown", "risk"],
            source="B03",
            section_id="S08",
        ),
    ]


@pytest.fixture
def sample_conflicting_sections() -> List[DoctrineSection]:
    """Sample conflicting Doctrine sections"""
    return [
        DoctrineSection(
            id="B01#S12",
            text="單一持股權重不得超過 15%。",
            tags=["position", "risk"],
            source="B01",
            section_id="S12",
        ),
        DoctrineSection(
            id="B04#S03",
            text="單一持股權重可達 30%。",
            tags=["position", "risk"],
            source="B04",
            section_id="S03",
        ),
    ]


@pytest.fixture
def sample_duplicate_sections() -> List[DoctrineSection]:
    """Sample duplicate Doctrine sections"""
    duplicate_text = "單一持股權重不得超過 15%。"
    return [
        DoctrineSection(
            id="B01#S12",
            text=duplicate_text,
            tags=["position", "risk"],
            source="B01",
            section_id="S12",
        ),
        DoctrineSection(
            id="B01#S13",
            text=duplicate_text,
            tags=["position", "risk"],
            source="B01",
            section_id="S13",
        ),
    ]


@pytest.fixture
def sample_ambiguous_section() -> List[DoctrineSection]:
    """Sample ambiguous Doctrine section"""
    return [
        DoctrineSection(
            id="B05#S01",
            text="注意風險。",
            tags=["risk"],
            source="B05",
            section_id="S01",
        ),
    ]


@pytest.fixture
def sample_consistency_issues() -> List[ConsistencyIssue]:
    """Sample consistency issues for testing"""
    return [
        ConsistencyIssue(
            id="issue-001",
            issue_type=IssueType.CONFLICT,
            doctrine_refs=["B01#S12", "B04#S03"],
            description="規則衝突：持股權重上限不一致",
            severity=IssueSeverity.HIGH,
            context={"section1": "B01#S12", "section2": "B04#S03"},
        ),
        ConsistencyIssue(
            id="issue-002",
            issue_type=IssueType.AMBIGUOUS,
            doctrine_refs=["B05#S01"],
            description="定義模糊：缺乏具體操作標準",
            severity=IssueSeverity.MEDIUM,
            context={"section": "B05#S01"},
        ),
    ]


@pytest.fixture
def sample_fix_proposals() -> List[FixProposal]:
    """Sample fix proposals for testing"""
    return [
        FixProposal(
            id="proposal-001",
            issue_id="issue-001",
            proposed_text="統一規定：單一持股權重不得超過 15%。",
            justification="解決兩條規則的衝突，採用較保守的標準",
            confidence=0.85,
            impact="risk-reduction",
            clarity_score=0.9,
            logical_score=0.8,
            impact_score=0.85,
            doctrine_alignment_score=0.9,
        ),
        FixProposal(
            id="proposal-002",
            issue_id="issue-002",
            proposed_text="當風險指標超過警戒值時，應立即減倉至安全範圍。",
            justification="將模糊描述具體化為可操作規則",
            confidence=0.75,
            impact="rule-clarity",
            clarity_score=0.8,
            logical_score=0.7,
            impact_score=0.75,
            doctrine_alignment_score=0.8,
        ),
    ]


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for testing"""
    class MockLLMProvider:
        def ask(self, system_prompt: str, user_prompt: str) -> str:
            # Return deterministic mock response
            if "CONFLICT" in system_prompt or "衝突" in user_prompt:
                return "CONFLICT: 兩條規則對持股權重上限有不同標準"
            elif "AMBIGUOUS" in system_prompt or "模糊" in user_prompt:
                return "AMBIGUOUS: 規則描述過於抽象，缺乏具體操作標準"
            elif "GAP" in system_prompt:
                return "GAP: 缺少具體的操作步驟和判斷條件"
            elif "CLARITY" in system_prompt or "評分" in user_prompt:
                return """CLARITY: 0.85
LOGICAL: 0.80
IMPACT: 0.85
ALIGNMENT: 0.90
CONFIDENCE: 0.85"""
            elif "PROPOSED_TEXT" in system_prompt or "修正" in user_prompt:
                return """PROPOSED_TEXT:
統一規定：單一持股權重不得超過 15%。

JUSTIFICATION:
解決兩條規則的衝突，採用較保守的標準。

IMPACT:
risk-reduction"""
            else:
                return "CLEAR"
    
    return MockLLMProvider()

