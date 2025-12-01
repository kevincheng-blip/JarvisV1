# J-GOD Optimizer Standard v1

### Step 5 — MV + MVCO 多限制條件組合優化器標準規格

---

# 1. Overview

J-GOD Optimizer 是系統中負責將：

- Step 2 的 Alpha 訊號
- Step 4 的 Risk Model（八大風險因子 Σ）
- Step 3、4、5 的各種限制（TE、暴露、行業、槓桿、換手率）

整合為最終投資組合權重 **w\*** 的核心模組。

優化器採用 **Quadratic Programming（QP）**，包含：

- **Mean-Variance（MV）模型**
- **Mean-Variance-Cost（MVCO）模型**
- **Active Return 模型（相對基準）**
- **Tracking Error 限制**
- **Factor Exposure 限制**
- **Sector Exposure 限制**
- **Turnover 限制 + 成本模型**

---

# 2. Objective Function

## 2.1 Mean-Variance 版本（無成本）

\[
\max_w \; w^\top R_{\text{active}} - 
\lambda \cdot w^\top \Sigma w
\]

- \(R_{\text{active}}\): 來自 Alpha Engine 的 active return 預測值  
- \(\Sigma\): Risk Model（八大風險因子）

---

## 2.2 Mean-Variance-Cost（MVCO）版本

\[
\max_w \; 
w^\top R_{\text{active}}
- \lambda \cdot w^\top \Sigma w
- C(w)
\]

其中交易成本 \(C(w)\) 包含：

### (a) 線性成本（linear）

\[
C_{\text{lin}} = \sum_i \gamma_i |w_i - w_i^{\text{prev}}|
\]

### (b) 二次成本（quadratic）

\[
C_{\text{quad}} = \sum_i \beta_i (w_i - w_i^{\text{prev}})^2
\]

**目的：懲罰高換手率（Turnover）。**

---

# 3. Constraints（限制條件）

## 3.1 Leverage / Exposure Constraints

| 限制項目 | 規格 |
|---------|------|
| 多頭總權重 | \(\sum_{i:w_i>0} w_i ≤ 1.30\) |
| 空頭總權重 | \(\sum_{i:w_i<0} |w_i| ≤ 0.30\) |
| 淨暴露 | \(0.90 ≤ \sum_i w_i ≤ 1.10\) |

---

## 3.2 Concentration / Liquidity

| 限制項目 | 規格 |
|---------|------|
| 個股最大權重 | \(w_i ≤ 0.10\) |
| 個股最小持有 | \(w_i = 0\) or \(w_i ≥ 0.005\) |
| 流動性門檻 | 股票需在「Top 500 liquidity」內 |

---

## 3.3 Factor Exposure Limits  

因子暴露計算：

\[
X_k = \sum_i w_i B_{i,k}
\]

| 因子 | 限制 |
|------|-------|
| MKT | \(|X_{MKT}| ≤ 0.05\) |
| SIZE | \(|X_{SIZE}| ≤ 0.03\) |
| VAL | \(|X_{VAL}| ≤ 0.03\) |
| MOM | \(|X_{MOM}| ≤ 0.03\) |
| FLOW | optional \(|X_{FLOW}| ≤ 0.10\) |

---

## 3.4 Tracking Error Constraint

\[
TE^2(w) = (w - w_{\text{BM}})^\top 
\Sigma_{\text{TE}} 
(w - w_{\text{BM}})
≤ TE_{\max}^2
\]

預設：  
\(\text{TE}_{\max} = 4\%\)（年化）

---

## 3.5 Turnover Constraint

\[
\text{Turnover} = \sum_i |w_i - w_i^{\text{prev}}| ≤ T_{\max}
\]

預設：每日 \(T_{\max} = 0.20\)

---

## 3.6 Sector Constraints

\[
S_j = \sum_{i \in \text{Sector j}} w_i
\]

| 限制 | 內容 |
|------|------|
| 單一產業集中度 | \(S_j ≤ 0.20\) |
| 產業相對中性 | \(|S_j - S_j^{BM}| ≤ 0.05\) |

---

# 4. Required Inputs

（詳細在 Spec 中定義）

- active_return (N,)
- sigma (N,N)
- factor_betas (N,K)
- sector_map (N,J)
- prev_weights (N,)
- benchmark_weights (N,)
- linear_cost (N,)
- quad_cost (N,)
- bounds (min,max)
- TE matrix
- parameters (λ, TE_max, T_max, etc.)

---

# 5. Outputs

- w\*（最佳權重向量）
- diagnostics（Sharpe、TE、Exposure、Turnover）
- cost breakdown

---

# 6. Implementation Notes

- 使用 cvxpy or gurobi solver  
- 所有限制使用向量化  
- 必須防止 infeasible  
- 使用 slack mechanism（可選）

---

