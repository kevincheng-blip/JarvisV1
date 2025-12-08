"""
Doctrine Review Loop v1

從 14 本聖經切 section，產生「AI 可加工」的 review JSONL。

功能：
- 分類 section 內容（偵測程式碼、算式、checklist）
- 提取 code blocks 和 formula lines
- 產生 review JSONL skeleton（不呼叫 LLM）
"""

from __future__ import annotations

import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from jgod.doctrine.doctrine_query_v1 import DoctrineQueryV1, DoctrineSection
from jgod.doctrine.doctrine_registry_v1 import DoctrineRegistryV1

logger = logging.getLogger(__name__)


def classify_section_content(section_text: str) -> Dict[str, Any]:
    """
    分類 section 內容，偵測程式碼、算式、checklist 等。
    
    Args:
        section_text: Section 的原始文字內容
    
    Returns:
        {
            "has_code": bool,
            "has_formula": bool,
            "has_checklist": bool,
            "knowledge_tags": List[str]
        }
    """
    text_lower = section_text.lower()
    text_lines = section_text.split('\n')
    
    # 1. 偵測程式碼 (has_code)
    has_code = False
    
    # 檢查 code block (```)
    if '```' in section_text:
        has_code = True
    
    # 檢查常見的程式語言標記
    code_patterns = [
        r'```python', r'```py', r'```javascript', r'```js',
        r'```typescript', r'```ts', r'```java', r'```cpp',
        r'```c\+\+', r'```c#', r'```go', r'```rust',
        r'```code', r'```', r'def\s+\w+\(', r'class\s+\w+',
        r'function\s+\w+\(', r'const\s+\w+\s*=', r'let\s+\w+\s*=',
        r'import\s+', r'from\s+', r'#\s*程式碼', r'#\s*CODE',
        r'程式碼', r'代碼', r'代碼區塊'
    ]
    
    for pattern in code_patterns:
        if re.search(pattern, section_text, re.IGNORECASE):
            has_code = True
            break
    
    # 檢查行首有 CODE, 程式碼, def, class
    for line in text_lines[:50]:  # 只檢查前 50 行
        stripped = line.strip()
        if any(keyword in stripped for keyword in ['CODE:', '程式碼:', 'def ', 'class ', 'function ']):
            has_code = True
            break
    
    # 2. 偵測算式 (has_formula)
    has_formula = False
    
    # 檢查 FORMULA, 公式 關鍵字
    formula_keywords = [
        'FORMULA', '公式', 'formula', '算式',
        'P(Loss)', 'Sharpe', 'VaR', 'MaxDD', 'Return',
        'Sharpe =', 'VaR =', 'MaxDD =', 'Return =',
        '收益率', '夏普', '最大回撤'
    ]
    
    for keyword in formula_keywords:
        if keyword in section_text:
            has_formula = True
            break
    
    # 檢查數學符號（大量出現）
    math_symbols = ['∑', 'Σ', '√', '^', '∫', '∂', '∇', '±', '×', '÷']
    math_symbol_count = sum(1 for sym in math_symbols if sym in section_text)
    if math_symbol_count >= 2:
        has_formula = True
    
    # 檢查等號與運算符號的組合（可能是公式）
    formula_patterns = [
        r'\w+\s*=\s*[^=]+[+\-*/%]',  # 變數 = 表達式
        r'\w+\s*=\s*\w+\s*/\s*\w+',  # 變數 = 變數 / 變數
        r'\w+\s*=\s*\w+\s*\*\s*\w+',  # 變數 = 變數 * 變數
        r'Sharpe\s*=', r'VaR\s*=', r'MaxDD\s*=', r'Return\s*=',
    ]
    
    for pattern in formula_patterns:
        if re.search(pattern, section_text, re.IGNORECASE):
            has_formula = True
            break
    
    # 3. 偵測 checklist (has_checklist)
    has_checklist = False
    
    checklist_keywords = ['檢查', 'Checklist', '步驟', '步驟一', '步驟二', '步驟三', 'todo', 'TODO']
    bullet_lines = 0
    
    for line in text_lines:
        stripped = line.strip()
        # 檢查是否以 - 或 * 開頭
        if stripped.startswith('-') or stripped.startswith('*') or stripped.startswith('•'):
            bullet_lines += 1
            # 檢查是否包含 checklist 關鍵字
            if any(keyword in stripped for keyword in checklist_keywords):
                has_checklist = True
                break
    
    # 如果有多行 bullet 且包含關鍵字，也視為 checklist
    if bullet_lines >= 3 and any(keyword in text_lower for keyword in checklist_keywords):
        has_checklist = True
    
    # 4. 產生 knowledge_tags
    knowledge_tags = []
    
    # 預設至少有 CONCEPT
    knowledge_tags.append("CONCEPT")
    
    # 規則相關
    if any(keyword in text_lower for keyword in ['規則', '原則', '心法', 'rule', 'principle']):
        knowledge_tags.append("RULE")
    
    # 風險規則
    if any(keyword in text_lower for keyword in ['不要', '避免', '風險', 'risk', '避免', '禁止']):
        knowledge_tags.append("RISK_RULE")
    
    # 公式
    if has_formula:
        knowledge_tags.append("FORMULA")
    
    # 程式碼
    if has_code:
        knowledge_tags.append("CODE_SNIPPET")
    
    # 故事/案例
    if any(keyword in text_lower for keyword in ['故事', '案例', '例子', 'story', 'case', 'example']):
        knowledge_tags.append("STORY")
    
    # 去重
    knowledge_tags = list(dict.fromkeys(knowledge_tags))  # 保持順序的去重
    
    return {
        "has_code": has_code,
        "has_formula": has_formula,
        "has_checklist": has_checklist,
        "knowledge_tags": knowledge_tags,
    }


