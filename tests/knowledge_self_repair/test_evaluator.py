"""Tests for ProposalEvaluator

Tests for proposal quality evaluation functionality.
"""

import pytest
from jgod.knowledge.self_repair.evaluator import ProposalEvaluator
from jgod.knowledge.self_repair.models import FixProposal


class TestProposalEvaluator:
    """Test suite for ProposalEvaluator"""
    
    def test_evaluate_empty_proposals(self):
        """Test evaluating empty proposals list"""
        evaluator = ProposalEvaluator(llm_provider=None)
        evaluated = evaluator.evaluate_proposals([])
        assert len(evaluated) == 0
    
    def test_evaluate_proposals_no_llm(self, sample_fix_proposals):
        """Test evaluating proposals without LLM provider"""
        evaluator = ProposalEvaluator(llm_provider=None)
        evaluated = evaluator.evaluate_proposals(sample_fix_proposals)
        
        assert len(evaluated) == len(sample_fix_proposals)
        # Should assign default confidence when LLM is not available
        for prop in evaluated:
            assert hasattr(prop, 'confidence')
            assert 0.0 <= prop.confidence <= 1.0
    
    def test_evaluate_proposals_with_llm(self, sample_fix_proposals, mock_llm_provider):
        """Test evaluating proposals with LLM provider"""
        evaluator = ProposalEvaluator(llm_provider=mock_llm_provider)
        evaluated = evaluator.evaluate_proposals(sample_fix_proposals)
        
        assert len(evaluated) == len(sample_fix_proposals)
        for prop in evaluated:
            assert hasattr(prop, 'confidence')
            assert 0.0 <= prop.confidence <= 1.0
            assert hasattr(prop, 'clarity_score')
            assert hasattr(prop, 'logical_score')
            assert hasattr(prop, 'impact_score')
            assert hasattr(prop, 'doctrine_alignment_score')
    
    def test_evaluation_scores_range(self, sample_fix_proposals, mock_llm_provider):
        """Test that evaluation scores are within valid range [0.0, 1.0]"""
        evaluator = ProposalEvaluator(llm_provider=mock_llm_provider)
        evaluated = evaluator.evaluate_proposals(sample_fix_proposals)
        
        for prop in evaluated:
            assert 0.0 <= prop.clarity_score <= 1.0
            assert 0.0 <= prop.logical_score <= 1.0
            assert 0.0 <= prop.impact_score <= 1.0
            assert 0.0 <= prop.doctrine_alignment_score <= 1.0
            assert 0.0 <= prop.confidence <= 1.0
    
    def test_low_confidence_proposals(self):
        """Test handling of low confidence proposals"""
        evaluator = ProposalEvaluator(llm_provider=None)
        
        # Create a proposal with low confidence
        low_confidence_prop = FixProposal(
            id="low-conf-001",
            issue_id="issue-001",
            proposed_text="Test proposal",
            justification="Test",
            confidence=0.3,
            impact="test",
        )
        
        evaluated = evaluator.evaluate_proposals([low_confidence_prop])
        assert len(evaluated) == 1
        assert evaluated[0].confidence < 0.6  # Should be marked as questionable
    
    def test_high_confidence_proposals(self):
        """Test handling of high confidence proposals"""
        evaluator = ProposalEvaluator(llm_provider=None)
        
        high_confidence_prop = FixProposal(
            id="high-conf-001",
            issue_id="issue-001",
            proposed_text="Test proposal",
            justification="Test",
            confidence=0.9,
            impact="test",
        )
        
        evaluated = evaluator.evaluate_proposals([high_confidence_prop])
        assert len(evaluated) == 1
        assert evaluated[0].confidence >= 0.6
    
    def test_evaluation_preserves_proposal_data(self, sample_fix_proposals, mock_llm_provider):
        """Test that evaluation preserves original proposal data"""
        evaluator = ProposalEvaluator(llm_provider=mock_llm_provider)
        original = sample_fix_proposals[0]
        evaluated = evaluator.evaluate_proposals([original])
        
        if evaluated:
            prop = evaluated[0]
            assert prop.id == original.id
            assert prop.issue_id == original.issue_id
            assert prop.proposed_text == original.proposed_text
            assert prop.justification == original.justification
            assert prop.impact == original.impact

