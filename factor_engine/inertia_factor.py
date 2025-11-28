"""
資金流慣性因子引擎（F_Inertia）：Step 6

本模組實作創世紀量化系統 Step 6：資金流慣性因子引擎。

核心功能：
1. InertiaWindowConfig：慣性窗口配置
2. InertiaFactor：慣性因子輸出結構
3. InertiaFactorEngine：基於 F_C (CapitalFlowFactor) 的長期資金慣性計算

設計原則：
- 輸入：CapitalFlowFactor (至少包含 symbol, timestamp, smart_aggression_index)
- 輸出：InertiaFactor（當歷史資料足夠時）
- 使用 EMA 或簡單平均計算長期慣性

作者：創世紀量化系統開發團隊
版本：v1.0
建立日期：2024-11-28
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Deque
from collections import deque, defaultdict
import numpy as np

from .capital_flow_factor import CapitalFlowFactor


# ============================================================================
# 資料結構定義
# ============================================================================

@dataclass(frozen=True)
class InertiaWindowConfig:
    """
    慣性因子計算窗口配置
    
    Attributes:
        symbol: 目標標的，例如 "2330.TW"
        window_size: 慣性窗口大小（用 F_C 因子筆數計），預設 100
        min_effective_points: 至少多少個點才開始輸出因子，預設 20
    """
    symbol: str
    window_size: int = 100
    min_effective_points: int = 20
    
    def __post_init__(self):
        """驗證配置參數"""
        if self.window_size <= 0:
            raise ValueError("window_size must be positive")
        if self.min_effective_points <= 0:
            raise ValueError("min_effective_points must be positive")
        if self.min_effective_points > self.window_size:
            raise ValueError("min_effective_points must be <= window_size")


@dataclass(frozen=True)
class InertiaFactor:
    """
    資金流慣性因子輸出結構
    
    代表單一時間點的慣性因子輸出。
    
    Attributes:
        symbol: 股票代號
        timestamp: 因子計算時間戳
        inertia_sai: 長期資金慣性（基於 SAI 平均），範圍 [-1, 1]
            - inertia_sai > 0：長期偏多
            - inertia_sai < 0：長期偏空
            - 接近 0：長期拉鋸
    
    說明：
        inertia_sai 是最近 window_size 筆 SAI 值的平均，反映長期的資金流動慣性。
        正值表示長期資金偏向買方，負值表示長期資金偏向賣方。
    """
    symbol: str
    timestamp: float
    inertia_sai: float


# ============================================================================
# 慣性因子引擎
# ============================================================================

class InertiaFactorEngine:
    """
    基於 F_C (CapitalFlowFactor) 的長期資金慣性引擎。
    
    功能：
    - 輸入：CapitalFlowFactor (至少包含 symbol, timestamp, smart_aggression_index)
    - 輸出：InertiaFactor（當歷史資料足夠時）
    
    設計特點：
    - 使用滾動窗口計算長期慣性
    - 只對配置中指定的 symbol 計算慣性
    - 當歷史資料不足時，不輸出因子
    """
    
    def __init__(self, config: InertiaWindowConfig):
        """
        初始化慣性因子引擎
        
        Args:
            config: 慣性窗口配置（symbol, window_size, min_effective_points）
        """
        self.config = config
        
        # 儲存各 symbol 的歷史 SAI 值（Deque[float]）
        self._sai_history: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=config.window_size))
        
        # 儲存對應時間戳（方便除錯 / 測試）
        self._ts_history: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=config.window_size))
    
    def reset(self) -> None:
        """清空所有歷史資料，重置引擎狀態"""
        self._sai_history.clear()
        self._ts_history.clear()
    
    def update_with_capital_flow(
        self, 
        factor: CapitalFlowFactor
    ) -> Optional[InertiaFactor]:
        """
        更新單筆 CapitalFlowFactor，並視情況回傳 InertiaFactor。
        
        Args:
            factor: CapitalFlowFactor 實例（需包含 symbol, timestamp, smart_aggression_index）
        
        Returns:
            InertiaFactor: 當歷史資料足夠時回傳慣性因子，否則回傳 None
        
        邏輯：
            - 若 symbol 不符 config.symbol，只保留該 symbol 的歷史但不會計算因子
            - 當歷史 SAI 筆數 < config.min_effective_points 時，回傳 None
            - 否則計算 inertia_sai = 最近 window_size 筆 SAI 的平均
        """
        # 只處理配置中指定的 symbol
        if factor.symbol != self.config.symbol:
            # 可以選擇保留其他 symbol 的歷史，但不計算因子
            return None
        
        # 檢查 SAI 是否有效
        if factor.smart_aggression_index is None:
            return None
        
        # 更新歷史
        history = self._sai_history[factor.symbol]
        ts_history = self._ts_history[factor.symbol]
        
        history.append(factor.smart_aggression_index)
        ts_history.append(factor.timestamp)
        
        # 檢查歷史資料是否足夠
        if len(history) < self.config.min_effective_points:
            return None
        
        # 計算長期慣性（最近 window_size 筆 SAI 的平均）
        # 由於使用了 maxlen，history 最多只會保留 window_size 筆
        inertia_sai = float(np.mean(history))
        
        # 確保在 [-1, 1] 之間，避免極端數值
        inertia_sai = float(max(-1.0, min(1.0, inertia_sai)))
        
        # 回傳慣性因子
        return InertiaFactor(
            symbol=factor.symbol,
            timestamp=factor.timestamp,
            inertia_sai=inertia_sai,
        )
    
    def get_current_history_length(self, symbol: Optional[str] = None) -> int:
        """
        獲取當前歷史資料長度（用於調試）
        
        Args:
            symbol: 股票代號，若為 None 則使用 config.symbol
        
        Returns:
            歷史資料長度
        """
        sym = symbol or self.config.symbol
        return len(self._sai_history.get(sym, deque()))

