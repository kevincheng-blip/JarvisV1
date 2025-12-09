"""J-GOD Doctrine Alert Engine v1

Provides unified Doctrine risk alert scanning for positions, predictions, and conflicts.
"""

from .models import (
    DoctrineAlertSeverity,
    DoctrineAlertSource,
    DoctrineRef,
    DoctrineAlertItem,
    AlertContext,
    RuleConfig,
)
from .config import DoctrineAlertConfig, load_rule_configs
from .engine import DoctrineAlertEngineV1

__all__ = [
    "DoctrineAlertSeverity",
    "DoctrineAlertSource",
    "DoctrineRef",
    "DoctrineAlertItem",
    "AlertContext",
    "RuleConfig",
    "DoctrineAlertConfig",
    "load_rule_configs",
    "DoctrineAlertEngineV1",
]

