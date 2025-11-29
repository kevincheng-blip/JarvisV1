"""因子引擎模組

詳見 spec/JGOD_Python_Interface_Spec.md 的 Factor Engine 章節。
未來實作需參考 structured_books/股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, Any, Literal, Dict, Optional
import pandas as pd
import numpy as np


class FactorEngine(ABC):
    """因子引擎基類
    
    詳見 spec/JGOD_Python_Interface_Spec.md 的 FactorEngine 章節。
    對應文件：股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md
    對應概念：因子計算模組（F_C、F_S、F_D、F_Inertia 等）
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化因子引擎
        
        詳見 spec/JGOD_Python_Interface_Spec.md
        """
        self.config = config
        self.historical_stats: Optional[pd.DataFrame] = None
    
    @abstractmethod
    def compute_factor(self,
                       market_data: pd.DataFrame,
                       xq_data: Optional[Dict[str, Any]] = None,
                       historical_weights: Optional[pd.Series] = None) -> Dict[str, float]:
        """計算單一因子值
        
        詳見 spec/JGOD_Python_Interface_Spec.md 的 compute_factor 方法。
        對應文件：股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md
        """
        pass
    
    def compute_all_factors(self, market_data: pd.DataFrame) -> Dict[str, float]:
        """計算所有啟用的因子
        
        詳見 spec/JGOD_Python_Interface_Spec.md 的 compute_all_factors 方法。
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        """
        pass
    
    def update_historical_stats(self, historical_data: pd.DataFrame) -> None:
        """更新歷史統計資料（用於標準化計算）
        
        詳見 spec/JGOD_Python_Interface_Spec.md 的 update_historical_stats 方法。
        """
        pass

