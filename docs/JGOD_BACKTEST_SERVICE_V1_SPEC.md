# J-GOD Backtest Service v1 — API 規格文件

## 📋 概述

Backtest Service v1 將 Path A 回測功能封裝為 HTTP API 服務，讓任何外部系統可以透過 HTTP 觸發回測並取得結果。

### 目的

1. **服務化封裝**: 將 Path A 回測從 CLI 工具升級為可被任何系統呼叫的 HTTP 服務
2. **解耦合**: 外部系統無需直接操作 Path A Engine，只需透過 HTTP API 即可使用
3. **標準化介面**: 提供統一的 Request/Response 格式，便於整合

### 與 Policy Service v1 的關係

- **Backtest Service**: 負責「執行回測」並產生 `BacktestResult` + JSONL log
- **Policy Service**: 負責「分析實驗記錄」、排名、產生建議 RiskConfig

```
┌─────────────────────────────────────────────────────────┐
│              J-GOD Backtest & Policy Flow               │
└─────────────────────────────────────────────────────────┘

Backtest Service (執行回測)
    ↓
    PathAEngineV1.run_backtest()
    ↓
    BacktestResult + JSONL Log
    ↓
Policy Service (分析建議)
    ↓
    PolicyLogReaderV1 → PolicyWriterV1
    ↓
    RiskConfig YAML
    ↓
Decision Engine (應用配置)
```

---

## 🔌 API 規格

### Base URL

所有 Backtest Service endpoints 的前綴：`/api/v1/backtest`

### Endpoints

#### 1. POST `/api/v1/backtest/path-a/run-sync`

**功能**: 執行 Path A 同步回測

**請求體**: `PathABacktestRequest`

```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "capital": 1000000.0,
  "long_budget": 0.6,
  "short_budget": 0.2,
  "max_weight_per_symbol": 0.1,
  "min_score": 0.0,
  "allow_short": true,
  "risk_config_file": null,
  "tag": "api_test_001"
}
```

**回應**: `PathABacktestResponse`

```json
{
  "request": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "capital": 1000000.0,
    "long_budget": 0.6,
    "short_budget": 0.2,
    "max_weight_per_symbol": 0.1,
    "min_score": 0.0,
    "allow_short": true,
    "risk_config_file": null,
    "tag": "api_test_001"
  },
  "summary": {
    "run_id": "abc123def456",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 1000000.0,
    "final_capital": 1200000.0,
    "total_return": 0.20,
    "annualized_return": 0.20,
    "annualized_volatility": 0.15,
    "sharpe_ratio": 1.33,
    "max_drawdown": 0.08,
    "win_rate": 0.55,
    "num_days": 252,
    "num_trades": 120,
    "long_trades": 80,
    "short_trades": 40
  }
}
```

**錯誤處理**:
- `400 Bad Request`: 日期格式錯誤、參數驗證失敗
- `500 Internal Server Error`: 回測執行失敗、資料庫錯誤

---

#### 2. GET `/api/v1/backtest/path-a/experiments/recent`

**功能**: 讀取最近 Path A 回測實驗記錄

**Query 參數**:
- `start_date` (可選): 篩選開始日期 (YYYY-MM-DD)
- `end_date` (可選): 篩選結束日期 (YYYY-MM-DD)
- `limit` (可選, 預設: 20): 返回筆數上限 (1-100)

**回應**: `List[PathABacktestSummary]`

```json
[
  {
    "run_id": "abc123def456",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 1000000.0,
    "final_capital": 1200000.0,
    "total_return": 0.20,
    "annualized_return": 0.20,
    "annualized_volatility": 0.15,
    "sharpe_ratio": 1.33,
    "max_drawdown": 0.08,
    "win_rate": 0.55,
    "num_days": 252,
    "num_trades": 120,
    "long_trades": 80,
    "short_trades": 40
  },
  ...
]
```

**排序**: 按 `timestamp` 由新到舊

---

## 📝 使用範例

### 使用 curl

#### 1. 執行同步回測

```bash
curl -X POST "http://localhost:8000/api/v1/backtest/path-a/run-sync" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "capital": 1000000.0,
    "long_budget": 0.6,
    "short_budget": 0.2,
    "max_weight_per_symbol": 0.1,
    "min_score": 0.0,
    "allow_short": true,
    "tag": "curl_test_001"
  }'
```

#### 2. 讀取最近 10 筆實驗

```bash
curl "http://localhost:8000/api/v1/backtest/path-a/experiments/recent?limit=10"
```

#### 3. 篩選特定日期範圍的實驗

```bash
curl "http://localhost:8000/api/v1/backtest/path-a/experiments/recent?start_date=2024-01-01&end_date=2024-12-31&limit=20"
```

---

### 使用 Python requests

