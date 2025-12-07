# J-GOD 股神作戰系統進度總結 v2

生成時間：2025-01-06  
資料來源：實際程式碼、資料庫結構、Git 歷史

---

## (一) 資料層現況

### 1.1 資料庫檔案

**主要資料庫：** `data/jgod_tw_stock.db`

**其他資料庫檔案（Legacy/備用）：**
- `data/jgod_simulation.db`
- `data/jgod_simulation_backup_20251206.db`

### 1.2 主要資料表

根據 `jgod/storage/models.py` 定義，`jgod_tw_stock.db` 包含以下主要資料表：

1. **stocks** - 標的基本資訊表（8 個欄位）
   - symbol, name_zh, name_en, sector, is_active 等

2. **daily_bars** - 歷史日線資料表（13 個欄位）
   - symbol, date, open, high, low, close, volume, turnover 等

3. **indicator_snapshots** - 100 指標快照表（12 個欄位）
   - symbol, date, indicator_code, raw_value, normalized_value, weight, category 等

4. **prediction_snapshots** - 選股結果快照表（16 個欄位）
   - symbol, date, score, signal, verdict, positive_factors_json, negative_factors_json, risk_flags_json 等

5. **virtual_trades** - 模擬交易紀錄表（16 個欄位）
   - symbol, open_datetime, close_datetime, side, pnl, mode, engine 等

6. **portfolio_snapshots** - 組合淨值快照表（12 個欄位）
   - date, snapshot_time, equity_curve, cash, max_drawdown, sharpe 等

### 1.3 2024 全年 Daily Bars 資料

**所有 8 檔股票都有完整資料：**
- 1301: 242 筆 (2024-01-02 ~ 2024-12-31)
- 1303: 242 筆 (2024-01-02 ~ 2024-12-31)
- 2303: 242 筆 (2024-01-02 ~ 2024-12-31)
- 2308: 242 筆 (2024-01-02 ~ 2024-12-31)
- 2317: 242 筆 (2024-01-02 ~ 2024-12-31)
- 2330: 242 筆 (2024-01-02 ~ 2024-12-31)
- 2412: 242 筆 (2024-01-02 ~ 2024-12-31)
- 2454: 242 筆 (2024-01-02 ~ 2024-12-31)

**狀態：** ✅ 8 檔股票都有完整的 242 個交易日資料

### 1.4 100 指標覆蓋率（Indicator Snapshots）

**所有 8 檔股票都有 100% 指標覆蓋率：**
- 1301: 262 天, 100 指標, coverage 100.0%
- 1303: 262 天, 100 指標, coverage 100.0%
- 2303: 262 天, 100 指標, coverage 100.0%
- 2308: 262 天, 100 指標, coverage 100.0%
- 2317: 262 天, 100 指標, coverage 100.0%
- 2330: 262 天, 100 指標, coverage 100.0%
- 2412: 262 天, 100 指標, coverage 100.0%
- 2454: 262 天, 100 指標, coverage 100.0%

**狀態：** ✅ 所有股票都有完整的 100 指標覆蓋率（262 個日期）

### 1.5 Prediction Snapshots 預測資料

**只有 4 檔股票有預測資料：**
- 2303: 143 筆
- 2317: 262 筆
- 2330: 262 筆
- 2454: 262 筆

**缺少預測的股票：** 1301, 1303, 2308, 2412

**狀態：** ⚠️ 僅 4 檔股票有預測資料（3 檔完整，1 檔部分）

---

## (二) Backfill 腳本現況

### 2.1 資料建構腳本清單

**scripts/ 目錄下的 Backfill 腳本：**
- `scripts/run_backfill_raw_data.py`
- `scripts/run_backfill_indicators_100.py`
- `scripts/run_backfill_predictions.py`

### 2.2 run_backfill_raw_data.py

**功能：** 回填原始日線資料（daily_bars）

**支援參數：**
- `--universe-file` (str, optional) - Universe YAML 檔案路徑，預設：`config/universe/tw_top50_2024.yaml`
- `--symbols` (str, optional) - 逗號分隔的股票代號，例如：`2330,2454,2317`。若提供，會覆蓋 universe-file
- `--start-date` (str) - 起始日期（YYYY-MM-DD），預設：`2024-01-01`
- `--end-date` (str) - 結束日期（YYYY-MM-DD），預設：`2024-12-31`

