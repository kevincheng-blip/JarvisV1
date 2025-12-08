"""
J-GOD Doctrine Service v1

統一管理與查詢 14 本聖經（structured_books）的 Service Layer。

主要組件：
- DoctrineRegistryV1: 註冊所有聖經檔案的 metadata
- DoctrineLoaderV1: 讀取與解析聖經檔案
- DoctrineQueryV1: 提供查詢 API（sections, content）

使用範例：
    from jgod.doctrine import DoctrineRegistryV1, DoctrineLoaderV1, DoctrineQueryV1
    
    # 註冊表
    registry = DoctrineRegistryV1()
    book = registry.get_book_meta("book_01")
    
    # 讀取器
    loader = DoctrineLoaderV1()
    text = loader.load_book_text("book_01", version="ENHANCED")
    
    # 查詢器
    query = DoctrineQueryV1()
    sections = query.list_sections("book_01")
"""

from jgod.doctrine.doctrine_registry_v1 import (
    DoctrineBookMeta,
    DoctrineRegistryV1,
    get_book_meta,
    list_books,
)

from jgod.doctrine.doctrine_loader_v1 import (
    DoctrineLoaderV1,
    load_book_text,
)

from jgod.doctrine.doctrine_query_v1 import (
    DoctrineSection,
    DoctrineQueryV1,
)

__all__ = [
    "DoctrineBookMeta",
    "DoctrineRegistryV1",
    "DoctrineLoaderV1",
    "DoctrineQueryV1",
    "DoctrineSection",
    "get_book_meta",
    "list_books",
    "load_book_text",
]

