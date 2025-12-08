# J-GOD Policy Loop v2 — 設計規格

## 📋 概述

Policy Loop v2 在 v1 基礎上，實現了「自動實驗 + 自動產生建議 RiskConfig + 自動驗證」的一鍵腳本，大幅簡化了 Policy Loop 的使用流程。

### v1 → v2 主要差異

| 項目 | v1 | v2 |
|------|----|----|
| **實驗配置** | 硬編碼在腳本中 | YAML/JSON 配置檔 |
| **批次執行** | 需要手動執行多個腳本 | 一鍵自動完成 |
| **流程** | 分步驟執行 | 自動化完整閉環 |
| **驗證** | 手動驗證 | 自動驗證（Final Backtest） |

---

## 🏗️ 架構設計

### 核心組件

1. **實驗配置檔** (`config/path_a_experiments_v1.yaml`)
   - 定義要執行的實驗組合
   - 包含日期範圍、資金、風險參數等

2. **批次實驗腳本** (`scripts/run_path_a_batch_v1.py` v2)
   - 支援從配置檔讀取實驗參數
   - 支援實驗標籤（tag）

3. **Policy Loop v2 腳本** (`scripts/run_policy_loop_v2.py`)
   - 一鍵完成：實驗 → 分析 → 建議 → 驗證

---

## 📄 配置檔格式

### 檔案位置

`config/path_a_experiments_v1.yaml` 或 `config/path_a_experiments_v1.json`

### YAML 格式

```yaml
start_date: "2024-01-01"
end_date: "2024-12-31"
capital: 1000000
experiments:
  - name: "exp_lb50_sb10"
    long_budget: 0.5
    short_budget: 0.10
    max_weight_per_symbol: 0.10
    min_score: 0.0
    allow_short: true
  - name: "exp_lb60_sb15"
    long_budget: 0.6
    short_budget: 0.15
    max_weight_per_symbol: 0.10
    min_score: 0.0
    allow_short: true
  - name: "exp_lb70_sb15"
    long_budget: 0.7
    short_budget: 0.15
    max_weight_per_symbol: 0.10
    min_score: 0.0
    allow_short: true
  - name: "exp_lb80_sb20"
    long_budget: 0.8
    short_budget: 0.20
    max_weight_per_symbol: 0.10
    min_score: 0.0
    allow_short: true
```

### JSON 格式（替代方案）

```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "capital": 1000000,
  "experiments": [
    {
      "name": "exp_lb50_sb10",
      "long_budget": 0.5,
      "short_budget": 0.10,
      "max_weight_per_symbol": 0.10,
      "min_score": 0.0,
      "allow_short": true
    },
    ...
  ]
}
```

### 欄位說明

**頂層欄位**:
- `start_date` (str): 回測開始日期 (YYYY-MM-DD)
- `end_date` (str): 回測結束日期 (YYYY-MM-DD)
- `capital` (float): 初始資金
- `experiments` (list): 實驗組合清單

**實驗項目欄位**:
- `name` (str): 實驗名稱（用於識別）
- `long_budget` (float): Long 部位預算 (0.0-1.0)
- `short_budget` (float): Short 部位預算 (0.0-1.0)
- `max_weight_per_symbol` (float): 單檔最大權重 (0.0-1.0)
- `min_score` (float): 最低分數門檻
- `allow_short` (bool): 是否允許放空

---

## 🔧 腳本使用說明

### 1. 批次實驗腳本 v2

**檔案**: `scripts/run_path_a_batch_v1.py`

**新增參數**:
- `--config-file`: 實驗配置檔路徑（預設: `config/path_a_experiments_v1.yaml`）
- `--tag`: 實驗標籤（可選，用於標記這一批實驗）

**使用範例**:
```bash
# 使用預設配置檔
PYTHONPATH=. python scripts/run_path_a_batch_v1.py

# 指定配置檔和標籤
PYTHONPATH=. python scripts/run_path_a_batch_v1.py \
  --config-file config/path_a_experiments_v1.yaml \
  --tag "policy_v2_round1"
```

**輸出**:
- 每個實驗的核心績效摘要
- 最終總結
- 所有結果寫入 `data/path_a_backtest_logs.jsonl`

---

### 2. Policy Loop v2 一鍵腳本

**檔案**: `scripts/run_policy_loop_v2.py`

**功能**: 一鍵完成完整 Policy Loop

**執行流程**:
1. 讀取實驗配置檔
2. 執行批次回測（所有實驗組合）
3. 使用 Policy Log Reader 找出最佳實驗
4. 使用 Policy Writer 產生建議 RiskConfig
5. 使用建議配置執行 Final Backtest 驗證
6. 輸出完整摘要報告

