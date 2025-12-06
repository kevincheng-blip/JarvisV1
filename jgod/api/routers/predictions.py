"""
Prediction API Router

Endpoints for prediction snapshots (verdict, score, indicators).
"""

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

import yaml
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc

from jgod.storage.db import get_session
from jgod.storage.models import PredictionSnapshot, Stock

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for timeline endpoint
class PredictionTimelinePoint(BaseModel):
    """Single point in prediction timeline"""
    date: date
    score: float
    signal: str


class PredictionTimelineResponse(BaseModel):
    """Response for prediction timeline endpoint"""
    symbol: str
    start_date: date
    end_date: date
    points: List[PredictionTimelinePoint]


# Pydantic models for latest prediction endpoint
class LatestPrediction(BaseModel):
    """Latest prediction result for a symbol"""
    symbol: str
    date: date
    score: float
    signal: str
    positive_factors: List[str]
    negative_factors: List[str]
    risk_flags: List[str]


def load_universe(universe_file: str) -> List[dict]:
    """Load universe from YAML file"""
    file_path = Path(universe_file)
    if not file_path.exists():
        return []
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    return data.get("universe", [])


# --- Timeline endpoint FIRST (to avoid being swallowed by {date}/{symbol}) ---
@router.get("/predictions/timeline/{symbol}", response_model=PredictionTimelineResponse)
async def get_prediction_timeline(
    symbol: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    """
    Get prediction timeline for a specific symbol within a date range.
    
    Returns a time series of predictions (score, signal) for the symbol.
    Used by UI for trend analysis and historical prediction visualization.
    
    Example:
        GET /api/predictions/timeline/2330?start_date=2024-01-01&end_date=2024-12-31
    """
    # 手動解析日期，避免 FastAPI 將 symbol 誤判為日期
    try:
        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # 將變數名稱統一
    start_date = start_date_dt
    end_date = end_date_dt
    
    # Validate date range
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail=f"start_date ({start_date}) must be before or equal to end_date ({end_date})",
        )
    
    # Query predictions from DB
    session_gen = get_session()
    session = next(session_gen)
    try:
        predictions = (
            session.query(PredictionSnapshot)
            .filter(
                PredictionSnapshot.symbol == symbol,
                PredictionSnapshot.date >= start_date,
                PredictionSnapshot.date <= end_date,
            )
            .order_by(PredictionSnapshot.date.asc())
            .all()
        )
        
        # Map to timeline points
        points = []
        for pred in predictions:
            # Use score if available, fallback to total_score
            score_value = pred.score if pred.score is not None else (pred.total_score or 0.0)
            
            # Use signal if available, fallback to verdict
            signal_value = pred.signal if pred.signal is not None else (pred.verdict or "UNKNOWN")
            
            points.append(
                PredictionTimelinePoint(
                    date=pred.date,
                    score=score_value,
                    signal=signal_value,
                )
            )
        
        # Return response (empty list if no data, not 404)
        return PredictionTimelineResponse(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            points=points,
        )
        
    finally:
        session.close()


