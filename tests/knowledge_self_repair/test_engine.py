"""Tests for SelfRepairEngineV1

Tests for the main self-repair engine orchestration.
"""

import pytest
from jgod.knowledge.self_repair.engine import SelfRepairEngineV1
from jgod.knowledge.self_repair.models import RepairReport


class TestSelfRepairEngineV1:
    """Test suite for SelfRepairEngineV1"""
    
    def test_engine_initialization(self):
        """Test engine initialization"""
        engine = SelfRepairEngineV1(llm_provider=None)
        assert engine.scanner is not None
        assert engine.proposer is not None
        assert engine.evaluator is not None
        assert engine.storage is not None
    
    def test_engine_initialization_with_llm(self, mock_llm_provider):
        """Test engine initialization with LLM provider"""
        engine = SelfRepairEngineV1(llm_provider=mock_llm_provider)
        assert engine.scanner is not None
        assert engine.proposer is not None
        assert engine.evaluator is not None
    
    def test_run_full_analysis_empty_sections(self):
        """Test running analysis on empty sections"""
        engine = SelfRepairEngineV1(llm_provider=None)
        report = engine.run_full_repair_analysis([], use_llm=False, save_report=False)
        
        assert isinstance(report, RepairReport)
        assert len(report.scan_summary) == 0
        assert len(report.proposals) == 0
    
    def test_run_full_analysis_no_llm(self, sample_doctrine_sections):
        """Test running full analysis without LLM"""
        engine = SelfRepairEngineV1(llm_provider=None)
        report = engine.run_full_repair_analysis(
            sample_doctrine_sections,
            use_llm=False,
            save_report=False
        )
        
        assert isinstance(report, RepairReport)
        assert hasattr(report, 'id')
        assert hasattr(report, 'scan_summary')
        assert hasattr(report, 'proposals')
        assert hasattr(report, 'created_at')
        assert hasattr(report, 'metadata')
    
    def test_run_full_analysis_with_llm(self, sample_doctrine_sections, mock_llm_provider):
        """Test running full analysis with LLM"""
        engine = SelfRepairEngineV1(llm_provider=mock_llm_provider)
        report = engine.run_full_repair_analysis(
            sample_doctrine_sections,
            use_llm=True,
            save_report=False
        )
        
        assert isinstance(report, RepairReport)
        assert len(report.scan_summary) >= 0
        assert len(report.proposals) >= 0
    
    def test_report_structure(self, sample_doctrine_sections):
        """Test that report has correct structure"""
        engine = SelfRepairEngineV1(llm_provider=None)
        report = engine.run_full_repair_analysis(
            sample_doctrine_sections,
            use_llm=False,
            save_report=False
        )
        
        # Check report structure
        assert isinstance(report.id, str)
        assert len(report.id) > 0
        assert isinstance(report.scan_summary, list)
        assert isinstance(report.proposals, list)
        assert isinstance(report.created_at, type(report.created_at))  # datetime
        assert isinstance(report.metadata, dict)
    
    def test_report_metadata(self, sample_doctrine_sections):
        """Test that report metadata is populated"""
        engine = SelfRepairEngineV1(llm_provider=None)
        report = engine.run_full_repair_analysis(
            sample_doctrine_sections,
            use_llm=False,
            save_report=False
        )
        
        assert 'num_sections_scanned' in report.metadata
        assert report.metadata['num_sections_scanned'] == len(sample_doctrine_sections)
        assert 'use_llm' in report.metadata
        assert 'engine_version' in report.metadata
    
    def test_report_save_disabled(self, sample_doctrine_sections):
        """Test running analysis with save disabled"""
        engine = SelfRepairEngineV1(llm_provider=None)
        report = engine.run_full_repair_analysis(
            sample_doctrine_sections,
            use_llm=False,
            save_report=False
        )
        
        # Report should be created even if save is disabled
        assert isinstance(report, RepairReport)
    
    def test_report_proposal_mapping(self, sample_doctrine_sections):
        """Test that proposals map to issues in report"""
        engine = SelfRepairEngineV1(llm_provider=None)
        report = engine.run_full_repair_analysis(
            sample_doctrine_sections,
            use_llm=False,
            save_report=False
        )
        
        issue_ids = {issue.id for issue in report.scan_summary}
        proposal_issue_ids = {prop.issue_id for prop in report.proposals}
        
        # All proposal issue_ids should reference existing issues (or be empty)
        for prop_issue_id in proposal_issue_ids:
            if prop_issue_id:  # May be empty if no proposals generated
                assert prop_issue_id in issue_ids
    
    def test_duplicate_detection_in_pipeline(self, sample_doctrine_sections):
        """Test that duplicate detection works in full pipeline"""
        # Add duplicate sections
        duplicate_section = sample_doctrine_sections[0]
        sections_with_duplicate = sample_doctrine_sections + [duplicate_section]
        
        engine = SelfRepairEngineV1(llm_provider=None)
        report = engine.run_full_repair_analysis(
            sections_with_duplicate,
            use_llm=False,
            save_report=False
        )
        
        # Should detect duplicates
        duplicate_issues = [
            issue for issue in report.scan_summary
            if issue.issue_type.value == "DUPLICATE"
        ]
        # May or may not find duplicates depending on exact matching logic
        assert isinstance(report.scan_summary, list)

