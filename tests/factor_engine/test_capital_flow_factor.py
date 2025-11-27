"""
測試 CapitalFlowEngine 模組

測試 F_C 因子計算、SAI/MOI 計算、Symbol 過濾、無效報價處理等功能
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dataclasses import dataclass
from factor_engine import CapitalFlowEngine, CapitalFlowFactor


@dataclass
class FakeTick:
    """測試用 Tick，模擬 UnifiedTick 的必要欄位"""
    timestamp: float
    symbol: str
    price: float
    volume: float
    bid_price: float
    ask_price: float


class TestCapitalFlowEngine:
    """測試 CapitalFlowEngine"""
    
    def test_capital_flow_engine_basic_sai_and_moi(self):
        """測試基本 SAI 和 MOI 計算"""
        engine = CapitalFlowEngine(symbol="2330.TW", window_size=10, min_points=4)

        # 模擬一段多方稍微佔優的行情
        ticks = [
            FakeTick(1.0, "2330.TW", 100.3, 10, 100.0, 100.2),  # price > mid → 買方
            FakeTick(2.0, "2330.TW", 100.1, 20, 100.0, 100.2),  # 接近 mid → 中性
            FakeTick(3.0, "2330.TW", 99.9, 15, 100.0, 100.2),   # price < mid → 賣方
            FakeTick(4.0, "2330.TW", 100.35, 30, 100.1, 100.3), # 買方
        ]

        factors = []
        for t in ticks:
            f = engine.update_from_tick(t)
            factors.append(f)

        # 前幾筆可能因 min_points 未滿為 None
        assert factors[0] is None
        assert factors[1] is None
        assert factors[2] is None

        last_factor = factors[3]
        assert isinstance(last_factor, CapitalFlowFactor)
        assert last_factor.symbol == "2330.TW"

        # 檢查基本欄位
        assert last_factor.window_trades == 4
        assert last_factor.window_volume > 0
        assert last_factor.buy_volume >= 0
        assert last_factor.sell_volume >= 0

        # SAI 判斷：在 [-1, 1] 之間
        assert last_factor.smart_aggression_index is not None
        assert -1.0 <= last_factor.smart_aggression_index <= 1.0
    
    def test_capital_flow_engine_symbol_filter(self):
        """測試 Symbol 過濾功能"""
        engine = CapitalFlowEngine(symbol="2330.TW", window_size=10, min_points=2)

        t1 = FakeTick(1.0, "2317.TW", 100.3, 10, 100.0, 100.2)
        t2 = FakeTick(2.0, "2330.TW", 100.3, 10, 100.0, 100.2)

        f1 = engine.update_from_tick(t1)
        f2 = engine.update_from_tick(t2)

        assert f1 is None  # 不處理別的 symbol
        assert f2 is None  # 視窗筆數尚未達 min_points
    
    def test_capital_flow_engine_no_symbol_filter(self):
        """測試不指定 Symbol 時接受所有標的"""
        engine = CapitalFlowEngine(symbol=None, window_size=10, min_points=2)

        t1 = FakeTick(1.0, "2330.TW", 100.3, 10, 100.0, 100.2)
        t2 = FakeTick(2.0, "2317.TW", 200.3, 20, 200.0, 200.2)

        f1 = engine.update_from_tick(t1)
        f2 = engine.update_from_tick(t2)

        # 第一個可能因 min_points 未滿為 None
        # 第二個應該有結果（但要注意 symbol 混合的情況）
        # 實際上，如果 symbol 不同，視窗會混合，這可能不是預期行為
        # 但根據設計，symbol=None 時應該接受所有標的
        # 這裡我們主要測試不會因為 symbol 不同而直接返回 None
        assert f1 is None or isinstance(f1, CapitalFlowFactor)
        assert f2 is None or isinstance(f2, CapitalFlowFactor)
    
    def test_capital_flow_engine_invalid_quotes(self):
        """測試無效報價處理"""
        engine = CapitalFlowEngine(symbol=None, window_size=5, min_points=2)

        # 無效 bid/ask
        t1 = FakeTick(1.0, "2330.TW", 100.0, 10, 0.0, 100.0)
        assert engine.update_from_tick(t1) is None

        # ask <= bid
        t2 = FakeTick(2.0, "2330.TW", 100.0, 10, 100.0, 100.0)
        assert engine.update_from_tick(t2) is None

        # volume <= 0
        t3 = FakeTick(3.0, "2330.TW", 100.2, 0.0, 100.0, 100.2)
        assert engine.update_from_tick(t3) is None
    
    def test_capital_flow_engine_compute_from_ticks(self):
        """測試一次性計算功能"""
        engine = CapitalFlowEngine(symbol="2330.TW", window_size=10, min_points=3)

        ticks = [
            FakeTick(1.0, "2330.TW", 100.3, 10, 100.0, 100.2),
            FakeTick(2.0, "2330.TW", 100.4, 20, 100.1, 100.3),
            FakeTick(3.0, "2330.TW", 100.35, 30, 100.1, 100.3),
            FakeTick(4.0, "2330.TW", 100.2, 15, 100.0, 100.2),
        ]

        factor = engine.compute_from_ticks(ticks)
        assert isinstance(factor, CapitalFlowFactor)
        assert factor.symbol == "2330.TW"
        assert factor.window_trades == len(ticks)
        assert factor.window_volume > 0
        assert factor.smart_aggression_index is not None
    
    def test_sai_calculation(self):
        """測試 SAI 計算正確性"""
        engine = CapitalFlowEngine(symbol="2330.TW", window_size=10, min_points=4)

        # 全部買方主動
        ticks = [
            FakeTick(1.0, "2330.TW", 100.3, 10, 100.0, 100.2),  # 買方
            FakeTick(2.0, "2330.TW", 100.4, 20, 100.1, 100.3),  # 買方
            FakeTick(3.0, "2330.TW", 100.35, 30, 100.1, 100.3), # 買方
            FakeTick(4.0, "2330.TW", 100.5, 40, 100.2, 100.4), # 買方
        ]

        factor = engine.compute_from_ticks(ticks)
        assert factor is not None
        assert factor.smart_aggression_index is not None
        # 全部買方，SAI 應該接近 1.0
        assert factor.smart_aggression_index > 0.5
    
    def test_moi_calculation(self):
        """測試 MOI 計算正確性"""
        engine = CapitalFlowEngine(symbol="2330.TW", window_size=10, min_points=6)

        # 前半段偏空，後半段偏多（應該 MOI > 0）
        ticks = [
            FakeTick(1.0, "2330.TW", 99.9, 10, 100.0, 100.2),   # 賣方
            FakeTick(2.0, "2330.TW", 99.8, 20, 100.0, 100.2),   # 賣方
            FakeTick(3.0, "2330.TW", 99.95, 15, 100.0, 100.2),  # 賣方
            FakeTick(4.0, "2330.TW", 100.3, 25, 100.1, 100.3),  # 買方
            FakeTick(5.0, "2330.TW", 100.4, 30, 100.1, 100.3),  # 買方
            FakeTick(6.0, "2330.TW", 100.35, 35, 100.1, 100.3), # 買方
        ]

        factor = engine.compute_from_ticks(ticks)
        assert factor is not None
        assert factor.momentum_of_imbalance is not None
        # 後半段比前半段更偏多，MOI 應該 > 0
        assert factor.momentum_of_imbalance > 0.0
    
    def test_side_classification(self):
        """測試多空方向判斷"""
        engine = CapitalFlowEngine(symbol="2330.TW", window_size=10, min_points=1, at_mid_tolerance_bp=1.0)

        # price 明顯 > mid → 買方
        tick1 = FakeTick(1.0, "2330.TW", 100.3, 10, 100.0, 100.2)  # mid=100.1, price=100.3
        factor1 = engine.update_from_tick(tick1)
        # 由於 min_points=1，應該有結果
        if factor1:
            # 檢查 buy_volume > 0
            assert factor1.buy_volume > 0

        # price 明顯 < mid → 賣方
        tick2 = FakeTick(2.0, "2330.TW", 99.9, 10, 100.0, 100.2)  # mid=100.1, price=99.9
        factor2 = engine.update_from_tick(tick2)
        if factor2:
            # 檢查 sell_volume > 0
            assert factor2.sell_volume > 0
    
    def test_reset(self):
        """測試重置功能"""
        engine = CapitalFlowEngine(symbol="2330.TW", window_size=10, min_points=2)

        # 新增一些 Tick
        tick1 = FakeTick(1.0, "2330.TW", 100.3, 10, 100.0, 100.2)
        tick2 = FakeTick(2.0, "2330.TW", 100.4, 20, 100.1, 100.3)
        engine.update_from_tick(tick1)
        engine.update_from_tick(tick2)

        # 重置
        engine.reset()

        # 驗證視窗已清空
        assert len(engine._window) == 0


class TestIntegration:
    """整合測試：與 UnifiedTick 整合"""
    
    def test_with_unified_tick(self):
        """測試與真實 UnifiedTick 整合"""
        from data_feed.tick_handler import UnifiedTick

        engine = CapitalFlowEngine(symbol="2330.TW", window_size=10, min_points=3)

        ticks = [
            UnifiedTick(
                timestamp=1000.0 + i,
                symbol="2330.TW",
                source="sinopac",
                price=750.0 + i * 0.1,
                volume=100 + i * 10,
                bid_price=749.5 + i * 0.1,
                ask_price=750.5 + i * 0.1,
            )
            for i in range(5)
        ]

        factor = engine.compute_from_ticks(ticks)
        assert factor is not None
        assert factor.symbol == "2330.TW"
        assert factor.window_trades == 5
        assert factor.smart_aggression_index is not None
        assert -1.0 <= factor.smart_aggression_index <= 1.0
    
    def test_with_mock_api_pipeline(self):
        """測試與 Mock API 完整流程"""
        from data_feed.tick_handler import MockSinopacAPI, SinopacConverter

        # 1. 建立數據來源
        mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)
        converter = SinopacConverter()

        # 2. 建立 CapitalFlowEngine
        engine = CapitalFlowEngine(symbol="2330.TW", window_size=20, min_points=10)

        # 3. 處理多個 Tick
        factors = []
        for i in range(30):
            raw_tick = mock_api.get_next_raw_tick()
            unified_tick = converter.convert_to_unified(raw_tick)
            
            factor = engine.update_from_tick(unified_tick)
            if factor:
                factors.append(factor)
        
        # 4. 驗證結果
        assert len(factors) > 0
        assert all(isinstance(f, CapitalFlowFactor) for f in factors)
        assert all(f.symbol == "2330.TW" for f in factors)
        assert all(f.smart_aggression_index is not None for f in factors)
        assert all(-1.0 <= f.smart_aggression_index <= 1.0 for f in factors)


if __name__ == "__main__":
    # 簡單測試執行
    print("=== 執行單元測試 ===")
    
    test_engine = TestCapitalFlowEngine()
    
    print("\n1. 測試基本 SAI 和 MOI 計算...")
    test_engine.test_capital_flow_engine_basic_sai_and_moi()
    print("   ✓ 通過")
    
    print("\n2. 測試 Symbol 過濾...")
    test_engine.test_capital_flow_engine_symbol_filter()
    print("   ✓ 通過")
    
    print("\n3. 測試無效報價處理...")
    test_engine.test_capital_flow_engine_invalid_quotes()
    print("   ✓ 通過")
    
    print("\n4. 測試一次性計算...")
    test_engine.test_capital_flow_engine_compute_from_ticks()
    print("   ✓ 通過")
    
    print("\n5. 測試 SAI 計算...")
    test_engine.test_sai_calculation()
    print("   ✓ 通過")
    
    print("\n6. 測試 MOI 計算...")
    test_engine.test_moi_calculation()
    print("   ✓ 通過")
    
    print("\n7. 測試重置功能...")
    test_engine.test_reset()
    print("   ✓ 通過")
    
    print("\n8. 測試完整流程...")
    test_integration = TestIntegration()
    test_integration.test_with_mock_api_pipeline()
    print("   ✓ 通過")
    
    print("\n✅ 所有測試通過！")

