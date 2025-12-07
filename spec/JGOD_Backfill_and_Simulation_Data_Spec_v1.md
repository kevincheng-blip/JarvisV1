# J-GOD Backfill & Simulation Data Spec v1

## 1. 目標與範圍

**目標：**

1. 建立一套穩定的「資料背填 + 模擬交易」資料管線，支援：
   - 100 指標 Builder（`StockIndicatorBuilder100`）
   - 60/100 指標 Filter（`StockUpsideFilter60V1`）
   - Path A/B/C/D/E 的歷史與模擬結果

2. 所有資料都要可以被：
   - Rule-based 選股引擎使用
   - RL / Path D 使用
   - 未來 React 交易指揮中心 UI 使用（WebSocket + REST）

3. **嚴格限制**：所有「下單」只允許 **DRY_RUN / PAPER 模式**，不連線真實券商、不送出真實委託。

**不做的事：**

- 不實作真實券商 API（不連台新、不連凱基、不連任何實際券商）
- 不實作真實下單（`LIVE` mode 永久鎖死）

---

## 2. 資料流總覽

資料流分成三層：

1. **Raw Data 層（FinMind / 歷史資料）**
   - 來源：FinMind API（你已經整合完成）
   - 資料：日線、法人、籌碼、財報、現金流、資產負債表…等

2. **Feature & Prediction 層**
   - 100 指標 Builder（`StockIndicatorBuilder100`）
   - 60/100 指標 Filter（`StockUpsideFilter60V1`）
   - 輸出：指標快照、Verdict、Score

3. **Simulation & Portfolio 層**
   - Path A：歷史回測結果
   - Path D：RL Test / Eval 結果
   - Path E：LiveTradingEngine（**只允許 DRY_RUN / PAPER 模式**）
   - 輸出：模擬交易紀錄、Portfolio 淨值曲線、每日 P&L

---

## 3. 資料庫 Schema 規劃（建議）

> 未來可以用 SQLite / PostgreSQL，先以 SQLite 為主。

### 3.1 stocks（標的基本資訊）

- `id` (PK, integer)
- `symbol` (text) - 例如 "2330", "1101"
- `name_zh` (text) - 公司中文名
- `name_en` (text) - 公司英文名
- `sector` (text) - 產業分類
- `is_active` (boolean)
- `created_at` (datetime)
- `updated_at` (datetime)

### 3.2 daily_bars（歷史日線）

- `id` (PK)
- `symbol` (text, FK→stocks.symbol)
- `date` (date)
- `open` (real)
- `high` (real)
- `low` (real)
- `close` (real)
- `volume` (real)
- `turnover` (real, 可選)
- `adjusted_close` (real, 可選)
- `source` (text, e.g. "FinMind")
- UNIQUE(`symbol`, `date`)

### 3.3 indicator_snapshots（100 指標快照）

- `id` (PK)
- `symbol` (text)
- `date` (date)
- `indicator_code` (text) - 例如 "P01", "C08", "F05", "M12"
- `raw_value` (real)
- `normalized_value` (real)
- `weight` (real)
- `category` (text) - "Price", "Capital", "Fundamental", "Catalyst", "Sentiment", "Quant", "X", "M"
- `data_source` (text) - 對應 FinMind 或其他來源
- `status` (text) - "ok" / "missing" / "placeholder"
- UNIQUE(`symbol`, `date`, `indicator_code`)

### 3.4 prediction_snapshots（選股結果快照）

- `id` (PK)
- `symbol` (text)
- `date` (date)
- `total_score` (real)
- `verdict` (text) - "STRONG_BUY" / "BUY" / "NEUTRAL" / "AVOID" / "SHORT"
- `positive_indicators` (json) - Top positive 指標列表
- `negative_indicators` (json) - Top negative 指標列表
- `raw_payload` (json) - 完整 evaluate 結果
- UNIQUE(`symbol`, `date`)

### 3.5 virtual_trades（模擬交易紀錄）

- `id` (PK)
- `symbol` (text)
- `open_datetime` (datetime)
- `close_datetime` (datetime, nullable)
- `side` (text) - "LONG" / "SHORT"
- `open_price` (real)
- `close_price` (real, nullable)
- `quantity` (real)
- `pnl` (real, nullable)
- `pnl_pct` (real, nullable)
- `mode` (text) - "DRY_RUN" / "PAPER"
- `engine` (text) - "PathE" / "PathD" / "ScenarioLab"
- `strategy_tag` (text) - e.g. "INTRADAY_ALPHA_V1"
- `metadata` (json)

