#!/usr/bin/env python
"""
Doctrine Knowledge Sync v1 CLI

將已完成的 review JSONL（AI 已填好）轉換成 KnowledgeBrain 格式的知識庫 JSONL。

Usage:
    PYTHONPATH=. python scripts/run_doctrine_knowledge_sync_v1.py --inputs data/doctrine_reviews/review_2025-12-09.jsonl
    PYTHONPATH=. python scripts/run_doctrine_knowledge_sync_v1.py --inputs "review1.jsonl,review2.jsonl" --output custom_output.jsonl
"""

from __future__ import annotations

import argparse
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jgod.doctrine.doctrine_knowledge_sync_v1 import DoctrineKnowledgeSyncV1

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Doctrine Knowledge Sync v1 - Convert review JSONL to knowledge base JSONL"
    )
    parser.add_argument(
        "--inputs",
        type=str,
        required=True,
        help="Comma-separated paths to review JSONL files (e.g., 'review1.jsonl,review2.jsonl')"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="knowledge_base/jgod_doctrine_knowledge_v1.jsonl",
        help="Output knowledge base JSONL file path (default: knowledge_base/jgod_doctrine_knowledge_v1.jsonl)"
    )
    
    args = parser.parse_args()
    
    # 解析 input paths
    input_paths = [p.strip() for p in args.inputs.split(',') if p.strip()]
    
    if not input_paths:
        logger.error("No input files specified")
        return 1
    
    logger.info(f"Input files: {input_paths}")
    logger.info(f"Output file: {args.output}")
    
    # 執行 sync
    sync = DoctrineKnowledgeSyncV1(
        input_paths=input_paths,
        output_path=args.output
    )
    
    try:
        stats = sync.sync()
        
        # 輸出統計
        print("\n" + "=" * 80)
        print("📊 Knowledge Sync Statistics")
        print("=" * 80)
        print(f"Input review records: {stats['input_records']}")
        print(f"Output knowledge entries: {stats['output_entries']}")
        print(f"Entries with code: {stats['entries_with_code']}")
        print(f"Entries with formula: {stats['entries_with_formula']}")
        print(f"Skipped entries: {stats['skipped_entries']}")
        print(f"\nOutput file: {stats['output_file']}")
        print("=" * 80)
        print("\n✅ Knowledge sync completed successfully!")
        print("\nNote: This file can be used by KnowledgeBrain (future integration).")
        print()
        
        return 0
        
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

