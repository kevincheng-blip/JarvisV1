"""
測試 InertiaFactorEngine 模組

測試 F_Inertia 慣性因子計算、窗口配置、多空拉鋸等情境
"""

import sys
import os
import pytest

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from factor_engine import (
    InertiaWindowConfig,
    InertiaFactor,
    InertiaFactorEngine,
    CapitalFlowFactor,
)


class TestInertiaWindowConfig:
    """測試 InertiaWindowConfig 資料結構"""
    
    def test_valid_config(self):
        """測試有效配置"""
        config = InertiaWindowConfig(
            symbol="2330.TW",
            window_size=100,
            min_effective_points=20,
        )
        assert config.symbol == "2330.TW"
        assert config.window_size == 100
        assert config.min_effective_points == 20
    
    def test_invalid_window_size(self):
        """測試無效的 window_size"""
        with pytest.raises(ValueError, match="window_size must be positive"):
            InertiaWindowConfig(
                symbol="2330.TW",
                window_size=0,
            )
    
    def test_invalid_min_effective_points(self):
        """測試無效的 min_effective_points"""
        with pytest.raises(ValueError, match="min_effective_points must be positive"):
            InertiaWindowConfig(
                symbol="2330.TW",
                window_size=100,
                min_effective_points=0,
            )
    
    def test_min_effective_points_greater_than_window_size(self):
        """測試 min_effective_points > window_size 的情況"""
        with pytest.raises(ValueError, match="min_effective_points must be <= window_size"):
            InertiaWindowConfig(
                symbol="2330.TW",
                window_size=10,
                min_effective_points=15,
            )


