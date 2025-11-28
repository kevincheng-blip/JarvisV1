"""
Tick Handler：統一處理多家 API 來源的 Tick 資料

本模組提供：
1. UnifiedTick：統一的 Tick 數據結構
2. BaseTickConverter：抽象基底類別，規範不同 API 來源的轉換流程
3. SinopacConverter：永豐 API 的轉換器（目前為骨架，待正式 API 文件）
4. MockSinopacAPI：模擬永豐 API 的資料來源（用於開發與測試）

作者：創世紀量化系統開發團隊
版本：v1.0
建立日期：2024-11-28
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any
import time
import random


# ============================================================================
# 任務一：定義統一的 Tick 數據結構（UnifiedTick）
# ============================================================================

@dataclass
class UnifiedTick:
    """
    統一的 Tick 數據結構
    
    此資料結構將作為全系統標準 Tick 格式，
    所有來源（Sinopac / XQ / Polygon / Mock）最終都要轉成這個格式。
    
    Attributes:
        timestamp: 納秒級 Unix 時間戳（或以 float 表示的精確時間）
        symbol: 股票代號，例如："2330.TW", "AAPL" 等
        source: 資料來源，例如："sinopac", "xq", "polygon_mock"
        price: 成交價格
        volume: 成交量
        bid_price: 買價（五檔第一檔）
        ask_price: 賣價（五檔第一檔）
    """
    timestamp: float
    symbol: str
    source: str
    price: float
    volume: int
    bid_price: float
    ask_price: float
    
    def __post_init__(self):
        """驗證數據完整性"""
        if self.timestamp <= 0:
            raise ValueError(f"Invalid timestamp: {self.timestamp}")
        if self.price <= 0:
            raise ValueError(f"Invalid price: {self.price}")
        if self.volume < 0:
            raise ValueError(f"Invalid volume: {self.volume}")
        if self.bid_price <= 0 or self.ask_price <= 0:
            raise ValueError(f"Invalid bid/ask prices: bid={self.bid_price}, ask={self.ask_price}")
        if self.bid_price >= self.ask_price:
            raise ValueError(f"Bid price ({self.bid_price}) should be less than ask price ({self.ask_price})")


# ============================================================================
# 任務二：建立 Tick 校準與轉換的基底類別（BaseTickConverter）
# ============================================================================

class BaseTickConverter(ABC):
    """
    抽象基底類別：規範「不同 API / 資料源 → UnifiedTick」的轉換流程
    
    所有具體的 API Converter（SinopacConverter、XQConverter、PolygonConverter 等）
    都必須繼承此類別並實作 convert_to_unified 方法。
    """
    
    @abstractmethod
    def convert_to_unified(self, raw_data: Dict[str, Any]) -> UnifiedTick:
        """
        將原始 Tick 數據轉換為 UnifiedTick 格式
        
        Args:
            raw_data: 各來源的原始 Tick 結構（Sinopac / Mock / 未來 XQ/Polygon）
        
        Returns:
            UnifiedTick: 標準化的 Tick 數據結構
        
        Raises:
            ValueError: 當 raw_data 格式不正確或缺少必要欄位時
        """
        pass
    
    def validate_raw_data(self, raw_data: Dict[str, Any], required_fields: list) -> bool:
        """
        驗證原始數據是否包含必要欄位
        
        Args:
            raw_data: 原始數據字典
            required_fields: 必要欄位列表
        
        Returns:
            bool: True 表示驗證通過，False 表示缺少必要欄位
        """
        if not isinstance(raw_data, dict):
            return False
        return all(field in raw_data for field in required_fields)


# ============================================================================
# 任務三：Sinopac Converter 骨架 ＋ Mock 資料來源
# ============================================================================

class SinopacConverter(BaseTickConverter):
    """
    永豐 Sinopac API 的 Tick 數據轉換器
    
    目前為骨架版本，待正式 API 文件後再完善欄位映射邏輯。
    
    預期 Sinopac 原始數據格式（待確認）：
    {
        "ts": <float，時間戳>,
        "code": <str，股票代號>,
        "price": <float，成交價格>,
        "volume": <int，成交量>,
        "bid": <float，買價>,
        "ask": <float，賣價>,
        ...
    }
    """
    
    def __init__(self):
        """初始化 Sinopac Converter"""
        self.source_name = "sinopac"
    
    def convert_to_unified(self, raw_data: Dict[str, Any]) -> UnifiedTick:
        """
        將 Sinopac 原始 Tick 數據轉換為 UnifiedTick
        
        Args:
            raw_data: Sinopac API 的原始 Tick 數據
        
        Returns:
            UnifiedTick: 標準化的 Tick 數據結構
        
        Raises:
            ValueError: 當 raw_data 格式不正確或缺少必要欄位時
        
        TODO:
            - 實作 Sinopac 原始欄位 → UnifiedTick 映射
            - 確認 Sinopac API 實際欄位名稱
            - 處理時間戳格式轉換（可能需要時區轉換）
            - 處理股票代號格式（例如：需要加上 ".TW" 後綴）
        """
        # 驗證必要欄位
        required_fields = ["ts", "code", "price", "volume", "bid", "ask"]
        if not self.validate_raw_data(raw_data, required_fields):
            raise ValueError(f"Missing required fields in Sinopac raw_data: {raw_data}")
        
        # TODO: 實作 Sinopac 原始欄位 → UnifiedTick 映射
        # 目前先用示意的欄位映射（待正式 API 文件確認後修正）
        
        # 時間戳處理（假設 raw_data["ts"] 是 Unix 時間戳）
        timestamp = float(raw_data.get("ts", time.time()))
        
        # 股票代號處理（假設需要加上 ".TW" 後綴）
        code = str(raw_data.get("code", ""))
        symbol = f"{code}.TW" if not code.endswith(".TW") else code
        
        # 價格與成交量
        price = float(raw_data.get("price", 0.0))
        volume = int(raw_data.get("volume", 0))
        
        # 買賣價
        bid_price = float(raw_data.get("bid", 0.0))
        ask_price = float(raw_data.get("ask", 0.0))
        
        # 建立 UnifiedTick
        unified_tick = UnifiedTick(
            timestamp=timestamp,
            symbol=symbol,
            source=self.source_name,
            price=price,
            volume=volume,
            bid_price=bid_price,
            ask_price=ask_price,
        )
        
        return unified_tick


class MockSinopacAPI:
    """
    模擬永豐 Sinopac API 的資料來源
    
    用於在無正式 API 金鑰前提供測試資料，讓 Pipeline 可以跑起來。
    
    此類別會產生結構類似 Sinopac 原始 Tick 的假資料，
    之後只需要修改 SinopacConverter 的 convert_to_unified，
    就可以無痛切換真實 API。
    """
    
    def __init__(self, symbol: str = "2330", base_price: float = 750.0, price_range: float = 10.0):
        """
        初始化 Mock Sinopac API
        
        Args:
            symbol: 股票代號（例如："2330"）
            base_price: 基礎價格（價格會在此基礎上隨機波動）
            price_range: 價格波動範圍（±price_range）
        """
        self.symbol = symbol
        self.base_price = base_price
        self.price_range = price_range
        self.current_price = base_price
        self.current_time = time.time()
        self.tick_count = 0
    
    def get_next_raw_tick(self) -> Dict[str, Any]:
        """
        取得下一個模擬的原始 Tick 數據
        
        每次呼叫時，回傳一個「結構類似 Sinopac 原始 Tick」的 dict。
        
        Returns:
            dict: 模擬的 Sinopac 原始 Tick 數據
                {
                    "ts": <float，模擬的時間戳>,
                    "code": <str，股票代號>,
                    "price": <float，成交價格>,
                    "volume": <int，成交量>,
                    "bid": <float，買價>,
                    "ask": <float，賣價>,
                    "source": "sinopac_mock"
                }
        """
        # 更新時間戳（每次增加 0.1 秒，模擬真實 Tick 間隔）
        self.current_time += 0.1
        self.tick_count += 1
        
        # 價格隨機波動（在 base_price ± price_range 範圍內）
        price_change = random.uniform(-self.price_range, self.price_range)
        self.current_price = max(0.01, self.base_price + price_change)
        
        # 買賣價（買價略低於成交價，賣價略高於成交價）
        spread = random.uniform(0.1, 0.5)  # 價差 0.1~0.5
        bid_price = self.current_price - spread / 2
        ask_price = self.current_price + spread / 2
        
        # 成交量（隨機，範圍 1~1000）
        volume = random.randint(1, 1000)
        
        # 建立模擬的原始 Tick 數據
        raw_tick = {
            "ts": self.current_time,
            "code": self.symbol,
            "price": round(self.current_price, 2),
            "volume": volume,
            "bid": round(bid_price, 2),
            "ask": round(ask_price, 2),
            "source": "sinopac_mock",
        }
        
        return raw_tick
    
    def reset(self, base_price: float = None):
        """
        重置模擬器狀態
        
        Args:
            base_price: 新的基礎價格（可選）
        """
        if base_price is not None:
            self.base_price = base_price
        # 無論是否傳入 base_price，都要重置 current_price 為 base_price
        self.current_price = self.base_price
        self.current_time = time.time()
        self.tick_count = 0


# ============================================================================
# 使用範例與測試輔助函數
# ============================================================================

def example_usage():
    """
    使用範例：展示如何使用 MockSinopacAPI 和 SinopacConverter
    """
    # 1. 建立 Mock API
    mock_api = MockSinopacAPI(symbol="2330", base_price=750.0, price_range=10.0)
    
    # 2. 建立 Converter
    converter = SinopacConverter()
    
    # 3. 取得模擬的原始 Tick 並轉換為 UnifiedTick
    for i in range(5):
        raw_tick = mock_api.get_next_raw_tick()
        print(f"\n原始 Tick {i+1}: {raw_tick}")
        
        unified_tick = converter.convert_to_unified(raw_tick)
        print(f"統一格式: {unified_tick}")


if __name__ == "__main__":
    # 執行使用範例
    example_usage()

