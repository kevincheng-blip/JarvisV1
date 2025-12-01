# J-GOD 投資組合優化器 v1.0 標準規範

> **重要**：這是 J-GOD Step 5：投資組合優化器與限制條件的基準標準，所有優化器相關模組必須遵循此規範。

---

## 📋 文件簡介

本文件定義 J-GOD 系統建構 **Step 5：投資組合優化器與限制條件**（Optimizer & Constraints）的標準規格。

### 相關文件對應關係

本標準與以下文件具有明確的依賴關係：

- **J-GOD_RISK_MODEL_STANDARD_v1.md**（Step 4）
  - Optimizer 必須使用 Risk Model v1 提供的協方差矩陣 Σ、因子暴露矩陣 B、特有風險矩陣 D
  - 所有風險相關計算必須透過 Risk Model 標準介面取得

- **Alpha Engine**（Step 3）
  - Optimizer 使用 Alpha Engine 輸出的預期報酬向量 μ 作為優化目標的輸入

- **Path A / Validation Lab**
  - Optimizer 在 Walk-Forward 分析中被反覆呼叫，用於驗證優化策略的有效性
  - 透過 Path A 回測結果驗證 Optimizer 的限制條件設定是否合理

---

## 🎯 核心原則

**J-GOD Optimizer v1 的設計原則是：**

> **最大化 Sharpe Ratio（絕對報酬）＋ 在可接受的 Tracking Error 範圍內運作（控制相對基準風險）**

- **Sharpe Ratio**：作為目標函數（Objective Function）
- **Tracking Error**：作為硬限制條件（Hard Constraint）

Optimizer v1 採用「融合架構」：
- 使用 SR 作為主要優化目標
- 使用 TE 上限來約束，避免偏離基準過多

---

## 📊 Sharpe Ratio 與 Tracking Error 的關係與角色

### 指標對比表

| 指標 | 定義 | 核心目標 | 關注的風險類型 | 在 J-GOD 中的角色 |
|------|------|---------|--------------|-----------------|
| **Sharpe Ratio (SR)** | 超額報酬 / 總波動度 | 最大化風險調整後絕對報酬 | 總風險 σ_p | **優化目標（Objective）** |
| **Tracking Error (TE)** | 組合 vs 基準 報酬差異的波動度 | 最小化相對基準的偏離 | 相對風險 vs Benchmark | **限制條件（Constraint）** |

### 數學定義

**Sharpe Ratio：**

\[
SR(w) = \frac{w^T \mu - r_f}{\sqrt{w^T \Sigma w}}
\]

**Tracking Error：**

\[
TE(w) = \sqrt{(w - w_b)^T \Sigma (w - w_b)}
\]

其中：
- \(w\)：投資組合權重向量
- \(w_b\)：Benchmark 權重向量
- \(\mu\)：預期報酬向量
- \(\Sigma\)：協方差矩陣
- \(r_f\)：無風險利率

### 核心結論

在 J-GOD Optimizer v1 中：

1. **Sharpe Ratio = 優化目標（Objective）**
   - 主要目標是最大化風險調整後的絕對報酬
   - 透過最大化 SR，系統會自動平衡報酬與風險

2. **Tracking Error = 限制條件（Constraint）**
   - 不追求 TE 最小化（這會導致過度追蹤基準）
   - 設定 TE 上限，避免組合偏離基準失控
   - 允許在 TE 上限內自由優化，以追求 Alpha

3. **兩者相輔相成但存在目標衝突**
   - 高 SR 可能導致高 TE（主動管理風險）
   - 低 TE 可能限制 SR 的提升空間
   - J-GOD 採用「融合架構」：在 TE 約束下最大化 SR

---

## 🎯 目標函數定義（Objective Function）

### 3.1 變數與輸入定義

#### 核心變數

| 變數符號 | 定義 | 維度 | 來源模組 |
|---------|------|------|---------|
| \(w\) | 投資組合權重向量 | (N × 1) | Optimizer 輸出 |
| \(w_b\) | Benchmark 權重向量 | (N × 1) | 配置參數（如台灣 50、J-GOD 51 檔宇宙） |
| \(w_a = w - w_b\) | Active Weight（超額權重） | (N × 1) | 計算得出 |
| \(\mu\) | 預期報酬向量 | (N × 1) | Alpha Engine（composite_alpha 經適當 scaling） |
| \(\Sigma\) | 協方差矩陣 | (N × N) | Risk Model（Σ = B F Bᵀ + D） |
| \(r_f\) | 無風險利率 | Scalar | 配置參數（可設為 0 或實質利率） |
| \(\lambda\) | 風險厭惡係數 | Scalar | Optimizer 可調參數 |

