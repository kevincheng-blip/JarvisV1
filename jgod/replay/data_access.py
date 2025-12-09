"""Data Access Layer for Error Replay Engine

Functions to load error events, price data, factor data, and trade records
from various sources (JSONL, database, etc.).
"""

import json
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

from jgod.replay.models import PricePoint, FactorPoint, TradePoint
from jgod.learning.error_event import ErrorEvent, ErrorAnalysisResult

logger = logging.getLogger(__name__)


class ReplayNotFoundError(Exception):
    """Raised when an error event cannot be found for replay"""
    pass


def _load_error_event(error_id: str, error_reports_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load error event from JSONL file
    
    Args:
        error_id: Unique identifier for the error event
        error_reports_path: Path to error_reports.jsonl (default: data/error_learning/error_reports.jsonl)
    
    Returns:
        Dictionary containing error event and analysis data
    
    Raises:
        ReplayNotFoundError: If error event not found
    """
    if error_reports_path is None:
        project_root = Path(__file__).parent.parent.parent
        error_reports_path = project_root / "data" / "error_learning" / "error_reports.jsonl"
    
    error_reports_path = Path(error_reports_path)
    
    if not error_reports_path.exists():
        raise ReplayNotFoundError(f"Error reports file not found: {error_reports_path}")
    
    # Read JSONL and search for matching error_id
    with open(error_reports_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                
                # Check if this record matches the error_id
                # error_id might be in "id" field or constructed from other fields
                record_id = record.get("id")
                
                # If no explicit id, try to construct one from timestamp + symbol
                if not record_id:
                    timestamp_str = record.get("timestamp", "")
                    symbol = record.get("symbol", "")
                    if timestamp_str and symbol:
                        # Simple hash-like construction
                        record_id = f"{symbol}_{timestamp_str}"
                
                if record_id == error_id or record.get("error_id") == error_id:
                    logger.info(f"Found error event {error_id} at line {line_num}")
                    return record
            
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse line {line_num} in {error_reports_path}: {e}")
                continue
    
    raise ReplayNotFoundError(f"Error event {error_id} not found in {error_reports_path}")


def _load_price_series(
    symbol: str,
    target_date: date,
    db_session=None,
    days_before: int = 1,
    days_after: int = 1
) -> List[PricePoint]:
    """Load price series (daily bars) from database
    
    Args:
        symbol: Stock symbol (e.g., "2330")
        target_date: Target date for the error
        db_session: SQLAlchemy database session (optional)
        days_before: Number of days before target_date to include
        days_after: Number of days after target_date to include
    
    Returns:
        List of PricePoint objects
    """
    price_points = []
    
    if db_session is None:
        logger.warning(f"Database session not available, returning empty price series for {symbol}")
        return price_points
    
    try:
        from jgod.storage.models import DailyBar
        
        start_date = target_date - timedelta(days=days_before)
        end_date = target_date + timedelta(days=days_after)
        
        bars = db_session.query(DailyBar).filter(
            DailyBar.symbol == symbol,
            DailyBar.date >= start_date,
            DailyBar.date <= end_date
        ).order_by(DailyBar.date.asc()).all()
        
        for bar in bars:
            # Convert date to datetime (assume market open time 09:00:00)
            ts = datetime.combine(bar.date, datetime.min.time().replace(hour=9, minute=0))
            
            price_points.append(PricePoint(
                ts=ts,
                open=bar.open or 0.0,
                high=bar.high or 0.0,
                low=bar.low or 0.0,
                close=bar.close or 0.0,
                volume=bar.volume or 0.0
            ))
        
        logger.info(f"Loaded {len(price_points)} price points for {symbol} from {start_date} to {end_date}")
    
    except ImportError:
        logger.warning("DailyBar model not found, trying alternative data source (tw_stock_daily)")
        # Fallback to legacy SQLite database
        try:
            from jgod.data.db import get_connection
            
            conn = get_connection()
            cursor = conn.cursor()
            
            start_date_str = (target_date - timedelta(days=days_before)).strftime("%Y-%m-%d")
            end_date_str = (target_date + timedelta(days=days_after)).strftime("%Y-%m-%d")
            
            cursor.execute("""
                SELECT trade_date, open, high, low, close, volume
                FROM tw_stock_daily
                WHERE stock_id = ? AND trade_date >= ? AND trade_date <= ?
                ORDER BY trade_date ASC
            """, (symbol, start_date_str, end_date_str))
            
            rows = cursor.fetchall()
            
            for row in rows:
                trade_date_str, open_p, high_p, low_p, close_p, volume = row
                try:
                    trade_date = datetime.strptime(trade_date_str, "%Y-%m-%d").date()
                    ts = datetime.combine(trade_date, datetime.min.time().replace(hour=9, minute=0))
                    
                    price_points.append(PricePoint(
                        ts=ts,
                        open=open_p or 0.0,
                        high=high_p or 0.0,
                        low=low_p or 0.0,
                        close=close_p or 0.0,
                        volume=volume or 0.0
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse date {trade_date_str}: {e}")
                    continue
            
            cursor.close()
            conn.close()
            
            logger.info(f"Loaded {len(price_points)} price points from legacy DB for {symbol}")
        
        except Exception as e:
            logger.error(f"Failed to load price series from legacy DB: {e}", exc_info=True)
    
    except Exception as e:
        logger.error(f"Error loading price series: {e}", exc_info=True)
    
    return price_points


def _load_factor_series(
    symbol: str,
    target_date: date,
    db_session=None
) -> List[FactorPoint]:
    """Load factor/scores series from database
    
    Args:
        symbol: Stock symbol
        target_date: Target date for the error
        db_session: SQLAlchemy database session (optional)
    
    Returns:
        List of FactorPoint objects
    """
    factor_points = []
    
    if db_session is None:
        logger.warning(f"Database session not available, returning empty factor series for {symbol}")
        return factor_points
    
    try:
        from jgod.storage.models import PredictionSnapshot, IndicatorSnapshot
        
        # Get prediction snapshot for the date
        prediction = db_session.query(PredictionSnapshot).filter(
            PredictionSnapshot.symbol == symbol,
            PredictionSnapshot.date == target_date
        ).first()
        
        if prediction:
            ts = datetime.combine(target_date, datetime.min.time().replace(hour=9, minute=0))
            
            factor_values = {}
            
            # Try to extract key factors from indicator snapshots
            # Select a few important indicators (e.g., momentum, volatility, liquidity)
            key_indicators = ["M01", "M02", "M03", "P01", "P02"]  # Example indicator codes
            
            indicators = db_session.query(IndicatorSnapshot).filter(
                IndicatorSnapshot.symbol == symbol,
                IndicatorSnapshot.date == target_date,
                IndicatorSnapshot.indicator_code.in_(key_indicators)
            ).all()
            
            for ind in indicators:
                if ind.normalized_value is not None:
                    factor_values[ind.indicator_code] = ind.normalized_value
            
            # Get raw_score and final_score from prediction
            raw_score = prediction.score or prediction.total_score or None
            
            # Note: final_score might not be stored in PredictionSnapshot yet
            # We'll use raw_score as both for now
            final_score = raw_score
            
            factor_points.append(FactorPoint(
                ts=ts,
                raw_score=raw_score,
                final_score=final_score,
                factor_values=factor_values
            ))
        
        logger.info(f"Loaded {len(factor_points)} factor points for {symbol} on {target_date}")
    
    except ImportError as e:
        logger.warning(f"Database models not available: {e}")
    except Exception as e:
        logger.error(f"Error loading factor series: {e}", exc_info=True)
    
    return factor_points


def _load_trades(
    symbol: str,
    target_date: date,
    db_session=None
) -> List[TradePoint]:
    """Load trade records for the symbol and date
    
    Args:
        symbol: Stock symbol
        target_date: Target date for the error
        db_session: SQLAlchemy database session (optional)
    
    Returns:
        List of TradePoint objects
    """
    trade_points = []
    
    try:
        from jgod.storage.models import VirtualTrade
        
        if db_session:
            # Query VirtualTrade table
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            trades = db_session.query(VirtualTrade).filter(
                VirtualTrade.symbol == symbol,
                VirtualTrade.open_datetime >= start_datetime,
                VirtualTrade.open_datetime <= end_datetime
            ).all()
            
            for trade in trades:
                action = "BUY" if trade.side == "LONG" else "SELL"
                trade_points.append(TradePoint(
                    ts=trade.open_datetime,
                    action=action,
                    price=trade.open_price,
                    quantity=trade.quantity
                ))
        else:
            # Fallback to legacy TradeRecorder database
            try:
                from jgod.execution.trade_recorder import TradeRecorder
                
                start_datetime = datetime.combine(target_date, datetime.min.time())
                end_datetime = datetime.combine(target_date, datetime.max.time())
                
                recorder = TradeRecorder()
                trades = recorder.get_trade_history(
                    symbol=symbol,
                    start_date=start_datetime,
                    end_date=end_datetime
                )
                
                for trade in trades:
                    action = trade.get("side", "BUY").upper()
                    if action == "LONG":
                        action = "BUY"
                    elif action == "SHORT":
                        action = "SELL"
                    
                    trade_points.append(TradePoint(
                        ts=datetime.fromisoformat(trade.get("timestamp", "")),
                        action=action,
                        price=trade.get("price", 0.0),
                        quantity=trade.get("quantity", 0.0)
                    ))
            
            except Exception as e:
                logger.warning(f"Failed to load trades from legacy TradeRecorder: {e}")
    
    except ImportError as e:
        logger.warning(f"VirtualTrade model not available: {e}")
    except Exception as e:
        logger.error(f"Error loading trades: {e}", exc_info=True)
    
    logger.info(f"Loaded {len(trade_points)} trades for {symbol} on {target_date}")
    return trade_points

