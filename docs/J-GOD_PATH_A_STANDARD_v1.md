# J-GOD PATH A STANDARD v1.0

（Validation Lab / 驗證實驗室 標準規格）

> 版本：v1.0  
> 狀態：Draft（可執行骨架）  
> 目的：定義「Path A 驗證實驗室」的標準結構、資料流程與與現有模組的介面。

---

## 1. Path A 的定位

Path A = **Validation Lab（驗證實驗室）**

目標不是追求最漂亮的績效，而是：

1. 在「真實歷史資料」上，讓 J-GOD 的核心骨架實際跑起來：

   - Alpha Engine v1

   - Risk Model v1

   - Optimizer v1

   - Knowledge Brain v1

   - Error Learning Engine v1.1

2. 找出「資料 / Alpha / Risk / Optimizer / Execution 偏差」並將錯誤事件送入 Error Learning Engine。

3. 建立一套可重複、可回溯、可比較的驗證流程。

---

## 2. 系統邏輯總覽（Alpha → Risk → Optimizer → Path A → Error Engine）

整體流程：

1. **DataLoader**  

   - 從 FinMind 或其他來源撈取歷史資料  

   - 轉成統一格式的 `PathADailyInput` / `PathAFeatureFrame`  

2. **Alpha Engine Adapter**  

   - 將 Path A 的特徵 DataFrame 餵進 `AlphaEngine`  

   - 產生 `composite_alpha`（per date, per symbol）

3. **Risk Model Adapter**  

   - 使用歷史窗口（例如：過去 252 交易日）估計：

     - 因子暴露 B

     - 因子協方差 F

     - 特有風險 D

   - 產生共變異矩陣 Σ

4. **Optimizer Adapter**  

   - 將 Alpha 預期報酬向量 μ（可由 composite_alpha 映射）與 Σ 餵給 `OptimizerCore`  

   - 套用權重 / TE / 因子暴露等限制  

   - 產出當期投資組合權重 `w_t`

5. **Path A Backtest Engine（簡化版）**  

   - 以「隔日開盤價」或「當日收盤價」模擬持有與調整  

   - 產生：

     - 每日 NAV / 組合報酬

     - 每日持股權重

     - Trade list / Turnover

6. **Error Bridge → Error Learning Engine**  

   - 針對每次「預測 vs 實際結果」產生 `ErrorEvent`：

     - Input: 預測分數 / 實際報酬 / 當時市場狀態 / 風險暴露

     - Output: ErrorAnalysisResult（分類 + 建議）

   - 將錯誤報告與新規則草案寫入：

     - `error_logs/reports/*.md`

     - `knowledge_base/jgod_knowledge_drafts.jsonl`

---

## 3. Path A 模組結構

目錄規劃（未來目標）：

```text

jgod/

  path_a/

    __init__.py

    path_a_config.py          # PathAConfig 定義

    path_a_schema.py          # 所有 Path A 的資料結構

    path_a_backtest.py        # Path A Backtest Skeleton

    path_a_error_bridge.py    # 將結果轉成 ErrorEvent 的橋接器

    data_loader/

      __init__.py

      finmind_loader.py       # 簡化版 FinMind 資料載入器（之後實作）

    utils/

      date_utils.py

      universe_utils.py

本標準文件 v1 僅要求建立：

path_a_schema.py

path_a_backtest.py

path_a_error_bridge.py（骨架）

path_a_config.py（簡單 Config，後續可擴充）

```

---

## 4. Path A 的 Universe 與時間區間（建議）

Universe 建議：

- 台股 0050 成分股（約 50 檔）

- 額外加入 1–5 檔代表性指數或金融股 / 傳產股

- 合計約 50–60 檔標的

時間區間建議：

- 測試區間：至少 2–3 年（例如 2022-01-01 ～ 2024-12-31）

- 訓練 / 校準窗口：252 交易日（約一年）

- Rebalancing：每月一次（或每週一次，視 PathAConfig 而定）

---

## 5. FinMind 資料欄位（v1 需求）

Path A v1 僅要求「日資料可用版本」，欄位包含（以 DataFrame 思維）：

### 5.1 價格與成交量（必備）

- `date`
- `symbol`
- `open`
- `high`
- `low`
- `close`（或 `adj_close`）
- `volume`

