"""
跨資產聯動因子引擎（F_CrossAsset）：Step 5

本模組實作創世紀量化系統 Step 5：跨資產聯動因子引擎。

核心功能：
1. CrossAssetWindowConfig：計算視窗與參考資產設定
2. CrossAssetFactor：單一 target 對 reference 的因子輸出
3. CrossAssetFactorEngine：計算 rolling correlation、beta、spread z-score

設計原則：
- 接收 VolumeBar（而非 Tick），計算跨市場聯動強度
- 支援多個 reference symbols（例如：QQQ, ES, USD/TWD）
- 使用 rolling window 計算動態相關性與 beta

作者：創世紀量化系統開發團隊
版本：v1.0
建立日期：2024-11-28
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Deque
from collections import deque
import numpy as np

from .info_time_engine import VolumeBar


# ============================================================================
# 資料結構定義
# ============================================================================

@dataclass(frozen=True)
class CrossAssetWindowConfig:
    """
    跨資產因子計算視窗配置
    
    Attributes:
        target_symbol: 目標資產，例如 '2330.TW'
        reference_symbols: 參考資產清單，例如 ['QQQ', 'ES', 'USD/TWD']
        window_size: 計算 rolling 因子的視窗長度（例如 50 個 Bar）
    """
    target_symbol: str
    reference_symbols: list[str]
    window_size: int

    def __post_init__(self):
        if self.window_size <= 0:
            raise ValueError("window_size must be positive")
        if not self.reference_symbols:
            raise ValueError("reference_symbols cannot be empty")
        if self.target_symbol in self.reference_symbols:
            raise ValueError("target_symbol cannot be in reference_symbols")


@dataclass(frozen=True)
class CrossAssetFactor:
    """
    跨資產因子輸出結構
    
    代表單一 target_symbol 對「某一個 reference_symbol」的即時因子輸出。
    
    Attributes:
        target_symbol: 目標資產代號
        reference_symbol: 參考資產代號
        timestamp: 因子計算時間戳（使用最新 Bar 的 end_ts）
        rolling_corr: 近期報酬的 rolling correlation（-1 到 1）
        rolling_beta: 以 ref 為自變數的回歸 beta（簡化版）
        spread_zscore: 價差 Z-score（pair spread 的標準化值，當 std 接近 0 時為 0.0）
    """
    target_symbol: str
    reference_symbol: str
    timestamp: float
    rolling_corr: float
    rolling_beta: float
    spread_zscore: Optional[float] = None


# ============================================================================
# 跨資產因子引擎
# ============================================================================

class CrossAssetFactorEngine:
    """
    跨資產聯動因子計算引擎
    
    功能：
    - 接收 VolumeBar 更新，維護各 symbol 的價格歷史
    - 計算 target 與每個 reference 之間的 rolling correlation 和 beta
    - 當視窗資料充足時，輸出 CrossAssetFactor 列表
    
    使用方式：
        config = CrossAssetWindowConfig(
            target_symbol="2330.TW",
            reference_symbols=["QQQ", "ES"],
            window_size=20,
        )
        engine = CrossAssetFactorEngine(config)
        
        # 每次有新的 VolumeBar 時
        factors = engine.update_with_bar(bar)
        if factors:
            for f in factors:
                print(f"Corr: {f.rolling_corr:.3f}, Beta: {f.rolling_beta:.3f}")
    """
    
    def __init__(self, config: CrossAssetWindowConfig):
        """
        初始化跨資產因子引擎
        
        Args:
            config: 視窗配置（target_symbol, reference_symbols, window_size）
        """
        self.config = config
        
        # 儲存各 symbol 的歷史價格序列（需要 window_size + 1 個點才能計算 window_size 個報酬）
        self.price_history: dict[str, Deque[float]] = {}
        
        # 儲存各 symbol 的歷史報酬序列（log return）
        self.return_history: dict[str, Deque[float]] = {}
        
        # 記錄各 symbol 的最新時間戳
        self.last_timestamp: dict[str, float] = {}
        
        # 初始化所有相關 symbol 的歷史序列
        all_symbols = [config.target_symbol] + config.reference_symbols
        for symbol in all_symbols:
            self.price_history[symbol] = deque(maxlen=config.window_size + 1)
            self.return_history[symbol] = deque(maxlen=config.window_size)
            self.last_timestamp[symbol] = 0.0
    
    def reset(self) -> None:
        """清空所有歷史資料，重置引擎狀態"""
        for symbol in self.price_history.keys():
            self.price_history[symbol].clear()
            self.return_history[symbol].clear()
            self.last_timestamp[symbol] = 0.0
    
    def update_with_bar(self, bar: VolumeBar) -> Optional[List[CrossAssetFactor]]:
        """
        由外部在每個 VolumeBar 完成時呼叫
        
        Args:
            bar: 新完成的 VolumeBar
            
        Returns:
            當所有相關資產的資料點數量 >= window_size 時，回傳 CrossAssetFactor 列表
            否則回傳 None
        """
        symbol = bar.symbol
        
        # 若 bar.symbol 不在 config 的 target 或 reference 裡面，則忽略
        all_symbols = [self.config.target_symbol] + self.config.reference_symbols
        if symbol not in all_symbols:
            return None
        
        # 更新價格歷史（使用 close_price）
        self.price_history[symbol].append(bar.close_price)
        self.last_timestamp[symbol] = bar.end_ts
        
        # 計算新的報酬（log return: log(p_t / p_{t-1})）
        if len(self.price_history[symbol]) >= 2:
            prev_price = list(self.price_history[symbol])[-2]
            curr_price = self.price_history[symbol][-1]
            
            if prev_price > 0 and curr_price > 0:
                log_return = np.log(curr_price / prev_price)
                self.return_history[symbol].append(log_return)
        
        # 檢查 target 是否有足夠的資料（至少需要 window_size 個 returns）
        # target 是必須的，其他 reference symbols 的檢查留給 _compute_factors 處理
        target_return_count = len(self.return_history[self.config.target_symbol])
        if target_return_count < self.config.window_size:
            return None
        
        # 檢查是否有至少一個 reference symbol 有足夠資料
        # 如果所有 reference 都沒有足夠資料，_compute_factors 會回傳空列表，但我們仍可讓它執行
        # 實際上，只要 target 有足夠資料，就可以嘗試計算因子（_compute_factors 會跳過資料不足的 references）
        
        # 若足夠，計算因子並回傳
        return self._compute_factors()
    
    def _compute_spread_zscore(
        self, 
        target_returns: np.ndarray, 
        ref_returns: np.ndarray, 
        beta: float
    ) -> float:
        """
        計算 pair spread Z-score（內部方法）
        
        Args:
            target_returns: 目標資產的報酬序列
            ref_returns: 參考資產的報酬序列
            beta: 已計算的 rolling beta
            
        Returns:
            spread_zscore: Z-score 值（float），若 std 接近 0 則回傳 0.0
        """
        # 計算 spread = target - beta * ref
        spread = target_returns - beta * ref_returns
        
        # 計算 spread 的 mean 與 std（使用 sample std，ddof=1）
        mean_spread = np.mean(spread)
        std_spread = np.std(spread, ddof=1)
        
        # 若 std_spread 幾乎為 0（避免除以零）
        # 使用更實務的門檻值，判斷 spread 是否幾乎沒有變動
        EPS = 1e-6
        if std_spread < EPS or np.isclose(std_spread, 0.0, atol=EPS):
            return 0.0
        
        # 取視窗內最新一筆 spread
        last_spread = spread[-1]
        
        # 計算 Z-score
        spread_zscore = (last_spread - mean_spread) / std_spread
        
        # 檢查是否為 NaN 或 inf（額外安全檢查）
        if not np.isfinite(spread_zscore):
            return 0.0
        
        return float(spread_zscore)
    
    def _compute_factors(self) -> List[CrossAssetFactor]:
        """
        計算跨資產因子（內部方法）
        
        對於每一個 reference_symbol：
        1. 計算 target 與 ref 的 rolling correlation
        2. 計算簡單 beta（Cov(x,y) / Var(x)）
        3. 建立 CrossAssetFactor 實例
        
        Returns:
            CrossAssetFactor 列表（每個 reference_symbol 一個）
        """
        factors: List[CrossAssetFactor] = []
        
        # 取得 target 的價格序列和 returns 序列（用於計算 price-level beta 和 correlation）
        target_prices = list(self.price_history[self.config.target_symbol])
        target_returns_array = np.array(list(self.return_history[self.config.target_symbol]))
        
        # 使用最新的時間戳（通常用 target 的時間戳）
        latest_ts = self.last_timestamp.get(self.config.target_symbol, 0.0)
        
        # 對每個 reference_symbol 計算因子
        for ref_symbol in self.config.reference_symbols:
            ref_prices = list(self.price_history[ref_symbol])
            ref_returns_list = list(self.return_history[ref_symbol])
            
            # 確保價格序列長度足夠（至少需要 window_size 個價格點）
            min_price_len = min(len(target_prices), len(ref_prices))
            if min_price_len < self.config.window_size:
                continue  # 跳過這個 reference
            
            # 取得最近的 window_size 個價格點
            target_price_window = target_prices[-self.config.window_size:]
            ref_price_window = ref_prices[-self.config.window_size:]
            
            # 轉成 numpy array，確保是 float 類型
            target_prices_array = np.asarray(target_price_window, dtype=float)
            ref_prices_array = np.asarray(ref_price_window, dtype=float)
            
            # 計算 rolling correlation（繼續使用 returns）
            if len(target_returns_array) >= self.config.window_size and len(ref_returns_list) >= self.config.window_size:
                target_ret = target_returns_array[-self.config.window_size:]
                ref_ret = np.array(ref_returns_list[-self.config.window_size:])
                if len(target_ret) >= 2 and np.std(target_ret, ddof=1) > 1e-12 and np.std(ref_ret, ddof=1) > 1e-12:
                    corr_matrix = np.corrcoef(target_ret, ref_ret)
                    rolling_corr = float(corr_matrix[0, 1])
                else:
                    rolling_corr = 0.0
            else:
                rolling_corr = 0.0
            
            # 計算 rolling beta（使用 price-level beta：beta = Cov(target_prices, ref_prices) / Var(ref_prices)）
            # 使用 sample variance/covariance（ddof=1）
            var_ref_prices = np.var(ref_prices_array, ddof=1)
            if len(ref_prices_array) >= 2 and var_ref_prices > 1e-12:
                # 計算協方差：Cov(target_prices, ref_prices)，使用 ddof=1
                cov_matrix = np.cov(target_prices_array, ref_prices_array, ddof=1)
                cov_tr = float(cov_matrix[0, 1])
                rolling_beta = cov_tr / var_ref_prices
            else:
                rolling_beta = 0.0
            
            # 計算 spread_zscore：pair spread Z-score（繼續使用 returns）
            if len(target_returns_array) >= self.config.window_size and len(ref_returns_list) >= self.config.window_size:
                target_ret = target_returns_array[-self.config.window_size:]
                ref_ret = np.array(ref_returns_list[-self.config.window_size:])
                spread_zscore = self._compute_spread_zscore(target_ret, ref_ret, rolling_beta)
            else:
                spread_zscore = 0.0
            
            # 建立 CrossAssetFactor 實例
            factor = CrossAssetFactor(
                target_symbol=self.config.target_symbol,
                reference_symbol=ref_symbol,
                timestamp=latest_ts,
                rolling_corr=rolling_corr,
                rolling_beta=rolling_beta,
                spread_zscore=spread_zscore,
            )
            factors.append(factor)
        
        return factors
    
    def get_current_window_status(self) -> dict[str, int]:
        """
        獲取當前各 symbol 的視窗狀態（用於調試）
        
        Returns:
            dict: {symbol: return_history_length}
        """
        status = {}
        all_symbols = [self.config.target_symbol] + self.config.reference_symbols
        for symbol in all_symbols:
            status[symbol] = len(self.return_history[symbol])
        return status


# ============================================================================
# 測試骨架
# ============================================================================

if __name__ == "__main__":
    import time
    import random
    
    print("=" * 60)
    print("Step 5: Cross-Asset Factor Engine Test")
    print("=" * 60)
    
    # 建立配置
    config = CrossAssetWindowConfig(
        target_symbol="2330.TW",
        reference_symbols=["QQQ", "ES"],
        window_size=20,
    )
    
    # 建立引擎
    engine = CrossAssetFactorEngine(config)
    
    print(f"\n配置：")
    print(f"  Target: {config.target_symbol}")
    print(f"  References: {config.reference_symbols}")
    print(f"  Window Size: {config.window_size}")
    print()
    
    # 人工建立假 VolumeBar 序列
    # 為 target_symbol 與每個 reference_symbol 各建立 25 個 VolumeBar
    base_time = time.time()
    bar_count = 25
    
    # 初始化價格
    prices = {
        "2330.TW": 750.0,
        "QQQ": 400.0,
        "ES": 4500.0,
    }
    
    # 價格變化趨勢（每 Bar 的增量）
    price_deltas = {
        "2330.TW": 1.0,   # target：每 Bar +1.0
        "QQQ": 0.8,       # QQQ：每 Bar +0.8
        "ES": 0.5,        # ES：每 Bar +0.5
    }
    
    print("開始生成 VolumeBar 序列...")
    print()
    
    for i in range(bar_count):
        for symbol in ["2330.TW", "QQQ", "ES"]:
            # 更新價格（加入趨勢）
            prices[symbol] += price_deltas[symbol]
            
            # 加入少量隨機波動
            prices[symbol] += random.gauss(0, prices[symbol] * 0.001)
            
            # 建立 VolumeBar
            bar = VolumeBar(
                start_ts=base_time + i * 60.0,
                end_ts=base_time + (i + 1) * 60.0,
                symbol=symbol,
                vwap=prices[symbol],
                total_volume=random.randint(1000000, 5000000),
                tick_count=random.randint(100, 500),
                open_price=prices[symbol] - random.uniform(-0.5, 0.5),
                high_price=prices[symbol] + random.uniform(0, 1.0),
                low_price=prices[symbol] - random.uniform(0, 1.0),
                close_price=prices[symbol],
                avg_bid=prices[symbol] - 0.5,  # 簡單假設
                avg_ask=prices[symbol] + 0.5,  # 簡單假設
            )
            
            # 更新引擎
            factors = engine.update_with_bar(bar)
            
            # 顯示狀態
            if i < 5 or factors is not None:
                status = engine.get_current_window_status()
                print(f"Bar #{i+1} [{symbol}]: price={prices[symbol]:.2f}, "
                      f"window_status={status}")
            
            # 當因子計算完成時，顯示結果
            if factors:
                print(f"\n{'='*60}")
                print(f"✅ Cross-Asset Factors Computed (Bar #{i+1}):")
                print(f"{'='*60}")
                for f in factors:
                    print(f"  Target: {f.target_symbol} vs Reference: {f.reference_symbol}")
                    print(f"    Rolling Correlation: {f.rolling_corr:.4f}")
                    print(f"    Rolling Beta: {f.rolling_beta:.4f}")
                    print(f"    Spread Z-score: {f.spread_zscore}")
                    print()
    
    print("=" * 60)
    print("測試完成！")
    print("=" * 60)

