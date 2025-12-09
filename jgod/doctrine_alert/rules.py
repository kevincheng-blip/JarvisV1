"""Doctrine Alert Rules

Rule evaluation functions for different alert sources.
"""

import logging
from typing import List
from datetime import datetime
import uuid

from jgod.doctrine_alert.models import (
    AlertContext,
    RuleConfig,
    DoctrineAlertItem,
    DoctrineAlertSeverity,
    DoctrineAlertSource,
)

logger = logging.getLogger(__name__)


def _check_threshold(metric_value: float, threshold: float, direction: str) -> bool:
    """Check if metric value triggers threshold based on direction"""
    if direction == "gt":
        return metric_value > threshold
    elif direction == "ge":
        return metric_value >= threshold
    elif direction == "lt":
        return metric_value < threshold
    elif direction == "le":
        return metric_value <= threshold
    elif direction == "eq":
        return abs(metric_value - threshold) < 1e-6
    else:
        logger.warning(f"Unknown direction: {direction}, defaulting to ge")
        return metric_value >= threshold


def _create_alert(
    ctx: AlertContext,
    rule: RuleConfig,
    metric_value: float,
) -> DoctrineAlertItem:
    """Create a DoctrineAlertItem from context and rule"""
    
    # Generate alert title and message based on rule
    if rule.id == "POSITION_MAX_WEIGHT":
        title = "單一持股過度集中"
        message = f"{ctx.symbol} ({ctx.name or 'N/A'}) 持倉權重 {metric_value:.2%} 超過上限 {rule.threshold:.2%}"
    elif rule.id.startswith("CONFLICT_"):
        if rule.severity == DoctrineAlertSeverity.CRITICAL:
            title = "策略衝突嚴重"
            message = f"{ctx.symbol} ({ctx.name or 'N/A'}) 策略衝突分數 {metric_value:.1f} 達到嚴重級別"
        else:
            title = "策略分歧明顯"
            message = f"{ctx.symbol} ({ctx.name or 'N/A'}) 策略衝突分數 {metric_value:.1f} 超過警示門檻"
    elif rule.id.startswith("PREDICTION_"):
        title = "預測信心過高"
        message = f"{ctx.symbol} ({ctx.name or 'N/A'}) Final Score {metric_value:.2f} 超過警示門檻"
    else:
        title = f"風險警示: {rule.metric_name}"
        message = f"{ctx.symbol} ({ctx.name or 'N/A'}) {rule.metric_name} {metric_value:.2f} 觸發 {rule.severity.value} 級別警示"
    
    alert_id = f"{rule.id}_{ctx.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    return DoctrineAlertItem(
        id=alert_id,
        symbol=ctx.symbol,
        name=ctx.name,
        severity=rule.severity,
        source=rule.source,
        title=title,
        message=message,
        metric_name=rule.metric_name,
        metric_value=metric_value,
        threshold=rule.threshold,
        conflict_score=ctx.conflict_score,
        consensus_score=ctx.consensus_score,
        final_score=ctx.final_score,
        raw_score=ctx.raw_score,
        doctrine_refs=rule.doctrine_refs,
        tags=rule.tags,
        created_at=datetime.now(),
    )


def evaluate_position_rules(
    ctx: AlertContext,
    rules: List[RuleConfig],
) -> List[DoctrineAlertItem]:
    """Evaluate position-based alert rules"""
    alerts = []
    
    for rule in rules:
        if rule.source != DoctrineAlertSource.POSITION:
            continue
        
        # Get metric value from context
        metric_value = None
        
        if rule.metric_name == "position_weight":
            metric_value = ctx.position_weight
        
        if metric_value is None:
            continue
        
        # Check threshold
        if _check_threshold(metric_value, rule.threshold, rule.direction):
            alert = _create_alert(ctx, rule, metric_value)
            alerts.append(alert)
            logger.debug(
                f"Position rule {rule.id} triggered for {ctx.symbol}: "
                f"{metric_value} {rule.direction} {rule.threshold}"
            )
    
    return alerts


def evaluate_prediction_rules(
    ctx: AlertContext,
    rules: List[RuleConfig],
) -> List[DoctrineAlertItem]:
    """Evaluate prediction-based alert rules"""
    alerts = []
    
    for rule in rules:
        if rule.source != DoctrineAlertSource.PREDICTION:
            continue
        
        # Get metric value from context
        metric_value = None
        
        if rule.metric_name == "final_score":
            metric_value = ctx.final_score
        
        if metric_value is None:
            continue
        
        # Check threshold
        if _check_threshold(metric_value, rule.threshold, rule.direction):
            alert = _create_alert(ctx, rule, metric_value)
            alerts.append(alert)
            logger.debug(
                f"Prediction rule {rule.id} triggered for {ctx.symbol}: "
                f"{metric_value} {rule.direction} {rule.threshold}"
            )
    
    return alerts


def evaluate_conflict_rules(
    ctx: AlertContext,
    rules: List[RuleConfig],
) -> List[DoctrineAlertItem]:
    """Evaluate conflict-based alert rules"""
    alerts = []
    
    for rule in rules:
        if rule.source != DoctrineAlertSource.CONFLICT:
            continue
        
        # Get metric value from context
        metric_value = None
        
        if rule.metric_name == "conflict_score":
            metric_value = ctx.conflict_score
        
        if metric_value is None:
            continue
        
        # Check threshold
        if _check_threshold(metric_value, rule.threshold, rule.direction):
            alert = _create_alert(ctx, rule, metric_value)
            alerts.append(alert)
            logger.debug(
                f"Conflict rule {rule.id} triggered for {ctx.symbol}: "
                f"{metric_value} {rule.direction} {rule.threshold}"
            )
    
    return alerts

