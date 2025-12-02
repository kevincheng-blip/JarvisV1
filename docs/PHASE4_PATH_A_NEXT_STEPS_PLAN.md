# Phase 4: Path A v1 下一步實戰化規劃

## 📋 概述

本文檔規劃 J-GOD Path A v1 Mock Pipeline 完成後的下一步實戰化任務，包含三個主要方向：
1. **Mock 線的「合理化版本」** - 讓 mock 資料參數更合理
2. **FinMind data_source="finmind" 的版本規劃** - 整合真實資料源
3. **最小回歸測試（Regression Test）規劃** - 確保系統穩定性

---

## 1️⃣ Mock 線的「合理化版本」

### 📌 目標
在不破壞目前 mock_flow 的前提下，設計一組「比較合理的參數與安全檢查」，避免出現誇張到離譜的 Sharpe / CAGR。

### 📊 現況分析

**當前 Mock 資料特性（`MockPathADataLoader`）：**
- 每日收益率：`rng.normal(loc=0.0005, scale=0.01)` → 均值 0.05%，標準差 1%
- 價格隨機遊走，無限制單日漲跌幅
- 交易成本：`transaction_cost_bps = 5.0` (0.05%)
- 權重限制：`max_weight_per_symbol = 0.1` (10%)
- OptimizerConfig：`max_weight = 0.05` (5%)，`long_only = True`

**問題點：**
1. 單日收益率可能過大（1% 標準差可能產生 ±3% 以上的極端值）
2. 累積效應導致 NAV 增長過快或過慢
3. 交易成本計算過於簡化
4. 缺乏 NAV / weights 的安全檢查

### 🎯 修改方案

#### **A. 調整 MockPathADataLoader 參數**

**檔案：`jgod/path_a/mock_data_loader.py`**

**修改項目：**

1. **限制單日最大漲跌幅**
   - 加入 `max_daily_return` 參數（例如：0.07 = 7%，對應台股漲跌停板）
   - 在 `load_price_frame()` 中，限制 `daily_returns` 的範圍

2. **降低收益率波動**
   - 將 `scale=0.01` 改為 `scale=0.005` (0.5%)
   - 或使用更保守的分佈（例如：Beta 分佈）

3. **加入均值回歸特性**
   - 引入輕微的均值回歸，避免價格無限上漲/下跌
   - 可以使用 AR(1) 模型：`returns[t] = alpha * returns[t-1] + epsilon`

4. **控制初始價格範圍**
   - 確保不同股票的價格差距不會太誇張
   - 例如：所有股票在 50-500 範圍內

**預期效果：**
- 單日收益率控制在合理範圍（-7% ~ +7%）
- 累積收益率更穩定（年化 Sharpe 約 0.5-2.0）
- NAV 增長曲線更平滑

---

#### **B. 增強交易成本計算**

**檔案：`jgod/path_a/path_a_backtest.py`**

**修改項目：**

1. **改善交易成本計算邏輯（第 356-359 行）**
   - 當前：`cost = turnover * (config.transaction_cost_bps / 1e4)`
   - 改為：考慮雙向成本（買入 + 賣出）
   - 加入最小交易成本（例如：每筆交易至少 20 元）

2. **使用 ExecutionEngine 的 CostModel**
   - 目前已有 `DefaultCostModel`（在 `build_orchestrator()` 中建立）
   - 但 Path A Backtest 中未使用，仍用簡化版 `transaction_cost_bps`
   - 建議：在 Path A Backtest 中加入 `ExecutionEngine` 的實際成本計算

**預期效果：**
- 交易成本更貼近真實情況
- 高頻調倉會受到明顯成本懲罰

---

#### **C. 加入 NAV / Weights 安全檢查**

**檔案：`jgod/path_a/path_a_backtest.py`**

**修改項目：**

