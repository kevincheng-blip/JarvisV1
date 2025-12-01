"""Error Event and Analysis Result Data Structures

This module defines the data structures for error events and their analysis results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


# Error classification constants
CLASS_UTILIZATION_GAP = "UTILIZATION_GAP"
CLASS_FORM_INSUFFICIENT = "FORM_INSUFFICIENT"
CLASS_KNOWLEDGE_GAP = "KNOWLEDGE_GAP"
CLASS_UNKNOWN = "UNKNOWN"


@dataclass
class ErrorEvent:
    """Error event data structure
    
    Represents a single prediction error or trading mistake that needs to be analyzed.
    
    Attributes:
        id: Unique identifier for this error event
        timestamp: When the error occurred (datetime or ISO format string)
        symbol: Stock symbol (e.g., "2330")
        timeframe: Trading timeframe (e.g., "1m", "5m", "1d")
        side: Trade direction ("long", "short", or None)
        predicted_outcome: What the system predicted (e.g., "up", "down", "range", "hit_tp", "hit_sl")
        actual_outcome: What actually happened
        pnl: Profit/loss for this trade/decision (if applicable)
        error_type: Type of error (e.g., "direction", "timing", "stop_loss", "take_profit")
        tags: List of tags for categorization
        used_signals: List of signal/factor IDs that were used in this decision
        used_rules: List of RULE IDs that were actually applied
        regime: Dictionary containing market regime/volatility information
        context: Additional context (e.g., strategy name, market conditions)
        notes: Additional notes or observations
    """
    id: str
    timestamp: str | datetime
    symbol: str
    timeframe: str
    side: Optional[str] = None  # "long" / "short" / None
    predicted_outcome: str = ""
    actual_outcome: str = ""
    pnl: Optional[float] = None
    error_type: Optional[str] = None  # "direction", "timing", "stop_loss", "take_profit"
    tags: List[str] = field(default_factory=list)
    used_signals: List[str] = field(default_factory=list)
    used_rules: List[str] = field(default_factory=list)
    regime: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ErrorEvent:
        """Create ErrorEvent from dictionary
        
        Args:
            data: Dictionary containing error event data
        
        Returns:
            ErrorEvent instance
        """
        # Handle timestamp conversion
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                pass  # Keep as string if parsing fails
        
        return cls(
            id=data.get("id", ""),
            timestamp=timestamp or datetime.now(),
            symbol=data.get("symbol", ""),
            timeframe=data.get("timeframe", ""),
            side=data.get("side"),
            predicted_outcome=data.get("predicted_outcome", ""),
            actual_outcome=data.get("actual_outcome", ""),
            pnl=data.get("pnl"),
            error_type=data.get("error_type"),
            tags=data.get("tags", []),
            used_signals=data.get("used_signals", []),
            used_rules=data.get("used_rules", []),
            regime=data.get("regime"),
            context=data.get("context"),
            notes=data.get("notes")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ErrorEvent to dictionary
        
        Returns:
            Dictionary representation of ErrorEvent
        """
        result = {
            "id": self.id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "predicted_outcome": self.predicted_outcome,
            "actual_outcome": self.actual_outcome,
        }
        
        # Handle timestamp
        if isinstance(self.timestamp, datetime):
            result["timestamp"] = self.timestamp.isoformat()
        else:
            result["timestamp"] = str(self.timestamp)
        
        # Add optional fields
        if self.side:
            result["side"] = self.side
        if self.pnl is not None:
            result["pnl"] = self.pnl
        if self.error_type:
            result["error_type"] = self.error_type
        if self.tags:
            result["tags"] = self.tags
        if self.used_signals:
            result["used_signals"] = self.used_signals
        if self.used_rules:
            result["used_rules"] = self.used_rules
        if self.regime:
            result["regime"] = self.regime
        if self.context:
            result["context"] = self.context
        if self.notes:
            result["notes"] = self.notes
        
        return result


@dataclass
class ErrorAnalysisResult:
    """Error analysis result data structure
    
    Contains the results of analyzing an error event against the Knowledge Brain.
    
    Attributes:
        event_id: ID of the error event being analyzed
        classification: Error classification (UTILIZATION_GAP, FORM_INSUFFICIENT, KNOWLEDGE_GAP, UNKNOWN)
        related_items: Simplified summaries of related KnowledgeItems (id/type/title/score)
        utilization_gap_reasons: List of reasons for utilization gap classification
        knowledge_gap_notes: List of notes about knowledge gaps
        draft_rule_suggestions: List of suggested draft rules
        draft_concept_suggestions: List of suggested draft concepts
        follow_up_actions: List of recommended follow-up actions
        raw_query: Query string used to search the knowledge base
        created_at: When this analysis was created (datetime or ISO format string)
    """
    event_id: str
    classification: str  # UTILIZATION_GAP / FORM_INSUFFICIENT / KNOWLEDGE_GAP / UNKNOWN
    related_items: List[Dict[str, Any]] = field(default_factory=list)
    utilization_gap_reasons: List[str] = field(default_factory=list)
    knowledge_gap_notes: List[str] = field(default_factory=list)
    draft_rule_suggestions: List[str] = field(default_factory=list)
    draft_concept_suggestions: List[str] = field(default_factory=list)
    follow_up_actions: List[str] = field(default_factory=list)
    raw_query: str = ""
    created_at: str | datetime = field(default_factory=datetime.now)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ErrorAnalysisResult:
        """Create ErrorAnalysisResult from dictionary
        
        Args:
            data: Dictionary containing analysis result data
        
        Returns:
            ErrorAnalysisResult instance
        """
        # Handle timestamp conversion
        created_at = data.get("created_at", datetime.now())
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                pass
        
        return cls(
            event_id=data.get("event_id", ""),
            classification=data.get("classification", CLASS_UNKNOWN),
            related_items=data.get("related_items", []),
            utilization_gap_reasons=data.get("utilization_gap_reasons", []),
            knowledge_gap_notes=data.get("knowledge_gap_notes", []),
            draft_rule_suggestions=data.get("draft_rule_suggestions", []),
            draft_concept_suggestions=data.get("draft_concept_suggestions", []),
            follow_up_actions=data.get("follow_up_actions", []),
            raw_query=data.get("raw_query", ""),
            created_at=created_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ErrorAnalysisResult to dictionary
        
        Returns:
            Dictionary representation of ErrorAnalysisResult
        """
        result = {
            "event_id": self.event_id,
            "classification": self.classification,
            "related_items": self.related_items,
            "utilization_gap_reasons": self.utilization_gap_reasons,
            "knowledge_gap_notes": self.knowledge_gap_notes,
            "draft_rule_suggestions": self.draft_rule_suggestions,
            "draft_concept_suggestions": self.draft_concept_suggestions,
            "follow_up_actions": self.follow_up_actions,
            "raw_query": self.raw_query,
        }
        
        # Handle timestamp
        if isinstance(self.created_at, datetime):
            result["created_at"] = self.created_at.isoformat()
        else:
            result["created_at"] = str(self.created_at)
        
        return result

