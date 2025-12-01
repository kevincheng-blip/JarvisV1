"""Base Extractor Utilities

Common utilities for extracting knowledge from structured markdown files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, Tuple, List
import re


def list_source_files(source_dir: Path | None = None) -> List[Path]:
    """List all source markdown files to extract from
    
    Scans the structured_books/ directory for files matching:
    - *_CORRECTED.md
    - *_AI知識庫版_v1.md
    
    Args:
        source_dir: Directory to scan. If None, uses structured_books/ relative to project root.
    
    Returns:
        List of Path objects sorted by filename
    
    Example:
        files = list_source_files()
        for file in files:
            print(file.name)
    """
    if source_dir is None:
        # Default to structured_books/ relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        source_dir = project_root / "structured_books"
    
    source_dir = Path(source_dir)
    if not source_dir.exists():
        return []
    
    files = []
    
    # Pattern 1: *_CORRECTED.md
    files.extend(source_dir.glob("*_CORRECTED.md"))
    
    # Pattern 2: *_AI知識庫版_v1.md
    files.extend(source_dir.glob("*_AI知識庫版_v1.md"))
    
    # Remove duplicates and sort
    files = sorted(set(files))
    
    return files


def normalize_type_tag(type_tag: str) -> str:
    """Normalize type tag to uppercase schema format
    
    Converts "[RULE]", "RULE", "[Rule]" etc. to "RULE"
    
    Args:
        type_tag: Type tag string (may include brackets, mixed case)
    
    Returns:
        Uppercase normalized type tag (RULE, FORMULA, CONCEPT, etc.)
    
    Example:
        normalize_type_tag("[RULE]")  # Returns: "RULE"
        normalize_type_tag("formula")  # Returns: "FORMULA"
    """
    # Remove brackets if present
    cleaned = re.sub(r'[\[\]]', '', type_tag.strip())
    
    # Convert to uppercase
    normalized = cleaned.upper()
    
    # Valid types
    valid_types = {"RULE", "FORMULA", "CONCEPT", "STRUCTURE", "TABLE", "CODE", "NOTE"}
    
    # If it's a valid type, return it; otherwise return as-is for flexibility
    return normalized if normalized in valid_types else normalized


def iter_blocks(path: Path) -> Iterator[Tuple[str, List[str], int]]:
    """Iterate over knowledge blocks in a markdown file
    
    This is a flexible block parser that tries to identify knowledge blocks
    based on content patterns since the markdown files don't have explicit
    [RULE], [FORMULA] markers.
    
    Currently returns blocks based on:
    1. Explicit markers like [RULE], [FORMULA] (if found)
    2. Content-based detection (formulas, rules, concepts)
    
    Args:
        path: Path to markdown file
    
    Yields:
        Tuple of (type_tag, lines, start_line_number)
        - type_tag: Detected type (RULE, FORMULA, CONCEPT, etc.)
        - lines: List of lines in the block
        - start_line_number: Line number where block starts (1-based)
    
    Example:
        for type_tag, lines, line_num in iter_blocks(Path("file.md")):
            if type_tag == "RULE":
                # Process rule block
                pass
    """
    if not path.exists():
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
    
    current_block_type = None
    current_block_lines = []
    current_start_line = 1
    
    # Patterns for detecting block types
    explicit_marker_pattern = re.compile(r'^\*\*\[(RULE|FORMULA|CONCEPT|CODE|TABLE|STRUCTURE|NOTE)\]', re.IGNORECASE)
    formula_pattern = re.compile(r'\$\$|外部知識補強.*公式|公式：|Formula|formula')
    rule_pattern = re.compile(r'Rules_Entry|Rules_Exit|進場條件|出場條件|停損|規則|Rule|rule')
    concept_pattern = re.compile(r'定義|Definition|概念|Concept|是什麼|What is')
    code_pattern = re.compile(r'```python|```sql|```bash|程式碼|Code|code')
    structure_pattern = re.compile(r'架構|Architecture|系統結構|模組層級|Structure')
    
    for i, line in enumerate(all_lines, 1):
        stripped = line.strip()
        
        # Check for explicit marker
        explicit_match = explicit_marker_pattern.match(stripped)
        if explicit_match:
            # Yield previous block if exists
            if current_block_type and current_block_lines:
                yield (normalize_type_tag(current_block_type), current_block_lines, current_start_line)
            
            # Start new block
            current_block_type = explicit_match.group(1)
            current_block_lines = [line]
            current_start_line = i
            continue
        
        # Check for content-based patterns (only if we're not already in a block)
        if not current_block_type:
            if formula_pattern.search(stripped):
                current_block_type = "FORMULA"
                current_block_lines = [line]
                current_start_line = i
                continue
            elif rule_pattern.search(stripped):
                current_block_type = "RULE"
                current_block_lines = [line]
                current_start_line = i
                continue
            elif concept_pattern.search(stripped):
                current_block_type = "CONCEPT"
                current_block_lines = [line]
                current_start_line = i
                continue
            elif code_pattern.search(stripped):
                current_block_type = "CODE"
                current_block_lines = [line]
                current_start_line = i
                continue
            elif structure_pattern.search(stripped):
                current_block_type = "STRUCTURE"
                current_block_lines = [line]
                current_start_line = i
                continue
        
        # Accumulate lines in current block
        if current_block_type:
            current_block_lines.append(line)
            
            # Heuristic: Block ends when we hit a new major section (## heading)
            # or empty line + new heading pattern
            if stripped.startswith('##') and len(current_block_lines) > 1:
                # Yield current block
                yield (normalize_type_tag(current_block_type), current_block_lines[:-1], current_start_line)
                # Reset for potential new block
                current_block_type = None
                current_block_lines = []
                current_start_line = i
    
    # Yield final block if exists
    if current_block_type and current_block_lines:
        yield (normalize_type_tag(current_block_type), current_block_lines, current_start_line)


def extract_title_from_block(lines: List[str]) -> str:
    """Extract title from a block of lines
    
    Tries to find the first meaningful title/heading in the block.
    
    Args:
        lines: List of lines in the block
    
    Returns:
        Extracted title string
    """
    for line in lines:
        stripped = line.strip()
        # Skip empty lines and markers
        if not stripped or stripped.startswith('[') or stripped.startswith('**['):
            continue
        
        # Remove markdown formatting
        stripped = re.sub(r'^#+\s*', '', stripped)  # Remove heading markers
        stripped = re.sub(r'\*\*', '', stripped)  # Remove bold markers
        stripped = re.sub(r'\[.*?\]', '', stripped)  # Remove bracketed annotations
        
        if stripped and len(stripped) > 3:
            # Limit title length
            return stripped[:100]
    
    return "Untitled"


def clean_markdown_annotations(text: str) -> str:
    """Remove markdown annotations and formatting
    
    Args:
        text: Text with markdown annotations
    
    Returns:
        Cleaned text
    """
    # Remove common annotations
    text = re.sub(r'\*\*\[.*?\]\*\*', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'^\*\*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*$', '', text, flags=re.MULTILINE)
    
    return text.strip()

