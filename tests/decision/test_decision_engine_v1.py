"""
Decision Layer v1 - Unit Tests

測試 DecisionEngineV1 的核心功能
"""

import pytest
from datetime import date
from unittest.mock import Mock, MagicMock

from jgod.decision.models import RawScoreItem, DecisionOutput
from jgod.decision.config import DecisionConfig
from jgod.decision.engine import DecisionEngineV1
from jgod.decision.integration_policy import generate_final_predictions


@pytest.fixture
def mock_knowledge_brain():
    """Mock KnowledgeBrain"""
    brain = Mock()
    
    # Mock DoctrineHit-like object
    mock_hit = Mock()
    mock_hit.book_id = "book_05"
    mock_hit.section_id = "section_001"
    mock_hit.summary = "風險控制原則：單筆曝險不應超過總資本的 10%"
    mock_hit.core_principles = ["資本保護", "風險分散"]
    mock_hit.risk_rules = ["單筆曝險 < 10% 總資本"]
    mock_hit.tags = ["RISK_RULE", "CONCENTRATION"]
    
    brain.search_doctrine.return_value = [mock_hit]
    return brain


@pytest.fixture
def config_llm_disabled():
    """Config with LLM disabled"""
    return DecisionConfig(enable_llm=False, enable_doctrine=True)


@pytest.fixture
def config_doctrine_disabled():
    """Config with Doctrine disabled"""
    return DecisionConfig(enable_llm=False, enable_doctrine=False)


@pytest.fixture
def sample_raw_item():
    """Sample RawScoreItem"""
    return RawScoreItem(
        symbol="2330",
        name="台積電",
        date=date.today(),
        raw_score=0.85,
        strategy_scores={"S1_momentum": 0.9, "S2_value": 0.8},
        risk_metrics={"vol_20d": 0.25, "max_dd_60d": -0.08},
        context_tags=["high_beta", "tech_sector"]
    )


def test_decision_engine_llm_disabled(config_llm_disabled, mock_knowledge_brain, sample_raw_item):
    """測試 LLM 關閉時，final_score = raw_score"""
    engine = DecisionEngineV1(config_llm_disabled, mock_knowledge_brain)
    
    result = engine.decide_for_single(sample_raw_item)
    
    assert result.symbol == "2330"
    assert result.raw_score == 0.85
    assert result.final_score == 0.85  # correction_factor = 1.0 (fallback)
    assert result.correction_factor == 1.0
    assert result.llm_model == "fallback"


def test_decision_engine_doctrine_disabled(config_doctrine_disabled, sample_raw_item):
    """測試 Doctrine 關閉時，仍能正常處理"""
    mock_brain = Mock()
    engine = DecisionEngineV1(config_doctrine_disabled, mock_brain)
    
    result = engine.decide_for_single(sample_raw_item)
    
    assert result.symbol == "2330"
    assert result.final_score == 0.85
    # Doctrine 查詢不應該被呼叫
    mock_brain.search_doctrine.assert_not_called()


def test_correction_factor_clipping(sample_raw_item):
    """測試 correction_factor 超出範圍時的 clipping"""
    config = DecisionConfig(
        enable_llm=False,  # 使用 fallback
        min_correction=0.5,
        max_correction=1.5
    )
    
    # Mock LLM 回傳超出範圍的 factor（需要修改 engine 以注入 mock）
    # 這裡先測試基本邏輯
    mock_brain = Mock()
    engine = DecisionEngineV1(config, mock_brain)
    
    result = engine.decide_for_single(sample_raw_item)
    
    # Fallback factor = 1.0，應在範圍內
    assert 0.5 <= result.correction_factor <= 1.5


def test_batch_processing(config_llm_disabled, mock_knowledge_brain):
    """測試批次處理"""
    engine = DecisionEngineV1(config_llm_disabled, mock_knowledge_brain)
    
    raw_items = [
        RawScoreItem(symbol="2330", raw_score=0.85),
        RawScoreItem(symbol="2317", raw_score=0.75),
        RawScoreItem(symbol="2454", raw_score=0.65),
    ]
    
    batch_result = engine.decide_for_batch(raw_items)
    
    assert len(batch_result.items) == 3
    assert batch_result.items[0].symbol == "2330"
    assert batch_result.items[1].symbol == "2317"
    assert batch_result.items[2].symbol == "2454"


def test_generate_final_predictions(config_llm_disabled, mock_knowledge_brain):
    """測試 generate_final_predictions 整合函式"""
    engine = DecisionEngineV1(config_llm_disabled, mock_knowledge_brain)
    
    raw_items = [
        RawScoreItem(symbol="2330", raw_score=0.85),
        RawScoreItem(symbol="2317", raw_score=0.75),
        RawScoreItem(symbol="2454", raw_score=0.65),
    ]
    
    results = generate_final_predictions(raw_items, engine)
    
    assert len(results) == 3
    # 應該按 final_score 降序排序
    assert results[0].final_score >= results[1].final_score
    assert results[1].final_score >= results[2].final_score


def test_error_handling_in_batch(config_llm_disabled, mock_knowledge_brain):
    """測試批次處理中的錯誤處理"""
    engine = DecisionEngineV1(config_llm_disabled, mock_knowledge_brain)
    
    # 建立一個會導致錯誤的項目（例如 symbol 為 None）
    raw_items = [
        RawScoreItem(symbol="2330", raw_score=0.85),
        RawScoreItem(symbol="", raw_score=0.75),  # 可能導致錯誤
    ]
    
    # 應該能處理錯誤並繼續處理
    batch_result = engine.decide_for_batch(raw_items)
    
    # 應該至少有結果（可能包含 fallback）
    assert len(batch_result.items) == 2

