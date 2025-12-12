# J-GOD 後端模組地圖 v1

**文件版本：** 1.0  
**最後更新：** 2025-01-06  
**目標讀者：** 後端工程師、架構師

---

## 文件說明

本文檔提供 J-GOD 後端所有模組的詳細說明，包括職責、輸入輸出、依賴關係與完整度評估。用於快速理解各模組功能與定位。

---

## 1. 後端總覽

J-GOD 後端採用模組化架構，主要分為以下類別：

1. **核心引擎模組**：市場資料、預測、決策、策略、風險、執行
2. **知識與治理模組**：知識引擎、Doctrine 系統、警報系統
3. **實驗與模擬模組**：Path 引擎、回測、規則模擬、A/B 測試
4. **觀察與監控模組**：Observer、診斷、錯誤引擎
5. **戰情室與編排模組**：War Room 核心、後端 API
6. **資料儲存模組**：資料庫模型與連接

---

## 2. 核心引擎模組

### 2.1 `jgod/market/` - 市場資料引擎

**職責：** 市場資料載入、快取、技術指標計算

**主要類別：**
- `DataLoader` - 資料載入器
- `TechnicalIndicators` - 技術指標計算器
- `MarketStatus` - 市場開盤狀態判斷
- `PriceCache` - 價格快取機制

**主要資料流：**
```
外部 API (FinMind) → DataLoader → PriceCache → TechnicalIndicators → OHLCV DataFrame
```

**輸入：** 股票代號、日期範圍

**輸出：** OHLCV DataFrame、技術指標（MA, RSI, MACD 等）

**依賴：** `api_clients/finmind_client.py`

**完整度：** ✅ 高（已實作 DataLoader, Indicators, MarketStatus）

---

### 2.2 `jgod/prediction/` - 預測引擎

**職責：** 規則型預測、特徵建構、排名

**主要類別：**
- `PredictionEngine` - 規則型預測引擎
- `FeatureBuilder` - 特徵建構器
- `RankingEngine` - 排名引擎
- `IndicatorBuilder100` - 100 指標建構器

**主要資料流：**
```
特徵向量 → PredictionEngine → Raw Score → RankingEngine → PredictionSnapshot
```

**輸入：** 股票特徵向量（Features）

**輸出：** `PredictionSnapshot`（包含 score, signal, factors, risk_flags）

**依賴：** `jgod/storage/`, `jgod/market/`

**完整度：** ✅ 高（已實作 prediction_engine, feature_builder, ranking, indicator_builder_100）

---

### 2.3 `jgod/decision/` - 決策引擎

**職責：** Raw Score → Final Score 轉換、Doctrine 查詢、LLM 修正

**主要類別：**
- `DecisionEngineV1` - Decision Layer V1（LLM-based）
- `DecisionEngineV2` - Decision Layer V2（S-Rank weighted）
- `DecisionLlmWrapper` - LLM 包裝器
- `PromptBuilder` - 提示詞建構器

**主要資料流：**
```
Raw Score → DecisionEngine → Doctrine 查詢 → LLM 修正 → Final Score + Doctrine Flags
```

**輸入：** Raw Score + Context

**輸出：** `DecisionOutput`（final_score, correction_factor, doctrine_flags）

**依賴：** `jgod/knowledge/`, LLM Clients（OpenAI, Claude, etc.）

**完整度：** ✅ 中高（V1/V2 已實作，但整合測試可能不足）

**注意：** 目前 V1 和 V2 並存，建議逐步遷移到 V2

---

### 2.4 `jgod/strategy/` - 策略引擎

**職責：** 交易策略框架、訊號生成

**主要類別：**
- `BaseStrategy` - 策略基類
- `BreakoutStrategy` - 突破策略實作
- `AISignalBridge` - AI 訊號橋接器

**主要資料流：**
```
預測結果 + 市場資料 → Strategy Engine → 交易訊號 (BUY/SELL/HOLD)
```

**輸入：** 預測結果、市場資料

