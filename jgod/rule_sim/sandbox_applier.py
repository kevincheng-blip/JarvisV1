"""Rule Sandbox Applier

Applies rule changes in sandbox directory without modifying production files.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

from jgod.rule_sim.models import RuleSimExperimentConfig, RuleSimTargetType
from jgod.rule_sim.config import RULE_SIM_SANDBOX_ROOT
from jgod.doctrine_v2.service import DoctrineServiceV2

logger = logging.getLogger(__name__)


class RuleSandboxApplier:
    """Applies rule changes in sandbox environment"""
    
    def __init__(self, doctrine_service_v2: Optional[DoctrineServiceV2] = None):
        """
        Initialize sandbox applier
        
        Args:
            doctrine_service_v2: Doctrine Service V2 instance (optional)
        """
        self.doctrine_service_v2 = doctrine_service_v2 or DoctrineServiceV2()
        logger.info("RuleSandboxApplier initialized")
    
    def create_sandbox(self, experiment_config: RuleSimExperimentConfig) -> Path:
        """
        Create sandbox directory and apply rule changes.
        
        Creates directory structure:
        {RULE_SIM_SANDBOX_ROOT}/{experiment_id}/
          - doctrine/  (if Doctrine rules are modified)
          - alerts/    (if Alert rules are modified)
        
        Args:
            experiment_config: Experiment configuration
        
        Returns:
            Path to sandbox directory
        """
        experiment_id = experiment_config.experiment_id
        sandbox_dir = RULE_SIM_SANDBOX_ROOT / experiment_id
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Creating sandbox for experiment {experiment_id} at {sandbox_dir}")
        
        target_ruleset = experiment_config.target_ruleset
        if not target_ruleset:
            logger.warning("No target ruleset specified, sandbox will be empty")
            return sandbox_dir
        
        # Apply rules based on type
        if target_ruleset.type == RuleSimTargetType.DOCTRINE_SECTION:
            self._apply_doctrine_section(
                sandbox_dir,
                target_ruleset,
                experiment_config.baseline_version_id,
                experiment_config.variant_version_id,
            )
        elif target_ruleset.type == RuleSimTargetType.ALERT_RULES_YAML:
            self._apply_alert_rules(
                sandbox_dir,
                target_ruleset,
                experiment_config.baseline_version_id,
                experiment_config.variant_version_id,
            )
        else:
            logger.warning(f"Unsupported ruleset type: {target_ruleset.type}")
        
        return sandbox_dir
    
    def _apply_doctrine_section(
        self,
        sandbox_dir: Path,
        ruleset: "RuleSetRef",
        baseline_version_id: Optional[str],
        variant_version_id: Optional[str],
    ) -> None:
        """
        Apply Doctrine section changes to sandbox.
        
        For v1, we copy the variant version content to sandbox.
        Future versions can implement more sophisticated merging.
        
        Args:
            sandbox_dir: Sandbox directory
            ruleset: Ruleset reference
            baseline_version_id: Baseline version ID
            variant_version_id: Variant version ID
        """
        doctrine_dir = sandbox_dir / "doctrine"
        doctrine_dir.mkdir(parents=True, exist_ok=True)
        
        if not variant_version_id:
            logger.warning("No variant_version_id provided for Doctrine section")
            return
        
        # Extract section_id from ruleset.id (e.g., "B01#S12-R03" -> "B01_S12_R03")
        section_id = ruleset.id.replace("#", "_").replace("-", "_")
        
        # Get variant version content from DoctrineServiceV2
        try:
            variant_content = self.doctrine_service_v2.get_version_content(
                section_id=section_id,
                version_id=variant_version_id,
            )
            
            if variant_content:
                # Write to sandbox
                sandbox_file = doctrine_dir / f"{section_id}_variant.md"
                sandbox_file.write_text(variant_content, encoding="utf-8")
                logger.info(f"Applied Doctrine variant to {sandbox_file}")
            else:
                logger.warning(f"Variant content not found for {section_id}/{variant_version_id}")
        except Exception as e:
            logger.error(f"Failed to apply Doctrine section: {e}", exc_info=True)
    
    def _apply_alert_rules(
        self,
        sandbox_dir: Path,
        ruleset: "RuleSetRef",
        baseline_version_id: Optional[str],
        variant_version_id: Optional[str],
    ) -> None:
        """
        Apply Alert rules YAML changes to sandbox.
        
        Args:
            sandbox_dir: Sandbox directory
            ruleset: Ruleset reference
            baseline_version_id: Baseline version ID
            variant_version_id: Variant version ID
        """
        alerts_dir = sandbox_dir / "alerts"
        alerts_dir.mkdir(parents=True, exist_ok=True)
        
        if not ruleset.alert_config_path:
            logger.warning("No alert_config_path specified")
            return
        
        original_path = Path(ruleset.alert_config_path)
        if not original_path.exists():
            logger.warning(f"Original alert config not found: {original_path}")
            return
        
        # For v1, copy original file to sandbox
        # Future versions can apply variant changes
        sandbox_file = alerts_dir / original_path.name
        shutil.copy(original_path, sandbox_file)
        logger.info(f"Copied alert config to {sandbox_file}")
        
        # TODO: Apply variant_version_id changes if provided

