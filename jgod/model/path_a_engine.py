"""
# LEGACY: do not use for new development

此檔案為舊版 Path A Engine 定義，目前未被使用。
實際的 Path A 實作位於 jgod/path_a/ 目錄下。

Path A 的正確使用方式：
- 使用 jgod.path_a.path_a_backtest.run_path_a_backtest()
- 使用 jgod.path_a 下的資料結構與模組

此檔案保留僅為向後相容性，新開發請勿使用。

Path A 歷史回測資料引擎模組

詳見 spec/JGOD_Python_Interface_Spec.md 的 Path A Engine 章節。
未來實作需參考 structured_books/Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Any, Literal, Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd


class PathAEngine:
    """Path A 歷史回測資料引擎
    
    詳見 spec/JGOD_Python_Interface_Spec.md 的 PathAEngine 章節。
    對應文件：Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md
    對應概念：歷史資料撈取清單、必須撈取的欄位、還原股價的重要性
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化 Path A 引擎
        
        詳見 spec/JGOD_Python_Interface_Spec.md
        """
        self.config = config
    
    def fetch_historical_data(self,
                             symbols: List[str],
                             start_date: datetime,
                             end_date: datetime,
                             fields: Optional[List[str]] = None) -> pd.DataFrame:
        """撈取歷史資料
        
        詳見 spec/JGOD_Python_Interface_Spec.md 的 fetch_historical_data 方法。
        對應文件：Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md
        對應概念：必須撈取的欄位（Date、Adjusted Close Price、Open Price、Low Price、Trading Volume）
        
        關鍵要求：
        - 必須使用 Adjusted Close Price（還原收盤價）避免除權息影響
        - 必須是交易日序列，且無跳日
        """
        pass
    
    def adjust_price_for_dividend(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """還原股價（處理除權息）
        
        詳見 spec/JGOD_Python_Interface_Spec.md 的 adjust_price_for_dividend 方法。
        對應文件：Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md
        對應概念：還原股價的重要性
        """
        pass
    
    def validate_data_integrity(self, data: pd.DataFrame) -> Dict[str, bool]:
        """驗證資料完整性
        
        詳見 spec/JGOD_Python_Interface_Spec.md 的 validate_data_integrity 方法。
        對應文件：Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md
        對應概念：嚴格時間戳記隔離原則、確保無未來資料洩漏
        """
        pass