**資料流程：**
- Input: Universe 檔案或 symbols 列表 + 日期範圍
- Process: 同步 stocks 表 → 從 FinMind 取得日線資料 → 寫入 daily_bars 表（去重處理）
- Output: daily_bars 表中的歷史資料

### 2.3 run_backfill_indicators_100.py

**功能：** 回填 100 指標快照（indicator_snapshots）

**支援參數：**
- `--universe-file` (str, optional) - Universe YAML 檔案路徑
- `--symbols` (str, optional) - 逗號分隔的股票代號，覆蓋 universe-file
- `--start-date` (str) - 起始日期，預設：`2024-01-01`
- `--end-date` (str) - 結束日期，預設：`2024-12-31`
- `--force` (flag) - 強制重建已存在的指標快照

**資料流程：**
- Input: Symbol 列表 + 日期範圍
- Process: 使用 `StockIndicatorBuilder100` 建構 100 指標 → 對每個 symbol × date 呼叫 `build_indicators()` → 應用 FinMind API 節流 → 寫入 indicator_snapshots 表
- Output: indicator_snapshots 表中的指標快照（P01-P12, C01-C09, F01-F08, K/S/Q/X/M 系列）

### 2.4 run_backfill_predictions.py

**功能：** 回填預測結果（prediction_snapshots）

**支援參數：**
- `--start-date` (str) - 起始日期，預設：`2024-01-01`
- `--end-date` (str) - 結束日期，預設：`2024-12-31`
- `--symbols` (str, optional) - 逗號分隔的股票代號。若未提供，使用資料庫中所有 active stocks
- `--force` (flag) - 強制重建已存在的預測
- `--min-indicators` (int) - 最少指標數量要求，預設：90

**資料流程：**
- Input: Symbol 列表（或從 DB 取得）+ 日期範圍
- Process: 檢查資料可用性 → 從 indicator_snapshots 載入指標資料 → 使用 `StockUpsideFilter60V1.evaluate()` 產生預測結果 → 寫入 prediction_snapshots 表（score, signal, verdict, positive_factors_json, negative_factors_json, risk_flags_json）
- Output: prediction_snapshots 表中的預測結果

**特殊規則：** 支援 indicators-only 模式（只要有 indicators > 0，就允許預測，不強制要求 daily_bars）

### 2.5 FinMind API 節流機制

**位置：** `jgod/prediction/data/indicator_builder_100.py`

**Rate Limit 設定：**
- `_max_calls_per_sec = 1`（每秒最多 1 次請求）

**實作方式：**
- 使用 `collections.deque` 記錄 API 呼叫時間
- `_rate_limit()` 方法會檢查最近 1 秒內的呼叫次數
- 如果超過限制，會自動 sleep 直到可以進行下一次呼叫
- 在建構指標的每個 FinMind API 呼叫前都會執行 `_rate_limit()`

---

## (三) 後端 API 現況

### 3.1 API 架構

**主應用程式：** `jgod/api/main.py`
- FastAPI 應用，整合所有路由
- 掛載路由前綴：`/api`

**路由模組：**
- `jgod/api/routers/predictions.py` - 預測相關 API
- `jgod/api/routers/indicators.py` - 指標相關 API
- `jgod/api/routers/universe.py` - 股票池與覆蓋率 API

### 3.2 API Endpoints 清單

#### Predictions API (`/api/predictions/...`)

**GET /api/predictions/{date}**
- 用途：取得指定日期的所有股票預測
- 參數：Path `date` (YYYY-MM-DD), Query `universe` (optional)
- 回傳：Prediction[] 陣列（symbol, name, verdict, total_score, sector 等）

**GET /api/predictions/{date}/{symbol}**
- 用途：取得特定股票在特定日期的預測
- 參數：Path `date`, `symbol`, Query `include_payload` (optional)
- 回傳：單一 Prediction 物件（total_score, verdict, positive_indicators, negative_indicators）

