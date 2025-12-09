#!/usr/bin/env python
"""
Fill AI fields in review JSONL

This script processes review JSONL file and fills in ai_* fields based on content.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def extract_key_points(text: str) -> List[str]:
    """Extract key points from text"""
    # Split by common separators
    points = []
    lines = text.split('\n')
    current_point = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_point:
                points.append(' '.join(current_point))
                current_point = []
            continue
        
        # Check for bullet points
        if line.startswith(('-', '*', '•', '1.', '2.', '3.', '4.', '5.')):
            if current_point:
                points.append(' '.join(current_point))
            current_point = [line.lstrip('-*•0123456789. ')]
        elif line.startswith('**') or line.startswith('#'):
            if current_point:
                points.append(' '.join(current_point))
            current_point = []
        else:
            current_point.append(line)
    
    if current_point:
        points.append(' '.join(current_point))
    
    return [p for p in points if len(p) > 10]  # Filter short points


def generate_ai_summary(record: Dict[str, Any]) -> str:
    """Generate ai_summary (3-6 sentences)"""
    raw_text = record.get('raw_text', '')
    section_title = record.get('section_title', '')
    classification = record.get('classification', {})
    has_code = classification.get('has_code', False)
    has_formula = classification.get('has_formula', False)
    extracted_code = record.get('extracted_code', [])
    extracted_formulas = record.get('extracted_formulas', [])
    
    # Skip if empty or just a title
    if len(raw_text.strip()) < 20 or raw_text.strip() == section_title:
        return "此段僅為標題或空白，無實質內容。"
    
    # Check for repetitive content
    if '重複' in raw_text or '說明' in raw_text[:50] and len(raw_text) < 100:
        return "此段為重覆說明／激勵文，無新增實質操作資訊。"
    
    sentences = []
    
    # First sentence: what this section teaches
    if section_title and section_title != "示例結構：" and not section_title.startswith('def ') and not section_title.startswith('#'):
        sentences.append(f"本段落說明「{section_title}」的相關概念與操作方法。")
    else:
        # Extract from first meaningful line
        first_line = raw_text.split('\n')[0].strip().lstrip('#').strip()
        if first_line and len(first_line) > 5:
            sentences.append(f"本段落介紹 {first_line[:50]}。")
        else:
            sentences.append("本段落說明 J-GOD 系統的相關操作原則。")
    
    # Code-related content
    if has_code and extracted_code:
        sentences.append("段落中包含程式碼範例，可用於實作策略判斷邏輯。")
    
    # Formula-related content
    if has_formula and extracted_formulas:
        sentences.append("段落中包含數學公式，用於計算風險調整後的報酬或評估指標。")
    
    # Extract key concepts (look for keywords)
    text_lower = raw_text.lower()
    if '規則' in text_lower or '原則' in text_lower:
        sentences.append("文中強調遵循特定規則與原則，確保交易策略的一致性。")
    if '風險' in text_lower or '止損' in text_lower or '停損' in text_lower:
        sentences.append("段落中提及風險控制的重要性，強調設定停損點的必要性。")
    if '策略' in text_lower:
        sentences.append("內容涉及策略設計與執行要點，提供實務操作指引。")
    
    # Limit to 3-6 sentences
    if len(sentences) > 6:
        sentences = sentences[:6]
    elif len(sentences) < 3:
        # Add generic sentence if too short
        sentences.append("此內容為 J-GOD 系統的核心操作指南。")
    
    return ' '.join(sentences)


def generate_ai_core_principles(record: Dict[str, Any]) -> List[str]:
    """Generate ai_core_principles"""
    raw_text = record.get('raw_text', '')
    classification = record.get('classification', {})
    extracted_code = record.get('extracted_code', [])
    extracted_formulas = record.get('extracted_formulas', [])
    
    principles = []
    
    # Extract rules and principles from text
    text_lower = raw_text.lower()
    
    # Look for explicit rules
    rule_patterns = [
        r'必須[^。]+',
        r'應該[^。]+',
        r'原則[：:][^。]+',
        r'規則[：:][^。]+',
        r'要[^。]+',
        r'不要[^。]+',
    ]
    
    for pattern in rule_patterns:
        matches = re.findall(pattern, raw_text)
        for match in matches[:3]:  # Limit to 3 matches per pattern
            cleaned = match.strip().lstrip('：:').strip()
            if len(cleaned) > 10 and len(cleaned) < 200:
                principles.append(cleaned)
    
    # Code-related principles
    if extracted_code:
        principles.append("程式碼應清楚表達策略邏輯，確保條件判斷的可執行性。")
    
    # Formula-related principles
    if extracted_formulas:
        principles.append("使用公式計算風險與報酬指標，作為決策依據。")
    
    # Check for specific keywords
    if '條件' in text_lower:
        principles.append("進場需滿足所有必要條件，避免衝動交易。")
    if '停損' in text_lower or '止損' in text_lower:
        principles.append("每筆交易必須設定停損點，嚴格執行風險控制。")
    if '觀察' in text_lower or '監控' in text_lower:
        principles.append("持續觀察市場變化，及時調整策略參數。")
    
    # Remove duplicates and limit
    seen = set()
    unique_principles = []
    for p in principles:
        if p not in seen and len(p) > 10:
            seen.add(p)
            unique_principles.append(p)
    
    return unique_principles[:5] if unique_principles else []


def generate_ai_risk_rules(record: Dict[str, Any]) -> List[str]:
    """Generate ai_risk_rules"""
    raw_text = record.get('raw_text', '')
    classification = record.get('classification', {})
    
    risk_rules = []
    text_lower = raw_text.lower()
    
    # Check if content is risk-related
    risk_keywords = ['風險', '止損', '停損', '槓桿', '槓杆', '錯誤', '警告', '避免', '禁止']
    if not any(kw in text_lower for kw in risk_keywords):
        return []
    
    # Extract risk-related sentences
    risk_patterns = [
        r'[^。]*風險[^。]*',
        r'[^。]*止損[^。]*',
        r'[^。]*停損[^。]*',
        r'[^。]*不要[^。]*',
        r'[^。]*避免[^。]*',
        r'[^。]*禁止[^。]*',
    ]
    
    for pattern in risk_patterns:
        matches = re.findall(pattern, raw_text)
        for match in matches[:2]:  # Limit to 2 per pattern
            cleaned = match.strip()
            if len(cleaned) > 10 and len(cleaned) < 200:
                risk_rules.append(cleaned)
    
    # Specific risk rules based on content
    if '2%' in raw_text or '百分之二' in raw_text:
        risk_rules.append("單筆交易最大虧損不得超過總資金的 2%。")
    if '槓桿' in text_lower or '槓杆' in text_lower:
        risk_rules.append("謹慎使用槓桿，避免過度槓桿導致重大虧損。")
    if '停損' in text_lower or '止損' in text_lower:
        risk_rules.append("每筆交易必須設定停損點，並嚴格執行。")
    
    # Remove duplicates
    seen = set()
    unique_rules = []
    for r in risk_rules:
        if r not in seen:
            seen.add(r)
            unique_rules.append(r)
    
    return unique_rules[:5] if unique_rules else []


def generate_ai_error_patterns(record: Dict[str, Any]) -> List[str]:
    """Generate ai_error_patterns"""
    raw_text = record.get('raw_text', '')
    text_lower = raw_text.lower()
    
    error_patterns = []
    
    # Check for error-related content
    error_keywords = ['錯誤', '陷阱', '弱點', '常犯', '失敗', '虧損', '損失']
    if not any(kw in text_lower for kw in error_keywords):
        return []
    
    # Extract error patterns
    error_patterns_text = [
        r'[^。]*錯誤[^。]*',
        r'[^。]*陷阱[^。]*',
        r'[^。]*弱點[^。]*',
        r'[^。]*常犯[^。]*',
    ]
    
    for pattern in error_patterns_text:
        matches = re.findall(pattern, raw_text)
        for match in matches[:2]:
            cleaned = match.strip()
            if len(cleaned) > 10 and len(cleaned) < 200:
                error_patterns.append(cleaned)
    
    return error_patterns[:3] if error_patterns else []


def generate_ai_alpha_ideas(record: Dict[str, Any]) -> List[str]:
    """Generate ai_alpha_ideas"""
    raw_text = record.get('raw_text', '')
    classification = record.get('classification', {})
    extracted_formulas = record.get('extracted_formulas', [])
    
    alpha_ideas = []
    text_lower = raw_text.lower()
    
    # Check for alpha-related content
    alpha_keywords = ['賺', 'edge', 'alpha', '優勢', '利潤', '報酬', '收益', '獲利']
    if not any(kw in text_lower for kw in alpha_keywords):
        return []
    
    # Extract alpha ideas
    if '公式' in text_lower or extracted_formulas:
        alpha_ideas.append("使用量化公式計算風險調整後的報酬，找出具有統計優勢的策略。")
    
    if '策略' in text_lower and ('設計' in text_lower or '建立' in text_lower):
        alpha_ideas.append("透過系統化策略設計，捕捉市場中的規律性機會。")
    
    if '觀察' in text_lower or '監控' in text_lower:
        alpha_ideas.append("持續觀察市場變化與指標，及時發現交易機會。")
    
    return alpha_ideas[:3] if alpha_ideas else []


def generate_ai_checklist(record: Dict[str, Any]) -> List[str]:
    """Generate ai_checklist"""
    raw_text = record.get('raw_text', '')
    classification = record.get('classification', {})
    
    checklist = []
    
    # Check if content has checklist-like structure
    if not classification.get('has_checklist', False):
        # Look for step-by-step or action items
        text_lower = raw_text.lower()
        if '步驟' not in text_lower and '檢查' not in text_lower:
            return []
    
    # Extract checklist items
    lines = raw_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for checklist markers
        if (line.startswith(('-', '*', '•', '1.', '2.', '3.', '4.', '5.')) or 
            '檢查' in line or '確認' in line or '核對' in line):
            cleaned = line.lstrip('-*•0123456789. ').strip()
            if len(cleaned) > 5 and len(cleaned) < 200:
                checklist.append(cleaned)
    
    return checklist[:8] if checklist else []


def process_review_file(input_path: str, output_path: str) -> Dict[str, int]:
    """Process review JSONL file and fill ai_* fields"""
    stats = {
        'total_records': 0,
        'processed': 0,
        'skipped': 0,
        'ai_summary_filled': 0,
        'ai_core_principles_filled': 0,
        'ai_risk_rules_filled': 0,
        'ai_error_patterns_filled': 0,
        'ai_alpha_ideas_filled': 0,
        'ai_checklist_filled': 0,
    }
    
    records = []
    
    # Read all records
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                records.append(record)
                stats['total_records'] += 1
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON at line {line_num}: {e}")
                continue
    
    # Process each record
    for record in records:
        modified = False
        
        # Fill ai_summary if empty
        if not record.get('ai_summary', '').strip():
            record['ai_summary'] = generate_ai_summary(record)
            if record['ai_summary']:
                stats['ai_summary_filled'] += 1
                modified = True
        
        # Fill ai_core_principles if empty
        if not record.get('ai_core_principles', []):
            principles = generate_ai_core_principles(record)
            if principles:
                record['ai_core_principles'] = principles
                stats['ai_core_principles_filled'] += 1
                modified = True
        
        # Fill ai_risk_rules if empty
        if not record.get('ai_risk_rules', []):
            risk_rules = generate_ai_risk_rules(record)
            record['ai_risk_rules'] = risk_rules  # Can be empty list
            if risk_rules:
                stats['ai_risk_rules_filled'] += 1
                modified = True
        
        # Fill ai_error_patterns if empty
        if not record.get('ai_error_patterns', []):
            error_patterns = generate_ai_error_patterns(record)
            record['ai_error_patterns'] = error_patterns  # Can be empty list
            if error_patterns:
                stats['ai_error_patterns_filled'] += 1
                modified = True
        
        # Fill ai_alpha_ideas if empty
        if not record.get('ai_alpha_ideas', []):
            alpha_ideas = generate_ai_alpha_ideas(record)
            record['ai_alpha_ideas'] = alpha_ideas  # Can be empty list
            if alpha_ideas:
                stats['ai_alpha_ideas_filled'] += 1
                modified = True
        
        # Fill ai_checklist if field doesn't exist or is empty
        if 'ai_checklist' not in record or not record.get('ai_checklist', []):
            checklist = generate_ai_checklist(record)
            record['ai_checklist'] = checklist  # Can be empty list
            if checklist:
                stats['ai_checklist_filled'] += 1
                modified = True
        
        if modified:
            stats['processed'] += 1
        else:
            stats['skipped'] += 1
    
    # Write back
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in records:
            # Ensure JSON is valid (use ensure_ascii=False for Chinese)
            json_line = json.dumps(record, ensure_ascii=False)
            f.write(json_line + '\n')
    
    return stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fill AI fields in review JSONL')
    parser.add_argument('input', help='Input review JSONL file')
    parser.add_argument('-o', '--output', help='Output file (default: overwrite input)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return 1
    
    output_path = Path(args.output) if args.output else input_path
    
    print(f"Processing {input_path}...")
    stats = process_review_file(str(input_path), str(output_path))
    
    print("\n" + "=" * 80)
    print("Processing Statistics")
    print("=" * 80)
    print(f"Total records: {stats['total_records']}")
    print(f"Processed: {stats['processed']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"\nFields filled:")
    print(f"  ai_summary: {stats['ai_summary_filled']}")
    print(f"  ai_core_principles: {stats['ai_core_principles_filled']}")
    print(f"  ai_risk_rules: {stats['ai_risk_rules_filled']}")
    print(f"  ai_error_patterns: {stats['ai_error_patterns_filled']}")
    print(f"  ai_alpha_ideas: {stats['ai_alpha_ideas_filled']}")
    print(f"  ai_checklist: {stats['ai_checklist_filled']}")
    print(f"\nOutput: {output_path}")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