**CLI 參數**:
- `--config-file` (預設: `config/path_a_experiments_v1.yaml`): 實驗配置檔
- `--log-path` (預設: `data/path_a_backtest_logs.jsonl`): 回測日誌檔案
- `--output-dir` (預設: `policy`): 輸出目錄
- `--file-name` (預設: `risk_config_suggested_auto_v2.yaml`): 建議配置檔名
- `--min-days` (預設: 60): 最小交易日數
- `--min-trades` (預設: 10): 最小交易次數
- `--sharpe-weight` (預設: 0.7): Sharpe 權重
- `--maxdd-weight` (預設: 0.3): Max Drawdown 權重
- `--final-backtest-start` (可選): Final Backtest 開始日期
- `--final-backtest-end` (可選): Final Backtest 結束日期

**使用範例**:

**範例 1（全部預設）**:
```bash
PYTHONPATH=. python scripts/run_policy_loop_v2.py
```

**範例 2（自訂實驗配置檔＋權重）**:
```bash
PYTHONPATH=. python scripts/run_policy_loop_v2.py \
  --config-file config/path_a_experiments_v1.yaml \
  --sharpe-weight 0.8 \
  --maxdd-weight 0.2 \
  --output-dir policy \
  --file-name risk_config_suggested_policy_v2_round1.yaml
```

**範例 3（自訂 Final Backtest 日期範圍）**:
```bash
PYTHONPATH=. python scripts/run_policy_loop_v2.py \
  --config-file config/path_a_experiments_v1.yaml \
  --final-backtest-start 2024-07-01 \
  --final-backtest-end 2024-12-31
```

**輸出格式**:
- 區塊 1: Policy Loop v2 設定摘要
- 區塊 2: 本次實驗總覽
- 區塊 3: 最佳實驗摘要
- 區塊 4: 產生的 YAML 檔案路徑
- 區塊 5: Final Backtest 結果

---

## 📊 工作流程

```
┌─────────────────────────────────────────────────────────┐
│            J-GOD Policy Loop v2 完整流程                │
└─────────────────────────────────────────────────────────┘

1. 讀取配置檔 (config/path_a_experiments_v1.yaml)
   └─> 解析實驗組合清單

2. 批次執行回測
   └─> 對每個實驗組合執行 Path A Backtest
       └─> 寫入 JSONL Logs

3. Policy 分析
   └─> Policy Log Reader 分析所有實驗
       └─> Policy Writer 選出最佳實驗
           └─> 產生建議 RiskConfig YAML

4. Final Backtest 驗證
   └─> 使用建議配置執行最終回測
       └─> 確認建議配置的實際表現

5. 輸出摘要報告
   └─> Terminal 顯示完整結果
       └─> 建議配置已寫入 YAML 檔
```

---

## 🔍 技術細節

### YAML Parser

使用簡單的 YAML parser（不依賴 PyYAML），支援：
- 基本鍵值對
- 列表
- 嵌套結構（dict + list）

或使用標準 JSON 格式（更簡單可靠）。

### 向後兼容

- 不破壞現有功能
- 所有現有腳本繼續可用
- Log 格式保持不變
- API 介面保持不變

---

## 📝 開發注意事項

### 不修改的模組

- `PathAEngineV1` - 保持不變
- `PolicyLogReaderV1` - 保持不變
- `PolicyWriterV1` - 保持不變
- Log Writer 格式 - 保持 JSONL 格式

### 允許的變更

- 內部重構 `run_path_a_batch_v1.py`（不影響 CLI 介面）
- 新增配置檔解析功能
- 新增 Policy Loop v2 腳本

### 錯誤處理

所有腳本應檢查：
- 配置檔是否存在
- 配置檔格式是否正確
- Log 檔是否存在（若需要讀取）
- 必要的欄位是否存在

---

## 🚀 未來擴展

### v3 可能的方向

1. **並行執行**: 多個實驗同時執行
2. **自動參數搜尋**: 使用 Grid Search 或 Bayesian Optimization
3. **多目標優化**: 不只考慮 Sharpe 和 MaxDD
4. **版本管理**: 建議配置的版本控制
5. **A/B 測試**: 比較不同配置的表現

---

## 📚 相關文件

- `docs/JGOD_POLICY_LOOP_V1.md` - Policy Loop v1 架構
- `docs/JGOD_POLICY_LOOP_V1_FINAL_SUMMARY.md` - Policy Loop v1 總結
- `docs/JGOD_POLICY_SERVICE_V1_COMPLETION_REPORT.md` - Policy Service v1 完成報告

---

**版本**: Policy Loop v2.0  
**完成日期**: 2024-12  
**狀態**: ✅ 開發中

