"""
Alerting Service: Production alerting

v0.6.12-A12: Alerting for critical issues
"""

import logging
from typing import Dict, List, Literal, Optional
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


AlertLevel = Literal["INFO", "WARN", "CRITICAL"]


class AlertingService:
    """
    Alerting Service: Sends alerts for critical issues.
    
    v0.6.12-A12: Alerting for production monitoring.
    """
    
    def __init__(self, storage_path: Optional[Path] = None, max_alerts: int = 1000):
        """
        Initialize AlertingService.
        
        Args:
            storage_path: Optional custom storage path (default: data/monitoring/alerts.jsonl)
            max_alerts: Maximum number of alerts to keep in memory
        """
        if storage_path is None:
            project_root = Path(__file__).resolve().parents[2]
            storage_dir = project_root / "data" / "monitoring"
            storage_dir.mkdir(parents=True, exist_ok=True)
            storage_path = storage_dir / "alerts.jsonl"
        
        self.storage_path = storage_path
        self.max_alerts = max_alerts
        self.alerts: List[Dict] = []
    
    def send_alert(
        self,
        level: AlertLevel,
        message: str,
        context: Optional[Dict] = None,
    ) -> None:
        """
        Send an alert.
        
        Args:
            level: Alert level (INFO, WARN, CRITICAL)
            message: Alert message
            context: Optional context dict
        """
        alert = {
            "level": level,
            "message": message,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
        }
        
        # Add to memory
        self.alerts.append(alert)
        if len(self.alerts) > self.max_alerts:
            self.alerts.pop(0)  # Remove oldest
        
        # Log based on level
        if level == "CRITICAL":
            logger.critical(f"ALERT [{level}]: {message}", extra={"context": context})
        elif level == "WARN":
            logger.warning(f"ALERT [{level}]: {message}", extra={"context": context})
        else:
            logger.info(f"ALERT [{level}]: {message}", extra={"context": context})
        
        # Persist to file (append-only JSONL)
        try:
            with open(self.storage_path, "a", encoding="utf-8") as f:
                json.dump(alert, f, ensure_ascii=False)
                f.write("\n")
        except Exception as e:
            logger.error(f"Failed to persist alert: {e}", exc_info=True)
    
    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        Get recent alerts.
        
        Args:
            level: Optional filter by level
            limit: Maximum number of alerts to return
            
        Returns:
            List of alerts (newest first)
        """
        alerts = self.alerts
        
        if level:
            alerts = [a for a in alerts if a["level"] == level]
        
        # Return newest first
        alerts.reverse()
        return alerts[:limit]
    
    def get_critical_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent CRITICAL alerts."""
        return self.get_alerts(level="CRITICAL", limit=limit)
    
    def get_warn_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent WARN alerts."""
        return self.get_alerts(level="WARN", limit=limit)