### 5.2 法人籌碼（可選但強烈建議）

- `foreign_net`
- `investment_trust_net`
- `dealer_net`

以及對應的累積或 N 日 rolling 指標（可由 FeatureBuilder 衍生）

### 5.3 融資融券（可選）

- `margin_balance`
- `short_balance`

### 5.4 基本面（可選）

- `pe`
- `pb`
- `roe`
- `roa`
- `market_cap`

### 5.5 市場與指數（可選）

- 大盤指數報酬
- 產業指數報酬
- 匯率 / 利率 / CPI（若 FinMind 能提供）

**v1 的 Path A 標準：先定義欄位與 Schema，不強迫一次全部接好 FinMind。**

---

## 6. 核心資料結構（概念）

詳細型別在 `path_a_schema.py` 實作，這裡只定義概念：

### PathAConfig：

- 測試區間（start_date, end_date）
- Universe 列表
- Rebalance 週期
- Transaction cost / slippage 假設
- 其他實驗參數

### PathADailyInput：

- 某一日的原始輸入資料（含所有 symbols 的 OHLCV + feature 欄位）

### PathAFeatureFrame：

- 整段期間、整個 Universe 的特徵表（MultiIndex: [date, symbol]）

### PathAPrediction：

- 當日每檔標的的 composite_alpha / signal

### PathAPortfolioSnapshot：

- 某日的投資組合狀態（權重 / NAV / factor exposure）

### PathABacktestResult：

- NAV 曲線
- 每日報酬
- Trade list / Turnover
- ErrorEvent 列表

---

## 7. Path A Backtest Skeleton（邏輯）

Pseudo-code：

```python
def run_path_a_backtest(
    config: PathAConfig,
    data_loader: PathADataLoader,
    alpha_engine: AlphaEngine,
    risk_model: MultiFactorRiskModel,
    optimizer: OptimizerCore,
    error_engine: ErrorLearningEngine,
) -> PathABacktestResult:
    # 1) 載入資料
    # 2) 準備特徵 (PathAFeatureFrame)
    # 3) 迴圈走過每一個 rebalancing date:
    #       a. 用歷史窗口訓練 / 更新 Risk Model
    #       b. 用 AlphaEngine 算當日 composite_alpha
    #       c. 用 Optimizer 產生新權重 w_t
    #       d. 模擬未來一段期間的報酬
    #       e. 比較預測 vs 實際，產生 ErrorEvent
    # 4) 收集所有 NAV / trades / errors
    # 5) 回傳 PathABacktestResult
```

**v1 的要求：先有函式骨架與資料結構，邏輯可以先放 TODO。**

---

## 8. Error Bridge 標準

`path_a_error_bridge.py` 應建立：

### `build_error_event_from_prediction(...)`：

**Input:**
- 當日預測（signal / composite_alpha）
- 實際報酬（ex-post return）
- 當下市場狀態 / 因子暴露

**Output:**
- `ErrorEvent`

由 Path A Backtest 在「每一次預測結束後」呼叫：

將所有 error events 丟給 ErrorLearningEngine 的：
- `analyze_error()` 或 `process_error_event()`

---

## 9. 非目標（Non-goals v1）

Path A v1 刻意不做：

- 盤中 Tick / Orderbook 級別模擬
- RL Reward & Memory Engine
- 複雜交易成本模型 / TCA
- 真實券商 API 下單

這些屬於 Genesis 15 Steps 後段，未來再考慮。

---

## 10. 實作優先順序（Path A v1）

1. 建立：
   - `path_a_config.py`
   - `path_a_schema.py`
   - `path_a_backtest.py`
   - `path_a_error_bridge.py`（骨架）

2. 定義 FinMind 欄位需求（只寫型別與欄位名，不實作 API）

3. 寫測試：
   - `tests/path_a/test_path_a_schema.py`
   - `tests/path_a/test_path_a_backtest_skeleton.py`

4. 第一次整合：
   - 使用「假資料 DataFrame」跑完整 Backtest 流程
   - 確認 ErrorEvent 能被 ErrorLearningEngine 接收
   - 之後才接 FinMind 實際資料

---

*本標準文件 v1.0 定義了 Path A Validation Lab 的基本架構與資料流程。後續版本將根據實作經驗逐步擴充。*

