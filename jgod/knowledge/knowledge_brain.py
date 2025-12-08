"""J-GOD Knowledge Brain v1

This module implements the KnowledgeBrain class for querying structured knowledge
from the J-GOD knowledge base (JSONL format).

See docs/JGOD_Knowledge_Schema_v1.md for schema specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json
import re


@dataclass
class KnowledgeItem:
    """Knowledge Item data structure
    
    Represents a single piece of structured knowledge (formula, rule, concept, etc.)
    See docs/JGOD_Knowledge_Schema_v1.md for full schema specification.
    """
    id: str
    type: str  # TABLE / CODE / FORMULA / RULE / CONCEPT / STRUCTURE / NOTE
    title: str
    description: str
    tags: List[str] = field(default_factory=list)
    source_doc: str = ""
    source_location: str = ""
    raw_text: str = ""
    structured: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> KnowledgeItem:
        """Create KnowledgeItem from dictionary"""
        return cls(
            id=data.get("id", ""),
            type=data.get("type", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            source_doc=data.get("source_doc", ""),
            source_location=data.get("source_location", ""),
            raw_text=data.get("raw_text", ""),
            structured=data.get("structured")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert KnowledgeItem to dictionary"""
        result = {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "source_doc": self.source_doc,
            "source_location": self.source_location,
            "raw_text": self.raw_text
        }
        if self.structured:
            result["structured"] = self.structured
        return result


# Default knowledge base files (multiple sources)
DEFAULT_KNOWLEDGE_FILES = [
    "knowledge_base/jgod_knowledge_v1.jsonl",
    "knowledge_base/jgod_doctrine_knowledge_v1.jsonl",
]


