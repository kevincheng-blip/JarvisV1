"""
Path A 整合 Smoke Test

測試 Path A 完整回測流程，使用真實的 Alpha Engine、Risk Model、Optimizer。
這是「最小可運作」的整合測試，確保 Path A 可以正常執行。
"""

import pytest
import pandas as pd

from jgod.path_a.path_a_schema import PathAConfig
from jgod.path_a.path_a_backtest import PathARunContext, run_path_a_backtest
from jgod.path_a.mock_data_loader import MockPathADataLoader
from jgod.alpha_engine.alpha_engine import AlphaEngine
from jgod.risk.risk_model import MultiFactorRiskModel
from jgod.optimizer.optimizer_core_v2 import OptimizerCoreV2
from jgod.learning.error_learning_engine import ErrorLearningEngine


@pytest.mark.slow
def test_path_a_integration_smoke():
    """
    Path A 整合 Smoke Test
    
    測試完整的 Path A 回測流程：
    - Mock Data Loader
    - Alpha Engine (Basic)
    - Risk Model (Basic)
    - Optimizer (V2)
    - Error Learning Engine
    """
    # 1. 建立配置
    config = PathAConfig(
        start_date="2024-01-01",
        end_date="2024-01-31",  # 一個月的資料
        universe=["2330.TW", "2317.TW", "2303.TW"],
        rebalance_frequency="M",
        experiment_name="test_path_a_integration_smoke",
        initial_nav=100.0,
        transaction_cost_bps=5.0,
    )
    
    # 2. 初始化各模組
    data_loader = MockPathADataLoader(seed=42)
    alpha_engine = AlphaEngine(enable_micro_momentum=False)
    
    # Risk Model 需要先 fit
    price_frame = data_loader.load_price_frame(config)
    risk_model = MultiFactorRiskModel()
    # 簡化：只使用前 60 天來 fit risk model
    risk_model.fit(
        returns_df=price_frame.pct_change().dropna(),
        universe=list(config.universe),
    )
    
    optimizer = OptimizerCoreV2()
    error_engine = ErrorLearningEngine()
    
    # 3. 建立執行上下文
    ctx = PathARunContext(
        config=config,
        data_loader=data_loader,
        alpha_engine=alpha_engine,
        risk_model=risk_model,
        optimizer=optimizer,
        error_engine=error_engine,
        error_bridge=None,  # 簡化測試，不使用 error bridge
    )
    
    # 4. 執行回測
    result = run_path_a_backtest(ctx)
    
    # 5. 基本驗證
    assert isinstance(result, PathABacktestResult)
    assert not result.nav_series.empty, "NAV series should not be empty"
    assert not result.return_series.empty, "Return series should not be empty"
    assert len(result.portfolio_snapshots) > 0, "Should have at least one portfolio snapshot"
    
    # 6. 驗證 NAV 合理性
    assert (result.nav_series > 0).all(), "All NAV values should be positive"
    assert result.nav_series.iloc[0] == config.initial_nav, "Initial NAV should match config"
    
    # 7. 驗證 portfolio snapshots
    for snapshot in result.portfolio_snapshots:
        assert snapshot.date is not None
        assert len(snapshot.symbols) == len(config.universe)
        assert snapshot.nav > 0
        # 權重應該合理（總和約等於 1，允許誤差）
        weights_sum = snapshot.weights.abs().sum()
        assert weights_sum <= 1.5, f"Weights sum should be reasonable, got {weights_sum}"
    
    # 8. 驗證日期索引對齊
    assert len(result.nav_series) == len(result.return_series), "NAV and return series should have same length"
    
    print(f"✅ Path A integration smoke test passed")
    print(f"   Dates: {len(result.nav_series)}")
    print(f"   Snapshots: {len(result.portfolio_snapshots)}")
    print(f"   Final NAV: {result.nav_series.iloc[-1]:.2f}")


@pytest.mark.slow
def test_path_a_with_error_bridge():
    """
    測試 Path A 與 Error Bridge 的整合
    """
    from jgod.path_a.path_a_error_bridge import PathAErrorBridge
    
    config = PathAConfig(
        start_date="2024-01-01",
        end_date="2024-01-31",
        universe=["2330.TW", "2317.TW"],
        rebalance_frequency="M",
        experiment_name="test_path_a_error_bridge",
    )
    
    data_loader = MockPathADataLoader(seed=42)
    alpha_engine = AlphaEngine()
    
    price_frame = data_loader.load_price_frame(config)
    risk_model = MultiFactorRiskModel()
    risk_model.fit(
        returns_df=price_frame.pct_change().dropna(),
        universe=list(config.universe),
    )
    
    optimizer = OptimizerCoreV2()
    error_engine = ErrorLearningEngine()
    error_bridge = PathAErrorBridge()
    
    ctx = PathARunContext(
        config=config,
        data_loader=data_loader,
        alpha_engine=alpha_engine,
        risk_model=risk_model,
        optimizer=optimizer,
        error_engine=error_engine,
        error_bridge=error_bridge,
    )
    
    result = run_path_a_backtest(ctx)
    
    # 基本驗證
    assert isinstance(result, PathABacktestResult)
    assert not result.nav_series.empty