1. **在 NAV 計算後加入檢查（約第 360 行附近）**
   - 確保 `current_nav > 0`
   - 如果 NAV 過低，觸發警告或停止回測
   - 檢查 NAV 增長率是否異常（例如：單日 > 50%）

2. **在權重正規化後加入檢查（約第 318 行附近）**
   - 確保權重總和 ≈ 1.0（允許小誤差，例如 ±0.01）
   - 確保沒有負權重（如果是 long-only）
   - 確保單一股票權重不超過限制

3. **在 OptimizerConfig 中調整參數**
   - 檔案：`scripts/run_jgod_experiment.py` (第 163 行)
   - 確保 `max_weight` 與 `PathAConfig.max_weight_per_symbol` 一致

**預期效果：**
- 避免 NAV 或 weights 出現荒謬數值
- 提前發現異常情況並記錄警告

---

#### **D. 調整 OptimizerConfig 參數**

**檔案：`scripts/run_jgod_experiment.py`**

**修改項目：**

1. **設定更保守的權重限制**
   ```python
   optimizer = OptimizerCore(
       config=OptimizerConfig(
           weight_constraints=WeightConstraints(
               long_only=True,
               min_weight=0.0,
               max_weight=0.10,  # 10% 上限（對齊 PathAConfig）
           ),
           tracking_error=TrackingErrorConstraint(
               enabled=False,  # Mock 模式下可先關閉 TE 限制
           ),
       )
   )
   ```

**預期效果：**
- 避免單一股票權重過大
- 與 PathAConfig 的設定一致

---

### 📝 Editor 指令包（Mock 合理化版本）

```
任務：優化 Mock 資料產生參數，讓回測結果更合理

檔案 1: jgod/path_a/mock_data_loader.py
修改點 1.1: 在 `MockPathADataLoader` 類別中新增參數
- 新增 `max_daily_return: float = 0.07` 欄位（對應漲跌停板）
- 新增 `volatility_scale: float = 0.005` 欄位（降低波動）

修改點 1.2: 在 `load_price_frame()` 方法中（約第 76 行）
- 將 `scale=0.01` 改為 `scale=self.volatility_scale`
- 在計算 `daily_returns` 後，加入 clipping：`np.clip(daily_returns, -self.max_daily_return, self.max_daily_return)`

修改點 1.3: 控制初始價格範圍（約第 70 行）
- 將 `base_prices` 計算改為：`{symbol: float(50 + 450 * i / (len(symbols) - 1)) for i, symbol in enumerate(symbols)}`
- 確保價格在 50-500 範圍內

---

檔案 2: jgod/path_a/path_a_backtest.py
修改點 2.1: 改善交易成本計算（約第 356-359 行）
- 將簡化版改為：
  ```python
  turnover = (new_weights - current_weights).abs().sum()
  # 雙向成本（買入 + 賣出）
  cost = turnover * (config.transaction_cost_bps / 1e4) * 2
  # 加入最小交易成本檢查
  min_cost = len(config.universe) * 0.0002  # 每檔至少 0.02% 成本
  cost = max(cost, min_cost)
  current_nav *= (1.0 - cost)
  ```

修改點 2.2: 加入 NAV 安全檢查（約第 360 行後）
- 在 `nav_series.at[current_date] = current_nav` 後加入：
  ```python
  # 檢查 NAV 合理性
  if current_nav <= 0:
      print(f"Warning: NAV became non-positive on {current_date}. Stopping backtest.")
      break
  if i > 0:
      daily_change = (current_nav / nav_series.iloc[i-1]) - 1.0
      if abs(daily_change) > 0.5:  # 單日變化超過 50%
          print(f"Warning: Extreme NAV change on {current_date}: {daily_change:.2%}")
  ```

修改點 2.3: 加入權重安全檢查（約第 318 行後）
- 在 `new_weights = new_weights / new_weights.abs().sum()` 後加入：
  ```python
  # 檢查權重合理性
  weight_sum = new_weights.sum()
  if abs(weight_sum - 1.0) > 0.01:
      print(f"Warning: Weights do not sum to 1.0 on {current_date}: sum={weight_sum:.4f}")
      new_weights = new_weights / weight_sum  # 重新正規化
  if config.allow_short == False:
      if (new_weights < 0).any():
          print(f"Warning: Negative weights detected in long-only mode. Clipping to 0.")
          new_weights = new_weights.clip(lower=0.0)
          new_weights = new_weights / new_weights.sum()  # 重新正規化
  ```

---

檔案 3: scripts/run_jgod_experiment.py
修改點 3.1: 調整 OptimizerConfig（約第 162-164 行）
- 將 `OptimizerCore(config=OptimizerConfig())` 改為：
  ```python
  optimizer = OptimizerCore(
      config=OptimizerConfig(
          weight_constraints=WeightConstraints(
              long_only=True,
              min_weight=0.0,
              max_weight=0.10,  # 10% 上限
          ),
          tracking_error=TrackingErrorConstraint(
              enabled=False,  # Mock 模式下先關閉
          ),
      )
  )
  ```
```

