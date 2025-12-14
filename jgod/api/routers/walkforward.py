"""
Walk-Forward API Router

v0.6.8-A8: Walk-Forward Runner API endpoints
v0.6.9-A9: Added notifications and shadow run endpoints
"""

import logging
from fastapi import APIRouter, Query, Body
from typing import List, Optional

from jgod.research.walkforward_runner import WalkForwardRunner
from jgod.research.storage import list_notifications, latest_notification, latest_portfolio_report, list_portfolio_logs
from jgod.api.schemas.walkforward_notifications import (
    NotificationSchema,
    NotificationListSchema,
    ShadowReportSchema,
)
from jgod.api.schemas.portfolio import (
    PortfolioRunRequestSchema,
    PortfolioReportSchema,
    PortfolioLogListSchema,
)
from jgod.strategy.portfolio_manager import PortfolioManager
from jgod.strategy.models import PortfolioConfig

logger = logging.getLogger(__name__)

router = APIRouter(tags=["walkforward"])


@router.post("/run-daily/{symbol}")
async def run_daily_cycle(
    symbol: str,
    date: str = Query(..., description="Date string (YYYY-MM-DD)"),
    doctrine_version: str = Query("v1.0", description="Doctrine version"),
    feature_version: str = Query("v1.0", description="Feature version"),
    feature_lookback: int = Query(60, ge=10, le=200, description="Feature lookback days"),
) -> dict:
    """
    Run daily walkforward cycle for a symbol.
    
    Strictly uses only T-1 data (no future data leakage).
    """
    runner = WalkForwardRunner(use_mock_mdts=False)
    
    try:
        result = runner.run_daily_cycle(
            symbol=symbol,
            date_str=date,
            doctrine_version=doctrine_version,
            feature_version=feature_version,
            feature_lookback=feature_lookback,
        )
        return result
    except Exception as e:
        logger.error(f"Failed to run daily cycle for {symbol} on {date}: {e}", exc_info=True)
        return {
            "symbol": symbol,
            "date": date,
            "error": str(e),
        }


@router.post("/run-range/{symbol}")
async def run_range(
    symbol: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    doctrine_version: str = Query("v1.0", description="Doctrine version"),
    feature_version: str = Query("v1.0", description="Feature version"),
    feature_lookback: int = Query(60, ge=10, le=200, description="Feature lookback days"),
) -> dict:
    """
    Run walkforward for a date range.
    
    Returns list of daily log entries.
    """
    runner = WalkForwardRunner(use_mock_mdts=False)
    
    try:
        results = runner.run_range(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            doctrine_version=doctrine_version,
            feature_version=feature_version,
            feature_lookback=feature_lookback,
        )
        return {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "total_days": len(results),
            "logs": results,
        }
    except Exception as e:
        logger.error(f"Failed to run range for {symbol}: {e}", exc_info=True)
        return {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "error": str(e),
            "logs": [],
        }


@router.get("/notifications/latest", response_model=NotificationSchema)
async def get_latest_notification() -> dict:
    """
    Get latest notification.
    
    Always returns 200 (empty state if no notifications).
    """
    notification = latest_notification()
    if notification is None:
        return {
            "event": "NO_DATA",
            "layer": "",
            "snapshot_id": "",
            "symbol": "",
            "date": "",
            "created_at": "",
        }
    return notification


@router.get("/notifications/list", response_model=NotificationListSchema)
async def list_notifications_endpoint(
    n: int = Query(50, ge=1, le=200, description="Number of notifications to return")
) -> dict:
    """
    List latest N notifications.
    
    Always returns 200 (empty list if no notifications).
    """
    notifications = list_notifications(n=n)
    return {
        "notifications": notifications,
        "total": len(notifications),
    }


@router.post("/shadow/run/{symbol}", response_model=ShadowReportSchema)
async def run_shadow(
    symbol: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    autopilot: bool = Query(True, description="Enable autopilot"),
    baseline_mode: str = Query("static", description="Baseline mode"),
) -> dict:
    """
    Run shadow test comparing autopilot vs baseline.
    
    Returns shadow report with P&L comparison.
    """
    runner = WalkForwardRunner(use_mock_mdts=False)
    
    try:
        report = runner.run_shadow(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            baseline_mode=baseline_mode,
            autopilot_enabled=autopilot,
        )
        return report
    except Exception as e:
        logger.error(f"Failed to run shadow test for {symbol}: {e}", exc_info=True)
        return {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "error": str(e),
        }


@router.post("/portfolio/run", response_model=dict)
async def run_portfolio(
    request: PortfolioRunRequestSchema,
) -> dict:
    """
    Run portfolio walkforward for multiple symbols.
    
    Always returns 200 (with error field if failed).
    """
    manager = PortfolioManager(
        portfolio_autopilot_enabled=request.autopilot_enabled,
        portfolio_time_sync_check_enabled=True,
        portfolio_parallel_enabled=False,
    )
    
    config = PortfolioConfig(
        symbols=request.symbols,
        initial_cash_total=request.initial_cash_total,
        allocation_mode=request.allocation_mode,
        doctrine_version=request.doctrine_version,
        feature_version=request.feature_version,
    )
    
    try:
        portfolio_logs = manager.run_portfolio_walkforward(
            config=config,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        
        # Get latest report
        latest = latest_portfolio_report()
        
        return {
            "success": True,
            "symbols": request.symbols,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "total_days": len(portfolio_logs),
            "latest_report": latest,
        }
    except Exception as e:
        logger.error(f"Failed to run portfolio: {e}", exc_info=True)
        return {
            "success": False,
            "symbols": request.symbols,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "error": str(e),
            "latest_report": latest_portfolio_report(),
        }


@router.get("/portfolio/latest", response_model=PortfolioReportSchema)
async def get_latest_portfolio_report() -> dict:
    """
    Get latest portfolio report.
    
    Always returns 200 (empty state if no data).
    """
    report = latest_portfolio_report()
    return report


@router.get("/portfolio/list", response_model=PortfolioLogListSchema)
async def list_portfolio_logs_endpoint(
    n: int = Query(20, ge=1, le=200, description="Number of logs to return")
) -> dict:
    """
    List latest N portfolio logs.
    
    Always returns 200 (empty list if no data).
    """
    logs = list_portfolio_logs(n=n)
    return {
        "logs": logs,
        "total": len(logs),
    }

