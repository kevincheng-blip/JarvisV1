"""Extract RULE knowledge items from markdown files"""

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


class RuleIdGenerator:
    """Generate unique rule IDs"""
    
    def __init__(self):
        self.counter = 0
    
    def next_id(self) -> str:
        """Generate next rule ID"""
        self.counter += 1
        return f"RULE_{self.counter:04d}"


def parse_rule_content(lines: List[str]) -> Dict[str, Any]:
    """Parse rule content from block lines
    
    Args:
        lines: Block lines containing rule content
    
    Returns:
        Dictionary with parsed rule components
    """
    text = ''.join(lines)
    
    # Try to extract IF/THEN pattern
    if_match = re.search(r'(?:如果|若|當|if|IF|If)[：:：]?\s*(.+?)(?:則|則|那麼|then|THEN|Then|→)', text, re.IGNORECASE | re.DOTALL)
    then_match = re.search(r'(?:則|那麼|then|THEN|Then|→|必須|應該|執行|行動)[：:：]?\s*(.+?)(?:\.|$|\\n)', text, re.IGNORECASE | re.DOTALL)
    
    # Alternative patterns
    if not if_match:
        if_match = re.search(r'(?:條件|條件是|condition)[：:：]?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if not then_match:
        then_match = re.search(r'(?:行動|結果|action|result)[：:：]?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    
    # Extract priority based on keywords
    priority = 3  # Default
    if re.search(r'必須|必須|critical|Critical|重要|high priority', text):
        priority = 10
    elif re.search(r'建議|recommend|建議|medium priority', text):
        priority = 5
    
    # Extract scope
    scope = "unknown"
    if re.search(r'進場|entry|Entry|進場條件', text):
        scope = "entry"
    elif re.search(r'出場|exit|Exit|出場條件', text):
        scope = "exit"
    elif re.search(r'風控|risk|Risk|風險', text):
        scope = "risk"
    elif re.search(r'策略|strategy|Strategy', text):
        scope = "strategy"
    
    # Extract tags
    tags = []
    if re.search(r'風險|risk|Risk', text):
        tags.append("risk")
    if re.search(r'停損|stop.*loss|Stop.*Loss', text, re.IGNORECASE):
        tags.append("stop_loss")
    if re.search(r'進場|entry|Entry', text):
        tags.append("entry")
    if re.search(r'出場|exit|Exit', text):
        tags.append("exit")
    if re.search(r'部位|position|Position', text):
        tags.append("position_sizing")
    if re.search(r'盤中|intraday|Intraday', text):
        tags.append("intraday")
    
    return {
        "if": clean_markdown_annotations(if_match.group(1)) if if_match else "",
        "then": clean_markdown_annotations(then_match.group(1)) if then_match else "",
        "priority": priority,
        "scope": scope,
        "tags": list(set(tags)) if tags else []
    }


def extract_rules(source_dir: Path | None = None) -> List[Dict[str, Any]]:
    """Extract all RULE knowledge items from source files
    
    Args:
        source_dir: Directory containing source markdown files. If None, uses default.
    
    Returns:
        List of dictionaries representing RULE knowledge items
    """
    files = list_source_files(source_dir)
    id_gen = RuleIdGenerator()
    rules = []
    
    for file_path in files:
        source_doc = file_path.name
        
        # Iterate through blocks looking for RULE type
        for type_tag, block_lines, start_line in iter_blocks(file_path):
            if type_tag != "RULE":
                # Also check for rule-like content in other blocks
                block_text = ''.join(block_lines)
                if not (re.search(r'Rules_Entry|Rules_Exit|進場條件|出場條件|停損|規則|單筆最大虧損|單日最大虧損', block_text) or
                        re.search(r'必須|必須|則|那麼|if.*then', block_text, re.IGNORECASE)):
                    continue
            
            # Extract title
            title = extract_title_from_block(block_lines)
            if not title or title == "Untitled":
                # Try to generate from content
                for line in block_lines:
                    stripped = line.strip()
                    if stripped and len(stripped) > 5 and not stripped.startswith('['):
                        title = stripped[:80]
                        break
            
            # Clean raw text
            raw_text = ''.join(block_lines)
            cleaned_text = clean_markdown_annotations(raw_text)
            
            # Parse rule content
            parsed = parse_rule_content(block_lines)
            
            # Create rule item
            rule_item = {
                "id": id_gen.next_id(),
                "type": "RULE",
                "title": title[:100] if title else "Untitled Rule",
                "description": cleaned_text[:500] if cleaned_text else "",
                "tags": parsed.get("tags", []),
                "source_doc": source_doc,
                "source_location": f"line {start_line}",
                "raw_text": raw_text,
                "structured": {
                    "if": parsed.get("if", "") or cleaned_text[:200],
                    "then": parsed.get("then", "") or cleaned_text[:200],
                    "priority": parsed.get("priority", 3),
                    "scope": parsed.get("scope", "unknown")
                }
            }
            
            rules.append(rule_item)
    
    return rules


if __name__ == "__main__":
    # Test extraction
    rules = extract_rules()
    print(f"Extracted {len(rules)} rules")
    for rule in rules[:3]:
        print(f"- {rule['title']} (id: {rule['id']})")

