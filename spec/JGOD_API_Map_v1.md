# J-GOD API 映射 v1

**文件版本：** 1.0  
**最後更新：** 2025-01-06  
**目標讀者：** 後端工程師、前端工程師、API 使用者

---

## 文件說明

本文檔提供 J-GOD 系統所有 API 端點的完整映射，包括 HTTP 方法、路徑、功能說明與對應的 router 檔案。用於快速查找 API 端點與理解 API 設計。

---

## 1. API 設計原則

### 1.1 RESTful 設計

- 使用標準 HTTP 方法（GET, POST, PUT, DELETE, PATCH）
- 資源導向的 URL 設計
- JSON 格式的請求與回應

### 1.2 版本前綴

- **無前綴**：`/api/*` - 穩定 API（Predictions, Indicators, Universe）
- **v1 前綴**：`/api/v1/*` - v1 API（Decision, Doctrine Patch, Rule Sim 等）
- **v2 前綴**：`/api/v2/*` - v2 API（Doctrine V2）

### 1.3 模組劃分

API 端點按功能模組劃分，每個模組對應一個 router 檔案（`jgod/api/routers/*.py`）

---

## 2. Predictions / Indicators / Universe 區

### 2.1 Predictions API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/predictions/{date}` | 取得指定日期的所有股票預測 | `predictions.py` |
| GET | `/api/predictions/{date}/{symbol}` | 取得特定股票在特定日期的預測 | `predictions.py` |
| GET | `/api/predictions/timeline/{symbol}` | 取得股票的預測時間序列 | `predictions.py` |
| GET | `/api/predictions/latest/{symbol}` | 取得股票的最新預測結果（包含 factors 和 risk flags） | `predictions.py` |

### 2.2 Predictions V2 API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/v1/predictions/v2/final-score/{symbol}/{date}` | 取得 Final Score V2（包含 S-Rank, Strategy Scores, Conflict Summary） | `predictions_v2.py` |

### 2.3 Indicators API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/indicators/{symbol}/{date}` | 取得股票的 100 指標快照 | `indicators.py` |
| GET | `/api/v1/features/{symbol}/{date}` | 取得股票的特徵向量 | `indicators.py` |

### 2.4 Universe API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/universe/coverage` | 取得所有股票的指標覆蓋率狀況 | `universe.py` |
| GET | `/api/universe/coverage-detail` | 取得詳細的覆蓋率資訊（legacy） | `universe.py` |

---

## 3. Decision / Decision AB Test 區

### 3.1 Decision API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/v1/decision/portfolio` | 取得投資組合決策 | `decision.py` |

### 3.2 Decision AB Test API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/v1/decision-ab/experiments` | 取得 Decision AB 測試實驗列表 | `decision_ab.py` |
| GET | `/api/v1/decision-ab/experiments/{experiment_id}` | 取得特定實驗詳情 | `decision_ab.py` |
| POST | `/api/v1/decision-ab/experiments` | 建立新的 Decision AB 測試實驗 | `decision_ab.py` |
| GET | `/api/v1/decision-ab/reports/{experiment_id}` | 取得實驗報告 | `decision_ab.py` |
| GET | `/api/v1/decision-ab/summary` | 取得 Decision AB 測試摘要 | `decision_ab.py` |

---

## 4. Doctrine / Doctrine Patch / Doctrine Alert 區

### 4.1 Doctrine V2 API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/v2/doctrine/sections` | 取得 Doctrine 條文列表 | `doctrine_v2.py` |
| GET | `/api/v2/doctrine/sections/{section_id}` | 取得特定條文詳情 | `doctrine_v2.py` |
| GET | `/api/v2/doctrine/sections/{section_id}/versions/{version_id}` | 取得特定版本的內容 | `doctrine_v2.py` |
| GET | `/api/v2/doctrine/sections/{section_id}/diff` | 取得版本差異 | `doctrine_v2.py` |
| POST | `/api/v2/doctrine/sections/{section_id}/draft` | 建立草稿版本 | `doctrine_v2.py` |
| POST | `/api/v2/doctrine/sections/{section_id}/submit` | 提交審核 | `doctrine_v2.py` |
| POST | `/api/v2/doctrine/sections/{section_id}/approve` | 核准版本 | `doctrine_v2.py` |
| POST | `/api/v2/doctrine/sections/{section_id}/reject` | 拒絕版本 | `doctrine_v2.py` |
| POST | `/api/v2/doctrine/sections/{section_id}/rollback` | 回滾到指定版本 | `doctrine_v2.py` |

### 4.2 Doctrine Patch API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/v1/doctrine/patches` | 取得 Doctrine Patch 列表 | `doctrine_patch.py` |
| POST | `/api/v1/doctrine/patches` | 建立新的 Doctrine Patch | `doctrine_patch.py` |
| GET | `/api/v1/doctrine/patches/{patch_id}` | 取得特定 Patch 詳情 | `doctrine_patch.py` |
| POST | `/api/v1/doctrine/patches/{patch_id}/submit` | 提交 Patch 審核 | `doctrine_patch.py` |
| POST | `/api/v1/doctrine/patches/{patch_id}/approve` | 核准 Patch | `doctrine_patch.py` |
| POST | `/api/v1/doctrine/patches/{patch_id}/reject` | 拒絕 Patch | `doctrine_patch.py` |
| POST | `/api/v1/doctrine/patches/{patch_id}/apply` | 套用 Patch | `doctrine_patch.py` |

### 4.3 Doctrine Alert API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/v1/doctrine/alerts` | 取得 Doctrine 警報列表 | `doctrine_alert.py` |
| GET | `/api/v1/doctrine/alerts/{alert_id}` | 取得特定警報詳情 | `doctrine_alert.py` |

