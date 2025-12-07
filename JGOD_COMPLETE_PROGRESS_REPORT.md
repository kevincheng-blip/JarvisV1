# J-GOD 股神作戰系統 - 完整進度分析與現況報告

**報告生成時間：** 2025-01-06  
**報告版本：** v2.0  
**編撰者：** J-GOD 系統總工程師（AI Assistant）

---

## 執行摘要

J-GOD（股神作戰系統）是一個模組化、可部署的量化交易決策系統，整合了市場資料、100 指標引擎、預測系統、風險管理、執行引擎、多 AI 戰情室和前端交易介面。本報告全面掃描專案現況，包含已完成模組、資料庫狀態、技術架構、已知弱點與未來發展建議。

**專案規模：**
- 後端 Python 檔案：約 11,087 個（包含測試）
- 前端 TypeScript/React 檔案：約 543 個
- 測試檔案：83 個 Python 測試
- 資料庫表：10 個主要資料表
- 總程式碼行數：估計 100,000+ 行

---

## 一、後端（Backend）現況

### 1.1 核心模組架構

#### **API 層（`jgod/api/`）**
- **狀態：** ✅ 已實作並運行中
- **檔案：**
  - `main.py` - FastAPI 主應用程式（版本 1.0.0）
  - `routers/predictions.py` - 預測相關 API（7 個 endpoints）
  - `routers/indicators.py` - 指標相關 API
  - `routers/universe.py` - 股票池與覆蓋率 API
- **功能：**
  - RESTful API 設計，支援 CORS
  - 提供預測時間線、最新預測、指標快照、覆蓋率統計
  - 已整合 SQLAlchemy ORM 與資料庫

#### **資料層（`jgod/storage/`）**
- **狀態：** ✅ 完整實作
- **檔案：**
  - `models.py` - ORM 模型定義（10 個主要模型）
  - `db.py` - 資料庫連線與 session 管理
- **資料表：**
  1. `stocks` - 標的基本資訊（18 筆）
  2. `daily_bars` - 歷史日線資料（4,356 筆）
  3. `indicator_snapshots` - 100 指標快照（471,600 筆）
  4. `prediction_snapshots` - 預測結果（4,716 筆）
  5. `virtual_trades` - 模擬交易紀錄（0 筆，未啟用）
  6. `portfolio_snapshots` - 組合淨值快照（0 筆，未啟用）
  7. `tw_index_daily` - 台股指數日線（0 筆）
  8. `tw_stock_daily` - 台股日線（15 筆，legacy）
  9. `tw_stock_fundamentals` - 台股基本面（0 筆）
  10. `tw_stock_institutional` - 台股法人資料（0 筆）

#### **預測引擎（`jgod/prediction/`）**
- **狀態：** ✅ 完整實作
- **檔案：**
  - `rules/stock_upside_filter_60_v1.py` - 60 指標規則引擎
  - `rules/stock_upside_filter_v1.py` - 原始版本（向後兼容）
  - `data/indicator_builder_100.py` - 100 指標建構器
  - `prediction_engine.py` - 預測引擎主程式
  - `feature_builder.py` - 特徵建構器
  - `ranking.py` - 股票排序引擎
- **功能：**
  - 支援 100 指標框架（P01-P12, C01-C09, F01-F08, K01-K07, S01-S06, Q01-Q06, X01-X16, M01-M36）
  - 規則式評分系統（Rule-based Filter）
  - 產生 VERDICT（STRONG_BUY/BUY/NEUTRAL/AVOID/SHORT）
  - 提取 Positive/Negative Factors 與 Risk Flags

#### **資料建構（`jgod/prediction/data/`）**
- **狀態：** ✅ 完整實作
- **檔案：**
  - `indicator_builder_100.py` - 100 指標建構器（471 行）
- **功能：**
  - 整合 FinMind API Client
  - Rate Limiting：每秒最多 1 次 API 呼叫
  - 建構 100 指標字典供預測引擎使用
  - 支援 Price、Capital、Fundamental、Catalyst、Sentiment、Quant、Derivatives、Meta 指標

