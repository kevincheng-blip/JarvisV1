# J-GOD War Room Policy Evolution Panel v1

## 📋 概述

Policy Evolution Panel v1 是 War Room 的一個新面板，用於觀察和比較不同 Policy Loop 回合的策略表現，追蹤 RiskConfig 的演進歷史。

### 目的

1. **策略進化追蹤**: 觀察不同實驗階段的策略表現變化
2. **版本比較**: 對比不同 RiskConfig 配置的 Sharpe、MaxDD、Return 等指標
3. **歷史分析**: 作為未來「策略白皮書」的圖表來源
4. **決策支援**: 幫助判斷哪個 RiskConfig 配置最適合當前市場

---

## 🔌 後端 API

### Base URL

所有 Policy Evolution API 的前綴：`/api/v1/policy`

### Endpoints

#### 1. GET `/api/v1/policy/experiments/history`

**功能**: 取得政策實驗歷史列表

**Query 參數**:
- `start_date` (可選): 篩選開始日期 (YYYY-MM-DD)
- `end_date` (可選): 篩選結束日期 (YYYY-MM-DD)
- `limit` (可選, 預設: 50): 返回筆數上限 (1-200)
- `order_by` (可選, 預設: "timestamp"): 排序方式 ("timestamp", "score", "sharpe")

**回應**: `List[PolicyExperimentHistoryItem]`

```json
[
  {
    "run_id": "abc123def456",
    "timestamp": "2024-12-01T10:00:00",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "score": 0.85,
    "sharpe_ratio": 1.33,
    "max_drawdown": 0.08,
    "total_return": 0.20,
    "win_rate": 0.55,
    "num_days": 252,
    "num_trades": 120,
    "long_budget": 0.6,
    "short_budget": 0.2,
    "max_weight_per_symbol": 0.1,
    "min_score": 0.0,
    "allow_short": true,
    "tag": "policy_v2_round1"
  },
  ...
]
```

**使用範例**:
```bash
curl "http://localhost:8000/api/v1/policy/experiments/history?start_date=2024-01-01&end_date=2024-12-31&limit=50&order_by=timestamp"
```

---

#### 2. GET `/api/v1/policy/risk-config/active`

**功能**: 取得當前生效的 RiskConfig

**Query 參數**:
- `file` (可選): RiskConfig 檔案路徑（預設: `policy/risk_config_suggested_v1.yaml`）

**回應**: `PolicyActiveConfig`

```json
{
  "file_path": "policy/risk_config_suggested_v1.yaml",
  "exists": true,
  "risk_version": 1,
  "run_id": "abc123def456",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "long_budget": 0.6,
  "short_budget": 0.2,
  "max_weight_per_symbol": 0.1,
  "min_score": 0.0,
  "allow_short": true,
  "sharpe_ratio": 1.33,
  "max_drawdown": 0.08,
  "total_return": 0.20,
  "win_rate": 0.55
}
```

**使用範例**:
```bash
curl "http://localhost:8000/api/v1/policy/risk-config/active"
curl "http://localhost:8000/api/v1/policy/risk-config/active?file=policy/risk_config_suggested_auto_v2.yaml"
```

---

## 🎨 前端 Panel

### 組件位置

- `trading-ui/jgod-trading-ui/src/components/PolicyEvolutionPanel.tsx`

### 功能

1. **Active RiskConfig 顯示**
   - 顯示當前生效的 RiskConfig 檔案路徑
   - 顯示來源實驗的 Run ID、Sharpe、MaxDD 等指標
   - 顯示配置參數（long_budget, short_budget 等）

2. **實驗歷史表格**
   - 顯示 Timestamp、Run ID、Sharpe、MaxDD、Return、Score、Config
   - 支援日期範圍篩選
   - 快速選擇：最近 7/30/90 天
   - 可重新載入資料

3. **狀態處理**
   - Loading 狀態
   - Error 狀態（顯示錯誤訊息）
   - Empty 狀態（沒有實驗時顯示提示）

### UI 結構

