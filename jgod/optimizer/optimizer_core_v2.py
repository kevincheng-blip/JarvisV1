"""Optimizer Core v2

J-GOD Optimizer v2 核心類別。

實作 Mean-Variance (MV) 和 Mean-Variance-Cost (MVCO) 優化模型，
支援多種限制條件：Tracking Error、Factor Exposure、Sector Exposure、Turnover。

Reference:
- docs/JGOD_OPTIMIZER_STANDARD_v1.md
- spec/JGOD_Optimizer_Spec.md
"""

from __future__ import annotations

import numpy as np
from typing import Dict, Optional
import warnings

try:
    import cvxpy as cp
    CVXPY_AVAILABLE = True
except ImportError:
    CVXPY_AVAILABLE = False
    warnings.warn(
        "cvxpy is not installed. OptimizerCoreV2 requires cvxpy. "
        "Please install it: pip install cvxpy"
    )

from .optimizer_types import OptimizerRequest, OptimizerResult


class OptimizerCoreV2:
    """J-GOD Optimizer v2 核心類別
    
    支援 Mean-Variance (MV) 和 Mean-Variance-Cost (MVCO) 優化模型。
    使用 cvxpy 進行二次規劃求解。
    
    Attributes:
        solver: cvxpy solver 名稱，預設為 'OSQP'
        verbose: 是否輸出詳細資訊
    """
    
    def __init__(self, solver: str = "OSQP", verbose: bool = False):
        """初始化 OptimizerCoreV2
        
        Args:
            solver: cvxpy solver 名稱，可選值：'OSQP', 'ECOS', 'SCS', 'GUROBI' 等
            verbose: 是否輸出求解過程的詳細資訊
        """
        if not CVXPY_AVAILABLE:
            raise ImportError(
                "cvxpy is required for OptimizerCoreV2. "
                "Please install it: pip install cvxpy"
            )
        
        self.solver = solver
        self.verbose = verbose
    
    def solve(self, req: OptimizerRequest) -> OptimizerResult:
        """執行投資組合優化
        
        Args:
            req: OptimizerRequest 物件，包含所有輸入資料
        
        Returns:
            OptimizerResult 物件，包含最優權重和診斷資訊
        
        Raises:
            ValueError: 輸入資料格式錯誤
            RuntimeError: 優化求解失敗
        """
        # 驗證輸入
        req.validate()
        
        N = len(req.expected_active_return)
        
        # 定義決策變數
        w = cp.Variable(N)
        
        # === 目標函數 ===
        active_ret = req.expected_active_return
        Sigma = req.cov_matrix
        
        # 風險項：w^T Σ w
        risk_term = cp.quad_form(w, Sigma)
        
        # 成本項
        w_diff = w - req.prev_weights
        
        # 線性成本：sum(γ_i |w_i - w_i^prev|)
        # 注意：cvxpy 的 norm1 是 sum of absolute values
        cost_linear = cp.norm1(w_diff) * np.mean(req.linear_cost) if np.any(req.linear_cost) else 0
        
        # 二次成本：sum(β_i (w_i - w_i^prev)^2)
        cost_quad = cp.quad_form(w_diff, np.diag(req.quad_cost)) if np.any(req.quad_cost) else 0
        
        # 目標函數：最大化 active return - λ * risk - cost
        objective = cp.Maximize(
            active_ret @ w
            - req.params["lambda"] * risk_term
            - cost_linear
            - cost_quad
        )
        
        constraints = []
        
        # === 權重邊界限制 ===
        lower, upper = req.bounds
        constraints += [w >= lower, w <= upper]
        
        # === 換手率限制 ===
        turnover = cp.norm1(w_diff)
        T_max = req.params.get("T_max", 0.20)
        constraints += [turnover <= T_max]
        
        # === 因子暴露限制 ===
        betas = req.factor_betas  # (N, K)
        if betas is not None and betas.size > 0:
            X = betas.T @ w  # (K,)
            
            factor_limits = req.params.get("factor_limits", {})
            factor_index = req.params.get("factor_index", {})
            
            for k, limit in factor_limits.items():
                if k in factor_index:
                    idx = factor_index[k]
                    if isinstance(limit, (list, tuple)) and len(limit) == 2:
                        # 雙邊限制 (min, max)
                        constraints += [X[idx] >= limit[0], X[idx] <= limit[1]]
                    else:
                        # 單邊限制（絕對值）
                        constraints += [cp.abs(X[idx]) <= limit]
        
        # === 行業暴露限制 ===
        sectors = req.sector_map  # (N, J)
        if sectors is not None and sectors.size > 0:
            S = sectors.T @ w  # (J,)
            
            sector_limits = req.params.get("sector_limits", {})
            
            for j, limits in sector_limits.items():
                if isinstance(limits, (list, tuple)) and len(limits) == 2:
                    min_j, max_j = limits
                    if j < S.shape[0]:
                        constraints += [S[j] >= min_j, S[j] <= max_j]
        
        # === 槓桿和淨暴露限制 ===
        # 多頭總權重限制
        w_long = cp.maximum(w, 0)
        constraints += [cp.sum(w_long) <= req.params.get("long_leverage", 1.30)]
        
        # 空頭總權重限制
        w_short = cp.maximum(-w, 0)
        constraints += [cp.sum(w_short) <= req.params.get("short_leverage", 0.30)]
        
        # 淨暴露限制
        net_exposure_lower = req.params.get("net_exposure_lower", 0.90)
        net_exposure_upper = req.params.get("net_exposure_upper", 1.10)
        constraints += [
            cp.sum(w) >= net_exposure_lower,
            cp.sum(w) <= net_exposure_upper
        ]
        
        # === Tracking Error 限制 ===
        TE_max = req.params.get("TE_max", 0.04)
        TE_matrix = req.params.get("TE_matrix", None)
        
        if TE_matrix is not None:
            w_active = w - req.benchmark_weights
            TE_square = cp.quad_form(w_active, TE_matrix)
            constraints += [TE_square <= TE_max ** 2]
        
        # === 建立並求解問題 ===
        prob = cp.Problem(objective, constraints)
        
        try:
            prob.solve(solver=self.solver, verbose=self.verbose)
        except Exception as e:
            raise RuntimeError(f"Optimization solver failed: {e}") from e
        
        # 檢查求解狀態
        if prob.status not in ["optimal", "optimal_inaccurate"]:
            raise RuntimeError(
                f"Optimization did not converge. Status: {prob.status}. "
                f"Problem may be infeasible or unbounded."
            )
        
        # 取得最優權重
        weights = w.value
        
        if weights is None:
            raise RuntimeError("Solver did not return optimal weights")
        
        # 計算後處理指標
        turnover_val = float(np.sum(np.abs(weights - req.prev_weights)))
        
        # 計算 Tracking Error
        TE_val = 0.0
        if TE_matrix is not None:
            w_active = weights - req.benchmark_weights
            TE_val = float(np.sqrt(w_active.T @ TE_matrix @ w_active))
        
        # 計算因子暴露
        factor_exposures = {}
        if betas is not None and betas.size > 0:
            X_val = betas.T @ weights
            factor_names = req.params.get("factor_names", [f"factor_{i}" for i in range(len(X_val))])
            for i, name in enumerate(factor_names[:len(X_val)]):
                factor_exposures[name] = float(X_val[i])
        
        # 計算行業暴露
        sector_exposures = {}
        if sectors is not None and sectors.size > 0:
            S_val = sectors.T @ weights
            sector_names = req.params.get("sector_names", [f"sector_{i}" for i in range(len(S_val))])
            for i, name in enumerate(sector_names[:len(S_val)]):
                sector_exposures[name] = float(S_val[i])
        
        # 計算成本
        cost_val = float(cost_linear.value if cost_linear != 0 else 0) + \
                   float(cost_quad.value if cost_quad != 0 else 0)
        
        # 估計 Sharpe Ratio（簡化版）
        expected_return = float(active_ret @ weights)
        portfolio_risk = float(np.sqrt(weights.T @ Sigma @ weights))
        sharpe_est = expected_return / portfolio_risk if portfolio_risk > 0 else 0.0
        
        # 建立結果物件
        result = OptimizerResult(
            weights=weights,
            turnover=turnover_val,
            TE=TE_val,
            factor_exposures=factor_exposures,
            sector_exposures=sector_exposures,
            cost=cost_val,
            sharpe_est=sharpe_est,
            diagnostics={
                "status": prob.status,
                "objective_value": float(prob.value) if prob.value is not None else None,
                "solver": self.solver,
            }
        )
        
        return result

