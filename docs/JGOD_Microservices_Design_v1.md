# J-GOD Microservices Design v1

## 1. Overview

### Current State (Monolith)

J-GOD 目前是一個 **FastAPI monolith**，包含以下核心模組：

- **FastAPI Application** (`jgod/api/main.py`): 統一的 HTTP API 入口
- **Data Layer**: SQLite 資料庫 (`data/jgod_tw_stock.db`) 包含 `daily_bars`, `indicator_snapshots`, `prediction_snapshots`
- **Feature Store** (`jgod/feature_store/`): 因子資料封裝層
- **Prediction Engine** (`jgod/prediction/`): 預測引擎
- **Strategy Engine** (`jgod/strategy/strategy_engine_v1.py`): 策略與信號產生
- **Decision Engine** (`jgod/decision/decision_engine_v1.py`): 決策與風險引擎
- **Path A Engine** (`jgod/path_a/path_a_engine_v1.py`): 回測引擎
- **Policy Service** (`jgod/policy/`): Policy Log Reader, Writer, Reward Adapter
- **War Room Backend** (`jgod/war_room_backend/`, `jgod/war_room_backend_v6/`): 戰情室後端

所有功能都在單一進程中運行，透過內部 Python 模組呼叫進行溝通。

### Microservices Goal

微服務化的目標：

1. **關注點分離 (Separation of Concerns)**: 每個服務專注於單一職責
2. **獨立擴展 (Independent Scaling)**: 可以根據負載獨立擴展不同服務
3. **故障隔離 (Fault Isolation)**: 單一服務故障不影響整體系統
4. **技術多樣性**: 不同服務可使用不同技術棧（如果需要）
5. **團隊協作**: 不同團隊可以獨立開發和部署各自負責的服務

## 2. Proposed Services

### 2.1 MarketData Service

**責任：**
- 管理原始市場資料（daily_bars, tick data）
- 管理 Feature Store（indicator_snapshots）
- 提供標準化的市場資料查詢介面

**Key APIs:**
```
GET  /v1/prices/{symbol}?start_date=...&end_date=...
GET  /v1/features/{symbol}/{date}
GET  /v1/features/batch
POST /v1/features/compute (觸發因子計算)
```

**Data Ownership:**
- `daily_bars` table
- `indicator_snapshots` table
- Feature Store cache

**對應現有模組：**
- `jgod/storage/models.py` (DailyBar, IndicatorSnapshot)
- `jgod/feature_store/feature_store.py`

---

### 2.2 Prediction Service

**責任：**
- 執行預測計算（使用 Feature Store 的資料）
- 管理預測結果（prediction_snapshots）
- 提供預測查詢 API

**Key APIs:**
```
GET  /v1/predictions/{symbol}/{date}
GET  /v1/predictions/batch?date=...
POST /v1/predictions/compute (觸發預測計算)
```

**Data Ownership:**
- `prediction_snapshots` table

**對應現有模組：**
- `jgod/prediction/`
- `jgod/api/routers/predictions.py`

---

### 2.3 Strategy Service

**責任：**
- 讀取 Prediction Service 的預測結果
- 產生策略信號（DailySignalSet）
- 管理策略參數和配置

**Key APIs:**
```
GET  /v1/strategy/signals?date=...&universe=...
GET  /v1/strategy/signals/{symbol}/{date}
POST /v1/strategy/config (更新策略參數)
```

**Data Ownership:**
- 無直接資料庫所有權（只讀 prediction_snapshots）
- 策略配置檔案

**對應現有模組：**
- `jgod/strategy/strategy_engine_v1.py`
- `jgod/api/routers/strategy.py`

---

### 2.4 Decision Service

**責任：**
- 讀取 Strategy Service 的信號
- 執行權重分配和風險控制
- 產生 PortfolioPlan

