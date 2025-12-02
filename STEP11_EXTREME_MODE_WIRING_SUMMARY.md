# J-GOD Step 11：EXTREME MODE Switch & Wiring - 完成報告

## ✅ 所有任務已完成

### 任務 1：CLI 加上 --mode 參數 ✅
**檔案**: `scripts/run_jgod_experiment.py`

**修改內容**:
- ✅ 在 `parse_args()` 中新增 `--mode` 參數
  - 類型: str
  - choices: ["basic", "extreme"]
  - 預設值: "basic"
  - help: 說明 basic/extreme 差異
- ✅ 在 `main()` 中輸出 Mode 資訊
  - `print(f"Mode: {args.mode}")`
- ✅ 將 mode 傳遞給 `build_orchestrator()`

### 任務 2：build_orchestrator 接上 Extreme 模組 ✅
**檔案**: `scripts/run_jgod_experiment.py`

**修改內容**:
- ✅ 修改函式簽名：`build_orchestrator(data_source: str = "mock", mode: str = "basic")`
- ✅ 新增 Extreme 模組的 import（條件式導入）
- ✅ 根據 mode 選擇 DataLoader:
  - `mode="basic"`: MockPathADataLoader / FinMindPathADataLoader
  - `mode="extreme"`: MockPathADataLoaderExtreme / FinMindPathADataLoaderExtreme
- ✅ 根據 mode 選擇 Alpha Engine:
  - `mode="basic"`: AlphaEngine
  - `mode="extreme"`: AlphaEngineExtreme
- ✅ 根據 mode 選擇 Risk Model:
  - `mode="basic"`: MultiFactorRiskModel
  - `mode="extreme"`: MultiFactorRiskModelExtreme
- ✅ 根據 mode 選擇 Execution Engine:
  - `mode="basic"`: ExecutionEngine
  - `mode="extreme"`: ExecutionEngineExtreme

### 任務 3：Extreme Smoke Test ✅
**檔案**: `tests/experiments/test_experiment_extreme_smoke.py`

**測試內容**:
- ✅ 使用 `data_source="mock"` + `mode="extreme"`
- ✅ 短日期區間（2024-01-01 ~ 2024-01-10）
- ✅ 小 universe（2 檔股票）
- ✅ 斷言：
  - result 不為 None
  - result.report.summary 包含 total_return / sharpe
  - 不丟出 Exception

## 📋 修改檔案清單

1. **scripts/run_jgod_experiment.py**
   - 新增 `--mode` CLI 參數
   - 修改 `build_orchestrator()` 支援 mode 參數
   - 條件式導入 Extreme 模組
   - 根據 mode 選擇對應模組

2. **tests/experiments/test_experiment_extreme_smoke.py** (NEW)
   - 新增 smoke test 檔案

## 🎯 測試指令

### 1. 語法檢查
```bash
PYTHONPATH=. python3 -m py_compile scripts/run_jgod_experiment.py
PYTHONPATH=. python3 -m py_compile tests/experiments/test_experiment_extreme_smoke.py
```

### 2. Smoke Test
```bash
PYTHONPATH=. pytest tests/experiments/test_experiment_extreme_smoke.py -q -v
```

### 3. Basic 模式測試（確保不破壞現有功能）
```bash
PYTHONPATH=. python3 scripts/run_jgod_experiment.py \
  --name mock_demo_v2 \
  --start-date 2024-01-01 \
  --end-date 2024-01-10 \
  --rebalance-frequency D \
  --universe "2330.TW,2317.TW,2303.TW" \
  --data-source mock \
  --mode basic
```

### 4. Extreme 模式測試
```bash
PYTHONPATH=. python3 scripts/run_jgod_experiment.py \
  --name mock_extreme_demo \
  --start-date 2024-01-01 \
  --end-date 2024-01-10 \
  --rebalance-frequency D \
  --universe "2330.TW,2317.TW" \
  --data-source mock \
  --mode extreme
```

## ✨ 完成狀態

- ✅ 任務 1：CLI 參數
- ✅ 任務 2：Extreme 模組整合
- ✅ 任務 3：Smoke Test

所有任務已完成，可以開始測試！