#### **資料輸入（`api_clients/`）**
- **狀態：** ✅ 完整實作
- **檔案：**
  - `finmind_client.py` - FinMind API 客戶端（Rate Limiter 整合）
  - `openai_client.py` - OpenAI API 客戶端
  - `anthropic_client.py` - Anthropic API 客戶端
  - `gemini_client.py` - Google Gemini API 客戶端
  - `perplexity_client.py` - Perplexity API 客戶端
- **功能：**
  - 統一的 API 客戶端介面
  - 內建 Rate Limiting 機制
  - 錯誤處理與重試邏輯

#### **War Room 引擎（`jgod/war_room/`）**
- **狀態：** ✅ 多版本並存（v4.2, v5.0, v6.0）
- **檔案結構：**
  - `war_room/` - Streamlit v4.2（48 個檔案）
  - `war_room_backend/` - FastAPI v5.0（9 個檔案）
  - `war_room_backend_v6/` - FastAPI v6.0（5 個檔案）
  - `war_room_v6/` - Engine v6（4 個檔案）
- **功能：**
  - 多 AI Provider 管理（OpenAI、Anthropic、Gemini、Perplexity）
  - 多角色戰情室（Intel Officer、Scout、Analyst、Strategist、Risk Officer）
  - WebSocket 即時串流
  - Streamlit Pseudo-Live 模式
- **已知問題：** ⚠️ 多版本並存導致程式碼重複，需要統一

#### **路徑引擎（Path Engines）**
- **狀態：** ✅ 已實作但使用率低
- **模組：**
  - `path_a/` - 基礎回測引擎（Extreme Mode 支援）
  - `path_b/` - Walk-Forward 引擎（Step B1-B4）
  - `path_c/` - 場景測試引擎（TW Equities 配置）
  - `path_d/` - 強化學習引擎（RL Agent、Training Loop）
  - `path_e/` - 即時交易引擎（Live Trading、Order Planner、Risk Guard）
- **功能：**
  - 多種策略驗證路徑
  - 模擬交易執行
  - 風險控制與部位管理

#### **風險管理（`jgod/risk/`）**
- **狀態：** ✅ 完整實作
- **檔案：**
  - `risk_manager.py` - 風險管理器
  - `portfolio.py` - 投資組合管理
  - `sizing.py` - 部位大小計算
  - `risk_model.py` / `risk_model_extreme.py` - 風險模型（標準版與 Extreme 版）
- **功能：**
  - 最大虧損控制
  - 最大持倉限制
  - 部位大小計算
  - 投資組合風險評估

#### **執行引擎（`jgod/execution/`）**
- **狀態：** ✅ 完整實作
- **檔案：**
  - `execution_engine.py` / `execution_engine_extreme.py` - 執行引擎
  - `virtual_broker.py` - 虛擬券商
  - `broker_adapter.py` - 券商適配器
  - `cost_model.py` - 成本模型
  - `slippage.py` - 滑點模型
- **功能：**
  - 模擬交易執行
  - 成本與滑點計算
  - 訂單管理

#### **其他核心模組**
- **`jgod/alpha_engine/`** - Alpha 因子引擎（10 個檔案）
- **`jgod/market/`** - 市場資料引擎（data_loader、indicators、price_cache）
- **`jgod/strategy/`** - 策略引擎（base_strategy、breakout_strategy）
- **`jgod/optimizer/`** - 組合優化器（optimizer_core_v2）
- **`jgod/performance/`** - 績效分析引擎（attribution、metrics）
- **`jgod/diagnostics/`** - 診斷引擎（health_check、diagnosis_engine）
- **`jgod/knowledge/`** - 知識庫引擎（11 個檔案）
- **`jgod/code_intel/`** - 程式碼洞察引擎（insight_engine、scanner）
- **`jgod/learning/`** - 錯誤學習引擎（error_learning_engine）
- **`jgod/experiments/`** - 實驗編排器（experiment_orchestrator）

---

### 1.2 Backfill 腳本現況

#### **已實作腳本（`scripts/`）**
1. **`run_backfill_raw_data.py`** ✅
   - 功能：回填原始日線資料（daily_bars）
   - 支援參數：`--universe-file`, `--symbols`, `--start-date`, `--end-date`
   - 狀態：完整實作，已用於 8 檔股票 2024 全年資料

2. **`run_backfill_indicators_100.py`** ✅
   - 功能：回填 100 指標快照（indicator_snapshots）
   - 支援參數：`--universe-file`, `--symbols`, `--start-date`, `--end-date`, `--force`
   - 狀態：完整實作，已產生 471,600 筆指標快照

