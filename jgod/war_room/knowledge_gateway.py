"""
Knowledge Gateway for J-GOD War Room and All Engines

This module is the unified entry point for the J-GOD Knowledge Brain (v1).
All engines (factor, signal, risk, execution) and the war room should query
trading rules, formulas, concepts, and structured knowledge via this gateway.

Usage:
    from jgod.war_room.knowledge_gateway import (
        get_knowledge_brain,
        ask_for_rules,
        ask_for_formulas,
        ask_for_concept
    )
    
    # Get all risk rules
    risk_rules = ask_for_rules(tag="risk")
    
    # Get performance formulas
    formulas = ask_for_formulas(tag="performance")
    
    # Explain a concept
    rcnc = ask_for_concept("RCNC")
"""

from __future__ import annotations

from typing import Optional, List
from pathlib import Path

from jgod.knowledge.knowledge_brain import KnowledgeBrain, KnowledgeItem


# Singleton instance
_knowledge_brain: Optional[KnowledgeBrain] = None


def get_knowledge_brain() -> KnowledgeBrain:
    """Get or create the singleton KnowledgeBrain instance
    
    This function implements lazy loading - the knowledge base is only loaded
    when first accessed.
    
    Returns:
        KnowledgeBrain: The singleton KnowledgeBrain instance
    
    Example:
        brain = get_knowledge_brain()
        all_items = brain.get_all()
    """
    global _knowledge_brain
    
    if _knowledge_brain is None:
        # Use default path: knowledge_base/jgod_knowledge_v1.jsonl
        _knowledge_brain = KnowledgeBrain()
        _knowledge_brain.load()
    
    return _knowledge_brain


def ask_for_rules(tag: Optional[str] = None) -> List[KnowledgeItem]:
    """Ask the knowledge brain for rules, optionally filtered by tag
    
    Args:
        tag: Optional tag to filter rules (e.g., "risk", "entry", "exit")
    
    Returns:
        List of KnowledgeItem with type="RULE"
    
    Examples:
        # Get all risk-related rules
        risk_rules = ask_for_rules(tag="risk")
        
        # Get all entry rules
        entry_rules = ask_for_rules(tag="entry")
        
        # Get all rules
        all_rules = ask_for_rules()
    """
    brain = get_knowledge_brain()
    return brain.get_rules(tag=tag)


def ask_for_formulas(tag: Optional[str] = None) -> List[KnowledgeItem]:
    """Ask the knowledge brain for formulas, optionally filtered by tag
    
    Args:
        tag: Optional tag to filter formulas (e.g., "risk", "performance", "sharpe")
    
    Returns:
        List of KnowledgeItem with type="FORMULA"
    
    Examples:
        # Get all performance-related formulas
        perf_formulas = ask_for_formulas(tag="performance")
        
        # Get all risk formulas
        risk_formulas = ask_for_formulas(tag="risk")
        
        # Get all formulas
        all_formulas = ask_for_formulas()
    """
    brain = get_knowledge_brain()
    return brain.get_formulas(tag=tag)


def ask_for_concept(name: str) -> Optional[KnowledgeItem]:
    """Ask the knowledge brain to explain a concept by name
    
    Args:
        name: Concept name to search for (e.g., "RCNC", "Sharpe Ratio")
    
    Returns:
        KnowledgeItem of type CONCEPT if found, None otherwise
    
    Examples:
        # Explain RCNC
        rcnc = ask_for_concept("RCNC")
        if rcnc:
            print(rcnc.description)
            print(rcnc.structured["definition"])
        
        # Explain Sharpe Ratio
        sharpe = ask_for_concept("Sharpe Ratio")
    """
    brain = get_knowledge_brain()
    return brain.explain_concept(name)


def reload_knowledge() -> None:
    """Reload the knowledge base from file
    
    Useful when knowledge base has been updated externally and you want
    to refresh the in-memory cache.
    
    Example:
        # After updating knowledge_base/jgod_knowledge_v1.jsonl
        reload_knowledge()
    """
    global _knowledge_brain
    
    if _knowledge_brain is not None:
        _knowledge_brain.reload()
    else:
        # Force reload by resetting singleton
        _knowledge_brain = None
        get_knowledge_brain()

