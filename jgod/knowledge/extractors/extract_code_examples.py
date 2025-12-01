"""Extract CODE knowledge items from markdown files"""

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


class CodeIdGenerator:
    """Generate unique code IDs"""
    
    def __init__(self):
        self.counter = 0
    
    def next_id(self) -> str:
        """Generate next code ID"""
        self.counter += 1
        return f"CODE_{self.counter:04d}"


def extract_code_block(lines: List[str]) -> tuple[str, str]:
    """Extract code block from lines
    
    Args:
        lines: Block lines potentially containing code
    
    Returns:
        Tuple of (language, code_content)
    """
    code_blocks = []
    current_language = "python"
    in_code_block = False
    current_code = []
    
    for line in lines:
        # Check for code block start
        code_start_match = re.match(r'```(\w+)', line)
        if code_start_match:
            if in_code_block and current_code:
                code_blocks.append((current_language, '\n'.join(current_code)))
            current_language = code_start_match.group(1)
            in_code_block = True
            current_code = []
            continue
        
        # Check for code block end
        if line.strip() == '```' and in_code_block:
            if current_code:
                code_blocks.append((current_language, '\n'.join(current_code)))
            in_code_block = False
            current_code = []
            continue
        
        # Accumulate code lines
        if in_code_block:
            current_code.append(line)
    
    # Handle unclosed code block
    if in_code_block and current_code:
        code_blocks.append((current_language, '\n'.join(current_code)))
    
    # Return first code block, or default
    if code_blocks:
        return code_blocks[0]
    
    return ("unknown", "")


def extract_code_examples(source_dir: Path | None = None) -> List[Dict[str, Any]]:
    """Extract all CODE knowledge items from source files
    
    Args:
        source_dir: Directory containing source markdown files. If None, uses default.
    
    Returns:
        List of dictionaries representing CODE knowledge items
    """
    files = list_source_files(source_dir)
    id_gen = CodeIdGenerator()
    code_items = []
    
    for file_path in files:
        source_doc = file_path.name
        
        for type_tag, block_lines, start_line in iter_blocks(file_path):
            block_text = ''.join(block_lines)
            
            # Check if this block contains code
            is_code_block = (
                type_tag == "CODE" or
                re.search(r'```python|```sql|```bash|程式碼|Code|code|程式化說明', block_text, re.IGNORECASE)
            )
            
            if not is_code_block:
                continue
            
            # Extract code block
            language, code_content = extract_code_block(block_lines)
            
            if not code_content or len(code_content.strip()) < 5:
                continue
            
            # Extract title
            title = extract_title_from_block(block_lines)
            if not title or title == "Untitled":
                # Try to extract from context
                for line in block_lines:
                    if not line.strip().startswith('```') and len(line.strip()) > 5:
                        title = clean_markdown_annotations(line.strip())[:80]
                        break
                if not title or title == "Untitled":
                    title = f"Code Example ({language})"
            
            # Extract tags
            tags = []
            if language:
                tags.append(language.lower())
            if re.search(r'factor|因子', block_text, re.IGNORECASE):
                tags.append("factor")
            if re.search(r'strategy|策略', block_text, re.IGNORECASE):
                tags.append("strategy")
            if re.search(r'risk|風險', block_text, re.IGNORECASE):
                tags.append("risk")
            if re.search(r'example|範例', block_text, re.IGNORECASE):
                tags.append("example")
            
            # Create code item
            code_item = {
                "id": id_gen.next_id(),
                "type": "CODE",
                "title": title[:100] if title else f"Code Example ({language})",
                "description": clean_markdown_annotations(block_text)[:500],
                "tags": list(set(tags)) if tags else [],
                "source_doc": source_doc,
                "source_location": f"line {start_line}",
                "raw_text": block_text,
                "structured": {
                    "language": language if language else "unknown",
                    "code": code_content
                }
            }
            
            code_items.append(code_item)
    
    return code_items

