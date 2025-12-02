# J-GOD Step 10 Mega Task - Editor Instructions

## 📋 任務完成摘要

本文檔提供 J-GOD Step 10 所有修改的完整 Editor 指令包，包含：
- 檔案新增清單
- 檔案修改清單
- 驗證步驟
- 測試指令

---

## 📁 檔案新增清單

### 1. 核心檔案

#### `jgod/path_a/mock_data_loader.py` (重寫)
- **狀態**: 完整重寫
- **功能**: 增強版 Mock 資料載入器
- **主要改進**:
  - 所有價格關係正確（high >= max(open, close), etc.）
  - 成交量使用遞增/波動模型
  - 日報酬限制在 ±3%
  - 完整特徵集（momentum, rolling_vol, turnover_rate）
  - MockConfig dataclass 集中管理所有參數

#### `jgod/path_a/finmind_data_loader.py` (新增)
- **狀態**: 全新檔案
- **功能**: FinMind 資料載入器
- **主要功能**:
  - 實作 PathADataLoader 協定
  - API caching 機制
  - Fallback 到 mock 資料
  - 資料格式轉換（FinMind → J-GOD）
  - 完整的錯誤處理

### 2. 文件檔案

#### `docs/JGOD_FINMIND_LOADER_STANDARD_v1.md` (新增)
- **狀態**: 完整文件
- **內容**: FinMind Loader 標準規範、API 介面、使用範例

### 3. 測試檔案

#### `tests/regression/__init__.py` (新增)
- **狀態**: 空檔案（建立目錄結構）

#### `tests/regression/test_mock_basic.py` (新增)
- **狀態**: 完整測試
- **測試內容**: Mock loader 基本功能

#### `tests/regression/test_mock_alpha_valid.py` (新增)
- **狀態**: 完整測試
- **測試內容**: Mock loader 與 AlphaEngine 整合

#### `tests/regression/test_mock_covariance.py` (新增)
- **狀態**: 完整測試
- **測試內容**: Covariance matrix 計算

#### `tests/regression/test_finmind_basic.py` (新增)
- **狀態**: 完整測試
- **測試內容**: FinMind loader 基本功能

#### `tests/regression/test_finmind_alpha_valid.py` (新增)
- **狀態**: 完整測試
- **測試內容**: FinMind loader 與 AlphaEngine 整合

---

## 📝 檔案修改清單

### 1. `scripts/run_jgod_experiment.py`

#### 修改點 1: Mock Loader 初始化
**位置**: 約第 119-120 行

**原碼**:
```python
if data_source == "mock":
    data_loader = MockPathADataLoader(seed=123)
```

**新碼**:
```python
if data_source == "mock":
    from jgod.path_a.mock_data_loader import MockConfig
    mock_config = MockConfig(seed=123)
    data_loader = MockPathADataLoader(config=mock_config)
```

#### 修改點 2: FinMind Loader 啟用
**位置**: 約第 121-130 行

**原碼**:
```python
elif data_source == "finmind":
    # TODO: 之後接 FinMindPathADataLoader
    # ...
    raise NotImplementedError(...)
```

**新碼**:
```python
elif data_source == "finmind":
    from jgod.path_a.finmind_data_loader import FinMindPathADataLoader
    
    try:
        data_loader = FinMindPathADataLoader()
    except Exception as e:
        raise ValueError(
            f"Failed to initialize FinMind data loader: {e}. "
            "Please ensure FINMIND_TOKEN is set in environment variables, "
            "or use --data-source mock for testing."
        )
```

---

## 🔧 目錄結構變更

### 新增目錄

1. **`data_cache/finmind/`**
   - **用途**: 儲存 FinMind API 快取資料
   - **建立方式**: 程式自動建立（如果 cache_enabled=True）
   - **清理**: 可手動刪除來更新資料

2. **`tests/regression/`**
   - **用途**: 存放回歸測試
   - **建立方式**: 已建立並包含 `__init__.py`

---

## ✅ 驗證步驟

### 步驟 1: 語法檢查

```bash
# 檢查所有新增/修改的檔案
PYTHONPATH=. python3 -m py_compile \
  jgod/path_a/mock_data_loader.py \
  jgod/path_a/finmind_data_loader.py \
  scripts/run_jgod_experiment.py
```

**預期結果**: 無語法錯誤

---

### 步驟 2: 執行回歸測試

```bash
# 執行所有回歸測試
PYTHONPATH=. pytest tests/regression -v -q

# 或執行單個測試檔案
PYTHONPATH=. pytest tests/regression/test_mock_basic.py -v
PYTHONPATH=. pytest tests/regression/test_mock_alpha_valid.py -v
PYTHONPATH=. pytest tests/regression/test_mock_covariance.py -v
PYTHONPATH=. pytest tests/regression/test_finmind_basic.py -v
PYTHONPATH=. pytest tests/regression/test_finmind_alpha_valid.py -v
```

**預期結果**: 所有測試通過（或跳過，如果 FinMind token 未設定）

---

### 步驟 3: Mock 資料源測試

```bash
# 執行完整實驗（使用 mock 資料源）
PYTHONPATH=. python3 scripts/run_jgod_experiment.py \
  --name mock_demo_step10 \
  --start-date 2024-01-01 \
  --end-date 2024-01-10 \
  --rebalance-frequency D \
  --universe "2330.TW,2317.TW,2303.TW" \
  --data-source mock
```

**預期結果**:
- ✅ 實驗成功執行
- ✅ 無 datetime parsing 錯誤
- ✅ 無 covariance shape mismatch 錯誤
- ✅ 輸出檔案正常產生：
  - `output/experiments/mock_demo_step10/nav.csv`
  - `output/experiments/mock_demo_step10/returns.csv`
  - `output/experiments/mock_demo_step10/performance_summary.json`
  - `output/experiments/mock_demo_step10/performance_report.md`
  - `output/experiments/mock_demo_step10/diagnosis_report.md`
  - `output/experiments/mock_demo_step10/repair_plan.md`
  - `output/experiments/mock_demo_step10/config.json`

