"""
Decision Layer v1 - Integration Functions

與 Policy / Prediction Engine 整合的函式
"""

import logging
from typing import List, Optional
from datetime import date

from jgod.decision.models import RawScoreItem, DecisionOutput
from jgod.decision.engine import DecisionEngineV1
from jgod.decision.config import DecisionConfig

logger = logging.getLogger(__name__)


def generate_final_predictions(
    raw_items: List[RawScoreItem],
    decision_engine: DecisionEngineV1
) -> List[DecisionOutput]:
    """產生最終預測結果（供 TopN API / Final Orders API 使用）
    
    這個函式將會：
    1. 呼叫 decision_engine.decide_for_batch(raw_items)
    2. 回傳 DecisionOutput 列表，供：
       - TopN API
       - Final Orders API
       - War Room 使用
    
    Args:
        raw_items: Raw Score 項目列表
        decision_engine: DecisionEngineV1 實例
    
    Returns:
        DecisionOutput 列表，已按 final_score 排序（降序）
    """
    logger.info(f"Generating final predictions for {len(raw_items)} items")
    
    # 批次處理
    batch_result = decision_engine.decide_for_batch(raw_items)
    
    # 按 final_score 排序（降序）
    sorted_items = sorted(
        batch_result.items,
        key=lambda x: x.final_score,
        reverse=True
    )
    
    logger.info(f"Generated {len(sorted_items)} final predictions")
    
    return sorted_items


def convert_to_top_n_items(decision_outputs: List[DecisionOutput], n: int = 30) -> List[DecisionOutput]:
    """轉換為 Top N 項目
    
    Args:
        decision_outputs: 已排序的 DecisionOutput 列表
        n: 要取前 N 筆
    
    Returns:
        Top N DecisionOutput 列表
    """
    return decision_outputs[:n]


def generate_final_predictions_for_date(
    trade_date: date,
    raw_items: List[RawScoreItem],
    config: Optional[DecisionConfig] = None,
    knowledge_brain=None,
) -> List[DecisionOutput]:
    """為指定日期產生 Final Predictions（整合 Prediction Engine → Decision Layer）
    
    這個函式是 Prediction Engine 與 Decision Layer 的主要整合點。
    
    Args:
        trade_date: 交易日期
        raw_items: 從 Prediction Engine 取得的 RawScoreItem 列表
        config: DecisionConfig（如果為 None，使用預設配置）
        knowledge_brain: KnowledgeBrain 實例（如果為 None，會嘗試從 gateway 取得）
    
    Returns:
        DecisionOutput 列表（未排序，由呼叫方決定排序邏輯）
    
    Behavior:
        1. 從 Prediction Engine 取得指定日期的 RawScoreItem 列表（已由呼叫方提供）
        2. 初始化 DecisionEngineV1（如果 knowledge_brain 為 None，嘗試從 gateway 取得）
        3. 呼叫 DecisionEngineV1.decide_for_batch(...)
        4. 回傳 DecisionOutput 列表
        
        錯誤隔離：
        - 單一股票決策失敗不影響其他股票
        - 失敗的股票會 fallback：final_score = raw_score，空 doctrine_flags
    """
    if not raw_items:
        logger.warning(f"No raw items provided for date {trade_date}")
        return []
    
    # 使用預設配置（如果未提供）
    if config is None:
        config = DecisionConfig()
    
    # 取得 KnowledgeBrain（如果未提供）
    if knowledge_brain is None:
        try:
            from jgod.council_chamber.knowledge_gateway import get_knowledge_brain
            knowledge_brain = get_knowledge_brain()
            logger.debug("KnowledgeBrain loaded from gateway")
        except Exception as e:
            logger.warning(f"Failed to load KnowledgeBrain: {e}. Continuing without Doctrine.")
            knowledge_brain = None
    
    # 初始化 Decision Engine
    engine = DecisionEngineV1(config=config, knowledge_brain=knowledge_brain)
    
    # 批次處理 Raw Scores
    logger.info(f"Processing {len(raw_items)} raw items for date {trade_date}")
    batch_result = engine.decide_for_batch(raw_items)
    
    logger.info(f"Generated {len(batch_result.items)} final predictions for date {trade_date}")
    
    return batch_result.items