**Key APIs:**
```
GET  /v1/decision/portfolio?date=...&universe=...
POST /v1/decision/portfolio (使用自訂 RiskConfig)
POST /v1/decision/risk-config (更新風險參數)
```

**Data Ownership:**
- 風險配置檔案（RiskConfig）
- 無直接資料庫所有權

**對應現有模組：**
- `jgod/decision/decision_engine_v1.py`
- `jgod/api/routers/decision.py`

---

### 2.5 Backtest Service (Path A)

**責任：**
- 執行回測計算（讀取 Decision Service 的 PortfolioPlan）
- 模擬交易執行（讀取 MarketData Service 的價格資料）
- 寫入回測日誌（path_a_backtest_logs.jsonl）
- 產生績效報告

**Key APIs:**
```
POST /v1/backtest/run
  Request: { start_date, end_date, initial_capital, risk_config }
  Response: { run_id, metrics, trades, equity_curve }

GET  /v1/backtest/{run_id}
GET  /v1/backtest/logs?start_date=...&end_date=...
```

**Data Ownership:**
- `path_a_backtest_logs.jsonl` (JSON Lines 格式)
- 回測結果快取

**對應現有模組：**
- `jgod/path_a/path_a_engine_v1.py`
- `scripts/run_path_a_v1.py`

**關鍵設計：**
- Path A 是**性能驗證的唯一來源**（canonical source of truth）
- 所有策略和風險參數的驗證都必須通過 Path A

---

### 2.6 Policy Service

**責任：**
- 讀取 Backtest Service 產生的日誌
- 分析實驗結果並評分
- 產生建議的 RiskConfig
- 提供 reward adapter 給 RL 模組使用

**Key APIs:**
```
GET  /v1/policy/experiments/best?start_date=...&end_date=...&top_n=...
GET  /v1/policy/risk-config/suggest?start_date=...&end_date=...
GET  /v1/policy/reward-samples?start_date=...&end_date=...
```

**Data Ownership:**
- 只讀 `path_a_backtest_logs.jsonl`
- 產生的建議配置檔案（`policy/risk_config_suggested_v1.yaml`）

**對應現有模組：**
- `jgod/policy/policy_log_reader_v1.py`
- `jgod/policy/policy_writer_v1.py`
- `jgod/policy/policy_reward_adapter_v1.py`
- `jgod/api/routers/policy.py`

**關鍵設計：**
- Policy Service 是**無狀態**的（只讀日誌，不修改資料）
- 可以獨立部署和擴展，不影響其他服務

---

### 2.7 War Room Service

**責任：**
- 提供 War Room UI 所需的聚合資料
- 協調多個服務的 API 呼叫
- 管理 WebSocket 連線（即時更新）

**Key APIs:**
```
GET  /v1/war-room/session
WS   /v1/war-room/ws/{session_id}

聚合端點：
GET  /v1/war-room/dashboard?date=...
  (聚合 Prediction + Strategy + Decision + Policy)
```

**Data Ownership:**
- 無直接資料庫所有權
- Session 狀態（可選，可改為無狀態）

**對應現有模組：**
- `jgod/war_room_backend/`
- `jgod/war_room_backend_v6/`

---

## 3. Service Boundaries & Data Flow

### 3.1 End-to-End Flow

```
┌─────────────────┐
│  MarketData     │
│   Service       │
│  (Features)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Prediction     │
│   Service       │
│  (Scores)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Strategy       │
│   Service       │
│  (Signals)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Decision       │
│   Service       │
│  (Portfolio)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│  Backtest       │◄─────┤  MarketData     │
│   Service       │      │   (Prices)      │
│  (Logs)         │      └─────────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Policy         │
│   Service       │
│  (Config)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Decision       │
│   (Apply Config)│
└─────────────────┘
```

### 3.2 Service Communication