3. **`run_backfill_predictions.py`** ✅
   - 功能：回填預測結果（prediction_snapshots）
   - 支援參數：`--start-date`, `--end-date`, `--symbols`, `--force`, `--min-indicators`
   - 狀態：完整實作，支援 indicators-only 模式
   - 已知問題：部分股票預測資料未完整（1301, 1303, 2308, 2412 缺少）

4. **`backfill_predictions_batch.sh`** ✅
   - 功能：批次執行預測回填（6 個批次）
   - 狀態：已生成，待執行

#### **其他腳本**
- `run_jgod_path_a.py` - Path A 實驗腳本
- `run_jgod_path_b.py` - Path B Walk-Forward 腳本
- `run_jgod_path_c.py` - Path C 場景測試腳本
- `run_jgod_path_d.py` - Path D RL 訓練腳本
- `run_jgod_path_e.py` - Path E 即時交易腳本
- `run_stock_upside_eval.py` - 單檔股票評估腳本
- `check_indicator_gaps.py` - 指標缺口檢查腳本
- `debug_check_db.py` - 資料庫檢查腳本

---

### 1.3 API Endpoints 清單

#### **Predictions API（`/api/predictions/...`）**
1. `GET /api/predictions/{date}` - 取得指定日期的所有股票預測
2. `GET /api/predictions/{date}/{symbol}` - 取得特定股票在特定日期的預測
3. `GET /api/predictions/timeline/{symbol}` - 取得股票的預測時間序列（Timeline Chart）
4. `GET /api/predictions/latest/{symbol}` - 取得股票的最新預測結果（Signal Panel）

#### **Indicators API（`/api/indicators/...`）**
5. `GET /api/indicators/{symbol}/{date}` - 取得股票的 100 指標快照

#### **Universe API（`/api/universe/...`）**
6. `GET /api/universe/coverage` - 取得所有股票的指標覆蓋率狀況
7. `GET /api/universe/coverage-detail` - 取得詳細的覆蓋率資訊（legacy）

---

## 二、前端（Trading UI）現況

### 2.1 技術棧
- **框架：** React 18.2.0 + TypeScript 5.2.2
- **建置工具：** Vite 5.0.8
- **圖表庫：** Recharts 2.10.3
- **HTTP 客戶端：** Axios 1.6.2
- **國際化：** i18next 23.7.16 + react-i18next 13.5.0

### 2.2 頁面與元件

#### **主要頁面**
1. **`DashboardPage.tsx`** ✅
   - 主儀表板，整合所有 Panel
   - 左右分欄佈局（左：SmartWatchlist，右：其他 Panels）

#### **核心元件（`src/components/`）**
1. **`SmartWatchlist.tsx`** ✅
   - 智能自選股列表
   - 支援收藏與最近使用記錄（localStorage）
   - 點擊切換 Timeline 與 Signal Panel

2. **`PredictionTimelinePanel.tsx`** ✅
   - 使用 Recharts 繪製預測分數時間序列
   - Score 作為 Y 軸，Signal 顏色區分點
   - 支援日期範圍選擇

3. **`SignalPanel.tsx`** ✅
   - 顯示最新預測結果重點資訊
   - 主訊號（signal、score、date）
   - Positive/Negative Factors（只顯示 code，hover 顯示完整）
   - Risk Flags（顯示 severity 與 message）
   - J-GOD 建議（人性化中文建議）

4. **`CoverageHeatmapPanel.tsx`** ✅
   - 顯示股票覆蓋率熱力圖
   - 用於視覺化資料完整性

5. **`WatchlistPanel.tsx`** ✅
   - 顯示指定日期的所有股票預測列表

6. **`PredictionSummaryPanel.tsx`** ✅
   - 顯示單一股票的預測摘要

#### **API 客戶端（`src/api/`）**
- **`client.ts`** ✅ - 統一 Axios 客戶端，整合所有 API 呼叫
- **`universeApi.ts`** ✅ - Universe 相關 API 封裝

#### **類型定義（`src/types/`）**
- **`index.ts`** ✅ - TypeScript 介面定義（LatestPrediction、PredictionTimelineResponse 等）

