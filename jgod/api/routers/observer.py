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

