"""Rule Simulation Storage

JSONL-based storage for rule simulation reports.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from jgod.rule_sim.models import RuleSimReport

logger = logging.getLogger(__name__)


class RuleSimStorageV1:
    """Storage for rule simulation reports"""
    
    def __init__(self, path: Optional[Path] = None):
        """
        Initialize storage
        
        Args:
            path: Path to JSONL file (default: config.RULE_SIM_REPORTS_PATH)
        """
        from jgod.rule_sim.config import RULE_SIM_REPORTS_PATH
        self.path = path or RULE_SIM_REPORTS_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"RuleSimStorageV1 initialized at: {self.path}")
    
    def _report_to_dict(self, report: RuleSimReport) -> dict:
        """Convert RuleSimReport to dict for JSON serialization"""
        return {
            "experiment_id": report.experiment_id,
            "config": {
                "experiment_id": report.config.experiment_id,
                "created_at": report.config.created_at.isoformat(),
                "created_by": report.config.created_by,
                "target_ruleset": {
                    "id": report.config.target_ruleset.id if report.config.target_ruleset else None,
                    "type": report.config.target_ruleset.type.value if report.config.target_ruleset else None,
                    "description": report.config.target_ruleset.description if report.config.target_ruleset else None,
                    "doctrine_section_ids": report.config.target_ruleset.doctrine_section_ids if report.config.target_ruleset else None,
                    "alert_config_path": report.config.target_ruleset.alert_config_path if report.config.target_ruleset else None,
                } if report.config.target_ruleset else None,
                "baseline_version_id": report.config.baseline_version_id,
                "variant_version_id": report.config.variant_version_id,
                "start_date": report.config.start_date.isoformat(),
                "end_date": report.config.end_date.isoformat(),
                "universe": report.config.universe,
                "path_a_config_name": report.config.path_a_config_name,
                "note": report.config.note,
            },
            "status": {
                "status": report.status.status.value,
                "started_at": report.status.started_at.isoformat() if report.status.started_at else None,
                "finished_at": report.status.finished_at.isoformat() if report.status.finished_at else None,
                "error_message": report.status.error_message,
            },
            "baseline_metrics": {
                "arm": report.baseline_metrics.arm.value,
                "sharpe": report.baseline_metrics.sharpe,
                "max_drawdown": report.baseline_metrics.max_drawdown,
                "total_return": report.baseline_metrics.total_return,
                "win_rate": report.baseline_metrics.win_rate,
                "turnover": report.baseline_metrics.turnover,
                "var_95": report.baseline_metrics.var_95,
                "alert_trigger_count": report.baseline_metrics.alert_trigger_count,
                "doctrine_violation_count": report.baseline_metrics.doctrine_violation_count,
            },
            "variant_metrics": {
                "arm": report.variant_metrics.arm.value,
                "sharpe": report.variant_metrics.sharpe,
                "max_drawdown": report.variant_metrics.max_drawdown,
                "total_return": report.variant_metrics.total_return,
                "win_rate": report.variant_metrics.win_rate,
                "turnover": report.variant_metrics.turnover,
                "var_95": report.variant_metrics.var_95,
                "alert_trigger_count": report.variant_metrics.alert_trigger_count,
                "doctrine_violation_count": report.variant_metrics.doctrine_violation_count,
            },
            "deltas": {
                "sharpe_delta": report.deltas.sharpe_delta,
                "max_drawdown_delta": report.deltas.max_drawdown_delta,
                "total_return_delta": report.deltas.total_return_delta,
                "win_rate_delta": report.deltas.win_rate_delta,
                "turnover_delta": report.deltas.turnover_delta,
                "alert_trigger_delta": report.deltas.alert_trigger_delta,
                "doctrine_violation_delta": report.deltas.doctrine_violation_delta,
            },
            "key_findings": report.key_findings,
            "recommendation": report.recommendation,
            "created_at": report.created_at.isoformat(),
        }
    
    def _dict_to_report(self, data: dict) -> RuleSimReport:
        """Convert dict to RuleSimReport"""
        from datetime import datetime, date
        from jgod.rule_sim.models import (
            RuleSetRef, RuleSimExperimentConfig, RuleSimArmMetrics,
            RuleSimDeltaMetrics, RuleSimStatusSummary, RuleSimArm,
        )
        
        config_data = data["config"]
        ruleset_data = config_data.get("target_ruleset")
        
        config = RuleSimExperimentConfig(
            experiment_id=config_data["experiment_id"],
            created_at=datetime.fromisoformat(config_data["created_at"]),
            created_by=config_data["created_by"],
            target_ruleset=RuleSetRef(
                id=ruleset_data["id"],
                type=ruleset_data["type"],
                description=ruleset_data.get("description"),
                doctrine_section_ids=ruleset_data.get("doctrine_section_ids"),
                alert_config_path=ruleset_data.get("alert_config_path"),
            ) if ruleset_data else None,
            baseline_version_id=config_data.get("baseline_version_id"),
            variant_version_id=config_data.get("variant_version_id"),
            start_date=date.fromisoformat(config_data["start_date"]),
            end_date=date.fromisoformat(config_data["end_date"]),
            universe=config_data.get("universe", []),
            path_a_config_name=config_data.get("path_a_config_name", "path_a_tw_basic_v1"),
            note=config_data.get("note"),
        )
        
        status_data = data["status"]
        status = RuleSimStatusSummary(
            status=status_data["status"],
            started_at=datetime.fromisoformat(status_data["started_at"]) if status_data.get("started_at") else None,
            finished_at=datetime.fromisoformat(status_data["finished_at"]) if status_data.get("finished_at") else None,
            error_message=status_data.get("error_message"),
        )
        
        baseline_data = data["baseline_metrics"]
        baseline_metrics = RuleSimArmMetrics(
            arm=RuleSimArm(baseline_data["arm"]),
            sharpe=baseline_data["sharpe"],
            max_drawdown=baseline_data["max_drawdown"],
            total_return=baseline_data["total_return"],
            win_rate=baseline_data["win_rate"],
            turnover=baseline_data["turnover"],
            var_95=baseline_data.get("var_95"),
            alert_trigger_count=baseline_data.get("alert_trigger_count"),
            doctrine_violation_count=baseline_data.get("doctrine_violation_count"),
        )
        
        variant_data = data["variant_metrics"]
        variant_metrics = RuleSimArmMetrics(
            arm=RuleSimArm(variant_data["arm"]),
            sharpe=variant_data["sharpe"],
            max_drawdown=variant_data["max_drawdown"],
            total_return=variant_data["total_return"],
            win_rate=variant_data["win_rate"],
            turnover=variant_data["turnover"],
            var_95=variant_data.get("var_95"),
            alert_trigger_count=variant_data.get("alert_trigger_count"),
            doctrine_violation_count=variant_data.get("doctrine_violation_count"),
        )
        
        deltas_data = data["deltas"]
        deltas = RuleSimDeltaMetrics(
            sharpe_delta=deltas_data["sharpe_delta"],
            max_drawdown_delta=deltas_data["max_drawdown_delta"],
            total_return_delta=deltas_data["total_return_delta"],
            win_rate_delta=deltas_data["win_rate_delta"],
            turnover_delta=deltas_data["turnover_delta"],
            alert_trigger_delta=deltas_data.get("alert_trigger_delta"),
            doctrine_violation_delta=deltas_data.get("doctrine_violation_delta"),
        )
        
        return RuleSimReport(
            experiment_id=data["experiment_id"],
            config=config,
            status=status,
            baseline_metrics=baseline_metrics,
            variant_metrics=variant_metrics,
            deltas=deltas,
            key_findings=data.get("key_findings", []),
            recommendation=data.get("recommendation", "CAUTION"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
        )
    
    def save_report(self, report: RuleSimReport) -> None:
        """
        Save a report to JSONL
        
        Args:
            report: RuleSimReport to save
        """
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(self._report_to_dict(report), ensure_ascii=False) + "\n")
            logger.info(f"Saved rule sim report: {report.experiment_id}")
        except Exception as e:
            logger.error(f"Failed to save report {report.experiment_id}: {e}", exc_info=True)
            raise
    
    def load_recent(self, limit: int = 20) -> List[RuleSimReport]:
        """
        Load recent reports
        
        Args:
            limit: Maximum number of reports to load
        
        Returns:
            List of RuleSimReport (sorted by created_at descending)
        """
        if not self.path.exists():
            return []
        
        reports: List[RuleSimReport] = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        reports.append(self._dict_to_report(data))
            
            # Sort by created_at descending
            reports.sort(key=lambda r: r.created_at, reverse=True)
            return reports[:limit]
        except Exception as e:
            logger.error(f"Failed to load reports: {e}", exc_info=True)
            return []
    
    def load_by_id(self, experiment_id: str) -> Optional[RuleSimReport]:
        """
        Load a specific report by ID
        
        Args:
            experiment_id: Experiment ID
        
        Returns:
            RuleSimReport if found, None otherwise
        """
        if not self.path.exists():
            return None
        
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if data["experiment_id"] == experiment_id:
                            return self._dict_to_report(data)
            return None
        except Exception as e:
            logger.error(f"Failed to load report {experiment_id}: {e}", exc_info=True)
            return None

