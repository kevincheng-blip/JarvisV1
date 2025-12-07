# J-GOD Trading System 完整專案總結

生成時間：2025-01-06

---

## 一、後端（JarvisV1）已完成模組

### 1.1 API 路由模組 (`jgod/api/`)

**主應用程式：**
- `jgod/api/main.py` - FastAPI 主應用，整合所有路由

**API 路由：**

#### Predictions Router (`jgod/api/routers/predictions.py`)
- `GET /api/predictions/{date}` - 取得指定日期的所有股票預測
- `GET /api/predictions/{date}/{symbol}` - 取得特定股票在特定日期的預測
- `GET /api/predictions/timeline/{symbol}` - 取得股票的預測時間序列
- `GET /api/predictions/latest/{symbol}` - 取得股票的最新預測結果（包含 factors 和 risk flags）

#### Indicators Router (`jgod/api/routers/indicators.py`)
- `GET /api/indicators/{symbol}/{date}` - 取得股票的 100 指標快照

#### Universe Router (`jgod/api/routers/universe.py`)
- `GET /api/universe/coverage` - 取得所有股票的指標覆蓋率狀況
- `GET /api/universe/coverage-detail` - 取得詳細的覆蓋率資訊（legacy）

### 1.2 資料儲存模組 (`jgod/storage/`)

**資料庫模型 (`jgod/storage/models.py`)：**
- `Stock` - 標的基本資訊表
- `DailyBar` - 歷史日線資料表
- `IndicatorSnapshot` - 100 指標快照表
- `PredictionSnapshot` - 選股結果快照表（包含 score, signal, factors, risk flags）
- `VirtualTrade` - 模擬交易紀錄表
- `PortfolioSnapshot` - 組合淨值快照表

**資料庫連接 (`jgod/storage/db.py`)：**
- SQLite 資料庫：`data/jgod_tw_stock.db`
- SQLAlchemy ORM 設定
- Session 管理

### 1.3 預測引擎模組 (`jgod/prediction/`)

**核心引擎：**
- `prediction_engine.py` - 規則型預測引擎
- `feature_builder.py` - 特徵建構器
- `ranking.py` - 排名引擎

**100 指標建構器 (`jgod/prediction/data/`)：**
- `indicator_builder_100.py` - 建構 100 指標快照
  - P 系列：價量技術指標（12 個）
  - C 系列：籌碼指標（9 個）
  - F 系列：財報指標（8 個）
  - K/S/Q/X/M 系列：其他指標（預留）
  - **FinMind API 節流機制**：每秒最多 1 次請求

**規則引擎 (`jgod/prediction/rules/`)：**
- `stock_upside_filter_60_v1.py` - StockUpsideFilter60V1 評分系統

### 1.4 資料回填腳本 (`scripts/`)

**主要腳本：**
- `run_backfill_raw_data.py` - 回填原始資料（daily_bars）
  - 支援 `--symbols` 參數（可選，覆蓋 universe-file）
  - 支援 `--universe-file`、`--start-date`、`--end-date`
- `run_backfill_indicators_100.py` - 回填 100 指標快照
- `run_backfill_predictions.py` - 回填預測結果
  - 支援 indicators-only 模式（不強制要求 daily_bars）
  - 放寬 insufficient data 檢查

**其他腳本：**
- `check_indicator_gaps.py` - 檢查指標資料缺口
- `debug_check_db.py` - 資料庫檢查工具
- `run_jgod_path_*.py` - 各種 Path 實驗腳本

### 1.5 其他核心模組

**市場資料：**
- `jgod/market/` - 市場資料載入、指標計算
- `api_clients/finmind_client.py` - FinMind API 客戶端（含 RateLimiter）

**風險管理：**
- `jgod/risk/` - 風險引擎、組合風險、部位大小計算

**執行引擎：**
- `jgod/execution/` - 執行引擎、虛擬券商、滑價模型

**Alpha 引擎：**
- `jgod/alpha_engine/` - Alpha 因子引擎（extreme、flow、inertia 等）

**War Room：**
- `jgod/war_room_backend_v6/` - War Room Backend v6.0（FastAPI + WebSocket）

---

## 二、前端（trading-ui）已完成 UI 元件

### 2.1 專案結構 (`trading-ui/jgod-trading-ui/`)

**技術棧：**
- React 18 + TypeScript
- Vite 建置工具
- Recharts 圖表庫
- Axios HTTP 客戶端
- react-i18next 國際化

### 2.2 UI 元件 (`src/components/`)

**核心面板：**