**GET /api/predictions/timeline/{symbol}**
- 用途：取得股票的預測時間序列（用於 Timeline Chart）
- 參數：Path `symbol`, Query `start_date`, `end_date` (都是 YYYY-MM-DD 字串格式)
- 回傳：PredictionTimelineResponse（symbol, start_date, end_date, points[]，每個 point: date, score, signal）
- **最終路徑：** `/api/predictions/timeline/{symbol}?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

**GET /api/predictions/latest/{symbol}**
- 用途：取得股票的最新預測結果（用於 Signal Panel）
- 參數：Path `symbol`, Query `date` (optional，若提供則取 <= 該日期的最新一筆)
- 回傳：LatestPrediction 物件，包含：
  - symbol, date, score, signal
  - positive_factors[]（字串陣列）
  - negative_factors[]（字串陣列）
  - risk_flags[]（字串陣列）

#### Indicators API (`/api/indicators/...`)

**GET /api/indicators/{symbol}/{date}**
- 用途：取得股票的 100 指標快照（用於 Indicator Radar/Heatmap）
- 參數：Path `symbol`, `date` (YYYY-MM-DD)
- 回傳：IndicatorSnapshot 物件（symbol, date, indicators[]，每個 indicator: indicator_code, category, raw_value, normalized_value, weight, status）

#### Universe API (`/api/universe/...`)

**GET /api/universe/coverage**
- 用途：取得所有股票的指標覆蓋率狀況（用於 Coverage Heatmap）
- 參數：Query `start_date` (required), `end_date` (required)
- 回傳：CoverageSummary（start_date, end_date, total_symbols, completed_symbols, average_coverage, items[]）

**GET /api/universe/coverage-detail**
- 用途：取得詳細的覆蓋率資訊（legacy endpoint）
- 參數：Query `universe` (optional), `from_date`, `to_date` (optional)
- 回傳：CoverageResponse（symbols[], dates[], coverage[]）

---

## (四) 前端 Trading UI 現況

### 4.1 主要 React 組件

根據 `trading-ui/jgod-trading-ui/src/components/` 目錄，目前有以下組件：

1. **SmartWatchlist** (`SmartWatchlist.tsx`)
   - 智能自選股列表，支援收藏與最近使用記錄
   - 使用 localStorage 持久化

2. **WatchlistPanel** (`WatchlistPanel.tsx`)
   - 顯示指定日期的所有股票預測列表

3. **PredictionSummaryPanel** (`PredictionSummaryPanel.tsx`)
   - 顯示單一股票的預測摘要

4. **CoverageHeatmapPanel** (`CoverageHeatmapPanel.tsx`)
   - 顯示股票覆蓋率熱力圖

5. **PredictionTimelinePanel** (`PredictionTimelinePanel.tsx`)
   - 使用 Recharts 繪製預測分數時間序列折線圖
   - Score 作為 y 軸
   - 以 signal 顏色區分點（BUY/STRONG_BUY → 綠色，SHORT → 紅色，AVOID → 灰色）

6. **SignalPanel** (`SignalPanel.tsx`)
   - 顯示最新預測結果的重點資訊
   - 包含主訊號（signal, score, date）、Positive/Negative Factors、Risk Flags
   - 有「J-GOD 建議」區塊（人性化中文建議文字）

### 4.2 Dashboard 版面配置

根據 `trading-ui/jgod-trading-ui/src/pages/DashboardPage.tsx`：

**左側（固定寬度 256px）：**
- SmartWatchlist

**右側（自適應寬度）：**
- 上方：WatchlistPanel + PredictionSummaryPanel（並排）
- 中間：CoverageHeatmapPanel
- 下方：PredictionTimelinePanel
- 最下方：SignalPanel

### 4.3 Timeline 圖表實作

**技術：** Recharts 圖表庫

**顯示方式：**
- Y 軸：預測分數（score）
- X 軸：日期
- 點顏色：根據 signal 動態設定（BUY → 綠色 #22c55e，STRONG_BUY → 深綠 #15803d，SHORT → 紅色 #ef4444，AVOID → 灰色 #6b7280）
- Tooltip：顯示日期、分數、訊號
- 高度：300px，寬度響應式

### 4.4 SignalPanel 實作細節

**Positive/Negative Factors 處理：**
- 使用 helper 函數 `extractCode()` 從原始字串中提取 code
- 只顯示 code（例如 "C08"），hover 時顯示完整原始字串
- Positive Factors：綠色 badge 樣式（bg-green-100 text-green-800）
- Negative Factors：紅色 badge 樣式（bg-red-100 text-red-800）

**Risk Flags 處理：**
- 使用 helper 函數 `extractMessage()` 和 `extractSeverity()` 提取資訊
- 顯示 severity（大寫）和 message
- 使用警告圖示（⚠️）和 amber 配色（bg-amber-50 text-amber-800）
- hover 顯示完整原始字串

**人類可讀建議：**
- 內建 `getHumanAdvice()` helper 函數
- 根據 signal、score、risk_flags 產生中文建議文字
- 例如：SHORT → "偏空訊號，偏向逢高放空或減碼，嚴控風險與部位。"
- BUY/STRONG_BUY → "偏多訊號，可考慮分批佈局，但仍需搭配大盤與個股風險評估。"

---

## (五) Git 狀態與最近關鍵 Commit

### 5.1 目前 Git 狀態

**分支：** main

**狀態：** ✅ 工作區乾淨（nothing to commit, working tree clean）

**遠端同步：** ✅ 已同步到 origin/main

### 5.2 最近 10 個關鍵 Commit

1. **bcc1b10** - Add J-GOD API & trading UI core files
   - **類型：** 加入 API + Trading UI
   - **範圍：** jgod/api/, trading-ui/jgod-trading-ui/, config/universe/, scripts/, spec/, *.md

2. **8b5f353** - Tune FinMind rate limit to 1 call per second
   - **類型：** 調整 FinMind rate limit
   - **範圍：** jgod/prediction/data/indicator_builder_100.py

3. **6207278** - Improve SignalPanel factor rendering and add human-readable advice
   - **類型：** Trading UI 改進
   - **範圍：** trading-ui/jgod-trading-ui/src/components/SignalPanel.tsx

4. **a392312** - Add latest prediction signals panel to Dashboard
   - **類型：** 加入 API + Trading UI
   - **範圍：** jgod/api/routers/predictions.py, trading-ui/jgod-trading-ui/src/components/SignalPanel.tsx

5. **a80f30b** - Add SmartWatchlist component and Dashboard symbol selection
   - **類型：** Trading UI
   - **範圍：** trading-ui/jgod-trading-ui/src/components/SmartWatchlist.tsx

6. **59e9f7f** - Upgrade PredictionTimelinePanel into Recharts score timeline chart
   - **類型：** Trading UI
   - **範圍：** trading-ui/jgod-trading-ui/src/components/PredictionTimelinePanel.tsx

7. **e0c921e** - Add PredictionTimelinePanel and API integration for 2330
   - **類型：** 加入 API + Trading UI
   - **範圍：** trading-ui/jgod-trading-ui/src/components/PredictionTimelinePanel.tsx, jgod/api/routers/predictions.py

8. **b1cb48c** - Add prediction timeline API endpoint
   - **類型：** 加入 API
   - **範圍：** jgod/api/routers/predictions.py

9. **2f6f550** - Add --symbols option to raw data backfill script
   - **類型：** Backfill 腳本改進
   - **範圍：** scripts/run_backfill_raw_data.py

10. **6fd9bda** - Update prediction data-check rule: allow prediction without daily bars; indicators-only mode enabled
    - **類型：** 調整 prediction backfill 資料檢查邏輯
    - **範圍：** scripts/run_backfill_predictions.py

---

## 總結

### 完成狀態

- ✅ **資料層：** 8 檔股票 daily_bars 完整，100 指標覆蓋率 100%，但僅 4 檔有 predictions
- ✅ **Backfill 腳本：** 3 個腳本完整可用，支援 indicators-only 模式
- ✅ **後端 API：** 7 個 endpoints 已實作並測試
- ✅ **前端 UI：** 6 個核心組件已實作，Dashboard 基本架構完整
- ✅ **Git 狀態：** 工作區乾淨，已同步到遠端

### 待補齊項目

- ⚠️ 為 1301, 1303, 2308, 2412 執行 prediction backfill
- ⚠️ 為 2303 補齊更多日期的 predictions（目前只有 143 筆）

---

**報告生成時間：** 2025-01-06  
**資料來源：** 實際程式碼、資料庫查詢、Git 歷史

