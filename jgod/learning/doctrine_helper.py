"""
Doctrine Helper for Error Learning Engine

This module provides helper functions to query Doctrine knowledge base
and convert results to DoctrineHit format for error analysis.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from jgod.knowledge.knowledge_brain import KnowledgeBrain, KnowledgeItem
from jgod.learning.error_event import DoctrineHit

logger = logging.getLogger(__name__)


def get_doctrine_suggestions(
    brain: KnowledgeBrain,
    error_type: str | None,
    symbol: str | None,
    human_summary: str | None,
    max_hits: int = 5,
) -> List[DoctrineHit]:
    """
    Query Doctrine knowledge base and return relevant suggestions.
    
    This function builds a query from error context and searches the Doctrine
    knowledge base for relevant rules, principles, and risk guidelines.
    
    Args:
        brain: KnowledgeBrain instance (must have Doctrine knowledge loaded)
        error_type: Type of error (e.g., "STOP_LOSS_TOO_LATE", "direction")
        symbol: Stock symbol (e.g., "2330")
        human_summary: Human-written summary or description of the error
        max_hits: Maximum number of Doctrine suggestions to return
    
    Returns:
        List of DoctrineHit objects (empty list if no matches found)
    
    Example:
        from jgod.knowledge.knowledge_brain import KnowledgeBrain
        from jgod.learning.doctrine_helper import get_doctrine_suggestions
        
        brain = KnowledgeBrain()
        brain.load()
        
        hits = get_doctrine_suggestions(
            brain=brain,
            error_type="STOP_LOSS_TOO_LATE",
            symbol="2330",
            human_summary="停損設定過晚導致虧損擴大",
            max_hits=5
        )
    """
    if brain is None:
        logger.warning("KnowledgeBrain is None, cannot query Doctrine suggestions")
        return []
    
    # Build query string
    query_parts = []
    
    if error_type:
        query_parts.append(f"錯誤類型: {error_type}")
    
    if symbol:
        query_parts.append(f"股票: {symbol}")
    
    if human_summary:
        # Use human summary as main query content
        query_parts.append(human_summary)
    
    query = "; ".join(query_parts) if query_parts else "錯誤 風控"
    
    try:
        # Search Doctrine knowledge base
        doctrine_items = brain.search_doctrine(query, top_k=max_hits)
        
        if not doctrine_items:
            logger.debug(f"No Doctrine suggestions found for query: {query}")
            return []
        
        # Convert KnowledgeItem to DoctrineHit
        hits = []
        for item in doctrine_items:
            try:
                hit = _convert_to_doctrine_hit(item)
                if hit:
                    hits.append(hit)
            except Exception as e:
                logger.warning(f"Failed to convert Doctrine item {item.id} to DoctrineHit: {e}")
                continue
        
        logger.info(f"Found {len(hits)} Doctrine suggestions for query: {query}")
        return hits
        
    except Exception as e:
        logger.error(f"Error querying Doctrine suggestions: {e}", exc_info=True)
        return []


def _convert_to_doctrine_hit(item: KnowledgeItem) -> Optional[DoctrineHit]:
    """
    Convert KnowledgeItem from Doctrine knowledge base to DoctrineHit.
    
    Args:
        item: KnowledgeItem from Doctrine knowledge base
    
    Returns:
        DoctrineHit object, or None if conversion fails
    """
    if not item:
        return None
    
    # Extract book_id and section_id from item metadata
    book_id = "unknown"
    section_id = item.id  # Use item ID as fallback
    
    # Try to extract from source_location or structured data
    if item.source_location:
        # Format might be like "book_01_section_123" or "book_01_section_001"
        parts = item.source_location.split("_")
        if len(parts) >= 2 and parts[0] == "book":
            book_id = f"{parts[0]}_{parts[1]}"
    
    # Also check structured data
    if item.structured and isinstance(item.structured, dict):
        if "book_id" in item.structured:
            book_id = item.structured["book_id"]
        if "section_id" in item.structured:
            section_id = item.structured["section_id"]
    
    # Extract from source_doc if available
    if item.source_doc and ":" in item.source_doc:
        # Format might be "doctrine_review_v1:book_07"
        parts = item.source_doc.split(":")
        if len(parts) >= 2:
            potential_book_id = parts[1]
            if potential_book_id.startswith("book_"):
                book_id = potential_book_id
    
    # Extract title
    title = item.title if item.title else None
    
    # Extract summary (from structured.ai_summary or description)
    summary = None
    if item.structured and isinstance(item.structured, dict):
        summary = item.structured.get("ai_summary") or item.structured.get("summary")
    if not summary:
        summary = item.description if item.description else None
    
    # Extract core_principles (from structured.ai_core_principles or rules)
    core_principles = []
    if item.structured and isinstance(item.structured, dict):
        core_principles = item.structured.get("ai_core_principles", [])
        if not core_principles:
            # Fallback to rules
            rules = item.structured.get("rules", [])
            if rules and isinstance(rules, list):
                core_principles = [r for r in rules if isinstance(r, str)]
    
    # Extract risk_rules (from structured.ai_risk_rules)
    risk_rules = []
    if item.structured and isinstance(item.structured, dict):
        risk_rules = item.structured.get("ai_risk_rules", [])
        if not risk_rules and isinstance(risk_rules, list):
            risk_rules = []
    
    # Extract tags (filter out DOCTRINE tag for cleaner output)
    tags = [t for t in item.tags if t.upper() != "DOCTRINE"]
    
    return DoctrineHit(
        book_id=book_id,
        section_id=section_id,
        title=title,
        summary=summary,
        core_principles=core_principles if isinstance(core_principles, list) else [],
        risk_rules=risk_rules if isinstance(risk_rules, list) else [],
        tags=tags if isinstance(tags, list) else []
    )

