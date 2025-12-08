"""
Doctrine Query v1

提供查詢聖經 sections 的 API。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from jgod.doctrine.doctrine_registry_v1 import DoctrineRegistryV1
from jgod.doctrine.doctrine_loader_v1 import DoctrineLoaderV1


@dataclass
class DoctrineSection:
    """Doctrine Section
    
    代表聖經中的一個 section（章節）。
    """
    book_id: str
    section_id: str
    heading: str
    content: str
    level: int  # 標題層級（1=#, 2=##, ...）
    start_line: int
    end_line: int
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def get_preview(self, max_length: int = 200) -> str:
        """取得內容預覽（截斷到指定長度）"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."
    
    def contains_keyword(self, keyword: str) -> bool:
        """檢查 section 是否包含關鍵字（簡單字串匹配）"""
        keyword_lower = keyword.lower()
        return (
            keyword_lower in self.heading.lower() or
            keyword_lower in self.content.lower()
        )


class DoctrineQueryV1:
    """Doctrine Query v1
    
    提供查詢聖經 sections 的 API。
    """
    
    def __init__(
        self,
        registry: Optional[DoctrineRegistryV1] = None,
        loader: Optional[DoctrineLoaderV1] = None,
        default_version: str = "ENHANCED"
    ):
        """初始化 Query
        
        Args:
            registry: 可選的 DoctrineRegistryV1 實例
            loader: 可選的 DoctrineLoaderV1 實例
            default_version: 預設使用的版本
        """
        self.registry = registry if registry is not None else DoctrineRegistryV1()
        self.loader = loader if loader is not None else DoctrineLoaderV1(self.registry)
        self.default_version = default_version
        self._section_cache: dict[str, List[DoctrineSection]] = {}  # book_id -> sections
    
    def list_sections(
        self,
        book_id: str,
        version: Optional[str] = None
    ) -> List[DoctrineSection]:
        """列出指定書籍的所有 sections
        
        Args:
            book_id: 書本 ID
            version: 版本（可選，預設使用 default_version）
        
        Returns:
            List of DoctrineSection
        """
        if version is None:
            version = self.default_version
        
        # 檢查快取
        cache_key = f"{book_id}:{version}"
        if cache_key in self._section_cache:
            return self._section_cache[cache_key]
        
        # 讀取並轉換
        raw_sections = self.loader.load_book_sections(book_id, version)
        sections = [
            DoctrineSection(
                book_id=book_id,
                section_id=sec['section_id'],
                heading=sec['heading'],
                content=sec['content'],
                level=sec['level'],
                start_line=sec['start_line'],
                end_line=sec['end_line'],
                tags=[],  # v1 先不處理 tags
            )
            for sec in raw_sections
        ]
        
        # 快取結果
        self._section_cache[cache_key] = sections
        
        return sections
    
    def get_section(
        self,
        book_id: str,
        section_id: str,
        version: Optional[str] = None
    ) -> Optional[DoctrineSection]:
        """取得指定的 section
        
        Args:
            book_id: 書本 ID
            section_id: Section ID
            version: 版本（可選，預設使用 default_version）
        
        Returns:
            DoctrineSection 或 None（如果不存在）
        """
        sections = self.list_sections(book_id, version)
        for sec in sections:
            if sec.section_id == section_id:
                return sec
        return None
    
    def search_sections(
        self,
        book_id: str,
        keyword: str,
        version: Optional[str] = None
    ) -> List[DoctrineSection]:
        """搜尋包含關鍵字的 sections（簡單字串匹配）
        
        Args:
            book_id: 書本 ID
            keyword: 搜尋關鍵字
            version: 版本（可選，預設使用 default_version）
        
        Returns:
            符合條件的 sections 列表
        """
        sections = self.list_sections(book_id, version)
        return [sec for sec in sections if sec.contains_keyword(keyword)]
    
    def search_across_books(
        self,
        keyword: str,
        book_ids: Optional[List[str]] = None,
        version: Optional[str] = None
    ) -> List[DoctrineSection]:
        """跨書籍搜尋關鍵字
        
        Args:
            keyword: 搜尋關鍵字
            book_ids: 要搜尋的書本 ID 列表（None 表示搜尋所有書籍）
            version: 版本（可選，預設使用 default_version）
        
        Returns:
            符合條件的 sections 列表
        """
        if book_ids is None:
            book_ids = self.registry.get_all_book_ids()
        
        results = []
        for book_id in book_ids:
            sections = self.search_sections(book_id, keyword, version)
            results.extend(sections)
        
        return results
    
    def clear_cache(self, book_id: Optional[str] = None) -> None:
        """清除快取
        
        Args:
            book_id: 可選，只清除指定書籍的快取（None 表示清除所有）
        """
        if book_id is None:
            self._section_cache.clear()
        else:
            # 清除該書籍的所有版本快取
            keys_to_remove = [
                key for key in self._section_cache.keys()
                if key.startswith(f"{book_id}:")
            ]
            for key in keys_to_remove:
                del self._section_cache[key]

