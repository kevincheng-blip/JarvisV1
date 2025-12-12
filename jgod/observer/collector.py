"""Knowledge Data Collector

Collects data from various knowledge governance modules.
"""

import logging
from datetime import datetime, timedelta, date
from typing import Optional, Dict

from jgod.observer.models import KnowledgeGovernanceSummary
from jgod.observer.config import (
    DAYS_FOR_SECTIONS_MODIFIED,
    DAYS_FOR_SIMULATIONS,
    HOURS_FOR_S_RANK_RECALCULATIONS,
    DAYS_FOR_STRATEGY_DEGRADATION,
)

logger = logging.getLogger(__name__)


class KnowledgeDataCollector:
    """數據收集核心"""
    
    def __init__(
        self,
        doctrine_service=None,
        rule_sim_storage=None,
        s_rank_storage=None,
        alert_engine=None,
    ):
        """
        Initialize collector with dependencies
        
        Args:
            doctrine_service: Doctrine Service V2 instance (optional)
            rule_sim_storage: RuleSimStorageV1 instance (optional)
            s_rank_storage: SRankFactorStorageV1 instance (optional)
            alert_engine: DoctrineAlertEngineV1 instance (optional)
        """
        self.doctrine_service = doctrine_service
        self.rule_sim_storage = rule_sim_storage
        self.s_rank_storage = s_rank_storage
        self.alert_engine = alert_engine
        
        logger.info("KnowledgeDataCollector initialized")
    
    def collect_governance_data(self) -> KnowledgeGovernanceSummary:
        """
        從多個來源收集數據，並組合成 KnowledgeGovernanceSummary
        """
        logger.debug("Collecting knowledge governance data...")
        
        summary = KnowledgeGovernanceSummary()
        
        # 1. Doctrine 數據
        self._collect_doctrine_data(summary)
        
        # 2. Rule Sim 數據
        self._collect_rule_sim_data(summary)
        
        # 3. S-Rank 數據
        self._collect_s_rank_data(summary)
        
        # 4. Alert 數據
        self._collect_alert_data(summary)
        
        logger.debug(f"Knowledge governance data collected: {summary.model_dump()}")
        
        return summary
    
    def _collect_doctrine_data(self, summary: KnowledgeGovernanceSummary) -> None:
        """收集 Doctrine 治理數據"""
        try:
            if self.doctrine_service is None:
                # Try to import and instantiate
                try:
                    from jgod.doctrine_v2.service import DoctrineServiceV2
                    self.doctrine_service = DoctrineServiceV2()
                except Exception as e:
                    logger.debug(f"Doctrine Service V2 not available: {e}")
                    return
            
            # Get total sections count
            # Assuming DoctrineServiceV2 has a method to list all sections
            try:
                if hasattr(self.doctrine_service, "list_all_sections"):
                    all_sections = self.doctrine_service.list_all_sections()
                    summary.total_sections = len(all_sections) if all_sections else 0
                else:
                    # Fallback: try to count from storage
                    logger.debug("list_all_sections not available, skipping total_sections")
            except Exception as e:
                logger.debug(f"Error getting total sections: {e}")
            
            # Get pending review count
            try:
                if hasattr(self.doctrine_service, "list_sections"):
                    pending_sections = self.doctrine_service.list_sections(status="PENDING_REVIEW")
                    summary.pending_review_count = len(pending_sections) if pending_sections else 0
                else:
                    logger.debug("list_sections not available, skipping pending_review_count")
            except Exception as e:
                logger.debug(f"Error getting pending review count: {e}")
            
            # Get sections modified in last 7 days
            try:
                if hasattr(self.doctrine_service, "get_sections_modified_since"):
                    cutoff_date = date.today() - timedelta(days=DAYS_FOR_SECTIONS_MODIFIED)
                    modified = self.doctrine_service.get_sections_modified_since(cutoff_date)
                    summary.sections_modified_last_7d = len(modified) if modified else 0
                else:
                    logger.debug("get_sections_modified_since not available, skipping sections_modified_last_7d")
            except Exception as e:
                logger.debug(f"Error getting modified sections: {e}")
                
        except Exception as e:
            logger.warning(f"Error collecting Doctrine data: {e}", exc_info=True)
    
    def _collect_rule_sim_data(self, summary: KnowledgeGovernanceSummary) -> None:
        """收集 Rule Simulation 數據"""
        try:
            if self.rule_sim_storage is None:
                try:
                    from jgod.rule_sim.storage import RuleSimStorageV1
                    self.rule_sim_storage = RuleSimStorageV1()
                except Exception as e:
                    logger.debug(f"Rule Sim Storage not available: {e}")
                    return
            
            # Load all reports
            all_reports = self.rule_sim_storage.load_all()
            
            if not all_reports:
                return
            
            # Filter reports from last 30 days
            cutoff_date = datetime.now() - timedelta(days=DAYS_FOR_SIMULATIONS)
            recent_reports = [
                r for r in all_reports
                if r.status.status == "SUCCESS" and r.config.created_at >= cutoff_date
            ]
            
            summary.simulations_last_30d = len(recent_reports)
            
            if not recent_reports:
                summary.sim_approve_rate_30d = 0.0
                summary.sim_maxdd_increase_rate_30d = 0.0
                return
            
            # Calculate approve rate
            approve_count = sum(1 for r in recent_reports if r.recommendation == "APPROVE")
            summary.sim_approve_rate_30d = approve_count / len(recent_reports) if recent_reports else 0.0
            
            # Calculate MaxDD increase rate (REJECT recommendations)
            reject_count = sum(1 for r in recent_reports if r.recommendation == "REJECT")
            summary.sim_maxdd_increase_rate_30d = reject_count / len(recent_reports) if recent_reports else 0.0
            
        except Exception as e:
            logger.warning(f"Error collecting Rule Sim data: {e}", exc_info=True)
    
    def _collect_s_rank_data(self, summary: KnowledgeGovernanceSummary) -> None:
        """收集 S-Rank 數據"""
        try:
            if self.s_rank_storage is None:
                try:
                    from jgod.s_rank_engine.storage import SRankFactorStorageV1
                    self.s_rank_storage = SRankFactorStorageV1()
                except Exception as e:
                    logger.debug(f"S-Rank Storage not available: {e}")
                    return
            
            # Load latest factors for current distribution
            latest_factors = self.s_rank_storage.load_latest_factors()
            
            if latest_factors:
                # Calculate distribution
                distribution = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0}
                for factor in latest_factors:
                    rank = factor.rank_level
                    if rank in distribution:
                        distribution[rank] += 1
                summary.s_rank_distribution = distribution
            
            # Count recalculations in last 24 hours
            cutoff_time = datetime.now() - timedelta(hours=HOURS_FOR_S_RANK_RECALCULATIONS)
            
            # Load all historical factors and count unique calculation timestamps
            try:
                all_factors = self.s_rank_storage.load_all() if hasattr(self.s_rank_storage, "load_all") else []
                
                # Group by calculated_at timestamp (same timestamp = same calculation)
                calculation_times = set()
                for factor in all_factors:
                    if factor.calculated_at >= cutoff_time:
                        # Round to hour to group calculations
                        calc_hour = factor.calculated_at.replace(minute=0, second=0, microsecond=0)
                        calculation_times.add(calc_hour)
                
                summary.s_rank_recalculations_last_24h = len(calculation_times)
                
            except Exception as e:
                logger.debug(f"Error counting S-Rank recalculations: {e}")
            
            # Calculate strategy degradation (A/B -> C/D) in last 7 days
            try:
                cutoff_date = date.today() - timedelta(days=DAYS_FOR_STRATEGY_DEGRADATION)
                
                # Get factors from 7 days ago and now
                factors_7d_ago = self.s_rank_storage.load_historical_factors(cutoff_date)
                factors_now = latest_factors
                
                # Build rank maps
                rank_7d_ago = {f.strategy_id: f.rank_level for f in factors_7d_ago}
                rank_now = {f.strategy_id: f.rank_level for f in factors_now}
                
                degradation_count = 0
                rank_order = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}
                
                for strategy_id, current_rank in rank_now.items():
                    old_rank = rank_7d_ago.get(strategy_id)
                    if old_rank:
                        old_level = rank_order.get(old_rank, 0)
                        current_level = rank_order.get(current_rank, 0)
                        # Degradation: A/B (4 or 3) -> C/D (2 or 1)
                        if old_level >= 3 and current_level <= 2:
                            degradation_count += 1
                
                summary.s_rank_strategy_degradation_7d = degradation_count
                
            except Exception as e:
                logger.debug(f"Error calculating strategy degradation: {e}")
                
        except Exception as e:
            logger.warning(f"Error collecting S-Rank data: {e}", exc_info=True)
    
    def _collect_alert_data(self, summary: KnowledgeGovernanceSummary) -> None:
        """收集 Alert 數據"""
        try:
            if self.alert_engine is None:
                try:
                    from jgod.doctrine_alert.engine import DoctrineAlertEngineV1
                    from jgod.doctrine_alert.config import DoctrineAlertConfig
                    config = DoctrineAlertConfig()
                    self.alert_engine = DoctrineAlertEngineV1(config=config)
                except Exception as e:
                    logger.debug(f"Alert Engine not available: {e}")
                    return
            
            # Scan all alerts and count critical
            try:
                if hasattr(self.alert_engine, "scan_all"):
                    all_alerts = self.alert_engine.scan_all()
                    summary.critical_alerts_active = sum(
                        1 for alert in all_alerts
                        if (alert.severity.value == "CRITICAL" if hasattr(alert.severity, "value") else str(alert.severity) == "CRITICAL")
                    )
                else:
                    logger.debug("scan_all not available, skipping critical_alerts_active")
            except Exception as e:
                logger.debug(f"Error getting critical alerts: {e}")
                
        except Exception as e:
            logger.warning(f"Error collecting Alert data: {e}", exc_info=True)
    
    def load_all(self) -> list:
        """Load all S-Rank factors (helper for storage compatibility)"""
        if hasattr(self.s_rank_storage, "load_all"):
            return self.s_rank_storage.load_all()
        # Fallback: read file directly
        import json
        from pathlib import Path
        from jgod.s_rank_engine.config import S_RANK_REPORTS_PATH
        
        factors = []
        if S_RANK_REPORTS_PATH.exists():
            with open(S_RANK_REPORTS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            from jgod.s_rank_engine.storage import SRankFactorStorageV1
                            storage = SRankFactorStorageV1()
                            factor = storage._dict_to_factor(data)
                            factors.append(factor)
                        except Exception:
                            pass
        return factors

