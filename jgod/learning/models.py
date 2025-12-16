"""
Learning Models: Data structures for Learning Layers

v0.6.8-A8: Models for Method/Thought/Strategy layers
v0.6.9-A9: Added quality_score, status enum, snapshot_id
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from datetime import datetime
from enum import Enum


class PatchStatus(str, Enum):
    """Patch status enum."""
    PENDING_APPROVAL = "PENDING_APPROVAL"
    AUTO_APPLY = "AUTO_APPLY"
    REJECTED = "REJECTED"


@dataclass
class FeatureSubset:
    """Feature subset recommendation from Method Layer."""
    date: str  # YYYY-MM-DD
    recommended_features: List[str]  # e.g., ["SMA_20", "RSI_14", ...]
    reason: str  # Traditional Chinese
    symbol: Optional[str] = None  # v0.6.10-A10: Optional for global scope
    evidence: Dict = field(default_factory=dict)  # P&L comparison, metrics
    quality_score: float = 0.0  # v0.6.9-A9: Quality score (0.0 ~ 1.0)
    status: PatchStatus = PatchStatus.PENDING_APPROVAL  # v0.6.9-A9: Status enum
    snapshot_id: str = ""  # v0.6.9-A9: Snapshot ID for consistency
    scope: str = "symbol"  # v0.6.10-A10: "symbol" or "global"
    target_symbols: List[str] = field(default_factory=list)  # v0.6.10-A10: For global scope


@dataclass
class TuningPatch:
    """Tuning patch suggestion from Thought Layer."""
    patch_id: str  # e.g., "TUNE-20240405-001"
    date: str  # YYYY-MM-DD
    symbol: str
    target: str  # "risk_mapping", "composite_weights", etc.
    changes: Dict  # Specific changes to apply
    reason: str  # Traditional Chinese
    evidence: Dict = field(default_factory=dict)  # pnl_delta, mdd_change, etc.
    quality_score: float = 0.0  # v0.6.9-A9: Quality score (0.0 ~ 1.0)
    status: PatchStatus = PatchStatus.PENDING_APPROVAL  # v0.6.9-A9: Status enum
    snapshot_id: str = ""  # v0.6.9-A9: Snapshot ID for consistency


@dataclass
class StrategyAllocation:
    """Strategy allocation recommendation from Strategy Layer."""
    date: str  # YYYY-MM-DD
    symbol: str
    recommended_primary_strategy: str
    reason: str  # Traditional Chinese
    recommended_secondary_strategies: List[str] = field(default_factory=list)
    evidence: Dict = field(default_factory=dict)  # Regime analysis, performance comparison
    quality_score: float = 0.0  # v0.6.9-A9: Quality score (0.0 ~ 1.0)
    status: PatchStatus = PatchStatus.PENDING_APPROVAL  # v0.6.9-A9: Status enum
    snapshot_id: str = ""  # v0.6.9-A9: Snapshot ID for consistency

