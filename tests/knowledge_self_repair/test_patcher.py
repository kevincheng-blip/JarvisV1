"""Tests for SafePatcher

Tests for safe knowledge base patching functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from jgod.knowledge.self_repair.patcher import SafePatcher
from jgod.knowledge.self_repair.models import FixProposal


class TestSafePatcher:
    """Test suite for SafePatcher"""
    
    @pytest.fixture
    def temp_knowledge_file(self):
        """Create temporary knowledge base file for testing"""
        temp_dir = tempfile.mkdtemp()
        temp_file = Path(temp_dir) / "test_knowledge.jsonl"
        
        # Create sample knowledge base
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write('{"id": "test-001", "type": "RULE", "title": "Test Rule"}\n')
            f.write('{"id": "test-002", "type": "RULE", "title": "Test Rule 2"}\n')
        
        yield temp_file
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_proposal(self):
        """Sample fix proposal for testing"""
        return FixProposal(
            id="proposal-001",
            issue_id="issue-001",
            proposed_text="Updated rule text",
            justification="Test justification",
            confidence=0.8,
            impact="rule-clarity",
        )
    
    def test_patcher_initialization(self):
        """Test patcher initialization"""
        patcher = SafePatcher()
        assert patcher.knowledge_path is not None
    
    def test_patcher_custom_path(self):
        """Test patcher with custom knowledge path"""
        custom_path = Path("custom/knowledge.jsonl")
        patcher = SafePatcher(knowledge_path=custom_path)
        assert patcher.knowledge_path == custom_path
    
    def test_apply_proposal_file_not_exists(self, sample_proposal):
        """Test applying proposal when file doesn't exist"""
        patcher = SafePatcher(knowledge_path=Path("nonexistent.jsonl"))
        result = patcher.apply_proposal(sample_proposal)
        assert result is False
    
    def test_apply_proposal_with_backup(self, temp_knowledge_file, sample_proposal):
        """Test applying proposal with backup creation"""
        patcher = SafePatcher(knowledge_path=temp_knowledge_file)
        
        # Count original lines
        with open(temp_knowledge_file, 'r') as f:
            original_lines = len(f.readlines())
        
        result = patcher.apply_proposal(sample_proposal, create_backup=True)
        
        # Should succeed
        assert result is True
        
        # Check backup was created
        backup_files = list(temp_knowledge_file.parent.glob(f"{temp_knowledge_file.stem}.bak.*"))
        assert len(backup_files) > 0
        
        # Check knowledge file was modified (should have new entry)
        with open(temp_knowledge_file, 'r') as f:
            new_lines = len(f.readlines())
        assert new_lines >= original_lines
    
    def test_apply_proposal_no_backup(self, temp_knowledge_file, sample_proposal):
        """Test applying proposal without backup"""
        patcher = SafePatcher(knowledge_path=temp_knowledge_file)
        
        # Count original lines
        with open(temp_knowledge_file, 'r') as f:
            original_lines = len(f.readlines())
        
        result = patcher.apply_proposal(sample_proposal, create_backup=False)
        
        # Should succeed
        assert result is True
        
        # Check no backup was created
        backup_files = list(temp_knowledge_file.parent.glob(f"{temp_knowledge_file.stem}.bak.*"))
        assert len(backup_files) == 0
    
    def test_create_backup(self, temp_knowledge_file):
        """Test backup creation"""
        patcher = SafePatcher(knowledge_path=temp_knowledge_file)
        backup_path = patcher.create_backup()
        
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path != temp_knowledge_file
        
        # Verify backup content matches original
        with open(temp_knowledge_file, 'r') as f:
            original_content = f.read()
        with open(backup_path, 'r') as f:
            backup_content = f.read()
        assert original_content == backup_content
    
    def test_create_backup_file_not_exists(self):
        """Test backup creation when file doesn't exist"""
        patcher = SafePatcher(knowledge_path=Path("nonexistent.jsonl"))
        backup_path = patcher.create_backup()
        assert backup_path is None
    
    def test_apply_proposal_preserves_existing_entries(self, temp_knowledge_file, sample_proposal):
        """Test that applying proposal preserves existing entries"""
        patcher = SafePatcher(knowledge_path=temp_knowledge_file)
        
        # Read original content
        with open(temp_knowledge_file, 'r') as f:
            original_content = f.read()
        
        result = patcher.apply_proposal(sample_proposal)
        assert result is True
        
        # Verify original content is still present
        with open(temp_knowledge_file, 'r') as f:
            new_content = f.read()
        assert "test-001" in new_content
        assert "test-002" in new_content

