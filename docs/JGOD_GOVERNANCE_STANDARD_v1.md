# J-GOD Governance 標準 v1.0

**版本**: 1.0  
**最後更新**: 2025-12-04  
**適用範圍**: Path B、Path C、Path D

---

## 📋 治理的目標

J-GOD Governance 的目標是**確保所有策略符合機構級投資標準**，避免：

1. **風險不對稱**: 策略在特定市場環境下出現嚴重虧損
2. **過度槓桿**: 透過高風險換取報酬，而非真正的 alpha
3. **策略失效**: Alpha 訊號衰減但策略仍在執行
4. **流動性風險**: 換手率過高導致實際執行困難
5. **追蹤誤差過大**: 策略與預期表現偏差過大

透過多層級的 Governance 規則，J-GOD 確保只有**穩健、可解釋、符合風控要求**的策略才會被採用。

---

## 🎯 治理規則說明

### 1. SHARPE_TOO_LOW（Sharpe 比率過低）

**目的**: 確保策略的風險調整後報酬達到最低標準。

**判斷邏輯**:
```
if sharpe_ratio < sharpe_threshold:
    trigger "SHARPE_TOO_LOW"
```

**參數**:
- `sharpe_threshold`: 最低 Sharpe 比率門檻（float）

**實作位置**: `jgod/path_b/path_b_engine.py::_evaluate_governance_for_window()`

**預設閾值範例**:
- Basic Mode: `sharpe_threshold = 2.0`
- Extreme Mode: `sharpe_threshold = 2.0`（可調整更嚴格）
- Path C TW Equities 實驗: `min_sharpe = 1.0` (Basic), `1.5` (Extreme)

**說明**: Sharpe 比率低於門檻表示策略的風險調整後報酬不足，可能需要重新檢視策略邏輯或參數設定。

---

### 2. MAX_DRAWDOWN_BREACH（最大回撤超標）

**目的**: 確保策略的最大回撤控制在可接受範圍內。

**判斷邏輯**:
```
if max_drawdown <= max_drawdown_threshold:
    trigger "MAX_DRAWDOWN_BREACH"
```

**參數**:
- `max_drawdown_threshold`: 最大回撤限制（float，負數，例如 -0.15 表示 -15%）

**實作位置**: `jgod/path_b/path_b_engine.py::_evaluate_governance_for_window()`

**預設閾值範例**:
- Basic Mode: `max_drawdown_threshold = -0.15`（-15%）
- Extreme Mode: `max_drawdown_threshold = -0.15`（可調整更嚴格）
- Path C TW Equities 實驗: `max_drawdown_limit = 0.15`（15%）

**說明**: 最大回撤超過限制表示策略在不利市場環境下的風險控制不足，可能導致無法接受的損失。

---

### 3. TE_BREACH（追蹤誤差超標）

**目的**: 確保策略的實際表現與預期表現的偏差在可接受範圍內。

**判斷邏輯**:
```
if tracking_error > tracking_error_max:
    trigger "TE_BREACH"
```

**參數**:
- `tracking_error_max`: 最大追蹤誤差（float，例如 0.04 表示 4%）

**實作位置**: `jgod/path_b/path_b_engine.py::_evaluate_governance_for_window()`

**預設閾值範例**:
- Basic Mode: `tracking_error_max = 0.04`（4%）
- Extreme Mode: `tracking_error_max = 0.04`（可調整更嚴格）
- Path C TW Equities 實驗: `max_tracking_error = 0.04`（4%）

**說明**: 追蹤誤差過大表示策略的實際表現與預期偏差過大，可能是風險模型不準確或執行問題。

---

### 4. TURNOVER_TOO_HIGH（換手率過高）

**目的**: 確保策略的換手率在可執行範圍內，避免流動性風險與過高的交易成本。

**判斷邏輯**:
```
if turnover_rate > turnover_max:
    trigger "TURNOVER_TOO_HIGH"
```

