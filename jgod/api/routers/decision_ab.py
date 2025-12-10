"""Decision AB Test API Router

Provides endpoints for Decision Layer AB test results.
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Query, Body

from jgod.api.schemas.decision_ab import (
    DecisionAbResultSchema,
    ArmResultSchema,
    ArmMetricsSchema,
    DecisionComparisonRequestSchema,
    DecisionABTestReportSchema,
    DecisionABTestReportSummarySchema,
    ArmBacktestResultSchema,
)
from jgod.decision_ab.storage import AbResultStorage, DecisionAbStorageV1
from jgod.decision_ab.models import DecisionAbResult, DecisionABTestReport
from jgod.decision_ab.runner import DecisionAbRunnerV1

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize storage
_storage = AbResultStorage()
_v2_storage = DecisionAbStorageV1()
_runner = DecisionAbRunnerV1()


def _convert_ab_result_to_schema(result: DecisionAbResult) -> DecisionAbResultSchema:
    """Convert DecisionAbResult to API schema"""
    return DecisionAbResultSchema(
        experiment_id=result.experiment_id,
        created_at=result.created_at,
        raw_only=ArmResultSchema(
            experiment_id=result.raw_only.experiment_id,
            mode=result.raw_only.mode,
            start_date=result.raw_only.start_date,
            end_date=result.raw_only.end_date,
            metrics=ArmMetricsSchema(**result.raw_only.metrics.model_dump()),
        ),
        decision_on=ArmResultSchema(
            experiment_id=result.decision_on.experiment_id,
            mode=result.decision_on.mode,
            start_date=result.decision_on.start_date,
            end_date=result.decision_on.end_date,
            metrics=ArmMetricsSchema(**result.decision_on.metrics.model_dump()),
        ),
        delta_sharpe=result.delta_sharpe,
        delta_max_drawdown=result.delta_max_drawdown,
        delta_total_return=result.delta_total_return,
        delta_win_rate=result.delta_win_rate,
        delta_turnover=result.delta_turnover,
    )


@router.get(
    "/recent",
    response_model=List[DecisionAbResultSchema],
    summary="Get recent Decision AB test results",
    description="Retrieves recent Decision Layer AB test results, comparing RAW_ONLY vs DECISION_ON modes.",
)
async def get_recent_ab_results(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results to return"),
) -> List[DecisionAbResultSchema]:
    """
    Get recent Decision AB test results.
    
    Returns:
        List of DecisionAbResultSchema, sorted by created_at (newest first)
    """
    try:
        results = _storage.load_recent(limit=limit)
        return [_convert_ab_result_to_schema(r) for r in results]
    except Exception as e:
        logger.error(f"Error loading recent AB results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/{experiment_id}",
    response_model=DecisionAbResultSchema,
    summary="Get Decision AB test result by experiment ID",
    description="Retrieves a specific Decision AB test result by experiment_id.",
)
async def get_ab_result_by_id(
    experiment_id: str,
) -> DecisionAbResultSchema:
    """
    Get Decision AB test result by experiment ID.
    
    Args:
        experiment_id: Experiment identifier
    
    Returns:
        DecisionAbResultSchema
    
    Raises:
        404: If experiment not found
    """
    try:
        result = _storage.load_by_experiment_id(experiment_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Experiment not found: {experiment_id}")
        return _convert_ab_result_to_schema(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading AB result for {experiment_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ============================================================================
# V1 vs V2 Decision AB Test Endpoints (New)
# ============================================================================

def _convert_report_to_schema(report: DecisionABTestReport) -> DecisionABTestReportSchema:
    """Convert DecisionABTestReport to API schema"""
    return DecisionABTestReportSchema(
        experiment_id=report.experiment_id,
        created_at=report.created_at,
        config=report.config,
        baseline=ArmBacktestResultSchema(**report.baseline.model_dump()),
        variant=ArmBacktestResultSchema(**report.variant.model_dump()),
        sharpe_delta=report.sharpe_delta,
        max_drawdown_delta=report.max_drawdown_delta,
        return_delta=report.return_delta,
        volatility_delta=report.volatility_delta,
        win_rate_delta=report.win_rate_delta,
        turnover_delta=report.turnover_delta,
        recommendation=report.recommendation,
        notes=report.notes,
    )


@router.post(
    "/ab-test/decision-comparison",
    response_model=DecisionABTestReportSchema,
    summary="Run Decision V1 vs V2 AB Test",
    description="觸發一次 V1 vs V2 的 AB Test 回測並產生報告。",
)
async def run_decision_comparison(
    request: DecisionComparisonRequestSchema = Body(...),
) -> DecisionABTestReportSchema:
    """
    Run Decision V1 vs V2 AB Test
    
    Triggers a backtest comparison between Decision Layer V1 and V2,
    generating a comprehensive report with performance metrics and recommendation.
    """
    try:
        report = _runner.run_decision_v1_vs_v2(
            start_date=request.start_date,
            end_date=request.end_date,
            capital=request.capital,
            path_a_config_name=request.path_a_config_name,
            note=request.note,
        )
        
        return _convert_report_to_schema(report)
        
    except Exception as e:
        logger.error(f"Error running Decision V1 vs V2 comparison: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/ab-test/decision-reports/recent",
    response_model=List[DecisionABTestReportSummarySchema],
    summary="Get recent Decision AB Test reports",
    description="取得最近執行的 Decision V1 vs V2 AB Test 報告概要。",
)
async def get_recent_decision_reports(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of reports to return"),
) -> List[DecisionABTestReportSummarySchema]:
    """Get recent Decision AB Test reports"""
    try:
        reports = _v2_storage.load_recent_decision_reports(limit=limit)
        
        summaries = []
        for report in reports:
            config = report.config
            summaries.append(DecisionABTestReportSummarySchema(
                experiment_id=report.experiment_id,
                created_at=report.created_at,
                path_a_config_name=config.get("path_a_config_name", "unknown"),
                sharpe_delta=report.sharpe_delta,
                return_delta=report.return_delta,
                max_drawdown_delta=report.max_drawdown_delta,
                recommendation=report.recommendation,
            ))
        
        return summaries
        
    except Exception as e:
        logger.error(f"Error loading recent Decision AB Test reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/ab-test/decision-reports/{experiment_id}",
    response_model=DecisionABTestReportSchema,
    summary="Get Decision AB Test report by ID",
    description="取得指定 experiment_id 的完整 Decision V1 vs V2 AB Test 報告。",
)
async def get_decision_report_by_id(
    experiment_id: str,
) -> DecisionABTestReportSchema:
    """Get Decision AB Test report by experiment ID"""
    try:
        report = _v2_storage.load_decision_report(experiment_id)
        if report is None:
            raise HTTPException(status_code=404, detail=f"Experiment report not found: {experiment_id}")
        
        return _convert_report_to_schema(report)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading Decision AB Test report for {experiment_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

