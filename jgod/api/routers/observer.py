"""Knowledge Brain Observer API Router

Provides endpoints for monitoring knowledge governance state.
"""

import logging
from datetime import date, timedelta
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Query

from jgod.api.schemas.observer import (
    KnowledgeGovernanceSummarySchema,
    StabilityAlertSchema,
    SRankDistributionHistorySchema,
)
from jgod.observer.collector import KnowledgeDataCollector
from jgod.observer.analyzer import GovernanceAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize collector and analyzer (singleton)
_collector = KnowledgeDataCollector()
_analyzer = GovernanceAnalyzer()


@router.get(
    "/governance-summary",
    response_model=KnowledgeGovernanceSummarySchema,
    summary="Get knowledge governance summary",
    description="取得最新的知識治理概覽數據，包含 Doctrine、Rule Sim、S-Rank 等核心 KPI。",
)
async def get_governance_summary() -> KnowledgeGovernanceSummarySchema:
    """Get latest knowledge governance summary"""
    try:
        summary = _collector.collect_governance_data()
        return KnowledgeGovernanceSummarySchema.model_validate(summary.model_dump())
    except Exception as e:
        logger.error(f"Error collecting governance summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/stability-alerts",
    response_model=List[StabilityAlertSchema],
    summary="Get stability alerts",
    description="取得當前系統檢測到的穩定性警報，基於預設閾值自動判定異常。",
)
async def get_stability_alerts() -> List[StabilityAlertSchema]:
    """Get current stability alerts"""
    try:
        summary = _collector.collect_governance_data()
        alerts = _analyzer.check_stability_alerts(summary)
        return [StabilityAlertSchema.model_validate(alert.model_dump()) for alert in alerts]
    except Exception as e:
        logger.error(f"Error getting stability alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/s-rank-history/distribution",
    response_model=List[SRankDistributionHistorySchema],
    summary="Get S-Rank distribution history",
    description="取得過去 N 天 S-Rank 分佈的歷史數據，用於繪製堆疊柱狀圖。",
)
async def get_s_rank_distribution_history(
    days: int = Query(30, ge=1, le=90, description="歷史天數，預設 30 天，最多 90 天"),
) -> List[SRankDistributionHistorySchema]:
    """Get S-Rank distribution history for charting"""
    try:
        if _collector.s_rank_storage is None:
            from jgod.s_rank_engine.storage import SRankFactorStorageV1
            _collector.s_rank_storage = SRankFactorStorageV1()
        
        # Get date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Load factors for each date in range
        history_data: List[Dict[str, Any]] = []
        
        current_date = start_date
        while current_date <= end_date:
            factors = _collector.s_rank_storage.load_historical_factors(current_date)
            
            if factors:
                # Calculate distribution for this date
                distribution = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0}
                for factor in factors:
                    rank = factor.rank_level
                    if rank in distribution:
                        distribution[rank] += 1
                
                history_data.append({
                    "date": current_date.isoformat(),
                    "distribution": distribution,
                })
            
            current_date = current_date + timedelta(days=1)
        
        # Sort by date ascending
        history_data.sort(key=lambda x: x["date"])
        
        return [
            SRankDistributionHistorySchema(
                date=item["date"],
                distribution=item["distribution"],
            )
            for item in history_data
        ]
        
    except Exception as e:
        logger.error(f"Error getting S-Rank distribution history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/prediction-stability/{symbol}",
    summary="Get prediction stability metrics for symbol",
    description="取得指定股票代號的預測穩定性指標，包含標準差、最大日間變化、趨勢斜率與穩定性等級。",
)
async def get_prediction_stability(
    symbol: str,
    limit: int = Query(60, ge=1, le=200, description="Maximum number of timeline points to analyze"),
) -> dict:
    """Get prediction stability metrics for a symbol"""
    try:
        from jgod.storage.models import PredictionSnapshot
        from jgod.observer.prediction_stability import compute_stability_metrics
        
        # Get database connection (same pattern as predictions router)
        try:
            from jgod.api.dependencies import get_db
        except ImportError:
            try:
                from jgod.storage.db import get_session as get_db
            except ImportError:
                raise HTTPException(status_code=503, detail="Database not available")
        
        db = None
        try:
            db_gen = get_db()
            if db_gen:
                db = next(db_gen)
        except Exception as e:
            logger.debug(f"Could not get database session: {e}")
            db = None
        
        if db is None:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Query prediction timeline (same as /api/v1/predictions/timeline/{symbol})
        predictions = db.query(PredictionSnapshot).filter(
            PredictionSnapshot.symbol == symbol
        ).order_by(
            PredictionSnapshot.date.desc()
        ).limit(limit).all()
        
        # Convert to timeline items format
        items = []
        for pred in predictions:
            raw_score = pred.score if hasattr(pred, 'score') and pred.score is not None else (pred.total_score or 0.0)
            items.append({
                "date": pred.date.isoformat(),
                "final_score": float(raw_score),  # Using raw_score as final_score for now
            })
        
        # Compute stability metrics
        metrics = compute_stability_metrics(items)
        
        return {
            "symbol": symbol,
            "n_points": metrics["n_points"],
            "score_std": metrics["score_std"],
            "max_abs_delta": metrics["max_abs_delta"],
            "trend_slope": metrics["trend_slope"],
            "stability_grade": metrics["stability_grade"],
            "thresholds": metrics["thresholds"],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing prediction stability for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

