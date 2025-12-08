"""
Doctrine Loader v1

根據 DoctrineBookMeta 讀取聖經檔案內容，提供簡單的 section 切割功能。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from jgod.doctrine.doctrine_registry_v1 import (
    DoctrineRegistryV1,
    DoctrineBookMeta,
    get_book_meta,
)

logger = logging.getLogger(__name__)


class DoctrineLoaderV1:
    """Doctrine Loader v1
    
    提供讀取與解析聖經檔案的功能。
    """
    
    def __init__(self, registry: Optional[DoctrineRegistryV1] = None):
        """初始化 Loader
        
        Args:
            registry: 可選的 DoctrineRegistryV1 實例
        """
        self.registry = registry if registry is not None else DoctrineRegistryV1()
    
    def load_book_text(
        self,
        book_id: str,
        version: str = "ENHANCED"
    ) -> str:
        """讀取指定書籍的文字內容
        
        Args:
            book_id: 書本 ID（book_01 ~ book_14）
            version: 版本（"STRUCTURED" / "CORRECTED" / "ENHANCED"）
        
        Returns:
            檔案內容文字，如果檔案不存在則返回空字串
        
        Raises:
            ValueError: 如果 book_id 不存在
        """
        book_meta = self.registry.get_book_meta(book_id)
        if book_meta is None:
            raise ValueError(f"Book ID '{book_id}' not found in registry")
        
        file_path = book_meta.get_path(version)
        if file_path is None:
            logger.warning(
                f"Version '{version}' not available for book '{book_id}' ({book_meta.title})"
            )
            return ""
        
        path = Path(file_path)
        if not path.exists():
            logger.warning(
                f"File not found: {file_path} (book_id={book_id}, version={version})"
            )
            return ""
        
        try:
            content = path.read_text(encoding="utf-8")
            return content
        except Exception as e:
            logger.error(
                f"Failed to read file {file_path}: {e}",
                exc_info=True
            )
            return ""
    
    def split_book_into_sections(
        self,
        text: str,
        book_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """將文字內容切割成 sections（基於 Markdown 標題）
        
        v1 實作：簡單的標題切割，依據 #, ##, ### 等標記。
        
        Args:
            text: 要切割的文字內容
            book_id: 可選的 book_id（用於生成 section_id）
        
        Returns:
            List of sections，每個 section 包含：
            - section_id: str（例如 "book_01_section_001"）
            - heading: str（標題文字）
            - level: int（標題層級，1=#, 2=##, ...）
            - content: str（該 section 的內容）
            - start_line: int（起始行號）
            - end_line: int（結束行號）
        """
        if not text:
            return []
        
        lines = text.split('\n')
        sections = []
        current_section: Optional[Dict[str, Any]] = None
        section_index = 0
        
        for line_num, line in enumerate(lines, start=1):
            # 檢查是否為標題行（以 # 開頭）
            stripped = line.strip()
            if stripped.startswith('#'):
                # 計算標題層級
                level = 0
                for char in stripped:
                    if char == '#':
                        level += 1
                    else:
                        break
                
                if level > 0:
                    # 保存上一個 section（如果有）
                    if current_section is not None:
                        current_section['end_line'] = line_num - 1
                        sections.append(current_section)
                    
                    # 開始新 section
                    heading_text = stripped[level:].strip()
                    section_index += 1
                    section_id = f"{book_id}_section_{section_index:03d}" if book_id else f"section_{section_index:03d}"
                    
                    current_section = {
                        'section_id': section_id,
                        'heading': heading_text,
                        'level': level,
                        'content': line + '\n',  # 包含標題行
                        'start_line': line_num,
                        'end_line': line_num,  # 暫時，會在遇到下一個標題時更新
                    }
                else:
                    # 不是有效的標題，加入當前 section
                    if current_section is not None:
                        current_section['content'] += line + '\n'
            else:
                # 一般內容行，加入當前 section
                if current_section is not None:
                    current_section['content'] += line + '\n'
                else:
                    # 如果沒有當前 section（檔案開頭沒有標題），創建一個
                    section_index += 1
                    section_id = f"{book_id}_section_{section_index:03d}" if book_id else f"section_{section_index:03d}"
                    current_section = {
                        'section_id': section_id,
                        'heading': '(無標題)',
                        'level': 0,
                        'content': line + '\n',
                        'start_line': line_num,
                        'end_line': line_num,
                    }
        
        # 保存最後一個 section
        if current_section is not None:
            current_section['end_line'] = len(lines)
            sections.append(current_section)
        
        return sections
    
    def load_book_sections(
        self,
        book_id: str,
        version: str = "ENHANCED"
    ) -> List[Dict[str, Any]]:
        """讀取書籍並切割成 sections
        
        Args:
            book_id: 書本 ID
            version: 版本（"STRUCTURED" / "CORRECTED" / "ENHANCED"）
        
        Returns:
            List of sections
        """
        text = self.load_book_text(book_id, version)
        return self.split_book_into_sections(text, book_id=book_id)


# 便利函式
def load_book_text(book_id: str, version: str = "ENHANCED") -> str:
    """便利函式：讀取指定書籍的文字內容"""
    loader = DoctrineLoaderV1()
    return loader.load_book_text(book_id, version)

