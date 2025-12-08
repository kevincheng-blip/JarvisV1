"""
Error Review API Router

Provides endpoints for querying error analysis results with Doctrine suggestions.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from jgod.api.schemas.error_review import ErrorReviewItem, DoctrineHitLite

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_error_reports_path() -> Path:
    """Get path to error reports JSONL file"""
    # Assume we're in jgod/api/routers/, go up to project root
    project_root = Path(__file__).parent.parent.parent.parent
    return project_root / "data" / "error_learning" / "error_reports.jsonl"


@router.get(
    "/recent",
    response_model=List[ErrorReviewItem],
    summary="Get recent error analysis results with Doctrine suggestions",
    description="Retrieves recent error analysis results from the unified error reports JSONL file, "
                "with optional filtering by date range, symbol, and error type.",
)
async def get_recent_error_reviews(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results to return"),
    start_date: Optional[str] = Query(None, description="Filter errors starting from this date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter errors ending by this date (YYYY-MM-DD)"),
    symbol: Optional[str] = Query(None, description="Filter by stock symbol"),
    error_type: Optional[str] = Query(None, description="Filter by error type"),
) -> List[ErrorReviewItem]:
    """
    Get recent error analysis results with Doctrine suggestions.
    
    Reads from data/error_learning/error_reports.jsonl and applies filters.
    Results are sorted by timestamp (newest first).
    """
    reports_path = _get_error_reports_path()
    
    # If file doesn't exist, return empty list (not an error)
    if not reports_path.exists():
        logger.info(f"Error reports file not found: {reports_path}, returning empty list")
        return []
    
    # Parse date filters
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}. Use YYYY-MM-DD")
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}. Use YYYY-MM-DD")
    
    # Read and parse JSONL
    results = []
    line_num = 0
    
    try:
        with open(reports_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_num += 1
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line {line_num} in {reports_path}: {e}")
                    continue
                
                # Apply filters
                if symbol and record.get("symbol") != symbol:
                    continue
                
                if error_type and record.get("error_type") != error_type:
                    continue
                
                # Date filter
                error_dt = None
                try:
                    timestamp_str = record.get("timestamp", "")
                    if timestamp_str:
                        # Parse timestamp (could be ISO format or other)
                        if isinstance(timestamp_str, str):
                            try:
                                error_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            except ValueError:
                                # Try other formats
                                try:
                                    error_dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                                except ValueError:
                                    logger.warning(f"Could not parse timestamp: {timestamp_str}")
                                    continue
                        else:
                            continue
                        
                        if error_dt:
                            error_date = error_dt.date()
                            
                            if start_dt and error_date < start_dt:
                                continue
                            if end_dt and error_date > end_dt:
                                continue
                except Exception as e:
                    logger.warning(f"Error parsing timestamp for record {record.get('id', 'unknown')}: {e}")
                    continue
                
                # If we couldn't parse timestamp, use current time as fallback
                if not error_dt:
                    error_dt = datetime.now()
                
                # Extract analysis data
                analysis = record.get("analysis", {})
                doctrine_suggestions = analysis.get("doctrine_suggestions", [])
                
                # Convert to DoctrineHitLite (limit to first 3 for table display)
                doctrine_hits = []
                for hit_data in doctrine_suggestions[:3]:
                    doctrine_hits.append(DoctrineHitLite(
                        book_id=hit_data.get("book_id", "unknown"),
                        section_id=hit_data.get("section_id", "unknown"),
                        summary=hit_data.get("summary"),
                        core_principles=hit_data.get("core_principles"),
                        risk_rules=hit_data.get("risk_rules"),
                        tags=hit_data.get("tags")
                    ))
                
                # Build human_summary from analysis notes
                human_summary_parts = []
                if analysis.get("knowledge_gap_notes"):
                    human_summary_parts.extend(analysis["knowledge_gap_notes"][:2])
                if analysis.get("utilization_gap_reasons"):
                    human_summary_parts.extend(analysis["utilization_gap_reasons"][:2])
                human_summary = " ".join(human_summary_parts) if human_summary_parts else record.get("notes")
                
                # Create ErrorReviewItem
                item = ErrorReviewItem(
                    id=record.get("id", ""),
                    timestamp=error_dt if 'error_dt' in locals() else datetime.now(),
                    symbol=record.get("symbol", ""),
                    error_type=record.get("error_type"),
                    pnl_impact=record.get("pnl"),
                    human_summary=human_summary,
                    doctrine_hits=doctrine_hits,
                    classification=analysis.get("classification", "UNKNOWN"),
                    timeframe=record.get("timeframe"),
                    side=record.get("side"),
                    predicted_outcome=record.get("predicted_outcome"),
                    actual_outcome=record.get("actual_outcome")
                )
                
                results.append(item)
        
    except Exception as e:
        logger.error(f"Error reading error reports file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to read error reports: {str(e)}")
    
    # Sort by timestamp (newest first)
    results.sort(key=lambda x: x.timestamp, reverse=True)
    
    # Apply limit
    results = results[:limit]
    
    logger.info(f"Returning {len(results)} error review items (filtered from {line_num} lines)")
    
    return results

