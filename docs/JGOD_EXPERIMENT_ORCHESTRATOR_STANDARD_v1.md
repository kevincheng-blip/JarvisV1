# J-GOD Experiment Orchestrator & Reporting Standard v1

### Step 9 — 實驗編排器與報告生成標準規格

---

# 1. Step 9 的角色與定位

## 1.1 要解決的問題

目前我們已經建立了完整的模組生態：

- **Path A Backtest 核心**：`run_path_a_backtest(...)`
- **FinMind Loader**：`FinMindPathADataLoader`
- **Optimizer v2**：`OptimizerCoreV2`
- **Execution Engine v1**：交易執行
- **Performance & Attribution Engine v1**：績效分析
- **Diagnosis & Repair Engine v1**：系統診斷
- **ErrorLearningEngine + Knowledge Brain**：錯誤學習

**Step 9 的目標**：建立一個「一鍵實驗 + 自動報告管線」

> **給一組實驗設定 → 自動跑完 Path A → 執行交易 → 算績效 → 做歸因 → 診斷 + 修復建議 → 輸出報告（檔案＋Console）**

讓使用者只需要一個指令，就能跑一個完整實驗，而不需要手動串接每一個模組。

## 1.2 在整個 J-GOD 系統中的位置

```
┌─────────────────────────────────────────────────────────┐
│      Experiment Orchestrator (Step 9) - 實驗大腦        │
│                                                          │
│  • 接收 ExperimentConfig                                 │
│  • 編排整個實驗流程                                       │
│  • 收集所有模組的結果                                     │
│  • 生成完整報告                                           │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐  ┌─────────▼────────────┐
│ Path A Backtest│  │ Performance Engine   │
│  • DataLoader  │  │  • Metrics           │
│  • AlphaEngine │  │  • Attribution       │
│  • RiskModel   │  └──────────────────────┘
│  • Optimizer   │
│  • Execution   │  ┌──────────────────────┐
└───────────────┘  │ Diagnosis Engine     │
                   │  • Health Check       │
                   │  • Repair Plan        │
                   └───────────────────────┘
                           │
                   ┌───────▼────────┐
                   │ ErrorLearning  │
                   │    Engine      │
                   └────────────────┘
```

## 1.3 核心價值

- **一鍵執行**：單一指令完成完整實驗
- **自動化報告**：自動生成多格式報告
- **模組化整合**：不重複發明輪子，只「編排」現有模組
- **可重現性**：所有實驗設定和結果都完整記錄

---

# 2. 完整實驗生命週期（Life-cycle）

## 2.1 ASCII 流程圖

```
┌─────────────────────────────────────────────────────────┐
│                  Experiment Config                       │
│  • name, dates, universe                                │
│  • optimizer_params, execution_params                    │
│  • diagnosis_params                                      │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│  Step 1: Load Data                                      │
│  • DataLoader (FinMind / Mock)                          │
│  • 價格 + 特徵 DataFrame                                 │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│  Step 2: Run Path A Backtest                            │
│  • AlphaEngine → expected returns                       │
│  • RiskModel → covariance matrix                        │
│  • OptimizerCoreV2 → target weights                     │
│  • ExecutionEngine → trades & fills                     │
│  • → PathABacktestResult                                │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│  Step 3: Analyze Performance                            │
│  • PerformanceEngine.compute_full_report()              │
│  • PerformanceSummary                                   │
│  • AttributionReport                                    │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│  Step 4: Run Diagnosis                                  │
│  • DiagnosisEngine.from_path_a_and_performance()        │
│  • SystemHealthSnapshot                                 │
│  • DiagnosticEvents                                     │
│  • RepairPlan                                           │
│  • → ErrorLearningEngine (自動觸發)                     │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│  Step 5: Build Report                                   │
│  • 組合 summary 指標                                    │
│  • 生成亮點摘要                                         │
│  • 整理修復建議                                         │
│  • 記錄檔案清單                                         │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│  Step 6: Persist Outputs                                │
│  • output/experiments/{name}/nav.csv                    │
│  • output/experiments/{name}/returns.csv                │
│  • output/experiments/{name}/performance_summary.json   │
│  • output/experiments/{name}/diagnosis_report.md        │
│  • output/experiments/{name}/repair_plan.md             │
└─────────────────────────────────────────────────────────┘
```

