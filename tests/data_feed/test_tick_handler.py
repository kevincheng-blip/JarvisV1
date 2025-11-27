"""
測試 Tick Handler 模組

測試 UnifiedTick、SinopacConverter、MockSinopacAPI 的功能
"""

import pytest
from data_feed.tick_handler import (
    UnifiedTick,
    BaseTickConverter,
    SinopacConverter,
    MockSinopacAPI,
)


class TestUnifiedTick:
    """測試 UnifiedTick 資料結構"""
    
    def test_create_valid_tick(self):
        """測試建立有效的 UnifiedTick"""
        tick = UnifiedTick(
            timestamp=1234567890.123,
            symbol="2330.TW",
            source="sinopac",
            price=750.0,
            volume=100,
            bid_price=749.5,
            ask_price=750.5,
        )
        assert tick.timestamp == 1234567890.123
        assert tick.symbol == "2330.TW"
        assert tick.price == 750.0
    
    def test_invalid_timestamp(self):
        """測試無效的時間戳"""
        with pytest.raises(ValueError):
            UnifiedTick(
                timestamp=-1,
                symbol="2330.TW",
                source="sinopac",
                price=750.0,
                volume=100,
                bid_price=749.5,
                ask_price=750.5,
            )
    
    def test_invalid_price(self):
        """測試無效的價格"""
        with pytest.raises(ValueError):
            UnifiedTick(
                timestamp=1234567890.123,
                symbol="2330.TW",
                source="sinopac",
                price=-100.0,
                volume=100,
                bid_price=749.5,
                ask_price=750.5,
            )
    
    def test_bid_ask_validation(self):
        """測試買賣價驗證（bid 必須 < ask）"""
        with pytest.raises(ValueError):
            UnifiedTick(
                timestamp=1234567890.123,
                symbol="2330.TW",
                source="sinopac",
                price=750.0,
                volume=100,
                bid_price=750.5,
                ask_price=749.5,
            )


class TestSinopacConverter:
    """測試 SinopacConverter"""
    
    def test_convert_valid_raw_tick(self):
        """測試轉換有效的原始 Tick"""
        converter = SinopacConverter()
        raw_tick = {
            "ts": 1234567890.123,
            "code": "2330",
            "price": 750.0,
            "volume": 100,
            "bid": 749.5,
            "ask": 750.5,
        }
        unified = converter.convert_to_unified(raw_tick)
        assert isinstance(unified, UnifiedTick)
        assert unified.symbol == "2330.TW"
        assert unified.price == 750.0
        assert unified.source == "sinopac"
    
    def test_convert_missing_fields(self):
        """測試缺少必要欄位的情況"""
        converter = SinopacConverter()
        raw_tick = {
            "ts": 1234567890.123,
            "code": "2330",
            # 缺少 price, volume, bid, ask
        }
        with pytest.raises(ValueError):
            converter.convert_to_unified(raw_tick)


class TestMockSinopacAPI:
    """測試 MockSinopacAPI"""
    
    def test_get_next_raw_tick(self):
        """測試取得下一個原始 Tick"""
        mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)
        raw_tick = mock_api.get_next_raw_tick()
        
        assert isinstance(raw_tick, dict)
        assert "ts" in raw_tick
        assert "code" in raw_tick
        assert "price" in raw_tick
        assert "volume" in raw_tick
        assert "bid" in raw_tick
        assert "ask" in raw_tick
        assert raw_tick["code"] == "2330"
        assert raw_tick["source"] == "sinopac_mock"
    
    def test_tick_sequence(self):
        """測試 Tick 序列（時間戳應該遞增）"""
        mock_api = MockSinopacAPI()
        tick1 = mock_api.get_next_raw_tick()
        tick2 = mock_api.get_next_raw_tick()
        
        assert tick2["ts"] > tick1["ts"]
    
    def test_reset(self):
        """測試重置功能"""
        mock_api = MockSinopacAPI(base_price=750.0)
        mock_api.get_next_raw_tick()
        mock_api.get_next_raw_tick()
        
        initial_count = mock_api.tick_count
        mock_api.reset()
        
        assert mock_api.tick_count == 0
        assert mock_api.current_price == 750.0


class TestIntegration:
    """整合測試：Mock API + Converter"""
    
    def test_full_pipeline(self):
        """測試完整流程：Mock API → Converter → UnifiedTick"""
        # 1. 建立 Mock API
        mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)
        
        # 2. 建立 Converter
        converter = SinopacConverter()
        
        # 3. 取得原始 Tick 並轉換
        raw_tick = mock_api.get_next_raw_tick()
        unified_tick = converter.convert_to_unified(raw_tick)
        
        # 4. 驗證結果
        assert isinstance(unified_tick, UnifiedTick)
        assert unified_tick.symbol == "2330.TW"
        assert unified_tick.source == "sinopac"
        assert unified_tick.price > 0
        assert unified_tick.volume > 0
        assert unified_tick.bid_price < unified_tick.ask_price