```python
import requests

# 執行回測
response = requests.post(
    "http://localhost:8000/api/v1/backtest/path-a/run-sync",
    json={
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "capital": 1000000.0,
        "long_budget": 0.6,
        "short_budget": 0.2,
        "tag": "python_test_001"
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Run ID: {result['summary']['run_id']}")
    print(f"Sharpe Ratio: {result['summary']['sharpe_ratio']:.4f}")
    print(f"Total Return: {result['summary']['total_return']:.2%}")
else:
    print(f"Error: {response.status_code} - {response.text}")

# 讀取最近實驗
response = requests.get(
    "http://localhost:8000/api/v1/backtest/path-a/experiments/recent",
    params={"limit": 10}
)

if response.status_code == 200:
    experiments = response.json()
    print(f"Found {len(experiments)} recent experiments")
    for exp in experiments:
        print(f"  - {exp['run_id']}: Sharpe={exp['sharpe_ratio']:.4f}")
```

---

### 使用 RiskConfig YAML

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/backtest/path-a/run-sync",
    json={
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "capital": 1000000.0,
        "risk_config_file": "policy/risk_config_suggested_v1.yaml",
        "tag": "risk_config_test"
    }
)
```

---

## 🏗️ 架構設計

### 模組結構

```
jgod/api/
├── schemas/
│   └── backtest.py          # Pydantic models
├── routers/
│   └── backtest.py          # API endpoints
└── main.py                  # FastAPI app (註冊 router)
```

### 資料流程

```
HTTP Request
    ↓
Backtest Router (jgod/api/routers/backtest.py)
    ↓
PathAEngineV1 (jgod/path_a/path_a_engine_v1.py)
    ↓
BacktestResult
    ↓
JSONL Log Writer (自動)
    ↓
HTTP Response (PathABacktestResponse)
```

### 與現有 Policy Loop 的關係

```
┌─────────────────────────────────────────────────────────┐
│        Backtest Service + Policy Service 流程           │
└─────────────────────────────────────────────────────────┘

1. Backtest Service
   POST /api/v1/backtest/path-a/run-sync
   ↓
   PathAEngineV1.run_backtest()
   ↓
   BacktestResult + JSONL Log (data/path_a_backtest_logs.jsonl)

2. Policy Service
   GET /api/v1/policy/experiments/best
   ↓
   PolicyLogReaderV1 (讀取 JSONL)
   ↓
   排名後的實驗列表

3. Policy Service
   GET /api/v1/policy/risk-config/suggest
   ↓
   PolicyWriterV1 (分析 + 產生建議)
   ↓
   RiskConfig YAML

4. Backtest Service (再次使用建議配置)
   POST /api/v1/backtest/path-a/run-sync
   ↓
   risk_config_file: "policy/risk_config_suggested_v1.yaml"
   ↓
   驗證建議配置的表現
```

---

## 🔧 技術細節

### Request/Response Models

#### PathABacktestRequest

- 所有 Decision Engine 參數
- 可選的 `risk_config_file`（YAML 路徑）
- 可選的 `tag`（實驗標籤）

#### PathABacktestSummary

- 精簡版的績效摘要
- 包含所有關鍵指標
- 適合前端顯示或外部系統整合

#### PathABacktestResponse

- 包含原始請求與結果摘要
- 方便追蹤與除錯

### 錯誤處理

- **日期格式錯誤**: 400 Bad Request
- **參數驗證失敗**: 400 Bad Request
- **RiskConfig 檔案不存在**: 400 Bad Request
- **回測執行失敗**: 500 Internal Server Error
- **資料庫錯誤**: 500 Internal Server Error

### Log 寫入

- 自動寫入 `data/path_a_backtest_logs.jsonl`
- 使用與 `scripts/run_path_a_v1.py` 相同的格式
- 支援 `tag` 欄位（可選）

### 同步執行

- v1 版本為同步執行（立即返回結果）
- 未來 v2 可能支援非同步執行（使用 Celery 或類似工具）

---

## 📚 相關文件

- `docs/JGOD_POLICY_LOOP_V1.md` - Policy Loop v1 架構
- `docs/JGOD_POLICY_SERVICE_V1_COMPLETION_REPORT.md` - Policy Service v1 完成報告
- `docs/JGOD_Microservices_Design_v1.md` - 微服務設計藍圖

---

## ✅ 開發注意事項

### 不修改的模組

- `jgod/path_a/path_a_engine_v1.py` - 保持不變
- `jgod/policy/policy_log_reader_v1.py` - 保持不變
- `jgod/policy/policy_writer_v1.py` - 保持不變
- Log Writer 格式（JSONL）- 保持不變

### 重用現有機制

- PathAEngineV1 - 完全重用
- BacktestResult - 完全重用
- Log Writer - 重用相同的寫入邏輯

### 未來擴展

- 非同步執行（Celery/Background Tasks）
- 回測佇列管理
- 進度查詢 API
- 結果快取機制

---

**版本**: Backtest Service v1.0  
**完成日期**: 2024-12  
**狀態**: ✅ Production Ready

