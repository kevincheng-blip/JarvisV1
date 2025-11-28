"""
因子資料載入模組

定義「因子快取」的資料結構與抽象載入介面。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Protocol, Sequence, Tuple


@dataclass
class FactorCacheEntry:
    """
    單一時間點的因子快取紀錄。
    
    在離線模擬裡，我們假設：
    - capital_flow: 代表一步 F_C 的輸出（至少包含 symbol, timestamp, sai, moi 等欄位）
    - inertia:      代表一步 F_Inertia 的輸出（至少包含 symbol, timestamp, inertia_sai 等欄位）
    
    這裡不強制具體型別，交給上層確保物件結構正確即可。
    """
    timestamp: float
    symbol: str
    capital_flow: Optional[Any] = None
    inertia: Optional[Any] = None


class FactorDataLoader(Protocol):
    """
    因子資料的抽象載入介面。
    
    之後可以有很多實作：
    - 從 CSV / Parquet 讀取
    - 從 SQLite / Redis 讀取
    - 從 FinMind 即時計算後寫入 cache 再讀取
    """
    
    def load_factors_for_period(
        self,
        start_ts: float,
        end_ts: float,
        symbols: Sequence[str],
    ) -> List[FactorCacheEntry]:
        """
        載入指定時間區間內、指定標的的因子快取紀錄。
        
        回傳的 list 不保證排序，呼叫端需要自己依 timestamp 排序。
        """
        ...
    
    def get_factor_instances(
        self, entry: FactorCacheEntry
    ) -> Tuple[Optional[Any], Optional[Any]]:
        """
        從 FactorCacheEntry 中取出因子物件。
        
        在目前版本中：
        - 第 1 個元素預期是 F_C 對應的因子物件
        - 第 2 個元素預期是 F_Inertia 對應的因子物件
        """
        ...