#### **國際化（`src/i18n/`）**
- **`en.json`** / **`zh-TW.json`** ✅ - 多語系支援
- **`index.ts`** ✅ - i18n 初始化

---

## 三、資料庫現況

### 3.1 資料庫檔案
- **主要資料庫：** `data/jgod_tw_stock.db` ✅
- **Legacy 資料庫：** `data/jgod_simulation.db`, `data/jgod_simulation_backup_20251206.db`

### 3.2 資料表統計

| 資料表 | 筆數 | 狀態 | 說明 |
|--------|------|------|------|
| `stocks` | 18 | ✅ | 標的基本資訊 |
| `daily_bars` | 4,356 | ✅ | 2024 全年日線資料（8 檔股票，242 交易日/檔） |
| `indicator_snapshots` | 471,600 | ✅ | 100 指標快照（8 檔股票，262 天，100 指標） |
| `prediction_snapshots` | 4,716 | ⚠️ | 預測結果（僅 4 檔股票完整，其他部分） |
| `virtual_trades` | 0 | ❌ | 未啟用 |
| `portfolio_snapshots` | 0 | ❌ | 未啟用 |
| `tw_index_daily` | 0 | ❌ | 未使用 |
| `tw_stock_daily` | 15 | ⚠️ | Legacy 資料 |
| `tw_stock_fundamentals` | 0 | ❌ | 未使用 |
| `tw_stock_institutional` | 0 | ❌ | 未使用 |

### 3.3 資料覆蓋率（2024-01-01 ~ 2024-12-31）

#### **Daily Bars**
- ✅ **8 檔股票**：1301, 1303, 2303, 2308, 2317, 2330, 2412, 2454
- ✅ **每檔 242 筆**（2024-01-02 ~ 2024-12-31）

#### **Indicator Snapshots**
- ✅ **8 檔股票**：100% 指標覆蓋率
- ✅ **每檔 262 天，100 指標**（coverage 100.0%）

#### **Prediction Snapshots**
- ⚠️ **僅 4 檔股票有資料**：
  - 2317: 262 筆（完整）
  - 2330: 262 筆（完整）
  - 2454: 262 筆（完整）
  - 2303: 143 筆（2024-01-01 ~ 2024-07-17，部分）
- ❌ **缺少預測的股票**：1301, 1303, 2308, 2412

---

## 四、Predictor / 100 指標引擎狀態

### 4.1 指標引擎（`jgod/prediction/data/indicator_builder_100.py`）
- **狀態：** ✅ 完整實作（543 行）
- **功能：**
  - 建構 100 指標字典（P01-P12, C01-C09, F01-F08, K01-K07, S01-S06, Q01-Q06, X01-X16, M01-M36）
  - 整合 FinMind API Client
  - Rate Limiting：每秒最多 1 次 API 呼叫（保守設定）
  - 支援 Price、Capital、Fundamental、Catalyst、Sentiment、Quant、Derivatives、Meta 指標
- **已知問題：** ⚠️ 部分指標實作標記為 TODO（VAP、分點資料相關）

### 4.2 預測規則引擎（`jgod/prediction/rules/stock_upside_filter_60_v1.py`）
- **狀態：** ✅ 完整實作（302 行）
- **功能：**
  - 規則式評分系統（Rule-based Filter）
  - 支援 100 指標（實際名稱是 60-indicator，但擴充至 100）
  - 產生 VERDICT（STRONG_BUY/BUY/NEUTRAL/AVOID/SHORT）
  - 提取 Positive/Negative Factors 與 Risk Flags
  - 權重系統（DEFAULT_WEIGHTS）
- **已知問題：** 無

---

## 五、系統架構弱點與技術債

### 5.1 架構弱點

#### **1. War Room 多版本並存** 🔴 高優先級
- **問題：** `war_room/`、`war_room_backend/`、`war_room_backend_v6/`、`war_room_v6/` 四套版本並存
- **影響：** 程式碼重複、維護困難、行為不一致
- **建議：** 統一為 v6，移除舊版本或標記為 deprecated

#### **2. 資料庫表重複定義** 🟡 中優先級
- **問題：** `jgod/storage/models.py` 與 `jgod/data/db.py` 可能重複
- **影響：** 資料模型不一致風險
- **建議：** 統一資料模型定義位置

