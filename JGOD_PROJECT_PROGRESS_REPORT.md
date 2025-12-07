# J-GOD / JarvisV1 專案完整進度報告

生成時間：2025-01-06

---

## 一、J-GOD 量化系統模組架構

### 1.1 Data Feed 模組

**位置：** `jgod/market/`, `api_clients/`

**主要檔案與功能：**

- `jgod/market/data_loader.py`
  - 市場資料載入器
  - 整合 FinMind 和 yfinance
  - 載入台股/美股歷史資料

- `jgod/market/indicators.py`
  - 技術指標計算
  - MA、RSI、MACD 等指標

- `jgod/market/price_cache.py`
  - 價格快取機制
  - 減少 API 呼叫次數

- `jgod/market/market_status.py`
  - 市場開盤狀態判斷
  - 交易時間檢測

- `api_clients/finmind_client.py`
  - FinMind API 客戶端封裝
  - 含 RateLimiter 節流機制（每小時 6000 次，每分鐘 80 次）
  - 支援多種資料類型：日線、三大法人、融資券、財報等

- `jgod/data/finmind_loader.py`
  - FinMind 資料載入輔助函數

### 1.2 Factor Engine 模組

**位置：** `jgod/alpha_engine/`, `jgod/factor/`

**主要檔案與功能：**

- `jgod/alpha_engine/alpha_engine.py`
  - Alpha 因子引擎主程式
  - 整合多種 Alpha 因子

- `jgod/alpha_engine/alpha_engine_extreme.py`
  - Extreme 版本 Alpha 引擎

- `jgod/alpha_engine/factor_base.py`
  - 因子基類定義

- `jgod/alpha_engine/flow_factor.py`
  - 資金流動因子

- `jgod/alpha_engine/inertia_factor.py`
  - 慣性因子

- `jgod/alpha_engine/micro_momentum_factor.py`
  - 微觀動能因子

- `jgod/alpha_engine/reversion_factor.py`
  - 均值回歸因子

- `jgod/alpha_engine/value_quality_factor.py`
  - 價值品質因子

- `jgod/alpha_engine/divergence_factor.py`
  - 背離因子

- `jgod/factor/factor_engine.py`
  - 因子引擎核心邏輯

### 1.3 Prediction 模組

**位置：** `jgod/prediction/`

**主要檔案與功能：**

- `jgod/prediction/prediction_engine.py`
  - 規則型預測引擎
  - 預測明日可能漲/跌最多的股票
  - 支援 top movers 預測

- `jgod/prediction/feature_builder.py`
  - 特徵建構器
  - 建構股票特徵 DataFrame
  - 計算技術指標特徵

- `jgod/prediction/ranking.py`
  - 排名引擎
  - 多因子排名
  - 動態權重調整

- `jgod/prediction/data/indicator_builder_100.py`
  - 100 指標建構器
  - P 系列：價量技術指標（12 個）
  - C 系列：籌碼指標（9 個）
  - F 系列：財報指標（8 個）
  - K/S/Q/X/M 系列：其他指標（預留）
  - **FinMind API 節流機制**：每秒最多 1 次請求

- `jgod/prediction/rules/stock_upside_filter_60_v1.py`
  - StockUpsideFilter60V1 評分系統
  - 使用 60 指標框架評估股票上漲潛力
  - 產生 verdict：STRONG_BUY / BUY / NEUTRAL / AVOID / SHORT

### 1.4 Path 模組（多路徑實驗）

**Path A - 基礎回測引擎**

**位置：** `jgod/path_a/`

- `path_a_engine.py` - Path A 引擎主程式
- `path_a_backtest.py` - 回測邏輯
- `finmind_data_loader.py` - FinMind 資料載入器

**Path B - Walk-Forward 引擎**

**位置：** `jgod/path_b/`

- `path_b_engine.py` - Path B 引擎
- 實作 walk-forward 驗證機制

**Path C - 情境實驗引擎**

**位置：** `jgod/path_c/`

- `path_c_engine.py` - Path C 引擎
- `path_c_types.py` - 類型定義
- `scenario_presets.py` - 情境預設值

**Path D - 強化學習引擎**

**位置：** `jgod/path_d/`

- `path_d_engine.py` - Path D 引擎
- `rl_agent.py` - RL 智能體
- `rl_state_encoder.py` - 狀態編碼器
- `rl_reward.py` - 獎勵函數
- `rl_training_loop.py` - 訓練迴圈

