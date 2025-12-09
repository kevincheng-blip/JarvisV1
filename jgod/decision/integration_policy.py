"""
Decision Layer v1 - Integration Functions

與 Policy / Prediction Engine 整合的函式
"""

import logging
from typing import List

from jgod.decision.models import RawScoreItem, DecisionOutput
from jgod.decision.engine import DecisionEngineV1

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