**輸出：** 交易訊號（BUY/SELL/HOLD）

**依賴：** `jgod/prediction/`, `jgod/market/`

**完整度：** ⚠️ 中（基礎框架存在，但策略實作較少）

---

### 2.5 `jgod/risk/` - 風險引擎

**職責：** 風險評估、部位大小計算、投資組合管理

**主要類別：**
- `RiskManager` - 風險管理器
- `Portfolio` - 投資組合管理器
- `PositionSizer` - 部位大小計算器

**主要資料流：**
```
交易訊號 + 當前持倉 + 帳戶狀態 → Risk Engine → 風險評估 + 建議部位大小
```

**輸入：** 交易訊號、當前持倉、帳戶狀態

**輸出：** 風險評估結果、建議部位大小

**依賴：** `jgod/execution/`

**完整度：** ✅ 中高（RiskManager, Portfolio, PositionSizer 已實作）

---

### 2.6 `jgod/execution/` - 執行引擎

**職責：** 虛擬交易執行、滑價模擬、交易記錄

**主要類別：**
- `VirtualBroker` - 虛擬券商
- `SlippageModel` - 滑價模型
- `TradeRecorder` - 交易記錄器
- `ExecutionEngine` - 執行引擎

**主要資料流：**
```
核准的交易訂單 → VirtualBroker → SlippageModel → TradeRecorder → VirtualTrade
```

**輸入：** 核准的交易訂單

**輸出：** `VirtualTrade` 記錄

**依賴：** `jgod/storage/`

**完整度：** ✅ 高（VirtualBroker, SlippageModel, TradeRecorder 已實作）

---

## 3. 知識與治理模組

### 3.1 `jgod/knowledge/` - 知識引擎

**職責：** 知識提取、Doctrine 查詢、Self-Repair

**主要類別：**
- `KnowledgeBrain` - 知識大腦（核心查詢引擎）
- `SelfRepairEngine` - 自我修復引擎
- `KnowledgeExtractors` - 知識提取器集合

**主要資料流：**
```
查詢字串 → KnowledgeBrain → Doctrine 查詢 → 知識條文
錯誤事件 → SelfRepairEngine → 修復建議
```

**輸入：** 查詢字串、錯誤事件

**輸出：** 知識條文、修復建議

**依賴：** `knowledge_base/` JSONL 檔案

**完整度：** ✅ 中高（KnowledgeBrain, Self-Repair Engine 已實作）

---

### 3.2 `jgod/doctrine_v2/` - Doctrine 版本控制系統

**職責：** Doctrine 條文版本管理、審核流程、Patch 管理

**主要類別：**
- `DoctrineServiceV2` - Doctrine 服務（核心）
- `VersionStorage` - 版本儲存
- `PatchService` - Patch 服務

**主要資料流：**
```
Doctrine 條文內容 → VersionStorage → 版本化條文
審核決策 → DoctrineServiceV2 → 狀態更新
```

**輸入：** Doctrine 條文內容、審核決策

**輸出：** 版本化的 Doctrine 條文

**依賴：** `jgod/knowledge/`

**完整度：** ✅ 高（Service, VersionStorage, PatchService 已實作）

---

### 3.3 `jgod/doctrine_alert/` - Doctrine 警報系統

**職責：** 監控 Doctrine 違規、觸發警報

**主要類別：**
- `DoctrineAlertEngine` - 警報引擎
- `DoctrineRules` - Doctrine 規則定義

**主要資料流：**
```
交易決策 + Doctrine 規則 → DoctrineAlertEngine → 警報事件
```

**輸入：** 交易決策、Doctrine 規則

**輸出：** 警報事件

**依賴：** `jgod/doctrine_v2/`

**完整度：** ✅ 中（Engine, Rules 已實作）

---

## 4. 實驗與模擬模組

### 4.1 `jgod/path_a/` - Path A 引擎

**職責：** Path A 策略實作（規則型選股）

