"""
Decision Layer v1 - Data Models

定義 Decision Layer 的輸入/輸出資料結構
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Dict, List


@dataclass
class RawScoreItem:
    """Raw Score 輸入（來自策略 / Prediction Engine）"""
    symbol: str
    name: Optional[str] = None
    date: date = field(default_factory=date.today)
    raw_score: float = 0.0
    strategy_scores: Dict[str, float] = field(default_factory=dict)  # e.g. {"S1_momentum": 0.85, "S2_value": 0.6}
    risk_metrics: Dict[str, float] = field(default_factory=dict)     # e.g. {"vol_20d": 0.3, "max_dd_60d": -0.12}
    context_tags: List[str] = field(default_factory=list)            # e.g. ["high_beta", "low_liquidity"]


@dataclass
class DoctrineFlag:
    """Doctrine 風險標籤（這一層產出的風險標籤）"""
    code: str          # e.g. "over_concentration", "chasing_high"
    severity: str      # "info" | "warning" | "critical"
    message: str       # 短說明（顯示在 War Room）
    doctrine_refs: List[str] = field(default_factory=list)  # e.g. ["Book_03#S12", "Book_08#R21"]


@dataclass
class DecisionOutput:
    """Decision Layer 回傳結果"""
    symbol: str
    date: date
    raw_score: float
    final_score: float
    correction_factor: float  # final_score = raw_score * correction_factor
    doctrine_flags: List[DoctrineFlag] = field(default_factory=list)
    adjustment_reason: str = ""    # 給人看的 summary
    llm_model: str = ""            # 用了哪個模型


@dataclass
class DecisionBatchResult:
    """批次處理結果（供 Policy Engine / API 使用）"""
    date: date
    items: List[DecisionOutput] = field(default_factory=list)


@dataclass
class LlmDecisionResponse:
    """LLM 回傳的決策響應（解析後）"""
    correction_factor: float
    doctrine_flags: List[Dict[str, any]]  # 原始 dict，稍後轉成 DoctrineFlag
    adjustment_reason: str


@dataclass
class DecisionContext:
    """決策上下文（內部使用）"""
    raw_item: RawScoreItem
    doctrine_hits: List[any] = field(default_factory=list)  # DoctrineHit 類型
    query_string: str = ""

