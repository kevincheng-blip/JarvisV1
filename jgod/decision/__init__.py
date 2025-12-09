"""
J-GOD Decision Layer v1

Raw Score → Final Score（Doctrine 仲裁層）

主要組件：
- DecisionEngineV1: 核心決策引擎
- RawScoreItem: Raw Score 輸入
- DecisionOutput: Final Score 輸出
- generate_final_predictions: 整合函式
"""

from jgod.decision.models import (
    RawScoreItem,
    DecisionOutput,
    DecisionBatchResult,
    DoctrineFlag,
)
from jgod.decision.config import DecisionConfig
from jgod.decision.engine import DecisionEngineV1
from jgod.decision.integration_policy import (
    generate_final_predictions,
    convert_to_top_n_items,
)

__all__ = [
    # Models
    "RawScoreItem",
    "DecisionOutput",
    "DecisionBatchResult",
    "DoctrineFlag",
    # Config
    "DecisionConfig",
    # Engine
    "DecisionEngineV1",
    # Integration
    "generate_final_predictions",
    "convert_to_top_n_items",
]