```
┌─────────────────────────────────────────────────┐
│ Policy Evolution                                │
├─────────────────────────────────────────────────┤
│ Active RiskConfig                               │
│   File: policy/risk_config_suggested_v1.yaml    │
│   Run ID: abc123...def456                       │
│   Sharpe: 1.3300                                │
│   Config:                                       │
│     - Long Budget: 60.0%                        │
│     - Short Budget: 20.0%                       │
│     - Max Weight/Symbol: 10.0%                  │
├─────────────────────────────────────────────────┤
│ Experiment History                              │
│   [Start Date] [End Date] [7d] [30d] [90d] [Reload] │
│   ┌─────────────────────────────────────────┐   │
│   │ Timestamp | Run ID | Sharpe | MaxDD | ...│   │
│   │ 2024-12-01|abc123..| 1.3300 | 8.00% | ...│   │
│   │ 2024-11-28|def456..| 1.2100 | 9.50% | ...│   │
│   └─────────────────────────────────────────┘   │
│   Total: 50                                     │
└─────────────────────────────────────────────────┘
```

---

## 📊 使用情境

### 1. 觀察不同 Policy Loop 回合的策略表現

- 執行多次 Policy Loop v2
- 在 Evolution Panel 中查看歷史實驗
- 觀察 Sharpe、MaxDD 等指標的變化趨勢
- 判斷策略是否持續改善

### 2. 對比不同 RiskConfig 的指標

- 比較不同 long_budget / short_budget 組合的表現
- 分析 max_weight_per_symbol 的影響
- 評估 min_score 門檻的效果

### 3. 作為策略白皮書的圖表來源

- 匯出歷史實驗數據
- 生成策略表現圖表
- 記錄 RiskConfig 演進過程
- 展示策略優化成果

---

## 🔧 技術實作

### 後端

- **重用現有組件**:
  - `PolicyLogReaderV1` - 讀取 JSONL log
  - `load_risk_config` - 載入 YAML 配置
  - `PolicyScoreConfig` - 計算實驗評分

- **新增 Schemas**:
  - `PolicyExperimentHistoryItem` - 實驗歷史項目
  - `PolicyActiveConfig` - 當前生效配置

### 前端

- **API 呼叫**:
  - 使用 `axios` 進行 HTTP 請求
  - 並行請求 Active Config 和 Experiments
  - 完整的錯誤處理

- **狀態管理**:
  - React Hooks (`useState`, `useEffect`, `useCallback`)
  - 日期範圍篩選
  - Loading / Error / Empty 狀態

---

## 📝 資料流程

```
┌─────────────────────────────────────────────────┐
│         Policy Evolution Panel Flow             │
└─────────────────────────────────────────────────┘

1. Frontend (PolicyEvolutionPanel.tsx)
   ↓
   GET /api/v1/policy/risk-config/active
   GET /api/v1/policy/experiments/history
   ↓
2. Backend (jgod/api/routers/policy.py)
   ↓
   PolicyLogReaderV1 (讀取 JSONL)
   load_risk_config (讀取 YAML)
   ↓
3. Response (JSON)
   ↓
4. Frontend (顯示在 Panel)
   - Active RiskConfig Card
   - Experiment History Table
```

---

## 📚 相關文件

- `docs/JGOD_POLICY_LOOP_V1.md` - Policy Loop v1 架構
- `docs/JGOD_POLICY_SERVICE_V1_COMPLETION_REPORT.md` - Policy Service v1 完成報告
- `docs/JGOD_BACKTEST_SERVICE_V1_SPEC.md` - Backtest Service v1 規格
- `docs/JGOD_POLICY_LOOP_V2_SPEC.md` - Policy Loop v2 規格

---

## 🚀 未來擴展

### v2 可能的方向

1. **圖表視覺化**
   - Sharpe / MaxDD 走勢圖
   - 配置參數散點圖
   - 時間序列分析

2. **互動功能**
   - 點擊實驗查看詳細資訊
   - 比較多個實驗
   - 匯出數據為 CSV

3. **版本管理**
   - 標記特定實驗為「最佳版本」
   - 版本回滾功能
   - 版本差異比較

---

**版本**: Policy Evolution Panel v1.0  
**完成日期**: 2024-12  
**狀態**: ✅ Production Ready

