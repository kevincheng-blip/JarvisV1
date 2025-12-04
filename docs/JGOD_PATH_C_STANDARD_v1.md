# J-GOD Path C Engine Standard v1

## 📖 概述

Path C Engine（Validation Lab / Scenario Engine）是 J-GOD 系統中用於批次場景驗證的核心引擎。它透過呼叫 Path B Engine 多次，比較不同設定組合的表現，並識別最佳策略候選。

---

## 🎯 Path A / Path B / Path C 對照表

| 引擎 | 功能 | 輸入 | 輸出 |
|------|------|------|------|
| **Path A** | 單一回測 | 一組策略設定 | 單一回測結果 |
| **Path B** | Walk-Forward 分析 | 一組策略設定 + Walk-Forward 參數 | 多個 Window 的結果 + Governance 評估 |
| **Path C** | 批次場景驗證 | 多組策略設定（Scenarios） | 所有 Scenarios 的排名 + 最佳候選 |

---

## 📋 Path C 使用情境

### 1. 比較不同 Window/Step 組合

測試不同的 walk-forward window 和 step 大小：

- Scenario 1: 6m window, 1m step
- Scenario 2: 6m window, 3m step
- Scenario 3: 12m window, 3m step

### 2. 比較 Basic vs Extreme Mode

測試相同設定在不同模式下的表現：

- Scenario 1: Basic mode
- Scenario 2: Extreme mode

### 3. 比較不同 Universe

測試不同股票組合：

- Scenario 1: 台積電 + 鴻海
- Scenario 2: 台塑 + 中鋼
- Scenario 3: 全部股票

### 4. 比較不同治理門檻

測試不同風險控制設定：

- Scenario 1: 嚴格門檻（MaxDD = -10%, Sharpe >= 2.5）
- Scenario 2: 寬鬆門檻（MaxDD = -20%, Sharpe >= 1.5）

---

## 📊 核心指標

Path C 報告中使用的核心指標：

### 1. Sharpe Ratio（平均）

所有 Window 的 Sharpe Ratio 平均值。越高越好。

### 2. Max Drawdown

所有 Window 的最大回撤平均值。越小越好（負數，越接近 0 越好）。

### 3. Governance Breach 比例

觸發 Governance 規則的 Window 比例。越低越好。

### 4. 排名方法

Path C 使用以下規則進行排名：

1. **主要排序**：Sharpe Ratio（降冪）
2. **次要排序**：Max Drawdown（升冪）
3. **第三排序**：Governance Breach Ratio（升冪）

---

## 📁 輸出檔案說明

### scenarios_rankings.csv

包含所有 scenarios 的排名表，欄位包括：

- rank: 排名
- scenario_name: Scenario 名稱
- sharpe: Sharpe Ratio
- max_drawdown: 最大回撤
- total_return: 總報酬
- governance_breach_ratio: Breach 比例
- mode: 模式（basic/extreme）
- data_source: 資料來源

### path_c_summary.json

完整的實驗總結，包含：

- experiment_name: 實驗名稱
- total_scenarios: 總 Scenario 數量
- successful_scenarios: 成功數量
- best_scenarios: 最佳 Scenario 名稱列表
- ranking_table: 完整排名表
- scenarios: 所有 Scenario 的詳細結果

### path_c_report.md

可讀性高的 Markdown 報告，包含：

- 實驗基本資訊
- 前 3 名 Scenario 的詳細資訊
- 所有 Scenarios 的摘要表格

---

## 🔧 使用方式

### 使用預設 Scenarios

```bash
PYTHONPATH=. python3 scripts/run_jgod_path_c.py \
  --name demo_path_c \
  --output-dir output/path_c
```

### 使用自訂 Config JSON

```bash
PYTHONPATH=. python3 scripts/run_jgod_path_c.py \
  --name custom_experiment \
  --config path/to/scenarios.json \
  --output-dir output/path_c
```

---

## 4. Taiwan Equities Real-Market Validation (FinMind)

### 概述

Path C 可用來對「真實台股資料」進行 Validation Lab，驗證策略在真實市場環境下的穩健性、失效模式以及治理規則的有效性。

### 實驗配置

對應的實驗配置 JSON：

- **配置檔案**: `configs/path_c/path_c_tw_equities_v1.json`
- **實驗期間**: 2015-01-01 ~ 2024-12-31（涵蓋一輪完整牛熊週期）
- **資料來源**: FinMind 台股日行情
- **股票池**: 台股前 10 大市值股票

### Scenario 設計

#### Basic Mode Scenarios

用於確認基礎策略在真實市場環境下的穩健性表現：

- `basic_3y_6m_top10`: 3 年訓練窗，6 個月步長
- `basic_5y_6m_top10`: 5 年訓練窗，6 個月步長
- `basic_2y_3m_top10`: 2 年訓練窗，3 個月步長（高適應性）

**目標**: Sharpe Ratio 穩定在 1.5~2.0 以上，Max Drawdown 控制在 15% 以內，Governance Breach 比例低。

#### Extreme Mode Scenarios

用於觀察策略在高壓情境下的失效模式與治理規則觸發情況：

- `extreme_3y_6m_top10`: 3 年訓練窗，6 個月步長（壓力測試）
- `extreme_3y_3m_top10`: 3 年訓練窗，3 個月步長（模擬 regime shift）
- `extreme_2y_3m_top10`: 2 年訓練窗，3 個月步長（高適應，易 overfit）

**目標**: 觀察 Sharpe 下降、MaxDD 超標、Governance Rule 觸發情況，驗證治理規則的有效性。

### 執行前準備

#### 1. FinMind API 金鑰設定

實際執行前需要設定 FinMind API 金鑰：

```bash
export FINMIND_TOKEN=your_token_here
```

或在 `.env` 檔案中設定：

```
FINMIND_TOKEN=your_token_here
```

參考文件：
- `docs/JGOD_FINMIND_LOADER_STANDARD_v1.md`: FinMind 資料載入器說明

#### 2. 執行指令

```bash
PYTHONPATH=. python3 scripts/run_jgod_path_c.py \
  --name tw_equities_v1 \
  --config configs/path_c/path_c_tw_equities_v1.json \
  --output-dir output/path_c
```

#### 3. 執行時間預估

- 每個 Scenario: 約 5-15 分鐘（取決於 Window 數量）
- 完整實驗（6 個 Scenario）: 約 30-90 分鐘

### 詳細文件

更多詳細資訊請參考：

- `docs/JGOD_PATH_C_TW_EQUITIES_EXPERIMENTS_v1.md`: 完整的實驗設計文件

---

## 📝 備註

- Path C 僅調用 Path B，不重複實作回測邏輯
- 每個 Scenario 的執行時間取決於 Path B 的複雜度
- 建議在測試環境中先用少量 Scenario 驗證，再進行完整實驗
- 使用 FinMind 資料時，請確保 API 金鑰已正確設定