---

## 2️⃣ FinMind data_source="finmind" 的版本規劃

### 📌 目標
規劃並實作 `data_source="finmind"` 的整合方案，讓 Path A 可以使用真實的台股資料。

### 📊 現況分析

**當前狀態：**
- `build_orchestrator()` 中已有 `data_source == "finmind"` 的分支，但僅有 TODO 註解
- 系統中已有 `FinMindClient`（`api_clients/finmind_client.py`）
- 已有 `DataLoader`（`jgod/market/data_loader.py`），但非 `PathADataLoader` 介面

**需要實作的組件：**
1. `FinMindPathADataLoader` - 實作 `PathADataLoader` 協定
2. 資料格式轉換邏輯（FinMind → Path A 格式）
3. 錯誤處理與資料驗證

---

### 🎯 設計方案

#### **A. FinMindPathADataLoader 實作**

**新檔案：`jgod/path_a/finmind_data_loader.py`**

**主要功能：**

1. **實作 `PathADataLoader` 協定**
   - `load_price_frame()`: 從 FinMind 取得 OHLCV 資料，轉換為 MultiIndex DataFrame
   - `load_feature_frame()`: 計算 features（daily_return, rolling_vol 等）

2. **資料格式轉換**
   - FinMind 格式：`pd.DataFrame` with columns `['date', 'stock_id', 'open', 'high', 'low', 'close', 'volume']`
   - Path A 格式：
     - `price_frame`: `index=date`, `columns=MultiIndex(symbol, field)`
     - `feature_frame`: `index=MultiIndex(date, symbol)`, `columns=feature_names`

3. **錯誤處理**
   - 處理資料缺漏（停牌、資料缺失）
   - 處理交易日對齊問題
   - 處理權息調整（目前可先用原始價格，未來可擴充）

**資料流程：**
```
FinMind API
  ↓
FinMindClient.get_stock_daily()
  ↓
pd.DataFrame (date, stock_id, ohlcv)
  ↓
FinMindPathADataLoader.load_price_frame()
  ↓
price_frame: MultiIndex DataFrame (date × (symbol, field))
  ↓
FinMindPathADataLoader.load_feature_frame()
  ↓
feature_frame: MultiIndex DataFrame ((date, symbol) × features)
```

---

#### **B. 風險點與對策**