**參數**:
- `turnover_max`: 最大換手率（float，例如 1.0 表示 100% per window，或 3.0 表示年化 300%）

**實作位置**: `jgod/path_b/path_b_engine.py::_evaluate_governance_for_window()`

**預設閾值範例**:
- Basic Mode: `turnover_max = 1.0`（100% per window）
- Extreme Mode: `turnover_max = 1.0`（可調整更嚴格）
- Path C TW Equities 實驗: `max_turnover = 3.0`（年化 300%）

**說明**: 換手率過高會導致：
- 交易成本過高（手續費、滑價）
- 流動性風險（大額交易可能無法執行）
- 策略可能過度交易（over-trading）

---

## 📊 治理彙總指標

### Breach Ratio（違規比例）

**定義**: 
```
breach_ratio = windows_with_any_breach / total_windows
```

**用途**: 衡量策略在所有時間視窗中違規的比例。

**判斷標準**:
- `breach_ratio = 0.0`: 完全符合 Governance（最佳）
- `breach_ratio < 0.2`: 大部分時間符合（可接受）
- `breach_ratio >= 0.2`: 違規頻繁（需檢討）
- `breach_ratio = 1.0`: 全部違規（不可接受）

**實作位置**: `jgod/path_b/path_b_engine.py::_compute_governance_summary()`

---

### Max Consecutive Breach Windows（最大連續違規視窗數）

**定義**: 連續違規的視窗數量。

**用途**: 識別策略是否在特定市場環境下持續失效。

**判斷標準**:
- `max_consecutive = 0`: 沒有連續違規（最佳）
- `max_consecutive <= 2`: 偶發性違規（可接受）
- `max_consecutive > 2`: 持續性違規（需檢討）

**實作位置**: `jgod/path_b/path_b_engine.py::_compute_governance_summary()`

---

### Rule Hit Counts（規則觸發次數）

**定義**: 每個規則被觸發的次數統計。

**用途**: 識別策略最容易違反的規則，指導策略改進方向。

**實作位置**: `jgod/path_b/path_b_engine.py::_compute_governance_summary()`

**範例輸出**:
```python
rule_hit_counts = {
    "SHARPE_TOO_LOW": 5,
    "MAX_DRAWDOWN_BREACH": 3,
    "TE_BREACH": 1,
    "TURNOVER_TOO_HIGH": 0,
}
```

---

## 🔧 實務判斷閾值範例

### Path C TW Equities 實驗（真實市場驗證）

**Basic Mode**:
- `min_sharpe = 1.0`
- `max_drawdown_limit = 0.15`（15%）
- `max_tracking_error = 0.04`（4%）
- `max_turnover = 3.0`（年化 300%）

**Extreme Mode**:
- `min_sharpe = 1.5`（更嚴格）
- `max_drawdown_limit = 0.15`（15%）
- `max_tracking_error = 0.04`（4%）
- `max_turnover = 3.0`（年化 300%）

**結果解讀**:
- 根據 `docs/JGOD_PATH_C_TW_EQUITIES_EXPERIMENTS_v1.md`，所有 Scenario 的 `breach_ratio = 100%`
- 這表示當前策略配置在真實台股市場上未達到 Governance 標準
- 這是**預期結果**，因為 Governance 的目的是「阻止不合格策略」，而非「讓所有策略都通過」

---

### Path D RL 優化後的結果

**目標**: 透過 RL 優化治理參數，使策略從 `breach_ratio = 100%` 降到 `0%`

**根據 `docs/JGOD_PATH_D_TW_EXPERIMENT_v1.md`**:
- Baseline Path B: `breach_ratio = 100%`
- Path D 優化後: `breach_ratio = 0%` ✅

**RL 成功找到一組治理參數，使策略完全符合 Governance 標準。**

---

## 🔮 未來可擴充的治理規則

