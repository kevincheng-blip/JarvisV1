"""
Walk-Forward 模擬流程核心執行器

用 WalkForwardConfig + FactorDataLoader + FSignalEngine，
在時間軸上跑多個 WF 週期，收集 OOS 期間的 F_Signal 訊號。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from factor_engine.signal_factor import (
    FSignalConfig,
    FSignalEngine,
    FSignalFactor,
)
from factor_engine.capital_flow_factor import (
    CapitalFlowEngine,
)
from factor_engine.inertia_factor import (
    InertiaWindowConfig,
    InertiaFactorEngine,
)
from pipeline.walk_forward_config import WalkForwardConfig, WalkForwardPeriod
from pipeline.data_loader import FactorDataLoader, FactorCacheEntry


@dataclass
class SimulationResult:
    """
    單一 Walk-Forward 週期的模擬結果。
    
    目前只紀錄：
    - 這個週期的 period 定義
    - symbol
    - 在 OOS 期間產生的所有 F_Signal 因子
    """
    period: WalkForwardPeriod
    symbol: str
    signal_history: List[FSignalFactor]


@dataclass
class SymbolEngines:
    """
    儲存單一標的所需的引擎實例。
    
    注意：在目前的「因子快取版」中，實際運算只用到 FSignalEngine，
    CapitalFlowEngine / InertiaFactorEngine 主要是為未來版本（從 K 線直接算因子）預留的鉤子。
    """
    cf_engine: CapitalFlowEngine
    inertia_engine: InertiaFactorEngine
    signal_engine: FSignalEngine


class WalkForwardSimulator:
    """
    Walk-Forward 模擬流程的核心執行器。
    
    ✅ 目前版本：
      - 使用固定的 FSignalConfig 參數
      - 只依賴 FactorDataLoader 提供的因子快取
      - 專注於「在時間軸上如何餵資料與收集 OOS 訊號」
    
    ❌ 尚未包含：
      - 在訓練期間自動搜尋最佳參數（Grid Search / Bayesian 等）
      - 在迴圈中動態使用 CapitalFlowEngine / InertiaFactorEngine 重新計算因子
    """
    
    def __init__(self, config: WalkForwardConfig, data_loader: FactorDataLoader) -> None:
        self.config = config
        self.data_loader = data_loader
        self._engines: Dict[str, SymbolEngines] = {}
        self._initialize_engines()
    
    # ------------------------------------------------------------------
    # 初始化所有引擎
    # ------------------------------------------------------------------
    
    def _initialize_engines(self) -> None:
        """根據 WalkForwardConfig 初始化每個標的的引擎。"""
        # 從 engine_config 取得各引擎的參數
        cf_cfg = self.config.engine_config.get("CapitalFlowConfig", {})
        inertia_cfg = self.config.engine_config.get("InertiaWindowConfig", {})
        signal_cfg = self.config.engine_config.get("FSignalConfig", {})
        
        self._engines.clear()
        
        for symbol in self.config.target_symbols:
            # CapitalFlowEngine 不使用 config，而是直接接受參數
            cf_engine = CapitalFlowEngine(
                symbol=symbol,
                window_size=cf_cfg.get("window_size", 100),
                min_points=cf_cfg.get("min_points", 10),
                mid_epsilon=cf_cfg.get("mid_epsilon", 1e-9),
                at_mid_tolerance_bp=cf_cfg.get("at_mid_tolerance_bp", 1.0),
            )
            
            # InertiaFactorEngine 使用 InertiaWindowConfig
            inertia_engine = InertiaFactorEngine(
                config=InertiaWindowConfig(
                    symbol=symbol,
                    window_size=inertia_cfg.get("window_size", 100),
                    min_effective_points=inertia_cfg.get("min_effective_points", 20),
                )
            )
            
            # FSignalEngine 使用 FSignalConfig
            signal_engine = FSignalEngine(
                config=FSignalConfig(
                    symbol=symbol,
                    w_sai=signal_cfg.get("w_sai", 0.4),
                    w_moi=signal_cfg.get("w_moi", 0.2),
                    w_inertia=signal_cfg.get("w_inertia", 0.4),
                    moi_scale=signal_cfg.get("moi_scale", 2.0),
                    strong_threshold=signal_cfg.get("strong_threshold", 0.4),
                    weak_threshold=signal_cfg.get("weak_threshold", 0.15),
                )
            )
            
            self._engines[symbol] = SymbolEngines(
                cf_engine=cf_engine,
                inertia_engine=inertia_engine,
                signal_engine=signal_engine,
            )
    
    # ------------------------------------------------------------------
    # 主流程：跑多個 Walk-Forward 週期
    # ------------------------------------------------------------------
    
    def run_simulation(self) -> List[SimulationResult]:
        """
        執行多個 Walk-Forward 週期，並收集各標的在 OOS 期間的 F_Signal 訊號。
        
        回傳：
        - List[SimulationResult]，每個 target symbol × 每個 period 各一筆結果。
        """
        all_results: List[SimulationResult] = []
        
        for idx, period in enumerate(self.config.periods):
            print(f"--- 執行 Walk-Forward 週期 {idx + 1}/{len(self.config.periods)} ---")
            print(
                f"  Train: {period.train_start_ts} ~ {period.train_end_ts}, "
                f"OOS: {period.oos_start_ts} ~ {period.oos_end_ts}"
            )
            
            # 1) 載入當前週期所需的全部因子資料
            all_data: List[FactorCacheEntry] = self.data_loader.load_factors_for_period(
                start_ts=period.train_start_ts,
                end_ts=period.oos_end_ts,
                symbols=self.config.target_symbols,
            )
            
            # 2) 重置引擎，確保每個 period 狀態獨立
            self._initialize_engines()
            
            # 3) 依時間排序
            all_data.sort(key=lambda e: e.timestamp)
            
            # 4) 迴圈跑完整個 train + OOS，但只記錄 OOS 的訊號
            oos_signal_history: Dict[str, List[FSignalFactor]] = {
                sym: [] for sym in self.config.target_symbols
            }
            
            for entry in all_data:
                symbol = entry.symbol
                if symbol not in self._engines:
                    continue
                
                engines = self._engines[symbol]
                cf_factor, inertia_factor = self.data_loader.get_factor_instances(entry)
                
                # 目前版本：只有在兩個因子都存在時，才計算 F_Signal
                if cf_factor is None or inertia_factor is None:
                    continue
                
                signal_factor = engines.signal_engine.update_with_factors(
                    capital_flow=cf_factor,
                    inertia=inertia_factor,
                )
                
                if signal_factor is None:
                    continue
                
                # 只記錄 OOS 期間的訊號
                if (
                    signal_factor.timestamp >= period.oos_start_ts
                    and signal_factor.timestamp <= period.oos_end_ts
                ):
                    oos_signal_history[symbol].append(signal_factor)
            
            # 5) 收集結果
            for symbol in self.config.target_symbols:
                all_results.append(
                    SimulationResult(
                        period=period,
                        symbol=symbol,
                        signal_history=oos_signal_history[symbol],
                    )
                )
        
        return all_results

