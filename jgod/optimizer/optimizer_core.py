"""Optimizer Core

J-GOD Optimizer v1 核心類別。

目標：在滿足
- Tracking Error 限制
- 權重上下限 / long-only
- 因子暴露限制
的前提下，最大化風險調整後報酬（Max Sharpe），
或使用 Mean-Variance 形式的目標函數。

Reference:
- docs/J-GOD_RISK_MODEL_STANDARD_v1.md
- docs/J-GOD_OPTIMIZER_STANDARD_v1.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict

import numpy as np
import pandas as pd

try:
    from scipy.optimize import minimize
except ImportError:
    minimize = None

from jgod.risk.risk_model import MultiFactorRiskModel
from .optimizer_config import OptimizerConfig
from .optimizer_constraints import ConstraintBuilder


@dataclass
class OptimizerResult:
    """
    優化結果封裝：
    - weights: 最終權重（Series）
    - status: 'success' / 'failed'
    - message: 說明文字
    - objective_value: 最後目標函數值（例如 -Sharpe 或 mean-variance）
    - diagnostics: 額外的診斷資訊（例如 TE, SR, factor exposures）
    """

    weights: pd.Series
    status: str
    message: str
    objective_value: float
    diagnostics: Optional[Dict] = None


class OptimizerCore:
    """
    J-GOD Optimizer v1 核心類別。

    目標：在滿足各種限制條件的前提下，最大化風險調整後報酬。

    實作邏輯需參考：
    - docs/J-GOD_RISK_MODEL_STANDARD_v1.md
    - docs/J-GOD_OPTIMIZER_STANDARD_v1.md
    """

    def __init__(self, config: Optional[OptimizerConfig] = None) -> None:
        """Initialize OptimizerCore

        Args:
            config: OptimizerConfig instance. If None, uses default config.
        """
        self.config = config or OptimizerConfig()
        self.constraint_builder = ConstraintBuilder(self.config)
        
        if minimize is None:
            raise ImportError(
                "scipy.optimize.minimize is required for OptimizerCore. "
                "Please install scipy: pip install scipy"
            )

    def optimize(
        self,
        expected_returns: pd.Series,
        risk_model: MultiFactorRiskModel,
        factor_exposure: Optional[pd.DataFrame] = None,
        benchmark_weights: Optional[pd.Series] = None,
        sector_map: Optional[Dict[str, str]] = None,
    ) -> OptimizerResult:
        """
        執行一次投資組合優化。

        Parameters
        ----------
        expected_returns : pd.Series
            預期報酬率向量，index 為 stock_id。
        risk_model : MultiFactorRiskModel
            已 fit 完成的風險模型，可提供 Σ, B 等資訊。
        factor_exposure : Optional[pd.DataFrame]
            股票的因子暴露，index = stock_id, columns = factor_names。
            若為 None，將嘗試從 risk_model 取得。
        benchmark_weights : Optional[pd.Series]
            基準指數權重，用於 TE 限制。
        sector_map : Optional[Dict[str, str]]
            stock_id -> sector_name，用於 sector 中性限制。

        Returns
        -------
        OptimizerResult
            優化結果封裝。
        """
        # 1. 基本檢查與對齊 index
        stock_ids = expected_returns.index.tolist()
        n_stocks = len(stock_ids)
        
        if n_stocks == 0:
            return OptimizerResult(
                weights=pd.Series(dtype=float),
                status='failed',
                message='Empty expected returns',
                objective_value=0.0
            )
        
        # 2. 從 risk_model 取得 Σ (covariance matrix)
        cov_matrix = self._build_covariance_matrix(
            pd.Index(stock_ids),
            risk_model
        )
        
        if cov_matrix is None or cov_matrix.shape[0] != n_stocks:
            return OptimizerResult(
                weights=pd.Series(index=stock_ids, dtype=float),
                status='failed',
                message='Failed to get covariance matrix from risk model',
                objective_value=0.0
            )
        
        # 3. 準備預期報酬向量（對齊到 stock_ids 順序）
        mu = expected_returns.values
        
        # 4. 建立初始權重 guess（均勻分配）
        w0 = np.ones(n_stocks) / n_stocks
        
        # 5. 透過 ConstraintBuilder 構建權重 bounds
        bounds = self.constraint_builder.build_weight_bounds(stock_ids)
        
        # 6. 建立目標函數（Mean-Variance 形式）
        risk_aversion = self.config.risk_objective.risk_aversion
        
        def objective(w: np.ndarray) -> float:
            """目標函數：負的 mean-variance 形式（因為 scipy minimize）"""
            return -self._objective_mean_variance(w, mu, cov_matrix, risk_aversion)
        
        # 7. 建立 constraints
        constraints = []
        
        # 7.1 權重合計 = 1 的限制
        constraints.append({
            'type': 'eq',
            'fun': lambda w: np.sum(w) - 1.0
        })
        
        # 7.2 Tracking Error 限制（如果啟用）
        if self.config.tracking_error.enabled and benchmark_weights is not None:
            te_max = self.config.tracking_error.te_max
            
            # 對齊 benchmark weights
            w_bench = self._align_benchmark_weights(benchmark_weights, stock_ids)
            
            if w_bench is not None:
                te_constraint = self._build_te_constraint(
                    w_bench, cov_matrix, te_max
                )
                constraints.append(te_constraint)
        
        # 7.3 因子暴露限制（如果啟用且有 factor_exposure）
        if factor_exposure is not None and not factor_exposure.empty:
            factor_constraints = self._build_factor_exposure_constraints(
                factor_exposure, stock_ids, risk_model
            )
            constraints.extend(factor_constraints)
        
        # 7.4 Sector 中性限制（如果啟用）
        if sector_map is not None:
            sector_constraints = self._build_sector_constraints(
                stock_ids, sector_map
            )
            if sector_constraints:
                constraints.extend(sector_constraints)
        
        # 8. 呼叫 minimize 求解
        try:
            result = minimize(
                objective,
                w0,
                method='SLSQP',  # Sequential Least Squares Programming
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000, 'ftol': 1e-9}
            )
            
            if result.success:
                # 優化成功
                weights = pd.Series(result.x, index=stock_ids)
                
                # 計算診斷資訊
                diagnostics = self._calculate_diagnostics(
                    weights, mu, cov_matrix, risk_model,
                    benchmark_weights, factor_exposure
                )
                
                return OptimizerResult(
                    weights=weights,
                    status='success',
                    message='Optimization successful',
                    objective_value=result.fun,
                    diagnostics=diagnostics
                )
            else:
                # 優化失敗
                return OptimizerResult(
                    weights=pd.Series(result.x, index=stock_ids) if hasattr(result, 'x') else pd.Series(index=stock_ids, dtype=float),
                    status='failed',
                    message=f'Optimization failed: {result.message}',
                    objective_value=result.fun if hasattr(result, 'fun') else 0.0
                )
                
        except Exception as e:
            return OptimizerResult(
                weights=pd.Series(index=stock_ids, dtype=float),
                status='failed',
                message=f'Optimization error: {str(e)}',
                objective_value=0.0
            )

    # ---- 內部工具方法 ----

    def _build_covariance_matrix(
        self,
        stock_ids: pd.Index,
        risk_model: MultiFactorRiskModel,
    ) -> Optional[np.ndarray]:
        """
        從 risk_model 取得 Σ 並依 stock_ids 排序為 N x N 矩陣。

        Args:
            stock_ids: Index of stock identifiers
            risk_model: MultiFactorRiskModel instance

        Returns:
            Covariance matrix (N x N) or None if failed
        """
        try:
            cov_matrix = risk_model.get_covariance_matrix()
            
            if cov_matrix is None:
                return None
            
            # 取得 risk_model 中的 symbols
            model_symbols = risk_model.get_symbols()
            
            if len(model_symbols) == 0 or len(model_symbols) != len(stock_ids):
                # 如果 symbols 不匹配，嘗試使用對角矩陣作為 fallback
                n = len(stock_ids)
                return np.eye(n) * 1e-4  # 很小的預設值
            
            # 對齊到 stock_ids 順序
            symbol_to_idx = {symbol: i for i, symbol in enumerate(model_symbols)}
            
            aligned_cov = np.zeros((len(stock_ids), len(stock_ids)))
            for i, stock_id in enumerate(stock_ids):
                for j, stock_id2 in enumerate(stock_ids):
                    idx_i = symbol_to_idx.get(stock_id, -1)
                    idx_j = symbol_to_idx.get(stock_id2, -1)
                    
                    if idx_i >= 0 and idx_j >= 0:
                        aligned_cov[i, j] = cov_matrix[idx_i, idx_j]
                    else:
                        # 如果找不到，使用預設值
                        aligned_cov[i, j] = 1e-4 if i == j else 0.0
            
            return aligned_cov
            
        except Exception:
            # Fallback: 返回 identity matrix
            n = len(stock_ids)
            return np.eye(n) * 1e-4

    def _objective_mean_variance(
        self,
        w: np.ndarray,
        mu: np.ndarray,
        cov: np.ndarray,
        risk_aversion: float,
    ) -> float:
        """
        Mean-variance 形式：
        maximize mu^T w - λ w^T Σ w

        注意：此函數回傳正值（因為 scipy minimize 會最小化，所以外部會取負）

        Args:
            w: Weight vector (N x 1)
            mu: Expected returns (N x 1)
            cov: Covariance matrix (N x N)
            risk_aversion: Risk aversion parameter λ

        Returns:
            Objective function value: mu^T w - λ w^T Σ w
        """
        portfolio_return = np.dot(w, mu)
        portfolio_variance = np.dot(w, np.dot(cov, w))
        
        return portfolio_return - risk_aversion * portfolio_variance

    def _build_te_constraint(
        self,
        w_bench: np.ndarray,
        cov: np.ndarray,
        te_max: float,
    ) -> Dict:
        """
        建立 Tracking Error 限制：
        TE(w) = sqrt( (w - w_bench)^T Σ (w - w_bench) ) <= te_max

        在 scipy 中可用非線性 constraint 方式實作：
        g(w) = te_max - TE(w) >= 0

        Args:
            w_bench: Benchmark weight vector (N x 1)
            cov: Covariance matrix (N x N)
            te_max: Maximum tracking error

        Returns:
            Constraint dictionary for scipy.optimize
        """
        def te_constraint(w: np.ndarray) -> float:
            """TE constraint: te_max - TE(w) >= 0"""
            active_weight = w - w_bench
            te_squared = np.dot(active_weight, np.dot(cov, active_weight))
            te = np.sqrt(max(te_squared, 0.0))
            return te_max - te
        
        return {
            'type': 'ineq',
            'fun': te_constraint
        }

    def _align_benchmark_weights(
        self,
        benchmark_weights: pd.Series,
        stock_ids: List[str]
    ) -> Optional[np.ndarray]:
        """
        對齊 benchmark weights 到 stock_ids 順序。

        Args:
            benchmark_weights: Benchmark weight Series
            stock_ids: List of stock IDs to align to

        Returns:
            Aligned benchmark weight array or None if failed
        """
        try:
            aligned = benchmark_weights.reindex(stock_ids, fill_value=0.0)
            return aligned.values
        except Exception:
            return None

    def _build_factor_exposure_constraints(
        self,
        factor_exposure: pd.DataFrame,
        stock_ids: List[str],
        risk_model: MultiFactorRiskModel,
    ) -> List[Dict]:
        """
        建立因子暴露限制。

        Args:
            factor_exposure: DataFrame with factor exposures
            stock_ids: List of stock IDs
            risk_model: MultiFactorRiskModel instance

        Returns:
            List of constraint dictionaries
        """
        constraints = []
        
        # 取得因子暴露限制配置
        factor_bounds = self.constraint_builder.build_factor_exposure_constraints(
            factor_exposure
        )
        
        if not factor_bounds:
            return constraints
        
        # 對齊 factor_exposure 到 stock_ids
        aligned_exposure = factor_exposure.reindex(stock_ids, fill_value=0.0)
        
        # 取得 benchmark factor exposures（如果有 benchmark）
        # 這裡簡化處理：假設 benchmark 因子暴露為 0（可在未來擴充）
        benchmark_exposure = None
        
        for factor_name, (min_delta, max_delta) in factor_bounds.items():
            if factor_name not in aligned_exposure.columns:
                continue
            
            # 取得該因子的暴露向量
            factor_vec = aligned_exposure[factor_name].values
            
            # 建立限制：min_delta <= w^T * factor_exposure <= max_delta
            # 轉換為兩個不等式：w^T * factor_exposure >= min_delta 和 w^T * factor_exposure <= max_delta
            
            # 使用閉包來避免 lambda 變數綁定問題
            if not np.isinf(min_delta):
                factor_vec_min = factor_vec.copy()
                min_val = min_delta
                constraints.append({
                    'type': 'ineq',
                    'fun': lambda w, f=factor_vec_min, mv=min_val: np.dot(w, f) - mv
                })
            
            if not np.isinf(max_delta):
                factor_vec_max = factor_vec.copy()
                max_val = max_delta
                constraints.append({
                    'type': 'ineq',
                    'fun': lambda w, f=factor_vec_max, mv=max_val: mv - np.dot(w, f)
                })
        
        return constraints

    def _build_sector_constraints(
        self,
        stock_ids: List[str],
        sector_map: Dict[str, str],
    ) -> List[Dict]:
        """
        建立 Sector 中性限制。

        Args:
            stock_ids: List of stock IDs
            sector_map: Dictionary mapping stock_id -> sector_name

        Returns:
            List of constraint dictionaries
        """
        constraints = []
        
        sector_constraint_data = self.constraint_builder.build_sector_constraints(
            stock_ids, sector_map
        )
        
        if sector_constraint_data is None:
            return constraints
        
        exposure_matrix = sector_constraint_data['exposure_matrix']
        bounds = sector_constraint_data['bounds']
        sectors = sector_constraint_data['sectors']
        
        # 為每個 sector 建立限制
        for i, sector in enumerate(sectors):
            min_delta, max_delta = bounds[sector]
            
            # Sector exposure: w^T * exposure_matrix[i, :]
            sector_exposure_vec = exposure_matrix[i, :]
            
            # 使用閉包來避免 lambda 變數綁定問題
            if not np.isinf(min_delta):
                sector_vec_min = sector_exposure_vec.copy()
                min_val = min_delta
                constraints.append({
                    'type': 'ineq',
                    'fun': lambda w, vec=sector_vec_min, mv=min_val: np.dot(w, vec) - mv
                })
            
            if not np.isinf(max_delta):
                sector_vec_max = sector_exposure_vec.copy()
                max_val = max_delta
                constraints.append({
                    'type': 'ineq',
                    'fun': lambda w, vec=sector_vec_max, mv=max_val: mv - np.dot(w, vec)
                })
        
        return constraints

    def _calculate_diagnostics(
        self,
        weights: pd.Series,
        mu: np.ndarray,
        cov: np.ndarray,
        risk_model: MultiFactorRiskModel,
        benchmark_weights: Optional[pd.Series],
        factor_exposure: Optional[pd.DataFrame],
    ) -> Dict:
        """
        計算診斷資訊（TE, SR, factor exposures 等）。

        Args:
            weights: Optimized weights
            mu: Expected returns
            cov: Covariance matrix
            risk_model: Risk model instance
            benchmark_weights: Optional benchmark weights
            factor_exposure: Optional factor exposure DataFrame

        Returns:
            Dictionary with diagnostic information
        """
        diagnostics = {}
        w = weights.values
        
        # 總風險
        portfolio_variance = np.dot(w, np.dot(cov, w))
        portfolio_vol = np.sqrt(max(portfolio_variance, 0.0))
        diagnostics['total_volatility'] = float(portfolio_vol)
        
        # 預期報酬
        portfolio_return = np.dot(w, mu)
        diagnostics['expected_return'] = float(portfolio_return)
        
        # Sharpe Ratio（假設無風險利率為 0）
        if portfolio_vol > 1e-10:
            sharpe_ratio = portfolio_return / portfolio_vol
            diagnostics['sharpe_ratio'] = float(sharpe_ratio)
        
        # Tracking Error（如果有 benchmark）
        if benchmark_weights is not None:
            w_bench = self._align_benchmark_weights(benchmark_weights, weights.index.tolist())
            if w_bench is not None:
                active_weight = w - w_bench
                te_squared = np.dot(active_weight, np.dot(cov, active_weight))
                te = np.sqrt(max(te_squared, 0.0))
                diagnostics['tracking_error'] = float(te)
        
        # 最大持股
        diagnostics['max_position'] = float(weights.max())
        diagnostics['min_position'] = float(weights.min())
        
        # 因子暴露（如果有 factor_exposure）
        if factor_exposure is not None:
            aligned_exposure = factor_exposure.reindex(weights.index, fill_value=0.0)
            factor_exposures = {}
            for factor_name in aligned_exposure.columns:
                exposure = np.dot(weights.values, aligned_exposure[factor_name].values)
                factor_exposures[factor_name] = float(exposure)
            diagnostics['factor_exposures'] = factor_exposures
        
        return diagnostics

