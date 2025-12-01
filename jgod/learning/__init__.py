"""J-GOD Error Learning Engine Module

This module provides error learning capabilities for the J-GOD trading system,
allowing the system to learn from prediction errors by querying the Knowledge Brain
and classifying root causes.
"""

from jgod.learning.error_event import (
    ErrorEvent,
    ErrorAnalysisResult,
    CLASS_UTILIZATION_GAP,
    CLASS_FORM_INSUFFICIENT,
    CLASS_KNOWLEDGE_GAP,
    CLASS_UNKNOWN
)
from jgod.learning.error_learning_engine import ErrorLearningEngine

__all__ = [
    'ErrorEvent',
    'ErrorAnalysisResult',
    'ErrorLearningEngine',
    'CLASS_UTILIZATION_GAP',
    'CLASS_FORM_INSUFFICIENT',
    'CLASS_KNOWLEDGE_GAP',
    'CLASS_UNKNOWN'
]

