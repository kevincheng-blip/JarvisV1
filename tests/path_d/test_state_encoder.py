"""
State Encoder 測試
"""

import pytest
import numpy as np

from jgod.path_d.rl_state_encoder import (
    build_pathd_state_from_pathb,
    encode_state_to_vector,
)
from jgod.path_d.path_d_types import PathDState
from jgod.path_b.path_b_engine import PathBWindowResult
from jgod.path_a.path_a_schema import PathABacktestResult, PathAConfig
import pandas as pd


@pytest.fixture
def sample_window_result():
    """建立一個範例 PathBWindowResult"""
    # 建立一個簡單的 PathAConfig
    config = PathAConfig(
        start_date="2023-01-01",
        end_date="2023-12-31",
        universe=["AAPL", "GOOGL"],
    )
    
    # 建立一個簡單的 PathABacktestResult
    backtest_result = PathABacktestResult(
        config=config,
        nav_series=pd.Series([100.0, 105.0, 110.0]),
        return_series=pd.Series([0.0, 0.05, 0.048]),
        portfolio_snapshots=[],
    )
    
    window_result = PathBWindowResult(
        window_id=1,
        train_start="2020-01-01",
        train_end="2022-12-31",
        test_start="2023-01-01",
        test_end="2023-12-31",
        test_result=backtest_result,
        sharpe_ratio=1.5,
        max_drawdown=-15.0,
        total_return=0.2,
        turnover_rate=50.0,
        governance_events=[],
    )
    
    return window_result


def test_build_pathd_state(sample_window_result):
    """測試 PathDState 建立"""
    current_params = {
        "sharpe_floor": 1.0,
        "max_drawdown_limit": 15.0,
        "turnover_limit": 100.0,
        "te_max": 4.0,
        "mode": "basic",
    }
    
    state = build_pathd_state_from_pathb(
        window_result=sample_window_result,
        current_params=current_params,
        recent_windows=[],
    )
    
    assert isinstance(state, PathDState)
    assert state.sharpe_last == 1.5
    assert state.max_drawdown_last == -15.0
    assert state.current_sharpe_floor == 1.0
    assert state.mode_id == 0  # basic


def test_encode_state_to_vector(sample_window_result):
    """測試狀態向量編碼"""
    current_params = {
        "sharpe_floor": 1.0,
        "max_drawdown_limit": 15.0,
        "turnover_limit": 100.0,
        "te_max": 4.0,
        "mode": "basic",
    }
    
    state = build_pathd_state_from_pathb(
        window_result=sample_window_result,
        current_params=current_params,
        recent_windows=[],
    )
    
    vector = encode_state_to_vector(state)
    
    # 檢查向量長度（PathDState 有 12 個欄位）
    assert len(vector) == 12
    assert vector.dtype == np.float32
    
    # 檢查沒有 NaN
    assert not np.isnan(vector).any()
    
    # 檢查數值範圍合理（已做 clip）
    assert np.all(vector >= -10.0)
    assert np.all(vector <= 10.0)


def test_encode_state_extreme_mode(sample_window_result):
    """測試 Extreme 模式的 state encoding"""
    current_params = {
        "sharpe_floor": 1.5,
        "max_drawdown_limit": 20.0,
        "turnover_limit": 150.0,
        "te_max": 5.0,
        "mode": "extreme",
    }
    
    state = build_pathd_state_from_pathb(
        window_result=sample_window_result,
        current_params=current_params,
        recent_windows=[],
    )
    
    assert state.mode_id == 1  # extreme
    
    vector = encode_state_to_vector(state)
    assert len(vector) == 12
    assert not np.isnan(vector).any()