| 風險點 | 影響 | 對策 |
|--------|------|------|
| **資料缺漏** | 回測日期不連續、AlphaEngine 計算失敗 | 1. 在 `load_price_frame()` 中，使用 `pd.date_range` 生成完整交易日曆<br>2. 對缺失資料使用前一日價格 forward fill<br>3. 記錄缺失資料警告 |
| **停牌處理** | 無法取得該日資料 | 1. 停牌期間維持前一日價格<br>2. 在該日期將該股票權重置為 0（或在 Optimizer 中排除） |
| **權息調整** | 價格不連續，影響收益率計算 | 1. v1 版本先使用原始價格（未調整）<br>2. 在日誌中標註未來需加入權息調整<br>3. v2 可加入 `adjust_price()` helper |
| **交易日對齊** | 不同股票交易日可能不同 | 1. 使用 `pd.date_range` 生成統一交易日曆<br>2. 對齊所有股票的日期 index |
| **API 限制** | FinMind API 可能限流或失敗 | 1. 加入重試機制（最多 3 次）<br>2. 快取已取得的資料<br>3. 提供 fallback 到本地資料庫（如果有的話） |
| **資料品質** | 價格異常值、成交量為 0 | 1. 在 `load_price_frame()` 中加入資料驗證<br>2. 過濾異常值（例如：價格 < 0 或變化 > 20%）<br>3. 記錄資料品質警告 |

---

#### **C. 最小測試建議**

**測試 Universe：**
- 建議使用 **3-5 檔流動性高的股票**
- 例如：`2330.TW`（台積電）、`2317.TW`（鴻海）、`2454.TW`（聯發科）

**測試期間：**
- **短期測試**：`2024-01-01` 至 `2024-01-31`（1 個月）
- **中期測試**：`2024-01-01` 至 `2024-03-31`（1 季）
- **長期測試**：`2024-01-01` 至 `2024-12-31`（1 年）

**測試重點：**
1. 資料完整性（所有日期都有資料）
2. 格式正確性（MultiIndex 結構正確）
3. 與 Mock 版本的結果差異（預期會有不同，但流程應該一致）

---

### 📝 Editor 指令包（FinMind 整合 - 設計階段）

```
任務：設計 FinMindPathADataLoader 實作方案（先出設計，不直接寫 code）

請在 jgod/path_a/ 目錄下建立新檔案：finmind_data_loader.py

設計要點：

1. 類別結構：
   - 類別名稱：`FinMindPathADataLoader`
   - 繼承：實作 `PathADataLoader` 協定（Protocol）
   - 初始化參數：
     * `client: FinMindClient` (必需)
     * `cache_enabled: bool = True` (是否啟用快取)

2. 主要方法：

   a. `load_price_frame(config: PathAConfig) -> pd.DataFrame`:
      - 對每個 symbol，呼叫 `client.get_stock_daily(symbol, start_date, end_date)`
      - 轉換為 MultiIndex DataFrame：`index=date`, `columns=(symbol, field)`
      - 處理資料缺漏（forward fill）
      - 處理交易日對齊（統一交易日曆）
      - 回傳格式與 MockPathADataLoader 一致

   b. `load_feature_frame(config: PathAConfig) -> pd.DataFrame`:
      - 從 `load_price_frame()` 取得價格資料
      - 計算 features：daily_return_1d, rolling_vol_5d, close, volume, open, high, low
      - 回傳 MultiIndex DataFrame：`index=(date, symbol)`, `columns=feature_names`

3. 錯誤處理：
   - 如果某個 symbol 的資料完全無法取得，記錄警告並使用 NaN
   - 如果某日的資料缺漏，使用前一日價格 forward fill
   - 如果 API 呼叫失敗，重試 3 次後仍失敗則 raise Exception

4. 資料驗證：
   - 檢查價格 > 0
   - 檢查成交量 >= 0
   - 檢查單日價格變化不超過 20%（異常值過濾）

5. 相依模組：
   - 從 `api_clients.finmind_client import FinMindClient` 匯入
   - 從 `jgod.path_a.path_a_schema import PathAConfig` 匯入
   - 從 `jgod.path_a.path_a_backtest import PathADataLoader` 匯入

6. 未來擴充點：
   - 權息調整功能（v2）
   - 本地資料快取（v2）
   - 多資料源支援（v2）

---

修改 scripts/run_jgod_experiment.py：

在 build_orchestrator() 函式中（約第 121-130 行），將 TODO 改為實際實作：

```python
elif data_source == "finmind":
    from jgod.path_a.finmind_data_loader import FinMindPathADataLoader
    from api_clients.finmind_client import FinMindClient
    
    try:
        finmind_client = FinMindClient()
        data_loader = FinMindPathADataLoader(client=finmind_client)
    except ValueError as e:
        raise ValueError(
            f"Failed to initialize FinMind client: {e}. "
            "Please ensure FINMIND_TOKEN is set in environment variables."
        )