## 2.2 詳細步驟說明

### Step 1: Load Data

使用 `PathADataLoader` 載入資料：
- 價格資料（OHLCV）
- 特徵資料（用於 Alpha Engine）
- 因子資料（用於 Risk Model）

### Step 2: Run Path A Backtest

調用現有的 `run_path_a_backtest()` 函數，它內部會：
1. 遍歷每個交易日
2. 在再平衡日：
   - AlphaEngine 計算預期報酬
   - RiskModel 更新協方差矩陣
   - OptimizerCoreV2 計算目標權重
   - ExecutionEngine 執行交易
3. 記錄每日 NAV 和 returns

### Step 3: Analyze Performance

使用 PerformanceEngine 分析：
- 計算績效指標（Sharpe、Max Drawdown、IR、TE）
- 進行歸因分析（Symbol、Sector、Factor）

### Step 4: Run Diagnosis

使用 DiagnosisEngine 診斷：
- 建立 SystemHealthSnapshot
- 生成 DiagnosticEvents
- 產生 RepairPlan
- 自動橋接到 ErrorLearningEngine

### Step 5: Build Report

組合所有結果：
- 績效摘要
- 亮點摘要（供人類閱讀）
- 診斷摘要
- 修復建議

### Step 6: Persist Outputs

將結果寫入檔案：
- CSV 檔案（NAV、returns）
- JSON 檔案（performance summary）
- Markdown 檔案（診斷報告、修復計畫）

---

# 3. 推薦使用方式

## 3.1 小型實驗（幾檔股票）

**適用場景**：測試新策略、驗證單一因子

**範例設定**：
```python
config = ExperimentConfig(
    name="test_single_factor",
    start_date="2023-01-01",
    end_date="2023-12-31",
    rebalance_frequency="M",
    universe=["2330.TW", "2317.TW", "2454.TW"],
    data_source="finmind",
    optimizer_params={
        "lambda": 1.0,
        "TE_max": 0.05,
        "T_max": 0.20,
    },
    notes="測試單一 Alpha 因子效果"
)
```

## 3.2 中型實驗（TW50 宇宙）

**適用場景**：完整策略驗證、多因子組合測試

**範例設定**：
```python
config = ExperimentConfig(
    name="tw50_full_test",
    start_date="2022-01-01",
    end_date="2023-12-31",
    rebalance_frequency="M",
    universe=TW50_SYMBOLS,  # 50 檔股票
    data_source="finmind",
    optimizer_params={
        "lambda": 1.0,
        "TE_max": 0.05,
        "T_max": 0.15,
        "factor_limits": {...},
        "sector_limits": {...},
    },
    notes="TW50 完整策略測試"
)
```

## 3.3 不同時區 / 區間對比

**適用場景**：測試策略在不同市場環境下的表現

**範例設定**：
```python
# 牛市期間
config_bull = ExperimentConfig(
    name="bull_market_2020",
    start_date="2020-01-01",
    end_date="2020-12-31",
    ...
)

# 熊市期間
config_bear = ExperimentConfig(
    name="bear_market_2022",
    start_date="2022-01-01",
    end_date="2022-12-31",
    ...
)

# 對比兩個時期
```

---

# 4. 輸出檔案結構

## 4.1 目錄結構

```
output/experiments/
└── {experiment_name}/
    ├── nav.csv                    # NAV 時間序列
    ├── returns.csv                # Returns 時間序列
    ├── performance_summary.json   # 績效摘要（JSON）
    ├── performance_report.md      # 績效報告（Markdown）
    ├── diagnosis_report.md        # 診斷報告（Markdown）
    ├── repair_plan.md            # 修復計畫（Markdown）
    ├── config.json               # 實驗設定（JSON，用於重現）
    └── artifacts/                # 中間產物（可選）
        ├── path_a_result.pkl
        ├── performance_result.pkl
        └── diagnosis_result.pkl
```