**Path E - 即時交易引擎**

**位置：** `jgod/path_e/`

- `live_trading_engine.py` - 即時交易引擎
- `live_signal_engine.py` - 即時訊號引擎
- `live_data_feed.py` - 即時資料流
- `broker_client.py` - 券商客戶端
- `order_planner.py` - 訂單規劃器
- `portfolio_state.py` - 組合狀態管理
- `risk_guard.py` - 風險守衛

### 1.5 Risk 模組

**位置：** `jgod/risk/`

**主要檔案與功能：**

- `risk_engine.py`
  - 風險引擎核心
  - 風險評估與控制

- `risk_manager.py`
  - 風險管理器
  - 控制最大虧損、最大持倉

- `portfolio.py`
  - 投資組合管理器
  - 追蹤多標的持倉

- `portfolio_risk.py`
  - 組合風險評估

- `sizing.py`
  - 部位大小計算器
  - 根據風險計算適當持倉

- `risk_model.py` / `risk_model_extreme.py`
  - 風險模型
  - Extreme 版本風險模型

- `risk_factors.py`
  - 風險因子定義

- `exposure_schema.py`
  - 風險暴露結構定義

### 1.6 Optimizer 模組

**位置：** `jgod/optimizer/`

**主要檔案與功能：**

- `optimizer_core.py` / `optimizer_core_v2.py`
  - 優化器核心邏輯
  - V2 版本優化器

- `optimizer_config.py`
  - 優化器配置

- `optimizer_constraints.py`
  - 優化約束條件

- `optimizer_types.py`
  - 優化器類型定義

### 1.7 War Room 模組

**位置：** `jgod/war_room/`, `jgod/war_room_backend/`, `jgod/war_room_backend_v6/`

**主要檔案與功能：**

- `jgod/war_room/` (48 個檔案)
  - War Room 核心引擎
  - AI 議會機制
  - 多 AI 提供者整合

- `jgod/war_room_backend_v6/`
  - War Room Backend v6.0
  - FastAPI + WebSocket
  - 即時串流輸出

- `jgod/war_room_backend/`
  - War Room Backend v5.0
  - FastAPI 版本

### 1.8 API 模組

**位置：** `jgod/api/`

**主要檔案與功能：**

- `jgod/api/main.py`
  - FastAPI 主應用程式
  - 整合所有路由

- `jgod/api/routers/predictions.py`
  - 預測相關 API 路由

- `jgod/api/routers/indicators.py`
  - 指標相關 API 路由

- `jgod/api/routers/universe.py`
  - 股票池與覆蓋率 API 路由

### 1.9 Storage 模組

**位置：** `jgod/storage/`

**主要檔案與功能：**

- `models.py`
  - SQLAlchemy ORM 模型定義
  - Stock, DailyBar, IndicatorSnapshot, PredictionSnapshot 等

- `db.py`
  - 資料庫連接管理
  - Session 管理
  - 資料庫初始化

### 1.10 Execution 模組

**位置：** `jgod/execution/`

**主要檔案與功能：**

- `virtual_broker.py`
  - 虛擬券商
  - 模擬交易執行

- `trade_recorder.py`
  - 交易記錄器
  - 記錄到 CSV 和 SQLite

- `slippage.py`
  - 滑價模型
  - 模擬實際交易滑價

- `execution_engine.py` / `execution_engine_extreme.py`
  - 執行引擎
  - Extreme 版本

- `cost_model.py`
  - 成本模型
  - 手續費計算

- `broker_adapter.py`
  - 券商適配器

---

## 二、資料庫狀態

### 2.1 資料庫檔案

**位置：** `data/jgod_tw_stock.db`

**資料庫類型：** SQLite 3

### 2.2 資料表結構

#### `stocks` - 標的基本資訊表
- **欄位：** id, symbol (unique), name_zh, name_en, sector, is_active, created_at, updated_at
- **功能：** 儲存股票基本資訊
- **目前資料：** 8 檔股票

#### `daily_bars` - 歷史日線資料表
- **欄位：** id, symbol, date, open, high, low, close, volume, turnover, adjusted_close, source, created_at, updated_at
- **功能：** 儲存歷史日 K 線資料（OHLCV）
- **唯一約束：** (symbol, date)
- **目前資料：** 1,936 筆，8 檔股票
- **日期範圍：** 2024-01-02 ~ 2024-12-31（242 個交易日）