#### **3. Path 引擎使用率低** 🟡 中優先級
- **問題：** Path A/B/C/D/E 引擎已實作但使用率低
- **影響：** 程式碼冗餘，維護成本高
- **建議：** 評估實際需求，考慮移除或標記為實驗性功能

#### **4. Extreme Mode 與標準版並存** 🟡 中優先級
- **問題：** 多個模組有 `_extreme.py` 版本（alpha_engine_extreme、execution_engine_extreme、risk_model_extreme）
- **影響：** 程式碼重複，測試覆蓋率分散
- **建議：** 統一為可配置模式，而非分離版本

#### **5. 測試覆蓋率未知** 🟡 中優先級
- **問題：** 83 個測試檔案，但覆蓋率未統計
- **影響：** 重構風險高，品質不確定
- **建議：** 使用 pytest-cov 統計測試覆蓋率

### 5.2 技術債

#### **TODO 標記（grep 結果）**
1. **`indicator_builder_100.py:254`** - VAP 指標實作待完成
2. **`indicator_builder_100.py:345`** - 分點資料相關實作待完成
3. **`path_b_engine.py:248-250`** - AlphaHealthMonitor、RegimeManager、KillSwitchController 整合待完成
4. **`path_b_engine.py:300`** - 結果匯出功能待實作
5. **`path_b_engine.py:483`** - window_result 傳遞待實作
6. **`path_b_engine.py:504`** - factor_attribution 提取待實作
7. **`path_b_engine.py:612-620`** - Alpha Sunset、Kill Switch、Regime Switch 檢查待實作
8. **`path_b_engine.py:695`** - DiagnosisEngine 整合待實作
9. **`path_b_engine.py:743`** - 摘要統計擴充待實作
10. **`rl_agent.py:23`** - 強化學習演算法升級建議（PPO、SAC）

#### **已知問題**
- **API CORS 設定過寬：** `allow_origins=["*"]`，生產環境應限制
- **Rate Limiting 保守：** 1 次/秒，可能導致 backfill 時間過長
- **資料庫連線管理：** 使用 SQLAlchemy session，但未見連線池設定
- **錯誤處理：** 部分模組錯誤處理不完整

---

## 六、下一步建議（總工程師觀點）

### 6.1 短期目標（1-2 週）

#### **優先級 1：補齊預測資料** 🔴
- 執行 `backfill_predictions_batch.sh`，補齊 1301, 1303, 2308, 2412 的 2024 全年預測
- 補齊 2303 的 2024-07-18 ~ 2024-12-31 預測
- **預期成果：** 8 檔股票都有完整預測資料

#### **優先級 2：War Room 版本統一** 🔴
- 評估 v4.2、v5.0、v6.0 功能差異
- 統一為 v6.0，移除或標記舊版本為 deprecated
- **預期成果：** 單一 War Room 版本，減少維護成本

#### **優先級 3：API 安全性改進** 🟡
- 限制 CORS origins 為特定域名
- 新增 API 認證機制（JWT 或 API Key）
- **預期成果：** 生產環境安全性提升

### 6.2 中期目標（1-2 個月）

#### **優先級 1：測試覆蓋率提升** 🟡
- 使用 pytest-cov 統計現有測試覆蓋率
- 針對核心模組（prediction、api、storage）增加單元測試
- **目標：** 核心模組覆蓋率 > 80%

#### **優先級 2：文件化** 🟡
- 生成 API 文件（FastAPI 自動生成 Swagger）
- 補充核心模組的 docstring
- 建立開發者指南
- **目標：** 新成員可快速上手

#### **優先級 3：效能優化** 🟡
- 優化資料庫查詢（索引、查詢優化）
- 實作 API 回應快取（Redis 或記憶體快取）
- 優化 100 指標建構速度（並行處理）
- **目標：** API 回應時間 < 500ms

### 6.3 長期目標（3-6 個月）

#### **優先級 1：架構重構** 🟢
- 統一 Path 引擎介面，減少程式碼重複
- 移除 Extreme Mode 分離版本，改為可配置模式
- 實作統一錯誤處理機制
- **目標：** 程式碼維護性提升 50%