## 4.2 檔案格式說明

### nav.csv

```csv
date,nav
2023-01-01,100.0
2023-01-02,100.5
...
```

### performance_summary.json

```json
{
  "total_return": 0.15,
  "cagr": 0.12,
  "sharpe": 1.2,
  "max_drawdown": -0.08,
  "tracking_error": 0.04,
  "turnover": 0.15,
  ...
}
```

### performance_report.md

包含：
- 績效指標表格
- 歸因分析表格
- 圖表（可選）

### diagnosis_report.md

包含：
- 系統健康快照
- 診斷事件列表
- 問題摘要

### repair_plan.md

包含：
- 修復建議摘要
- 優先級排序的修復行動
- 配置調整建議

---

# 5. 設計原則

## 5.1 Orchestrator 不重複發明輪子

**原則**：不要在 Orchestrator 中重寫 Alpha / Risk / Optimizer / Execution / Performance / Diagnosis 的邏輯，只「呼叫」。

**實作方式**：
- 所有業務邏輯都透過現有模組的 API 呼叫
- Orchestrator 只負責編排和資料傳遞

## 5.2 所有數字都來自 config

**原則**：不要 hard-code TE_max、T_max、Sharpe threshold 等。

**實作方式**：
- 所有參數都從 `ExperimentConfig` 讀取
- 提供合理的預設值，但允許覆蓋

## 5.3 強調「實驗」而不是「實盤」

**原則**：Step 9 v1 僅用於 Path A / Backtest / Simulation。

**實作方式**：
- 所有輸出都標記為「實驗結果」
- 不包含實盤交易相關功能

## 5.4 與 ErrorLearningEngine 的關係

**原則**：Orchestrator 不直接操作 ErrorLearning 的細節，而是透過 DiagnosisEngine 來間接觸發。

**實作方式**：
- DiagnosisEngine 負責橋接到 ErrorLearningEngine
- Orchestrator 只需要呼叫 DiagnosisEngine，不需要直接操作 ErrorLearningEngine

---

# 6. 實作架構

## 6.1 模組結構

```
jgod/experiments/
├── __init__.py
├── experiment_types.py      # 資料結構定義
└── experiment_orchestrator.py  # 核心編排器
```

## 6.2 依賴關係

```
ExperimentOrchestrator
  ├── PathADataLoader
  ├── AlphaEngine
  ├── MultiFactorRiskModel
  ├── OptimizerCoreV2
  ├── ExecutionEngine
  ├── PerformanceEngine
  ├── DiagnosisEngine
  ├── KnowledgeBrain
  └── ErrorLearningEngine
```

---

# 7. Required Inputs & Outputs

## 7.1 Inputs

### ExperimentConfig

包含實驗的所有設定：
- 基本資訊（name、dates、universe）
- 資料來源（data_source）
- 優化器參數（optimizer_params）
- 執行參數（execution_params）
- 診斷參數（diagnosis_params）

## 7.2 Outputs

### ExperimentRunResult

包含：
- `config`：實驗設定
- `artifacts`：所有中間產物
- `report`：完整報告

---

# 8. Integration with Existing Modules

## 8.1 Path A Backtest

直接使用現有的 `run_path_a_backtest()` 函數，不重新實作。

## 8.2 Performance Engine

使用 `PerformanceEngine.compute_full_report()` 方法。

## 8.3 Diagnosis Engine

使用 `DiagnosisEngine.from_path_a_and_performance()` 方法。

## 8.4 ErrorLearningEngine

透過 DiagnosisEngine 間接觸發，不直接操作。

---

**版本**：v1.0  
**最後更新**：2025-12-02  
**狀態**：✅ 標準規範已確立