**主要類別：**
- `PathAEngine` - Path A 核心引擎
- 多個版本實作（可能有不一致）

**主要資料流：**
```
市場資料 + 配置檔案 → PathAEngine → 選股結果 + 回測報告
```

**輸入：** 市場資料、配置檔案

**輸出：** 選股結果、回測報告

**依賴：** `jgod/prediction/`, `jgod/backtest/`

**完整度：** ✅ 中高（多個版本存在，但可能有不一致）

---

### 4.2 `jgod/path_b/` ~ `jgod/path_e/` - 其他 Path 引擎

**Path B：** ⚠️ 低（檔案較少，可能未完成）

**Path C：** ⚠️ 低（檔案較少）

**Path D：** ✅ 中（有模型檔案和配置）

**Path E：** ✅ 中（有配置和實作）

**注意：** 各 Path 實作方式可能不一致，建議統一 Strategy Interface

---

### 4.3 `jgod/backtest/` - 回測引擎

**職責：** 歷史資料回測、績效計算

**主要類別：**
- `BacktestEngine` - 回測引擎核心

**主要資料流：**
```
策略配置 + 歷史資料 → BacktestEngine → 回測報告 + 績效指標
```

**輸入：** 策略配置、歷史資料

**輸出：** 回測報告、績效指標（Sharpe, MaxDD, Total Return 等）

**依賴：** `jgod/storage/`, `jgod/execution/`

**完整度：** ✅ 中高（BacktestEngine 已實作）

---

### 4.4 `jgod/rule_sim/` - 規則模擬引擎

**職責：** 規則變更的 A/B 測試、回測比較

**主要類別：**
- `RuleSimEngineV1` - 規則模擬引擎
- `RuleSimStorageV1` - 儲存層
- `RuleSandboxApplier` - 沙盒規則應用器

**主要資料流：**
```
規則變更配置 + 回測參數 → RuleSimEngine → Baseline vs Variant 比較 → RuleSimReport
```

**輸入：** 規則變更配置、回測參數

**輸出：** `RuleSimReport`（Baseline vs Variant 比較）

**依賴：** `jgod/backtest/`, `jgod/path_a/`

**完整度：** ✅ 高（Engine, Storage, SandboxApplier 已實作）

---

### 4.5 `jgod/decision_ab/` - Decision A/B 測試

**職責：** Decision Layer 的 A/B 測試

**主要類別：**
- `DecisionABAggregator` - 聚合器
- `DecisionABRunner` - 執行器
- `DecisionABStorage` - 儲存層

**完整度：** ✅ 中（Aggregator, Runner, Storage 已實作）

---

## 5. 觀察與監控模組

### 5.1 `jgod/observer/` - 觀察者引擎

**職責：** 系統狀態監控、異常偵測

**主要資料流：**
```
系統日誌 + 交易記錄 → Observer Engine → 觀察報告 + 異常警報
```

**輸入：** 系統日誌、交易記錄

**輸出：** 觀察報告、異常警報

**依賴：** `jgod/storage/`, `jgod/diagnostics/`

**完整度：** ✅ 中（Observer Engine 已實作）

---

### 5.2 `jgod/diagnostics/` - 診斷引擎

**職責：** 系統健康檢查、錯誤診斷

**主要類別：**
- `DiagnosisEngine` - 診斷引擎
- `HealthCheck` - 健康檢查

**輸入：** 系統狀態

**輸出：** 診斷報告

**完整度：** ✅ 中（DiagnosisEngine, HealthCheck 已實作）

---

### 5.3 `jgod/error_engine/` - 錯誤引擎

**職責：** 錯誤監控、自動修復嘗試

**主要類別：**
- `ErrorWatcher` - 錯誤監控器

**輸入：** 錯誤事件

**輸出：** 錯誤記錄、修復建議

**完整度：** ✅ 中（ErrorWatcher 已實作）

---

## 6. 戰情室與編排模組

### 6.1 `jgod/council_chamber/` - War Room V2 核心引擎

