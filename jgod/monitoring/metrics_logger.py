"""
Metrics Logger: Production metrics tracking

v0.6.12-A12: Metrics logging for observability
"""

import logging
import time
from typing import Dict, Optional, List
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class MetricsLogger:
    """
    Metrics Logger: Tracks production metrics.
    
    v0.6.12-A12: Logs metrics for observability.
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize MetricsLogger.
        
        Args:
            max_history: Maximum number of metric entries to keep in memory
        """
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, List[float]] = defaultdict(list)
    
    def log_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Log a metric.
        
        Args:
            name: Metric name (e.g., "tick_duration_ms")
            value: Metric value
            tags: Optional tags (e.g., {"symbol": "2330"})
        """
        timestamp = datetime.now().isoformat()
        entry = {
            "name": name,
            "value": value,
            "timestamp": timestamp,
            "tags": tags or {},
        }
        
        self.metrics[name].append(entry)
        
        # Update counters for success/error metrics
        if name.endswith("_success") or name.endswith("_error"):
            self.counters[name] += 1
    
    def log_timer(
        self,
        name: str,
        duration_ms: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Log a timer metric.
        
        Args:
            name: Timer name (e.g., "decide_latency_ms")
            duration_ms: Duration in milliseconds
            tags: Optional tags
        """
        self.log_metric(name, duration_ms, tags)
        self.timers[name].append(duration_ms)
    
    def increment_counter(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Counter name (e.g., "ticks_success")
            tags: Optional tags
        """
        self.counters[name] += 1
        self.log_metric(name, self.counters[name], tags)
    
    def snapshot(self) -> Dict:
        """
        Get latest metrics snapshot.
        
        Returns:
            Dict with latest metrics values
        """
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
            "counters": dict(self.counters),
            "averages": {},
        }
        
        # Get latest value for each metric
        for name, entries in self.metrics.items():
            if entries:
                snapshot["metrics"][name] = entries[-1]["value"]
        
        # Calculate averages for timers
        for name, durations in self.timers.items():
            if durations:
                snapshot["averages"][name] = sum(durations) / len(durations)
        
        return snapshot
    
    def get_metric_history(
        self,
        name: str,
        limit: int = 100,
    ) -> List[Dict]:
        """
        Get metric history.
        
        Args:
            name: Metric name
            limit: Maximum number of entries to return
            
        Returns:
            List of metric entries (newest first)
        """
        if name not in self.metrics:
            return []
        
        entries = list(self.metrics[name])
        entries.reverse()  # Newest first
        return entries[:limit]