**同步呼叫（HTTP REST）：**
- Strategy Service → Prediction Service (讀取預測)
- Decision Service → Strategy Service (讀取信號)
- Backtest Service → Decision Service (讀取 PortfolioPlan)
- Backtest Service → MarketData Service (讀取價格)
- Policy Service → Backtest Service (讀取日誌，但實際上是讀檔案)
- War Room Service → 所有服務 (聚合資料)

**非同步通訊（未來可考慮）：**
- 使用 Message Queue (Kafka / RabbitMQ) 處理大量資料更新
- 關鍵 Topic：
  - `J-GOD_DATA_ALERT`: 市場資料更新通知
  - `J-GOD_PREDICTION_UPDATE`: 預測結果更新
  - `J-GOD_OPTIMAL_WEIGHTS`: 最佳權重建議
  - `J-GOD_POSITION_UPDATE`: 部位更新

### 3.3 Data Flow Principles

1. **單向資料流**: MarketData → Prediction → Strategy → Decision → Backtest → Policy
2. **Path A 是真理來源**: 所有策略和風險參數的驗證都必須通過 Path A 回測
3. **Policy 閉環**: Policy Service 分析 Backtest 結果，產生建議配置，Decision Service 可採用這些配置

---

## 4. API Contracts (High Level)

### 4.1 MarketData Service

**GET /v1/prices/{symbol}**
- Request: `symbol`, `start_date`, `end_date`
- Response: `[{date, open, high, low, close, volume}, ...]`
- Idempotent: Yes
- Stateless: Yes

**GET /v1/features/{symbol}/{date}**
- Request: `symbol`, `date`
- Response: `{symbol, date, indicators: [{code, category, value}, ...], coverage_ratio}`
- Idempotent: Yes
- Stateless: Yes

---

### 4.2 Prediction Service

**GET /v1/predictions/{symbol}/{date}**
- Request: `symbol`, `date`
- Response: `{symbol, date, score, signal, verdict, risk_flags}`
- Idempotent: Yes
- Stateless: Yes

---

### 4.3 Strategy Service

**GET /v1/strategy/signals**
- Request: `date`, `universe` (optional), `min_score` (optional)
- Response: `{date, universe_size, long_candidates: [...], short_candidates: [...]}`
- Idempotent: Yes
- Stateless: Yes

---

### 4.4 Decision Service

**GET /v1/decision/portfolio**
- Request: `date`, `universe` (optional), `risk_config` (optional)
- Response: `{date, universe_size, positions: [...], summary: {...}}`
- Idempotent: Yes
- Stateless: Yes

---

### 4.5 Backtest Service

**POST /v1/backtest/run**
- Request: `{start_date, end_date, initial_capital, risk_config}`
- Response: `{run_id, metrics: {...}, trades: [...], equity_curve: [...]}`
- Idempotent: No (每次執行都是新的回測)
- Stateless: No (需要維護回測狀態，但可改為非同步處理)

---

### 4.6 Policy Service

**GET /v1/policy/experiments/best**
- Request: `start_date`, `end_date`, `top_n`, `min_days`, `min_trades`
- Response: `[{run_id, sharpe_ratio, max_drawdown, score, config: {...}}, ...]`
- Idempotent: Yes
- Stateless: Yes

**GET /v1/policy/risk-config/suggest**
- Request: `start_date`, `end_date`, `top_k`
- Response: `{suggestion: {...}, config: {long_budget, short_budget, ...}}`
- Idempotent: Yes
- Stateless: Yes

---

### 4.7 War Room Service

**GET /v1/war-room/dashboard**
- Request: `date`
- Response: `{predictions: [...], signals: [...], portfolio: {...}, policy_suggestion: {...}}`
- Idempotent: Yes
- Stateless: Yes（如果 session 管理改為無狀態）

---

## 5. Migration Plan (Phased)

### Phase 0: Current Monolith (Status Today)

**狀態：** ✅ 已完成

- 所有功能都在單一 FastAPI 應用中
- 內部使用 Python 模組呼叫
- 穩定的 monolith 架構

