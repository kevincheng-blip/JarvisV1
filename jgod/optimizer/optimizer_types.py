"""Optimizer Types v2

定義 Optimizer v2 使用的資料結構類型。

Reference:
- docs/JGOD_OPTIMIZER_STANDARD_v1.md
- spec/JGOD_Optimizer_Spec.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np


@dataclass
class OptimizerRequest:
    """Optimizer 輸入請求資料結構
    
    Attributes:
        expected_active_return: 預期主動報酬向量，shape (N,)
        cov_matrix: 協方差矩陣，shape (N, N)
        factor_betas: 因子暴露矩陣，shape (N, K)，K 為因子數
        sector_map: 行業對應矩陣，shape (N, J)，J 為行業數
        prev_weights: 前一期的權重向量，shape (N,)
        benchmark_weights: 基準權重向量，shape (N,)
        linear_cost: 線性交易成本係數，shape (N,)
        quad_cost: 二次交易成本係數，shape (N,)
        bounds: 權重邊界，tuple (lower[N], upper[N])
        params: 優化參數字典，包含 λ, TE_max, T_max, factor_limits, sector_limits 等
    """
    
    expected_active_return: np.ndarray
    cov_matrix: np.ndarray
    factor_betas: np.ndarray
    sector_map: np.ndarray
    prev_weights: np.ndarray
    benchmark_weights: np.ndarray
    linear_cost: np.ndarray
    quad_cost: np.ndarray
    bounds: Tuple[np.ndarray, np.ndarray]
    params: Dict[str, any]
    
    def validate(self) -> None:
        """驗證輸入資料的格式和合理性"""
        N = len(self.expected_active_return)
        
        # 檢查維度一致性
        assert self.cov_matrix.shape == (N, N), f"cov_matrix shape mismatch: {self.cov_matrix.shape} != ({N}, {N})"
        assert len(self.prev_weights) == N, f"prev_weights length mismatch: {len(self.prev_weights)} != {N}"
        assert len(self.benchmark_weights) == N, f"benchmark_weights length mismatch: {len(self.benchmark_weights)} != {N}"
        assert len(self.linear_cost) == N, f"linear_cost length mismatch: {len(self.linear_cost)} != {N}"
        assert len(self.quad_cost) == N, f"quad_cost length mismatch: {len(self.quad_cost)} != {N}"
        
        lower, upper = self.bounds
        assert len(lower) == N, f"lower bounds length mismatch: {len(lower)} != {N}"
        assert len(upper) == N, f"upper bounds length mismatch: {len(upper)} != {N}"
        
        # 檢查 factor_betas
        if self.factor_betas.shape[0] != N:
            raise ValueError(f"factor_betas rows mismatch: {self.factor_betas.shape[0]} != {N}")
        
        # 檢查 sector_map
        if self.sector_map.shape[0] != N:
            raise ValueError(f"sector_map rows mismatch: {self.sector_map.shape[0]} != {N}")
        
        # 檢查必要參數
        required_params = ["lambda", "TE_max", "T_max"]
        for param in required_params:
            if param not in self.params:
                raise ValueError(f"Missing required parameter: {param}")


@dataclass
class OptimizerResult:
    """Optimizer 輸出結果資料結構
    
    Attributes:
        weights: 最優權重向量，shape (N,)
        turnover: 換手率（Turnover）
        TE: 追蹤誤差（Tracking Error）
        factor_exposures: 因子暴露字典，key 為因子名稱，value 為暴露值
        sector_exposures: 行業暴露字典，key 為行業名稱，value 為暴露值
        cost: 總交易成本
        sharpe_est: 估計的 Sharpe Ratio
        diagnostics: 診斷資訊字典，包含優化狀態、目標函數值等
    """
    
    weights: np.ndarray
    turnover: float
    TE: float
    factor_exposures: Dict[str, float]
    sector_exposures: Dict[str, float]
    cost: float
    sharpe_est: float
    diagnostics: Dict[str, any]
    
    def to_dict(self) -> Dict[str, any]:
        """轉換為字典格式"""
        return {
            "weights": self.weights.tolist() if isinstance(self.weights, np.ndarray) else self.weights,
            "turnover": self.turnover,
            "TE": self.TE,
            "factor_exposures": self.factor_exposures,
            "sector_exposures": self.sector_exposures,
            "cost": self.cost,
            "sharpe_est": self.sharpe_est,
            "diagnostics": self.diagnostics,
        }

