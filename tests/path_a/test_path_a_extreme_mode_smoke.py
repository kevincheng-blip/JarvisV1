"""
Path A Extreme Mode Smoke Test

測試 Path A Extreme Mode 的完整回測流程。
使用 Extreme 版本的 Data Loader、Alpha Engine、Risk Model、Execution Engine。
"""

import pytest
import pandas as pd

from jgod.path_a.path_a_schema import PathAConfig
from jgod.path_a.path_a_backtest import PathARunContext, run_path_a_backtest
from jgod.path_a.mock_data_loader_extreme import MockPathADataLoaderExtreme
from jgod.alpha_engine.alpha_engine_extreme import AlphaEngineExtreme
from jgod.risk.risk_model_extreme import MultiFactorRiskModelExtreme
from jgod.optimizer.optimizer_core_v2 import OptimizerCoreV2
from jgod.learning.error_learning_engine import ErrorLearningEngine


@pytest.mark.slow
def test_path_a_extreme_mode_smoke():
    """
    Path A Extreme Mode Smoke Test
    
    測試 Extreme Mode 的完整回測流程：
    - Extreme Mock Data Loader（OU process, volatility regimes）
    - Alpha Engine Extreme（更複雜的因子）
    - Risk Model Extreme（PCA 因子模型）
    - Optimizer V2
    """
    # 1. 建立配置
    config = PathAConfig(
        start_date="2024-01-01",
        end_date="2024-01-31",  # 一個月的資料
        universe=["2330.TW", "2317.TW", "2303.TW"],
        rebalance_frequency="M",
        experiment_name="test_path_a_extreme_mode_smoke",
        initial_nav=100.0,
        transaction_cost_bps=5.0,
    )
    
    # 2. 初始化 Extreme Mode 模組
    data_loader = MockPathADataLoaderExtreme(seed=42)
    alpha_engine = AlphaEngineExtreme()
    
    # Risk Model Extreme 需要先 fit
    price_frame = data_loader.load_price_frame(config)
    risk_model = MultiFactorRiskModelExtreme()
    # 使用 price_frame 計算 returns 來 fit
    returns_df = price_frame.pct_change().dropna()
    if not returns_df.empty:
        risk_model.fit(
            returns_df=returns_df,
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
        error_bridge=None,
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
    
    # 7. Extreme Mode 特定驗證
    # 檢查是否有至少一次再平衡（因為使用 M 頻率，至少應該有一次）
    assert len(result.portfolio_snapshots) >= 1, "Should have at least one rebalance"
    
    print(f"✅ Path A Extreme Mode smoke test passed")
    print(f"   Dates: {len(result.nav_series)}")
    print(f"   Snapshots: {len(result.portfolio_snapshots)}")
    print(f"   Final NAV: {result.nav_series.iloc[-1]:.2f}")


@pytest.mark.slow
def test_path_a_extreme_mode_with_extended_period():
    """
    測試 Extreme Mode 在較長期間的表現
    """
    config = PathAConfig(
        start_date="2024-01-01",
        end_date="2024-03-31",  # 3 個月的資料
        universe=["2330.TW", "2317.TW"],
        rebalance_frequency="M",
        experiment_name="test_path_a_extreme_extended",
    )
    
    data_loader = MockPathADataLoaderExtreme(seed=42)
    alpha_engine = AlphaEngineExtreme()
    
    price_frame = data_loader.load_price_frame(config)
    risk_model = MultiFactorRiskModelExtreme()
    returns_df = price_frame.pct_change().dropna()
    if not returns_df.empty:
        risk_model.fit(returns_df=returns_df, universe=list(config.universe))
    
    optimizer = OptimizerCoreV2()
    error_engine = ErrorLearningEngine()
    
    ctx = PathARunContext(
        config=config,
        data_loader=data_loader,
        alpha_engine=alpha_engine,
        risk_model=risk_model,
        optimizer=optimizer,
        error_engine=error_engine,
        error_bridge=None,
    )
    
    result = run_path_a_backtest(ctx)
    
    # 驗證
    assert isinstance(result, PathABacktestResult)
    assert len(result.nav_series) > 60, "Should have at least 60 trading days for 3 months"
    assert (result.nav_series > 0).all()

