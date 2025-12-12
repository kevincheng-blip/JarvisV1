"""Doctrine Alert Data Access Layer

Functions to retrieve positions, predictions, and conflicts for alert scanning.
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Dict

from jgod.storage.db import get_session
from jgod.storage.models import PredictionSnapshot, Stock, PortfolioSnapshot
from jgod.signal_aggregation.models import ConflictItem
from jgod.signal_aggregation.engine import SignalAggregationEngineV1

logger = logging.getLogger(__name__)


@dataclass
class PositionRow:
    """Position row data structure"""
    symbol: str
    name: Optional[str] = None
    weight: float = 0.0  # Portfolio weight
    quantity: int = 0
    avg_price: float = 0.0
    current_price: float = 0.0
    liquidity_score: Optional[float] = None


@dataclass
class PredictionRow:
    """Prediction row data structure"""
    symbol: str
    date: date
    name: Optional[str] = None
    raw_score: Optional[float] = None
    final_score: Optional[float] = None
    signal: Optional[str] = None


def get_current_positions(db_session=None) -> List[PositionRow]:
    """
    Get current portfolio positions.
    
    Args:
        db_session: SQLAlchemy session (optional)
    
    Returns:
        List of PositionRow objects
    """
    if db_session is None:
        session_gen = get_session()
        db_session = next(session_gen)
    
    try:
        # Get latest portfolio snapshot
        # Note: In v1, we'll get from the most recent PortfolioSnapshot or Path A state
        # For now, we'll try to get from PortfolioSnapshot or return empty list
        
        latest_snapshot = db_session.query(PortfolioSnapshot).order_by(
            PortfolioSnapshot.snapshot_time.desc()
        ).first()
        
        if not latest_snapshot:
            logger.info("No portfolio snapshot found, returning empty positions")
            return []
        
        # For v1, we'll return empty positions if we can't get detailed position data
        # Future: Query from a positions table or reconstruct from VirtualTrade
        
        # Placeholder: Return empty list for now
        # In production, this would query actual position data
        logger.info("Current positions retrieval is a placeholder in v1")
        return []
    
    except Exception as e:
        logger.error(f"Error retrieving current positions: {e}", exc_info=True)
        return []


def get_latest_predictions(limit: Optional[int] = None, db_session=None) -> List[PredictionRow]:
    """
    Get latest predictions with final scores.
    
    Args:
        limit: Maximum number of predictions to return
        db_session: SQLAlchemy session (optional)
    
    Returns:
        List of PredictionRow objects
    """
    if db_session is None:
        session_gen = get_session()
        db_session = next(session_gen)
    
    try:
        # Get latest prediction snapshots
        query = db_session.query(PredictionSnapshot).order_by(
            PredictionSnapshot.date.desc(),
            PredictionSnapshot.created_at.desc()
        )
        
        if limit:
            query = query.limit(limit)
        
        predictions = query.all()
        
        if not predictions:
            logger.info("No predictions found")
            return []
        
        # Get latest date
        latest_date = max(pred.date for pred in predictions)
        latest_predictions = [p for p in predictions if p.date == latest_date]
        
        # Get stock names
        symbols = [p.symbol for p in latest_predictions]
        stocks = db_session.query(Stock).filter(Stock.symbol.in_(symbols)).all()
        name_map = {stock.symbol: (stock.name_zh or stock.name_en or stock.symbol) for stock in stocks}
        
        # Convert to PredictionRow
        rows = []
        for pred in latest_predictions:
            rows.append(PredictionRow(
                symbol=pred.symbol,
                name=name_map.get(pred.symbol, pred.symbol),
                date=pred.date,
                raw_score=pred.score or pred.total_score,
                final_score=None,  # Future: Get from DecisionOutput table
                signal=pred.signal or pred.verdict,
            ))
        
        logger.info(f"Retrieved {len(rows)} latest predictions for date {latest_date}")
        return rows
    
    except Exception as e:
        logger.error(f"Error retrieving latest predictions: {e}", exc_info=True)
        return []


def get_conflicts_for_symbols(
    symbols: List[str],
    trade_date: Optional[date] = None,
    db_session=None,
) -> Dict[str, ConflictItem]:
    """
    Get conflict data for specified symbols.
    
    Args:
        symbols: List of stock symbols
        trade_date: Target date (default: latest available)
        db_session: SQLAlchemy session (optional)
    
    Returns:
        Dictionary mapping symbol to ConflictItem
    """
    if not symbols:
        return {}
    
    try:
        # Use Signal Aggregation Engine to get conflicts
        engine = SignalAggregationEngineV1(db_session=db_session)
        
        if trade_date is None:
            trade_date = date.today()
        
        # Get all conflicts for the date
        all_conflicts = engine.get_conflicts_for_date(
            trade_date=trade_date,
            limit=None,  # Get all
            side="all",
            db_session=db_session,
        )
        
        # Filter by symbols
        conflict_dict = {
            conflict.symbol: conflict
            for conflict in all_conflicts
            if conflict.symbol in symbols
        }
        
        logger.info(f"Retrieved conflicts for {len(conflict_dict)}/{len(symbols)} symbols")
        return conflict_dict
    
    except Exception as e:
        logger.error(f"Error retrieving conflicts: {e}", exc_info=True)
        return {}