class KnowledgeBrain:
    """J-GOD Knowledge Brain v1
    
    A knowledge query system for structured knowledge items (formulas, rules,
    concepts, etc.) stored in JSONL format.
    
    Supports loading from multiple knowledge base files, including:
    - Default knowledge base: knowledge_base/jgod_knowledge_v1.jsonl
    - Doctrine knowledge base: knowledge_base/jgod_doctrine_knowledge_v1.jsonl
    
    Usage:
        brain = KnowledgeBrain()
        brain.load()
        rules = brain.get_rules(tag="risk")
        formulas = brain.get_formulas(tag="performance")
        results = brain.search("Sharpe Ratio", type="FORMULA")
        doctrine_results = brain.search_doctrine("風控規則")
    """
    
    def __init__(self, path: Optional[Union[str, Path, List[Union[str, Path]]]] = None):
        """Initialize KnowledgeBrain
        
        Args:
            path: Path(s) to knowledge base JSONL file(s). If None, uses default paths:
                  - knowledge_base/jgod_knowledge_v1.jsonl
                  - knowledge_base/jgod_doctrine_knowledge_v1.jsonl
                  
                  Can be:
                  - Single string/Path: Single file path
                  - List of strings/Paths: Multiple file paths
        """
        if path is None:
            # Default: use multiple knowledge base files
            project_root = Path(__file__).parent.parent.parent
            self.paths = [project_root / p for p in DEFAULT_KNOWLEDGE_FILES]
        elif isinstance(path, (str, Path)):
            # Single path (backward compatibility)
            self.paths = [Path(path)]
        else:
            # List of paths
            self.paths = [Path(p) for p in path]
        
        self._items: List[KnowledgeItem] = []
        self._by_id: Dict[str, KnowledgeItem] = {}
        self._by_type: Dict[str, List[KnowledgeItem]] = {}
        self._loaded: bool = False
    
    def load(self) -> None:
        """Load knowledge items from JSONL file(s)
        
        Loads from multiple files if multiple paths were provided.
        Merges all entries into a single in-memory index.
        
        Raises:
            FileNotFoundError: If no knowledge base files exist (only warns if some files are missing)
            json.JSONDecodeError: If JSON parsing fails
        """
        self._items = []
        self._by_id = {}
        self._by_type = {}
        
        total_loaded = 0
        for path in self.paths:
            if not path.exists():
                # Warn but continue loading other files
                print(f"Warning: Knowledge base file not found: {path} (skipping)")
                continue
            
            # Ensure parent directory exists (for new files)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            file_loaded = 0
            with open(path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        item = KnowledgeItem.from_dict(data)
                        
                        # Skip if duplicate ID (later files override earlier ones)
                        if item.id in self._by_id:
                            # Update existing item
                            old_item = self._by_id[item.id]
                            # Remove old item from type index
                            if old_item.type in self._by_type:
                                self._by_type[old_item.type] = [
                                    i for i in self._by_type[old_item.type] if i.id != item.id
                                ]
                            # Remove old item from items list
                            self._items = [i for i in self._items if i.id != item.id]
                        
                        self._items.append(item)
                        self._by_id[item.id] = item
                        
                        # Index by type
                        if item.type not in self._by_type:
                            self._by_type[item.type] = []
                        self._by_type[item.type].append(item)
                        
                        file_loaded += 1
                        total_loaded += 1
                        
                    except json.JSONDecodeError as e:
                        # Skip invalid JSON lines but log error
                        print(f"Warning: Failed to parse line {line_num} in {path}: {e}")
                        continue
            
            if file_loaded > 0:
                print(f"Loaded {file_loaded} knowledge items from {path.name}")
        
        if total_loaded == 0:
            print(f"Warning: No knowledge items loaded from any of the specified files")
        
        self._loaded = True
    
    def search(self,
               query: Optional[str] = None,
               type: Optional[str] = None,
               tags: Optional[List[str]] = None,
               limit: int = 20,
               require_doctrine: bool = False) -> List[KnowledgeItem]:
        """Search knowledge items with multiple filters
        
        Args:
            query: Keyword to search in title, description, and raw_text
            type: Filter by knowledge type (FORMULA, RULE, CONCEPT, etc.)
            tags: Filter by tags (items must match at least one tag)
            limit: Maximum number of results to return
            require_doctrine: If True, only search items with "DOCTRINE" tag
        
        Returns:
            List of KnowledgeItem matching the criteria
        
        Examples:
            # Search for "Sharpe" in all items
            results = brain.search(query="Sharpe")
            
            # Get all risk-related rules
            rules = brain.search(type="RULE", tags=["risk"])
            
            # Find formulas about performance
            formulas = brain.search(type="FORMULA", tags=["performance"])
            
            # Search only in Doctrine knowledge base
            doctrine_results = brain.search(query="風控", require_doctrine=True)
        """
        if not self._loaded:
            self.load()
        
        candidates = self._items
        
        # Filter by Doctrine requirement
        if require_doctrine:
            candidates = [
                item for item in candidates
                if "DOCTRINE" in [tag.upper() for tag in item.tags]
            ]
        
        # Filter by type
        if type:
            type_upper = type.upper()
            candidates = [item for item in candidates if item.type == type_upper]
        
        # Filter by tags
        if tags:
            tag_set = set(t.lower() for t in tags)
            candidates = [
                item for item in candidates
                if any(tag.lower() in tag_set for tag in item.tags)
            ]
        
        # Filter by query (text search)
        if query:
            query_lower = query.lower()
            filtered = []
            for item in candidates:
                # Search in title, description, and raw_text
                if (query_lower in item.title.lower() or
                    query_lower in item.description.lower() or
                    query_lower in item.raw_text.lower()):
                    filtered.append(item)
            candidates = filtered
        
        # Sort by relevance (simple: exact title match first, then description match)
        if query:
            query_lower = query.lower()
            candidates.sort(key=lambda x: (
                0 if query_lower in x.title.lower() else 1,
                0 if query_lower in x.description.lower() else 1
            ))
        
        return candidates[:limit]
    
    def get_by_id(self, item_id: str) -> Optional[KnowledgeItem]:
        """Get knowledge item by ID
        
        Args:
            item_id: Unique identifier of the knowledge item
        
        Returns:
            KnowledgeItem if found, None otherwise
        
        Example:
            item = brain.get_by_id("formula_sharpe_ratio_001")
        """
        if not self._loaded:
            self.load()
        
        return self._by_id.get(item_id)
    
    def get_rules(self, tag: Optional[str] = None) -> List[KnowledgeItem]:
        """Get all rules, optionally filtered by tag
        
        Args:
            tag: Optional tag to filter rules
        
        Returns:
            List of KnowledgeItem with type="RULE"
        
        Example:
            risk_rules = brain.get_rules(tag="risk")
            all_rules = brain.get_rules()
        """
        if not self._loaded:
            self.load()
        
        rules = self._by_type.get("RULE", [])
        
        if tag:
            tag_lower = tag.lower()
            rules = [r for r in rules if any(tag_lower in t.lower() for t in r.tags)]
        
        return rules
    
    def get_formulas(self, tag: Optional[str] = None) -> List[KnowledgeItem]:
        """Get all formulas, optionally filtered by tag
        
        Args:
            tag: Optional tag to filter formulas
        
        Returns:
            List of KnowledgeItem with type="FORMULA"
        
        Example:
            risk_formulas = brain.get_formulas(tag="risk")
            all_formulas = brain.get_formulas()
        """
        if not self._loaded:
            self.load()
        
        formulas = self._by_type.get("FORMULA", [])
        
        if tag:
            tag_lower = tag.lower()
            formulas = [f for f in formulas if any(tag_lower in t.lower() for t in f.tags)]
        
        return formulas
    
    def explain_concept(self, name: str) -> Optional[KnowledgeItem]:
        """Explain a concept by name
        
        Searches for concepts matching the given name in structured.name or title.
        
        Args:
            name: Concept name to search for
        
        Returns:
            KnowledgeItem of type CONCEPT if found, None otherwise
        
        Example:
            rcnc = brain.explain_concept("RCNC")
            sharpe = brain.explain_concept("Sharpe Ratio")
        """
        if not self._loaded:
            self.load()
        
        name_lower = name.lower()
        concepts = self._by_type.get("CONCEPT", [])
        
        for concept in concepts:
            # Check title
            if name_lower in concept.title.lower():
                return concept
            
            # Check structured.name
            if (concept.structured and 
                isinstance(concept.structured, dict) and
                "name" in concept.structured):
                if name_lower in concept.structured["name"].lower():
                    return concept
        
        return None
    
    def get_all(self) -> List[KnowledgeItem]:
        """Get all knowledge items
        
        Returns:
            List of all KnowledgeItem in the knowledge base
        """
        if not self._loaded:
            self.load()
        
        return self._items.copy()
    
    def count(self) -> int:
        """Get total number of knowledge items
        
        Returns:
            Total count of knowledge items
        """
        if not self._loaded:
            self.load()
        
        return len(self._items)
    
    def reload(self) -> None:
        """Reload knowledge items from file(s)
        
        Useful when knowledge base has been updated externally.
        """
        self._loaded = False
        self.load()
    
    def search_doctrine(self, query: str, top_k: int = 10) -> List[KnowledgeItem]:
        """Search only in Doctrine knowledge base
        
        Convenience method that searches only items tagged with "DOCTRINE".
        
        Args:
            query: Keyword to search in title, description, and raw_text
            top_k: Maximum number of results to return (alias for limit)
        
        Returns:
            List of KnowledgeItem from Doctrine knowledge base matching the query
        
        Example:
            # Search for risk rules in Doctrine knowledge base
            doctrine_rules = brain.search_doctrine("風控規則")
        """
        return self.search(query=query, limit=top_k, require_doctrine=True)

