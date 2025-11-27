"""
跨資產聯動因子引擎單元測試

測試 CrossAssetFactorEngine 的核心功能：
1. 配置驗證
2. VolumeBar 更新與歷史維護
3. Rolling correlation 計算
4. Rolling beta 計算
5. 多個 reference symbols 處理
"""

import pytest
import numpy as np
from collections import deque

from factor_engine.cross_asset_factor import (
    CrossAssetWindowConfig,
    CrossAssetFactor,
    CrossAssetFactorEngine,
)
from factor_engine.info_time_engine import VolumeBar


class TestCrossAssetWindowConfig:
    """測試 CrossAssetWindowConfig 資料結構"""
    
    def test_valid_config(self):
        """測試有效配置"""
        config = CrossAssetWindowConfig(
            target_symbol="2330.TW",
            reference_symbols=["QQQ", "ES"],
            window_size=20,
        )
        assert config.target_symbol == "2330.TW"
        assert config.reference_symbols == ["QQQ", "ES"]
        assert config.window_size == 20
    
    def test_invalid_window_size(self):
        """測試無效的 window_size"""
        with pytest.raises(ValueError, match="window_size must be positive"):
            CrossAssetWindowConfig(
                target_symbol="2330.TW",
                reference_symbols=["QQQ"],
                window_size=0,
            )
    
    def test_empty_reference_symbols(self):
        """測試空的 reference_symbols"""
        with pytest.raises(ValueError, match="reference_symbols cannot be empty"):
            CrossAssetWindowConfig(
                target_symbol="2330.TW",
                reference_symbols=[],
                window_size=20,
            )
    
    def test_target_in_reference_symbols(self):
        """測試 target_symbol 在 reference_symbols 中（應該報錯）"""
        with pytest.raises(ValueError, match="target_symbol cannot be in reference_symbols"):
            CrossAssetWindowConfig(
                target_symbol="2330.TW",
                reference_symbols=["2330.TW", "QQQ"],
                window_size=20,
            )


