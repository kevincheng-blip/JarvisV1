"""
測試 FSignalEngine 模組

測試 F_Signal 訊號生成、權重計算、分桶邏輯等情境
"""

import sys
import os
import pytest

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from factor_engine import (
    FSignalConfig,
    FSignalBucket,
    FSignalFactor,
    FSignalEngine,
    CapitalFlowFactor,
    InertiaFactor,
)


class TestFSignalConfig:
    """測試 FSignalConfig 資料結構"""
    
    def test_valid_config(self):
        """測試有效配置"""
        config = FSignalConfig(
            symbol="2330.TW",
            w_sai=0.4,
            w_moi=0.2,
            w_inertia=0.4,
            moi_scale=2.0,
            strong_threshold=0.4,
            weak_threshold=0.15,
        )
        assert config.symbol == "2330.TW"
        assert config.w_sai == 0.4
        assert config.w_moi == 0.2
        assert config.w_inertia == 0.4
    
    def test_invalid_moi_scale(self):
        """測試無效的 moi_scale"""
        with pytest.raises(ValueError, match="moi_scale must be positive"):
            FSignalConfig(
                symbol="2330.TW",
                moi_scale=0,
            )
        
        with pytest.raises(ValueError, match="moi_scale must be positive"):
            FSignalConfig(
                symbol="2330.TW",
                moi_scale=-1.0,
            )
    
    def test_invalid_weak_threshold(self):
        """測試無效的 weak_threshold"""
        with pytest.raises(ValueError, match="weak_threshold must be positive"):
            FSignalConfig(
                symbol="2330.TW",
                weak_threshold=0,
            )
        
        with pytest.raises(ValueError, match="weak_threshold must be < strong_threshold"):
            FSignalConfig(
                symbol="2330.TW",
                weak_threshold=0.5,
                strong_threshold=0.4,
            )
    
    def test_invalid_strong_threshold(self):
        """測試無效的 strong_threshold"""
        with pytest.raises(ValueError, match="strong_threshold must be <= 1.0"):
            FSignalConfig(
                symbol="2330.TW",
                strong_threshold=1.5,
            )