class TestInertiaFactorEngine:
    """測試 InertiaFactorEngine 核心功能"""
    
    def test_data_insufficient_returns_none(self):
        """測試資料不足時不輸出因子"""
        config = InertiaWindowConfig(
            symbol="2330.TW",
            window_size=10,
            min_effective_points=5,
        )
        engine = InertiaFactorEngine(config)
        
        # 餵少於 5 筆 CapitalFlowFactor
        for i in range(4):
            factor = CapitalFlowFactor(
                timestamp=1000.0 + i,
                symbol="2330.TW",
                window_trades=10,
                window_volume=1000.0,
                buy_volume=600.0,
                sell_volume=400.0,
                net_signed_volume=200.0,
                smart_aggression_index=0.5,
                momentum_of_imbalance=None,
            )
            result = engine.update_with_capital_flow(factor)
            assert result is None, f"第 {i+1} 筆應該回傳 None（資料不足）"
    
    def test_long_term_bullish_inertia_positive(self):
        """測試長期偏多時 inertia_sai > 0"""
        config = InertiaWindowConfig(
            symbol="2330.TW",
            window_size=5,
            min_effective_points=3,
        )
        engine = InertiaFactorEngine(config)
        
        results = []
        # 連續餵 8 筆 sai=0.8 的 CapitalFlowFactor
        for i in range(8):
            factor = CapitalFlowFactor(
                timestamp=1000.0 + i,
                symbol="2330.TW",
                window_trades=10,
                window_volume=1000.0,
                buy_volume=900.0,
                sell_volume=100.0,
                net_signed_volume=800.0,
                smart_aggression_index=0.8,
                momentum_of_imbalance=None,
            )
            result = engine.update_with_capital_flow(factor)
            if result is not None:
                results.append(result)
        
        # 從第 3 筆開始應該開始回傳 InertiaFactor
        assert len(results) >= 6, "應該至少有 6 個因子（從第 3 筆開始）"
        
        # 檢查最後一個因子
        last_factor = results[-1]
        assert isinstance(last_factor, InertiaFactor)
        assert last_factor.symbol == "2330.TW"
        assert isinstance(last_factor.inertia_sai, float)
        assert last_factor.inertia_sai > 0.5, f"長期偏多時 inertia_sai 應該 > 0.5，實際為 {last_factor.inertia_sai}"
        assert -1.0 <= last_factor.inertia_sai <= 1.0, "inertia_sai 應該在 [-1, 1] 範圍內"
    
    def test_oscillating_market_inertia_near_zero(self):
        """測試多空拉鋸時 inertia_sai 接近 0"""
        config = InertiaWindowConfig(
            symbol="2330.TW",
            window_size=20,
            min_effective_points=10,
        )
        engine = InertiaFactorEngine(config)
        
        results = []
        # 交替餵 sai = +0.8 和 sai = -0.8
        for i in range(25):
            sai = 0.8 if i % 2 == 0 else -0.8
            factor = CapitalFlowFactor(
                timestamp=1000.0 + i,
                symbol="2330.TW",
                window_trades=10,
                window_volume=1000.0,
                buy_volume=900.0 if sai > 0 else 100.0,
                sell_volume=100.0 if sai > 0 else 900.0,
                net_signed_volume=800.0 if sai > 0 else -800.0,
                smart_aggression_index=sai,
                momentum_of_imbalance=None,
            )
            result = engine.update_with_capital_flow(factor)
            if result is not None:
                results.append(result)
        
        # 當歷史夠長時，檢查 abs(inertia_sai) < 0.3（接近中性）
        assert len(results) >= 15, "應該至少有 15 個因子"
        
        # 檢查最後幾個因子（歷史較長時應該接近 0）
        last_factor = results[-1]
        assert isinstance(last_factor, InertiaFactor)
        assert abs(last_factor.inertia_sai) < 0.3, (
            f"多空拉鋸時 inertia_sai 應該接近 0，實際為 {last_factor.inertia_sai}"
        )
        assert -1.0 <= last_factor.inertia_sai <= 1.0
    
    def test_only_processes_configured_symbol(self):
        """測試只作用於指定 symbol"""
        config = InertiaWindowConfig(
            symbol="2330.TW",
            window_size=5,
            min_effective_points=3,
        )
        engine = InertiaFactorEngine(config)
        
        results_2330 = []
        results_2317 = []
        
        # 同時餵 "2330.TW" 和 "2317.TW" 的 CapitalFlowFactor
        for i in range(8):
            # 2330.TW 的因子
            factor_2330 = CapitalFlowFactor(
                timestamp=1000.0 + i,
                symbol="2330.TW",
                window_trades=10,
                window_volume=1000.0,
                buy_volume=600.0,
                sell_volume=400.0,
                net_signed_volume=200.0,
                smart_aggression_index=0.5,
                momentum_of_imbalance=None,
            )
            result_2330 = engine.update_with_capital_flow(factor_2330)
            if result_2330 is not None:
                results_2330.append(result_2330)
            
            # 2317.TW 的因子（應該被忽略）
            factor_2317 = CapitalFlowFactor(
                timestamp=1000.0 + i,
                symbol="2317.TW",
                window_trades=10,
                window_volume=1000.0,
                buy_volume=600.0,
                sell_volume=400.0,
                net_signed_volume=200.0,
                smart_aggression_index=0.5,
                momentum_of_imbalance=None,
            )
            result_2317 = engine.update_with_capital_flow(factor_2317)
            if result_2317 is not None:
                results_2317.append(result_2317)
        
        # 2330.TW 應該有結果（從第 3 筆開始）
        assert len(results_2330) >= 6, "2330.TW 應該至少有 6 個因子"
        assert all(r.symbol == "2330.TW" for r in results_2330), "所有因子都應該是 2330.TW"
        
        # 2317.TW 應該沒有結果（因為不在配置中）
        assert len(results_2317) == 0, "2317.TW 應該沒有因子（不在配置中）"
    
    def test_handles_none_sai(self):
        """測試處理 SAI 為 None 的情況"""
        config = InertiaWindowConfig(
            symbol="2330.TW",
            window_size=5,
            min_effective_points=3,
        )
        engine = InertiaFactorEngine(config)
        
        # 餵一個 SAI 為 None 的因子
        factor = CapitalFlowFactor(
            timestamp=1000.0,
            symbol="2330.TW",
            window_trades=10,
            window_volume=0.0,  # volume=0 時 SAI 可能為 None
            buy_volume=0.0,
            sell_volume=0.0,
            net_signed_volume=0.0,
            smart_aggression_index=None,
            momentum_of_imbalance=None,
        )
        result = engine.update_with_capital_flow(factor)
        assert result is None, "SAI 為 None 時應該回傳 None"
    
    def test_inertia_sai_bounded(self):
        """測試 inertia_sai 始終在 [-1, 1] 範圍內"""
        config = InertiaWindowConfig(
            symbol="2330.TW",
            window_size=5,
            min_effective_points=3,
        )
        engine = InertiaFactorEngine(config)
        
        # 餵極端 SAI 值
        for i in range(8):
            factor = CapitalFlowFactor(
                timestamp=1000.0 + i,
                symbol="2330.TW",
                window_trades=10,
                window_volume=1000.0,
                buy_volume=1000.0 if i % 2 == 0 else 0.0,
                sell_volume=0.0 if i % 2 == 0 else 1000.0,
                net_signed_volume=1000.0 if i % 2 == 0 else -1000.0,
                smart_aggression_index=1.0 if i % 2 == 0 else -1.0,
                momentum_of_imbalance=None,
            )
            result = engine.update_with_capital_flow(factor)
            if result is not None:
                assert -1.0 <= result.inertia_sai <= 1.0, (
                    f"inertia_sai 應該在 [-1, 1] 範圍內，實際為 {result.inertia_sai}"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

