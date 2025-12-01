# JGOD Optimizer Spec v1

## 1. OptimizerRequest Schema（輸入）

```python
@dataclass
class OptimizerRequest:
    expected_active_return: np.ndarray  # shape (N,)
    cov_matrix: np.ndarray              # shape (N, N)
    factor_betas: np.ndarray            # shape (N, K)
    sector_map: np.ndarray              # shape (N, J)
    prev_weights: np.ndarray            # shape (N,)
    benchmark_weights: np.ndarray       # shape (N,)
    linear_cost: np.ndarray             # shape (N,)
    quad_cost: np.ndarray               # shape (N,)
    bounds: Tuple[np.ndarray, np.ndarray]  # (lower[N], upper[N])
    params: Dict[str, float]            # λ, TE_max, T_max ...
```

---

## 2. OptimizerResult Schema（輸出）

```python
@dataclass
class OptimizerResult:
    weights: np.ndarray
    turnover: float
    TE: float
    factor_exposures: Dict[str, float]
    sector_exposures: Dict[str, float]
    cost: float
    sharpe_est: float
    diagnostics: dict
```

---

## 3. API

```
class OptimizerCoreV2:
    def solve(self, req: OptimizerRequest) -> OptimizerResult:
        ...
```

---

## 4. Solver 需要具備：

- MV 求解器
- MVCO 求解器
- TE 限制
- Factor constraint
- Sector constraint
- Turnover
- Cost model
- Safety checks

---

