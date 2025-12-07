"""
Universe & Coverage API Router

Endpoints for universe coverage and data availability status.
"""

import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from jgod.storage.db import get_session
from jgod.storage.models import IndicatorSnapshot, PredictionSnapshot, Stock, DailyBar

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db():
    """FastAPI dependency for database session."""
    session_gen = get_session()
    session = next(session_gen)
    try:
        yield session
    finally:
        session.close()


def load_universe(universe_file: str) -> List[dict]:
    """Load universe from YAML file"""
    file_path = Path(universe_file)
    if not file_path.exists():
        return []
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    return data.get("universe", [])


# --- Response Schemas --------------------------------------------------------

class CoverageItem(BaseModel):
    symbol: str
    name: str
    bar_days: int
    indicator_days: int
    coverage: float  # 0~1 之間


class CoverageSummary(BaseModel):
    start_date: date
    end_date: date
    total_symbols: int
    completed_symbols: int
    average_coverage: float
    items: List[CoverageItem]


# --- Helper ------------------------------------------------------------------

def _compute_coverage(
    session: Session,
    start_date: date,
    end_date: date,
) -> List[CoverageItem]:
    """Compute coverage statistics for all stocks."""
    # 1) 所有股票
    stocks = (
        session.query(Stock)
        .order_by(Stock.symbol.asc())
        .all()
    )

    # 2) daily_bars -> bar_days
    bar_subq = (
        session.query(
            DailyBar.symbol.label("symbol"),
            func.count().label("bar_days"),
        )
        .filter(
            DailyBar.date >= start_date,
            DailyBar.date <= end_date,
        )
        .group_by(DailyBar.symbol)
        .subquery()
    )

    # 3) indicator_snapshots -> indicator_days
    ind_subq = (
        session.query(
            IndicatorSnapshot.symbol.label("symbol"),
            func.count(func.distinct(IndicatorSnapshot.date)).label(
                "indicator_days"
            ),
        )
        .filter(
            IndicatorSnapshot.date >= start_date,
            IndicatorSnapshot.date <= end_date,
        )
        .group_by(IndicatorSnapshot.symbol)
        .subquery()
    )

    rows = (
        session.query(
            Stock.symbol,
            Stock.name_zh,
            func.coalesce(bar_subq.c.bar_days, 0).label("bar_days"),
            func.coalesce(ind_subq.c.indicator_days, 0).label("indicator_days"),
        )
        .outerjoin(bar_subq, bar_subq.c.symbol == Stock.symbol)
        .outerjoin(ind_subq, ind_subq.c.symbol == Stock.symbol)
        .order_by(Stock.symbol.asc())
        .all()
    )

    items: List[CoverageItem] = []
    for symbol, name, bar_days, indicator_days in rows:
        bar_days = int(bar_days or 0)
        indicator_days = int(indicator_days or 0)
        if bar_days > 0:
            coverage = float(indicator_days) / float(bar_days)
        else:
            coverage = 0.0

        items.append(
            CoverageItem(
                symbol=symbol,
                name=name or "",
                bar_days=bar_days,
                indicator_days=indicator_days,
                coverage=coverage,
            )
        )
    return items


def generate_date_range(start_date: date, end_date: date) -> List[date]:
    """Generate list of trading dates"""
    dates = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Skip weekends
            dates.append(current)
        current += timedelta(days=1)
    return dates


# --- API Endpoints -----------------------------------------------------------

@router.get("/universe/coverage", response_model=CoverageSummary)
async def get_universe_coverage(
    start_date: date = Query(..., description="起始日期 YYYY-MM-DD"),
    end_date: date = Query(..., description="結束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    回傳指定日期區間內，所有股票的指標覆蓋率狀況。
    
    給前端 E1「Coverage Heatmap」面板使用。
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    items = _compute_coverage(db, start_date, end_date)
    total = len(items)
    if total == 0:
        return CoverageSummary(
            start_date=start_date,
            end_date=end_date,
            total_symbols=0,
            completed_symbols=0,
            average_coverage=0.0,
            items=[],
        )

    completed = sum(1 for i in items if i.coverage >= 0.999)
    avg_cov = sum(i.coverage for i in items) / total

    return CoverageSummary(
        start_date=start_date,
        end_date=end_date,
        total_symbols=total,
        completed_symbols=completed,
        average_coverage=avg_cov,
        items=items,
    )


@router.get("/universe/coverage-detail")
async def get_universe_coverage_detail(
    universe: Optional[str] = Query(default="tw_top50_2024", description="Universe name"),
    from_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
):
    """
    Get coverage status for universe symbols (legacy endpoint).
    
    Used by UI E1 Coverage Heatmap Panel.
    """
    # Load universe
    universe_file = f"config/universe/{universe}.yaml"
    universe_data = load_universe(universe_file)
    
    if not universe_data:
        raise HTTPException(status_code=404, detail=f"Universe not found: {universe}")
    
    symbols = [s["symbol"] for s in universe_data]
    
    # Parse date range (default: last 30 days)
    if from_date and to_date:
        try:
            start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        # Default: last 30 trading days
        end_date = date.today()
        start_date = end_date - timedelta(days=45)  # ~30 trading days
    
    dates = generate_date_range(start_date, end_date)
    date_strings = [d.isoformat() for d in dates]
    
    # Query coverage from DB
    session_gen = get_session()
    session = next(session_gen)
    try:
        coverage = []
        
        for symbol in symbols:
            for d in dates:
                # Check indicators
                indicator_count = (
                    session.query(IndicatorSnapshot)
                    .filter(
                        IndicatorSnapshot.symbol == symbol,
                        IndicatorSnapshot.date == d,
                    )
                    .count()
                )
                
                # Check prediction
                has_prediction = (
                    session.query(PredictionSnapshot)
                    .filter(
                        PredictionSnapshot.symbol == symbol,
                        PredictionSnapshot.date == d,
                    )
                    .first()
                    is not None
                )
                
                # Determine status
                if indicator_count >= 90 and has_prediction:  # ~90% indicators + prediction
                    status = "full"
                elif indicator_count > 0:
                    status = "partial"
                else:
                    status = "missing"
                
                coverage.append({
                    "symbol": symbol,
                    "date": d.isoformat(),
                    "status": status,
                    "indicator_count": indicator_count,
                    "has_prediction": has_prediction,
                })
        
        return {
            "symbols": symbols,
            "dates": date_strings,
            "coverage": coverage,
        }
        
    finally:
        session.close()