---

### Phase 1: Logical Modules (Current State)

**狀態：** ✅ 已完成

- 程式碼已按照邏輯模組組織（`jgod/feature_store/`, `jgod/prediction/`, `jgod/strategy/`, `jgod/decision/`, `jgod/path_a/`, `jgod/policy/`）
- API 路由已按模組分離（`jgod/api/routers/`）
- 資料結構已標準化（使用 dataclass / Pydantic）

**對應現有結構：**
- `jgod/api/routers/predictions.py`
- `jgod/api/routers/strategy.py`
- `jgod/api/routers/decision.py`
- `jgod/api/routers/policy.py`

---

### Phase 2: Extract Policy Service First

**目標：** 將 Policy Service 拆分成獨立服務

**理由：**
- Policy Service 是**無狀態**的（只讀日誌檔案）
- 不依賴其他服務的內部狀態
- 可以獨立部署和擴展

**實作步驟：**
1. 建立獨立的 FastAPI 應用（`services/policy_service/main.py`）
2. 將 `jgod/policy/` 模組移到 Policy Service
3. Policy Service 透過檔案系統或 HTTP 讀取 `path_a_backtest_logs.jsonl`
4. 其他服務透過 HTTP 呼叫 Policy Service API
5. 保持向後兼容（舊的 monolith 仍可使用）

**影響範圍：**
- ✅ 低風險（Policy Service 是只讀的）
- ✅ 不影響其他服務

---

### Phase 3: Extract Backtest Service

**目標：** 將 Path A Engine 拆分成獨立服務

**理由：**
- Backtest Service 是**計算密集型**服務，可以獨立擴展
- 需要讀取 Decision Service 的 PortfolioPlan 和 MarketData Service 的價格資料

**實作步驟：**
1. 建立獨立的 FastAPI 應用（`services/backtest_service/main.py`）
2. 將 `jgod/path_a/` 模組移到 Backtest Service
3. Backtest Service 透過 HTTP 呼叫 Decision Service 和 MarketData Service
4. 寫入日誌檔案（或改用資料庫儲存）
5. 提供非同步回測 API（避免長時間阻塞）

**影響範圍：**
- ⚠️ 中等風險（需要確保服務間通訊穩定）
- ⚠️ 需要處理非同步任務（使用 Celery 或類似工具）

---

### Phase 4: Gradual Extraction of Prediction/Strategy/Decision

**目標：** 依序拆分 Prediction、Strategy、Decision Service

**順序建議：**
1. **Prediction Service**（較獨立，只讀 Feature Store）
2. **Decision Service**（讀取 Strategy Service 的信號）
3. **Strategy Service**（讀取 Prediction Service 的預測）

**實作步驟：**
1. 為每個服務建立獨立的 FastAPI 應用
2. 將對應的模組移到新服務
3. 更新服務間通訊（從內部模組呼叫改為 HTTP API）
4. 保持 API 向後兼容

**影響範圍：**
- ⚠️ 高風險（影響核心資料流）
- ⚠️ 需要仔細測試服務間通訊

---

### Phase 5: Extract MarketData Service

**目標：** 將資料層拆分為獨立服務

**理由：**
- MarketData Service 是**資料密集型**服務
- 可以獨立優化資料存取效能（快取、索引等）

**實作步驟：**
1. 建立獨立的 FastAPI 應用（`services/marketdata_service/main.py`）
2. 將 `jgod/storage/` 和 `jgod/feature_store/` 移到 MarketData Service
3. 其他服務透過 HTTP 呼叫 MarketData Service
4. 考慮引入 Redis 快取層

**影響範圍：**
- ⚠️ 非常高風險（所有服務都依賴資料）
- ⚠️ 需要確保資料一致性和可用性

---

### Phase 6: War Room as Pure Frontend

**目標：** War Room 成為純前端應用，透過 API Gateway 呼叫所有後端服務

