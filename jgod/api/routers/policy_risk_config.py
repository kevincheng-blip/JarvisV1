# jgod/api/routers/policy_risk_config.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/policy", tags=["policy"])


@router.get("/risk-config/suggest")
def suggest_risk_config() -> Dict[str, Any]:
    """
    UI compatibility endpoint.
    MUST return 200 even if no suggestion logic yet.
    """
    return {
        "ok": True,
        "suggested": {
            # placeholders; UI can render or ignore
            "max_position_weight": 0.10,
            "max_gross_exposure": 1.00,
            "max_net_exposure": 0.30,
            "max_drawdown_limit": 0.10,
            "stop_loss_bps": 30,
        },
        "meta": {
            "version": "stub-v1",
            "generated_at": datetime.utcnow().isoformat(),
        },
    }

