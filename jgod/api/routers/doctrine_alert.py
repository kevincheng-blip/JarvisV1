"""Doctrine Alert API Router

Provides endpoints for Doctrine risk alerts.
"""

import logging
from typing import List, Optional, Literal

from fastapi import APIRouter, HTTPException, Query

from jgod.api.schemas.doctrine_alert import DoctrineAlertItem, DoctrineAlertSummary
from jgod.doctrine_alert.engine import DoctrineAlertEngineV1
from jgod.doctrine_alert.config import DoctrineAlertConfig, load_rule_configs
from jgod.doctrine_alert.models import DoctrineAlertSeverity, DoctrineAlertSource

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize engine (lazy-loaded)
_engine: Optional[DoctrineAlertEngineV1] = None


def _get_engine() -> DoctrineAlertEngineV1:
    """Get or create DoctrineAlertEngineV1 instance"""
    global _engine
    if _engine is None:
        rule_configs = load_rule_configs()
        config = DoctrineAlertConfig(rule_configs)
        _engine = DoctrineAlertEngineV1(config)
    return _engine


@router.get(
    "/alerts",
    response_model=List[DoctrineAlertItem],
    summary="Get Doctrine alerts",
    description="Retrieves Doctrine risk alerts for positions, predictions, and conflicts.",
)
async def get_doctrine_alerts(
    severity: Optional[Literal["info", "warning", "critical", "all"]] = Query(
        "all", description="Filter by severity"
    ),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    source: Optional[Literal["position", "prediction", "conflict", "error", "all"]] = Query(
        "all", description="Filter by source"
    ),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of alerts to return"),
) -> List[DoctrineAlertItem]:
    """
    Get Doctrine alerts.
    
    Returns list of DoctrineAlertItem objects filtered by severity, symbol, and source.
    """
    try:
        engine = _get_engine()
        
        # If symbol is provided, scan that symbol only
        if symbol:
            alerts = engine.scan_symbol(symbol)
        else:
            alerts = engine.scan_all(max_items=limit * 2)  # Get more, then filter
        
        # Filter by severity
        if severity and severity != "all":
            alerts = [a for a in alerts if a.severity.value == severity]
        
        # Filter by source
        if source and source != "all":
            alerts = [a for a in alerts if a.source.value == source]
        
        # Apply limit
        if len(alerts) > limit:
            alerts = alerts[:limit]
        
        logger.info(f"Returning {len(alerts)} Doctrine alerts (severity={severity}, symbol={symbol}, source={source})")
        return alerts
    
    except Exception as e:
        logger.error(f"Error getting Doctrine alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/alerts/summary",
    response_model=DoctrineAlertSummary,
    summary="Get Doctrine alerts summary",
    description="Returns summary statistics of Doctrine alerts.",
)
async def get_doctrine_alerts_summary() -> DoctrineAlertSummary:
    """
    Get Doctrine alerts summary.
    
    Returns summary statistics including counts by severity and source.
    """
    try:
        engine = _get_engine()
        alerts = engine.scan_all(max_items=1000)  # Get all for summary
        
        # Count by severity
        total_by_severity = {
            "critical": 0,
            "warning": 0,
            "info": 0,
        }
        for alert in alerts:
            severity = alert.severity.value
            total_by_severity[severity] = total_by_severity.get(severity, 0) + 1
        
        # Count by source
        total_by_source = {}
        for alert in alerts:
            source = alert.source.value
            total_by_source[source] = total_by_source.get(source, 0) + 1
        
        summary = DoctrineAlertSummary(
            total_by_severity=total_by_severity,
            total_by_source=total_by_source,
            total=len(alerts),
        )
        
        logger.info(f"Returning Doctrine alerts summary: {summary.total} total alerts")
        return summary
    
    except Exception as e:
        logger.error(f"Error getting Doctrine alerts summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