```

---

測試建議：

1. 建立測試腳本：tests/test_finmind_data_loader.py
   - 測試 load_price_frame() 格式
   - 測試 load_feature_frame() 格式
   - 測試資料缺漏處理
   - 測試錯誤處理

2. 執行最小回測：
   ```bash
   PYTHONPATH=. python3 scripts/run_jgod_experiment.py \
     --name finmind_test_2024Q1 \
     --start-date 2024-01-01 \
     --end-date 2024-01-31 \
     --rebalance-frequency D \
     --universe "2330.TW,2317.TW,2454.TW" \
     --data-source finmind
   ```
```

---

## 3️⃣ 最小回歸測試（Regression Test）規劃

### 📌 目標
針對 `mock_demo_v2` 指令，設計一個「最小回歸測試」，確認實驗可以跑完不崩潰、輸出檔案都有產生、並進行基本的 sanity check。

### 🎯 測試方案

#### **A. 測試結構**

**新檔案：`tests/test_path_a_mock_regression.py`**

**測試類別：**
1. **測試實驗執行**
   - 測試命令可以正常執行不崩潰
   - 測試執行時間在合理範圍內（例如：< 30 秒）

2. **測試輸出檔案**
   - 測試所有預期檔案都有產生
   - 測試檔案格式正確（CSV、JSON、Markdown）

3. **測試資料完整性**
   - 測試 NAV 序列長度正確
   - 測試 Returns 序列長度正確
   - 測試 Portfolio Snapshots 數量正確

4. **測試數值合理性（Sanity Check）**
   - NAV 始終 > 0
   - Returns 在合理範圍（例如：單日 < 50%）
   - Sharpe Ratio > 0（或至少不是 NaN）
   - 權重總和 ≈ 1.0

---

#### **B. 測試內容詳述**

**測試 1：實驗可以跑完不崩潰**
```python
def test_experiment_runs_without_error():
    """測試實驗可以正常執行，不出現 Exception"""
    # 執行 run_jgod_experiment.py 命令
    # 檢查 exit code == 0
    # 檢查沒有 unhandled exception
```

**測試 2：輸出檔案都存在**
```python
def test_output_files_exist():
    """測試所有預期檔案都有產生"""
    expected_files = [
        "nav.csv",
        "returns.csv",
        "performance_summary.json",
        "performance_report.md",
        "diagnosis_report.md",
        "repair_plan.md",
        "config.json",
    ]
    # 檢查每個檔案是否存在
```

**測試 3：NAV 序列合理性**
```python
def test_nav_series_sanity():
    """測試 NAV 序列的合理性"""
    # 1. NAV 長度 = 交易日數量
    # 2. NAV 始終 > 0
    # 3. NAV 單日變化 < 50%
    # 4. NAV 初始值 = config.initial_nav
```

**測試 4：Returns 序列合理性**
```python
def test_returns_series_sanity():
    """測試 Returns 序列的合理性"""
    # 1. Returns 長度 = NAV 長度 - 1
    # 2. Returns 在合理範圍（例如：-50% ~ +50%）
    # 3. Returns 沒有 NaN 或 Inf
```