1. **SmartWatchlist** (`SmartWatchlist.tsx`)
   - 智能自選股列表
   - 收藏功能（localStorage 持久化）
   - 最近使用記錄（最多 20 個）
   - 智能排序：收藏 → 最近使用 → 全部股票

2. **PredictionTimelinePanel** (`PredictionTimelinePanel.tsx`)
   - 使用 Recharts 繪製預測分數時間序列折線圖
   - Signal-based 顏色編碼（BUY/STRONG_BUY/SHORT/AVOID）
   - 自訂 Tooltip 顯示日期、分數、訊號
   - 300px 高度，響應式寬度

3. **SignalPanel** (`SignalPanel.tsx`)
   - 顯示最新預測結果的重點資訊
   - 主訊號區塊：signal、score、日期
   - Positive/Negative Factors：只顯示 code，hover 顯示完整內容
   - Risk Flags：顯示 message 和 severity
   - J-GOD 建議：人性化中文建議文字

4. **WatchlistPanel** (`WatchlistPanel.tsx`)
   - 顯示指定日期的所有股票預測列表
   - 表格格式：symbol、name、verdict、total_score、sector

5. **PredictionSummaryPanel** (`PredictionSummaryPanel.tsx`)
   - 顯示單一股票的預測摘要

6. **CoverageHeatmapPanel** (`CoverageHeatmapPanel.tsx`)
   - 顯示股票覆蓋率熱力圖

### 2.3 API 客戶端 (`src/api/`)

**主要檔案：**

1. **client.ts** - 主要 API 客戶端
   - `getPredictions()` - 取得指定日期的所有預測
   - `getPrediction()` - 取得特定股票的預測
   - `getIndicators()` - 取得 100 指標快照
   - `getCoverage()` - 取得覆蓋率摘要
   - `getCoverageDetail()` - 取得詳細覆蓋率
   - `getPredictionTimeline()` - 取得預測時間序列
   - `getLatestPrediction()` - 取得最新預測

2. **universeApi.ts** - 股票列表 API
   - `fetchUniverseStocks()` - 從 coverage endpoint 取得股票列表
   - 支援 fallback 到 mock 資料

### 2.4 狀態管理

**DashboardPage (`src/pages/DashboardPage.tsx`)：**
- `selectedDate` - 選中的日期
- `predictions` - 預測列表
- `coverage` - 覆蓋率資料
- `timelineSymbol` - 目前選擇的股票（初始："2330"）
- 左右兩欄佈局：左側 SmartWatchlist，右側主要內容

### 2.5 類型定義 (`src/types/index.ts`)

定義的 TypeScript 介面：
- `Prediction` - 預測結果
- `Indicator` / `IndicatorSnapshot` - 指標資料
- `CoverageItem` / `CoverageSummary` / `CoverageResponse` - 覆蓋率
- `PredictionTimelinePoint` / `PredictionTimelineResponse` - 時間序列
- `LatestPrediction` - 最新預測（包含 factors 和 risk flags）

---

## 三、資料庫完整度

### 3.1 資料庫概覽

**資料庫檔案：** `data/jgod_tw_stock.db`

**資料表：**
- `stocks` - 8 檔股票
- `daily_bars` - 1,936 筆，8 檔股票（2024-01-02 ~ 2024-12-31，242 個交易日）
- `indicator_snapshots` - 190,900 筆，8 檔股票（2024-01-01 ~ 2024-12-31，262 個日期）
- `prediction_snapshots` - 929 筆，4 檔股票（2024-01-01 ~ 2024-12-31，262 個日期）

**資料日期範圍：**
- Daily Bars：2024-01-02 ~ 2024-12-31（242 個交易日）
- Indicators：2024-01-01 ~ 2024-12-31（262 個日期）
- Predictions：2024-01-01 ~ 2024-12-31（262 個日期，僅部分股票）

### 3.2 各股票資料完整度

| Symbol | Name | Daily Bars | Indicators | Predictions | 狀態 |
|--------|------|-----------|-----------|-------------|------|
| 2330 | 台積電 | 242 dates | 262 dates (26,200 筆) | ✅ 262 dates | ✅ Complete |
| 2454 | 聯發科 | 242 dates | 262 dates (26,200 筆) | ✅ 262 dates | ✅ Complete |
| 2317 | 鴻海 | 242 dates | 262 dates (26,200 筆) | ✅ 262 dates | ✅ Complete |
| 2303 | 聯電 | 242 dates | 194 dates (19,400 筆) | ✅ 143 dates | ⚠️ Partial |
| 1301 | 台塑 | 242 dates | 262 dates (26,200 筆) | ❌ 0 dates | ⚠️ Missing |
| 1303 | 南亞 | 242 dates | 144 dates (14,400 筆) | ❌ 0 dates | ⚠️ Missing |
| 2308 | 台達電 | 242 dates | 262 dates (26,200 筆) | ❌ 0 dates | ⚠️ Missing |
| 2412 | 中華電 | 242 dates | 262 dates (26,200 筆) | ❌ 0 dates | ⚠️ Missing |

