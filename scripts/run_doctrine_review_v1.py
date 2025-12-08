#!/usr/bin/env python
"""
Doctrine Review Loop v1 CLI

執行完整的 doctrine review 流程，產生 AI 可加工的 review JSONL。

Usage:
    PYTHONPATH=. python scripts/run_doctrine_review_v1.py
    PYTHONPATH=. python scripts/run_doctrine_review_v1.py --books book_01,book_03
    PYTHONPATH=. python scripts/run_doctrine_review_v1.py --output data/doctrine_reviews/custom_review.jsonl
"""

from __future__ import annotations

import argparse
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jgod.doctrine_review.review_loop_v1 import DoctrineReviewLoopV1

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Doctrine Review Loop v1 - Generate review JSONL from 14 doctrine books"
    )
    parser.add_argument(
        "--books",
        type=str,
        help="Comma-separated book IDs (e.g., 'book_01,book_03'). If not provided, process all 14 books."
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output filename (e.g., 'review_2025-12-09.jsonl'). If not provided, auto-generate with timestamp."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/doctrine_reviews",
        help="Output directory (default: data/doctrine_reviews)"
    )
    
    args = parser.parse_args()
    
    # 解析 book_ids
    book_ids = None
    if args.books:
        book_ids = [bid.strip() for bid in args.books.split(',') if bid.strip()]
        logger.info(f"Processing specified books: {book_ids}")
    else:
        logger.info("Processing all 14 books")
    
    # 執行 review
    review_loop = DoctrineReviewLoopV1(output_dir=args.output_dir)
    
    try:
        stats = review_loop.run_full_review(
            book_ids=book_ids,
            output_filename=args.output
        )
        
        # 輸出統計
        print("\n" + "=" * 80)
        print("📊 Review Statistics")
        print("=" * 80)
        print(f"Total books processed: {stats['total_books']}")
        print(f"Total sections: {stats['total_sections']}")
        print(f"Sections with code: {stats['sections_with_code']}")
        print(f"Sections with formula: {stats['sections_with_formula']}")
        print(f"Sections with checklist: {stats['sections_with_checklist']}")
        print(f"Total code blocks extracted: {stats['total_code_blocks']}")
        print(f"Total formula lines extracted: {stats['total_formula_lines']}")
        print(f"\nOutput file: {stats['output_file']}")
        print("=" * 80)
        print("\n✅ Review completed successfully!")
        print("\nNext step: Use Cursor AI to fill in ai_* fields in the JSONL file.")
        print()
        
        return 0
        
    except Exception as e:
        logger.error(f"Review failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

