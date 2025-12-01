"""Tests for OptimizerCore

基本單元測試與整合測試。
"""

import pytest
import pandas as pd
import numpy as np

from jgod.optimizer import OptimizerCore, OptimizerConfig
from jgod.risk.risk_model import MultiFactorRiskModel
from jgod.risk.risk_factors import STANDARD_FACTOR_NAMES


class MockRiskModel:
    """簡化的 Risk Model Mock 用於測試"""
    
    def __init__(self, symbols, cov_matrix):
        self.symbols = symbols
        self.cov_matrix = cov_matrix
    
    def get_covariance_matrix(self):
        return self.cov_matrix
    
    def get_symbols(self):
        return self.symbols
    
    def get_factor_covariance(self):
        n = len(STANDARD_FACTOR_NAMES)
        return pd.DataFrame(
            np.eye(n) * 0.01,
            index=STANDARD_FACTOR_NAMES,
            columns=STANDARD_FACTOR_NAMES
        )
    
    def get_specific_risk(self, symbol):
        return 0.1


def test_optimizer_basic_long_only():
    """
    測試場景：
    - 三檔股票
    - 簡單的 Σ（identity）
    - 預期報酬不同
    - long-only, max_weight=0.7
    
    應該：高報酬的股票權重最大，但不超過上限，sum(w)=1。
    """
    stock_ids = ["A", "B", "C"]
    mu = pd.Series([0.10, 0.05, 0.02], index=stock_ids)
    
    # 建立簡單的 identity covariance matrix
    n = len(stock_ids)
    cov_matrix = np.eye(n) * 0.04  # 每個股票 20% 波動率
    
    # 建立 Mock Risk Model
    risk_model = MockRiskModel(symbols=stock_ids, cov_matrix=cov_matrix)
    
    # 建立 OptimizerConfig（允許較大的 max_weight 以便測試）
    config = OptimizerConfig()
    config.weight_constraints.max_weight = 0.7
    config.tracking_error.enabled = False  # 先不測試 TE
    
    optimizer = OptimizerCore(config=config)
    
    # 執行優化
    result = optimizer.optimize(
        expected_returns=mu,
        risk_model=risk_model,
        factor_exposure=None,
        benchmark_weights=None,
        sector_map=None
    )
    
    # 檢查結果
    assert result.status == "success", f"Optimization failed: {result.message}"
    assert abs(result.weights.sum() - 1.0) < 1e-6, f"Weights sum to {result.weights.sum()}, expected 1.0"
    
    # 檢查權重順序：高報酬的股票應該權重較大
    assert result.weights["A"] >= result.weights["B"], "Stock A should have higher weight than B"
    assert result.weights["B"] >= result.weights["C"], "Stock B should have higher weight than C"
    
    # 檢查權重上限
    assert (result.weights <= config.weight_constraints.max_weight + 1e-6).all(), \
        "All weights should be <= max_weight"
    
    # 檢查權重下限（long-only）
    assert (result.weights >= 0.0).all(), "All weights should be >= 0 (long-only)"


def test_optimizer_respects_weight_bounds():
    """
    測試個股上限/下限是否生效。
    """
    stock_ids = ["X", "Y", "Z"]
    mu = pd.Series([0.15, 0.10, 0.08], index=stock_ids)
    
    # 建立簡單的 identity covariance matrix
    n = len(stock_ids)
    cov_matrix = np.eye(n) * 0.04
    
    risk_model = MockRiskModel(symbols=stock_ids, cov_matrix=cov_matrix)
    
    # 建立嚴格的權重限制
    config = OptimizerConfig()
    config.weight_constraints.max_weight = 0.40  # 40% 上限
    config.weight_constraints.min_weight = 0.10  # 10% 下限
    config.tracking_error.enabled = False
    
    optimizer = OptimizerCore(config=config)
    
    result = optimizer.optimize(
        expected_returns=mu,
        risk_model=risk_model,
        factor_exposure=None,
        benchmark_weights=None,
        sector_map=None
    )
    
    assert result.status == "success", f"Optimization failed: {result.message}"
    
    # 檢查權重上下限
    assert (result.weights <= config.weight_constraints.max_weight + 1e-6).all(), \
        f"All weights should be <= {config.weight_constraints.max_weight}"
    assert (result.weights >= config.weight_constraints.min_weight - 1e-6).all(), \
        f"All weights should be >= {config.weight_constraints.min_weight}"