**完整資料（3 檔）：**
- ✅ 2330（台積電）- daily_bars + indicators + predictions 完整
- ✅ 2454（聯發科）- daily_bars + indicators + predictions 完整
- ✅ 2317（鴻海）- daily_bars + indicators + predictions 完整

**部分資料（1 檔）：**
- ⚠️ 2303（聯電）- 有 predictions 但日期較少（143 dates）

**缺少預測（4 檔）：**
- ❌ 1301, 1303, 2308, 2412 - 只有 daily_bars 和 indicators，缺少 predictions

---

## 四、最近提交記錄（過去 2 週）

### 4.1 核心功能開發

1. **8b5f353** - Tune FinMind rate limit to 1 call per second
   - 調整 `indicator_builder_100.py` 的 rate limit 從每秒 2 次降至 1 次

2. **6207278** - Improve SignalPanel factor rendering and add human-readable advice
   - 改進 SignalPanel 的 factor 渲染（只顯示 code）
   - 美化 Risk Flags 顯示
   - 添加人性化建議區塊

3. **a392312** - Add latest prediction signals panel to Dashboard
   - 新增 `/api/predictions/latest/{symbol}` endpoint
   - 建立 SignalPanel 組件
   - 集成到 Dashboard

4. **a80f30b** - Add SmartWatchlist component and Dashboard symbol selection
   - 建立 SmartWatchlist 組件（收藏、最近使用）
   - 整合到 Dashboard 左側
   - 動態 symbol 選擇功能

5. **59e9f7f** - Upgrade PredictionTimelinePanel into Recharts score timeline chart
   - 將 Timeline 面板升級為 Recharts 折線圖
   - Signal-based 顏色編碼
   - 自訂 Tooltip

6. **e0c921e** - Add PredictionTimelinePanel and API integration for 2330
   - 建立 Timeline Panel 組件
   - 整合 prediction timeline API

### 4.2 API 開發

7. **8417165** - Move timeline endpoint before dynamic routes to avoid routing conflicts
   - 調整路由順序避免衝突

8. **e13cca5** - Change prediction timeline route to `/api/predictions/timeline/{symbol}`
   - 修正路由路徑

9. **98dd50a** - Fix timeline endpoint: use string dates to avoid routing conflicts
   - 改用字串日期參數

10. **b1cb48c** - Add prediction timeline API endpoint
    - 新增 timeline API endpoint

### 4.3 資料處理改進

11. **2f6f550** - Add --symbols option to raw data backfill script
    - 支援命令行指定 symbols

12. **6fd9bda** - Update prediction data-check rule: allow prediction without daily bars
    - 允許 indicators-only 模式

13. **810a03c** - Relax insufficient data check in prediction backfill
    - 放寬資料檢查條件

14. **74267b0** - Adjust FinMind rate limits for 6000/hour plan
    - 調整 FinMind rate limiter 設定

### 4.4 基礎建設

15. **770ca83** - Align prediction backfill DB with TW stock database
    - 對齊資料庫結構

16. **739bbb9** - Add prediction backfill CLI for J-GOD
    - 新增 prediction backfill 腳本

---

## 五、未提交的變更（Untracked Files）

### 5.1 後端未追蹤檔案

**API 模組：**
- `jgod/api/__init__.py`
- `jgod/api/main.py`
- `jgod/api/routers/__init__.py`
- `jgod/api/routers/indicators.py`
- `jgod/api/routers/universe.py`

**儲存模組：**
- `jgod/storage/__init__.py`

**工具模組：**
- `jgod/utils/__init__.py`

**腳本：**
- `scripts/check_indicator_gaps.py`
- `scripts/debug_check_db.py`
- `scripts/run_backfill_indicators_100.py`

**配置：**
- `config/universe/`（目錄）

### 5.2 前端未追蹤檔案

**核心檔案：**
- `trading-ui/jgod-trading-ui/index.html`
- `trading-ui/jgod-trading-ui/src/App.tsx`
- `trading-ui/jgod-trading-ui/src/main.tsx`
- `trading-ui/jgod-trading-ui/tsconfig.json`
- `trading-ui/jgod-trading-ui/tsconfig.node.json`
- `trading-ui/jgod-trading-ui/vite.config.ts`
- `trading-ui/jgod-trading-ui/package-lock.json`

