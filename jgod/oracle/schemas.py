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
    prophecy_id: str
    as_of_date: str  # YYYY-MM-DD
    t0: Dict = Field(default_factory=dict)  # {timestamp, baseline_price, baseline_source, symbol, universe}
    top_bucket: Literal["UP", "DOWN"]
    rank_in_bucket: int = Field(ge=1, le=50)
    resonance_tag: Literal["STRONG", "MIXED", "SHORT_SPIKE", "LONG_WAVE"]
    conflict_score: float = Field(ge=0.0, le=1.0)
    forecast_matrix: Dict[str, ForecastHorizon] = Field(default_factory=dict)  # T1, T5, T10, T20, TM
    decision_footprint: DecisionFootprint = Field(default_factory=DecisionFootprint)
    versions: Dict[str, str] = Field(default_factory=dict)  # oracle_core_version, toolset_version, etc.
    immutable_hash: str  # sha256 of canonical JSON


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
    horizon: Literal["T1", "T5", "T10", "T20", "TM"]
    pred: Dict = Field(default_factory=dict)  # {direction, target_return, star}
    truth: TruthData
    metrics: Dict = Field(default_factory=dict)  # {hit_direction, abs_error, signed_error}
    context: Dict = Field(default_factory=dict)  # {regime, drift_status, cluster_risk, execution_confidence}
    attribution_stub: Dict = Field(default_factory=dict)  # {primary_driver, notes}