def extract_code_blocks(section_text: str) -> List[str]:
    """
    提取所有 code 區塊的純文字。
    
    Args:
        section_text: Section 的原始文字內容
    
    Returns:
        List of code blocks (純文字，保留原始格式)
    """
    code_blocks = []
    
    # 方法 1: 提取 ``` 區塊
    code_block_pattern = r'```(?:python|py|javascript|js|typescript|ts|java|cpp|c\+\+|c#|go|rust|code|)?\n(.*?)```'
    matches = re.findall(code_block_pattern, section_text, re.DOTALL | re.IGNORECASE)
    code_blocks.extend([match.strip() for match in matches])
    
    # 方法 2: 提取沒有 ``` 但明顯是程式碼的行（連續的 def/class/import/function）
    lines = section_text.split('\n')
    current_block = []
    in_code_block = False
    
    for line in lines:
        stripped = line.strip()
        
        # 檢查是否為程式碼行
        is_code_line = (
            stripped.startswith('def ') or
            stripped.startswith('class ') or
            stripped.startswith('import ') or
            stripped.startswith('from ') or
            stripped.startswith('function ') or
            stripped.startswith('const ') or
            stripped.startswith('let ') or
            (stripped and not stripped.startswith('#') and '=' in stripped and any(op in stripped for op in ['(', '[', '{']))
        )
        
        if is_code_line:
            if not in_code_block:
                in_code_block = True
                current_block = []
            current_block.append(line)
        else:
            if in_code_block and current_block:
                # 結束當前 code block
                code_blocks.append('\n'.join(current_block).strip())
                current_block = []
            in_code_block = False
    
    # 處理最後一個 block
    if current_block:
        code_blocks.append('\n'.join(current_block).strip())
    
    # 去重並過濾空字串
    code_blocks = [cb for cb in code_blocks if cb and len(cb.strip()) > 10]  # 至少 10 字元
    code_blocks = list(dict.fromkeys(code_blocks))  # 去重
    
    return code_blocks


def extract_formula_lines(section_text: str) -> List[str]:
    """
    提取包含公式的行。
    
    Args:
        section_text: Section 的原始文字內容
    
    Returns:
        List of formula lines
    """
    formula_lines = []
    lines = section_text.split('\n')
    
    # 關鍵字模式
    formula_keywords = ['FORMULA', '公式', 'formula', '算式', 'Sharpe', 'VaR', 'MaxDD', 'Return', '收益率', '夏普', '最大回撤']
    
    # 數學符號
    math_symbols = ['∑', 'Σ', '√', '^', '∫', '∂', '∇', '±', '×', '÷']
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # 檢查是否包含公式關鍵字
        has_keyword = any(keyword in stripped for keyword in formula_keywords)
        
        # 檢查是否包含數學符號
        has_math_symbol = any(sym in stripped for sym in math_symbols)
        
        # 檢查是否為公式模式（變數 = 表達式）
        is_formula_pattern = bool(re.search(r'\w+\s*=\s*[^=]+[+\-*/%∑Σ√^]', stripped))
        
        # 檢查是否包含等號與運算符號
        has_equals_and_ops = '=' in stripped and any(op in stripped for op in ['+', '-', '*', '/', '%'])
        
        if has_keyword or has_math_symbol or is_formula_pattern or has_equals_and_ops:
            # 過濾掉明顯不是公式的行（例如註解）
            if not stripped.startswith('#') and not stripped.startswith('//') and not stripped.startswith('*'):
                formula_lines.append(stripped)
    
    # 去重
    formula_lines = list(dict.fromkeys(formula_lines))
    
    return formula_lines


