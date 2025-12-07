"""
Indicators API Router

Endpoints for 100-indicator snapshots.
"""

from datetime import date, datetime
from typing import List

from fastapi import APIRouter, HTTPException

from jgod.storage.db import get_session
from jgod.storage.models import IndicatorSnapshot

router = APIRouter()


@router.get("/indicators/{symbol}/{date}")
async def get_indicators_by_symbol_date(
    symbol: str,
    date: str,
):
    """
    Get 100-indicator snapshot for a symbol on a specific date.
    
    Used by UI B1 Indicator Radar/Heatmap.
    
    Returns:
        - symbol
        - date
        - indicators: list of indicator objects
    """
    try:
        as_of_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date}. Use YYYY-MM-DD")
    
    session_gen = get_session()
    session = next(session_gen)
    try:
        snapshots = (
            session.query(IndicatorSnapshot)
            .filter(
                IndicatorSnapshot.symbol == symbol,
                IndicatorSnapshot.date == as_of_date,
            )
            .all()
        )
        
        if not snapshots:
            raise HTTPException(
                status_code=404,
                detail=f"Indicators not found for {symbol} on {date}",
            )
        
        indicators = [
            {
                "indicator_code": snap.indicator_code,
                "category": snap.category,
                "raw_value": snap.raw_value,
                "normalized_value": snap.normalized_value,
                "weight": snap.weight,
                "status": snap.status,
            }
            for snap in snapshots
        ]
        
        return {
            "symbol": symbol,
            "date": date,
            "indicators": indicators,
        }
        
    finally:
        session.close()