#### `indicator_snapshots` - 100 指標快照表
- **欄位：** id, symbol, date, indicator_code, raw_value, normalized_value, weight, category, data_source, status, created_at, updated_at
- **功能：** 儲存 100 指標框架的指標快照
- **唯一約束：** (symbol, date, indicator_code)
- **目前資料：** 190,900 筆，8 檔股票
- **日期範圍：** 2024-01-01 ~ 2024-12-31（262 個日期）

#### `prediction_snapshots` - 選股結果快照表
- **欄位：** id, symbol, date, score, total_score, signal, verdict, positive_factors_json, negative_factors_json, risk_flags_json, meta_json, positive_indicators, negative_indicators, raw_payload, created_at, updated_at
- **功能：** 儲存預測結果，包含分數、訊號、factors、risk flags
- **唯一約束：** (symbol, date)
- **目前資料：** 929 筆，4 檔股票
- **日期範圍：** 2024-01-01 ~ 2024-12-31（262 個日期，僅部分股票）

#### `virtual_trades` - 模擬交易紀錄表
- **欄位：** id, symbol, open_datetime, close_datetime, side, open_price, close_price, quantity, pnl, pnl_pct, mode, engine, strategy_tag, meta_json, created_at, updated_at
- **功能：** 儲存模擬交易記錄
- **模式：** DRY_RUN / PAPER（LIVE 已停用）

#### `portfolio_snapshots` - 組合淨值快照表
- **欄位：** id, date, snapshot_time, equity_curve, cash, positions_value, max_drawdown, sharpe, mode, engine, created_at, updated_at
- **功能：** 儲存投資組合淨值快照
- **唯一約束：** (snapshot_time, mode, engine)

#### 其他資料表（Legacy/備用）
- `tw_index_daily` - 台股指數日線（Legacy）
- `tw_stock_daily` - 台股日線（Legacy）
- `tw_stock_fundamentals` - 台股財報（Legacy）
- `tw_stock_institutional` - 台股三大法人（Legacy）

### 2.3 股票資料覆蓋率

| Symbol | Name | Daily Bars | Indicators | Predictions | 完整度 |
|--------|------|-----------|-----------|-------------|--------|
| 2330 | 台積電 | 242 dates<br>(2024-01-02 ~ 2024-12-31) | 262 dates<br>(2024-01-01 ~ 2024-12-31)<br>26,200 筆 | ✅ 262 dates<br>(2024-01-01 ~ 2024-12-31) | ✅ 完整 |
| 2454 | 聯發科 | 242 dates<br>(2024-01-02 ~ 2024-12-31) | 262 dates<br>(2024-01-01 ~ 2024-12-31)<br>26,200 筆 | ✅ 262 dates<br>(2024-01-01 ~ 2024-12-31) | ✅ 完整 |
| 2317 | 鴻海 | 242 dates<br>(2024-01-02 ~ 2024-12-31) | 262 dates<br>(2024-01-01 ~ 2024-12-31)<br>26,200 筆 | ✅ 262 dates<br>(2024-01-01 ~ 2024-12-31) | ✅ 完整 |
| 2303 | 聯電 | 242 dates<br>(2024-01-02 ~ 2024-12-31) | 247 dates<br>(2024-01-01 ~ 2024-12-10)<br>24,700 筆 | ⚠️ 143 dates<br>(2024-01-01 ~ 2024-07-17) | ⚠️ 部分 |
| 1301 | 台塑 | 242 dates<br>(2024-01-02 ~ 2024-12-31) | 262 dates<br>(2024-01-01 ~ 2024-12-31)<br>26,200 筆 | ❌ 0 dates | ❌ 缺少 |
| 1303 | 南亞 | 242 dates<br>(2024-01-02 ~ 2024-12-31) | 144 dates<br>(2024-01-01 ~ 2024-07-18)<br>14,400 筆 | ❌ 0 dates | ❌ 缺少 |
| 2308 | 台達電 | 242 dates<br>(2024-01-02 ~ 2024-12-31) | 262 dates<br>(2024-01-01 ~ 2024-12-31)<br>26,200 筆 | ❌ 0 dates | ❌ 缺少 |
| 2412 | 中華電 | 242 dates<br>(2024-01-02 ~ 2024-12-31) | 262 dates<br>(2024-01-01 ~ 2024-12-31)<br>26,200 筆 | ❌ 0 dates | ❌ 缺少 |