class DoctrineReviewLoopV1:
    """Doctrine Review Loop v1
    
    從 14 本聖經切 section，分類內容，提取程式碼與算式，產生 review JSONL。
    """
    
    def __init__(self, output_dir: str = "data/doctrine_reviews"):
        """初始化 Review Loop
        
        Args:
            output_dir: 輸出目錄（review JSONL 檔案存放位置）
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.registry = DoctrineRegistryV1()
        self.query = DoctrineQueryV1()
    
    def list_sections(self, book_id: str) -> List[DoctrineSection]:
        """列出指定書籍的所有 sections
        
        Args:
            book_id: 書本 ID
        
        Returns:
            List of DoctrineSection
        """
        return self.query.list_sections(book_id)
    
    def build_review_record(
        self,
        book_id: str,
        section: DoctrineSection
    ) -> Dict[str, Any]:
        """
        建立單一 section 的 review record（skeleton）。
        
        不呼叫 AI，只產生結構化資料，留空 ai_* 欄位給 Cursor AI 填寫。
        
        Args:
            book_id: 書本 ID
            section: DoctrineSection 物件
        
        Returns:
            Review record dictionary
        """
        book_meta = self.registry.get_book_meta(book_id)
        if book_meta is None:
            raise ValueError(f"Book ID '{book_id}' not found")
        
        # 分類內容
        classification = classify_section_content(section.content)
        
        # 提取程式碼
        extracted_code = extract_code_blocks(section.content)
        
        # 提取公式
        extracted_formulas = extract_formula_lines(section.content)
        
        # 建立 record
        record = {
            "book_id": book_id,
            "book_title": book_meta.title,
            "section_id": section.section_id,
            "section_title": section.heading,
            "raw_text": section.content,
            "classification": classification,
            "extracted_code": extracted_code,
            "extracted_formulas": extracted_formulas,
            # AI 欄位（留空，給 Cursor AI 填寫）
            "ai_summary": "",
            "ai_core_principles": [],
            "ai_risk_rules": [],
            "ai_error_patterns": [],
            "ai_alpha_ideas": [],
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        
        return record
    
    def run_full_review(
        self,
        book_ids: Optional[List[str]] = None,
        output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        執行完整的 review 流程。
        
        Args:
            book_ids: 要處理的書本 ID 列表（None 表示處理所有 14 本）
            output_filename: 輸出檔名（None 表示自動生成）
        
        Returns:
            統計資訊字典
        """
        if book_ids is None:
            # 處理所有書籍
            books = self.registry.list_books()
            book_ids = [b.book_id for b in books]
        
        # 生成輸出檔名
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d")
            output_filename = f"review_{timestamp}.jsonl"
        
        output_path = self.output_dir / output_filename
        
        # 統計資訊
        stats = {
            "total_books": len(book_ids),
            "total_sections": 0,
            "sections_with_code": 0,
            "sections_with_formula": 0,
            "sections_with_checklist": 0,
            "total_code_blocks": 0,
            "total_formula_lines": 0,
        }
        
        # 處理所有書籍
        with open(output_path, 'w', encoding='utf-8') as f:
            for book_id in book_ids:
                book_meta = self.registry.get_book_meta(book_id)
                if book_meta is None:
                    logger.warning(f"Book ID '{book_id}' not found, skipping")
                    continue
                
                logger.info(f"Processing book: {book_meta.title} ({book_id})")
                
                try:
                    sections = self.list_sections(book_id)
                    logger.info(f"  Found {len(sections)} sections")
                    
                    for section in sections:
                        try:
                            record = self.build_review_record(book_id, section)
                            
                            # 更新統計
                            stats["total_sections"] += 1
                            if record["classification"]["has_code"]:
                                stats["sections_with_code"] += 1
                            if record["classification"]["has_formula"]:
                                stats["sections_with_formula"] += 1
                            if record["classification"]["has_checklist"]:
                                stats["sections_with_checklist"] += 1
                            stats["total_code_blocks"] += len(record["extracted_code"])
                            stats["total_formula_lines"] += len(record["extracted_formulas"])
                            
                            # 寫入 JSONL
                            f.write(json.dumps(record, ensure_ascii=False) + '\n')
                            
                        except Exception as e:
                            logger.error(f"Error processing section {section.section_id}: {e}", exc_info=True)
                            continue
                
                except Exception as e:
                    logger.error(f"Error processing book {book_id}: {e}", exc_info=True)
                    continue
        
        stats["output_file"] = str(output_path)
        logger.info(f"Review completed. Output: {output_path}")
        logger.info(f"Statistics: {stats}")
        
        return stats

