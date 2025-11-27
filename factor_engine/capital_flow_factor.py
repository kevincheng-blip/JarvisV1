"""
F_C 資金流基礎因子引擎（SAI & MOI）

本模組實作創世紀量化系統 Step 4：資金流基礎引擎。

核心功能：
1. CapitalFlowFactor 資料結構：定義 F_C 因子的標準格式
2. CapitalFlowEngine：計算 SAI（Smart Aggression Index）和 MOI（Momentum of Imbalance）
3. 基於 Tick 的 price/volume 和 Bid/Ask 推估多空方向

設計原則：
- 輕量狀態：只保留最近 N 筆 CapitalFlowSample
- 不依賴特定 Tick 類型：只要求欄位存在
- 適合硬體加速與向量化

作者：創世紀量化系統開發團隊
版本：v1.0
建立日期：2024-11-28
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any, Deque, Iterable, List
from collections import deque


@dataclass(frozen=True)
class CapitalFlowSample:
    """
    內部用：代表一筆資金流樣本（已經判斷好多空方向）。
    """
    timestamp: float
    symbol: str
    volume: float
    side: int  # +1 = 買方主動, -1 = 賣方主動, 0 = 中性


@dataclass(frozen=True)
class CapitalFlowFactor:
    """
    【F_C 資金流基礎因子輸出結構】

    包含兩個核心指標：
    - SAI (Smart Aggression Index)：視窗內資金多空不平衡程度
    - MOI (Momentum of Imbalance)：視窗內「不平衡的變化趨勢」

    以及輔助說明欄位：
    - window_trades：視窗內筆數
    - window_volume：視窗內總成交量
    - buy_volume / sell_volume / net_signed_volume：多空成交量拆解
    """
    timestamp: float
    symbol: str

    window_trades: int
    window_volume: float
    buy_volume: float
    sell_volume: float
    net_signed_volume: float

    smart_aggression_index: Optional[float]  # SAI ∈ [-1, 1]，若 volume=0 則為 None
    momentum_of_imbalance: Optional[float]   # MOI = recent_imbalance - early_imbalance


class CapitalFlowEngine:
    """
    【F_C 資金流基礎引擎（SAI & MOI）】

    功能：
    ------
    - 對每一筆 Tick：
        1) 用 Bid/Ask 計算 mid price
        2) 依據 price 相對 mid 的位置推估多空 side（+1 / -1 / 0）
        3) 將結果放入有限長度視窗
        4) 視窗足夠長時，計算本次的 F_C 因子（SAI & MOI）

    設計特點：
    ----------
    - 輕量狀態：只保留最近 N 筆 CapitalFlowSample
    - 不依賴特定 Tick 類型：只要求欄位存在
    - 適合之後做：
        - Numba / C++ / CUDA 平行化
        - RL 狀態輸入（state["F_C"]）
    """

    def __init__(
        self,
        symbol: Optional[str] = None,
        window_size: int = 100,
        min_points: int = 10,
        mid_epsilon: float = 1e-9,
        at_mid_tolerance_bp: float = 1.0,
    ) -> None:
        """
        Args:
            symbol:
                若指定，Engine 僅處理該標的，其它 symbol 直接略過（回傳 None）。
                若為 None，則接受所有標的。
            window_size:
                視窗內最多保留多少筆資金流樣本。
            min_points:
                至少幾筆樣本才輸出因子（避免視窗太短不穩定）。
            mid_epsilon:
                避免 mid_price 過小導致除以 0。
            at_mid_tolerance_bp:
                判斷成交價是否「明顯偏離 mid」的容忍區間（以 bp 為單位）。
                |price - mid| / mid * 10000 <= at_mid_tolerance_bp → 視為中性 (side=0)。
        """
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if min_points <= 0:
            raise ValueError("min_points must be positive")

        self.symbol = symbol
        self.window_size = window_size
        self.min_points = min_points
        self.mid_epsilon = mid_epsilon
        self.at_mid_tolerance_bp = at_mid_tolerance_bp

        self._window: Deque[CapitalFlowSample] = deque(maxlen=window_size)

    def reset(self) -> None:
        """清空內部視窗狀態。"""
        self._window.clear()

    # ---- 外部主要接口 ----

    def update_from_tick(self, tick: Any) -> Optional[CapitalFlowFactor]:
        """
        從一筆 Tick 更新資金流視窗，並嘗試計算最新的 F_C 因子。

        需求欄位：
        ----------
        tick.timestamp : float
        tick.symbol    : str
        tick.price     : float   # 成交價
        tick.volume    : float   # 成交量
        tick.bid_price : float
        tick.ask_price : float

        Returns:
            CapitalFlowFactor 或 None（當視窗尚未達 min_points 或資料無效時）
        """
        symbol = getattr(tick, "symbol", "")
        if self.symbol is not None and symbol != self.symbol:
            return None

        price = getattr(tick, "price", None)
        volume = getattr(tick, "volume", None)
        bid = getattr(tick, "bid_price", None)
        ask = getattr(tick, "ask_price", None)

        # 基本欄位檢查
        if (
            price is None
            or volume is None
            or bid is None
            or ask is None
        ):
            return None

        if volume <= 0:
            return None

        # mid price 合理性檢查
        if bid <= 0 or ask <= 0:
            return None
        if ask <= bid:
            # 停牌、錯價等情形直接略過
            return None

        mid = 0.5 * (bid + ask)
        if mid <= self.mid_epsilon:
            return None

        side = self._classify_side(price=price, mid=mid)
        sample = CapitalFlowSample(
            timestamp=float(getattr(tick, "timestamp", 0.0)),
            symbol=symbol,
            volume=float(volume),
            side=side,
        )
        self._window.append(sample)

        if len(self._window) < self.min_points:
            return None

        return self._compute_factor()

    def compute_from_ticks(self, ticks: Iterable[Any]) -> Optional[CapitalFlowFactor]:
        """
        輔助函式：一次性從一個 Tick 序列計算最新 F_C 因子。

        適用情境：
        ----------
        - 離線回測
        - 單元測試
        """
        self.reset()
        last_factor: Optional[CapitalFlowFactor] = None
        for t in ticks:
            last_factor = self.update_from_tick(t)
        return last_factor

    # ---- 內部邏輯 ----

    def _classify_side(self, price: float, mid: float) -> int:
        """
        根據成交價相對 mid 的位置，判斷本筆成交為：
        +1 = 買方主動
        -1 = 賣方主動
         0 = 接近 mid，視為中性
        """
        bp_diff = (price - mid) / mid * 10_000.0  # basis points

        if bp_diff > self.at_mid_tolerance_bp:
            return +1
        if bp_diff < -self.at_mid_tolerance_bp:
            return -1
        return 0

    def _compute_factor(self) -> CapitalFlowFactor:
        """
        從目前視窗內的樣本計算 F_C 因子（SAI & MOI）。
        """
        samples: List[CapitalFlowSample] = list(self._window)
        latest = samples[-1]

        window_trades = len(samples)
        window_volume = sum(s.volume for s in samples)

        buy_volume = sum(s.volume for s in samples if s.side > 0)
        sell_volume = sum(s.volume for s in samples if s.side < 0)
        net_signed_volume = buy_volume - sell_volume

        if window_volume <= 0:
            sai: Optional[float] = None
        else:
            sai = net_signed_volume / window_volume  # ∈ [-1, 1]

        # ---- MOI 計算：視窗拆成前半段 & 後半段 ----
        half = window_trades // 2
        early_samples = samples[:half]
        recent_samples = samples[half:]

        def _imbalance(sub: List[CapitalFlowSample]) -> Optional[float]:
            if not sub:
                return None
            vol = sum(s.volume for s in sub)
            if vol <= 0:
                return None
            net_vol = sum(s.volume * s.side for s in sub)
            return net_vol / vol

        early_imbalance = _imbalance(early_samples)
        recent_imbalance = _imbalance(recent_samples)

        if early_imbalance is not None and recent_imbalance is not None:
            moi: Optional[float] = recent_imbalance - early_imbalance
        else:
            moi = None

        return CapitalFlowFactor(
            timestamp=latest.timestamp,
            symbol=latest.symbol,
            window_trades=window_trades,
            window_volume=window_volume,
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            net_signed_volume=net_signed_volume,
            smart_aggression_index=sai,
            momentum_of_imbalance=moi,
        )