@router.get("/predictions/latest/{symbol}", response_model=LatestPrediction)
async def get_latest_prediction(
    symbol: str,
    date: Optional[str] = Query(default=None, description="As-of date (YYYY-MM-DD). If not provided, returns the latest available."),
):
    """
    Get the latest prediction result for a specific symbol.
    
    Returns the most recent prediction snapshot, including score, signal,
    positive/negative factors, and risk flags.
    
    Used by UI Signal Panel to display current prediction status.
    
    Example:
        GET /api/predictions/latest/2330
        GET /api/predictions/latest/2330?date=2024-12-01
    """
    session_gen = get_session()
    session = next(session_gen)
    try:
        query = session.query(PredictionSnapshot).filter(
            PredictionSnapshot.symbol == symbol
        )
        
        # If date is provided, filter by <= date
        if date:
            try:
                as_of_date = datetime.strptime(date, "%Y-%m-%d").date()
                query = query.filter(PredictionSnapshot.date <= as_of_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Get the latest prediction (by date desc)
        pred = query.order_by(desc(PredictionSnapshot.date)).first()
        
        if not pred:
            raise HTTPException(
                status_code=404,
                detail=f"No prediction found for symbol {symbol}",
            )
        
        # Extract score
        score_value = pred.score if pred.score is not None else (pred.total_score or 0.0)
        
        # Extract signal
        signal_value = pred.signal if pred.signal is not None else (pred.verdict or "UNKNOWN")
        
        # Extract positive factors
        positive_factors = []
        if pred.positive_factors_json:
            if isinstance(pred.positive_factors_json, list):
                positive_factors = [str(item) for item in pred.positive_factors_json]
            else:
                positive_factors = [str(pred.positive_factors_json)]
        elif pred.positive_indicators:
            if isinstance(pred.positive_indicators, list):
                positive_factors = [str(item) for item in pred.positive_indicators]
            elif isinstance(pred.positive_indicators, str):
                positive_factors = [item.strip() for item in pred.positive_indicators.split(",") if item.strip()]
        
        # Extract negative factors
        negative_factors = []
        if pred.negative_factors_json:
            if isinstance(pred.negative_factors_json, list):
                negative_factors = [str(item) for item in pred.negative_factors_json]
            else:
                negative_factors = [str(pred.negative_factors_json)]
        elif pred.negative_indicators:
            if isinstance(pred.negative_indicators, list):
                negative_factors = [str(item) for item in pred.negative_indicators]
            elif isinstance(pred.negative_indicators, str):
                negative_factors = [item.strip() for item in pred.negative_indicators.split(",") if item.strip()]
        
        # Extract risk flags
        risk_flags = []
        if pred.risk_flags_json:
            if isinstance(pred.risk_flags_json, list):
                risk_flags = [str(item) for item in pred.risk_flags_json]
            else:
                risk_flags = [str(pred.risk_flags_json)]
        
        return LatestPrediction(
            symbol=pred.symbol,
            date=pred.date,
            score=score_value,
            signal=signal_value,
            positive_factors=positive_factors,
            negative_factors=negative_factors,
            risk_flags=risk_flags,
        )
        
    finally:
        session.close()


# --- Existing dynamic routes below ---
@router.get("/predictions/{date}")
async def get_predictions_by_date(
    date: str,
    universe: Optional[str] = Query(default="tw_top50_2024", description="Universe name"),
):
    """
    Get predictions for all symbols in universe on a specific date.
    
    Used by UI A1 Watchlist Panel.
    """
    try:
        # Parse date
        as_of_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date}. Use YYYY-MM-DD")
    
    # Load universe
    universe_file = f"config/universe/{universe}.yaml"
    universe_data = load_universe(universe_file)
    
    if not universe_data:
        raise HTTPException(status_code=404, detail=f"Universe not found: {universe}")
    
    # Create symbol lookup
    symbol_to_info = {s["symbol"]: s for s in universe_data}
    
    # Query predictions from DB
    session_gen = get_session()
    session = next(session_gen)
    try:
        predictions = (
            session.query(PredictionSnapshot)
            .filter(PredictionSnapshot.date == as_of_date)
            .all()
        )
        
        # Build response
        result = []
        for pred in predictions:
            symbol = pred.symbol
            if symbol not in symbol_to_info:
                continue  # Skip symbols not in universe
            
            info = symbol_to_info[symbol]
            result.append({
                "symbol": symbol,
                "name_zh": info.get("name_zh"),
                "name_en": info.get("name_en"),
                "sector_zh": info.get("sector_zh"),
                "sector_en": info.get("sector_en"),
                "total_score": pred.total_score,
                "verdict": pred.verdict,
            })
        
        return result
        
    finally:
        session.close()


@router.get("/predictions/{date}/{symbol}")
async def get_prediction_by_symbol(
    date: str,
    symbol: str,
    include_payload: bool = Query(default=False, description="Include raw_payload"),
):
    """
    Get prediction snapshot for a specific symbol on a specific date.
    
    Returns:
        - total_score
        - verdict
        - positive_indicators
        - negative_indicators
        - raw_payload (optional)
    """
    try:
        as_of_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date}. Use YYYY-MM-DD")
    
    session_gen = get_session()
    session = next(session_gen)
    try:
        pred = (
            session.query(PredictionSnapshot)
            .filter(
                PredictionSnapshot.symbol == symbol,
                PredictionSnapshot.date == as_of_date,
            )
            .first()
        )
        
        if not pred:
            raise HTTPException(
                status_code=404,
                detail=f"Prediction not found for {symbol} on {date}",
            )
        
        result = {
            "symbol": pred.symbol,
            "date": pred.date.isoformat(),
            "total_score": pred.total_score,
            "verdict": pred.verdict,
            "positive_indicators": pred.positive_indicators or [],
            "negative_indicators": pred.negative_indicators or [],
        }
        
        if include_payload:
            result["raw_payload"] = pred.raw_payload
        
        return result
        
    finally:
        session.close()