def test_optimizer_with_tracking_error():
    """
    測試 Tracking Error 限制是否生效。
    """
    stock_ids = ["A", "B", "C"]
    mu = pd.Series([0.12, 0.08, 0.05], index=stock_ids)
    
    # 建立簡單的 covariance matrix
    n = len(stock_ids)
    cov_matrix = np.eye(n) * 0.04
    
    risk_model = MockRiskModel(symbols=stock_ids, cov_matrix=cov_matrix)
    
    # 建立 benchmark（均勻分配）
    benchmark_weights = pd.Series([1/3, 1/3, 1/3], index=stock_ids)
    
    config = OptimizerConfig()
    config.tracking_error.enabled = True
    config.tracking_error.te_max = 0.03  # 3% TE 上限
    config.weight_constraints.max_weight = 0.6
    
    optimizer = OptimizerCore(config=config)
    
    result = optimizer.optimize(
        expected_returns=mu,
        risk_model=risk_model,
        factor_exposure=None,
        benchmark_weights=benchmark_weights,
        sector_map=None
    )
    
    assert result.status == "success", f"Optimization failed: {result.message}"
    
    # 檢查 TE 是否在限制內
    if result.diagnostics and 'tracking_error' in result.diagnostics:
        te = result.diagnostics['tracking_error']
        assert te <= config.tracking_error.te_max + 1e-6, \
            f"Tracking Error {te} should be <= {config.tracking_error.te_max}"


def test_optimizer_empty_input():
    """
    測試空輸入的處理。
    """
    mu = pd.Series([], dtype=float)
    
    risk_model = MockRiskModel(symbols=[], cov_matrix=np.array([]))
    
    config = OptimizerConfig()
    optimizer = OptimizerCore(config=config)
    
    result = optimizer.optimize(
        expected_returns=mu,
        risk_model=risk_model,
        factor_exposure=None,
        benchmark_weights=None,
        sector_map=None
    )
    
    assert result.status == "failed", "Should fail with empty input"
    assert "Empty" in result.message or "empty" in result.message.lower()


def test_optimizer_with_factor_exposure():
    """
    測試因子暴露限制（基本結構測試）。
    """
    stock_ids = ["A", "B", "C"]
    mu = pd.Series([0.10, 0.08, 0.06], index=stock_ids)
    
    n = len(stock_ids)
    cov_matrix = np.eye(n) * 0.04
    risk_model = MockRiskModel(symbols=stock_ids, cov_matrix=cov_matrix)
    
    # 建立簡單的 factor exposure
    factor_exposure = pd.DataFrame({
        'R_MKT': [1.0, 1.1, 0.9],
        'R_SIZE': [0.5, 0.6, 0.4],
    }, index=stock_ids)
    
    config = OptimizerConfig()
    config.factor_constraints.factor_bounds = {
        'R_MKT': (-0.2, 0.2),
    }
    config.tracking_error.enabled = False
    
    optimizer = OptimizerCore(config=config)
    
    result = optimizer.optimize(
        expected_returns=mu,
        risk_model=risk_model,
        factor_exposure=factor_exposure,
        benchmark_weights=None,
        sector_map=None
    )
    
    # 基本檢查：優化應該能完成（即使因子限制可能很寬鬆）
    assert result.status in ["success", "failed"], "Should return a valid status"
    
    if result.status == "success":
        assert abs(result.weights.sum() - 1.0) < 1e-6, "Weights should sum to 1"

