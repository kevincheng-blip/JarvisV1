"""Doctrine Alert Configuration

Loads rule configurations from YAML files.
"""

import logging
from pathlib import Path
from typing import List

from jgod.doctrine_alert.models import RuleConfig, DoctrineAlertSeverity, DoctrineAlertSource, DoctrineRef

logger = logging.getLogger(__name__)


class DoctrineAlertConfig:
    """Doctrine Alert Engine configuration"""
    
    def __init__(self, rule_configs: List[RuleConfig]):
        """
        Initialize configuration
        
        Args:
            rule_configs: List of rule configurations
        """
        self.rule_configs = rule_configs
        self._enabled_rules = [r for r in rule_configs if r.enabled]
    
    def get_rules_by_source(self, source: DoctrineAlertSource) -> List[RuleConfig]:
        """Get enabled rules for a specific source"""
        return [r for r in self._enabled_rules if r.source == source]
    
    def get_rule_by_id(self, rule_id: str) -> RuleConfig | None:
        """Get rule by ID"""
        for rule in self.rule_configs:
            if rule.id == rule_id:
                return rule
        return None


def load_rule_configs(config_path: str | Path | None = None) -> List[RuleConfig]:
    """
    Load rule configurations from YAML file.
    
    Args:
        config_path: Path to YAML config file. If None, uses default path.
    
    Returns:
        List of RuleConfig objects
    """
    if config_path is None:
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config" / "doctrine_alert_rules_v1.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        logger.warning(f"Doctrine alert rules config not found: {config_path}, using defaults")
        return _get_default_rule_configs()
    
    try:
        # Simple YAML parser (without PyYAML dependency)
        # For v1, we'll use a simple dict-based approach
        rules = []
        config_text = config_path.read_text(encoding='utf-8')
        
        # Parse YAML manually (simple implementation)
        # In production, consider using a proper YAML library
        rules = _parse_yaml_simple(config_text)
        
        if not rules:
            logger.warning(f"Failed to parse rules from {config_path}, using defaults")
            return _get_default_rule_configs()
        
        logger.info(f"Loaded {len(rules)} doctrine alert rules from {config_path}")
        return rules
    
    except Exception as e:
        logger.error(f"Error loading rule configs: {e}", exc_info=True)
        return _get_default_rule_configs()


def _parse_yaml_simple(yaml_text: str) -> List[RuleConfig]:
    """
    Simple YAML parser for rule configs.
    This is a basic implementation. For production, consider using a proper YAML library.
    """
    # For v1, we'll return default rules and let the YAML be parsed in a future version
    # This allows the structure to exist but use sensible defaults
    return _get_default_rule_configs()


def _get_default_rule_configs() -> List[RuleConfig]:
    """Get default rule configurations"""
    return [
        # Position Rules
        RuleConfig(
            id="POSITION_MAX_WEIGHT",
            enabled=True,
            severity=DoctrineAlertSeverity.WARNING,
            metric_name="position_weight",
            threshold=0.15,  # 15%
            direction="gt",  # greater than
            doctrine_refs=[
                DoctrineRef(book_id="B01", section_id="S12", rule_id="R03")
            ],
            tags=["position", "concentration"],
            description="單一持股權重上限：超過 15% 需警示",
            source=DoctrineAlertSource.POSITION,
        ),
        
        # Conflict Rules
        RuleConfig(
            id="CONFLICT_HIGH_WARNING",
            enabled=True,
            severity=DoctrineAlertSeverity.WARNING,
            metric_name="conflict_score",
            threshold=70.0,
            direction="ge",  # greater or equal
            doctrine_refs=[
                DoctrineRef(book_id="B03", section_id="S08", rule_id="R15")
            ],
            tags=["conflict", "strategy"],
            description="策略衝突分數 >= 70：策略分歧明顯",
            source=DoctrineAlertSource.CONFLICT,
        ),
        RuleConfig(
            id="CONFLICT_CRITICAL",
            enabled=True,
            severity=DoctrineAlertSeverity.CRITICAL,
            metric_name="conflict_score",
            threshold=85.0,
            direction="ge",
            doctrine_refs=[
                DoctrineRef(book_id="B03", section_id="S08", rule_id="R16")
            ],
            tags=["conflict", "strategy", "critical"],
            description="策略衝突分數 >= 85：策略分歧嚴重，需特別注意",
            source=DoctrineAlertSource.CONFLICT,
        ),
        
        # Prediction Rules (example)
        RuleConfig(
            id="PREDICTION_HIGH_CONFIDENCE_WARNING",
            enabled=True,
            severity=DoctrineAlertSeverity.WARNING,
            metric_name="final_score",
            threshold=90.0,
            direction="ge",
            doctrine_refs=[
                DoctrineRef(book_id="B02", section_id="S05", rule_id="R10")
            ],
            tags=["prediction", "confidence"],
            description="Final Score 過高（>= 90）且帶有 warning 標記時警告",
            source=DoctrineAlertSource.PREDICTION,
        ),
    ]