class TestCrossAssetFactorEngine:
    """測試 CrossAssetFactorEngine 核心功能"""
    
    @pytest.fixture
    def config(self):
        """建立測試配置"""
        return CrossAssetWindowConfig(
            target_symbol="2330.TW",
            reference_symbols=["QQQ", "ES"],
            window_size=10,  # 使用較小的 window_size 以便測試
        )
    
    @pytest.fixture
    def engine(self, config):
        """建立測試引擎"""
        return CrossAssetFactorEngine(config)
    
    def test_initialization(self, engine, config):
        """測試初始化"""
        assert engine.config == config
        assert "2330.TW" in engine.price_history
        assert "QQQ" in engine.price_history
        assert "ES" in engine.price_history
        assert len(engine.price_history["2330.TW"]) == 0
        assert len(engine.return_history["2330.TW"]) == 0
    
    def test_reset(self, engine):
        """測試重置功能"""
        # 先加入一些資料
        bar = VolumeBar(
            start_ts=1000.0,
            end_ts=1100.0,
            symbol="2330.TW",
            vwap=750.0,
            total_volume=1000000,
            tick_count=100,
            open_price=749.0,
            high_price=751.0,
            low_price=749.0,
            close_price=750.0,
            avg_bid=749.5,
            avg_ask=750.5,
        )
        engine.update_with_bar(bar)
        
        # 重置
        engine.reset()
        
        # 確認所有歷史都被清空
        for symbol in engine.price_history.keys():
            assert len(engine.price_history[symbol]) == 0
            assert len(engine.return_history[symbol]) == 0
    
    def test_update_with_bar_ignores_unrelated_symbol(self, engine):
        """測試更新時忽略不相關的 symbol"""
        bar = VolumeBar(
            start_ts=1000.0,
            end_ts=1100.0,
            symbol="AAPL",  # 不在配置中
            vwap=150.0,
            total_volume=1000000,
            tick_count=100,
            open_price=149.0,
            high_price=151.0,
            low_price=149.0,
            close_price=150.0,
            avg_bid=149.5,
            avg_ask=150.5,
        )
        result = engine.update_with_bar(bar)
        assert result is None
        assert len(engine.price_history["AAPL"]) == 0 if "AAPL" in engine.price_history else True
    
    def test_update_with_bar_returns_none_when_insufficient_data(self, engine):
        """測試資料不足時回傳 None"""
        bar = VolumeBar(
            start_ts=1000.0,
            end_ts=1100.0,
            symbol="2330.TW",
            vwap=750.0,
            total_volume=1000000,
            tick_count=100,
            open_price=749.0,
            high_price=751.0,
            low_price=749.0,
            close_price=750.0,
            avg_bid=749.5,
            avg_ask=750.5,
        )
        result = engine.update_with_bar(bar)
        assert result is None  # 只有一筆資料，不足以計算因子
    
    def test_update_with_bar_returns_factors_when_sufficient_data(self, engine):
        """測試資料充足時回傳因子列表"""
        base_price = 750.0
        
        # 為所有 symbol 生成足夠的 VolumeBar（至少 window_size + 1 個價格點）
        for i in range(12):  # window_size=10，需要 11 個價格點才能計算 10 個報酬
            for symbol in ["2330.TW", "QQQ", "ES"]:
                price = base_price + i * 1.0
                bar = VolumeBar(
                    start_ts=1000.0 + i * 60.0,
                    end_ts=1100.0 + i * 60.0,
                    symbol=symbol,
                    vwap=price,
                    total_volume=1000000,
                    tick_count=100,
                    open_price=price - 0.5,
                    high_price=price + 0.5,
                    low_price=price - 0.5,
                    close_price=price,
                    avg_bid=price - 0.25,
                    avg_ask=price + 0.25,
                )
                result = engine.update_with_bar(bar)
                
                # 當 i >= 10 時，應該有足夠的資料計算因子
                if i >= 10 and symbol == "ES":  # 最後一個 symbol 更新時
                    assert result is not None
                    assert isinstance(result, list)
                    assert len(result) == 2  # 兩個 reference symbols
                    for factor in result:
                        assert isinstance(factor, CrossAssetFactor)
                        assert factor.target_symbol == "2330.TW"
                        assert factor.reference_symbol in ["QQQ", "ES"]
                        assert -1.0 <= factor.rolling_corr <= 1.0
                        assert isinstance(factor.rolling_beta, float)
    
    def test_rolling_correlation_calculation(self, engine):
        """測試 rolling correlation 計算"""
        # 建立高度相關的價格序列
        base_time = 1000.0
        target_prices = [750.0 + i * 1.0 for i in range(12)]
        ref_prices = [400.0 + i * 0.8 for i in range(12)]  # 與 target 高度相關
        
        for i in range(12):
            for symbol, price in [("2330.TW", target_prices[i]), ("QQQ", ref_prices[i])]:
                bar = VolumeBar(
                    start_ts=base_time + i * 60.0,
                    end_ts=base_time + (i + 1) * 60.0,
                    symbol=symbol,
                    vwap=price,
                    total_volume=1000000,
                    tick_count=100,
                    open_price=price - 0.5,
                    high_price=price + 0.5,
                    low_price=price - 0.5,
                    close_price=price,
                    avg_bid=price - 0.25,
                    avg_ask=price + 0.25,
                )
                result = engine.update_with_bar(bar)
        
        # 最後一次更新應該回傳因子
        assert result is not None
        qqq_factor = next(f for f in result if f.reference_symbol == "QQQ")
        # 高度相關的序列應該有接近 1.0 的 correlation
        assert qqq_factor.rolling_corr > 0.9
    
    def test_rolling_beta_calculation(self, engine):
        """測試 rolling beta 計算"""
        base_time = 1000.0
        
        # 建立 beta = 2.0 的關係（target 變化是 ref 的 2 倍）
        for i in range(12):
            ref_price = 400.0 + i * 1.0
            target_price = 750.0 + i * 2.0  # beta = 2.0
            
            for symbol, price in [("2330.TW", target_price), ("QQQ", ref_price)]:
                bar = VolumeBar(
                    start_ts=base_time + i * 60.0,
                    end_ts=base_time + (i + 1) * 60.0,
                    symbol=symbol,
                    vwap=price,
                    total_volume=1000000,
                    tick_count=100,
                    open_price=price - 0.5,
                    high_price=price + 0.5,
                    low_price=price - 0.5,
                    close_price=price,
                    avg_bid=price - 0.25,
                    avg_ask=price + 0.25,
                )
                result = engine.update_with_bar(bar)
        
        # 檢查 beta 是否接近 2.0
        assert result is not None
        qqq_factor = next(f for f in result if f.reference_symbol == "QQQ")
        # 允許一些誤差（因為是 rolling window，可能不完全等於 2.0）
        assert 1.5 < qqq_factor.rolling_beta < 2.5
    
    def test_get_current_window_status(self, engine):
        """測試獲取視窗狀態"""
        status = engine.get_current_window_status()
        assert "2330.TW" in status
        assert "QQQ" in status
        assert "ES" in status
        assert all(v == 0 for v in status.values())  # 初始狀態應該都是 0
        
        # 加入一些資料後再檢查
        bar = VolumeBar(
            start_ts=1000.0,
            end_ts=1100.0,
            symbol="2330.TW",
            vwap=750.0,
            total_volume=1000000,
            tick_count=100,
            open_price=749.0,
            high_price=751.0,
            low_price=749.0,
            close_price=750.0,
            avg_bid=749.5,
            avg_ask=750.5,
        )
        engine.update_with_bar(bar)
        status = engine.get_current_window_status()
        assert status["2330.TW"] == 0  # 只有一個價格點，沒有報酬
        assert status["QQQ"] == 0
        assert status["ES"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

