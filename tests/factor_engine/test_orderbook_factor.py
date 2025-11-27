"""
測試 OrderbookFactorEngine 模組

測試 F_Orderbook 因子計算、Bid/Ask 驗證、硬體友善接口等功能
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dataclasses import dataclass
from factor_engine import OrderbookFactorEngine, OrderbookFactor


@dataclass
class FakeUnifiedTick:
    """
    測試用 Tick，模擬 data_feed.tick_handler.UnifiedTick。

    真實系統中，Engine 只會用到：
    - timestamp
    - symbol
    - bid_price
    - ask_price
    """
    timestamp: float
    symbol: str
    bid_price: float
    ask_price: float


class TestOrderbookFactor:
    """測試 OrderbookFactor 資料結構"""
    
    def test_create_valid_factor(self):
        """測試建立有效的 OrderbookFactor"""
        factor = OrderbookFactor(
            timestamp=1234567890.0,
            symbol="2330.TW",
            mid_price=100.25,
            spread=0.5,
            rel_spread_bp=49.88,
            liquidity_cost_index=49.88,
        )
        assert factor.symbol == "2330.TW"
        assert factor.mid_price == 100.25
        assert factor.spread == 0.5
        assert factor.rel_spread_bp > 0.0


class TestOrderbookFactorEngine:
    """測試 OrderbookFactorEngine"""
    
    def test_calculate_factor_basic(self):
        """測試基本因子計算"""
        engine = OrderbookFactorEngine(symbol="2330.TW")

        tick = FakeUnifiedTick(
            timestamp=1.0,
            symbol="2330.TW",
            bid_price=100.0,
            ask_price=100.5,
        )

        factor = engine.calculate_factor(tick)
        assert isinstance(factor, OrderbookFactor)
        assert factor.symbol == "2330.TW"
        assert factor.mid_price == 100.25
        assert factor.spread == 0.5
        assert factor.rel_spread_bp > 0.0
        assert factor.liquidity_cost_index == factor.rel_spread_bp
    
    def test_calculate_factor_symbol_filter(self):
        """測試 Symbol 過濾功能"""
        engine = OrderbookFactorEngine(symbol="2330.TW")

        tick = FakeUnifiedTick(
            timestamp=1.0,
            symbol="2317.TW",  # 不同標的
            bid_price=100.0,
            ask_price=100.5,
        )

        factor = engine.calculate_factor(tick)
        assert factor is None
    
    def test_calculate_factor_no_symbol_filter(self):
        """測試不指定 Symbol 時接受所有標的"""
        engine = OrderbookFactorEngine(symbol=None)

        tick1 = FakeUnifiedTick(
            timestamp=1.0,
            symbol="2330.TW",
            bid_price=100.0,
            ask_price=100.5,
        )
        factor1 = engine.calculate_factor(tick1)
        assert factor1 is not None
        assert factor1.symbol == "2330.TW"

        tick2 = FakeUnifiedTick(
            timestamp=2.0,
            symbol="2317.TW",
            bid_price=200.0,
            ask_price=200.5,
        )
        factor2 = engine.calculate_factor(tick2)
        assert factor2 is not None
        assert factor2.symbol == "2317.TW"
    
    def test_calculate_factor_invalid_quotes(self):
        """測試無效報價處理"""
        engine = OrderbookFactorEngine(symbol=None)

        # 負價
        tick1 = FakeUnifiedTick(
            timestamp=1.0,
            symbol="2330.TW",
            bid_price=-1.0,
            ask_price=100.0,
        )
        assert engine.calculate_factor(tick1) is None

        # ask <= bid
        tick2 = FakeUnifiedTick(
            timestamp=1.0,
            symbol="2330.TW",
            bid_price=100.0,
            ask_price=100.0,
        )
        assert engine.calculate_factor(tick2) is None

        # ask < bid
        tick3 = FakeUnifiedTick(
            timestamp=1.0,
            symbol="2330.TW",
            bid_price=100.0,
            ask_price=99.0,
        )
        assert engine.calculate_factor(tick3) is None

        # 零價
        tick4 = FakeUnifiedTick(
            timestamp=1.0,
            symbol="2330.TW",
            bid_price=0.0,
            ask_price=100.0,
        )
        assert engine.calculate_factor(tick4) is None
    
    def test_calculate_factor_missing_attributes(self):
        """測試缺少必要屬性的情況"""
        engine = OrderbookFactorEngine(symbol=None)

        # 缺少 bid_price
        class IncompleteTick:
            timestamp = 1.0
            symbol = "2330.TW"
            ask_price = 100.5

        tick1 = IncompleteTick()
        assert engine.calculate_factor(tick1) is None

        # 缺少 ask_price
        class IncompleteTick2:
            timestamp = 1.0
            symbol = "2330.TW"
            bid_price = 100.0

        tick2 = IncompleteTick2()
        assert engine.calculate_factor(tick2) is None
    
    def test_rel_spread_bp_calculation(self):
        """測試相對價差計算正確性"""
        engine = OrderbookFactorEngine(symbol=None)

        # Bid=100, Ask=100.5, Mid=100.25, Spread=0.5
        # rel_spread_bp = (0.5 / 100.25) * 10000 ≈ 49.88
        tick = FakeUnifiedTick(
            timestamp=1.0,
            symbol="2330.TW",
            bid_price=100.0,
            ask_price=100.5,
        )

        factor = engine.calculate_factor(tick)
        assert factor is not None
        expected_rel_spread_bp = (0.5 / 100.25) * 10000.0
        assert abs(factor.rel_spread_bp - expected_rel_spread_bp) < 0.01


class TestStaticCalculateFromBidAsk:
    """測試靜態方法 calculate_from_bid_ask"""
    
    def test_static_calculate_from_bid_ask(self):
        """測試硬體友善接口"""
        factor = OrderbookFactorEngine.calculate_from_bid_ask(
            timestamp=1.0,
            symbol="2330.TW",
            bid_price=100.0,
            ask_price=100.2,
        )

        assert isinstance(factor, OrderbookFactor)
        assert abs(factor.mid_price - 100.1) < 0.01
        assert abs(factor.spread - 0.2) < 0.01
        assert factor.rel_spread_bp > 0.0
        assert factor.liquidity_cost_index == factor.rel_spread_bp
    
    def test_static_calculate_from_bid_ask_invalid(self):
        """測試靜態方法處理無效輸入"""
        # 負價
        factor1 = OrderbookFactorEngine.calculate_from_bid_ask(
            timestamp=1.0,
            symbol="2330.TW",
            bid_price=-1.0,
            ask_price=100.0,
        )
        assert factor1 is None

        # ask <= bid
        factor2 = OrderbookFactorEngine.calculate_from_bid_ask(
            timestamp=1.0,
            symbol="2330.TW",
            bid_price=100.0,
            ask_price=100.0,
        )
        assert factor2 is None

        # 零價
        factor3 = OrderbookFactorEngine.calculate_from_bid_ask(
            timestamp=1.0,
            symbol="2330.TW",
            bid_price=0.0,
            ask_price=100.0,
        )
        assert factor3 is None


class TestIntegration:
    """整合測試：與 UnifiedTick 整合"""
    
    def test_with_unified_tick(self):
        """測試與真實 UnifiedTick 整合"""
        from data_feed.tick_handler import UnifiedTick

        engine = OrderbookFactorEngine(symbol="2330.TW")

        tick = UnifiedTick(
            timestamp=1234567890.0,
            symbol="2330.TW",
            source="sinopac",
            price=750.0,
            volume=100,
            bid_price=749.5,
            ask_price=750.5,
        )

        factor = engine.calculate_factor(tick)
        assert factor is not None
        assert factor.symbol == "2330.TW"
        assert factor.mid_price == 750.0
        assert factor.spread == 1.0
        assert factor.rel_spread_bp > 0.0
    
    def test_with_mock_api_pipeline(self):
        """測試與 Mock API 完整流程"""
        from data_feed.tick_handler import MockSinopacAPI, SinopacConverter

        # 1. 建立數據來源
        mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)
        converter = SinopacConverter()

        # 2. 建立 OrderbookFactorEngine
        engine = OrderbookFactorEngine(symbol="2330.TW")

        # 3. 處理多個 Tick
        factors = []
        for i in range(10):
            raw_tick = mock_api.get_next_raw_tick()
            unified_tick = converter.convert_to_unified(raw_tick)
            
            factor = engine.calculate_factor(unified_tick)
            if factor:
                factors.append(factor)
        
        # 4. 驗證結果
        assert len(factors) > 0
        assert all(isinstance(f, OrderbookFactor) for f in factors)
        assert all(f.symbol == "2330.TW" for f in factors)
        assert all(f.mid_price > 0 for f in factors)
        assert all(f.rel_spread_bp > 0 for f in factors)


if __name__ == "__main__":
    # 簡單測試執行
    print("=== 執行單元測試 ===")
    
    test_engine = TestOrderbookFactorEngine()
    
    print("\n1. 測試基本因子計算...")
    test_engine.test_calculate_factor_basic()
    print("   ✓ 通過")
    
    print("\n2. 測試 Symbol 過濾...")
    test_engine.test_calculate_factor_symbol_filter()
    print("   ✓ 通過")
    
    print("\n3. 測試無效報價處理...")
    test_engine.test_calculate_factor_invalid_quotes()
    print("   ✓ 通過")
    
    print("\n4. 測試相對價差計算...")
    test_engine.test_rel_spread_bp_calculation()
    print("   ✓ 通過")
    
    print("\n5. 測試靜態方法...")
    test_static = TestStaticCalculateFromBidAsk()
    test_static.test_static_calculate_from_bid_ask()
    print("   ✓ 通過")
    
    print("\n6. 測試完整流程...")
    test_integration = TestIntegration()
    test_integration.test_with_mock_api_pipeline()
    print("   ✓ 通過")
    
    print("\n✅ 所有測試通過！")