### 1. CVaR（Conditional Value at Risk）

**目標**: 更嚴格地控制尾端風險。

**判斷邏輯**:
```
if cvar_95 > cvar_threshold:
    trigger "CVAR_BREACH"
```

**說明**: CVaR 衡量在最壞情況（例如 5% 最壞情況）下的預期損失，比 MaxDD 更能捕捉極端風險。

---

### 2. Alpha Decay Detection（Alpha 衰減偵測）

**目標**: 偵測 Alpha 訊號是否正在衰減。

**判斷邏輯**:
```
if alpha_score_trailing_avg < alpha_score_historical_avg * decay_threshold:
    trigger "ALPHA_DECAY"
```

**說明**: 當 Alpha 訊號持續下降時，應考慮停用或調整策略。

---

### 3. Regime Mismatch（市場環境不匹配）

**目標**: 偵測策略是否在不適合的市場環境下運作。

**判斷邏輯**:
```
if current_regime != strategy_optimal_regime:
    trigger "REGIME_MISMATCH"
```

**說明**: 當市場環境（例如趨勢 vs 震盪）與策略設計的環境不匹配時，應調整策略或降低曝險。

---

### 4. Drawdown-Aware RL

**目標**: 在 Path D RL 的 Reward 函數中加入 Drawdown-aware 懲罰。

**實作方向**:
```python
def compute_reward(...):
    # 現有邏輯
    reward = base_reward + penalty_dd + penalty_breach
    
    # 新增: Drawdown-aware 懲罰
    if max_drawdown > current_max_drawdown_limit:
        penalty_dd_aware = -10.0 * (max_drawdown - current_max_drawdown_limit)
        reward += penalty_dd_aware
```

---

### 5. Correlation Breach（相關性超標）

**目標**: 確保策略與市場或基準的相關性在合理範圍內。

**判斷邏輯**:
```
if correlation_with_benchmark > max_correlation:
    trigger "CORRELATION_BREACH"
```

**說明**: 如果策略與基準高度相關，可能表示策略缺乏獨立的 alpha。

---

## 📝 實作細節

### Path B 中的實作

**檔案**: `jgod/path_b/path_b_engine.py`

**關鍵方法**:
- `_evaluate_governance_for_window()`: 評估單一 Window 的 Governance 規則
- `_compute_governance_summary()`: 計算所有 Window 的 Governance 彙總

**資料結構**:
- `PathBWindowGovernanceResult`: 單一 Window 的 Governance 結果
- `PathBRunGovernanceSummary`: 整體 Governance 彙總

---

### Path C 中的使用

Path C 會讀取每個 Scenario 的 Path B 結果，並從 `PathBRunGovernanceSummary` 中提取：
- `governance_breach_ratio`
- `rule_hit_counts`
- `max_consecutive_breach_windows`

這些指標用於 Scenario 排名與比較。

---

### Path D 中的使用

Path D RL Engine 的 Reward 函數會考慮 Governance 違規情況：

```python
def compute_reward(sharpe, max_drawdown, breach_ratio, avg_turnover):
    base = sharpe
    penalty_breach = -5.0 * breach_ratio  # 重大懲罰
    # ... 其他懲罰
    reward = base + penalty_breach + ...
```

Path D 的目標是找到一組參數，使 `breach_ratio` 降到最低（理想為 0）。

---

## 🎯 總結

J-GOD Governance 標準是確保策略品質的「憲法」，所有策略必須通過以下檢查：

1. ✅ Sharpe 比率達到最低標準
2. ✅ 最大回撤控制在可接受範圍內
3. ✅ 追蹤誤差在合理範圍內
4. ✅ 換手率在可執行範圍內

**Breach Ratio = 0% 是目標，但即使 Breach Ratio > 0%，只要能通過其他標準（例如 Sharpe、MaxDD），策略仍然可能被採用。**

---

**最後更新**: 2025-12-04

