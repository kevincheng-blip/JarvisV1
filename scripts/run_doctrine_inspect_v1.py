#!/usr/bin/env python
"""
Doctrine Inspect CLI v1

簡單的 CLI 工具，用於查詢與瀏覽 14 本聖經。

Usage:
    PYTHONPATH=. python scripts/run_doctrine_inspect_v1.py list
    PYTHONPATH=. python scripts/run_doctrine_inspect_v1.py list --category SYSTEM_PHILOSOPHY
    PYTHONPATH=. python scripts/run_doctrine_inspect_v1.py sections book_01
    PYTHONPATH=. python scripts/run_doctrine_inspect_v1.py show book_01 section_001
    PYTHONPATH=. python scripts/run_doctrine_inspect_v1.py search "風控" --book book_07
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jgod.doctrine import (
    DoctrineRegistryV1,
    DoctrineLoaderV1,
    DoctrineQueryV1,
)


def cmd_list(args) -> int:
    """列出所有書籍"""
    registry = DoctrineRegistryV1()
    
    if args.category:
        books = registry.list_books(category=args.category)
        print(f"\n📚 Books in category '{args.category}':")
    else:
        books = registry.list_books()
        print(f"\n📚 All Doctrine Books ({len(books)} books):")
    
    print("=" * 80)
    for book in books:
        print(f"\n{book.book_id}: {book.title}")
        print(f"  Category: {book.category}")
        print(f"  Description: {book.description}")
        if book.tags:
            print(f"  Tags: {', '.join(book.tags)}")
        
        # 顯示可用版本
        versions = []
        if book.structured_path and Path(book.structured_path).exists():
            versions.append("STRUCTURED")
        if book.corrected_path and Path(book.corrected_path).exists():
            versions.append("CORRECTED")
        if book.enhanced_path and Path(book.enhanced_path).exists():
            versions.append("ENHANCED")
        
        if versions:
            print(f"  Available versions: {', '.join(versions)}")
        else:
            print(f"  ⚠️  No files found")
    
    print()
    return 0


def cmd_sections(args) -> int:
    """列出指定書籍的所有 sections"""
    registry = DoctrineRegistryV1()
    query = DoctrineQueryV1()
    
    book_id = args.book_id
    book = registry.get_book_meta(book_id)
    if book is None:
        print(f"❌ Book ID '{book_id}' not found")
        return 1
    
    print(f"\n📖 Book: {book.title} ({book_id})")
    print("=" * 80)
    
    try:
        sections = query.list_sections(book_id, version=args.version)
        print(f"\nFound {len(sections)} sections:\n")
        
        for i, sec in enumerate(sections, 1):
            level_indent = "  " * (sec.level - 1) if sec.level > 0 else ""
            print(f"{i:3d}. {level_indent}[{sec.section_id}] {sec.heading}")
            print(f"     Lines {sec.start_line}-{sec.end_line}, Level {sec.level}")
            preview = sec.get_preview(max_length=100)
            if len(sec.content) > 100:
                preview = preview.rstrip() + "..."
            print(f"     Preview: {preview[:80].replace(chr(10), ' ')}")
            print()
        
    except Exception as e:
        print(f"❌ Error loading sections: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def cmd_show(args) -> int:
    """顯示指定 section 的完整內容"""
    registry = DoctrineRegistryV1()
    query = DoctrineQueryV1()
    
    book_id = args.book_id
    section_id = args.section_id
    
    book = registry.get_book_meta(book_id)
    if book is None:
        print(f"❌ Book ID '{book_id}' not found")
        return 1
    
    try:
        section = query.get_section(book_id, section_id, version=args.version)
        if section is None:
            print(f"❌ Section '{section_id}' not found in book '{book_id}'")
            return 1
        
        print(f"\n📖 Book: {book.title} ({book_id})")
        print(f"📄 Section: {section.heading} ({section_id})")
        print("=" * 80)
        print(f"\nLines {section.start_line}-{section.end_line}, Level {section.level}\n")
        print(section.content)
        print()
        
    except Exception as e:
        print(f"❌ Error loading section: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def cmd_search(args) -> int:
    """搜尋關鍵字"""
    registry = DoctrineRegistryV1()
    query = DoctrineQueryV1()
    
    keyword = args.keyword
    book_ids = args.book.split(',') if args.book else None
    
    if book_ids:
        # 驗證 book_ids
        valid_book_ids = []
        for bid in book_ids:
            if registry.has_book(bid):
                valid_book_ids.append(bid)
            else:
                print(f"⚠️  Warning: Book ID '{bid}' not found, skipping")
        
        if not valid_book_ids:
            print(f"❌ No valid book IDs found")
            return 1
        
        book_ids = valid_book_ids
    
    print(f"\n🔍 Searching for: '{keyword}'")
    if book_ids:
        print(f"📚 In books: {', '.join(book_ids)}")
    else:
        print(f"📚 In all books")
    print("=" * 80)
    
    try:
        results = query.search_across_books(
            keyword,
            book_ids=book_ids,
            version=args.version
        )
        
        if not results:
            print(f"\n❌ No results found")
            return 0
        
        print(f"\nFound {len(results)} matching sections:\n")
        
        for i, sec in enumerate(results, 1):
            print(f"{i}. [{sec.book_id}] {sec.heading}")
            print(f"   Section: {sec.section_id}, Lines {sec.start_line}-{sec.end_line}")
            preview = sec.get_preview(max_length=150)
            if len(sec.content) > 150:
                preview = preview.rstrip() + "..."
            print(f"   Preview: {preview.replace(chr(10), ' ')}")
            print()
        
    except Exception as e:
        print(f"❌ Error searching: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Doctrine Inspect CLI v1 - Query and browse 14 doctrine books"
    )
    parser.add_argument(
        "--version",
        type=str,
        default="ENHANCED",
        choices=["STRUCTURED", "CORRECTED", "ENHANCED"],
        help="Version to use (default: ENHANCED)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # list command
    list_parser = subparsers.add_parser("list", help="List all books")
    list_parser.add_argument(
        "--category",
        type=str,
        help="Filter by category (e.g., SYSTEM_PHILOSOPHY, RISK, RL_REWARD)"
    )
    list_parser.set_defaults(func=cmd_list)
    
    # sections command
    sections_parser = subparsers.add_parser("sections", help="List sections of a book")
    sections_parser.add_argument("book_id", help="Book ID (book_01 ~ book_14)")
    sections_parser.set_defaults(func=cmd_sections)
    
    # show command
    show_parser = subparsers.add_parser("show", help="Show full content of a section")
    show_parser.add_argument("book_id", help="Book ID (book_01 ~ book_14)")
    show_parser.add_argument("section_id", help="Section ID (e.g., book_01_section_001)")
    show_parser.set_defaults(func=cmd_show)
    
    # search command
    search_parser = subparsers.add_parser("search", help="Search keyword across books")
    search_parser.add_argument("keyword", help="Keyword to search")
    search_parser.add_argument(
        "--book",
        type=str,
        help="Comma-separated book IDs to search (e.g., 'book_01,book_02')"
    )
    search_parser.set_defaults(func=cmd_search)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