**完整資料股票（3 檔）：**
- ✅ 2330（台積電）
- ✅ 2454（聯發科）
- ✅ 2317（鴻海）

**部分資料股票（1 檔）：**
- ⚠️ 2303（聯電）- 有 predictions 但日期較少

**缺少預測資料（4 檔）：**
- ❌ 1301, 1303, 2308, 2412 - 有 daily_bars 和 indicators，但缺少 predictions

---

## 三、Backfill 腳本

### 3.1 `scripts/run_backfill_raw_data.py`

**功能：** 回填原始日線資料（daily_bars）

**參數：**
- `--universe-file` (str, optional) - Universe YAML 檔案路徑，預設：`config/universe/tw_top50_2024.yaml`
- `--symbols` (str, optional) - 逗號分隔的股票代號，例如：`2330,2454,2317`。若提供，會覆蓋 universe-file
- `--start-date` (str) - 起始日期（YYYY-MM-DD），預設：`2024-01-01`
- `--end-date` (str) - 結束日期（YYYY-MM-DD），預設：`2024-12-31`

**工作流程：**
1. **Input：** Universe 檔案或 symbols 列表 + 日期範圍
2. **Process：**
   - 同步 stocks 表
   - 對每個 symbol，從 FinMind 取得日線資料
   - 寫入 daily_bars 表（去重處理）
3. **Output：** daily_bars 表中的歷史資料

**使用範例：**
```bash
PYTHONPATH=. python scripts/run_backfill_raw_data.py --symbols 2330,2454 --start-date 2024-01-01 --end-date 2024-12-31
```

### 3.2 `scripts/run_backfill_indicators_100.py`

**功能：** 回填 100 指標快照（indicator_snapshots）

**參數：**
- `--universe-file` (str, optional) - Universe YAML 檔案路徑
- `--symbols` (str, optional) - 逗號分隔的股票代號，覆蓋 universe-file
- `--start-date` (str) - 起始日期，預設：`2024-01-01`
- `--end-date` (str) - 結束日期，預設：`2024-12-31`
- `--force` (flag) - 強制重建已存在的指標快照

**工作流程：**
1. **Input：** Symbol 列表 + 日期範圍
2. **Process：**
   - 使用 `StockIndicatorBuilder100` 建構 100 指標
   - 對每個 symbol × date，呼叫 `build_indicators()`
   - 指標建構過程中會自動應用 FinMind API 節流（每秒 1 次）
   - 將指標寫入 indicator_snapshots 表（P01-P12, C01-C09, F01-F08, K/S/Q/X/M 系列）
3. **Output：** indicator_snapshots 表中的指標快照

**使用範例：**
```bash
PYTHONPATH=. python scripts/run_backfill_indicators_100.py --symbols 2330 --start-date 2024-01-01 --end-date 2024-12-31
```

### 3.3 `scripts/run_backfill_predictions.py`

**功能：** 回填預測結果（prediction_snapshots）

**參數：**
- `--start-date` (str) - 起始日期，預設：`2024-01-01`
- `--end-date` (str) - 結束日期，預設：`2024-12-31`
- `--symbols` (str, optional) - 逗號分隔的股票代號。若未提供，使用資料庫中所有 active stocks
- `--force` (flag) - 強制重建已存在的預測
- `--min-indicators` (int) - 最少指標數量要求，預設：90（目前不使用作為跳過條件）

**工作流程：**
1. **Input：** Symbol 列表（或從 DB 取得）+ 日期範圍
2. **Process：**
   - 對每個 symbol × date：
     - 檢查資料可用性（`check_data_availability()`）
     - 新規則：只要有 indicators（>0），就允許預測（不強制要求 daily_bars）
     - 從 indicator_snapshots 載入指標資料
     - 使用 `StockUpsideFilter60V1.evaluate()` 產生預測結果
     - 將結果寫入 prediction_snapshots 表
       - score, signal, verdict
       - positive_factors_json, negative_factors_json, risk_flags_json
3. **Output：** prediction_snapshots 表中的預測結果

**使用範例：**
```bash
PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols 2330,2454 --start-date 2024-01-01 --end-date 2024-12-31
```

### 3.4 其他輔助腳本

- `scripts/check_indicator_gaps.py` - 檢查指標資料缺口
- `scripts/debug_check_db.py` - 資料庫檢查工具

---

## 四、API Endpoints

### 4.1 Predictions API (`/api/predictions/...`)

**Base Path：** `/api/predictions/`

