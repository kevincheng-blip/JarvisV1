"""
訊號生成因子引擎（F_Signal）：Step 7

本模組實作創世紀量化系統 Step 7：訊號生成因子引擎。

核心功能：
1. FSignalConfig：訊號生成配置（權重、閾值）
2. FSignalBucket：訊號分桶類型（strong_buy, weak_buy, neutral, weak_sell, strong_sell）
3. FSignalFactor：綜合交易訊號因子輸出結構
4. FSignalEngine：整合 CapitalFlowFactor 與 InertiaFactor 生成綜合訊號

設計原則：
- 輸入：CapitalFlowFactor（含 SAI、MOI）+ InertiaFactor（含 inertia_sai）
- 輸出：FSignalFactor（含 raw_score、bucket）
- 用於戰情室中文解釋層、UI 儀表板決策面板、未來 RL reward / policy reference

作者：創世紀量化系統開發團隊
版本：v1.0
建立日期：2024-11-28
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum

from .capital_flow_factor import CapitalFlowFactor
from .inertia_factor import InertiaFactor


# ============================================================================
# 訊號分桶類型
# ============================================================================

class FSignalBucket(str, Enum):
    """訊號分桶類型"""
    STRONG_BUY = "strong_buy"
    WEAK_BUY = "weak_buy"
    NEUTRAL = "neutral"
    WEAK_SELL = "weak_sell"
    STRONG_SELL = "strong_sell"


# ============================================================================
# 資料結構定義
# ============================================================================

@dataclass(frozen=True)
class FSignalConfig:
    """
    F_Signal 設定：
    - 決定權重
    - 決定 MOI 縮放
    - 決定訊號分桶閾值
    
    Attributes:
        symbol: 股票代號
        w_sai: SAI 權重（預設 0.4）
        w_moi: MOI 權重（預設 0.2）
        w_inertia: Inertia 權重（預設 0.4）
        moi_scale: MOI 縮放係數（預設 2.0），將 MOI 縮放後再裁切到 [-1, 1]
        strong_threshold: 強訊號閾值（預設 0.4），> 0.4 → 強買；< -0.4 → 強賣
        weak_threshold: 弱訊號閾值（預設 0.15），介於 weak_threshold ~ strong_threshold → 弱買/弱賣
    """
    symbol: str
    w_sai: float = 0.4
    w_moi: float = 0.2
    w_inertia: float = 0.4
    moi_scale: float = 2.0
    strong_threshold: float = 0.4
    weak_threshold: float = 0.15
    
    def __post_init__(self):
        """驗證配置參數"""
        if self.moi_scale <= 0:
            raise ValueError("moi_scale must be positive")
        if self.weak_threshold <= 0:
            raise ValueError("weak_threshold must be positive")
        if self.weak_threshold >= self.strong_threshold:
            raise ValueError("weak_threshold must be < strong_threshold")
        if self.strong_threshold > 1.0:
            raise ValueError("strong_threshold must be <= 1.0")


@dataclass(frozen=True)
class FSignalFactor:
    """
    綜合交易訊號因子：
    
    - raw_score: 綜合分數，介於 [-1, 1]
    - bucket: 離散決策標籤（strong_buy, weak_buy, neutral, weak_sell, strong_sell）
    
    Attributes:
        symbol: 股票代號
        timestamp: 因子計算時間戳
        raw_score: 綜合分數（加權和），範圍 [-1, 1]
        bucket: 訊號分桶類型
    """
    symbol: str
    timestamp: float
    raw_score: float
    bucket: FSignalBucket
    
    def __post_init__(self):
        """確保 raw_score 在 [-1, 1] 範圍內"""
        # 由於是 frozen dataclass，我們只能在創建時確保值正確
        # 實際的裁切會在計算端完成
        pass


# ============================================================================
# 訊號生成引擎
# ============================================================================

class FSignalEngine:
    """
    F_Signal 訊號生成引擎。
    
    功能：
    - 每次呼叫 update_with_factors，輸入當前的 CapitalFlowFactor + Optional[InertiaFactor]
    - 若該 symbol 的 Inertia 尚未準備好，可回傳 None（等待長期慣性成形）
    - 一旦條件足夠，即產生 FSignalFactor
    
    設計特點：
    - 整合 CapitalFlowFactor（SAI、MOI）與 InertiaFactor（inertia_sai）
    - 使用加權和計算 raw_score
    - 根據閾值將 raw_score 分桶為離散決策標籤
    """
    
    def __init__(self, config: FSignalConfig):
        """
        初始化訊號生成引擎
        
        Args:
            config: F_Signal 設定（權重、閾值等）
        """
        self.config = config
        # 以 symbol 為 key，維持最新的 inertia_sai，避免 inertia 每筆都必須同時到達
        self._latest_inertia: Dict[str, InertiaFactor] = {}
    
    def reset(self) -> None:
        """清空所有歷史資料，重置引擎狀態"""
        self._latest_inertia.clear()
    
    def update_with_factors(
        self,
        capital_flow: CapitalFlowFactor,
        inertia: Optional[InertiaFactor] = None,
    ) -> Optional[FSignalFactor]:
        """
        更新因子並生成綜合訊號
        
        Args:
            capital_flow: CapitalFlowFactor 實例（需包含 SAI、MOI）
            inertia: 可選的 InertiaFactor 實例（若為 None，則使用最新的 inertia）
        
        Returns:
            FSignalFactor: 當條件滿足時回傳綜合訊號，否則回傳 None
        
        邏輯：
            - 只處理 capital_flow.symbol == config.symbol 的資料
            - 如果 inertia 不為 None 且 symbol 符合，更新 _latest_inertia
            - 若該 symbol 的最新 InertiaFactor 不存在，回傳 None
            - 計算加權和得到 raw_score
            - 根據 raw_score 和閾值分桶
        """
        # 只處理配置中指定的 symbol
        if capital_flow.symbol != self.config.symbol:
            return None
        
        # 檢查 SAI 和 MOI 是否有效
        if capital_flow.smart_aggression_index is None:
            return None
        if capital_flow.momentum_of_imbalance is None:
            return None
        
        # 如果傳入了 inertia，更新最新值
        if inertia is not None and inertia.symbol == self.config.symbol:
            self._latest_inertia[inertia.symbol] = inertia
        
        # 取得該 symbol 的最新 InertiaFactor
        inertia_factor = self._latest_inertia.get(capital_flow.symbol)
        if inertia_factor is None:
            return None
        
        # 從 capital_flow 取出 sai 與 moi
        sai = capital_flow.smart_aggression_index
        moi = capital_flow.momentum_of_imbalance
        
        # 對 moi 做縮放與裁切
        moi_scaled = moi / self.config.moi_scale
        # 裁切到 [-1, 1]
        moi_scaled = max(-1.0, min(1.0, float(moi_scaled)))
        
        # 取出 inertia_sai
        inertia_sai = inertia_factor.inertia_sai
        
        # 計算 raw_score（加權和）
        score = (
            self.config.w_sai * sai
            + self.config.w_moi * moi_scaled
            + self.config.w_inertia * inertia_sai
        )
        # 裁切到 [-1, 1]
        score = float(max(-1.0, min(1.0, score)))
        
        # 根據 score 和 threshold 分桶
        bucket = self._bucket_from_score(score)
        
        # 回傳 FSignalFactor
        return FSignalFactor(
            symbol=capital_flow.symbol,
            timestamp=capital_flow.timestamp,
            raw_score=score,
            bucket=bucket,
        )
    
    def _bucket_from_score(self, score: float) -> FSignalBucket:
        """
        根據 raw_score 和閾值決定訊號分桶
        
        Args:
            score: raw_score（範圍 [-1, 1]）
        
        Returns:
            FSignalBucket: 訊號分桶類型
        """
        st = self.config.strong_threshold
        wt = self.config.weak_threshold
        
        if score >= st:
            return FSignalBucket.STRONG_BUY
        if score >= wt:
            return FSignalBucket.WEAK_BUY
        if score <= -st:
            return FSignalBucket.STRONG_SELL
        if score <= -wt:
            return FSignalBucket.WEAK_SELL
        return FSignalBucket.NEUTRAL

