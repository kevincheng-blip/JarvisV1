"""
F_Orderbook 微觀流動性因子引擎

本模組實作創世紀量化系統 Step 3：微觀因子硬體加速（F_Orderbook）。

核心功能：
1. OrderbookFactor 資料結構：定義 F_Orderbook 因子的標準格式
2. OrderbookFactorEngine：無狀態、硬體加速友善的因子計算引擎
3. 基於 Bid1/Ask1 的即時計算：Mid、Spread、LCI (Liquidity Cost Index)

設計原則：
- 完全無狀態 (Stateless)：每個 Tick 獨立計算，適合硬體加速與向量化
- 僅依賴 Bid1 / Ask1：不需要整本 Orderbook，也不需要歷史視窗
- 嚴格檢查 Bid / Ask 合理性：避免錯價或停牌噪音污染因子

作者：創世紀量化系統開發團隊
版本：v1.0
建立日期：2024-11-28
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any


@dataclass(frozen=True)
class OrderbookFactor:
    """
    【F_Orderbook 微觀流動性因子輸出】

    專注於「單一 Tick 的 Bid1 / Ask1」即時計算，設計給硬體加速與高頻場景。

    欄位說明：
    ----------
    timestamp:
        因子所對應 Tick 的時間戳（通常使用原始 UnifiedTick 的 timestamp）。

    symbol:
        標的代碼（例如 "2330.TW"）。

    mid_price:
        買賣中點價格 (Quote Midpoint) = (Bid + Ask) / 2。

    spread:
        絕對價差 (Ask - Bid)。

    rel_spread_bp:
        相對價差（Basis Points, 萬分之幾）= (spread / mid_price) * 10000。

    liquidity_cost_index:
        流動性成本指數 (LCI)，目前等同於 rel_spread_bp。
        LCI 越高 → 流動性越差、交易成本越高。
    """
    timestamp: float
    symbol: str
    mid_price: float
    spread: float
    rel_spread_bp: float
    liquidity_cost_index: float


class OrderbookFactorEngine:
    """
    【F_Orderbook 微觀因子計算引擎】

    設計原則：
    ----------
    - 完全無狀態 (Stateless)：每個 Tick 獨立計算，非常適合硬體加速與向量化。
    - 僅依賴 Bid1 / Ask1：不需要整本 Orderbook，也不需要歷史視窗。
    - 嚴格檢查 Bid / Ask 合理性：避免錯價或停牌噪音污染因子。

    使用方式：
    ----------
    engine = OrderbookFactorEngine(symbol="2330.TW")
    factor = engine.calculate_factor(tick)  # tick 需至少有 timestamp/symbol/bid_price/ask_price
    """

    def __init__(
        self,
        symbol: Optional[str] = None,
        price_epsilon: float = 1e-9,
    ) -> None:
        """
        Args:
            symbol:
                若指定，Engine 只處理該標的，其它 symbol 會直接略過（回傳 None）。
                若為 None，則接受所有標的。
            price_epsilon:
                用於避免除以 0 的極小數判斷門檻。
        """
        self.symbol = symbol
        self.price_epsilon = price_epsilon

    def calculate_factor(self, tick: Any) -> Optional[OrderbookFactor]:
        """
        處理一個 UnifiedTick（或任意具有相同欄位的物件），計算 F_Orderbook。

        需求欄位：
        ----------
        tick.timestamp : float
        tick.symbol    : str
        tick.bid_price : float
        tick.ask_price : float

        Returns:
            OrderbookFactor 或 None（當資料不合法或 symbol 不匹配時）
        """
        # 1. 若指定了 symbol，過濾不同標的
        tick_symbol = getattr(tick, "symbol", "")
        if self.symbol is not None and tick_symbol != self.symbol:
            return None

        bid = getattr(tick, "bid_price", None)
        ask = getattr(tick, "ask_price", None)

        # 2. 確保 Bid / Ask 存在且合理
        if bid is None or ask is None:
            return None

        if bid <= 0 or ask <= 0:
            return None

        # ask <= bid 多半代表停牌、錯價或特殊狀態，直接略過
        if ask <= bid:
            return None

        # 3. 核心計算：Mid / Spread / LCI
        spread = ask - bid
        mid_price = (ask + bid) / 2.0

        # 避免極端錯價導致除以 0
        if mid_price <= self.price_epsilon:
            return None

        # 相對價差 (bp)
        rel_spread_bp = (spread / mid_price) * 10000.0

        # 流動性成本指數（目前 == 相對價差bp，未來可在此擴充映射關係）
        liquidity_cost_index = rel_spread_bp

        return OrderbookFactor(
            timestamp=float(getattr(tick, "timestamp", 0.0)),
            symbol=tick_symbol,
            mid_price=mid_price,
            spread=spread,
            rel_spread_bp=rel_spread_bp,
            liquidity_cost_index=liquidity_cost_index,
        )

    # 提供一個純函式版本，方便之後做向量化 / C++ / GPU 實作對照。
    @staticmethod
    def calculate_from_bid_ask(
        timestamp: float,
        symbol: str,
        bid_price: float,
        ask_price: float,
        price_epsilon: float = 1e-9,
    ) -> Optional[OrderbookFactor]:
        """
        硬體友善接口：直接傳入 bid/ask 數值計算 F_Orderbook。

        這個函式不依賴 UnifiedTick 結構，方便之後做 C/CUDA/Numba 等實作。
        """
        if bid_price <= 0 or ask_price <= 0:
            return None

        if ask_price <= bid_price:
            return None

        spread = ask_price - bid_price
        mid_price = (ask_price + bid_price) / 2.0

        if mid_price <= price_epsilon:
            return None

        rel_spread_bp = (spread / mid_price) * 10000.0
        liquidity_cost_index = rel_spread_bp

        return OrderbookFactor(
            timestamp=timestamp,
            symbol=symbol,
            mid_price=mid_price,
            spread=spread,
            rel_spread_bp=rel_spread_bp,
            liquidity_cost_index=liquidity_cost_index,
        )

