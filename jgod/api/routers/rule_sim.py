"""Rule Simulation API Router

Provides endpoints for rule simulation experiments.
"""

import logging
import uuid
from datetime import datetime, date
from typing import List

from fastapi import APIRouter, HTTPException, Query

from jgod.api.schemas.rule_sim import (
    RuleSimRunRequest,
    RuleSimRunResponse,
    RuleSimStatusSummarySchema,
    RuleSimReportSummarySchema,
    RuleSimReportSchema,
    RuleSetRefSchema,
    RuleSimArmMetricsSchema,
    RuleSimDeltaMetricsSchema,
)
from jgod.rule_sim.engine import RuleSimEngineV1
from jgod.rule_sim.storage import RuleSimStorageV1
from jgod.rule_sim.models import (
    RuleSimExperimentConfig,
    RuleSetRef,
    RuleSimTargetType,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize engine (singleton)
_storage = RuleSimStorageV1()
_engine = RuleSimEngineV1(storage=_storage)


def _ruleset_ref_to_schema(ref) -> RuleSetRefSchema:
    """Convert RuleSetRef to schema"""
    return RuleSetRefSchema(
        id=ref.id,
        type=ref.type.value,
        description=ref.description,
        doctrine_section_ids=ref.doctrine_section_ids,
        alert_config_path=ref.alert_config_path,
    )


def _ruleset_ref_from_schema(schema: RuleSetRefSchema) -> RuleSetRef:
    """Convert schema to RuleSetRef"""
    return RuleSetRef(
        id=schema.id,
        type=RuleSimTargetType(schema.type),
        description=schema.description,
        doctrine_section_ids=schema.doctrine_section_ids,
        alert_config_path=schema.alert_config_path,
    )


@router.post(
    "/run",
    response_model=RuleSimRunResponse,
    summary="Run a rule simulation experiment",
    description="Triggers a rule simulation experiment comparing baseline vs variant rules.",
)
async def run_experiment(request: RuleSimRunRequest) -> RuleSimRunResponse:
    """
    Run a rule simulation experiment.
    
    For v1, this runs synchronously. Future versions may support async/background execution.
    """
    try:
        # Create experiment config
        experiment_id = str(uuid.uuid4())
        
        config = RuleSimExperimentConfig(
            experiment_id=experiment_id,
            created_at=datetime.now(),
            created_by="API",
            target_ruleset=_ruleset_ref_from_schema(request.target_ruleset),
            baseline_version_id=request.baseline_version_id,
            variant_version_id=request.variant_version_id,
            start_date=request.start_date,
            end_date=request.end_date,
            universe=request.universe or [],
            path_a_config_name=request.path_a_config_name,
            note=request.note,
        )
        
        # Run experiment (synchronous for v1)
        report = _engine.run_experiment(config)
        
        return RuleSimRunResponse(
            experiment_id=experiment_id,
            status=RuleSimStatusSummarySchema(
                status=report.status.status.value,
                started_at=report.status.started_at,
                finished_at=report.status.finished_at,
                error_message=report.status.error_message,
            ),
        )
        
    except Exception as e:
        logger.error(f"Error running experiment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/experiments/recent",
    response_model=List[RuleSimReportSummarySchema],
    summary="Get recent rule simulation experiments",
)
async def get_recent_experiments(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of experiments to return"),
) -> List[RuleSimReportSummarySchema]:
    """Get recent rule simulation experiments"""
    try:
        reports = _storage.load_recent(limit=limit)
        
        summaries = []
        for report in reports:
            summaries.append(
                RuleSimReportSummarySchema(
                    experiment_id=report.experiment_id,
                    created_at=report.created_at,
                    target_ruleset=_ruleset_ref_to_schema(report.config.target_ruleset) if report.config.target_ruleset else RuleSetRefSchema(id="unknown", type="unknown"),
                    status=report.status.status.value,
                    baseline_sharpe=report.baseline_metrics.sharpe,
                    variant_sharpe=report.variant_metrics.sharpe,
                    sharpe_delta=report.deltas.sharpe_delta,
                    recommendation=report.recommendation,
                )
            )
        
        return summaries
        
    except Exception as e:
        logger.error(f"Error loading recent experiments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/experiments/{experiment_id}",
    response_model=RuleSimReportSchema,
    summary="Get a specific rule simulation experiment report",
)
async def get_experiment_report(experiment_id: str) -> RuleSimReportSchema:
    """Get a specific experiment report"""
    try:
        report = _storage.load_by_id(experiment_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"Experiment not found: {experiment_id}")
        
        # Convert config to dict
        config_dict = {
            "experiment_id": report.config.experiment_id,
            "created_at": report.config.created_at.isoformat(),
            "created_by": report.config.created_by,
            "target_ruleset": {
                "id": report.config.target_ruleset.id,
                "type": report.config.target_ruleset.type.value,
                "description": report.config.target_ruleset.description,
                "doctrine_section_ids": report.config.target_ruleset.doctrine_section_ids,
                "alert_config_path": report.config.target_ruleset.alert_config_path,
            } if report.config.target_ruleset else None,
            "baseline_version_id": report.config.baseline_version_id,
            "variant_version_id": report.config.variant_version_id,
            "start_date": report.config.start_date.isoformat(),
            "end_date": report.config.end_date.isoformat(),
            "universe": report.config.universe,
            "path_a_config_name": report.config.path_a_config_name,
            "note": report.config.note,
        }
        
        return RuleSimReportSchema(
            experiment_id=report.experiment_id,
            config=config_dict,
            status=RuleSimStatusSummarySchema(
                status=report.status.status.value,
                started_at=report.status.started_at,
                finished_at=report.status.finished_at,
                error_message=report.status.error_message,
            ),
            baseline_metrics=RuleSimArmMetricsSchema(
                arm=report.baseline_metrics.arm.value,
                sharpe=report.baseline_metrics.sharpe,
                max_drawdown=report.baseline_metrics.max_drawdown,
                total_return=report.baseline_metrics.total_return,
                win_rate=report.baseline_metrics.win_rate,
                turnover=report.baseline_metrics.turnover,
                var_95=report.baseline_metrics.var_95,
                alert_trigger_count=report.baseline_metrics.alert_trigger_count,
                doctrine_violation_count=report.baseline_metrics.doctrine_violation_count,
            ),
            variant_metrics=RuleSimArmMetricsSchema(
                arm=report.variant_metrics.arm.value,
                sharpe=report.variant_metrics.sharpe,
                max_drawdown=report.variant_metrics.max_drawdown,
                total_return=report.variant_metrics.total_return,
                win_rate=report.variant_metrics.win_rate,
                turnover=report.variant_metrics.turnover,
                var_95=report.variant_metrics.var_95,
                alert_trigger_count=report.variant_metrics.alert_trigger_count,
                doctrine_violation_count=report.variant_metrics.doctrine_violation_count,
            ),
            deltas=RuleSimDeltaMetricsSchema(
                sharpe_delta=report.deltas.sharpe_delta,
                max_drawdown_delta=report.deltas.max_drawdown_delta,
                total_return_delta=report.deltas.total_return_delta,
                win_rate_delta=report.deltas.win_rate_delta,
                turnover_delta=report.deltas.turnover_delta,
                alert_trigger_delta=report.deltas.alert_trigger_delta,
                doctrine_violation_delta=report.deltas.doctrine_violation_delta,
            ),
            key_findings=report.key_findings,
            recommendation=report.recommendation,
            created_at=report.created_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading experiment {experiment_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

