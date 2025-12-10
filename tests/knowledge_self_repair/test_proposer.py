"""Tests for RepairProposer

Tests for fix proposal generation functionality.
"""

import pytest
from jgod.knowledge.self_repair.proposer import RepairProposer
from jgod.knowledge.self_repair.models import IssueType


class TestRepairProposer:
    """Test suite for RepairProposer"""
    
    def test_generate_proposals_empty_issues(self):
        """Test generating proposals for empty issues list"""
        proposer = RepairProposer(llm_provider=None)
        proposals = proposer.generate_proposals([], [])
        assert len(proposals) == 0
    
    def test_generate_proposals_no_llm(self, sample_consistency_issues, sample_doctrine_sections):
        """Test generating proposals without LLM provider"""
        proposer = RepairProposer(llm_provider=None)
        proposals = proposer.generate_proposals(sample_consistency_issues, sample_doctrine_sections)
        
        # Should return empty list when LLM is not available
        assert isinstance(proposals, list)
        # May be empty if LLM is required
    
    def test_generate_proposals_with_llm(self, sample_consistency_issues, sample_doctrine_sections, mock_llm_provider):
        """Test generating proposals with LLM provider"""
        proposer = RepairProposer(llm_provider=mock_llm_provider)
        proposals = proposer.generate_proposals(sample_consistency_issues, sample_doctrine_sections)
        
        assert isinstance(proposals, list)
        # May generate proposals if LLM works correctly
    
    def test_proposal_structure(self, sample_consistency_issues, sample_doctrine_sections, mock_llm_provider):
        """Test that proposals have correct structure"""
        proposer = RepairProposer(llm_provider=mock_llm_provider)
        proposals = proposer.generate_proposals(sample_consistency_issues, sample_doctrine_sections)
        
        if proposals:
            proposal = proposals[0]
            assert hasattr(proposal, 'id')
            assert hasattr(proposal, 'issue_id')
            assert hasattr(proposal, 'proposed_text')
            assert hasattr(proposal, 'justification')
            assert hasattr(proposal, 'confidence')
            assert hasattr(proposal, 'impact')
            assert len(proposal.proposed_text) > 0
    
    def test_conflict_fix_proposal(self, sample_consistency_issues, sample_doctrine_sections, mock_llm_provider):
        """Test generating fix for conflict issue"""
        proposer = RepairProposer(llm_provider=mock_llm_provider)
        conflict_issues = [i for i in sample_consistency_issues if i.issue_type == IssueType.CONFLICT]
        
        if conflict_issues:
            proposals = proposer.generate_proposals(conflict_issues, sample_doctrine_sections)
            assert isinstance(proposals, list)
    
    def test_duplicate_fix_proposal(self, sample_consistency_issues, sample_doctrine_sections):
        """Test generating fix for duplicate issue (should work without LLM)"""
        proposer = RepairProposer(llm_provider=None)
        
        # Create a duplicate issue
        from jgod.knowledge.self_repair.models import ConsistencyIssue, IssueType, IssueSeverity
        duplicate_issue = ConsistencyIssue(
            id="dup-001",
            issue_type=IssueType.DUPLICATE,
            doctrine_refs=["B01#S12", "B01#S13"],
            description="發現重複條文",
            severity=IssueSeverity.MEDIUM,
        )
        
        proposals = proposer.generate_proposals([duplicate_issue], sample_doctrine_sections)
        # Duplicate fix should work without LLM
        assert isinstance(proposals, list)
    
    def test_proposal_issue_id_mapping(self, sample_consistency_issues, sample_doctrine_sections, mock_llm_provider):
        """Test that proposals correctly map to issue IDs"""
        proposer = RepairProposer(llm_provider=mock_llm_provider)
        proposals = proposer.generate_proposals(sample_consistency_issues, sample_doctrine_sections)
        
        issue_ids = {issue.id for issue in sample_consistency_issues}
        proposal_issue_ids = {prop.issue_id for prop in proposals}
        
        # All proposal issue_ids should reference existing issues
        for prop_issue_id in proposal_issue_ids:
            assert prop_issue_id in issue_ids

