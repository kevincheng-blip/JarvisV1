"""
測試 Walk-Forward Pipeline 模組

測試 WalkForwardSimulator 的核心邏輯：時間軸處理、OOS 訊號收集等。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Sequence, Tuple
import pytest

from factor_engine.signal_factor import (
    FSignalBucket,
    FSignalConfig,
    FSignalEngine,
    FSignalFactor,
)
from factor_engine.capital_flow_factor import CapitalFlowFactor
from factor_engine.inertia_factor import InertiaFactor
from pipeline.walk_forward_config import WalkForwardConfig, WalkForwardPeriod
from pipeline.data_loader import FactorCacheEntry, FactorDataLoader
from pipeline.walk_forward_simulator import WalkForwardSimulator, SimulationResult

# ----------------------------------------------------------------------
# Dummy 因子物件：提供 FSignalEngine 會用到的欄位
# ----------------------------------------------------------------------

@dataclass
class DummyCapitalFlow:
    """
    測試用的 CapitalFlowFactor 替代品
    提供 FSignalEngine 需要的欄位：symbol, timestamp, smart_aggression_index, momentum_of_imbalance
    """
    symbol: str
    timestamp: float
    smart_aggression_index: float  # SAI
    momentum_of_imbalance: float   # MOI


@dataclass
class DummyInertia:
    """
    測試用的 InertiaFactor 替代品
    提供 FSignalEngine 需要的欄位：symbol, timestamp, inertia_sai
    """
    symbol: str
    timestamp: float
    inertia_sai: float


class DummyFactorDataLoader:
    """
    測試用的簡易 DataLoader：
    - 全部資料直接放在記憶體裡
    - 按時間與 symbol 篩選
    """
    
    def __init__(self, entries: List[FactorCacheEntry]) -> None:
        self._entries = entries
    
    def load_factors_for_period(
        self,
        start_ts: float,
        end_ts: float,
        symbols: Sequence[str],
    ) -> List[FactorCacheEntry]:
        return [
            e
            for e in self._entries
            if start_ts <= e.timestamp <= end_ts and e.symbol in symbols
        ]
    
    def get_factor_instances(
        self, entry: FactorCacheEntry
    ) -> Tuple[Optional[Any], Optional[Any]]:
        return entry.capital_flow, entry.inertia


# ----------------------------------------------------------------------
# 測試資料產生器
# ----------------------------------------------------------------------

def make_dummy_cache(symbol: str = "2330.TW") -> List[FactorCacheEntry]:
    """
    建立一組簡單但可預期的因子快取資料：
    - timestamp 以 60 秒為間隔
    - SAI / MOI / inertia_sai 做一些穩定的變化
    """
    entries: List[FactorCacheEntry] = []
    base_ts = 1_000.0
    
    for i in range(30):
        ts = base_ts + i * 60.0
        
        # 讓 SAI / inertia 有一點趨勢，MOI 當作小幅正向
        sai = 0.2 if i % 2 == 0 else -0.1
        moi = 0.3
        inertia_sai = 0.05 * (i / 30.0)
        
        # 使用正確的欄位名稱
        cf = DummyCapitalFlow(
            symbol=symbol,
            timestamp=ts,
            smart_aggression_index=sai,
            momentum_of_imbalance=moi,
        )
        inertia = DummyInertia(
            symbol=symbol,
            timestamp=ts,
            inertia_sai=inertia_sai,
        )
        
        entries.append(
            FactorCacheEntry(
                timestamp=ts,
                symbol=symbol,
                capital_flow=cf,
                inertia=inertia,
            )
        )
    
    return entries


# ----------------------------------------------------------------------
# 測試 1：單一 period、單一 symbol，基本流程
# ----------------------------------------------------------------------

def test_walk_forward_single_period_generates_oos_signals() -> None:
    """測試單一 Walk-Forward 週期能夠產生 OOS 期間的訊號"""
    symbol = "2330.TW"
    cache = make_dummy_cache(symbol=symbol)
    loader = DummyFactorDataLoader(entries=cache)
    
    # 設定一個簡單的 period：
    # - 前 10 根當訓練
    # - 後 10 根當 OOS
    base_ts = 1_000.0
    train_end = base_ts + 9 * 60.0
    oos_start = base_ts + 10 * 60.0
    oos_end = base_ts + 19 * 60.0
    
    period = WalkForwardPeriod(
        train_start_ts=base_ts,
        train_end_ts=train_end,
        oos_start_ts=oos_start,
        oos_end_ts=oos_end,
    )
    
    config = WalkForwardConfig(
        target_symbols=[symbol],
        periods=[period],
        engine_config={
            "FSignalConfig": {
                # 用預設值即可，主要測「流程」與時間區間
            }
        },
    )
    
    simulator = WalkForwardSimulator(config=config, data_loader=loader)
    results = simulator.run_simulation()
    
    # 只設定了一個 symbol 且一個 period，因此應該只會有一筆結果
    assert len(results) == 1
    
    result = results[0]
    assert isinstance(result, SimulationResult)
    assert result.symbol == symbol
    assert result.period == period
    
    # OOS 期間應該有產生一些訊號
    assert len(result.signal_history) > 0
    
    # 所有訊號都應該落在 OOS 時間區間內
    for sig in result.signal_history:
        assert period.oos_start_ts <= sig.timestamp <= period.oos_end_ts
        assert sig.symbol == symbol
        assert isinstance(sig.bucket, FSignalBucket)


# ----------------------------------------------------------------------
# 測試 2：多個 period，確保每個 period 都有對應結果
# ----------------------------------------------------------------------

def test_walk_forward_multiple_periods_returns_result_per_period() -> None:
    """測試多個 Walk-Forward 週期時，每個 period 都會產生對應的結果"""
    symbol = "2330.TW"
    cache = make_dummy_cache(symbol=symbol)
    loader = DummyFactorDataLoader(entries=cache)
    
    base_ts = 1_000.0
    
    period1 = WalkForwardPeriod(
        train_start_ts=base_ts,
        train_end_ts=base_ts + 5 * 60.0,
        oos_start_ts=base_ts + 6 * 60.0,
        oos_end_ts=base_ts + 10 * 60.0,
    )
    
    period2 = WalkForwardPeriod(
        train_start_ts=base_ts + 11 * 60.0,
        train_end_ts=base_ts + 15 * 60.0,
        oos_start_ts=base_ts + 16 * 60.0,
        oos_end_ts=base_ts + 20 * 60.0,
    )
    
    config = WalkForwardConfig(
        target_symbols=[symbol],
        periods=[period1, period2],
        engine_config={
            "FSignalConfig": {},
        },
    )
    
    simulator = WalkForwardSimulator(config=config, data_loader=loader)
    results = simulator.run_simulation()
    
    # 2 個 period × 1 個 symbol = 2 筆結果
    assert len(results) == 2
    
    # 確認每個 period 都有一筆結果
    periods_seen = {res.period for res in results}
    assert periods_seen == {period1, period2}
    
    # 每個結果的 signal_history 時間都要落在其對應的 OOS 範圍內
    for res in results:
        for sig in res.signal_history:
            assert res.period.oos_start_ts <= sig.timestamp <= res.period.oos_end_ts