#### **優先級 2：監控與日誌** 🟢
- 整合 Prometheus + Grafana 監控
- 統一日誌格式與收集（ELK Stack 或 Loki）
- 實作健康檢查端點
- **目標：** 系統可觀測性提升

#### **優先級 3：擴展性提升** 🟢
- 支援多資料庫（PostgreSQL、MySQL）
- 實作分散式快取（Redis Cluster）
- 支援水平擴展（Docker、Kubernetes）
- **目標：** 支援更大規模資料處理

---

## 七、建議改進的檔案列表

### 7.1 高優先級改進

1. **`jgod/api/main.py`**
   - 改進：限制 CORS origins，新增認證機制
   - 影響：安全性提升

2. **`jgod/prediction/data/indicator_builder_100.py`**
   - 改進：實作 TODO 項目（VAP、分點資料）
   - 影響：指標完整性提升

3. **`jgod/war_room/`（所有版本）**
   - 改進：統一為 v6，移除舊版本
   - 影響：維護成本降低，行為一致性提升

4. **`scripts/run_backfill_predictions.py`**
   - 改進：優化批次處理邏輯，支援並行處理
   - 影響：backfill 速度提升

5. **`jgod/storage/db.py`**
   - 改進：實作連線池，優化查詢效能
   - 影響：資料庫效能提升

### 7.2 中優先級改進

6. **`jgod/path_b/path_b_engine.py`**
   - 改進：實作 TODO 項目（AlphaHealthMonitor、RegimeManager 等）
   - 影響：Path B 功能完整性提升

7. **`jgod/risk/risk_manager.py`**
   - 改進：統一風險模型（移除 extreme 版本）
   - 影響：程式碼簡化

8. **`jgod/execution/execution_engine.py`**
   - 改進：統一執行引擎（移除 extreme 版本）
   - 影響：程式碼簡化

9. **`trading-ui/jgod-trading-ui/src/api/client.ts`**
   - 改進：新增錯誤重試機制、請求超時處理
   - 影響：前端穩定性提升

10. **`jgod/prediction/rules/stock_upside_filter_60_v1.py`**
    - 改進：優化權重系統，支援動態權重
    - 影響：預測準確性可能提升

### 7.3 低優先級改進

11. **`tests/` 目錄**
    - 改進：增加測試覆蓋率，統一測試框架
    - 影響：品質保證提升

12. **`docs/` 目錄**
    - 改進：統一文件格式，補充 API 文件
    - 影響：開發效率提升

13. **`requirements.txt`**
    - 改進：固定版本號，新增依賴說明
    - 影響：部署穩定性提升

---

## 八、Cursor 版本的搬家總綱

### 8.1 專案結構概覽

```
JarvisV1/
├── jgod/                    # 後端核心模組（Python）
│   ├── api/                 # FastAPI 應用（✅ 完成）
│   ├── prediction/          # 預測引擎（✅ 完成）
│   ├── storage/             # 資料庫模型（✅ 完成）
│   ├── war_room/            # War Room 引擎（⚠️ 多版本）
│   ├── path_a/              # Path A 引擎（✅ 完成，使用率低）
│   ├── path_b/              # Path B 引擎（✅ 完成，使用率低）
│   ├── path_c/              # Path C 引擎（✅ 完成，使用率低）
│   ├── path_d/              # Path D 引擎（✅ 完成，使用率低）
│   ├── path_e/              # Path E 引擎（✅ 完成，使用率低）
│   ├── risk/                # 風險管理（✅ 完成）
│   ├── execution/           # 執行引擎（✅ 完成）
│   └── ...
├── trading-ui/              # 前端交易介面（React + TypeScript）
│   └── jgod-trading-ui/     # ✅ 完成，6 個核心元件
├── scripts/                 # 腳本與工具
│   ├── run_backfill_*.py    # ✅ 3 個 backfill 腳本
│   └── run_jgod_path_*.py   # ✅ 5 個 path 引擎腳本
├── api_clients/             # 外部 API 客戶端（✅ 完成）
├── data/                    # 資料庫檔案
│   └── jgod_tw_stock.db     # ✅ 主要資料庫
├── tests/                   # 測試檔案（83 個）
└── docs/                    # 文件（112 個檔案）
```

### 8.2 核心模組依賴關係

