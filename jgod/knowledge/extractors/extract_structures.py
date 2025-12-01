"""Extract STRUCTURE knowledge items from markdown files"""

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


class StructureIdGenerator:
    """Generate unique structure IDs"""
    
    def __init__(self):
        self.counter = 0
    
    def next_id(self) -> str:
        """Generate next structure ID"""
        self.counter += 1
        return f"STRUCTURE_{self.counter:04d}"


def parse_structure_tree(text: str) -> Dict[str, Any]:
    """Parse hierarchical structure from text
    
    Args:
        text: Text containing structure description
    
    Returns:
        Dictionary representing tree structure
    """
    tree = {}
    current_level = None
    current_section = None
    
    lines = text.split('\n')
    for line in lines:
        stripped = line.strip()
        
        # Check for heading levels
        h1_match = re.match(r'^#\s+(.+)$', stripped)
        h2_match = re.match(r'^##\s+(.+)$', stripped)
        h3_match = re.match(r'^###\s+(.+)$', stripped)
        
        if h1_match:
            current_level = h1_match.group(1).strip()
            tree[current_level] = {}
            current_section = None
        elif h2_match:
            section = h2_match.group(1).strip()
            if current_level:
                if current_level not in tree:
                    tree[current_level] = {}
                tree[current_level][section] = []
                current_section = section
        elif h3_match:
            subsection = h3_match.group(1).strip()
            if current_section and current_level:
                if current_level in tree and current_section in tree[current_level]:
                    tree[current_level][current_section].append(subsection)
    
    # If no hierarchy found, create simple structure
    if not tree:
        # Look for module/component mentions
        modules = re.findall(r'([A-Z][a-zA-Z\s]+Engine|Module|System)', text)
        if modules:
            tree = {"modules": list(set(modules))}
        else:
            tree = {"content": clean_markdown_annotations(text)[:500]}
    
    return tree


def extract_structures(source_dir: Path | None = None) -> List[Dict[str, Any]]:
    """Extract all STRUCTURE knowledge items from source files
    
    Args:
        source_dir: Directory containing source markdown files. If None, uses default.
    
    Returns:
        List of dictionaries representing STRUCTURE knowledge items
    """
    files = list_source_files(source_dir)
    id_gen = StructureIdGenerator()
    structures = []
    
    for file_path in files:
        source_doc = file_path.name
        
        for type_tag, block_lines, start_line in iter_blocks(file_path):
            block_text = ''.join(block_lines)
            
            # Check if this block contains structure information
            is_structure_block = (
                type_tag == "STRUCTURE" or
                re.search(r'架構|Architecture|系統結構|模組層級|Structure|Engine|Module|系統', block_text, re.IGNORECASE)
            )
            
            if not is_structure_block:
                continue
            
            # Parse structure tree
            tree = parse_structure_tree(block_text)
            
            # Extract title
            title = extract_title_from_block(block_lines)
            if not title or title == "Untitled":
                # Try to extract from first heading
                for line in block_lines:
                    heading_match = re.match(r'^#+\s+(.+)$', line.strip())
                    if heading_match:
                        title = heading_match.group(1).strip()
                        break
                if not title or title == "Untitled":
                    title = "System Structure"
            
            # Extract tags
            tags = []
            if re.search(r'架構|Architecture|architecture', block_text):
                tags.append("architecture")
            if re.search(r'模組|Module|module', block_text):
                tags.append("module")
            if re.search(r'系統|System|system', block_text):
                tags.append("system")
            if re.search(r'Engine|engine|引擎', block_text):
                tags.append("engine")
            
            # Create structure item
            structure_item = {
                "id": id_gen.next_id(),
                "type": "STRUCTURE",
                "title": title[:100] if title else "Untitled Structure",
                "description": clean_markdown_annotations(block_text)[:500],
                "tags": list(set(tags)) if tags else [],
                "source_doc": source_doc,
                "source_location": f"line {start_line}",
                "raw_text": block_text,
                "structured": {
                    "tree": tree
                }
            }
            
            structures.append(structure_item)
    
    return structures