#### 輸入來源說明

- **μ（預期報酬）**：
  - 由 Alpha Engine 的 `composite_alpha` 經過適當轉換（例如 z-score 標準化後轉為預期年化報酬）
  - 轉換方法：\(\mu_i = \text{scaling_factor} \times \text{composite_alpha}_i\)
  - scaling_factor 可為配置參數（例如：0.15 表示每單位 Alpha 對應 15% 年化預期報酬）

- **Σ（協方差矩陣）**：
  - 必須透過 Risk Model 的 `get_covariance_matrix()` 方法取得
  - 不得自行計算或使用其他來源的協方差矩陣

---

### 3.2 Sharpe Ratio 標準形式

標準 Sharpe Ratio 定義：

\[
SR(w) = \frac{w^T \mu - r_f}{\sqrt{w^T \Sigma w}}
\]

**說明**：
- 分子：預期超額報酬（預期報酬減去無風險利率）
- 分母：投資組合總風險（標準差）

---

### 3.3 J-GOD Optimizer v1 使用的實務目標函數

在實務的二次規劃（QP）優化器中，採用 **等價的 mean-variance 形式**：

\[
\max_w \quad (w^T \mu - \lambda \cdot w^T \Sigma w)
\]

**這是 J-GOD Optimizer v1 的標準目標函數。**

#### 關鍵說明

1. **等價性**：
   - 在滿足相同約束條件下，最大化 SR 與最大化 \(w^T \mu - \lambda \cdot w^T \Sigma w\) 等價
   - \(\lambda\) 對應 SR 優化中的風險厭惡程度

2. **λ 參數**：
   - \(\lambda\) 是系統配置參數，可針對不同策略調整：
     - 保守模式：λ 較大（例如 2.0-3.0），強調風險控制
     - 激進模式：λ 較小（例如 0.5-1.0），強調報酬追求
   - **不得寫死在程式碼中，必須透過配置檔或參數傳入**

3. **實作規範**：
   - 所有 Optimizer 模組必須以此形式作為目標函數
   - 必須支援 λ 作為可調參數

---

## 📉 Tracking Error 定義與限制條件（核心約束）

### 4.1 TE 定義

使用基準權重與協方差矩陣定義 Tracking Error：

\[
TE(w) = \sqrt{(w - w_b)^T \Sigma (w - w_b)}
\]

#### 經濟意義

- TE 衡量的是「組合淨值 vs 基準淨值的偏離波動度」
- TE = 0 表示完全追蹤基準
- TE > 0 表示主動管理產生的偏離風險

#### J-GOD 的定位

對於 J-GOD 這種主打 Alpha 的系統：
- **不追求 TE 最小化**（這會導致過度追蹤基準，喪失 Alpha）
- **設定 TE 上限**，避免組合偏離基準失控
- 在 TE 上限內，允許 Optimizer 自由優化以追求最大 SR

---

### 4.2 J-GOD 標準 TE 限制

#### 限制形式

\[
TE(w) \leq TE_{\max}
\]

其中 \(TE_{\max}\) 為系統配置參數。

#### 配置參數說明

- **不得寫死在程式碼中**
- 必須透過配置檔或 Optimizer 參數傳入
- 建議範例值（僅供參考，實際值需依策略調整）：

| 策略模式 | 年化 TE_max 建議值 | 說明 |
|---------|-----------------|------|
| 保守模式 | 約 3% | 低偏離、穩定追蹤基準 |
| 標準 Alpha 模式 | 約 5% | 平衡 Alpha 與追蹤 |
| 雙核心 Alpha 模式 | 約 5%-8% | 高 Alpha、允許較大偏離 |

#### 實作要求

Optimizer 實作時必須支援：

```python
te_max: float | None
```

- 若 `te_max` 為 `None`，則不啟用 TE 限制
- 若 `te_max` 為正數，則強制執行 TE 上限約束

---

## 🔒 四大類限制條件族群（Constraints Families）

### 5.1 A 類：總風險限制 (Total Risk Constraints)

#### A.1 Tracking Error 上限（核心限制）