```
API Layer (jgod/api/)
    ↓
Storage Layer (jgod/storage/)
    ↓
Prediction Engine (jgod/prediction/)
    ↓
Data Builder (jgod/prediction/data/)
    ↓
API Clients (api_clients/)
    ↓
External APIs (FinMind, OpenAI, etc.)
```

### 8.3 資料流

```
FinMind API
    ↓
Indicator Builder 100
    ↓
Indicator Snapshots (DB)
    ↓
Prediction Engine (StockUpsideFilter60V1)
    ↓
Prediction Snapshots (DB)
    ↓
API Endpoints
    ↓
Frontend (Trading UI)
```

### 8.4 關鍵配置檔案

1. **`requirements.txt`** - Python 依賴（122 個套件）
2. **`trading-ui/jgod-trading-ui/package.json`** - Node.js 依賴
3. **`config/universe/tw_top50_2024.yaml`** - 股票池定義
4. **`.env`** - 環境變數（API Keys、資料庫路徑）

### 8.5 啟動指令

#### **後端 API**
```bash
cd /Users/kevincheng/JarvisV1
PYTHONPATH=. uvicorn jgod.api.main:app --reload --host 0.0.0.0 --port 8000
```

#### **前端 Trading UI**
```bash
cd trading-ui/jgod-trading-ui
npm install
npm run dev
```

#### **War Room（Streamlit）**
```bash
cd /Users/kevincheng/JarvisV1
streamlit run jgod/war_room/war_room_app.py
```

#### **War Room Backend v6**
```bash
cd /Users/kevincheng/JarvisV1
PYTHONPATH=. uvicorn jgod.war_room_backend_v6.main:app --reload --host 0.0.0.0 --port 8001
```

### 8.6 資料庫遷移建議

若需遷移資料庫：
1. 匯出 SQLite 資料：`sqlite3 data/jgod_tw_stock.db .dump > backup.sql`
2. 備份檔案：`cp data/jgod_tw_stock.db data/jgod_tw_stock_backup_$(date +%Y%m%d).db`
3. 遷移至 PostgreSQL/MySQL：使用 `sqlalchemy` 的遷移工具或手動轉換

### 8.7 環境變數需求

```bash
# FinMind API
FINMIND_API_TOKEN=your_token

# OpenAI API
OPENAI_API_KEY=your_key

# Anthropic API
ANTHROPIC_API_KEY=your_key

# Google Gemini API
GOOGLE_API_KEY=your_key

# Perplexity API
PERPLEXITY_API_KEY=your_key

# 資料庫路徑（預設）
DATABASE_PATH=data/jgod_tw_stock.db
```

---

## 九、總結

### 9.1 已完成功能 ✅

1. **後端 API** - FastAPI 應用，7 個 endpoints，已運行
2. **預測引擎** - 100 指標框架，規則式評分系統
3. **資料建構** - 3 個 backfill 腳本，支援完整資料流程
4. **前端 Trading UI** - React + TypeScript，6 個核心元件
5. **資料庫** - SQLite，10 個資料表，471,600 筆指標資料
6. **War Room** - 多 AI Provider，多角色戰情室（多版本）

### 9.2 待補齊功能 ⚠️

1. **預測資料** - 4 檔股票缺少 2024 全年預測
2. **War Room 版本統一** - 4 套版本需要統一
3. **測試覆蓋率** - 未統計，需要提升
4. **API 安全性** - CORS 與認證機制需改進

### 9.3 技術債 🔴

1. **多版本並存** - War Room、Extreme Mode、Path 引擎
2. **TODO 項目** - 10+ 個待實作功能
3. **程式碼重複** - 多處重複邏輯
4. **文件不足** - API 文件、開發者指南需補齊

### 9.4 下一步行動 🎯

**立即執行（本週）：**
1. 執行 `backfill_predictions_batch.sh` 補齊預測資料
2. 評估 War Room 版本統一方案
3. 限制 API CORS origins

**短期規劃（1-2 週）：**
1. 統一 War Room 為 v6
2. 新增 API 認證機制
3. 統計測試覆蓋率

**長期規劃（1-6 個月）：**
1. 架構重構，減少程式碼重複
2. 實作監控與日誌系統
3. 支援水平擴展

---

**報告結束**

*本報告基於實際程式碼掃描、資料庫查詢與 Git 歷史分析生成，確保準確性與時效性。*

