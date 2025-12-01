"""Extract CONCEPT knowledge items from markdown files"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any
import re

from jgod.knowledge.extractors.base_extractor import (
    list_source_files,
    iter_blocks,
    extract_title_from_block,
    clean_markdown_annotations
)


class ConceptIdGenerator:
    """Generate unique concept IDs"""
    
    def __init__(self):
        self.counter = 0
    
    def next_id(self) -> str:
        """Generate next concept ID"""
        self.counter += 1
        return f"CONCEPT_{self.counter:04d}"


def extract_concept_name(text: str) -> str:
    """Extract concept name from text
    
    Args:
        text: Text containing concept definition
    
    Returns:
        Concept name
    """
    # Pattern: "概念名稱" 或 Concept Name
    name_patterns = [
        r'(?:概念|Concept|概念名稱)[：:：]\s*([A-Za-z0-9_\s]+)',
        r'([A-Z][A-Z0-9_]+)\s*[：:：]',
        r'#+\s*(.+?)\s*\n',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and len(name) < 50:
                return name
    
    return ""


def extract_definition(text: str) -> str:
    """Extract concept definition from text
    
    Args:
        text: Text containing concept definition
    
    Returns:
        Concept definition
    """
    # Look for definition markers
    def_patterns = [
        r'(?:定義|Definition|definition)[：:：]\s*(.+?)(?:\n\n|$)',
        r'([^。]+。{1,2})',  # First sentence ending with period
    ]
    
    for pattern in def_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            definition = clean_markdown_annotations(match.group(1).strip())
            if len(definition) > 10:
                return definition[:500]
    
    # Use first meaningful paragraph
    paragraphs = text.split('\n\n')
    for para in paragraphs:
        cleaned = clean_markdown_annotations(para.strip())
        if len(cleaned) > 20:
            return cleaned[:500]
    
    return ""


def extract_examples(text: str) -> List[str]:
    """Extract concept examples from text
    
    Args:
        text: Text potentially containing examples
    
    Returns:
        List of example strings
    """
    examples = []
    
    # Pattern: "例如" or "Examples"
    example_patterns = [
        r'(?:例如|Example|example)[：:：]?\s*\n?[\*\-\d\.]+\s*(.+?)(?:\n|$)',
        r'(?:例如|Example|example)[：:：]?\s*(.+?)(?:。|$|\n\n)',
    ]
    
    for pattern in example_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
            example = clean_markdown_annotations(match.group(1).strip())
            if example and len(example) > 5:
                examples.append(example[:200])
                if len(examples) >= 5:  # Limit examples
                    break
    
    # Also look for bullet points after "例如"
    if not examples:
        bullet_pattern = r'[\*\-\d\.]+\s*(.+?)(?:\n|$)'
        lines = text.split('\n')
        in_example_section = False
        for line in lines:
            if re.search(r'例如|Example|example', line, re.IGNORECASE):
                in_example_section = True
                continue
            if in_example_section:
                match = re.match(bullet_pattern, line.strip())
                if match:
                    example = clean_markdown_annotations(match.group(1).strip())
                    if example:
                        examples.append(example[:200])
                    if len(examples) >= 5:
                        break
    
    return examples[:5]  # Limit to 5 examples


def extract_concepts(source_dir: Path | None = None) -> List[Dict[str, Any]]:
    """Extract all CONCEPT knowledge items from source files
    
    Args:
        source_dir: Directory containing source markdown files. If None, uses default.
    
    Returns:
        List of dictionaries representing CONCEPT knowledge items
    """
    files = list_source_files(source_dir)
    id_gen = ConceptIdGenerator()
    concepts = []
    
    for file_path in files:
        source_doc = file_path.name
        
        for type_tag, block_lines, start_line in iter_blocks(file_path):
            block_text = ''.join(block_lines)
            
            # Check if this block contains a concept
            is_concept_block = (
                type_tag == "CONCEPT" or
                re.search(r'定義|Definition|概念|Concept|是什麼|What is|RCNC|LAC|Regime', block_text, re.IGNORECASE)
            )
            
            if not is_concept_block:
                continue
            
            # Extract concept name
            name = extract_concept_name(block_text)
            if not name:
                # Try to get from title
                name = extract_title_from_block(block_lines)
                name = clean_markdown_annotations(name)
            
            # Extract definition
            definition = extract_definition(block_text)
            if not definition:
                definition = clean_markdown_annotations(block_text)[:500]
            
            # Extract examples
            examples = extract_examples(block_text)
            
            # Extract title
            title = name if name else extract_title_from_block(block_lines)
            
            # Extract tags
            tags = []
            if re.search(r'RCNC|rcnc', block_text):
                tags.append("rcnc")
                tags.append("intraday")
            if re.search(r'LAC|lac', block_text):
                tags.append("lac")
            if re.search(r'Regime|regime|市場風格', block_text):
                tags.append("regime")
                tags.append("market")
            if re.search(r'因子|factor|Factor', block_text):
                tags.append("factor")
            if re.search(r'策略|strategy|Strategy', block_text):
                tags.append("strategy")
            
            # Create concept item
            concept_item = {
                "id": id_gen.next_id(),
                "type": "CONCEPT",
                "title": title[:100] if title else "Untitled Concept",
                "description": definition if definition else clean_markdown_annotations(block_text)[:500],
                "tags": list(set(tags)) if tags else [],
                "source_doc": source_doc,
                "source_location": f"line {start_line}",
                "raw_text": block_text,
                "structured": {
                    "name": name[:100] if name else title[:100] if title else "Unknown",
                    "definition": definition,
                    "examples": examples
                }
            }
            
            concepts.append(concept_item)
    
    return concepts

