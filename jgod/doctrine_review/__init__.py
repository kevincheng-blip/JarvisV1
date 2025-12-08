"""
J-GOD Doctrine Review Module v1

提供從 14 本聖經切 section、分類內容、提取程式碼與算式，並產生 AI 可加工的 review JSONL。
"""

from jgod.doctrine_review.review_loop_v1 import (
    DoctrineReviewLoopV1,
    classify_section_content,
    extract_code_blocks,
    extract_formula_lines,
)

__all__ = [
    "DoctrineReviewLoopV1",
    "classify_section_content",
    "extract_code_blocks",
    "extract_formula_lines",
]

