"""Doctrine Alert Engine v1

Unified Doctrine risk alert scanning for positions, predictions, and conflicts.
"""

import logging
from typing import List, Optional
from datetime import date

from jgod.doctrine_alert.models import (
    AlertContext,
    DoctrineAlertItem,
    DoctrineAlertSeverity,
    DoctrineAlertSource,
)
from jgod.doctrine_alert.config import DoctrineAlertConfig
from jgod.doctrine_alert.data_access import (
    get_current_positions,
    get_latest_predictions,
    get_conflicts_for_symbols,
    PositionRow,
    PredictionRow,
)
from jgod.doctrine_alert.rules import (
    evaluate_position_rules,
    evaluate_prediction_rules,
    evaluate_conflict_rules,
)

logger = logging.getLogger(__name__)


class DoctrineAlertEngineV1:
    """Doctrine Alert Engine v1
    
    Provides unified scanning for Doctrine risk alerts across positions, predictions, and conflicts.
    """
    
    def __init__(self, config: DoctrineAlertConfig):
        """
        Initialize Doctrine Alert Engine
        
        Args:
            config: DoctrineAlertConfig with rule configurations
        """
        self.config = config
        logger.info(f"DoctrineAlertEngineV1 initialized with {len(self.config._enabled_rules)} enabled rules")
    
    def _build_alert_context(
        self,
        symbol: str,
        name: Optional[str] = None,
        position: Optional[PositionRow] = None,
        prediction: Optional[PredictionRow] = None,
        conflict_item: Optional = None,
    ) -> AlertContext:
        """Build AlertContext from various data sources"""
        ctx = AlertContext(symbol=symbol, name=name)
        
        # Add position data
        if position:
            ctx.position_weight = position.weight
            ctx.liquidity_score = position.liquidity_score
        
        # Add prediction data
        if prediction:
            ctx.raw_score = prediction.raw_score
            ctx.final_score = prediction.final_score
        
        # Add conflict data
        if conflict_item:
            ctx.conflict_score = conflict_item.conflict_score
            ctx.consensus_score = conflict_item.consensus_score
        
        return ctx
    
    def _deduplicate_alerts(self, alerts: List[DoctrineAlertItem]) -> List[DoctrineAlertItem]:
        """Remove duplicate alerts (same rule + symbol + severity)"""
        seen = set()
        unique_alerts = []
        
        for alert in alerts:
            # Create a key based on rule ID (from alert.id), symbol, and severity
            # Extract rule ID from alert.id (format: RULE_ID_SYMBOL_TIMESTAMP_UUID)
            parts = alert.id.split("_")
            if len(parts) >= 2:
                rule_id = parts[0]
                key = (rule_id, alert.symbol, alert.severity)
                
                if key not in seen:
                    seen.add(key)
                    unique_alerts.append(alert)
            else:
                # Fallback: use full ID
                if alert.id not in seen:
                    seen.add(alert.id)
                    unique_alerts.append(alert)
        
        return unique_alerts
    
    def scan_symbol(self, symbol: str, db_session=None) -> List[DoctrineAlertItem]:
        """
        Scan alerts for a single symbol.
        
        Args:
            symbol: Stock symbol
            db_session: Database session (optional)
        
        Returns:
            List of DoctrineAlertItem objects for the symbol
        """
        logger.info(f"Scanning alerts for symbol: {symbol}")
        
        all_alerts = []
        
        # Get position data
        positions = get_current_positions(db_session=db_session)
        position = next((p for p in positions if p.symbol == symbol), None)
        
        # Get prediction data
        predictions = get_latest_predictions(limit=None, db_session=db_session)
        prediction = next((p for p in predictions if p.symbol == symbol), None)
        
        # Get conflict data
        conflicts = get_conflicts_for_symbols([symbol], db_session=db_session)
        conflict_item = conflicts.get(symbol)
        
        # Get stock name
        name = None
        if position:
            name = position.name
        elif prediction:
            name = prediction.name
        elif conflict_item:
            name = conflict_item.name
        
        # Build context
        ctx = self._build_alert_context(
            symbol=symbol,
            name=name,
            position=position,
            prediction=prediction,
            conflict_item=conflict_item,
        )
        
        # Evaluate rules
        position_rules = self.config.get_rules_by_source(DoctrineAlertSource.POSITION)
        if position_rules and position:
            alerts = evaluate_position_rules(ctx, position_rules)
            all_alerts.extend(alerts)
        
        prediction_rules = self.config.get_rules_by_source(DoctrineAlertSource.PREDICTION)
        if prediction_rules and prediction:
            alerts = evaluate_prediction_rules(ctx, prediction_rules)
            all_alerts.extend(alerts)
        
        conflict_rules = self.config.get_rules_by_source(DoctrineAlertSource.CONFLICT)
        if conflict_rules and conflict_item:
            alerts = evaluate_conflict_rules(ctx, conflict_rules)
            all_alerts.extend(alerts)
        
        # Deduplicate
        all_alerts = self._deduplicate_alerts(all_alerts)
        
        logger.info(f"Found {len(all_alerts)} alerts for symbol {symbol}")
        return all_alerts
    
    def scan_all(self, max_items: Optional[int] = None, db_session=None) -> List[DoctrineAlertItem]:
        """
        Scan all alerts across positions, predictions, and conflicts.
        
        Args:
            max_items: Maximum number of alerts to return (None = all)
            db_session: Database session (optional)
        
        Returns:
            List of DoctrineAlertItem objects, sorted by severity and metric_value
        """
        logger.info("Scanning all Doctrine alerts")
        
        all_alerts = []
        
        # Get all data
        positions = get_current_positions(db_session=db_session)
        predictions = get_latest_predictions(limit=100, db_session=db_session)  # Limit predictions
        prediction_symbols = [p.symbol for p in predictions]
        conflict_symbols = [p.symbol for p in positions if p.symbol] + prediction_symbols
        conflicts = get_conflicts_for_symbols(conflict_symbols, db_session=db_session)
        
        # Collect all unique symbols
        all_symbols = set()
        if positions:
            all_symbols.update(p.symbol for p in positions)
        if predictions:
            all_symbols.update(p.symbol for p in predictions)
        if conflicts:
            all_symbols.update(conflicts.keys())
        
        # Scan each symbol
        for symbol in all_symbols:
            position = next((p for p in positions if p.symbol == symbol), None)
            prediction = next((p for p in predictions if p.symbol == symbol), None)
            conflict_item = conflicts.get(symbol)
            
            # Get name
            name = None
            if position:
                name = position.name
            elif prediction:
                name = prediction.name
            elif conflict_item:
                name = conflict_item.name
            
            # Build context
            ctx = self._build_alert_context(
                symbol=symbol,
                name=name,
                position=position,
                prediction=prediction,
                conflict_item=conflict_item,
            )
            
            # Evaluate rules
            position_rules = self.config.get_rules_by_source(DoctrineAlertSource.POSITION)
            if position_rules and position:
                alerts = evaluate_position_rules(ctx, position_rules)
                all_alerts.extend(alerts)
            
            prediction_rules = self.config.get_rules_by_source(DoctrineAlertSource.PREDICTION)
            if prediction_rules and prediction:
                alerts = evaluate_prediction_rules(ctx, prediction_rules)
                all_alerts.extend(alerts)
            
            conflict_rules = self.config.get_rules_by_source(DoctrineAlertSource.CONFLICT)
            if conflict_rules and conflict_item:
                alerts = evaluate_conflict_rules(ctx, conflict_rules)
                all_alerts.extend(alerts)
        
        # Deduplicate
        all_alerts = self._deduplicate_alerts(all_alerts)
        
        # Sort: severity (CRITICAL > WARNING > INFO) -> metric_value (desc) -> symbol
        severity_order = {
            DoctrineAlertSeverity.CRITICAL: 0,
            DoctrineAlertSeverity.WARNING: 1,
            DoctrineAlertSeverity.INFO: 2,
        }
        all_alerts.sort(
            key=lambda a: (
                severity_order.get(a.severity, 99),
                -(a.metric_value or 0.0),
                a.symbol,
            )
        )
        
        # Apply limit
        if max_items:
            all_alerts = all_alerts[:max_items]
        
        logger.info(f"Found {len(all_alerts)} total Doctrine alerts")
        return all_alerts

