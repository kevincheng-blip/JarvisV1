"""
Intelligence & Learning Status: Monitoring AI evolution and knowledge acquisition

v0.6.13-A13: Intelligence status tracking for Control Tower observability
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from datetime import datetime


# Status label specifications (fixed strings)
EvolutionStatusLabel = Literal["STABLE", "EVOLVING", "REGRESSIVE", "ERROR", "COMPLETE"]
AcquisitionStatusLabel = Literal[
    "ONLINE", "DELAYED", "OFFLINE", "READING", "CLASSIFYING", 
    "INTEGRATING", "RUNNING", "PAUSED", "COMPLETE", "MAINTENANCE", "IDLE"
]
EventTypeLabel = Literal["NEW", "DEPRECATED", "TUNED", "AUTO_APPLY", "ROLLED_BACK", "ERROR"]


@dataclass
class EvolutionStatus:
    """Evolution status for strategy/thought/method layers."""
    layer: str  # "strategy", "thought", "method"
    progress: int  # 0-100
    status: EvolutionStatusLabel
    last_updated: str  # ISO timestamp
    details: Dict = field(default_factory=dict)  # Additional details


@dataclass
class AcquisitionActivity:
    """Acquisition activity status."""
    name: str  # e.g., "Data Ingestion", "Feature Pipeline", "M50 Knowledge", "L10 Knowledge", "News Sentiment"
    status: AcquisitionStatusLabel
    detail: str  # Human-readable detail
    progress: int  # 0-100
    updated_at: str  # ISO timestamp


@dataclass
class EvolutionEvent:
    """Evolution event (NEW/DEPRECATED/TUNED/ROLLED_BACK)."""
    type: EventTypeLabel
    layer: str  # "strategy", "thought", "method"
    object_id: str  # e.g., patch_id, feature_name, strategy_id
    summary: str  # Traditional Chinese summary
    snapshot_id: Optional[str] = None
    doctrine_version: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class IntelligenceStatusSnapshot:
    """Complete intelligence status snapshot."""
    evolution: List[EvolutionStatus]  # strategy, thought, method
    activities: List[AcquisitionActivity]
    recent_events: List[EvolutionEvent]  # Recent N events
    health_flags: Dict[str, str]  # e.g., {"data_ingestion": "OK", "decide_latency": "WARN"}
    snapshot_id: str  # Unique snapshot ID
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


def compute_evolution_progress(
    layer: str,
    events: List[EvolutionEvent],
    *,
    window_days: int = 30,
) -> int:
    """
    Compute evolution progress for a layer (MVP calculation).
    
    Args:
        layer: Layer name ("strategy", "thought", "method")
        events: List of evolution events
        window_days: Time window in days
        
    Returns:
        Progress percentage (0-100)
    """
    from datetime import datetime, timedelta
    
    cutoff_date = (datetime.now() - timedelta(days=window_days)).isoformat()
    
    # Filter events for this layer within window
    layer_events = [
        e for e in events
        if e.layer == layer and e.created_at >= cutoff_date
    ]
    
    if layer == "strategy":
        # strategy_progress = min(100, 10 * count(strategy events last 30d))
        progress = min(100, 10 * len(layer_events))
    elif layer == "thought":
        # thought_progress = min(100, 10 * count(thought tuned events last 30d))
        tuned_events = [e for e in layer_events if e.type in ("TUNED", "AUTO_APPLY")]
        progress = min(100, 10 * len(tuned_events))
    elif layer == "method":
        # method_progress = min(100, 100 * active_methods/total_methods)
        # MVP: Use count of NEW events as proxy for active methods
        new_events = [e for e in layer_events if e.type == "NEW"]
        # Assume total_methods = 10 (proxy)
        active_methods = len(new_events)
        total_methods = 10
        progress = min(100, int(100 * active_methods / total_methods)) if total_methods > 0 else 0
    else:
        progress = 0
    
    return progress


def compute_evolution_status(
    layer: str,
    events: List[EvolutionEvent],
    *,
    window_days: int = 30,
) -> EvolutionStatusLabel:
    """
    Compute evolution status label for a layer.
    
    Args:
        layer: Layer name
        events: List of evolution events
        window_days: Time window in days
        
    Returns:
        Evolution status label
    """
    from datetime import datetime, timedelta
    
    cutoff_date = (datetime.now() - timedelta(days=window_days)).isoformat()
    
    layer_events = [
        e for e in events
        if e.layer == layer and e.created_at >= cutoff_date
    ]
    
    if not layer_events:
        return "STABLE"
    
    # Check for errors
    if any(e.type == "ERROR" for e in layer_events):
        return "ERROR"
    
    # Check for regressions (ROLLED_BACK)
    if any(e.type == "ROLLED_BACK" for e in layer_events):
        return "REGRESSIVE"
    
    # Check for recent activity
    recent_new = [e for e in layer_events if e.type in ("NEW", "TUNED", "AUTO_APPLY")]
    if len(recent_new) >= 3:
        return "EVOLVING"
    
    return "STABLE"

