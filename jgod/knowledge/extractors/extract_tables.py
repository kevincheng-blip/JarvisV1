"""Extract TABLE knowledge items from markdown files"""

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


class TableIdGenerator:
    """Generate unique table IDs"""
    
    def __init__(self):
        self.counter = 0
    
    def next_id(self) -> str:
        """Generate next table ID"""
        self.counter += 1
        return f"TABLE_{self.counter:04d}"


def parse_markdown_table(lines: List[str]) -> tuple[List[str], List[List[str]]]:
    """Parse markdown table from lines
    
    Args:
        lines: Block lines containing markdown table
    
    Returns:
        Tuple of (columns, rows)
    """
    columns = []
    rows = []
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check for table header
        if '|' in stripped and not in_table:
            # Extract column names
            parts = [p.strip() for p in stripped.split('|') if p.strip()]
            if parts and not all(p.startswith('-') for p in parts):
                columns = parts
                in_table = True
                continue
        
        # Skip separator line
        if in_table and all(c in '-:|' for c in stripped):
            continue
        
        # Extract data rows
        if in_table and '|' in stripped:
            parts = [p.strip() for p in stripped.split('|') if p.strip()]
            if parts:
                rows.append(parts[:len(columns)])  # Match column count
    
    return columns, rows


def extract_tables(source_dir: Path | None = None) -> List[Dict[str, Any]]:
    """Extract all TABLE knowledge items from source files
    
    Args:
        source_dir: Directory containing source markdown files. If None, uses default.
    
    Returns:
        List of dictionaries representing TABLE knowledge items
    """
    files = list_source_files(source_dir)
    id_gen = TableIdGenerator()
    tables = []
    
    for file_path in files:
        source_doc = file_path.name
        
        for type_tag, block_lines, start_line in iter_blocks(file_path):
            block_text = ''.join(block_lines)
            
            # Check if this block contains a table
            is_table_block = (
                type_tag == "TABLE" or
                '|' in block_text and block_text.count('|') > 5  # Heuristic: multiple pipes indicate table
            )
            
            if not is_table_block:
                continue
            
            # Parse table
            columns, rows = parse_markdown_table(block_lines)
            
            if not columns or not rows:
                continue
            
            # Extract title
            title = extract_title_from_block(block_lines)
            if not title or title == "Untitled":
                # Look for title before table
                for i, line in enumerate(block_lines):
                    if '|' in line:
                        # Check previous non-empty line
                        for prev_line in reversed(block_lines[:i]):
                            if prev_line.strip() and not prev_line.strip().startswith('|'):
                                title = clean_markdown_annotations(prev_line.strip())
                                break
                        break
                if not title or title == "Untitled":
                    title = "Data Table"
            
            # Extract tags
            tags = []
            if re.search(r'欄位|column|Column', block_text):
                tags.append("schema")
            if re.search(r'策略|strategy|Strategy', block_text):
                tags.append("strategy")
            if re.search(r'資料|data|Data', block_text):
                tags.append("data")
            
            # Create table item
            table_item = {
                "id": id_gen.next_id(),
                "type": "TABLE",
                "title": title[:100] if title else "Untitled Table",
                "description": clean_markdown_annotations(block_text)[:500],
                "tags": list(set(tags)) if tags else [],
                "source_doc": source_doc,
                "source_location": f"line {start_line}",
                "raw_text": block_text,
                "structured": {
                    "columns": columns,
                    "rows": rows[:50]  # Limit rows to prevent huge JSON
                }
            }
            
            tables.append(table_item)
    
    return tables