---

## 5. Rule Simulation / S-Rank / Observer / Signal Conflict 區

### 5.1 Rule Simulation API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| POST | `/api/v1/rule-sim/experiments` | 執行規則模擬實驗 | `rule_sim.py` |
| GET | `/api/v1/rule-sim/experiments/{experiment_id}` | 取得實驗詳情 | `rule_sim.py` |
| GET | `/api/v1/rule-sim/reports/{experiment_id}` | 取得實驗報告 | `rule_sim.py` |

### 5.2 S-Rank Engine API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| POST | `/api/v1/s-rank/rank` | 執行 S-Rank 排名 | `s_rank_engine.py` |
| GET | `/api/v1/s-rank/factors/{symbol}/{date}` | 取得 S-Rank 因子 | `s_rank_engine.py` |
| GET | `/api/v1/s-rank/trend` | 取得 S-Rank 趨勢 | `s_rank_engine.py` |

### 5.3 Observer API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/v1/observer/status` | 取得 Observer 狀態 | `observer.py` |
| GET | `/api/v1/observer/reports` | 取得 Observer 報告列表 | `observer.py` |
| GET | `/api/v1/observer/reports/{report_id}` | 取得特定報告詳情 | `observer.py` |

### 5.4 Signal Conflict API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/v1/predictions/conflicts` | 取得訊號衝突列表 | `signal_conflict.py` |

---

## 6. Error Review / Replay / Self-Repair 區

### 6.1 Error Review API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/v1/error-review/reports` | 取得錯誤審查報告列表 | `error_review.py` |

### 6.2 Error Replay API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/v1/error-replay/{replay_id}` | 取得錯誤重播詳情 | `error_replay.py` |

### 6.3 Self-Repair API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| POST | `/api/v1/knowledge/self-repair/analyze` | 執行 Self-Repair 分析 | `self_repair.py` |
| GET | `/api/v1/knowledge/self-repair/reports` | 取得 Self-Repair 報告列表 | `self_repair.py` |
| POST | `/api/v1/knowledge/self-repair/proposals/{proposal_id}/apply` | 套用 Self-Repair 提案 | `self_repair.py` |

---

## 7. Policy / Strategy / Backtest / Orders 區

### 7.1 Policy API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/v1/policy/experiments/best` | 取得最佳實驗配置 | `policy.py` |
| GET | `/api/v1/policy/risk-config/suggest` | 取得建議的風險配置 | `policy.py` |
| GET | `/api/v1/policy/health` | 取得政策健康度 | `policy.py` |
| GET | `/api/v1/policy/evolution` | 取得政策演進歷史 | `policy.py` |

### 7.2 Strategy API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/v1/strategy/signals` | 取得策略訊號 | `strategy.py` |

### 7.3 Backtest API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| POST | `/api/v1/backtest/run` | 執行回測 | `backtest.py` |
| GET | `/api/v1/backtest/reports/{report_id}` | 取得回測報告 | `backtest.py` |

### 7.4 Orders API

| 方法 | 路徑 | 功能 | Router 檔案 |
|------|------|------|-------------|
| GET | `/api/v1/orders` | 取得訂單列表 | `orders.py` |

---

## 8. 後續計畫

### 8.1 v1.0 穩定 API

以下 API 應在 v1.0 版本穩定，不應有重大變更：

- **Predictions API**（`/api/predictions/*`）
- **Indicators API**（`/api/indicators/*`）
- **Universe API**（`/api/universe/*`）
- **Decision V2 API**（`/api/v1/predictions/v2/*`）
- **Doctrine V2 API**（`/api/v2/doctrine/*`）

### 8.2 可能重構的 API

以下 API 可能在未來版本中重構：

- **Decision V1 API**：可能被 Decision V2 取代
- **Doctrine Patch API**：可能整合到 Doctrine V2
- **Policy API**：可能需要重新設計以支援更複雜的政策管理

### 8.3 新增 API 計畫

**實盤交易相關（v1.0+）：**
- `/api/v1/trading/orders` - 實盤訂單管理
- `/api/v1/trading/positions` - 持倉管理
- `/api/v1/trading/account` - 帳戶資訊

**即時監控相關（v0.3+）：**
- `/api/v1/monitoring/stream` - WebSocket 串流端點
- `/api/v1/monitoring/metrics` - 系統指標

---

## 9. API 使用範例

### 9.1 取得預測資料

```typescript
// 取得指定日期的所有預測
const predictions = await api.getPredictions('2024-12-31');

// 取得特定股票的預測
const prediction = await api.getPrediction('2330', '2024-12-31');

// 取得預測時間序列
const timeline = await api.getPredictionTimeline('2330');
```

### 9.2 取得 Final Score V2

```typescript
// 取得 Final Score V2（包含 S-Rank, Strategy Scores）
const finalScore = await api.getFinalScoreV2('2330', '2024-12-31');
```

### 9.3 Doctrine 管理

```typescript
// 取得 Doctrine 條文列表
const sections = await api.getDoctrineSections();

// 建立草稿版本
const versionId = await api.createDoctrineDraft('section_001', '新內容');

// 提交審核
await api.submitDoctrineForReview('section_001');
```

---

## 10. 相關文件

- [系統藍圖](./JGOD_System_Blueprint_v1.md) - 系統總覽
- [後端模組地圖](./JGOD_Backend_Module_Map_v1.md) - 後端模組說明
- [前端架構](./JGOD_Frontend_Architecture_v1.md) - 前端架構說明

---

**文件結束**