#### `GET /api/predictions/{date}`
- **用途：** 取得指定日期的所有股票預測
- **參數：**
  - Path: `date` (str, YYYY-MM-DD)
  - Query: `universe` (str, optional) - Universe 名稱，預設：`tw_top50_2024`
- **回傳：** `Prediction[]` 陣列
- **用途：** 給前端 Watchlist Panel 使用

#### `GET /api/predictions/{date}/{symbol}`
- **用途：** 取得特定股票在特定日期的預測
- **參數：**
  - Path: `date` (str, YYYY-MM-DD), `symbol` (str)
  - Query: `include_payload` (bool, optional)
- **回傳：** 單一 Prediction 物件，包含 total_score, verdict, positive_indicators, negative_indicators

#### `GET /api/predictions/timeline/{symbol}`
- **用途：** 取得股票的預測時間序列
- **參數：**
  - Path: `symbol` (str)
  - Query: `start_date` (str, YYYY-MM-DD), `end_date` (str, YYYY-MM-DD)
- **回傳：** `PredictionTimelineResponse`
  - symbol, start_date, end_date, points[]
  - 每個 point: date, score, signal
- **用途：** 給前端 Timeline Chart 使用

#### `GET /api/predictions/latest/{symbol}`
- **用途：** 取得股票的最新預測結果
- **參數：**
  - Path: `symbol` (str)
  - Query: `date` (str, optional) - 若提供，取 <= 該日期的最新一筆；若未提供，取 DB 中最大日期
- **回傳：** `LatestPrediction`
  - symbol, date, score, signal
  - positive_factors[], negative_factors[], risk_flags[]
- **用途：** 給前端 Signal Panel 使用

### 4.2 Indicators API (`/api/indicators/...`)

#### `GET /api/indicators/{symbol}/{date}`
- **用途：** 取得股票的 100 指標快照
- **參數：**
  - Path: `symbol` (str), `date` (str, YYYY-MM-DD)
- **回傳：** `IndicatorSnapshot`
  - symbol, date, indicators[]
  - 每個 indicator: indicator_code, category, raw_value, normalized_value, weight, status
- **用途：** 給前端 Indicator Radar/Heatmap 使用

### 4.3 Universe API (`/api/universe/...`)

#### `GET /api/universe/coverage`
- **用途：** 取得所有股票的指標覆蓋率狀況
- **參數：**
  - Query: `start_date` (date, required), `end_date` (date, required)
- **回傳：** `CoverageSummary`
  - start_date, end_date, total_symbols, completed_symbols, average_coverage
  - items[]: symbol, name, bar_days, indicator_days, coverage (0~1)
- **用途：** 給前端 Coverage Heatmap Panel 使用

#### `GET /api/universe/coverage-detail`
- **用途：** 取得詳細的覆蓋率資訊（legacy endpoint）
- **參數：**
  - Query: `universe` (str, optional), `from_date` (str, optional), `to_date` (str, optional)
- **回傳：** `CoverageResponse`
  - symbols[], dates[], coverage[]

---

## 五、前端 trading-ui 已完成的畫面與元件

### 5.1 DashboardPage 結構

**檔案：** `trading-ui/jgod-trading-ui/src/pages/DashboardPage.tsx`

**版面配置：**
- **左側（固定寬度 256px）：** SmartWatchlist
- **右側（自適應寬度）：**
  - 上方：WatchlistPanel + PredictionSummaryPanel（並排）
  - 中間：CoverageHeatmapPanel
  - 下方：PredictionTimelinePanel
  - 最下方：SignalPanel

**State 管理：**
- `selectedDate` - 選中的日期
- `predictions` - 預測列表
- `coverage` - 覆蓋率資料
- `timelineSymbol` - 目前選擇的股票（初始："2330"）

### 5.2 核心面板說明

#### SmartWatchlist (`src/components/SmartWatchlist.tsx`)
- **用途：** 智能自選股列表，讓使用者選擇要查看的股票
- **資料來源：**
  - `fetchUniverseStocks()` - 從 `/api/universe/coverage` endpoint 取得股票列表
  - localStorage - 儲存收藏和最近使用記錄
- **功能：**
  - 收藏功能（星星按鈕）
  - 最近使用記錄（最多 20 個）
  - 智能排序：收藏 → 最近使用 → 全部股票
- **互動：** 點擊股票 → 觸發 `onSelectSymbol()` → 更新 Dashboard 的 `timelineSymbol`

