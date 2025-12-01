"""Error Learning Engine for J-GOD

This module provides the ErrorLearningEngine class that analyzes prediction errors
by querying the Knowledge Brain and classifying root causes.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from jgod.learning.error_event import (
    ErrorEvent,
    ErrorAnalysisResult,
    CLASS_UTILIZATION_GAP,
    CLASS_FORM_INSUFFICIENT,
    CLASS_KNOWLEDGE_GAP,
    CLASS_UNKNOWN
)
from jgod.war_room.knowledge_gateway import get_knowledge_brain
from jgod.knowledge.knowledge_brain import KnowledgeItem


class ErrorLearningEngine:
    """Error learning engine for J-GOD
    
    Analyzes prediction errors by querying the Knowledge Brain and classifying
    the root cause into one of three categories:
    - Utilization Gap: Rules exist but weren't used
    - Form Insufficient: Only concepts exist, no executable rules
    - Knowledge Gap: No relevant knowledge exists
    
    Example:
        engine = ErrorLearningEngine()
        analysis = engine.analyze_error(error_event)
        report_path = engine.save_report(error_event, analysis)
    """
    
    def __init__(
        self,
        *,
        draft_output_path: Path | str | None = None,
        report_output_dir: Path | str | None = None,
    ) -> None:
        """Initialize ErrorLearningEngine
        
        Args:
            draft_output_path: Path to draft knowledge items JSONL file.
                              Default: knowledge_base/jgod_knowledge_drafts.jsonl
            report_output_dir: Directory for error analysis reports.
                              Default: error_logs/reports/
        """
        project_root = Path(__file__).parent.parent.parent
        
        if draft_output_path is None:
            draft_output_path = project_root / "knowledge_base" / "jgod_knowledge_drafts.jsonl"
        self.draft_output_path = Path(draft_output_path)
        self.draft_output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if report_output_dir is None:
            report_output_dir = project_root / "error_logs" / "reports"
        self.report_output_dir = Path(report_output_dir)
        self.report_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize knowledge brain (lazy load)
        self._knowledge_brain = None
    
    @property
    def knowledge_brain(self):
        """Get or create KnowledgeBrain instance (lazy loading)"""
        if self._knowledge_brain is None:
            self._knowledge_brain = get_knowledge_brain()
        return self._knowledge_brain
    
    def analyze_error(self, event: ErrorEvent) -> ErrorAnalysisResult:
        """Analyze an error event and classify its root cause
        
        Main workflow:
        1. Build query string from ErrorEvent
        2. Search KnowledgeBrain for related rules, concepts, structures, formulas
        3. Classify the error based on search results:
           - UTILIZATION_GAP: Rules exist but weren't used
           - FORM_INSUFFICIENT: Only concepts exist, no executable rules
           - KNOWLEDGE_GAP: No relevant knowledge found
           - UNKNOWN: Other cases
        4. Return ErrorAnalysisResult
        
        Args:
            event: ErrorEvent to analyze
        
        Returns:
            ErrorAnalysisResult containing analysis and classification
        """
        # Build query
        query = self._build_query_from_event(event)
        
        # Search KnowledgeBrain
        all_rules = self.knowledge_brain.get_rules()
        all_concepts = self.knowledge_brain.search(type="CONCEPT", query=query, limit=20)
        all_structures = self.knowledge_brain.search(type="STRUCTURE", query=query, limit=10)
        all_formulas = self.knowledge_brain.get_formulas()
        
        # Also do general search
        general_search = self.knowledge_brain.search(query=query, limit=30)
        
        # Filter relevant items with stricter relevance check
        relevant_rules = [r for r in all_rules if self._is_relevant(r, event, query)]
        relevant_concepts = [c for c in all_concepts if self._is_relevant(c, event, query)]
        relevant_structures = [s for s in all_structures if self._is_relevant(s, event, query)]
        relevant_formulas = [f for f in all_formulas if self._is_relevant(f, event, query)]
        
        # Count items by type
        rule_count = len(relevant_rules)
        concept_count = len(relevant_concepts)
        structure_count = len(relevant_structures)
        formula_count = len(relevant_formulas)
        note_count = len([i for i in general_search if i.type == "NOTE" and self._is_relevant(i, event, query)])
        total_count = rule_count + concept_count + structure_count + formula_count + note_count
        
        # Check for unused rules (rules found but not in event.used_rules)
        unused_rules = [
            r for r in relevant_rules
            if r.id not in event.used_rules
        ]
        
        # Initialize classification variables
        classification = CLASS_UNKNOWN
        utilization_gap_reasons = []
        knowledge_gap_notes = []
        draft_rule_suggestions = []
        draft_concept_suggestions = []
        follow_up_actions = []
        
        # ============================================================
        # Classification Logic (Priority Order: KNOWLEDGE_GAP > FORM_INSUFFICIENT > UTILIZATION_GAP > UNKNOWN)
        # ============================================================
        
        # 1️⃣ KNOWLEDGE_GAP (Highest Priority)
        # Condition: Very few or no relevant items found
        if (total_count == 0 or 
            (total_count <= 3 and rule_count == 0 and formula_count == 0 and concept_count <= 1)):
            classification = CLASS_KNOWLEDGE_GAP
            knowledge_gap_notes.append(
                f"知識庫中未找到與此錯誤相關的規則、概念或公式"
            )
            if total_count == 0:
                knowledge_gap_notes.append("完全找不到相關知識項目")
            else:
                knowledge_gap_notes.append(
                    f"僅找到 {total_count} 個弱相關項目（規則: {rule_count}, 概念: {concept_count}, 公式: {formula_count}）"
                )
            knowledge_gap_notes.append(
                f"錯誤類型：{event.error_type or '未知'}，標籤：{', '.join(event.tags or [])}"
            )
            
            # Generate draft suggestions
            draft_rule_suggestions.append(
                self._generate_gap_rule_draft(event)
            )
            draft_concept_suggestions.append(
                self._generate_gap_concept_draft(event)
            )
            
            follow_up_actions.append("新增相關規則到知識庫")
            follow_up_actions.append("補充相關概念定義")
        
        # 2️⃣ FORM_INSUFFICIENT (Second Priority)
        # Condition: Has concepts/notes/structures but NO rules or formulas
        elif (rule_count == 0 and formula_count == 0 and concept_count > 0):
            classification = CLASS_FORM_INSUFFICIENT
            knowledge_gap_notes.append(
                f"找到 {concept_count} 個相關概念，但無可執行的規則或公式"
            )
            if structure_count > 0:
                knowledge_gap_notes.append(f"找到 {structure_count} 個相關結構")
            if note_count > 0:
                knowledge_gap_notes.append(f"找到 {note_count} 個相關備註")
            
            # Generate draft rule suggestions from concepts
            for concept in relevant_concepts[:3]:
                draft_rule_suggestion = self._generate_rule_draft_from_concept(concept, event)
                if draft_rule_suggestion:
                    draft_rule_suggestions.append(draft_rule_suggestion)
            
            follow_up_actions.append("將概念轉化為可執行的規則")
            follow_up_actions.append("定義明確的觸發條件與行動")
        
        # 3️⃣ UTILIZATION_GAP (Third Priority)
        # Condition: Has rules that exist but weren't used, AND they are highly relevant
        elif (rule_count > 0 and len(unused_rules) > 0):
            # Additional check: unused rules should be highly relevant
            highly_relevant_unused = [
                r for r in unused_rules
                if self._is_highly_relevant(r, event, query)
            ]
            
            # Only classify as UTILIZATION_GAP if we have highly relevant unused rules
            if len(highly_relevant_unused) > 0:
                classification = CLASS_UTILIZATION_GAP
                for rule in highly_relevant_unused[:5]:  # Limit to top 5
                    utilization_gap_reasons.append(
                        f"規則 {rule.id} ({rule.title}) 存在但未被使用"
                    )
                follow_up_actions.append(
                    f"檢查為何 {len(highly_relevant_unused)} 條相關規則未被觸發"
                )
                follow_up_actions.append("檢視規則觸發條件是否過於嚴格")
                follow_up_actions.append("檢查規則優先級設定")
            else:
                # Rules exist but not highly relevant - might be FORM_INSUFFICIENT or UNKNOWN
                if concept_count > 0:
                    classification = CLASS_FORM_INSUFFICIENT
                    knowledge_gap_notes.append(
                        f"找到 {rule_count} 條弱相關規則和 {concept_count} 個概念，但缺乏高度相關的可執行規則"
                    )
                else:
                    classification = CLASS_UNKNOWN
                    knowledge_gap_notes.append("找到規則但相關度不足，分類不明確")
        
        # 4️⃣ UNKNOWN (Fallback)
        else:
            classification = CLASS_UNKNOWN
            knowledge_gap_notes.append("找到部分相關知識，但分類不明確")
            if rule_count > 0:
                knowledge_gap_notes.append(f"找到 {rule_count} 條規則（已使用或相關度不足）")
            if concept_count > 0:
                knowledge_gap_notes.append(f"找到 {concept_count} 個概念")
            if formula_count > 0:
                knowledge_gap_notes.append(f"找到 {formula_count} 個公式")
        
        # Summarize related items
        all_related = relevant_rules + relevant_concepts + relevant_structures + relevant_formulas
        related_items = self._summarize_items(all_related, limit=20)
        
        # Create analysis result
        analysis = ErrorAnalysisResult(
            event_id=event.id,
            classification=classification,
            related_items=related_items,
            utilization_gap_reasons=utilization_gap_reasons,
            knowledge_gap_notes=knowledge_gap_notes,
            draft_rule_suggestions=draft_rule_suggestions,
            draft_concept_suggestions=draft_concept_suggestions,
            follow_up_actions=follow_up_actions,
            raw_query=query,
            created_at=datetime.now()
        )
        
        return analysis
    
    def _build_query_from_event(self, event: ErrorEvent) -> str:
        """Build search query string from ErrorEvent
        
        Combines tags, error_type, symbol, and notes into a natural language query.
        
        Args:
            event: ErrorEvent to build query from
        
        Returns:
            Query string for KnowledgeBrain search
        """
        query_parts = []
        
        # Add error type
        if event.error_type:
            query_parts.append(event.error_type)
        
        # Add tags
        if event.tags:
            query_parts.extend(event.tags)
        
        # Add symbol context
        if event.symbol:
            query_parts.append(f"symbol {event.symbol}")
        
        # Add timeframe
        if event.timeframe:
            query_parts.append(f"timeframe {event.timeframe}")
        
        # Add predicted vs actual outcome
        if event.predicted_outcome and event.actual_outcome:
            query_parts.append(f"{event.predicted_outcome} vs {event.actual_outcome}")
        
        # Add notes if available
        if event.notes:
            # Extract key terms from notes
            note_words = event.notes.split()[:10]  # Limit to first 10 words
            query_parts.extend(note_words)
        
        query = " ".join(query_parts)
        
        # If query is empty, use a default
        if not query.strip():
            query = "prediction error trading mistake"
        
        return query.strip()
    
    def _is_relevant(self, item: KnowledgeItem, event: ErrorEvent, query: str) -> bool:
        """Check if a KnowledgeItem is relevant to the error event
        
        Basic relevance check - used for filtering initial candidate items.
        
        Args:
            item: KnowledgeItem to check
            event: ErrorEvent being analyzed
            query: Search query string
        
        Returns:
            True if item is relevant, False otherwise
        """
        # Check tags overlap
        if event.tags and item.tags:
            if set(event.tags) & set(item.tags):
                return True
        
        # Check query keywords in item content
        query_lower = query.lower()
        item_text = f"{item.title} {item.description} {item.raw_text}".lower()
        
        # Simple keyword matching
        query_words = [w for w in query_lower.split() if len(w) > 2]
        matches = sum(1 for word in query_words if word in item_text)
        
        return matches >= 1  # At least one keyword match
    
    def _is_highly_relevant(self, item: KnowledgeItem, event: ErrorEvent, query: str) -> bool:
        """Check if a KnowledgeItem is highly relevant to the error event
        
        Stricter relevance check - used for UTILIZATION_GAP classification.
        Requires stronger matching criteria.
        
        Args:
            item: KnowledgeItem to check
            event: ErrorEvent being analyzed
            query: Search query string
        
        Returns:
            True if item is highly relevant, False otherwise
        """
        relevance_score = 0
        
        # Strong tag overlap (2 points)
        if event.tags and item.tags:
            tag_overlap = set(t.lower() for t in event.tags) & set(t.lower() for t in item.tags)
            if tag_overlap:
                relevance_score += 2
        
        # Error type in item content (2 points)
        if event.error_type:
            item_text = f"{item.title} {item.description} {item.raw_text}".lower()
            if event.error_type.lower() in item_text:
                relevance_score += 2
        
        # Multiple keyword matches (1 point per match, max 3)
        query_lower = query.lower()
        item_text = f"{item.title} {item.description} {item.raw_text}".lower()
        query_words = [w for w in query_lower.split() if len(w) > 2]
        keyword_matches = sum(1 for word in query_words if word in item_text)
        relevance_score += min(keyword_matches, 3)
        
        # Notes contain item keywords (1 point)
        if event.notes:
            notes_lower = event.notes.lower()
            item_keywords = item.title.lower().split()[:3]  # First 3 words of title
            if any(kw in notes_lower for kw in item_keywords if len(kw) > 2):
                relevance_score += 1
        
        # Highly relevant if score >= 3
        return relevance_score >= 3
    
    def _summarize_items(self, items: List[KnowledgeItem], limit: int = 10) -> List[Dict[str, Any]]:
        """Summarize KnowledgeItems into simplified dictionaries
        
        Args:
            items: List of KnowledgeItems to summarize
            limit: Maximum number of items to include
        
        Returns:
            List of simplified dictionaries with id/type/title/tags
        """
        summarized = []
        for item in items[:limit]:
            summarized.append({
                "id": item.id,
                "type": item.type,
                "title": item.title[:100],
                "tags": item.tags[:10],  # Limit tags
                "source_doc": item.source_doc
            })
        return summarized
    
    def _generate_rule_draft_from_concept(self, concept: KnowledgeItem, event: ErrorEvent) -> str:
        """Generate a draft rule suggestion from a concept
        
        Args:
            concept: Concept KnowledgeItem
            event: ErrorEvent context
        
        Returns:
            Draft rule suggestion string
        """
        concept_name = concept.structured.get("name", concept.title) if concept.structured else concept.title
        concept_def = concept.structured.get("definition", concept.description) if concept.structured else concept.description
        
        draft = f"規則草案：基於「{concept_name}」概念\n"
        draft += f"如果：{event.error_type or '相關條件'}發生\n"
        draft += f"則：參考「{concept_name}」的定義（{concept_def[:100]}...）\n"
        draft += f"來源概念：{concept.id}"
        
        return draft
    
    def _generate_gap_rule_draft(self, event: ErrorEvent) -> str:
        """Generate a draft rule suggestion for knowledge gap
        
        Args:
            event: ErrorEvent that revealed the gap
        
        Returns:
            Draft rule suggestion string
        """
        draft = f"規則草案：處理「{event.error_type or '未知錯誤'}」情境\n"
        draft += f"如果：{event.predicted_outcome} 預測但實際 {event.actual_outcome}\n"
        draft += f"則：需要定義明確的處理規則\n"
        if event.tags:
            draft += f"相關標籤：{', '.join(event.tags)}\n"
        if event.notes:
            draft += f"情境說明：{event.notes[:200]}"
        
        return draft
    
    def _generate_gap_concept_draft(self, event: ErrorEvent) -> str:
        """Generate a draft concept suggestion for knowledge gap
        
        Args:
            event: ErrorEvent that revealed the gap
        
        Returns:
            Draft concept suggestion string
        """
        draft = f"概念草案：{event.error_type or '錯誤情境'}相關概念\n"
        draft += f"定義：需要補充「{event.predicted_outcome} vs {event.actual_outcome}」情境的概念說明\n"
        if event.tags:
            draft += f"相關分類：{', '.join(event.tags)}\n"
        if event.notes:
            draft += f"範例情境：{event.notes[:200]}"
        
        return draft
    
    def save_drafts(self, analysis: ErrorAnalysisResult) -> None:
        """Save draft suggestions to JSONL file
        
        If analysis contains draft_rule_suggestions or draft_concept_suggestions,
        append them to the draft knowledge items file.
        
        Args:
            analysis: ErrorAnalysisResult containing draft suggestions
        """
        if not (analysis.draft_rule_suggestions or analysis.draft_concept_suggestions):
            return
        
        drafts = []
        
        # Create draft entries
        for i, rule_draft in enumerate(analysis.draft_rule_suggestions):
            draft_item = {
                "id": f"DRAFT_RULE_{analysis.event_id}_{i}",
                "type": "RULE",
                "title": f"規則草案 - {analysis.event_id}",
                "description": rule_draft,
                "tags": ["draft", "suggested"],
                "source_doc": "error_learning_engine",
                "source_location": f"error_event:{analysis.event_id}",
                "raw_text": rule_draft,
                "structured": {
                    "if": "待定義",
                    "then": "待定義",
                    "priority": 1,
                    "scope": "unknown"
                },
                "metadata": {
                    "event_id": analysis.event_id,
                    "classification": analysis.classification,
                    "created_at": analysis.created_at.isoformat() if isinstance(analysis.created_at, datetime) else str(analysis.created_at),
                    "query": analysis.raw_query
                }
            }
            drafts.append(draft_item)
        
        for i, concept_draft in enumerate(analysis.draft_concept_suggestions):
            draft_item = {
                "id": f"DRAFT_CONCEPT_{analysis.event_id}_{i}",
                "type": "CONCEPT",
                "title": f"概念草案 - {analysis.event_id}",
                "description": concept_draft,
                "tags": ["draft", "suggested"],
                "source_doc": "error_learning_engine",
                "source_location": f"error_event:{analysis.event_id}",
                "raw_text": concept_draft,
                "structured": {
                    "name": f"Draft Concept {analysis.event_id}",
                    "definition": concept_draft,
                    "examples": []
                },
                "metadata": {
                    "event_id": analysis.event_id,
                    "classification": analysis.classification,
                    "created_at": analysis.created_at.isoformat() if isinstance(analysis.created_at, datetime) else str(analysis.created_at),
                    "query": analysis.raw_query
                }
            }
            drafts.append(draft_item)
        
        # Append to JSONL file
        with open(self.draft_output_path, 'a', encoding='utf-8') as f:
            for draft in drafts:
                json_line = json.dumps(draft, ensure_ascii=False)
                f.write(json_line + '\n')
    
    def save_report(self, event: ErrorEvent, analysis: ErrorAnalysisResult) -> Path:
        """Save error analysis report to file
        
        Generates a human-readable error analysis report in Markdown format.
        
        Args:
            event: ErrorEvent that was analyzed
            analysis: ErrorAnalysisResult from analysis
        
        Returns:
            Path to the generated report file
        """
        # Generate filename
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp_str}_{event.id}.md"
        report_path = self.report_output_dir / filename
        
        # Generate report content
        report_lines = []
        report_lines.append("# J-GOD 錯誤分析報告\n")
        report_lines.append(f"**事件 ID**: {event.id}\n")
        report_lines.append(f"**分析時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        report_lines.append("---\n\n")
        report_lines.append("## 1. 錯誤基本資訊\n\n")
        report_lines.append(f"- **標的**: {event.symbol}\n")
        report_lines.append(f"- **時間框架**: {event.timeframe}\n")
        report_lines.append(f"- **方向**: {event.side or 'N/A'}\n")
        report_lines.append(f"- **預測結果**: {event.predicted_outcome}\n")
        report_lines.append(f"- **實際結果**: {event.actual_outcome}\n")
        if event.pnl is not None:
            report_lines.append(f"- **損益**: {event.pnl:.2f}\n")
        report_lines.append(f"- **錯誤類型**: {event.error_type or '未知'}\n")
        if event.tags:
            report_lines.append(f"- **標籤**: {', '.join(event.tags)}\n")
        if event.notes:
            report_lines.append(f"\n**備註**: {event.notes}\n")
        
        report_lines.append("\n---\n\n")
        report_lines.append("## 2. 分類結果\n\n")
        report_lines.append(f"**分類**: `{analysis.classification}`\n\n")
        
        classification_desc = {
            CLASS_UTILIZATION_GAP: "運用落差：知識庫中已有相關規則，但未被使用",
            CLASS_FORM_INSUFFICIENT: "形式不足：僅有概念定義，缺乏可執行的規則",
            CLASS_KNOWLEDGE_GAP: "知識缺口：知識庫中未找到相關知識",
            CLASS_UNKNOWN: "未知：無法明確分類"
        }
        report_lines.append(f"**說明**: {classification_desc.get(analysis.classification, '未知分類')}\n\n")
        
        report_lines.append("\n---\n\n")
        report_lines.append("## 3. 相關知識項目\n\n")
        
        if analysis.related_items:
            # Group by type
            by_type = {}
            for item in analysis.related_items:
                item_type = item.get("type", "UNKNOWN")
                if item_type not in by_type:
                    by_type[item_type] = []
                by_type[item_type].append(item)
            
            for item_type in ["RULE", "CONCEPT", "FORMULA", "STRUCTURE", "TABLE", "CODE"]:
                if item_type in by_type:
                    report_lines.append(f"### {item_type}\n\n")
                    for item in by_type[item_type]:
                        report_lines.append(f"- **{item['title']}** (ID: {item['id']})\n")
                        if item.get('tags'):
                            report_lines.append(f"  - 標籤: {', '.join(item['tags'][:5])}\n")
                    report_lines.append("\n")
        else:
            report_lines.append("未找到相關知識項目\n\n")
        
        report_lines.append("\n---\n\n")
        report_lines.append("## 4. 系統判斷\n\n")
        
        if analysis.classification == CLASS_UTILIZATION_GAP:
            report_lines.append("### 運用落差分析\n\n")
            for reason in analysis.utilization_gap_reasons:
                report_lines.append(f"- {reason}\n")
            report_lines.append("\n**問題**: 明明存在但未使用的規則\n\n")
        
        elif analysis.classification == CLASS_FORM_INSUFFICIENT:
            report_lines.append("### 形式不足分析\n\n")
            report_lines.append("知識庫中僅有概念定義，但缺乏可執行的規則。\n\n")
            report_lines.append("**建議**: 將概念轉化為明確的規則\n\n")
        
        elif analysis.classification == CLASS_KNOWLEDGE_GAP:
            report_lines.append("### 知識缺口分析\n\n")
            for note in analysis.knowledge_gap_notes:
                report_lines.append(f"- {note}\n")
            report_lines.append("\n**問題**: 知識庫未涵蓋此情境\n\n")
        
        report_lines.append("\n---\n\n")
        report_lines.append("## 5. 建議補強方向\n\n")
        
        if analysis.draft_rule_suggestions:
            report_lines.append("### 規則草案建議\n\n")
            for i, draft in enumerate(analysis.draft_rule_suggestions, 1):
                report_lines.append(f"{i}. {draft}\n\n")
        
        if analysis.draft_concept_suggestions:
            report_lines.append("### 概念草案建議\n\n")
            for i, draft in enumerate(analysis.draft_concept_suggestions, 1):
                report_lines.append(f"{i}. {draft}\n\n")
        
        report_lines.append("\n---\n\n")
        report_lines.append("## 6. 後續動作\n\n")
        for action in analysis.follow_up_actions:
            report_lines.append(f"- {action}\n")
        
        report_lines.append("\n---\n\n")
        report_lines.append("## 7. 查詢資訊\n\n")
        report_lines.append(f"**查詢字串**: `{analysis.raw_query}`\n\n")
        report_lines.append(f"**查詢時間**: {analysis.created_at}\n\n")
        
        # Write report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(''.join(report_lines))
        
        return report_path
    
    def process_and_report(self, event: ErrorEvent) -> ErrorAnalysisResult:
        """Process error event and generate complete report
        
        Runs the full workflow:
        1. analyze_error
        2. save_drafts (if applicable)
        3. save_report
        
        Args:
            event: ErrorEvent to process
        
        Returns:
            ErrorAnalysisResult from analysis
        """
        # Analyze error
        analysis = self.analyze_error(event)
        
        # Save drafts if any
        if analysis.draft_rule_suggestions or analysis.draft_concept_suggestions:
            self.save_drafts(analysis)
        
        # Save report
        report_path = self.save_report(event, analysis)
        
        return analysis


def main():
    """CLI entry point for error learning engine"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze error events using J-GOD Knowledge Brain"
    )
    parser.add_argument(
        "--event-file",
        type=str,
        required=True,
        help="Path to error event JSON/JSONL file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for reports (default: error_logs/reports/)"
    )
    
    args = parser.parse_args()
    
    # Read error event
    event_path = Path(args.event_file)
    if not event_path.exists():
        print(f"Error: Event file not found: {event_path}")
        return 1
    
    try:
        with open(event_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # Try to parse as single JSON object
            try:
                event_data = json.loads(content)
            except json.JSONDecodeError:
                # Try JSONL (first line)
                event_data = json.loads(content.split('\n')[0])
        
        event = ErrorEvent.from_dict(event_data)
    except Exception as e:
        print(f"Error parsing event file: {e}")
        return 1
    
    # Initialize engine
    engine_kwargs = {}
    if args.output_dir:
        engine_kwargs["report_output_dir"] = args.output_dir
    
    engine = ErrorLearningEngine(**engine_kwargs)
    
    # Process and report
    try:
        analysis = engine.process_and_report(event)
        
        # Print summary
        print("=" * 60)
        print("ERROR ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"Event ID: {event.id}")
        print(f"Classification: {analysis.classification}")
        print(f"Related Items: {len(analysis.related_items)}")
        print(f"  - RULES: {len([i for i in analysis.related_items if i.get('type') == 'RULE'])}")
        print(f"  - CONCEPTS: {len([i for i in analysis.related_items if i.get('type') == 'CONCEPT'])}")
        
        # Find report file
        report_files = list(engine.report_output_dir.glob(f"*_{event.id}.md"))
        if report_files:
            print(f"\nReport saved to: {report_files[0]}")
        
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

