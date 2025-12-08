"""
Doctrine Registry v1

註冊所有 14 本聖經檔案的 metadata，提供查詢介面。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class DoctrineBookMeta:
    """Doctrine Book Metadata
    
    代表一本聖經的完整資訊，包括所有版本的檔案路徑。
    """
    book_id: str  # book_01 ~ book_14
    title: str
    description: str
    category: str  # SYSTEM_PHILOSOPHY / RISK / RL_REWARD / WALKFORWARD / ERROR_LEARNING
    structured_path: Optional[str] = None
    corrected_path: Optional[str] = None
    enhanced_path: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def get_path(self, version: str = "STRUCTURED") -> Optional[str]:
        """根據版本取得檔案路徑
        
        Args:
            version: "STRUCTURED" / "CORRECTED" / "ENHANCED"
        
        Returns:
            檔案路徑，如果不存在則返回 None
        """
        version = version.upper()
        if version == "STRUCTURED":
            return self.structured_path
        elif version == "CORRECTED":
            return self.corrected_path
        elif version == "ENHANCED":
            return self.enhanced_path
        else:
            return None


# 專案根目錄（用於建構完整路徑）
_PROJECT_ROOT = Path(__file__).parent.parent.parent


def _get_full_path(relative_path: str) -> str:
    """將相對路徑轉換為完整路徑"""
    return str(_PROJECT_ROOT / relative_path)


# Doctrine Registry v1：14 本核心聖經
DOCTRINE_REGISTRY_V1: Dict[str, DoctrineBookMeta] = {
    "book_01": DoctrineBookMeta(
        book_id="book_01",
        title="J-GOD 股市聖經系統1",
        description="核心系統設計與哲學",
        category="SYSTEM_PHILOSOPHY",
        structured_path=_get_full_path("structured_books/J-GOD 股市聖經系統1_AI知識庫版_v1_STRUCTURED.md"),
        corrected_path=_get_full_path("structured_books/J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md"),
        enhanced_path=_get_full_path("structured_books/J-GOD 股市聖經系統1_AI知識庫版_v1_ENHANCED.md"),
        tags=["system", "core", "philosophy"],
    ),
    "book_02": DoctrineBookMeta(
        book_id="book_02",
        title="股神腦系統具體化設計",
        description="股神腦系統具體化設計，核心大腦設計（~8788 行）",
        category="SYSTEM_PHILOSOPHY",
        structured_path=_get_full_path("structured_books/股神腦系統具體化設計_AI知識庫版_v1_STRUCTURED.md"),
        corrected_path=_get_full_path("structured_books/股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md"),
        enhanced_path=_get_full_path("structured_books/股神腦系統具體化設計_AI知識庫版_v1_ENHANCED.md"),
        tags=["system", "brain", "design", "factor"],
    ),
    "book_03": DoctrineBookMeta(
        book_id="book_03",
        title="股市大自然萬物修復法則",
        description="股市大自然萬物修復法則，系統哲學",
        category="SYSTEM_PHILOSOPHY",
        structured_path=_get_full_path("structured_books/股市大自然萬物修復法則_AI知識庫版_v1_STRUCTURED.md"),
        corrected_path=_get_full_path("structured_books/股市大自然萬物修復法則_AI知識庫版_v1_CORRECTED.md"),
        enhanced_path=_get_full_path("structured_books/股市大自然萬物修復法則_AI知識庫版_v1_ENHANCED.md"),
        tags=["system", "philosophy", "reversion"],
    ),
    "book_04": DoctrineBookMeta(
        book_id="book_04",
        title="股市聖經二",
        description="股市聖經系列第二本，系統哲學",
        category="SYSTEM_PHILOSOPHY",
        structured_path=_get_full_path("structured_books/股市聖經二_AI知識庫版_v1_STRUCTURED.md"),
        corrected_path=_get_full_path("structured_books/股市聖經二_AI知識庫版_v1_CORRECTED.md"),
        enhanced_path=_get_full_path("structured_books/股市聖經二_AI知識庫版_v1_ENHANCED.md"),
        tags=["system", "philosophy", "bible"],
    ),
    "book_05": DoctrineBookMeta(
        book_id="book_05",
        title="股市聖經三",
        description="股市聖經系列第三本，系統哲學",
        category="SYSTEM_PHILOSOPHY",
        structured_path=_get_full_path("structured_books/股市聖經三_AI知識庫版_v1_STRUCTURED.md"),
        corrected_path=_get_full_path("structured_books/股市聖經三_AI知識庫版_v1_CORRECTED.md"),
        enhanced_path=_get_full_path("structured_books/股市聖經三_AI知識庫版_v1_ENHANCED.md"),
        tags=["system", "philosophy", "bible"],
    ),
    "book_06": DoctrineBookMeta(
        book_id="book_06",
        title="股市聖經四",
        description="股市聖經系列第四本，系統哲學",
        category="SYSTEM_PHILOSOPHY",
        structured_path=_get_full_path("structured_books/股市聖經四_AI知識庫版_v1_STRUCTURED.md"),
        corrected_path=_get_full_path("structured_books/股市聖經四_AI知識庫版_v1_CORRECTED.md"),
        enhanced_path=_get_full_path("structured_books/股市聖經四_AI知識庫版_v1_ENHANCED.md"),
        tags=["system", "philosophy", "bible"],
    ),
    "book_07": DoctrineBookMeta(
        book_id="book_07",
        title="J-GOD 股票交易聖經 v1.0",
        description="J-GOD 股票交易聖經，風控總綱",
        category="RISK",
        structured_path=_get_full_path("structured_books/JGOD_STOCK_TRADING_BIBLE_v1_AI知識庫版_v1_STRUCTURED.md"),
        corrected_path=_get_full_path("structured_books/JGOD_STOCK_TRADING_BIBLE_v1_AI知識庫版_v1_CORRECTED.md"),
        enhanced_path=_get_full_path("structured_books/JGOD_STOCK_TRADING_BIBLE_v1_AI知識庫版_v1_ENHANCED.md"),
        tags=["risk", "trading", "bible"],
    ),
    "book_08": DoctrineBookMeta(
        book_id="book_08",
        title="雙引擎與自主演化閉環",
        description="雙引擎與自主演化閉環設計，RL & Reward",
        category="RL_REWARD",
        structured_path=_get_full_path("structured_books/雙引擎與自主演化閉環_AI知識庫版_v1_STRUCTURED.md"),
        corrected_path=_get_full_path("structured_books/雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md"),
        enhanced_path=_get_full_path("structured_books/雙引擎與自主演化閉環_AI知識庫版_v1_ENHANCED.md"),
        tags=["rl", "reward", "evolution", "policy"],
    ),
    "book_09": DoctrineBookMeta(
        book_id="book_09",
        title="Path A 歷史回測撈取資料＋分析",
        description="Path A 歷史回測撈取資料＋分析規範",
        category="WALKFORWARD",
        structured_path=_get_full_path("structured_books/Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_STRUCTURED.md"),
        corrected_path=_get_full_path("structured_books/Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md"),
        enhanced_path=_get_full_path("structured_books/Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_ENHANCED.md"),
        tags=["backtest", "path_a", "walkforward"],
    ),
    "book_10": DoctrineBookMeta(
        book_id="book_10",
        title="滾動式分析",
        description="滾動式分析（Walk-Forward Analysis）",
        category="WALKFORWARD",
        structured_path=_get_full_path("structured_books/滾動式分析_AI知識庫版_v1_STRUCTURED.md"),
        corrected_path=_get_full_path("structured_books/滾動式分析_AI知識庫版_v1_CORRECTED.md"),
        enhanced_path=_get_full_path("structured_books/滾動式分析_AI知識庫版_v1_ENHANCED.md"),
        tags=["walkforward", "analysis", "backtest"],
    ),
    "book_11": DoctrineBookMeta(
        book_id="book_11",
        title="J-GOD 邏輯系統補充",
        description="J-GOD 邏輯系統補充，錯誤學習",
        category="ERROR_LEARNING",
        structured_path=_get_full_path("structured_books/J-GOD 邏輯系統補充_AI知識庫版_v1_STRUCTURED.md"),
        corrected_path=_get_full_path("structured_books/J-GOD 邏輯系統補充_AI知識庫版_v1_CORRECTED.md"),
        enhanced_path=_get_full_path("structured_books/J-GOD 邏輯系統補充_AI知識庫版_v1_ENHANCED.md"),
        tags=["error", "learning", "logic"],
    ),
    "book_12": DoctrineBookMeta(
        book_id="book_12",
        title="邏輯版操作說明書",
        description="邏輯版操作說明書，錯誤學習",
        category="ERROR_LEARNING",
        structured_path=_get_full_path("structured_books/邏輯版操作說明書_AI知識庫版_v1_STRUCTURED.md"),
        corrected_path=_get_full_path("structured_books/邏輯版操作說明書_AI知識庫版_v1_CORRECTED.md"),
        enhanced_path=_get_full_path("structured_books/邏輯版操作說明書_AI知識庫版_v1_ENHANCED.md"),
        tags=["error", "learning", "manual"],
    ),
    "book_13": DoctrineBookMeta(
        book_id="book_13",
        title="JGOD 原始開發藍圖清整強化版",
        description="JGOD 原始開發藍圖清整強化版，系統哲學",
        category="SYSTEM_PHILOSOPHY",
        structured_path=_get_full_path("structured_books/JGOD_原始開發藍圖_清整強化版_AI知識庫版_v1_STRUCTURED.md"),
        corrected_path=_get_full_path("structured_books/JGOD_原始開發藍圖_清整強化版_AI知識庫版_v1_CORRECTED.md"),
        enhanced_path=_get_full_path("structured_books/JGOD_原始開發藍圖_清整強化版_AI知識庫版_v1_ENHANCED.md"),
        tags=["system", "blueprint", "philosophy"],
    ),
    "book_14": DoctrineBookMeta(
        book_id="book_14",
        title="J-GOD Book Complete v1",
        description="J-GOD Book Complete v1，完整版彙整",
        category="SYSTEM_PHILOSOPHY",
        structured_path=_get_full_path("structured_books/J-GOD_Book_Complete_v1_AI知識庫版_v1_STRUCTURED.md"),
        corrected_path=_get_full_path("structured_books/J-GOD_Book_Complete_v1_AI知識庫版_v1_CORRECTED.md"),
        enhanced_path=_get_full_path("structured_books/J-GOD_Book_Complete_v1_AI知識庫版_v1_ENHANCED.md"),
        tags=["system", "complete", "philosophy"],
    ),
}


class DoctrineRegistryV1:
    """Doctrine Registry v1
    
    提供查詢已註冊聖經 metadata 的介面。
    """
    
    def __init__(self, registry: Optional[Dict[str, DoctrineBookMeta]] = None):
        """初始化 Registry
        
        Args:
            registry: 自訂的 registry，預設使用 DOCTRINE_REGISTRY_V1
        """
        self._registry = registry if registry is not None else DOCTRINE_REGISTRY_V1.copy()
    
    def get_book_meta(self, book_id: str) -> Optional[DoctrineBookMeta]:
        """取得指定 book_id 的 metadata
        
        Args:
            book_id: 書本 ID（book_01 ~ book_14）
        
        Returns:
            DoctrineBookMeta 或 None（如果不存在）
        """
        return self._registry.get(book_id)
    
    def list_books(self, category: Optional[str] = None) -> List[DoctrineBookMeta]:
        """列出所有書籍，可選按 category 過濾
        
        Args:
            category: 可選的 category 過濾（如 "SYSTEM_PHILOSOPHY"）
        
        Returns:
            符合條件的書籍列表
        """
        books = list(self._registry.values())
        if category:
            books = [b for b in books if b.category == category]
        return sorted(books, key=lambda x: x.book_id)
    
    def get_all_book_ids(self) -> List[str]:
        """取得所有 book_id 列表"""
        return sorted(self._registry.keys())
    
    def has_book(self, book_id: str) -> bool:
        """檢查 book_id 是否存在"""
        return book_id in self._registry


# 便利函式
def get_book_meta(book_id: str) -> Optional[DoctrineBookMeta]:
    """便利函式：取得指定 book_id 的 metadata"""
    registry = DoctrineRegistryV1()
    return registry.get_book_meta(book_id)


def list_books(category: Optional[str] = None) -> List[DoctrineBookMeta]:
    """便利函式：列出所有書籍，可選按 category 過濾"""
    registry = DoctrineRegistryV1()
    return registry.list_books(category=category)

