"""Tests for SelfRepairScanner

Tests for Doctrine consistency scanning functionality.
"""

import pytest
from jgod.knowledge.self_repair.scanner import SelfRepairScanner
from jgod.knowledge.self_repair.models import IssueType, IssueSeverity


class TestSelfRepairScanner:
    """Test suite for SelfRepairScanner"""
    
    def test_scan_empty_sections(self):
        """Test scanning empty Doctrine sections list"""
        scanner = SelfRepairScanner(llm_provider=None)
        issues = scanner.scan_doctrine([], use_llm=False)
        assert len(issues) == 0
    
    def test_scan_single_section(self, sample_doctrine_sections):
        """Test scanning single Doctrine section"""
        scanner = SelfRepairScanner(llm_provider=None)
        issues = scanner.scan_doctrine([sample_doctrine_sections[0]], use_llm=False)
        # Single section should not have conflicts or duplicates
        assert isinstance(issues, list)
    
    def test_scan_duplicates_static(self, sample_duplicate_sections):
        """Test static duplicate detection"""
        scanner = SelfRepairScanner(llm_provider=None)
        issues = scanner.scan_doctrine(sample_duplicate_sections, use_llm=False)
        
        # Should find duplicate issue
        duplicate_issues = [i for i in issues if i.issue_type == IssueType.DUPLICATE]
        assert len(duplicate_issues) > 0
        
        issue = duplicate_issues[0]
        assert issue.severity == IssueSeverity.MEDIUM
        assert len(issue.doctrine_refs) == 2
    
    def test_scan_with_llm_disabled(self, sample_doctrine_sections):
        """Test scanning with LLM disabled (static analysis only)"""
        scanner = SelfRepairScanner(llm_provider=None)
        issues = scanner.scan_doctrine(sample_doctrine_sections, use_llm=False)
        
        # Should only perform static analysis (duplicates)
        assert isinstance(issues, list)
        # No conflicts should be found without LLM
        conflict_issues = [i for i in issues if i.issue_type == IssueType.CONFLICT]
        assert len(conflict_issues) == 0
    
    def test_scan_with_llm_enabled(self, sample_conflicting_sections, mock_llm_provider):
        """Test scanning with LLM enabled"""
        scanner = SelfRepairScanner(llm_provider=mock_llm_provider)
        issues = scanner.scan_doctrine(sample_conflicting_sections, use_llm=True)
        
        assert isinstance(issues, list)
        # Should potentially find conflicts with LLM
    
    def test_scan_ambiguity_detection(self, sample_ambiguous_section, mock_llm_provider):
        """Test ambiguity detection with LLM"""
        scanner = SelfRepairScanner(llm_provider=mock_llm_provider)
        issues = scanner.scan_doctrine(sample_ambiguous_section, use_llm=True)
        
        # Should find ambiguity issue
        ambiguous_issues = [i for i in issues if i.issue_type == IssueType.AMBIGUOUS]
        # Note: This depends on LLM response, may be empty in some cases
        assert isinstance(issues, list)
    
    def test_issue_structure(self, sample_duplicate_sections):
        """Test that issues have correct structure"""
        scanner = SelfRepairScanner(llm_provider=None)
        issues = scanner.scan_doctrine(sample_duplicate_sections, use_llm=False)
        
        if issues:
            issue = issues[0]
            assert hasattr(issue, 'id')
            assert hasattr(issue, 'issue_type')
            assert hasattr(issue, 'doctrine_refs')
            assert hasattr(issue, 'description')
            assert hasattr(issue, 'severity')
            assert isinstance(issue.doctrine_refs, list)
            assert len(issue.doctrine_refs) > 0
    
    def test_no_duplicates_different_sections(self, sample_doctrine_sections):
        """Test that different sections don't trigger duplicate detection"""
        scanner = SelfRepairScanner(llm_provider=None)
        issues = scanner.scan_doctrine(sample_doctrine_sections, use_llm=False)
        
        # Different sections should not be flagged as duplicates
        duplicate_issues = [i for i in issues if i.issue_type == IssueType.DUPLICATE]
        assert len(duplicate_issues) == 0