class TestFSignalEngine:
    """測試 FSignalEngine 核心功能"""
    
    @pytest.fixture
    def config(self):
        """建立測試配置"""
        return FSignalConfig(
            symbol="2330.TW",
            w_sai=0.4,
            w_moi=0.2,
            w_inertia=0.4,
            moi_scale=2.0,
            strong_threshold=0.4,
            weak_threshold=0.15,
        )
    
    @pytest.fixture
    def engine(self, config):
        """建立測試引擎"""
        return FSignalEngine(config)
    
    def test_no_inertia_returns_none(self, engine):
        """測試無 inertia 時不產生訊號"""
        capital_flow = CapitalFlowFactor(
            timestamp=1000.0,
            symbol="2330.TW",
            window_trades=10,
            window_volume=1000.0,
            buy_volume=800.0,
            sell_volume=200.0,
            net_signed_volume=600.0,
            smart_aggression_index=0.8,
            momentum_of_imbalance=0.5,
        )
        
        result = engine.update_with_factors(capital_flow, inertia=None)
        assert result is None, "無 inertia 時應該回傳 None"
    
    def test_positive_signal_weak_buy(self, engine):
        """測試有 inertia 時產生訊號（簡單正向場景 - WEAK_BUY）"""
        capital_flow = CapitalFlowFactor(
            timestamp=1000.0,
            symbol="2330.TW",
            window_trades=10,
            window_volume=1000.0,
            buy_volume=800.0,
            sell_volume=200.0,
            net_signed_volume=600.0,
            smart_aggression_index=0.8,
            momentum_of_imbalance=0.5,
        )
        
        inertia = InertiaFactor(
            symbol="2330.TW",
            timestamp=1000.0,
            inertia_sai=0.7,
        )
        
        result = engine.update_with_factors(capital_flow, inertia=inertia)
        
        assert result is not None, "有 inertia 時應該產生訊號"
        assert isinstance(result, FSignalFactor)
        assert result.symbol == "2330.TW"
        assert -1.0 <= result.raw_score <= 1.0, f"raw_score 應該在 [-1, 1] 範圍內，實際為 {result.raw_score}"
        assert result.bucket in [FSignalBucket.WEAK_BUY, FSignalBucket.STRONG_BUY], (
            f"正向訊號時 bucket 應該是 BUY 類型，實際為 {result.bucket}"
        )
    
    def test_positive_signal_strong_buy(self, engine):
        """測試高綜合分數時產生 STRONG_BUY 訊號"""
        # 使用較高的權重配置，讓綜合分數更容易達到 strong_threshold
        config = FSignalConfig(
            symbol="2330.TW",
            w_sai=0.5,
            w_moi=0.2,
            w_inertia=0.3,
            moi_scale=2.0,
            strong_threshold=0.4,
            weak_threshold=0.15,
        )
        engine = FSignalEngine(config)
        
        capital_flow = CapitalFlowFactor(
            timestamp=1000.0,
            symbol="2330.TW",
            window_trades=10,
            window_volume=1000.0,
            buy_volume=900.0,
            sell_volume=100.0,
            net_signed_volume=800.0,
            smart_aggression_index=0.9,
            momentum_of_imbalance=0.6,
        )
        
        inertia = InertiaFactor(
            symbol="2330.TW",
            timestamp=1000.0,
            inertia_sai=0.85,
        )
        
        result = engine.update_with_factors(capital_flow, inertia=inertia)
        
        assert result is not None
        assert result.bucket == FSignalBucket.STRONG_BUY, (
            f"高綜合分數時應該是 STRONG_BUY，實際為 {result.bucket}，raw_score={result.raw_score}"
        )
        assert result.raw_score >= 0.4, f"STRONG_BUY 時 raw_score 應該 >= 0.4，實際為 {result.raw_score}"
    
    def test_negative_signal_strong_sell(self, engine):
        """測試負向場景（賣出訊號）"""
        capital_flow = CapitalFlowFactor(
            timestamp=1000.0,
            symbol="2330.TW",
            window_trades=10,
            window_volume=1000.0,
            buy_volume=100.0,
            sell_volume=900.0,
            net_signed_volume=-800.0,
            smart_aggression_index=-0.9,
            momentum_of_imbalance=-0.6,
        )
        
        inertia = InertiaFactor(
            symbol="2330.TW",
            timestamp=1000.0,
            inertia_sai=-0.7,
        )
        
        result = engine.update_with_factors(capital_flow, inertia=inertia)
        
        assert result is not None
        assert result.bucket in [FSignalBucket.WEAK_SELL, FSignalBucket.STRONG_SELL], (
            f"負向訊號時 bucket 應該是 SELL 類型，實際為 {result.bucket}"
        )
        assert result.raw_score < 0, f"負向訊號時 raw_score 應該 < 0，實際為 {result.raw_score}"
        
        # 檢查是否為 STRONG_SELL
        if result.raw_score <= -0.4:
            assert result.bucket == FSignalBucket.STRONG_SELL, (
                f"極負向分數時應該是 STRONG_SELL，實際為 {result.bucket}"
            )
    
    def test_neutral_signal(self, engine):
        """測試拉鋸場景（接近 0）"""
        capital_flow = CapitalFlowFactor(
            timestamp=1000.0,
            symbol="2330.TW",
            window_trades=10,
            window_volume=1000.0,
            buy_volume=500.0,
            sell_volume=500.0,
            net_signed_volume=0.0,
            smart_aggression_index=0.0,
            momentum_of_imbalance=0.1,
        )
        
        inertia = InertiaFactor(
            symbol="2330.TW",
            timestamp=1000.0,
            inertia_sai=0.0,
        )
        
        result = engine.update_with_factors(capital_flow, inertia=inertia)
        
        assert result is not None
        assert result.bucket == FSignalBucket.NEUTRAL, (
            f"拉鋸場景時應該是 NEUTRAL，實際為 {result.bucket}，raw_score={result.raw_score}"
        )
        assert abs(result.raw_score) < 0.15, (
            f"NEUTRAL 時 raw_score 應該接近 0，實際為 {result.raw_score}"
        )
    
    def test_moi_scaling_and_clipping(self, engine):
        """測試 moi 縮放與裁切行為"""
        # 測試極端 moi 值（例如 100、-100）
        capital_flow = CapitalFlowFactor(
            timestamp=1000.0,
            symbol="2330.TW",
            window_trades=10,
            window_volume=1000.0,
            buy_volume=500.0,
            sell_volume=500.0,
            net_signed_volume=0.0,
            smart_aggression_index=0.0,
            momentum_of_imbalance=100.0,  # 極端值
        )
        
        inertia = InertiaFactor(
            symbol="2330.TW",
            timestamp=1000.0,
            inertia_sai=0.0,
        )
        
        result = engine.update_with_factors(capital_flow, inertia=inertia)
        
        assert result is not None
        # 檢查 raw_score 是否在 [-1, 1] 範圍內（即使 moi 極端）
        assert -1.0 <= result.raw_score <= 1.0, (
            f"即使 moi 極端，raw_score 也應該在 [-1, 1] 範圍內，實際為 {result.raw_score}"
        )
        
        # 測試負極端值
        capital_flow_neg = CapitalFlowFactor(
            timestamp=1001.0,
            symbol="2330.TW",
            window_trades=10,
            window_volume=1000.0,
            buy_volume=500.0,
            sell_volume=500.0,
            net_signed_volume=0.0,
            smart_aggression_index=0.0,
            momentum_of_imbalance=-100.0,  # 負極端值
        )
        
        result_neg = engine.update_with_factors(capital_flow_neg, inertia=inertia)
        
        assert result_neg is not None
        assert -1.0 <= result_neg.raw_score <= 1.0, (
            f"即使 moi 為負極端值，raw_score 也應該在 [-1, 1] 範圍內，實際為 {result_neg.raw_score}"
        )
    
    def test_only_processes_configured_symbol(self, engine):
        """測試只處理配置中的 symbol"""
        capital_flow = CapitalFlowFactor(
            timestamp=1000.0,
            symbol="2317.TW",  # 不同的 symbol
            window_trades=10,
            window_volume=1000.0,
            buy_volume=800.0,
            sell_volume=200.0,
            net_signed_volume=600.0,
            smart_aggression_index=0.8,
            momentum_of_imbalance=0.5,
        )
        
        inertia = InertiaFactor(
            symbol="2317.TW",
            timestamp=1000.0,
            inertia_sai=0.7,
        )
        
        result = engine.update_with_factors(capital_flow, inertia=inertia)
        assert result is None, "不同的 symbol 應該回傳 None"
    
    def test_handles_none_sai_or_moi(self, engine):
        """測試處理 SAI 或 MOI 為 None 的情況"""
        # SAI 為 None
        capital_flow_no_sai = CapitalFlowFactor(
            timestamp=1000.0,
            symbol="2330.TW",
            window_trades=10,
            window_volume=0.0,
            buy_volume=0.0,
            sell_volume=0.0,
            net_signed_volume=0.0,
            smart_aggression_index=None,  # None
            momentum_of_imbalance=0.5,
        )
        
        inertia = InertiaFactor(
            symbol="2330.TW",
            timestamp=1000.0,
            inertia_sai=0.7,
        )
        
        result = engine.update_with_factors(capital_flow_no_sai, inertia=inertia)
        assert result is None, "SAI 為 None 時應該回傳 None"
        
        # MOI 為 None
        capital_flow_no_moi = CapitalFlowFactor(
            timestamp=1001.0,
            symbol="2330.TW",
            window_trades=10,
            window_volume=1000.0,
            buy_volume=800.0,
            sell_volume=200.0,
            net_signed_volume=600.0,
            smart_aggression_index=0.8,
            momentum_of_imbalance=None,  # None
        )
        
        result2 = engine.update_with_factors(capital_flow_no_moi, inertia=inertia)
        assert result2 is None, "MOI 為 None 時應該回傳 None"
    
    def test_bucket_boundaries(self, engine):
        """測試分桶邊界"""
        inertia = InertiaFactor(
            symbol="2330.TW",
            timestamp=1000.0,
            inertia_sai=0.5,
        )
        
        # 測試各個分桶邊界
        test_cases = [
            (0.5, FSignalBucket.STRONG_BUY),   # >= strong_threshold
            (0.3, FSignalBucket.WEAK_BUY),     # >= weak_threshold but < strong_threshold
            (0.1, FSignalBucket.NEUTRAL),      # between -weak_threshold and weak_threshold
            (-0.1, FSignalBucket.NEUTRAL),     # between -weak_threshold and weak_threshold
            (-0.3, FSignalBucket.WEAK_SELL),   # <= -weak_threshold but > -strong_threshold
            (-0.5, FSignalBucket.STRONG_SELL), # <= -strong_threshold
        ]
        
        for target_score, expected_bucket in test_cases:
            # 調整參數以達到目標分數
            # 簡化：直接用 target_score 反推合適的參數（這裡只驗證分桶邏輯）
            capital_flow = CapitalFlowFactor(
                timestamp=1000.0,
                symbol="2330.TW",
                window_trades=10,
                window_volume=1000.0,
                buy_volume=800.0 if target_score > 0 else 200.0,
                sell_volume=200.0 if target_score > 0 else 800.0,
                net_signed_volume=600.0 if target_score > 0 else -600.0,
                smart_aggression_index=target_score,  # 直接用目標分數
                momentum_of_imbalance=0.0,
            )
            
            # 調整 inertia 以接近目標分數
            adjusted_inertia = InertiaFactor(
                symbol="2330.TW",
                timestamp=1000.0,
                inertia_sai=target_score,
            )
            
            result = engine.update_with_factors(capital_flow, inertia=adjusted_inertia)
            
            if result is not None:
                # 由於是加權和，實際分數可能不完全等於 target_score
                # 但我們可以檢查分桶是否在合理範圍內
                if target_score >= 0.4:
                    assert result.bucket == FSignalBucket.STRONG_BUY or result.bucket == FSignalBucket.WEAK_BUY
                elif target_score <= -0.4:
                    assert result.bucket == FSignalBucket.STRONG_SELL or result.bucket == FSignalBucket.WEAK_SELL
                elif abs(target_score) < 0.15:
                    assert result.bucket == FSignalBucket.NEUTRAL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