**實作步驟：**
1. War Room UI 改為純 React/Vue 前端（不依賴後端渲染）
2. 透過 API Gateway 統一呼叫所有後端服務
3. 使用 WebSocket Gateway 處理即時更新
4. 引入身份驗證和授權（OAuth / JWT）

**影響範圍：**
- ✅ 低風險（前端改動不影響後端）

---

## 6. Non-Goals for v1

### 不立即實作的項目

1. **不立即拆分程式碼**：保持 monolith 結構，只建立設計藍圖
2. **不需要 Kubernetes**：初期可以使用 Docker Compose 或簡單的服務編排
3. **不破壞現有 API**：保持向後兼容
4. **不需要服務網格 (Service Mesh)**：初期使用簡單的 HTTP 通訊即可
5. **不需要分散式追蹤系統**：初期可以使用簡單的日誌聚合
6. **不需要 API Gateway**：初期可以直接呼叫各服務 API

### 未來可考慮的增強

1. **Message Queue**：當服務間通訊量增加時，考慮引入 Kafka / RabbitMQ
2. **分散式快取**：使用 Redis 快取常用資料
3. **服務發現**：使用 Consul / etcd 進行服務註冊和發現
4. **負載均衡**：當單一服務需要擴展時，引入負載均衡器
5. **監控和告警**：使用 Prometheus + Grafana 監控服務健康狀態

---

## 7. Implementation Notes

### 7.1 服務間通訊

**初期方案（簡單）：**
- 使用 HTTP REST API
- 同步呼叫（適合低延遲需求）

**未來方案（可擴展）：**
- 引入 Message Queue（Kafka / RabbitMQ）
- 支援非同步處理
- 事件驅動架構

### 7.2 資料一致性

**策略：**
- 每個服務擁有自己的資料（如果適用）
- 透過 API 進行資料同步
- 使用事件溯源（Event Sourcing）記錄資料變更（未來）

### 7.3 錯誤處理

**原則：**
- 每個服務應獨立處理錯誤
- 使用標準 HTTP 狀態碼
- 提供清晰的錯誤訊息
- 實作重試機制（對於暫時性錯誤）

### 7.4 測試策略

**建議：**
- 每個服務應有獨立的單元測試
- 使用 Contract Testing（Pact）確保服務間 API 兼容性
- 建立整合測試環境（Docker Compose）

---

## 8. References

### 現有模組對應

- **MarketData Service**: `jgod/storage/`, `jgod/feature_store/`
- **Prediction Service**: `jgod/prediction/`, `jgod/api/routers/predictions.py`
- **Strategy Service**: `jgod/strategy/`, `jgod/api/routers/strategy.py`
- **Decision Service**: `jgod/decision/`, `jgod/api/routers/decision.py`
- **Backtest Service**: `jgod/path_a/`, `scripts/run_path_a_v1.py`
- **Policy Service**: `jgod/policy/`, `jgod/api/routers/policy.py`
- **War Room Service**: `jgod/war_room_backend/`, `jgod/war_room_backend_v6/`

### 相關文件

- `docs/JGOD_System_Architecture_v1.md`: 系統架構總覽
- `spec/JGOD_System_Architecture_v1.md`: 架構規格文件

---

## 9. Conclusion

這份文件提供了 J-GOD 微服務化的設計藍圖。**目前不需要立即實作**，但為未來的拆分提供了清晰的指引。

**關鍵原則：**
1. **逐步遷移**：一次只拆分一個服務，確保系統穩定性
2. **向後兼容**：保持現有 API 和腳本可用
3. **優先拆分獨立服務**：先從 Policy Service 開始（無狀態、獨立）
4. **Path A 是真理來源**：所有策略驗證都必須通過回測

**下一步行動：**
- 當系統規模擴大、需要獨立擴展時，參考此藍圖進行服務拆分
- 保持此文件的更新，反映實際架構變更