**測試 5：Performance Summary 合理性**
```python
def test_performance_summary_sanity():
    """測試 Performance Summary 的合理性"""
    # 1. 所有必要欄位都存在（total_return, cagr, sharpe, max_drawdown）
    # 2. Sharpe Ratio 不是 NaN（可以是負數）
    # 3. Max Drawdown <= 0
    # 4. CAGR 在合理範圍（例如：-100% ~ +1000%，但 mock 可能較誇張）
```

**測試 6：Portfolio Snapshots 合理性**
```python
def test_portfolio_snapshots_sanity():
    """測試 Portfolio Snapshots 的合理性"""
    # 1. Snapshots 數量 = 交易日數量（或 rebalance 次數）
    # 2. 每個 snapshot 的權重總和 ≈ 1.0
    # 3. 每個 snapshot 的 NAV > 0
    # 4. 權重都在合理範圍（0.0 ~ max_weight）
```

---

#### **C. 測試執行方式**

**方式 1：使用 pytest**
```bash
pytest tests/test_path_a_mock_regression.py -v
```

**方式 2：使用 unittest**
```bash
python -m unittest tests.test_path_a_mock_regression
```

**方式 3：直接執行 Python 腳本**
```bash
python tests/test_path_a_mock_regression.py
```

---

### 📝 Editor 指令包（回歸測試）

```
任務：建立 Path A Mock Pipeline 的最小回歸測試

新檔案：tests/test_path_a_mock_regression.py

測試內容：

1. 匯入必要模組：
   ```python
   import unittest
   import subprocess
   import json
   import pandas as pd
   from pathlib import Path
   from jgod.experiments import ExperimentOrchestrator, ExperimentConfig
   from jgod.path_a.mock_data_loader import MockPathADataLoader
   ```

2. 定義測試類別：
   ```python
   class TestPathAMockRegression(unittest.TestCase):
       """Path A Mock Pipeline 回歸測試"""
       
       @classmethod
       def setUpClass(cls):
           """設定測試環境"""
           cls.test_name = "mock_demo_v2"
           cls.output_dir = Path(f"output/experiments/{cls.test_name}")
           cls.test_config = ExperimentConfig(
               name=cls.test_name,
               start_date="2024-01-01",
               end_date="2024-01-10",
               rebalance_frequency="D",
               universe=["2330.TW", "2317.TW", "2303.TW"],
               data_source="mock",
           )
       
       def setUp(self):
           """每個測試前執行"""
           # 清理舊的輸出目錄（可選）
           pass
   ```

3. 實作測試方法：

   a. `test_experiment_runs_without_error(self)`:
      - 建立 ExperimentOrchestrator
      - 執行 `orchestrator.run_experiment(self.test_config)`
      - 檢查沒有 Exception
      - 檢查 result 不為 None

   b. `test_output_files_exist(self)`:
      - 檢查 output_dir 存在
      - 檢查所有預期檔案都存在：
        * nav.csv
        * returns.csv
        * performance_summary.json
        * performance_report.md
        * diagnosis_report.md
        * repair_plan.md
        * config.json

   c. `test_nav_series_sanity(self)`:
      - 讀取 nav.csv
      - 檢查 NAV 長度 > 0
      - 檢查所有 NAV 值 > 0
      - 檢查 NAV 單日變化 < 0.5（50%）

   d. `test_returns_series_sanity(self)`:
      - 讀取 returns.csv
      - 檢查 Returns 長度 = NAV 長度 - 1（或相等，取決於實作）
      - 檢查 Returns 沒有 NaN
      - 檢查 Returns 在合理範圍（例如：-0.5 ~ 0.5）

   e. `test_performance_summary_sanity(self)`:
      - 讀取 performance_summary.json
      - 檢查必要欄位存在：total_return, cagr, sharpe, max_drawdown
      - 檢查 sharpe 不是 NaN（可以是負數）
      - 檢查 max_drawdown <= 0

   f. `test_portfolio_snapshots_sanity(self)`:
      - 從 result 取得 portfolio_snapshots
      - 檢查 snapshots 數量 > 0
      - 檢查每個 snapshot 的權重總和 ≈ 1.0（誤差 < 0.01）
      - 檢查每個 snapshot 的 NAV > 0

4. 執行測試：
   ```python
   if __name__ == "__main__":
       unittest.main()
   ```

---

測試執行建議：

1. 在專案根目錄執行：
   ```bash
   PYTHONPATH=. python -m pytest tests/test_path_a_mock_regression.py -v
   ```

2. 或直接執行：
   ```bash
   PYTHONPATH=. python tests/test_path_a_mock_regression.py
   ```

3. 預期結果：
   - 所有測試都通過
   - 測試執行時間 < 1 分鐘
```

