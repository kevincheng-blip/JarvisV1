"""
OR-OS V1 Schemas (Pydantic models).
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ForecastHorizon(BaseModel):
    """Single horizon forecast."""
    direction: Literal["UP", "DOWN", "SIDE"]
    target_return: float  # Predicted return percentage
    star: int = Field(ge=1, le=5)  # 1-5 star rating
    confidence: Literal["LOW", "MED", "HIGH"] = "MED"


class DecisionFootprint(BaseModel):
    """Decision footprint snapshot (MVP)."""
    B: Optional[Dict] = Field(default_factory=dict)  # {"raw_score": float, "signals_used": [...]}
    C: Optional[Dict] = Field(default_factory=dict)  # {"tags": [...], "blocked": bool, "reasons": [...]}
    D: Optional[Dict] = Field(default_factory=dict)  # {"event_tags": [...], "impact_vector": {...}}
    A: Optional[Dict] = Field(default_factory=dict)  # {"mutual_answer_summary": str, "key_conflicts": [...]}


class Prophecy(BaseModel):
    """Prophecy Archive entry (immutable)."""
    schema_version: str = "or-os.v1"
    prophecy_id: str  # Deterministic SHA256 (64 hex)
    as_of_date: str  # YYYY-MM-DD
    symbol: str  # Normalized from t0 (backward compat)
    universe: str = "TOP50"  # Normalized from t0 (backward compat)
    t0: Dict = Field(default_factory=dict)  # {timestamp, baseline_price, baseline_source}
    top_bucket: Literal["UP", "DOWN"]
    rank_in_bucket: int = Field(ge=1, le=50)
    resonance_tag: Literal["STRONG", "MIXED", "SHORT_SPIKE", "LONG_WAVE"]
    conflict_score: float = Field(ge=0.0, le=1.0)
    forecast_matrix: Dict[str, ForecastHorizon] = Field(default_factory=dict)  # T1, T5, T10, T20, TM
    decision_footprint: DecisionFootprint = Field(default_factory=DecisionFootprint)
    versions: Dict[str, str] = Field(default_factory=dict)  # oracle_core_version, toolset_version, etc.
    immutable_hash: str  # sha256 of canonical JSON
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Load Prophecy with backward compat for t0.symbol/universe."""
        # Normalize: if t0 has symbol/universe, move to top level
        t0 = data.get("t0", {})
        if "symbol" in t0 and "symbol" not in data:
            data["symbol"] = t0.pop("symbol")
        if "universe" in t0 and "universe" not in data:
            data["universe"] = t0.pop("universe")
        return cls(**data)


class TruthData(BaseModel):
    """Truth data for scoring."""
    tN_date: str  # YYYY-MM-DD
    tN_price: float
    realized_return: float  # (tN_price - t0_price) / t0_price * 100


class ScorecardRow(BaseModel):
    """Oracle Scorecard entry."""
    schema_version: str = "or-os.v1"
    score_id: str
    prophecy_id: str
    as_of_date: str
    symbol: str
    top_bucket: Literal["UP", "DOWN"]
    rank_in_bucket: int
    horizon: Literal["T1", "T5", "T10", "T20", "TM"]
    baseline_price: float
    baseline_source: str  # "sqlite"|"stub"|"none"
    truth_price: float
    truth_source: str  # "sqlite"|"stub"|"none"
    pred_direction: Literal["UP", "DOWN", "SIDE"]
    pred_target_return: float  # Percentage
    pred_star: int
    pred_confidence: Literal["LOW", "MED", "HIGH"]
    realized_return: float  # Percentage
    hit_direction: bool
    abs_error: float
    signed_error: float
    context: Dict = Field(default_factory=dict)  # {regime_status, cluster_status, drift_status}
    explain: Dict = Field(default_factory=dict)  # {truth_date_used, baseline_date_used, ...}
    attribution_stub: Dict = Field(default_factory=dict)  # {primary_driver, notes}