#### PredictionTimelinePanel (`src/components/PredictionTimelinePanel.tsx`)
- **用途：** 顯示股票預測分數的時間序列折線圖
- **資料來源：**
  - `api.getPredictionTimeline({ symbol, startDate, endDate })`
  - 呼叫 `/api/predictions/timeline/{symbol}` endpoint
- **功能：**
  - 使用 Recharts 繪製折線圖
  - Signal-based 顏色編碼（點顏色根據 signal）
  - 自訂 Tooltip 顯示日期、分數、訊號
  - 300px 高度，響應式寬度
- **互動：** 隨 `timelineSymbol` 自動更新

#### SignalPanel (`src/components/SignalPanel.tsx`)
- **用途：** 顯示最新預測結果的重點資訊
- **資料來源：**
  - `api.getLatestPrediction(symbol)`
  - 呼叫 `/api/predictions/latest/{symbol}` endpoint
- **功能：**
  - 主訊號區塊：大字顯示 signal、score、日期
  - Positive/Negative Factors：只顯示 code，hover 顯示完整內容
  - Risk Flags：顯示 message 和 severity
  - J-GOD 建議：人性化中文建議文字
- **互動：** 隨 `timelineSymbol` 自動更新

#### WatchlistPanel (`src/components/WatchlistPanel.tsx`)
- **用途：** 顯示指定日期的所有股票預測列表
- **資料來源：** `api.getPredictions(date)`

#### PredictionSummaryPanel (`src/components/PredictionSummaryPanel.tsx`)
- **用途：** 顯示單一股票的預測摘要
- **資料來源：** 從 predictions 陣列中篩選 selectedSymbol

#### CoverageHeatmapPanel (`src/components/CoverageHeatmapPanel.tsx`)
- **用途：** 顯示股票覆蓋率熱力圖
- **資料來源：** `api.getCoverage()` 或 `api.getCoverageDetail()`

---

## 六、最近 20 個 J-GOD 相關 Commit

1. **8b5f353** (2025-12-07) - Tune FinMind rate limit to 1 call per second
   - 修改模組：`jgod/prediction/data/indicator_builder_100.py`
   - 概要：將 FinMind API rate limit 從每秒 2 次調整為 1 次

2. **6207278** (2025-12-06) - Improve SignalPanel factor rendering and add human-readable advice
   - 修改模組：`trading-ui/jgod-trading-ui/src/components/SignalPanel.tsx`
   - 概要：改進 factor 渲染邏輯，添加人性化建議區塊

3. **a392312** (2025-12-06) - Add latest prediction signals panel to Dashboard
   - 修改模組：`jgod/api/routers/predictions.py`, `trading-ui/jgod-trading-ui/src/components/SignalPanel.tsx`, `trading-ui/jgod-trading-ui/src/api/client.ts`, `trading-ui/jgod-trading-ui/src/types/index.ts`, `trading-ui/jgod-trading-ui/src/pages/DashboardPage.tsx`
   - 概要：新增 latest prediction API endpoint 和 SignalPanel 組件

4. **a80f30b** (2025-12-06) - Add SmartWatchlist component and Dashboard symbol selection
   - 修改模組：`trading-ui/jgod-trading-ui/src/api/universeApi.ts`, `trading-ui/jgod-trading-ui/src/components/SmartWatchlist.tsx`, `trading-ui/jgod-trading-ui/src/pages/DashboardPage.tsx`
   - 概要：建立 SmartWatchlist 組件，實現動態 symbol 選擇

5. **59e9f7f** (2025-12-06) - Upgrade PredictionTimelinePanel into Recharts score timeline chart
   - 修改模組：`trading-ui/jgod-trading-ui/package.json`, `trading-ui/jgod-trading-ui/src/components/PredictionTimelinePanel.tsx`
   - 概要：將 Timeline 面板升級為 Recharts 折線圖

6. **e0c921e** (2025-12-06) - Add PredictionTimelinePanel and API integration for 2330
   - 修改模組：`trading-ui/jgod-trading-ui/src/api/client.ts`, `trading-ui/jgod-trading-ui/src/components/PredictionTimelinePanel.tsx`, `trading-ui/jgod-trading-ui/src/pages/DashboardPage.tsx`, `trading-ui/jgod-trading-ui/src/types/index.ts`
   - 概要：建立 Timeline Panel 組件和 API 整合

