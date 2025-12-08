"""Unit tests for ErrorLearningEngine Doctrine integration

Tests the integration between ErrorLearningEngine and Doctrine knowledge base.
"""

import unittest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from jgod.learning.error_learning_engine import ErrorLearningEngine
from jgod.learning.error_event import ErrorEvent, DoctrineHit, ErrorAnalysisResult
from jgod.knowledge.knowledge_brain import KnowledgeBrain, KnowledgeItem


class TestDoctrineIntegration(unittest.TestCase):
    """Test Doctrine integration with ErrorLearningEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = ErrorLearningEngine(
            enable_doctrine_suggestions=True,
            max_doctrine_hits=5
        )
        
        # Create mock KnowledgeBrain
        self.mock_brain = Mock(spec=KnowledgeBrain)
        
        # Mock Doctrine search results
        mock_item1 = Mock(spec=KnowledgeItem)
        mock_item1.id = "doctrine_book_07_book-07-section-045_entry_0001"
        mock_item1.title = "單筆最大虧損 2% 規則"
        mock_item1.description = "單筆交易最大虧損不得超過總資金的 2%"
        mock_item1.source_doc = "doctrine_review_v1:book_07"
        mock_item1.source_location = "book_07_section_045"
        mock_item1.tags = ["DOCTRINE", "CONCEPT", "RULE", "RISK_RULE", "FORMULA"]
        mock_item1.structured = {
            "book_id": "book_07",
            "section_id": "book_07_section_045",
            "section_title": "單筆最大虧損 2% 規則",
            "ai_summary": "單筆交易最大虧損不得超過總資金的 2%",
            "ai_core_principles": ["風險控制是交易的第一要務"],
            "ai_risk_rules": ["每筆交易必須設定停損點", "虧損超過 2% 立即平倉"],
            "rules": ["風險控制是交易的第一要務"]
        }
        
        mock_item2 = Mock(spec=KnowledgeItem)
        mock_item2.id = "doctrine_book_01_book-01-section-123_entry_0002"
        mock_item2.title = "風控原則"
        mock_item2.description = "嚴格執行風險控制"
        mock_item2.source_doc = "doctrine_review_v1:book_01"
        mock_item2.source_location = "book_01_section_123"
        mock_item2.tags = ["DOCTRINE", "RULE", "RISK"]
        mock_item2.structured = {
            "book_id": "book_01",
            "section_id": "book_01_section_123",
            "ai_summary": "嚴格執行風險控制",
            "ai_core_principles": ["嚴格執行停損"],
            "ai_risk_rules": []
        }
        
        # Mock search_doctrine to return mock items
        self.mock_brain.search_doctrine = Mock(return_value=[mock_item1, mock_item2])
        
        # Replace engine's knowledge_brain with mock
        self.engine._knowledge_brain = self.mock_brain
    
    def test_doctrine_suggestions_enabled(self):
        """Test that Doctrine suggestions are included when enabled"""
        event = ErrorEvent(
            id="test_001",
            timestamp=datetime.now(),
            symbol="2330",
            timeframe="1d",
            error_type="STOP_LOSS_TOO_LATE",
            predicted_outcome="up",
            actual_outcome="down",
            notes="停損設定過晚"
        )
        
        analysis = self.engine.analyze_error(event)
        
        # Check that Doctrine suggestions are present
        self.assertIsNotNone(analysis.doctrine_suggestions)
        self.assertGreater(len(analysis.doctrine_suggestions), 0)
        
        # Check first suggestion structure
        hit = analysis.doctrine_suggestions[0]
        self.assertIsInstance(hit, DoctrineHit)
        self.assertEqual(hit.book_id, "book_07")
        self.assertIsNotNone(hit.title)
        self.assertIsNotNone(hit.summary)
        self.assertGreater(len(hit.core_principles), 0)
        
        # Verify search_doctrine was called
        self.mock_brain.search_doctrine.assert_called_once()
    
    def test_doctrine_suggestions_disabled(self):
        """Test that Doctrine suggestions are empty when disabled"""
        engine_disabled = ErrorLearningEngine(
            enable_doctrine_suggestions=False
        )
        engine_disabled._knowledge_brain = self.mock_brain
        
        event = ErrorEvent(
            id="test_002",
            timestamp=datetime.now(),
            symbol="2330",
            timeframe="1d",
            error_type="direction",
            predicted_outcome="up",
            actual_outcome="down"
        )
        
        analysis = engine_disabled.analyze_error(event)
        
        # Check that Doctrine suggestions are empty
        self.assertEqual(len(analysis.doctrine_suggestions), 0)
        
        # Verify search_doctrine was NOT called
        self.mock_brain.search_doctrine.assert_not_called()
    
    def test_doctrine_hit_structure(self):
        """Test DoctrineHit structure and field mapping"""
        event = ErrorEvent(
            id="test_003",
            timestamp=datetime.now(),
            symbol="2330",
            timeframe="1d",
            error_type="STOP_LOSS_TOO_LATE",
            predicted_outcome="up",
            actual_outcome="down",
            notes="停損問題"
        )
        
        analysis = self.engine.analyze_error(event)
        
        self.assertGreater(len(analysis.doctrine_suggestions), 0)
        hit = analysis.doctrine_suggestions[0]
        
        # Verify all fields are populated correctly
        self.assertIsNotNone(hit.book_id)
        self.assertIsNotNone(hit.section_id)
        self.assertIsNotNone(hit.title)
        self.assertIsNotNone(hit.summary)
        self.assertIsInstance(hit.core_principles, list)
        self.assertIsInstance(hit.risk_rules, list)
        self.assertIsInstance(hit.tags, list)
    
    def test_doctrine_serialization(self):
        """Test that Doctrine suggestions are properly serialized/deserialized"""
        event = ErrorEvent(
            id="test_004",
            timestamp=datetime.now(),
            symbol="2330",
            timeframe="1d",
            error_type="timing",
            predicted_outcome="up",
            actual_outcome="down"
        )
        
        analysis = self.engine.analyze_error(event)
        
        # Serialize
        result_dict = analysis.to_dict()
        
        # Check doctrine_suggestions in dict
        self.assertIn("doctrine_suggestions", result_dict)
        self.assertGreater(len(result_dict["doctrine_suggestions"]), 0)
        
        # Deserialize
        analysis2 = ErrorAnalysisResult.from_dict(result_dict)
        
        # Verify doctrine_suggestions are restored
        self.assertEqual(len(analysis2.doctrine_suggestions), len(analysis.doctrine_suggestions))
        self.assertEqual(
            analysis2.doctrine_suggestions[0].book_id,
            analysis.doctrine_suggestions[0].book_id
        )
    
    def test_doctrine_error_handling(self):
        """Test that Doctrine query errors don't crash the engine"""
        # Make search_doctrine raise an exception
        self.mock_brain.search_doctrine = Mock(side_effect=Exception("Test error"))
        
        event = ErrorEvent(
            id="test_005",
            timestamp=datetime.now(),
            symbol="2330",
            timeframe="1d",
            error_type="unknown",
            predicted_outcome="up",
            actual_outcome="down"
        )
        
        # Should not raise exception
        analysis = self.engine.analyze_error(event)
        
        # Doctrine suggestions should be empty list on error
        self.assertEqual(len(analysis.doctrine_suggestions), 0)
    
    def test_max_doctrine_hits_limit(self):
        """Test that max_doctrine_hits limit is respected"""
        # Create more mock items
        mock_items = []
        for i in range(10):
            mock_item = Mock(spec=KnowledgeItem)
            mock_item.id = f"doctrine_item_{i}"
            mock_item.title = f"Test Item {i}"
            mock_item.description = f"Description {i}"
            mock_item.source_doc = "doctrine_review_v1:book_01"
            mock_item.source_location = f"book_01_section_{i:03d}"
            mock_item.tags = ["DOCTRINE"]
            mock_item.structured = {
                "book_id": "book_01",
                "section_id": f"book_01_section_{i:03d}",
                "ai_summary": f"Summary {i}",
                "ai_core_principles": [],
                "ai_risk_rules": []
            }
            mock_items.append(mock_item)
        
        self.mock_brain.search_doctrine = Mock(return_value=mock_items)
        
        engine_limited = ErrorLearningEngine(
            enable_doctrine_suggestions=True,
            max_doctrine_hits=3
        )
        engine_limited._knowledge_brain = self.mock_brain
        
        event = ErrorEvent(
            id="test_006",
            timestamp=datetime.now(),
            symbol="2330",
            timeframe="1d",
            error_type="test",
            predicted_outcome="up",
            actual_outcome="down"
        )
        
        analysis = engine_limited.analyze_error(event)
        
        # Should respect max_doctrine_hits limit
        self.assertLessEqual(len(analysis.doctrine_suggestions), 3)


if __name__ == "__main__":
    unittest.main()

