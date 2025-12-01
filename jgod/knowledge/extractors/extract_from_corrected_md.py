"""Main Extractor: Extract all knowledge items from CORRECTED.md files and export to JSONL

This is the main entry point for extracting knowledge from structured markdown files
and generating the knowledge_base/jgod_knowledge_v1.jsonl file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from jgod.knowledge.extractors.extract_rules import extract_rules
from jgod.knowledge.extractors.extract_formulas import extract_formulas
from jgod.knowledge.extractors.extract_concepts import extract_concepts
from jgod.knowledge.extractors.extract_structures import extract_structures
from jgod.knowledge.extractors.extract_code_examples import extract_code_examples
from jgod.knowledge.extractors.extract_tables import extract_tables
from jgod.knowledge.extractors.base_extractor import list_source_files


def merge_all_items() -> List[Dict[str, Any]]:
    """Extract all knowledge items from all sources and merge them
    
    Returns:
        List of all knowledge items (dictionaries)
    """
    all_items = []
    
    print("Starting knowledge extraction...")
    print("=" * 60)
    
    # Extract rules
    print("\n[1/6] Extracting RULES...")
    try:
        rules = extract_rules()
        all_items.extend(rules)
        print(f"  ✓ Extracted {len(rules)} rules")
    except Exception as e:
        print(f"  ✗ Error extracting rules: {e}")
    
    # Extract formulas
    print("\n[2/6] Extracting FORMULAS...")
    try:
        formulas = extract_formulas()
        all_items.extend(formulas)
        print(f"  ✓ Extracted {len(formulas)} formulas")
    except Exception as e:
        print(f"  ✗ Error extracting formulas: {e}")
    
    # Extract concepts
    print("\n[3/6] Extracting CONCEPTS...")
    try:
        concepts = extract_concepts()
        all_items.extend(concepts)
        print(f"  ✓ Extracted {len(concepts)} concepts")
    except Exception as e:
        print(f"  ✗ Error extracting concepts: {e}")
    
    # Extract structures
    print("\n[4/6] Extracting STRUCTURES...")
    try:
        structures = extract_structures()
        all_items.extend(structures)
        print(f"  ✓ Extracted {len(structures)} structures")
    except Exception as e:
        print(f"  ✗ Error extracting structures: {e}")
    
    # Extract code examples
    print("\n[5/6] Extracting CODE EXAMPLES...")
    try:
        code_items = extract_code_examples()
        all_items.extend(code_items)
        print(f"  ✓ Extracted {len(code_items)} code examples")
    except Exception as e:
        print(f"  ✗ Error extracting code examples: {e}")
    
    # Extract tables
    print("\n[6/6] Extracting TABLES...")
    try:
        tables = extract_tables()
        all_items.extend(tables)
        print(f"  ✓ Extracted {len(tables)} tables")
    except Exception as e:
        print(f"  ✗ Error extracting tables: {e}")
    
    print("\n" + "=" * 60)
    print(f"\nTotal items extracted: {len(all_items)}")
    
    return all_items


def export_to_jsonl(items: List[Dict[str, Any]], output_path: Path) -> None:
    """Export knowledge items to JSONL file
    
    Args:
        items: List of knowledge item dictionaries
        output_path: Path to output JSONL file
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write items to JSONL file
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in items:
            json_line = json.dumps(item, ensure_ascii=False)
            f.write(json_line + '\n')
    
    print(f"\n✓ Exported {len(items)} items to: {output_path}")


def print_statistics(items: List[Dict[str, Any]]) -> None:
    """Print extraction statistics
    
    Args:
        items: List of all knowledge items
    """
    print("\n" + "=" * 60)
    print("EXTRACTION STATISTICS")
    print("=" * 60)
    
    # Count by type
    type_counts = {}
    for item in items:
        item_type = item.get("type", "UNKNOWN")
        type_counts[item_type] = type_counts.get(item_type, 0) + 1
    
    # Print counts
    for item_type in sorted(type_counts.keys()):
        count = type_counts[item_type]
        print(f"  {item_type:12s}: {count:4d} items")
    
    print("=" * 60)
    
    # Count by source document
    source_counts = {}
    for item in items:
        source = item.get("source_doc", "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
    
    print(f"\nExtracted from {len(source_counts)} source documents:")
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {source}: {count} items")
    if len(source_counts) > 5:
        print(f"  ... and {len(source_counts) - 5} more")


def main(output_path: Path | None = None) -> int:
    """Main extraction function
    
    Args:
        output_path: Path to output JSONL file. If None, uses default path.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Default output path
    if output_path is None:
        project_root = Path(__file__).parent.parent.parent.parent
        output_path = project_root / "knowledge_base" / "jgod_knowledge_v1.jsonl"
    
    output_path = Path(output_path)
    
    # Check source files exist
    source_files = list_source_files()
    if not source_files:
        print("⚠ Warning: No source files found in structured_books/")
        print("  Expected files matching: *_CORRECTED.md or *_AI知識庫版_v1.md")
        return 1
    
    print(f"Found {len(source_files)} source file(s)")
    
    # Extract all items
    try:
        all_items = merge_all_items()
    except Exception as e:
        print(f"\n✗ Fatal error during extraction: {e}")
        return 1
    
    if not all_items:
        print("\n⚠ Warning: No knowledge items extracted!")
        print("  Check if source files contain extractable content.")
        return 1
    
    # Export to JSONL
    try:
        export_to_jsonl(all_items, output_path)
    except Exception as e:
        print(f"\n✗ Error exporting to JSONL: {e}")
        return 1
    
    # Print statistics
    print_statistics(all_items)
    
    print(f"\n✅ Knowledge extraction completed successfully!")
    print(f"   Output file: {output_path}")
    
    return 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract knowledge from CORRECTED.md files and generate JSONL knowledge base"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSONL file path (default: knowledge_base/jgod_knowledge_v1.jsonl)"
    )
    
    args = parser.parse_args()
    
    output_path = Path(args.output) if args.output else None
    exit_code = main(output_path)
    sys.exit(exit_code)