7. **8417165** (2025-12-06) - Move timeline endpoint before dynamic routes to avoid routing conflicts
   - 修改模組：`jgod/api/routers/predictions.py`
   - 概要：調整路由順序避免衝突

8. **e13cca5** (2025-12-06) - Change prediction timeline route to /api/predictions/timeline/{symbol}
   - 修改模組：`jgod/api/routers/predictions.py`
   - 概要：修正路由路徑

9. **98dd50a** (2025-12-06) - Fix timeline endpoint: use string dates to avoid routing conflicts
   - 修改模組：`jgod/api/routers/predictions.py`
   - 概要：改用字串日期參數

10. **b1cb48c** (2025-12-06) - Add prediction timeline API endpoint
    - 修改模組：`jgod/api/routers/predictions.py`
    - 概要：新增 timeline API endpoint

11. **2f6f550** (2025-12-06) - Add --symbols option to raw data backfill script
    - 修改模組：`scripts/run_backfill_raw_data.py`
    - 概要：支援命令行指定 symbols

12. **6fd9bda** (2025-12-06) - Update prediction data-check rule: allow prediction without daily bars; indicators-only mode enabled
    - 修改模組：`scripts/run_backfill_predictions.py`
    - 概要：允許 indicators-only 模式，不強制要求 daily_bars

13. **810a03c** (2025-12-06) - Relax insufficient data check in prediction backfill
    - 修改模組：`scripts/run_backfill_predictions.py`
    - 概要：放寬資料檢查條件

14. **74267b0** (2025-12-06) - Adjust FinMind rate limits for 6000/hour plan
    - 修改模組：`api_clients/finmind_client.py`, `jgod/utils/rate_limiter.py`
    - 概要：調整 FinMind rate limiter 設定

15. **770ca83** (2025-12-06) - Align prediction backfill DB with TW stock database
    - 修改模組：`jgod/storage/db.py`
    - 概要：對齊資料庫結構

16. **c037de4** (2025-12-06) - Replace Typer with argparse for prediction backfill CLI
    - 修改模組：`scripts/run_backfill_predictions.py`
    - 概要：將 CLI 框架從 Typer 改為 argparse

17. **739bbb9** (2025-12-06) - Add prediction backfill CLI for J-GOD
    - 修改模組：`jgod/storage/models.py`, `requirements.txt`, `scripts/run_backfill_predictions.py`
    - 概要：新增 prediction backfill 腳本

18. **3b3bd23** (2025-12-05) - chore: auto-sync 2025-12-05 00:15:17 +0800 - J-GOD full sync after Path E v1
    - 修改模組：多個檔案（Makefile, api_clients, configs, 資料檔案等）
    - 概要：自動同步提交，包含 Path E v1 完整同步

19. **b1b80f2** (2025-12-04) - docs(path_c): add TW Path C v1 experiment conclusions
    - 修改模組：文件檔案
    - 概要：添加 Path C 實驗結論文件

20. **27e76f5** (2025-12-04) - docs(path_b): add walk-forward experiments report (v1.0)
    - 修改模組：文件檔案
    - 概要：添加 Path B walk-forward 實驗報告

---

## 七、未提交的變更（Untracked Files）

### 7.1 後端未追蹤檔案

**API 模組（核心功能）：**
- `jgod/api/__init__.py` - API 模組初始化
- `jgod/api/main.py` - FastAPI 主應用程式（**重要：包含所有路由整合**）
- `jgod/api/routers/__init__.py` - Routers 模組初始化
- `jgod/api/routers/indicators.py` - Indicators API 路由（**重要：100 指標快照端點**）
- `jgod/api/routers/universe.py` - Universe API 路由（**重要：覆蓋率端點**）

**儲存模組：**
- `jgod/storage/__init__.py` - Storage 模組初始化

**工具模組：**
- `jgod/utils/__init__.py` - Utils 模組初始化

**資料處理腳本：**
- `scripts/check_indicator_gaps.py` - 檢查指標資料缺口工具
- `scripts/debug_check_db.py` - 資料庫檢查除錯工具
- `scripts/run_backfill_indicators_100.py` - 100 指標回填腳本（**重要：資料建構工具**）

**配置檔案：**
- `config/universe/`（目錄） - Universe 配置檔案目錄
  - 包含 `tw_top50_2024.yaml` 等配置

### 7.2 前端未追蹤檔案