已在 [4.2 節](#42-j-god-標準-te-限制) 定義，為 Optimizer v1 的**核心總風險限制**。

#### A.2 VaR / CVaR 限制（預留）

**定義**：

- **VaR (Value at Risk)**：在給定信心水準下，投資組合的最大可能損失
- **CVaR (Conditional VaR)**：超過 VaR 門檻的平均損失（Tail Risk）

**限制形式**：

\[
\text{VaR}_\alpha(w) \leq \text{VaR}_{\max}
\]

\[
\text{CVaR}_\alpha(w) \leq \text{CVaR}_{\max}
\]

**v1 實作狀態**：

- **v1 實作時，TE 上限是唯一必須實作的總風險限制**
- VaR / CVaR 可以先做為未來版本的 hook，在文件中描述規範
- 程式碼中可預留介面，但不強制實作

---

### 5.2 B 類：因子暴露限制 (Exposure Constraints)

#### 目標

保持投資組合在八大風險因子上的暴露不會嚴重偏離基準，避免風格漂移。

#### B.1 因子暴露定義

| 變數符號 | 定義 | 計算方式 |
|---------|------|---------|
| \(E_{\text{fund},k}\) | 投資組合在第 k 個風險因子的暴露 | 透過 B 矩陣計算：\(E_{\text{fund},k} = w^T B_{:,k}\) |
| \(E_{\text{bench},k}\) | Benchmark 在第 k 個風險因子的暴露 | \(E_{\text{bench},k} = w_b^T B_{:,k}\) |
| \(L_k\) | 第 k 個因子的容忍度上限 | 配置參數 |

其中 \(B_{:,k}\) 為 Risk Model 的因子暴露矩陣 B 的第 k 列（對應第 k 個風險因子）。

#### B.2 標準限制形式

\[
|E_{\text{fund},k} - E_{\text{bench},k}| \leq L_k, \quad \forall k \in \{1, 2, \ldots, K\}
\]

其中 \(K = 8\)（對應八大風險因子）。

#### B.3 因子容忍度設定說明

\(L_k\) 為每個因子的容忍度，可依策略性質設定。**不得寫死在程式碼中，必須透過配置檔或參數傳入。**

建議範例值（僅供參考）：

| 風險因子 | 因子代碼 | 建議 \(L_k\) 範例 | 說明 |
|---------|---------|----------------|------|
| R-MKT | `R_MKT` | 0.05 - 0.10 | 允許低 Beta 結構，避免過度市場暴露 |
| R-SIZE | `R_SIZE` | 0.10 - 0.15 | 可允許中小型股配置 |
| R-VAL | `R_VAL` | 0.15 - 0.20 | 價值 Alpha 因子，允許較大偏離 |
| R-MOM | `R_MOM` | 0.10 - 0.15 | 動量因子暴露控制 |
| R-LIQ | `R_LIQ` | 0.10 - 0.15 | 流動性風險控制 |
| R-VOL | `R_VOL` | 0.10 - 0.15 | 波動率風險控制 |
| R-FX/IR | `R_FX_IR` | 0.05 - 0.10 | 宏觀風險，嚴格控制 |
| **R-FLOW** | **`R_FLOW`** | **0.20 - 0.30** | **J-GOD 核心 Alpha 對應，允許較大正暴露偏離** |

**特別說明**：
- R-FLOW 為 J-GOD 專屬因子，是核心 Alpha 來源
- 可允許較大的正暴露偏離（例如 0.20-0.30），以追求 Flow Alpha

#### B.4 產業 / 板塊中性限制（Sector Neutrality）

**定義**：

\[
|w_{\text{sector},s} - w_{\text{sector},s}^{(\text{bench})}| \leq S_s, \quad \forall s \in \{\text{sectors}\}
\]

其中：
- \(w_{\text{sector},s}\)：投資組合在產業 s 的權重合計
- \(w_{\text{sector},s}^{(\text{bench})}\)：Benchmark 在產業 s 的權重合計
- \(S_s\)：產業 s 的容忍度上限

**產業分類建議**：

可粗分為：
- 電子（含半導體、光電、電子零組件等）
- 金融（銀行、保險、證券）
- 傳產（鋼鐵、塑化、紡織等）
- 航運
- 其他

**v1 實作狀態**：

- 此限制可在 v1 中視實作進度逐步加入
- 不強制在 v1.0 版本實作，但需在文件中保留規範定義

---

### 5.3 C 類：流動性與集中度限制 (Liquidity & Concentration)

#### C.1 個股權重上限

**標準限制形式**：

\[
0 \leq w_i \leq w_{\max}, \quad \forall i \in \{1, 2, \ldots, N\}
\]

**配置參數說明**：

- \(w_{\max}\) 為個股最大權重上限
- **不得寫死在程式碼中，必須透過配置檔或參數傳入**
- **v1 建議範例值**：\(w_{\max} = 0.05\) 至 \(0.06\)（單檔最多 5%-6%）
  - 此為建議範例值，實際值需依策略與流動性需求調整

#### C.2 換手率 / 交易成本限制 (Turnover Constraint)

**定義**：

\[
\text{Turnover} = \frac{1}{2} \sum_i |w_i^{(\text{new})} - w_i^{(\text{old})}|
\]

其中：
- \(w_i^{(\text{new})}\)：新一期的權重
- \(w_i^{(\text{old})}\)：上一期的權重

**限制形式**：

\[
\text{Turnover} \leq \text{Turnover}_{\max}
\]

**說明**：

- Turnover 衡量組合再平衡的調整幅度
- 較低的 Turnover 可降低交易成本與市場衝擊
- \(\text{Turnover}_{\max}\) 可作為 Path A / Backtest 的控制參數（例如每次再平衡 ≤ 20%）

**v1 實作狀態**：

- v1 可以先在 Backtest / Path A 中實作檢查
- Optimizer 也可以在未來版本整合 Turnover 限制作為優化約束
- 文件中保留規範，但不強制 v1.0 版本實作

---

### 5.4 D 類：槓桿與權重合計限制 (Leverage & Net Exposure)

#### D.1 基本版：Long-only 結構

**標準限制**：

\[
\sum_i w_i = 1, \quad w_i \geq 0, \quad \forall i
\]

**說明**：

**J-GOD Optimizer v1 的標準模式為「Long-only + Full Invested」。**

- **Long-only**：不允許放空（所有權重非負）
- **Full Invested**：權重合計為 1（100% 投資，無現金持有）

#### D.2 進階版：Long/Short 模式（預留）

**多頭總權重限制**：

\[
\sum_i w_i^+ \leq L_{\text{long},\max}
\]

**空頭總權重限制**：

\[
\sum_i |w_i^-| \leq L_{\text{short},\max}
\]

**淨槓桿控制**：

\[
\sum_i w_i^+ - \sum_i |w_i^-| \approx 100\% - 110\%
\]

**說明**：

- 這是未來版本的設計方向
- v1 可以先不實作 Long/Short 模式
- 文件中保留規範定義，供未來擴充參考

---

## 🔗 與 Step 4 Risk Model 的對齊關係

### 6.1 核心結構重申

Optimizer 必須使用 Risk Model v1 提供的標準風險結構：

\[
\Sigma = B F B^T + D
\]

其中：
- \(\Sigma\)：總協方差矩陣（N × N）
- \(B\)：因子暴露矩陣（N × K，K = 8）
- \(F\)：因子協方差矩陣（K × K）
- \(D\)：特有風險對角矩陣（N × N）

### 6.2 介面依賴與要求

Optimizer 對 Risk Model 的依賴：

#### 必須使用的 Risk Model 介面

1. **`get_covariance_matrix()`**
   - 取得總協方差矩陣 Σ
   - 用於計算總風險、Tracking Error

2. **`get_beta_matrix()` 或 `FactorExposure` 結構**
   - 取得因子暴露矩陣 B
   - 用於計算因子暴露限制（B.2 節）

3. **`get_factor_covariance()`**
   - 取得因子協方差矩陣 F
   - 用於風險分解與診斷

4. **`get_specific_risk(symbol)`**
   - 取得個股特有風險
   - 用於風險分解與診斷

#### 八大風險因子標準名稱

所有 Optimizer / Backtest / Portfolio 模組，必須使用與以下文件完全一致的風險因子名稱：

- **J-GOD_RISK_MODEL_STANDARD_v1.md**
- **`jgod/risk/risk_factors.py`**

標準因子名稱列表：

```python
STANDARD_FACTOR_NAMES = [
    'R_MKT',    # 市場風險
    'R_SIZE',   # 規模風險
    'R_VAL',    # 價值風險
    'R_MOM',    # 動量風險
    'R_LIQ',    # 流動性風險
    'R_VOL',    # 波動率風險
    'R_FX_IR',  # 匯率/利率風險
    'R_FLOW'    # 生態資金流風險（J-GOD 專屬）
]
```

### 6.3 強制規範

> **任何 Optimizer / Backtest / Portfolio 模組，不得自行定義與上述八大風險因子衝突的名稱與計算方式。所有風險相關運算，必須透過 Risk Model v1 標準介面取得。**

**違規範例（禁止）**：
- ❌ 在 Optimizer 中自行計算協方差矩陣
- ❌ 自行定義風險因子名稱（如 "market_risk" 而非 "R_MKT"）
- ❌ 繞過 Risk Model 直接使用原始資料計算風險

**正確做法**：
- ✅ 透過 `risk_model.get_covariance_matrix()` 取得 Σ
- ✅ 使用標準因子名稱進行因子暴露計算
- ✅ 所有風險計算統一透過 Risk Model 介面

---

## 🏗️ Optimizer 在 J-GOD 模組體系中的角色

### 7.1 輸入與輸出

#### 輸入（Inputs）

| 輸入項目 | 來源模組 | 說明 |
|---------|---------|------|
| **μ（預期報酬向量）** | Alpha Engine | `composite_alpha` 經適當 scaling 轉換 |
| **Σ（協方差矩陣）** | Risk Model | 透過 `get_covariance_matrix()` 取得 |
| **B（因子暴露矩陣）** | Risk Model | 透過 `get_beta_matrix()` 取得 |
| **w_b（Benchmark 權重）** | 配置參數 | 例如台灣 50、J-GOD 51 檔宇宙 |
| **限制條件參數** | 配置參數 | 見下表 |

#### 限制條件參數列表

| 參數名稱 | 類型 | 說明 |
|---------|------|------|
| `te_max` | `float \| None` | Tracking Error 上限 |
| `w_max` | `float` | 個股權重上限（例如 0.06） |
| `lambda_risk_aversion` | `float` | 風險厭惡係數 λ |
| `factor_exposure_limits` | `Dict[str, float]` | 各因子暴露上限 \(L_k\) |
| `sector_neutrality_config` | `Dict[str, float]` | 產業中性配置（v1 可選） |
| `turnover_max` | `float \| None` | 換手率上限（v1 可選） |

#### 輸出（Outputs）

| 輸出項目 | 格式 | 說明 |
|---------|------|------|
| **w*（最優權重）** | `np.ndarray` (N × 1) | 優化後的投資組合權重向量 |
| **風險診斷** | `Dict` | 包含以下項目： |

**風險診斷項目**：

- `total_volatility`：總風險 \(\sigma_p = \sqrt{w^T \Sigma w}\)
- `tracking_error`：追蹤誤差 \(TE(w)\)
- `factor_exposures`：各因子暴露差異 \(\{E_{\text{fund},k} - E_{\text{bench},k}\}\)
- `max_position`：最大持股權重
- `turnover`：換手率（若有上一期權重）
- `sharpe_ratio`：預期 Sharpe Ratio

---

### 7.2 Optimizer v1 的使用場景

#### 7.2.1 Backtest Engine

- **每個 rebalance 日期呼叫 Optimizer**
- 產生當期最優權重 w*
- 計算回測績效（報酬、風險、TE、SR 等）

**流程**：
```
Backtest Loop:
  For each rebalance_date:
    1. Alpha Engine → μ
    2. Risk Model → Σ, B
    3. Optimizer(μ, Σ, B, constraints) → w*
    4. Calculate returns, risk, TE, SR
    5. Update portfolio
```

#### 7.2.2 Path A / Validation Lab

- **在 Walk-Forward 分段訓練 / 測試中反覆呼叫 Optimizer**
- 驗證不同限制條件設定的有效性
- 測試不同 λ、TE_max 參數組合的表現

**流程**：
```
Walk-Forward Loop:
  For each train/test split:
    1. Train Alpha Model on training period
    2. For each test_date:
       - Optimizer(μ, Σ, B, constraints) → w*
       - Calculate out-of-sample performance
    3. Aggregate results, select best parameters
```

#### 7.2.3 Portfolio Risk

- **對 Optimizer 產出的組合做風險分解**
- 計算因子風險拆解、特有風險貢獻
- 診斷組合風險結構是否合理

**流程**：
```
Portfolio Risk Analysis:
  1. Optimizer → w*
  2. Risk Model.decompose_portfolio_risk(w*)
  3. Output: factor_risk, specific_risk, risk_attribution
```

#### 7.2.4 Error Learning Engine

- **當決策出現大虧損時，分析限制條件設定**
- 檢查是否因限制設置不當導致損失（例如 TE 過鬆、w_max 過大）
- 提供限制條件調整建議

**流程**：
```
Error Analysis:
  1. Detect large loss event
  2. Retrieve historical w* and constraints
  3. Analyze:
     - Was TE constraint too loose?
     - Was w_max too large?
     - Were factor exposure limits appropriate?
  4. Suggest constraint adjustments
```

---

## 🚀 實作建議與未來擴充方向

### 8.1 v1 優先實作範圍

#### 必須實作（Must Have）

1. **單期 Mean-Variance 優化**
   - 目標函數：\(\max_w (w^T \mu - \lambda \cdot w^T \Sigma w)\)
   - 限制條件：
     - Long-only：\(w_i \geq 0, \forall i\)
     - Full Invested：\(\sum_i w_i = 1\)
     - Tracking Error 上限：\(TE(w) \leq TE_{\max}\)
     - 個股權重上限：\(w_i \leq w_{\max}, \forall i\)
     - 因子暴露限制：\(|E_{\text{fund},k} - E_{\text{bench},k}| \leq L_k, \forall k\)

2. **標準介面**
   - 輸入：μ, Σ, B, w_b, 限制條件參數
   - 輸出：w*, 風險診斷字典

3. **Risk Model 整合**
   - 透過 Risk Model 標準介面取得所有風險相關資料
   - 嚴格使用八大風險因子標準名稱

#### 建議實作（Should Have）

1. **參數驗證**
   - 驗證所有限制條件參數的合理性
   - 檢查優化問題的可行性（例如 TE_max 是否過小）

2. **優化失敗處理**
   - 當優化問題無解時，回報明確錯誤訊息
   - 提供限制條件放寬建議

#### 可選實作（Nice to Have）

1. **產業中性限制**（Sector Neutrality）
   - 視實作進度逐步加入

2. **換手率限制**（Turnover Constraint）
   - 可在 Backtest 中先實作檢查
   - Optimizer 整合可延後至未來版本

---

### 8.2 未來版本擴充方向

#### v2.0 預定功能

1. **Long/Short 模式**
   - 支援多空策略
   - 淨槓桿控制

2. **VaR / CVaR 限制**
   - 尾部風險控制

3. **多期優化**
   - 考慮交易成本的動態優化
   - 滾動視窗優化

4. **Robust Optimization**
   - 考慮參數不確定性的穩健優化
   - 最壞情況優化（Worst-case Optimization）

---

### 8.3 實作檔案結構

#### 核心模組

```
jgod/optimizer/
    __init__.py
    optimizer_core.py      # Optimizer 核心實作
    constraints.py         # 限制條件定義與驗證
    objective.py           # 目標函數定義
```

#### 測試模組

```
tests/optimizer/
    __init__.py
    test_optimizer_core.py    # Optimizer 核心測試
    test_constraints.py        # 限制條件測試
    test_objective.py          # 目標函數測試
```

#### 配置檔

```
config/
    optimizer_config.yaml      # Optimizer 預設參數配置
```

---

### 8.4 實作注意事項

1. **所有數值參數不得寫死在程式碼中**
   - 必須透過配置檔或函數參數傳入
   - 程式碼中可提供合理的預設值，但必須允許覆蓋

2. **嚴格遵循 Risk Model 標準介面**
   - 不得自行計算協方差矩陣
   - 必須使用標準風險因子名稱

3. **錯誤處理與日誌**
   - 優化失敗時提供明確錯誤訊息
   - 記錄優化過程中的關鍵資訊（目標函數值、約束違反情況等）

4. **效能考量**
   - 使用成熟的 QP 求解器（例如 CVXPY、cvxopt）
   - 對大規模問題（N > 100）考慮稀疏矩陣優化

---

## 📚 相關文件索引

- `docs/J-GOD_RISK_MODEL_STANDARD_v1.md` - Risk Model 標準規範
- `docs/八大風險因子_系統對映.md` - 八大風險因子系統對映
- `docs/J-GOD風險模型八大風險因子_AI知識庫版_v1.md` - 風險因子理論定義
- `jgod/risk/risk_model.py` - Risk Model 實作
- `jgod/risk/portfolio_risk.py` - 投資組合風險計算
- `jgod/risk/risk_factors.py` - 八大風險因子定義

---

**版本**：v1.0  
**最後更新**：2024-12-01  
**狀態**：✅ 標準規範已確立

---

> **重要提醒**：本文檔中的所有數值範例（如 TE_max = 5%、w_max = 0.06 等）均為**建議範例值**，實作時應以配置檔或參數配置為準，**不可寫死在程式碼中**。

