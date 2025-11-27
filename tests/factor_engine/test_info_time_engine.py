"""
測試 InfoTimeBarGenerator 模組

測試 VolumeBar 生成、VWAP 計算、F_InfoTime 因子計算等功能
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from data_feed.tick_handler import UnifiedTick, MockSinopacAPI, SinopacConverter
from factor_engine.info_time_engine import VolumeBar, InfoTimeBarGenerator


class TestVolumeBar:
    """測試 VolumeBar 資料結構"""
    
    def test_create_valid_volume_bar(self):
        """測試建立有效的 VolumeBar"""
        bar = VolumeBar(
            start_ts=1234567890.0,
            end_ts=1234567900.0,
            symbol="2330.TW",
            vwap=750.0,
            total_volume=5000,
            tick_count=10,
            open_price=745.0,
            high_price=755.0,
            low_price=745.0,
            close_price=750.0,
            avg_bid=749.5,
            avg_ask=750.5,
        )
        assert bar.symbol == "2330.TW"
        assert bar.vwap == 750.0
        assert bar.total_volume == 5000
    
    def test_invalid_time_range(self):
        """測試無效的時間範圍"""
        try:
            VolumeBar(
                start_ts=1234567900.0,
                end_ts=1234567890.0,  # end < start
                symbol="2330.TW",
                vwap=750.0,
                total_volume=5000,
                tick_count=10,
                open_price=745.0,
                high_price=755.0,
                low_price=745.0,
                close_price=750.0,
                avg_bid=749.5,
                avg_ask=750.5,
            )
            assert False, "Should raise ValueError"
        except ValueError:
            pass  # 預期會拋出錯誤


class TestInfoTimeBarGenerator:
    """測試 InfoTimeBarGenerator"""
    
    def test_add_tick_and_generate_bar(self):
        """測試新增 Tick 並產生 VolumeBar"""
        generator = InfoTimeBarGenerator(volume_bar_size=1000)  # 測試用小值
        
        mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)
        converter = SinopacConverter()
        
        # 新增多個 Tick，直到產生 VolumeBar
        volume_bar = None
        tick_count = 0
        
        while volume_bar is None and tick_count < 100:
            raw_tick = mock_api.get_next_raw_tick()
            unified_tick = converter.convert_to_unified(raw_tick)
            volume_bar = generator.add_tick(unified_tick)
            tick_count += 1
        
        assert volume_bar is not None, "Should generate a VolumeBar"
        assert isinstance(volume_bar, VolumeBar)
        assert volume_bar.symbol == "2330.TW"
        assert volume_bar.total_volume >= 1000
        assert volume_bar.vwap > 0
        assert volume_bar.tick_count > 0
    
    def test_vwap_calculation(self):
        """測試 VWAP 計算正確性"""
        generator = InfoTimeBarGenerator(volume_bar_size=1000)
        
        # 手動建立測試 Tick
        ticks = [
            UnifiedTick(
                timestamp=1000.0 + i * 0.1,
                symbol="2330.TW",
                source="test",
                price=750.0,
                volume=500,
                bid_price=749.5,
                ask_price=750.5,
            )
            for i in range(3)
        ]
        
        # 新增 Tick
        for tick in ticks:
            generator.add_tick(tick)
        
        # 手動計算預期 VWAP
        total_pv = sum(t.price * t.volume for t in ticks)
        total_vol = sum(t.volume for t in ticks)
        expected_vwap = total_pv / total_vol
        
        # 產生 VolumeBar（需要達到目標成交量）
        # 由於我們只有 1500 volume，應該會產生一個 Bar
        volume_bar = None
        for tick in ticks:
            volume_bar = generator.add_tick(tick)
            if volume_bar:
                break
        
        # 如果還沒產生，繼續添加
        if volume_bar is None:
            # 添加更多 Tick 直到產生 Bar
            for i in range(10):
                extra_tick = UnifiedTick(
                    timestamp=1000.0 + (3 + i) * 0.1,
                    symbol="2330.TW",
                    source="test",
                    price=750.0,
                    volume=200,
                    bid_price=749.5,
                    ask_price=750.5,
                )
                volume_bar = generator.add_tick(extra_tick)
                if volume_bar:
                    break
        
        assert volume_bar is not None
        # VWAP 應該接近 750.0（所有價格都是 750.0）
        assert abs(volume_bar.vwap - 750.0) < 1.0
    
    def test_infotime_factor_calculation(self):
        """測試 F_InfoTime 因子計算"""
        generator = InfoTimeBarGenerator(volume_bar_size=500)  # 小值以便快速產生 Bar
        
        mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)
        converter = SinopacConverter()
        
        # 產生至少 3 個 VolumeBar（需要至少 2 個間隔才能計算 F_InfoTime）
        bar_count = 0
        for i in range(200):
            raw_tick = mock_api.get_next_raw_tick()
            unified_tick = converter.convert_to_unified(raw_tick)
            volume_bar = generator.add_tick(unified_tick)
            
            if volume_bar:
                bar_count += 1
                if bar_count >= 3:
                    infotime = generator.calculate_infotime_factor()
                    assert infotime > 0, "F_InfoTime should be positive"
                    break
    
    def test_get_current_bar_progress(self):
        """測試取得當前 Bar 進度"""
        generator = InfoTimeBarGenerator(volume_bar_size=1000)
        
        # 初始狀態
        progress = generator.get_current_bar_progress()
        assert progress["status"] == "no_bar"
        assert progress["progress"] == 0.0
        
        # 新增一些 Tick
        mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)
        converter = SinopacConverter()
        
        for i in range(5):
            raw_tick = mock_api.get_next_raw_tick()
            unified_tick = converter.convert_to_unified(raw_tick)
            generator.add_tick(unified_tick)
        
        progress = generator.get_current_bar_progress()
        assert progress["status"] == "accumulating"
        assert 0.0 < progress["progress"] < 1.0
        assert progress["volume"] > 0
        assert progress["tick_count"] > 0
    
    def test_get_recent_bars(self):
        """測試取得最近的 VolumeBar"""
        generator = InfoTimeBarGenerator(volume_bar_size=500)
        
        mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)
        converter = SinopacConverter()
        
        # 產生多個 VolumeBar
        bar_count = 0
        for i in range(200):
            raw_tick = mock_api.get_next_raw_tick()
            unified_tick = converter.convert_to_unified(raw_tick)
            volume_bar = generator.add_tick(unified_tick)
            
            if volume_bar:
                bar_count += 1
                if bar_count >= 5:
                    break
        
        # 取得最近的 Bar
        recent_bars = generator.get_recent_bars(n=3)
        assert len(recent_bars) <= 3
        assert all(isinstance(bar, VolumeBar) for bar in recent_bars)
    
    def test_reset(self):
        """測試重置功能"""
        generator = InfoTimeBarGenerator(volume_bar_size=500)
        
        mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)
        converter = SinopacConverter()
        
        # 產生一些 Bar
        for i in range(100):
            raw_tick = mock_api.get_next_raw_tick()
            unified_tick = converter.convert_to_unified(raw_tick)
            generator.add_tick(unified_tick)
        
        # 重置
        generator.reset()
        
        # 驗證狀態已重置
        progress = generator.get_current_bar_progress()
        assert progress["status"] == "no_bar"
        assert len(generator.completed_bars) == 0


class TestIntegration:
    """整合測試：Mock API → Converter → InfoTimeBarGenerator"""
    
    def test_full_pipeline(self):
        """測試完整流程"""
        # 1. 建立 Mock API 和 Converter
        mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)
        converter = SinopacConverter()
        
        # 2. 建立 Volume Bar 生成器
        generator = InfoTimeBarGenerator(volume_bar_size=1000)
        
        # 3. 處理多個 Tick
        volume_bars = []
        for i in range(100):
            raw_tick = mock_api.get_next_raw_tick()
            unified_tick = converter.convert_to_unified(raw_tick)
            volume_bar = generator.add_tick(unified_tick)
            
            if volume_bar:
                volume_bars.append(volume_bar)
                if len(volume_bars) >= 3:
                    break
        
        # 4. 驗證結果
        assert len(volume_bars) >= 3, "Should generate at least 3 VolumeBars"
        assert all(bar.symbol == "2330.TW" for bar in volume_bars)
        assert all(bar.vwap > 0 for bar in volume_bars)
        assert all(bar.total_volume >= 1000 for bar in volume_bars)
        
        # 5. 計算 F_InfoTime
        infotime = generator.calculate_infotime_factor()
        assert infotime > 0


if __name__ == "__main__":
    # 簡單測試執行
    print("=== 執行單元測試 ===")
    
    test_generator = TestInfoTimeBarGenerator()
    
    print("\n1. 測試 add_tick_and_generate_bar...")
    test_generator.test_add_tick_and_generate_bar()
    print("   ✓ 通過")
    
    print("\n2. 測試 get_current_bar_progress...")
    test_generator.test_get_current_bar_progress()
    print("   ✓ 通過")
    
    print("\n3. 測試 infotime_factor_calculation...")
    test_generator.test_infotime_factor_calculation()
    print("   ✓ 通過")
    
    print("\n4. 測試 reset...")
    test_generator.test_reset()
    print("   ✓ 通過")
    
    print("\n5. 測試完整流程...")
    test_integration = TestIntegration()
    test_integration.test_full_pipeline()
    print("   ✓ 通過")
    
    print("\n✅ 所有測試通過！")