**專案核心檔案：**
- `trading-ui/jgod-trading-ui/index.html` - HTML 入口檔案
- `trading-ui/jgod-trading-ui/src/App.tsx` - React 應用主程式
- `trading-ui/jgod-trading-ui/src/main.tsx` - React 應用入口點
- `trading-ui/jgod-trading-ui/tsconfig.json` - TypeScript 配置
- `trading-ui/jgod-trading-ui/tsconfig.node.json` - Node TypeScript 配置
- `trading-ui/jgod-trading-ui/vite.config.ts` - Vite 建置配置
- `trading-ui/jgod-trading-ui/package-lock.json` - 依賴鎖定檔案

**UI 元件（已實作但未提交）：**
- `trading-ui/jgod-trading-ui/src/components/CoverageHeatmapPanel.tsx` - 覆蓋率熱力圖面板
- `trading-ui/jgod-trading-ui/src/components/PredictionSummaryPanel.tsx` - 預測摘要面板
- `trading-ui/jgod-trading-ui/src/components/WatchlistPanel.tsx` - 自選股列表面板

**國際化：**
- `trading-ui/jgod-trading-ui/src/i18n/`（目錄） - 國際化檔案目錄
  - 包含 `en.json`, `zh-TW.json`, `index.ts`

**文件：**
- `trading-ui/README.md` - 前端專案說明文件

### 7.3 文件與規格

- `spec/JGOD_Backfill_and_Simulation_Data_Spec_v1.md` - 資料回填與模擬規格文件
- `spec/JGOD_Trading_Command_Center_UI_Spec_v1.md` - 交易指揮中心 UI 規格文件

### 7.4 重要未提交檔案說明

**高優先級（核心功能）：**
- ✅ `jgod/api/main.py` - FastAPI 主應用，整合所有 API 路由
- ✅ `jgod/api/routers/indicators.py` - 100 指標 API 端點
- ✅ `jgod/api/routers/universe.py` - 覆蓋率 API 端點
- ✅ `scripts/run_backfill_indicators_100.py` - 100 指標回填腳本
- ✅ `trading-ui/jgod-trading-ui/src/App.tsx` - 前端應用主程式
- ✅ `trading-ui/jgod-trading-ui/src/components/CoverageHeatmapPanel.tsx` - 覆蓋率面板

**中優先級（輔助功能）：**
- `scripts/check_indicator_gaps.py` - 資料檢查工具
- `scripts/debug_check_db.py` - 除錯工具
- `config/universe/` - Universe 配置

**低優先級（配置與文件）：**
- TypeScript 配置檔案
- 國際化檔案
- README 文件

---

## 八、專案整體狀態總結

### 8.1 完成度評估

**後端 API（✅ 高完成度）：**
- ✅ 7 個 API endpoints 已實作並測試
- ✅ 資料庫模型完整定義
- ✅ 資料回填腳本完整可用

**前端 UI（✅ 中高完成度）：**
- ✅ 6 個核心面板已實作
- ✅ Dashboard 基本架構完整
- ✅ 動態 symbol 選擇功能運作
- ⚠️ 部分檔案未提交到 git

**資料完整性（⚠️ 部分完成）：**
- ✅ 8 檔股票的 daily_bars 完整
- ✅ 8 檔股票的 indicators 大部分完整
- ⚠️ 只有 4 檔股票有 predictions（3 檔完整，1 檔部分）

### 8.2 關鍵技術實現

- ✅ FinMind API 節流機制（每秒 1 次，每小時 6000 次）
- ✅ 100 指標框架（P/C/F/K/S/Q/X/M 系列）
- ✅ Prediction Timeline API 與視覺化
- ✅ Latest Prediction API 與 Signal Panel
- ✅ Smart Watchlist 與 localStorage 持久化
- ✅ Indicators-only 模式（不強制 daily_bars）

### 8.3 待完成項目

1. **資料補齊**
   - 為 1301, 1303, 2308, 2412 執行 prediction backfill
   - 為 2303 補齊更多日期

2. **代碼管理**
   - 提交所有未追蹤的核心檔案
   - 建立合理的 commit 結構

3. **功能擴充**
   - 完善 Coverage Heatmap 實作
   - 實作 Indicator Radar 視覺化
   - 擴充股票池（目前 8 檔，規劃 50 檔）

---

**報告生成時間：** 2025-01-06  
**最後提交：** 8b5f353 - Tune FinMind rate limit to 1 call per second  
**Git 狀態：** 已同步到遠端（origin/main），但有大量未追蹤檔案

