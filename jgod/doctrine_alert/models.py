"""Doctrine Alert Data Models

Defines data structures for Doctrine alerts, rules, and contexts.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DoctrineAlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class DoctrineAlertSource(str, Enum):
    """Alert source types"""
    POSITION = "position"       # 持倉風險
    PREDICTION = "prediction"   # 預測 / Final Score 風險
    CONFLICT = "conflict"       # 多策略衝突風險
    ERROR = "error"             # 來自 ErrorLearningEngine 的紀錄 (預留)


class DoctrineRef(BaseModel):
    """Reference to Doctrine book/section/rule"""
    book_id: str  # e.g. "B01"
    section_id: str  # e.g. "S12"
    rule_id: Optional[str] = None  # e.g. "R03"


class DoctrineAlertItem(BaseModel):
    """Doctrine alert item (API DTO compatible)"""
    id: str
    symbol: str
    name: Optional[str] = None
    
    severity: DoctrineAlertSeverity
    source: DoctrineAlertSource
    
    title: str  # 短標題，例如：「單一持股過度集中」
    message: str  # 可閱讀說明
    
    metric_name: str  # 觸發指標名稱 e.g. "position_weight"
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    
    conflict_score: Optional[float] = None  # 若 source=CONFLICT 可帶
    consensus_score: Optional[float] = None  # 同上
    final_score: Optional[float] = None  # 若與 Decision Layer 有關
    raw_score: Optional[float] = None
    
    doctrine_refs: List[DoctrineRef] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)  # e.g. ["position", "concentration", "leverage"]
    created_at: datetime


class AlertContext(BaseModel):
    """Context for evaluating alert rules"""
    symbol: str
    name: Optional[str] = None
    position_weight: Optional[float] = None  # 持倉權重
    liquidity_score: Optional[float] = None  # 流動性分數
    final_score: Optional[float] = None
    raw_score: Optional[float] = None
    conflict_score: Optional[float] = None
    consensus_score: Optional[float] = None
    # 可擴充其他欄位


class RuleConfig(BaseModel):
    """Doctrine alert rule configuration"""
    id: str  # e.g. "POSITION_MAX_WEIGHT"
    enabled: bool
    severity: DoctrineAlertSeverity
    metric_name: str  # "position_weight", "conflict_score"...
    threshold: float  # 觸發門檻
    direction: str  # "gt" / "lt" / "ge" / "le" / "eq"
    doctrine_refs: List[DoctrineRef] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    source: DoctrineAlertSource

