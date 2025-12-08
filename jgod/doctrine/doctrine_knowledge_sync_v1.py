"""
Doctrine Knowledge Sync v1

將已完成的 review JSONL（AI 已填好 ai_* 欄位）轉換成 KnowledgeBrain 格式的知識庫 JSONL。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DoctrineKnowledgeSyncV1:
    """Doctrine Knowledge Sync v1
    
    讀取 review JSONL，轉換成 KnowledgeBrain 格式的知識庫 JSONL。
    """
    
    def __init__(
        self,
        input_paths: List[str],
        output_path: str = "knowledge_base/jgod_doctrine_knowledge_v1.jsonl"
    ):
        """初始化 Knowledge Sync
        
        Args:
            input_paths: Review JSONL 檔案路徑列表
            output_path: 輸出知識庫 JSONL 檔案路徑
        """
        self.input_paths = [Path(p) for p in input_paths]
        self.output_path = Path(output_path)
        
        # 確保輸出目錄存在
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load_review_records(self) -> List[Dict[str, Any]]:
        """載入所有 review records
        
        Returns:
            List of review records
        """
        all_records = []
        
        for input_path in self.input_paths:
            if not input_path.exists():
                logger.warning(f"Review file not found: {input_path}, skipping")
                continue
            
            logger.info(f"Loading review file: {input_path}")
            
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            record = json.loads(line)
                            all_records.append(record)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON at line {line_num} in {input_path}: {e}")
                            continue
            
            except Exception as e:
                logger.error(f"Error reading {input_path}: {e}", exc_info=True)
                continue
        
        logger.info(f"Loaded {len(all_records)} review records")
        return all_records
    
    def convert_to_knowledge_entry(
        self,
        review_record: Dict[str, Any],
        entry_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        將單一 review record 轉換成 KnowledgeBrain 格式的 entry。
        
        Args:
            review_record: Review record dictionary
            entry_index: Entry 索引（用於生成唯一 ID）
        
        Returns:
            Knowledge entry dictionary 或 None（如果跳過）
        """
        book_id = review_record.get("book_id", "unknown")
        section_id = review_record.get("section_id", "unknown")
        section_title = review_record.get("section_title", "")
        classification = review_record.get("classification", {})
        knowledge_tags = classification.get("knowledge_tags", [])
        
        # 組合內容（優先使用 ai_summary，否則使用 section_title）
        content_parts = []
        
        ai_summary = review_record.get("ai_summary", "").strip()
        if ai_summary:
            content_parts.append(ai_summary)
        else:
            # 如果沒有 ai_summary，使用 section_title 作為 fallback
            if section_title:
                content_parts.append(section_title)
        
        # 組合 rules（來自 ai_core_principles 和 ai_risk_rules）
        rules = []
        ai_core_principles = review_record.get("ai_core_principles", [])
        ai_risk_rules = review_record.get("ai_risk_rules", [])
        rules.extend([r for r in ai_core_principles if r and r.strip()])
        rules.extend([r for r in ai_risk_rules if r and r.strip()])
        
        # 如果沒有 rules 但有 ai_summary，可以將 summary 當作單一 rule
        if not rules and ai_summary:
            rules.append(ai_summary)
        
        # 如果完全沒有內容，跳過這個 entry
        if not content_parts and not rules:
            return None
        
        # 組合完整內容
        full_content = "\n\n".join(content_parts) if content_parts else ""
        
        # 生成唯一 ID
        entry_id = f"doctrine_{book_id}_{section_id.replace('_', '-')}_entry_{entry_index:04d}"
        
        # 組合 tags（包含 DOCTRINE 和原始 knowledge_tags）
        tags = ["DOCTRINE"] + knowledge_tags
        
        # 如果有 ai_alpha_ideas，也加入 tags
        ai_alpha_ideas = review_record.get("ai_alpha_ideas", [])
        if ai_alpha_ideas:
            tags.append("ALPHA")
        
        # 如果有 ai_risk_rules，確保有 RISK tag
        if ai_risk_rules:
            if "RISK" not in tags:
                tags.append("RISK")
        
        # 去重 tags
        tags = list(dict.fromkeys(tags))
        
        # 建立 knowledge entry
        entry = {
            "id": entry_id,
            "type": "CONCEPT",  # 預設為 CONCEPT，可以根據 tags 調整
            "title": section_title or f"{book_id} Section",
            "description": full_content[:500] if full_content else "",  # 前 500 字元作為 description
            "tags": tags,
            "source_doc": f"doctrine_review_v1:{book_id}",
            "source_location": section_id,
            "raw_text": review_record.get("raw_text", ""),
            "structured": {
                "book_id": book_id,
                "book_title": review_record.get("book_title", ""),
                "section_id": section_id,
                "section_title": section_title,
                "rules": rules,
                "code_examples": review_record.get("extracted_code", []),
                "formulas": review_record.get("extracted_formulas", []),
                "ai_core_principles": ai_core_principles,
                "ai_risk_rules": ai_risk_rules,
                "ai_error_patterns": review_record.get("ai_error_patterns", []),
                "ai_alpha_ideas": ai_alpha_ideas,
                "classification": classification,
            },
            "created_at": review_record.get("created_at", datetime.utcnow().isoformat() + "Z"),
        }
        
        # 根據 tags 調整 type
        if "FORMULA" in tags:
            entry["type"] = "FORMULA"
        elif "RULE" in tags or "RISK_RULE" in tags:
            entry["type"] = "RULE"
        elif "CODE_SNIPPET" in tags:
            entry["type"] = "CODE"
        
        return entry
    
    def sync(self) -> Dict[str, Any]:
        """
        執行完整的 sync 流程。
        
        Returns:
            統計資訊字典
        """
        # 載入 review records
        review_records = self.load_review_records()
        
        if not review_records:
            logger.warning("No review records found, nothing to sync")
            return {
                "input_records": 0,
                "output_entries": 0,
                "entries_with_code": 0,
                "entries_with_formula": 0,
                "output_file": str(self.output_path),
            }
        
        # 轉換並寫入
        stats = {
            "input_records": len(review_records),
            "output_entries": 0,
            "entries_with_code": 0,
            "entries_with_formula": 0,
            "skipped_entries": 0,
        }
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            for idx, review_record in enumerate(review_records, 1):
                try:
                    entry = self.convert_to_knowledge_entry(review_record, idx)
                    
                    if entry is None:
                        stats["skipped_entries"] += 1
                        continue
                    
                    # 更新統計
                    stats["output_entries"] += 1
                    
                    structured = entry.get("structured", {})
                    if structured.get("code_examples"):
                        stats["entries_with_code"] += 1
                    if structured.get("formulas"):
                        stats["entries_with_formula"] += 1
                    
                    # 寫入 JSONL
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                    
                except Exception as e:
                    logger.error(f"Error converting record {idx}: {e}", exc_info=True)
                    stats["skipped_entries"] += 1
                    continue
        
        stats["output_file"] = str(self.output_path)
        logger.info(f"Sync completed. Output: {self.output_path}")
        logger.info(f"Statistics: {stats}")
        
        return stats