**元件：**
- `trading-ui/jgod-trading-ui/src/components/CoverageHeatmapPanel.tsx`
- `trading-ui/jgod-trading-ui/src/components/PredictionSummaryPanel.tsx`
- `trading-ui/jgod-trading-ui/src/components/WatchlistPanel.tsx`

**其他：**
- `trading-ui/jgod-trading-ui/src/i18n/`（目錄）
- `trading-ui/README.md`

### 5.3 文件

- `spec/JGOD_Backfill_and_Simulation_Data_Spec_v1.md`
- `spec/JGOD_Trading_Command_Center_UI_Spec_v1.md`

---

## 六、目前進行中的任務

### 6.1 資料回填

**可能需要執行：**
- 為 1301, 1303, 2308, 2412 執行 prediction backfill
- 為 2303 補齊更多日期的 predictions

### 6.2 前端開發

**已完成：**
- ✅ Dashboard 基本架構
- ✅ SmartWatchlist 整合
- ✅ Timeline Chart 視覺化
- ✅ Signal Panel 顯示最新預測

**待完成（推測）：**
- ⏳ Coverage Heatmap 完整實作
- ⏳ Indicator Radar/Heatmap 面板
- ⏳ 更多股票加入 universe

---

## 七、待辦任務

### 7.1 資料完整性

1. **補齊預測資料**
   - 為 1301, 1303, 2308, 2412 執行 prediction backfill
   - 為 2303 補齊更多日期

2. **擴充股票池**
   - 目前只有 8 檔股票
   - `config/universe/tw_top50_2024.yaml` 規劃了 50 檔

### 7.2 功能增強

1. **前端功能**
   - 完善 Coverage Heatmap 面板
   - 實作 Indicator Radar 視覺化
   - 添加更多互動功能

2. **API 擴充**
   - 可能需要更多分析端點
   - 歷史回測結果 API

### 7.3 代碼管理

1. **提交未追蹤檔案**
   - 將所有新開發的檔案加入 git 追蹤
   - 建立合理的 commit 結構

2. **文件完善**
   - API 文件
   - 前端組件使用說明

---

## 八、技術亮點

### 8.1 後端

- ✅ FastAPI + SQLAlchemy ORM
- ✅ FinMind API 節流機制（每秒 1 次）
- ✅ 100 指標框架（P/C/F/K/S/Q/X/M 系列）
- ✅ 預測時間序列 API
- ✅ 覆蓋率分析 API

### 8.2 前端

- ✅ React 18 + TypeScript
- ✅ Recharts 圖表庫
- ✅ localStorage 持久化（收藏、最近使用）
- ✅ 響應式設計
- ✅ Signal-based 視覺化

### 8.3 資料處理

- ✅ SQLite 資料庫（輕量、高效）
- ✅ 模組化資料回填腳本
- ✅ 支援 indicators-only 模式

---

## 九、專案架構總結

```
JarvisV1/
├── jgod/
│   ├── api/              # FastAPI 路由
│   ├── storage/          # 資料庫模型與連接
│   ├── prediction/       # 預測引擎與指標建構
│   ├── market/           # 市場資料處理
│   ├── risk/             # 風險管理
│   └── ...
├── trading-ui/
│   └── jgod-trading-ui/  # React 前端
│       ├── src/
│       │   ├── components/  # UI 元件
│       │   ├── api/         # API 客戶端
│       │   ├── pages/       # 頁面
│       │   └── types/       # TypeScript 類型
│       └── ...
├── scripts/              # 資料處理腳本
├── config/               # 配置檔案
└── data/                 # SQLite 資料庫
```

---

**總結生成時間：** 2025-01-06  
**最後提交：** 8b5f353 - Tune FinMind rate limit to 1 call per second  
**Git 狀態：** 已同步到遠端（origin/main）

---

## 十、快速參考

### 啟動後端 API
```bash
cd /Users/kevincheng/JarvisV1
PYTHONPATH=. uvicorn jgod.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 啟動前端開發伺服器
```bash
cd trading-ui/jgod-trading-ui
npm install
npm run dev
```

### 資料回填命令範例
```bash
# 回填原始資料
PYTHONPATH=. python scripts/run_backfill_raw_data.py --symbols 2330,2454 --start-date 2024-01-01 --end-date 2024-12-31

# 回填指標
PYTHONPATH=. python scripts/run_backfill_indicators_100.py --symbols 2330 --start-date 2024-01-01 --end-date 2024-12-31

# 回填預測
PYTHONPATH=. python scripts/run_backfill_predictions.py --symbols 2330 --start-date 2024-01-01 --end-date 2024-12-31
```

