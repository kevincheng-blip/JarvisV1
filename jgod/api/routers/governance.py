"""
Governance summary router (stubbed) for War Room Governance cards.
Always returns 200 with GovernanceSummary schema and is_stub flag.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter

from jgod.api.schemas.governance_summary import GovernanceSummary
from jgod.governance.assembler import assemble_governance_summary

router = APIRouter(prefix="/api/v1/governance", tags=["governance"])


@router.get("/summary")
def get_governance_summary():
    """
    Governance summary (Regime -> Drift -> Cluster -> Execution) with stubbed providers.
    Always 200. is_stub=True if any module is stub or drift unknown.
    """
    summary = assemble_governance_summary()
    return summary.model_dump()