### 3.6 portfolio_snapshots（組合淨值快照）

- `id` (PK)
- `date` (date)
- `datetime` (datetime)
- `equity_curve` (real) - 資產淨值
- `cash` (real)
- `positions_value` (real)
- `max_drawdown` (real)
- `sharpe` (real, nullable)
- `mode` (text) - "DRY_RUN" / "PAPER"
- `engine` (text)
- UNIQUE(`datetime`, `mode`, `engine`)

---

## 4. Backfill 任務規劃

### 4.1 任務一：歷史資料背填（Raw Data）

- 目的：抓取 2018-01-01 ~ 今日 的 FinMind 歷史資料。
- 標的範圍：
  - 第一階段：50 檔核心股票（例如 0050 成分股 or 你指定的 50 檔）
  - 第二階段：全部上市櫃

**Backfill Job: `scripts/run_backfill_raw_data.py`**

- Input:
  - `--symbols-file`（股票清單）
  - `--start-date`
  - `--end-date`
- Flow:
  1. 讀取 symbols 清單
  2. 對每個 symbol：
     - 抓 daily price
     - 抓籌碼、財報、現金流等
  3. 寫入 `daily_bars` + 暫存 Raw 財報表（之後給 Indicator Builder 用）

### 4.2 任務二：100 指標建構（Indicator Backfill）

**Job: `scripts/run_backfill_indicators_100.py`**

- Input:
  - `--date-range` / `--dates-file`
  - `--symbols-file`
- Flow:
  1. 迭代所有日期 × symbol
  2. 呼叫 `StockIndicatorBuilder100.build_indicators(symbol, date)`
  3. 把結果寫入 `indicator_snapshots`
  4. 記錄哪些指標為 missing / placeholder

### 4.3 任務三：選股結果快照（Prediction Backfill）

**Job: `scripts/run_backfill_predictions.py`**

- 基於 `indicator_snapshots`：
  - 每日對所有 symbol 呼叫 `StockUpsideFilter60V1.evaluate()`
  - 寫入 `prediction_snapshots`

---

## 5. 模擬交易（Simulation）與 Path E 限制

### 5.1 Path E 模式限制

- `LiveTradingEngine` 只允許：
  - `DRY_RUN`
  - `PAPER`
- `LIVE` 模式永久禁用：
  - Config 層禁止
  - 程式碼層如果有人塞 `LIVE`，必須 raise Exception

### 5.2 模擬交易 Runner

**Job: `scripts/run_simulation_path_e.py`**

- Input:
  - `--mode`：`DRY_RUN` / `PAPER`
  - `--start-date`, `--end-date`
  - `--symbols-file` or `--universe`（例如 "TW_TOP50"）
- Flow：
  1. 使用歷史資料（`daily_bars`）+ 指標（`indicator_snapshots`）
  2. 透過 Path E + Signal Engine 產生「模擬委託」
  3. 所有結果寫入：
     - `virtual_trades`
     - `portfolio_snapshots`

---

## 6. 給前端 / UI 用的 API 規劃（初版）

未來會在 FastAPI 實作：

### 6.1 REST API

- `GET /api/universe/coverage`
  - 回傳：哪些 symbol × 日期已有 100 指標、哪些缺 missing
- `GET /api/indicators/{symbol}/{date}`
  - 回傳：100 指標快照（含 raw / normalized / weight）
- `GET /api/predictions/{date}`
  - 回傳：當日所有 symbol 的 `total_score` + `verdict`
- `GET /api/virtual-trades?from=...&to=...`
  - 回傳：模擬交易紀錄
- `GET /api/portfolio/equity-curve?from=...&to=...`
  - 回傳：Portfolio 淨值時間序列

### 6.2 WebSocket Channels（for React）

- `/ws/quotes`
  - 推送：當前自選股報價（可從 FinMind 或其他資料源 / replay）
- `/ws/signals`
  - 推送：當日新產生的 STRONG_BUY / SHORT 信號
- `/ws/portfolio`
  - 推送：Portfolio 淨值、風險指標即時更新
- `/ws/virtual-orders`
  - 推送：模擬訂單狀態（NEW / FILLED / CANCELED）

---

## 7. 中英對照需求

所有對外欄位 / 面板名稱，需支援中英對照：

- 例如：
  - `sector_en`: "Semiconductor"
  - `sector_zh`: "半導體"
- 指標：
  - `indicator_code`: "P01"
  - `name_en`: "Trend Slope"
  - `name_zh`: "趨勢斜率"

未來會有獨立的 i18n 映射檔案（可在 `docs/` 或 `config/` 裡維護）。

---