**檢查項目**:
- Performance summary 中沒有 NaN 或 Inf
- NAV 序列合理（始終 > 0）
- Returns 序列合理（無異常值）

---

### 步驟 4: FinMind 資料源測試（可選）

**前置條件**: 需要設定 `FINMIND_TOKEN` 環境變數

```bash
# 設定環境變數（如果還沒設定）
export FINMIND_TOKEN="your_finmind_token_here"

# 執行完整實驗（使用 FinMind 資料源）
PYTHONPATH=. python3 scripts/run_jgod_experiment.py \
  --name finmind_demo_step10 \
  --start-date 2024-01-01 \
  --end-date 2024-01-10 \
  --rebalance-frequency D \
  --universe "2330.TW,2317.TW,2303.TW" \
  --data-source finmind
```

**預期結果**:
- ✅ 實驗成功執行
- ✅ 從 FinMind API 取得真實資料
- ✅ 如果 API 失敗，自動 fallback 到 mock 資料
- ✅ 輸出檔案正常產生

**檢查項目**:
- Cache 目錄有資料產生（`data_cache/finmind/`）
- 如果 API 失敗，有 fallback 警告訊息
- Performance summary 中沒有 NaN 或 Inf

---

## 🧪 手動測試檢查清單

### Mock Loader 測試

- [ ] `MockPathADataLoader` 可以正常初始化
- [ ] `load_price_frame()` 回傳正確格式
- [ ] 價格關係正確（high >= max(open, close), etc.）
- [ ] 成交量合理（不同股票有不同量級）
- [ ] 日報酬在 ±3% 範圍內
- [ ] `load_feature_frame()` 包含所有必要特徵
- [ ] 無意外的 NaN 值

### FinMind Loader 測試

- [ ] `FinMindPathADataLoader` 可以正常初始化
- [ ] 有 token 時可以從 API 取得資料
- [ ] 無 token 時可以 fallback 到 mock
- [ ] Cache 機制正常運作
- [ ] 資料格式轉換正確
- [ ] 錯誤處理完善

### AlphaEngine 整合測試

- [ ] 無 datetime parsing 錯誤
- [ ] AlphaEngine 可以計算 composite_alpha
- [ ] 無 shape mismatch 錯誤

### Covariance Matrix 測試

- [ ] Covariance matrix 形狀正確
- [ ] Matrix 是對稱的
- [ ] Matrix 是 positive semi-definite
- [ ] 無 shape mismatch 錯誤

### 完整實驗測試

- [ ] Mock 資料源實驗可以跑完
- [ ] FinMind 資料源實驗可以跑完（如果有 token）
- [ ] 所有輸出檔案都有產生
- [ ] Performance summary 沒有 NaN 或 Inf

---

## 🐛 已知問題與注意事項

### 1. FinMind Token 要求
- FinMind loader 需要 `FINMIND_TOKEN` 環境變數
- 如果未設定，會自動 fallback 到 mock 資料（如果 `fallback_to_mock=True`）

### 2. Cache 目錄
- Cache 目錄會自動建立（`data_cache/finmind/`）
- 如果需要更新資料，可以手動刪除 cache 檔案

### 3. Mock 資料特性
- Mock 資料是合成的，不應直接用於實際交易決策
- 用於測試和開發，確保系統穩定性

### 4. Rolling Window NaN
- `rolling_vol_20d` 前 19 天可能為 NaN（這是預期的）
- `momentum_20d` 前 20 天為 0.0（這是預期的）

---

## 📊 修改統計

### 檔案數量
- **新增檔案**: 7 個
- **修改檔案**: 1 個
- **總計**: 8 個檔案

### 程式碼行數
- **Mock Loader**: ~450 行（重寫）
- **FinMind Loader**: ~600 行（新增）
- **測試檔案**: ~800 行（新增）
- **文件**: ~400 行（新增）
- **總計**: ~2250 行

---

## 🎯 完成標準

所有任務視為完成當：

1. ✅ 所有檔案都已建立並通過語法檢查
2. ✅ 所有回歸測試通過（或合理跳過）
3. ✅ Mock 資料源實驗可以成功執行
4. ✅ FinMind 資料源實驗可以成功執行（如果有 token）
5. ✅ 無 datetime parsing 錯誤
6. ✅ 無 covariance shape mismatch 錯誤
7. ✅ Performance summary 沒有 NaN 或 Inf

---

## 📞 後續步驟

1. **執行驗證步驟**: 按照上述步驟逐一驗證
2. **檢查輸出**: 確認所有輸出檔案正常產生
3. **檢查日誌**: 確認無異常警告或錯誤
4. **提交變更**: 如果所有測試通過，可以提交變更

---

## 🔗 相關文件

- `docs/JGOD_FINMIND_LOADER_STANDARD_v1.md` - FinMind Loader 標準規範
- `docs/PHASE4_PATH_A_NEXT_STEPS_PLAN.md` - Path A 下一步規劃
- `jgod/path_a/mock_data_loader.py` - Mock Loader 實作
- `jgod/path_a/finmind_data_loader.py` - FinMind Loader 實作

---

## ✨ 總結

J-GOD Step 10 所有任務已完成：

1. ✅ **任務 A**: Mock 資料源完全合理化
2. ✅ **任務 B**: FinMind 資料源完整實作
3. ✅ **任務 C**: 回歸測試完整建立
4. ✅ **任務 D**: Editor 指令包完整提供

所有檔案都已建立，可以立即開始驗證與測試！