**職責：** 多 AI 角色並行分析、決策整合

**主要類別：**
- `WarRoomEngine` - War Room 核心引擎
- `ProviderManager` - Provider 管理器
- `RoleStateManager` - 角色狀態管理器

**主要資料流：**
```
使用者問題 + 市場資料 → WarRoomEngine → 多角色並行分析 → Strategist 總結
```

**輸入：** 使用者問題、市場資料

**輸出：** 多角色分析結果、Strategist 總結

**依賴：** `jgod/council_chamber/providers/`, LLM Clients

**完整度：** ✅ 高（WarRoomEngine, ProviderManager, RoleStateManager 已實作）

---

### 6.2 `jgod/council_chamber_backend_v6/` - War Room Backend V6

**職責：** FastAPI + WebSocket 後端（未來正式戰情室）

**完整度：** ⚠️ 中（基礎架構存在，但可能未完全整合）

---

### 6.3 `jgod/orchestrator/` - 編排器

**職責：** 任務編排、工作流管理

**完整度：** ⚠️ 低（檔案較少）

---

## 7. 資料儲存模組

### 7.1 `jgod/storage/` - 資料庫模型與連接

**職責：** SQLAlchemy ORM 模型、資料庫連接管理

**主要模型：**

| 模型 | 說明 | 主要欄位 |
|------|------|----------|
| `Stock` | 標的基本資訊 | symbol, name_zh, name_en, sector |
| `DailyBar` | 歷史日線資料 | symbol, date, open, high, low, close, volume |
| `IndicatorSnapshot` | 100 指標快照 | symbol, date, indicator_code, raw_value, normalized_value |
| `PredictionSnapshot` | 預測結果快照 | symbol, date, score, signal, factors_json, risk_flags_json |
| `VirtualTrade` | 模擬交易記錄 | symbol, open_datetime, close_datetime, side, quantity, pnl |
| `PortfolioSnapshot` | 組合淨值快照 | date, equity_curve, cash, positions_value, sharpe |

**資料庫：** SQLite (`data/jgod_tw_stock.db`)

**完整度：** ✅ 高（模型定義完整，SQLite 連接穩定）

---

## 8. 其他模組

### 8.1 `jgod/s_rank_engine/` - S-Rank 排名引擎

**職責：** 基於多因子加權的股票排名

**完整度：** ✅ 中（Engine 已實作）

---

### 8.2 `jgod/signal_aggregation/` - 訊號聚合

**職責：** 多策略訊號聚合

**完整度：** ✅ 中

---

### 8.3 `jgod/optimizer/` - 優化器

**職責：** 參數優化、超參數調整

**完整度：** ⚠️ 低（檔案較少）

---

## 9. 模組依賴關係圖

```
market → prediction → decision → strategy → risk → execution
  ↓         ↓            ↓
storage ← knowledge ← doctrine_v2
  ↓
observer → diagnostics → error_engine
  ↓
council_chamber (War Room)

path_a/b/c/d/e → backtest → rule_sim
```

---

## 10. 模組完整度總覽

| 模組類別 | 完整度 | 備註 |
|---------|--------|------|
| 核心引擎 | ✅ 中高 ~ 高 | 大部分已實作，部分需整合測試 |
| 知識與治理 | ✅ 中高 ~ 高 | Doctrine V2 已實作 |
| 實驗與模擬 | ⚠️ 中 ~ 高 | Path A 較完整，其他 Path 較少 |
| 觀察與監控 | ✅ 中 | 基礎功能已實作 |
| 戰情室 | ✅ 高 | War Room V2 核心已實作 |
| 資料儲存 | ✅ 高 | 模型定義完整 |

---

## 11. 相關文件

- [系統藍圖](./JGOD_System_Blueprint_v1.md) - 系統總覽
- [API 映射](./JGOD_API_Map_v1.md) - API 端點對應
- [架構風險與治理](./JGOD_Architecture_Risks_and_Governance_v1.md) - 技術債務與改進建議

---

**文件結束**