---

## 📋 給 Editor 的實作任務清單（總覽）

### ✅ 任務 1：Mock 合理化版本

**檔案清單：**
1. `jgod/path_a/mock_data_loader.py` - 調整參數與限制
2. `jgod/path_a/path_a_backtest.py` - 改善成本計算與安全檢查
3. `scripts/run_jgod_experiment.py` - 調整 OptimizerConfig

**修改重點：**
- 限制單日最大漲跌幅（7%）
- 降低收益率波動（0.5%）
- 改善交易成本計算（雙向成本）
- 加入 NAV / weights 安全檢查

**預期效果：**
- Sharpe Ratio 在合理範圍（0.5-2.0）
- CAGR 不會過度誇張
- NAV 曲線更平滑

---

### 📋 任務 2：FinMind 整合（設計階段）

**檔案清單：**
1. `jgod/path_a/finmind_data_loader.py` - **新檔案**（設計階段，不直接實作）
2. `scripts/run_jgod_experiment.py` - 啟用 FinMind 分支

**設計重點：**
- 實作 `PathADataLoader` 協定
- 處理資料缺漏與交易日對齊
- 錯誤處理與資料驗證
- 未來擴充點（權息調整、快取）

**預期效果：**
- 可以使用真實 FinMind 資料執行回測
- 資料格式與 Mock 版本一致

---

### ✅ 任務 3：回歸測試

**檔案清單：**
1. `tests/test_path_a_mock_regression.py` - **新檔案**

**測試重點：**
- 實驗可以跑完不崩潰
- 所有輸出檔案都存在
- 資料完整性檢查
- 數值合理性檢查（Sanity Check）

**預期效果：**
- 確保系統穩定性
- 快速發現回歸問題

---

## 🎯 執行順序建議

1. **先完成任務 1（Mock 合理化）**
   - 這是最關鍵的，影響後續所有測試
   - 可以立即改善回測結果的合理性

2. **再完成任務 3（回歸測試）**
   - 建立測試基礎，確保任務 1 的修改不會破壞現有功能

3. **最後規劃任務 2（FinMind 整合）**
   - 這是較大的任務，需要更多設計與測試
   - 可以分階段實作（先實作基本功能，再擴充）

---

## 📝 注意事項

1. **向後相容性**
   - 所有修改都要確保不會破壞現有的 `mock_demo_v2` 指令
   - 如果必須改變行為，要加入版本控制或配置選項

2. **測試覆蓋**
   - 每個任務完成後都要執行回歸測試
   - 確保沒有引入新的 bug

3. **文檔更新**
   - 修改後要更新相關文檔
   - 特別是參數說明與使用範例

4. **逐步推進**
   - 不要一次改太多
   - 每個任務完成後要驗證效果
   - 可以分階段提交

---

## 🔗 相關文件

- `docs/PHASE4_MASTER_INDEX_STANDARD_v1.md` - Phase 4 主索引
- `jgod/path_a/path_a_schema.py` - Path A 資料結構定義
- `jgod/path_a/path_a_backtest.py` - Path A 回測核心邏輯
- `scripts/run_jgod_experiment.py` - 實驗執行腳本

