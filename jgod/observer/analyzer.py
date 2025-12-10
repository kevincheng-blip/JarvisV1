"""Governance Analyzer

KPI calculation and anomaly detection for knowledge governance.
"""

import logging
from typing import List

from jgod.observer.models import KnowledgeGovernanceSummary, StabilityAlert
from jgod.observer.config import (
    THRESHOLD_PENDING_REVIEW_CRITICAL,
    THRESHOLD_PENDING_REVIEW_WARNING,
    THRESHOLD_SIM_APPROVE_RATE_CRITICAL,
    THRESHOLD_SIM_APPROVE_RATE_WARNING,
    THRESHOLD_STRATEGY_DEGRADATION_CRITICAL,
    THRESHOLD_STRATEGY_DEGRADATION_WARNING,
)

logger = logging.getLogger(__name__)


class GovernanceAnalyzer:
    """KPI 計算與異常檢測"""
    
    def check_stability_alerts(self, summary: KnowledgeGovernanceSummary) -> List[StabilityAlert]:
        """
        根據預設閾值，檢測系統穩定性異常
        
        Returns:
            List of StabilityAlert objects
        """
        alerts: List[StabilityAlert] = []
        
        # 1. DMC 待審核條目過多
        if summary.pending_review_count >= THRESHOLD_PENDING_REVIEW_CRITICAL:
            alerts.append(StabilityAlert(
                severity="CRITICAL",
                message=f"DMC 待審核條目過多 ({summary.pending_review_count} 條)，知識治理流程阻塞。建議優先處理高優先級條目。"
            ))
        elif summary.pending_review_count >= THRESHOLD_PENDING_REVIEW_WARNING:
            alerts.append(StabilityAlert(
                severity="WARNING",
                message=f"DMC 待審核條目較多 ({summary.pending_review_count} 條)，建議加快審核流程。"
            ))
        
        # 2. Rule Sim 批准率過低
        if summary.sim_approve_rate_30d > 0:  # Only check if there are simulations
            if summary.sim_approve_rate_30d < THRESHOLD_SIM_APPROVE_RATE_CRITICAL:
                alerts.append(StabilityAlert(
                    severity="CRITICAL",
                    message=f"Rule Sim 批准率過低 ({summary.sim_approve_rate_30d:.1%})，低於 50%。修正提案品質需審視，建議檢查規則修正邏輯。"
                ))
            elif summary.sim_approve_rate_30d < THRESHOLD_SIM_APPROVE_RATE_WARNING:
                alerts.append(StabilityAlert(
                    severity="WARNING",
                    message=f"Rule Sim 批准率較低 ({summary.sim_approve_rate_30d:.1%})，低於 70%。建議審視修正提案品質。"
                ))
        
        # 3. 策略嚴重退化
        if summary.s_rank_strategy_degradation_7d >= THRESHOLD_STRATEGY_DEGRADATION_CRITICAL:
            alerts.append(StabilityAlert(
                severity="CRITICAL",
                message=f"過去 7 天內有 {summary.s_rank_strategy_degradation_7d} 個策略從 A/B 級降至 C/D 級。建議檢查策略邏輯或市場環境變化。"
            ))
        elif summary.s_rank_strategy_degradation_7d >= THRESHOLD_STRATEGY_DEGRADATION_WARNING:
            alerts.append(StabilityAlert(
                severity="WARNING",
                message=f"過去 7 天內有 {summary.s_rank_strategy_degradation_7d} 個策略降級。建議監控策略表現。"
            ))
        
        # 4. Critical Alerts 過多
        if summary.critical_alerts_active >= 5:
            alerts.append(StabilityAlert(
                severity="CRITICAL",
                message=f"當前有 {summary.critical_alerts_active} 個 CRITICAL 警報活躍。建議優先處理高風險警報。"
            ))
        elif summary.critical_alerts_active >= 3:
            alerts.append(StabilityAlert(
                severity="WARNING",
                message=f"當前有 {summary.critical_alerts_active} 個 CRITICAL 警報活躍。建議檢查並處理。"
            ))
        
        # 5. S-Rank 重新計算頻繁
        if summary.s_rank_recalculations_last_24h >= 5:
            alerts.append(StabilityAlert(
                severity="WARNING",
                message=f"過去 24 小時內 S-Rank 重新計算 {summary.s_rank_recalculations_last_24h} 次。計算頻率過高，可能影響系統穩定性。"
            ))
        
        logger.debug(f"Generated {len(alerts)} stability alerts")
        
        return alerts

