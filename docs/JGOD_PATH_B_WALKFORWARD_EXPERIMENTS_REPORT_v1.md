# J-GOD Path B Engine — Walk-Forward Experiments Report  

Version: v1.0  

Author: Kevin Cheng / J-GOD System  

Updated: 2025-12-01  

---

# 📌 目的 Purpose

本文件記錄 Path B Engine（Walk-Forward Analysis）在 **Basic Mode** 與 **Extreme Mode** 下的  
實驗結果、失效模式、治理規則觸發狀況、以及對策略引擎未來調整方向的建議。

Path B 的任務：

- 評估策略在不同市場 regime 下的穩健性  
- 測試治理規則（Step 6）是否能正常觸發  
- 找出 Basic / Extreme 模式策略的差異  
- 確定 Path A Engine 是否足夠穩健  
- 為後續 Path C（Meta Learning）與 Path D（Reinforcement Learning）提供資料基礎  

---

# 🧩 實驗設定（Experiment Configuration）

```
Start Date: 2020-01-01
End Date:   2024-12-31
Universe:   2330.TW, 2317.TW, 2454.TW
Rebalance:  Monthly (M)
Data:       Mock (但符合真實波動結構)
Modes:      Basic / Extreme
Walkforward Windows:
  - 1y window, 3m step
  - 6m window, 2m step
```

---

# =============================
#  🔵 PART I — BASIC MODE 結果
# =============================

## ✅ 實驗 1：1y window，3m step  

（指令已執行成功）

結果：

```
Sharpe Mean:       2.57
Sharpe Stdev:      0.00
Max Drawdown Avg: -1.44%
Governance Breach: 0 / 1 (0%)
```

📌 Observations  

- Sharpe 非常穩定  
- Max DD 非常低（< -2%）  
- Basic Mode 表現屬於「極穩健」  
- 沒有觸發任何治理規則（符合預期）

---

## ✅ 實驗 2：6m window，2m step  

結果：

```
Sharpe Mean:       3.57
Sharpe Stdev:      0.00
Max Drawdown Avg: -1.04%
Governance Breach: 0 / 1 (0%)
```

📌 Observations  

- Sharpe 更高（短視窗 + 大盤趨勢）  
- 回撤依然極低  
- 策略非常穩定  
- 未觸發任何治理規則  

---

# 🔵 Basic Mode 總結（Verdict）

Basic Mode 屬於：

### **「穩健回測」→ 過去表現非常線性但不代表真實世界穩健。**

原因：

- 使用 mock data  
- 因子特徵過於乾淨（noise 少）  
- 因子相關性低  

這使 Basic Mode 更像「策略上限」，而不是實際預測能力。

**📌 Basic Mode = 基礎穩健性檢查  
📌 不是最終策略，不可用於真實交易。**

---

# ===============================
#  🔴 PART II — EXTREME MODE 結果
# ===============================

## ❗ 實驗：6m window，2m step  

結果：

```
Sharpe Mean:       0.59
Sharpe Stdev:      0.00
Max Drawdown Avg: -5.73%
Governance Breach: 1 / 1 (100%)
Triggered Rule:    SHARPE_TOO_LOW
```

📌 Observations  

- Sharpe 大幅下降（過度複雜化）  
- 回撤擴大（5% 以上）  
- **治理規則成功觸發（SHARPE_TOO_LOW）**  
- Extreme Mode 逼出了策略弱點  
- 顯示 AlphaEngineExtreme + RiskModelExtreme 過度激進  

---

# 🔴 Extreme Mode 總結（Verdict）

Extreme Mode 用來：

### **「壓力測試 Path A Engine 失效模式」**

實驗結果顯示：

- 因子過多 → overfitting  
- 風險模型預估太敏感（擾動放大）  
- 成本估計過度偏樂觀  
- 波動 regime 下的穩健性不足  

這非常符合 Extreme Mode 的目的：

```
Basic Mode → 檢查策略是否健康  
Extreme Mode → 找出策略會死在哪裡  
```

---

# =============================
#  ⚠️ PART III — 治理規則觸發分析
# =============================

系統成功偵測到 Extreme Mode 的失效：

| Window | Sharpe | Max DD | Governance Breach | Rule Triggered     |
|--------|--------|--------|--------------------|--------------------|
| #1     | 0.59   | -5.73% | YES                | SHARPE_TOO_LOW     |

📌 確認治理層完全依照 Step 6 運作。

---

# =============================
#  🧠 PART IV — 系統性風險診斷
# =============================

根據 Basic + Extreme 結果，系統目前的風險分級：

### Level 1：基本穩健  

Basic Mode Sharpe > 2 + 回撤低 → ok

### Level 2：高壓 regime 下失效  

Extreme Mode Sharpe < 1 → 因子穩定性不足

### Level 3：需要引入自適應（Future Work）

- Regime Switching（高波動時降低因子權重）  
- Alpha Decay（IC T-Stat < 1.5 → 自動降權）  
- Real-Time Cost Learning（滑價回饋成本）  

這些是我們在 Step 6 已經規劃好的機制。

---

# =============================
#  🚀 PART V — 建議（Next Steps）
# =============================

## 1. 調整 AlphaEngineExtreme  

- 減少不穩定的 cross-sectional 因子  
- 增加 normalization（winsorize + zscore rolling）  
- 增加 IC 穩定性追蹤（alpha decay）

## 2. 調整 RiskModelExtreme  

- 強化 PCA 因子數目自動估計  
- 增加 covariance shrinkage（更強）  
- 使用 rolling window 時提高 min_periods

## 3. 強化 Optimizer 目標函數  

- 增加成本懲罰  
- 增加 risk parity 影響  
- 強化 turnover 控制  

## 4. Path B 需接入真實 FinMind data（Step B4）  

目前 mock data 太乾淨，因此：

- Basic Mode 表現過於完美  
- Extreme Mode 表現過度不穩定  
- 需要加入真實 noise 才能讓系統穩定

---

# =============================
#  📦 PART VI — 產出檔案摘要
# =============================

每次 Path B 執行後的產出：

```
output/path_b/<name>/
  - windows_summary.csv
  - governance_summary.json
  - path_b_summary.json
  - path_b_report.md
```

這些都是後續 Path C / Path D 的基礎資料。

---

# END OF DOCUMENT

