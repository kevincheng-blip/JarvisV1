"""Extract FORMULA knowledge items from markdown files"""

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


class FormulaIdGenerator:
    """Generate unique formula IDs"""
    
    def __init__(self):
        self.counter = 0
    
    def next_id(self) -> str:
        """Generate next formula ID"""
        self.counter += 1
        return f"FORMULA_{self.counter:04d}"


def extract_latex_formula(text: str) -> str:
    """Extract LaTeX formula from text
    
    Args:
        text: Text potentially containing LaTeX formulas
    
    Returns:
        Extracted formula expression
    """
    # Match $$ ... $$ blocks
    latex_match = re.search(r'\$\$(.+?)\$\$', text, re.DOTALL)
    if latex_match:
        return latex_match.group(1).strip()
    
    # Match $ ... $ inline formulas
    inline_match = re.search(r'\$(.+?)\$', text)
    if inline_match:
        return inline_match.group(1).strip()
    
    # Match formula-like patterns
    formula_patterns = [
        r'(?:公式|Formula|formula)[：:：]?\s*(.+?)(?:\n|$)',
        r'([A-Za-z_]+\s*=\s*.+?)(?:\n|$)',
        r'([A-Za-z_]+\s*\([^)]+\)\s*=\s*.+)',
    ]
    
    for pattern in formula_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ""


def extract_variables(text: str) -> Dict[str, str]:
    """Extract variable descriptions from text
    
    Args:
        text: Text potentially containing variable definitions
    
    Returns:
        Dictionary mapping variable names to descriptions
    """
    variables = {}
    
    # Pattern: variable_name: description
    var_pattern = r'([A-Za-z_][A-Za-z0-9_]*)[：:：]\s*(.+?)(?:\n|$|，|,)'
    for match in re.finditer(var_pattern, text):
        var_name = match.group(1)
        var_desc = match.group(2).strip()
        variables[var_name] = var_desc
    
    # Pattern: $variable_name$ = description
    latex_var_pattern = r'\$([A-Za-z_][A-Za-z0-9_]*)\$\s*[=＝]\s*(.+?)(?:\n|$)'
    for match in re.finditer(latex_var_pattern, text):
        var_name = match.group(1)
        var_desc = match.group(2).strip()
        variables[var_name] = var_desc
    
    return variables


def extract_formulas(source_dir: Path | None = None) -> List[Dict[str, Any]]:
    """Extract all FORMULA knowledge items from source files
    
    Args:
        source_dir: Directory containing source markdown files. If None, uses default.
    
    Returns:
        List of dictionaries representing FORMULA knowledge items
    """
    files = list_source_files(source_dir)
    id_gen = FormulaIdGenerator()
    formulas = []
    
    for file_path in files:
        source_doc = file_path.name
        
        for type_tag, block_lines, start_line in iter_blocks(file_path):
            block_text = ''.join(block_lines)
            
            # Check if this block contains a formula
            is_formula_block = (
                type_tag == "FORMULA" or
                re.search(r'\$\$|外部知識補強.*公式|公式：|Formula|formula|Sharpe|Drawdown|Beta|Win.*Rate', block_text, re.IGNORECASE)
            )
            
            if not is_formula_block:
                continue
            
            # Extract LaTeX formula
            expression = extract_latex_formula(block_text)
            
            # If no LaTeX found, try to extract from text
            if not expression:
                # Look for formula-like expressions
                formula_match = re.search(r'([A-Za-z_][A-Za-z0-9_]*\s*[=＝]\s*.+?)(?:\n|$|。)', block_text)
                if formula_match:
                    expression = formula_match.group(1).strip()
            
            # Extract title
            title = extract_title_from_block(block_lines)
            if not title or title == "Untitled":
                # Try to extract from formula name
                name_match = re.search(r'(?:公式|Formula)[：:：]?\s*([A-Za-z_\s]+)', block_text, re.IGNORECASE)
                if name_match:
                    title = name_match.group(1).strip()
                else:
                    # Extract from first meaningful line
                    for line in block_lines:
                        stripped = clean_markdown_annotations(line.strip())
                        if stripped and len(stripped) > 3:
                            title = stripped[:80]
                            break
            
            # Extract variables
            variables = extract_variables(block_text)
            
            # Extract notes (everything else)
            notes = clean_markdown_annotations(block_text)
            # Remove formula expression from notes if present
            if expression:
                notes = notes.replace(expression, "").strip()
            
            # Extract tags
            tags = []
            if re.search(r'Sharpe|sharpe', block_text, re.IGNORECASE):
                tags.append("sharpe")
            if re.search(r'Drawdown|drawdown|回撤', block_text):
                tags.append("drawdown")
            if re.search(r'Beta|beta', block_text):
                tags.append("beta")
            if re.search(r'Win.*Rate|勝率|勝率', block_text, re.IGNORECASE):
                tags.append("win_rate")
            if re.search(r'風險|risk|Risk|performance', block_text, re.IGNORECASE):
                tags.append("risk")
                tags.append("performance")
            if re.search(r'統計|statistical|統計', block_text):
                tags.append("statistics")
            
            # Create formula item
            formula_item = {
                "id": id_gen.next_id(),
                "type": "FORMULA",
                "title": title[:100] if title else "Untitled Formula",
                "description": notes[:500] if notes else "",
                "tags": list(set(tags)) if tags else [],
                "source_doc": source_doc,
                "source_location": f"line {start_line}",
                "raw_text": ''.join(block_lines),
                "structured": {
                    "expression": expression or notes[:200],
                    "variables": variables if variables else {},
                    "notes": notes[:500] if notes else ""
                }
            }
            
            formulas.append(formula_item)
    
    return formulas

