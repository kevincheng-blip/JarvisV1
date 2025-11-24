"""
價格快取機制：減少 API 呼叫次數
"""
from typing import Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path
import json
import hashlib

import pandas as pd


class PriceCache:
    """
    價格快取管理器
    
    功能：
    - 快取股票價格資料
    - 自動過期機制
    - 檔案快取支援
    """
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_hours: int = 1):
        """
        初始化快取管理器
        
        Args:
            cache_dir: 快取目錄，如果為 None 則使用記憶體快取
            ttl_hours: 快取有效期（小時）
        """
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.ttl_hours = ttl_hours
        self._memory_cache: Dict[str, Dict] = {}
    
    def _get_cache_key(self, market: str, symbol: str, start_date: str, end_date: str) -> str:
        """產生快取鍵值"""
        key_str = f"{market}:{symbol}:{start_date}:{end_date}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Optional[Path]:
        """取得快取檔案路徑"""
        if not self.cache_dir:
            return None
        return self.cache_dir / f"{cache_key}.json"
    
    def get(
        self,
        market: str,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> Optional[pd.DataFrame]:
        """
        從快取取得資料
        
        Args:
            market: 市場（taiwan 或 us）
            symbol: 股票代號
            start_date: 開始日期
            end_date: 結束日期
        
        Returns:
            如果快取有效則回傳 DataFrame，否則回傳 None
        """
        cache_key = self._get_cache_key(market, symbol, start_date, end_date)
        
        # 檢查記憶體快取
        if cache_key in self._memory_cache:
            cached_data = self._memory_cache[cache_key]
            if self._is_valid(cached_data["timestamp"]):
                return pd.DataFrame(cached_data["data"])
        
        # 檢查檔案快取
        cache_path = self._get_cache_path(cache_key)
        if cache_path and cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    if self._is_valid(cached_data["timestamp"]):
                        # 同時更新記憶體快取
                        self._memory_cache[cache_key] = cached_data
                        return pd.DataFrame(cached_data["data"])
            except Exception:
                pass
        
        return None
    
    def set(
        self,
        market: str,
        symbol: str,
        start_date: str,
        end_date: str,
        data: pd.DataFrame,
    ) -> None:
        """
        將資料寫入快取
        
        Args:
            market: 市場
            symbol: 股票代號
            start_date: 開始日期
            end_date: 結束日期
            data: 要快取的資料
        """
        cache_key = self._get_cache_key(market, symbol, start_date, end_date)
        
        # 準備快取資料
        cached_data = {
            "timestamp": datetime.now().isoformat(),
            "data": data.to_dict("records") if not data.empty else [],
        }
        
        # 寫入記憶體快取
        self._memory_cache[cache_key] = cached_data
        
        # 寫入檔案快取
        cache_path = self._get_cache_path(cache_key)
        if cache_path:
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(cached_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
    
    def _is_valid(self, timestamp_str: str) -> bool:
        """檢查快取是否有效"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            age = datetime.now() - timestamp
            return age < timedelta(hours=self.ttl_hours)
        except Exception:
            return False
    
    def clear(self) -> None:
        """清除所有快取"""
        self._memory_cache.clear()
        if self.cache_dir:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except Exception:
                    pass

