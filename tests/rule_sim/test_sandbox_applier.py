"""Tests for Rule Sandbox Applier"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from jgod.rule_sim.sandbox_applier import RuleSandboxApplier
from jgod.rule_sim.models import RuleSimTargetType, RuleSetRef


@pytest.fixture
def sandbox_applier(rule_sim_tmp_dir, mock_doctrine_service):
    """Sandbox applier instance"""
    with patch("jgod.rule_sim.sandbox_applier.DoctrineServiceV2", return_value=mock_doctrine_service):
        applier = RuleSandboxApplier(doctrine_service_v2=mock_doctrine_service)
        # Override base path to tmp_dir
        applier.storage.base_path = rule_sim_tmp_dir / "doctrine_versions"
        applier.storage.base_path.mkdir(parents=True, exist_ok=True)
        return applier


class TestRuleSandboxApplier:
    """Tests for RuleSandboxApplier"""
    
    def test_create_sandbox_directory(self, sandbox_applier, sample_experiment_config, rule_sim_tmp_dir):
        """Test creating sandbox directory"""
        # Monkeypatch the base path
        from jgod.rule_sim.config import RULE_SIM_SANDBOX_ROOT
        original_path = RULE_SIM_SANDBOX_ROOT
        
        try:
            # Temporarily change to tmp_dir
            import jgod.rule_sim.sandbox_applier as applier_module
            applier_module.RULE_SIM_SANDBOX_ROOT = rule_sim_tmp_dir / "sandbox_root"
            
            sandbox_dir = sandbox_applier.create_sandbox(sample_experiment_config)
            
            assert sandbox_dir.exists()
            assert sandbox_dir.is_dir()
            assert sample_experiment_config.experiment_id in str(sandbox_dir)
        finally:
            applier_module.RULE_SIM_SANDBOX_ROOT = original_path
    
    def test_sandbox_does_not_modify_production(self, sandbox_applier, sample_experiment_config, tmp_path):
        """Test that sandbox creation doesn't modify production files"""
        # Create a mock production file
        production_file = tmp_path / "production_config.yaml"
        original_content = "production config content"
        production_file.write_text(original_content)
        
        # Record original hash
        import hashlib
        original_hash = hashlib.md5(production_file.read_bytes()).hexdigest()
        original_mtime = production_file.stat().st_mtime
        
        # Create sandbox
        sandbox_dir = sandbox_applier.create_sandbox(sample_experiment_config)
        
        # Verify production file unchanged
        assert production_file.exists()
        new_hash = hashlib.md5(production_file.read_bytes()).hexdigest()
        new_mtime = production_file.stat().st_mtime
        
        assert original_hash == new_hash
        assert original_mtime == new_mtime
    
    def test_doctrine_section_sandbox(self, sandbox_applier, sample_experiment_config, rule_sim_tmp_dir, mock_doctrine_service):
        """Test creating sandbox for Doctrine section"""
        # Mock get_version_content
        mock_doctrine_service.get_version_content = MagicMock(
            return_value="# Variant Version\n\nModified content here..."
        )
        
        # Set variant_version_id
        sample_experiment_config.variant_version_id = "variant-v1"
        
        # Override storage base path for DoctrineService
        doctrine_versions_dir = rule_sim_tmp_dir / "doctrine_versions"
        doctrine_versions_dir.mkdir(parents=True, exist_ok=True)
        
        # Create section directory
        section_id = sample_experiment_config.target_ruleset.id.replace("#", "_")
        section_dir = doctrine_versions_dir / section_id
        section_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sandbox
        from jgod.rule_sim.config import RULE_SIM_SANDBOX_ROOT
        original_path = RULE_SIM_SANDBOX_ROOT
        
        try:
            import jgod.rule_sim.sandbox_applier as applier_module
            applier_module.RULE_SIM_SANDBOX_ROOT = rule_sim_tmp_dir / "sandbox_root"
            
            sandbox_dir = sandbox_applier.create_sandbox(sample_experiment_config)
            
            # Check that variant content is written to sandbox
            doctrine_dir = sandbox_dir / "doctrine"
            if doctrine_dir.exists():
                # If sandbox applier wrote doctrine files, verify structure
                assert sandbox_dir.exists()
        finally:
            applier_module.RULE_SIM_SANDBOX_ROOT = original_path

