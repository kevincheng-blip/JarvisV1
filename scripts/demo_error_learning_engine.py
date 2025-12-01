"""J-GOD Error Learning Engine Demo Script

This script demonstrates how the ErrorLearningEngine works by creating
three example error events that represent different classification scenarios:

- Case A: UTILIZATION_GAP - Rules exist but weren't used
- Case B: FORM_INSUFFICIENT - Only concepts exist, no executable rules
- Case C: KNOWLEDGE_GAP - No relevant knowledge found

Usage:
    python scripts/demo_error_learning_engine.py

The script will:
1. Load the KnowledgeBrain from knowledge_base/jgod_knowledge_v1.jsonl
2. Dynamically find examples from the knowledge base
3. Create three demonstration ErrorEvents
4. Analyze each event using ErrorLearningEngine
5. Generate reports in error_logs/demo_reports/
6. Print summary statistics to console
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jgod.learning.error_event import ErrorEvent, CLASS_UTILIZATION_GAP, CLASS_FORM_INSUFFICIENT, CLASS_KNOWLEDGE_GAP
from jgod.learning.error_learning_engine import ErrorLearningEngine
from jgod.war_room.knowledge_gateway import get_knowledge_brain


def find_rule_example(brain) -> dict | None:
    """Find a rule from knowledge base to use as example
    
    Args:
        brain: KnowledgeBrain instance
    
    Returns:
        Dictionary with rule info, or None if no rules found
    """
    # Try to find rules by common tags
    rules = brain.get_rules(tag="risk")
    if not rules:
        rules = brain.get_rules()  # Get all rules
    
    if rules:
        rule = rules[0]
        return {
            "item": rule,
            "id": rule.id,
            "title": rule.title,
            "tags": rule.tags,
            "keywords": rule.title.split()[:3]  # First few words as keywords
        }
    return None


def find_concept_example(brain) -> dict | None:
    """Find a concept from knowledge base to use as example
    
    Args:
        brain: KnowledgeBrain instance
    
    Returns:
        Dictionary with concept info, or None if no concepts found
    """
    # Try to find concepts
    concepts = brain.search(type="CONCEPT", limit=10)
    
    if concepts:
        concept = concepts[0]
        concept_name = ""
        if concept.structured and isinstance(concept.structured, dict):
            concept_name = concept.structured.get("name", concept.title)
        else:
            concept_name = concept.title
        
        return {
            "item": concept,
            "id": concept.id,
            "title": concept.title,
            "name": concept_name,
            "tags": concept.tags,
            "description": concept.description[:100]
        }
    return None


def create_case_a_event(rule_example: dict | None) -> ErrorEvent:
    """Create ErrorEvent for Case A: UTILIZATION_GAP
    
    Args:
        rule_example: Rule example from knowledge base
    
    Returns:
        ErrorEvent designed to trigger UTILIZATION_GAP classification
    """
    if rule_example:
        rule = rule_example["item"]
        rule_title = rule_example["title"]
        rule_tags = rule_example.get("tags", [])
        
        # Extract key terms from rule to ensure high relevance
        rule_keywords = rule_title.split()[:3]  # First few words
        
        # Create event that should match the rule but didn't use it
        # Use same tags and keywords to ensure high relevance
        event = ErrorEvent(
            id="DEMO_CASE_A_UTILIZATION_GAP",
            timestamp=datetime.now(),
            symbol="2330",
            timeframe="1d",
            side="long",
            predicted_outcome="hit_tp",
            actual_outcome="hit_sl",
            pnl=-2000.0,
            error_type="stop_loss",
            tags=rule_tags[:3] if rule_tags else ["risk", "stop_loss"],
            used_signals=["SIG_001"],
            used_rules=[],  # Intentionally empty - rule exists but wasn't used
            context={
                "strategy": "主流突破",
                "market_regime": "bull_trend"
            },
            notes=f"預測會到達目標價，但實際上觸及停損。與「{rule_title}」相關的「{rule_keywords[0] if rule_keywords else '規則'}」規則存在但該規則未被觸發使用。"
        )
    else:
        # Fallback if no rules found
        event = ErrorEvent(
            id="DEMO_CASE_A_UTILIZATION_GAP",
            timestamp=datetime.now(),
            symbol="2330",
            timeframe="1d",
            error_type="stop_loss",
            tags=["risk", "stop_loss"],
            used_rules=[],  # Empty - simulating unused rules
            notes="單筆交易虧損超過 2%，但相關風控規則未被使用"
        )
    
    return event


def create_case_b_event(concept_example: dict | None) -> ErrorEvent:
    """Create ErrorEvent for Case B: FORM_INSUFFICIENT
    
    Args:
        concept_example: Concept example from knowledge base
    
    Returns:
        ErrorEvent designed to trigger FORM_INSUFFICIENT classification
    """
    if concept_example:
        concept = concept_example["item"]
        concept_name = concept_example.get("name", concept_example["title"])
        concept_tags = concept_example.get("tags", [])
        
        # Ensure tags don't overlap with common rule tags
        # Use concept-specific tags to avoid matching rules
        safe_tags = [t for t in concept_tags if t not in ["risk", "stop_loss", "entry", "exit"]]
        if not safe_tags:
            safe_tags = ["intraday", "concept", "theory"]
        
        # Create event that matches concept but no clear rule
        # Use timing error type to avoid matching stop_loss rules
        event = ErrorEvent(
            id="DEMO_CASE_B_FORM_INSUFFICIENT",
            timestamp=datetime.now(),
            symbol="2330",
            timeframe="5m",
            side="long",
            predicted_outcome="up",
            actual_outcome="down",
            pnl=-500.0,
            error_type="timing",  # Different from stop_loss to avoid rule matching
            tags=safe_tags[:3],
            used_signals=["SIG_002"],
            used_rules=[],  # No rules used
            context={
                "strategy": "急攻狙擊",
                "market_regime": "choppy"
            },
            notes=f"預測「{concept_name}」相關的市場行為，但僅有概念定義，缺乏可執行的規則或公式來判斷時機。此為概念層級的知識，尚未轉化為明確的執行規則。"
        )
    else:
        # Fallback - use tags that likely won't match rules
        event = ErrorEvent(
            id="DEMO_CASE_B_FORM_INSUFFICIENT",
            timestamp=datetime.now(),
            symbol="2330",
            timeframe="5m",
            error_type="timing",
            tags=["intraday", "concept", "theory"],
            notes="盤中出現相關概念描述的情境，但缺乏明確的規則判斷標準。僅有理論概念，無可執行的操作規則。"
        )
    
    return event


def create_case_c_event() -> ErrorEvent:
    """Create ErrorEvent for Case C: KNOWLEDGE_GAP
    
    Returns:
        ErrorEvent designed to trigger KNOWLEDGE_GAP classification
    """
    # Use obscure/new situation that likely doesn't exist in knowledge base
    # Use unique tags and error type to avoid matching any existing knowledge
    event = ErrorEvent(
        id="DEMO_CASE_C_KNOWLEDGE_GAP",
        timestamp=datetime.now(),
        symbol="2330",
        timeframe="1d",
        side="long",
        predicted_outcome="range",
        actual_outcome="breakout_false_signal",
        pnl=-1500.0,
        error_type="false_signal",  # Unique error type
        tags=["uncommon_situation", "novel_pattern", "edge_case", "untested_scenario"],
        used_signals=["SIG_003"],
        used_rules=[],
        context={
            "strategy": "未知策略",
            "market_regime": "unusual_volatility_spike"
        },
        notes="遇到一種全新的市場模式：在極低成交量下出現技術指標假突破，接著反向快速移動。此情境在現有知識庫中未找到相關規則、概念或公式。這是一個全新的edge case，需要補充新的知識。"
    )
    
    return event


def print_analysis_summary(event: ErrorEvent, analysis, report_path: Path):
    """Print analysis summary to console
    
    Args:
        event: ErrorEvent that was analyzed
        analysis: ErrorAnalysisResult from analysis
        report_path: Path to generated report file
    """
    print("=" * 70)
    print(f"Event ID: {event.id}")
    print(f"Classification: {analysis.classification}")
    print(f"-" * 70)
    
    # Count by type
    type_counts = {}
    for item in analysis.related_items:
        item_type = item.get("type", "UNKNOWN")
        type_counts[item_type] = type_counts.get(item_type, 0) + 1
    
    print("Related Knowledge Items:")
    for item_type, count in sorted(type_counts.items()):
        print(f"  {item_type:12s}: {count:3d} items")
    
    if analysis.classification == CLASS_UTILIZATION_GAP:
        print(f"\nUtilization Gap Reasons: {len(analysis.utilization_gap_reasons)}")
        for reason in analysis.utilization_gap_reasons[:2]:  # Show first 2
            print(f"  - {reason[:80]}...")
    
    elif analysis.classification == CLASS_FORM_INSUFFICIENT:
        print(f"\nDraft Rule Suggestions: {len(analysis.draft_rule_suggestions)}")
        for suggestion in analysis.draft_rule_suggestions[:1]:  # Show first 1
            print(f"  - {suggestion[:80]}...")
    
    elif analysis.classification == CLASS_KNOWLEDGE_GAP:
        print(f"\nKnowledge Gap Notes: {len(analysis.knowledge_gap_notes)}")
        for note in analysis.knowledge_gap_notes[:2]:  # Show first 2
            print(f"  - {note[:80]}...")
    
    print(f"\nReport saved to: {report_path}")
    print("=" * 70)
    print()


def main():
    """Main demo function"""
    print("=" * 70)
    print("J-GOD Error Learning Engine Demo")
    print("=" * 70)
    print()
    
    # Load KnowledgeBrain
    print("[1/4] Loading KnowledgeBrain...")
    try:
        brain = get_knowledge_brain()
        brain.load()
        total_items = brain.count()
        print(f"  ✓ Loaded {total_items} knowledge items")
    except Exception as e:
        print(f"  ✗ Error loading KnowledgeBrain: {e}")
        print("  ⚠ Continuing with empty knowledge base...")
        brain = get_knowledge_brain()
        brain.load()
    
    # Find examples from knowledge base
    print("\n[2/4] Finding examples from knowledge base...")
    rule_example = find_rule_example(brain)
    concept_example = find_concept_example(brain)
    
    if rule_example:
        print(f"  ✓ Found rule example: {rule_example['title']} (ID: {rule_example['id']})")
    else:
        print("  ⚠ No rules found in knowledge base")
    
    if concept_example:
        print(f"  ✓ Found concept example: {concept_example['title']} (ID: {concept_example['id']})")
    else:
        print("  ⚠ No concepts found in knowledge base")
    
    # Create ErrorLearningEngine
    print("\n[3/4] Initializing ErrorLearningEngine...")
    project_root = Path(__file__).parent.parent
    engine = ErrorLearningEngine(
        report_output_dir=project_root / "error_logs" / "demo_reports"
    )
    print("  ✓ Engine initialized")
    
    # Create and analyze error events
    print("\n[4/4] Creating and analyzing error events...")
    print()
    
    # Case A: UTILIZATION_GAP
    print("Case A: UTILIZATION_GAP (Rules exist but weren't used)")
    event_a = create_case_a_event(rule_example)
    try:
        analysis_a = engine.process_and_report(event_a)
        report_path_a = engine.report_output_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{event_a.id}.md"
        # Find actual report file
        report_files_a = list(engine.report_output_dir.glob(f"*_{event_a.id}.md"))
        if report_files_a:
            report_path_a = report_files_a[-1]  # Get latest
        print_analysis_summary(event_a, analysis_a, report_path_a)
    except Exception as e:
        print(f"  ✗ Error analyzing Case A: {e}")
        import traceback
        traceback.print_exc()
    
    # Case B: FORM_INSUFFICIENT
    print("Case B: FORM_INSUFFICIENT (Only concepts exist, no executable rules)")
    event_b = create_case_b_event(concept_example)
    try:
        analysis_b = engine.process_and_report(event_b)
        report_files_b = list(engine.report_output_dir.glob(f"*_{event_b.id}.md"))
        report_path_b = report_files_b[-1] if report_files_b else Path("N/A")
        print_analysis_summary(event_b, analysis_b, report_path_b)
    except Exception as e:
        print(f"  ✗ Error analyzing Case B: {e}")
        import traceback
        traceback.print_exc()
    
    # Case C: KNOWLEDGE_GAP
    print("Case C: KNOWLEDGE_GAP (No relevant knowledge found)")
    event_c = create_case_c_event()
    try:
        analysis_c = engine.process_and_report(event_c)
        report_files_c = list(engine.report_output_dir.glob(f"*_{event_c.id}.md"))
        report_path_c = report_files_c[-1] if report_files_c else Path("N/A")
        print_analysis_summary(event_c, analysis_c, report_path_c)
    except Exception as e:
        print(f"  ✗ Error analyzing Case C: {e}")
        import traceback
        traceback.print_exc()
    
    # Final summary
    print()
    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print(f"\nReports generated in: {engine.report_output_dir}")
    print(f"\nTo view reports:")
    print(f"  ls -lh {engine.report_output_dir}")
    print(f"\nTo view a specific report:")
    print(f"  cat {engine.report_output_dir}/*DEMO_CASE_*.md | head -50")
    print()


if __name__ == "__main__":
    main()

