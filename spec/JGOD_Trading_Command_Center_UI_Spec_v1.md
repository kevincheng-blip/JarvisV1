# J-GOD Trading Command Center UI Spec v1
（React + WebSocket, Simulation-Only）

## 1. 目標與定位

**目標：**

打造一套超越三竹股市 App 的「J-GOD 交易指揮中心」，具備：

- 多面板、多工作區、即時跳動（WebSocket）
- 完整連接 J-GOD 大腦（100 指標 + Filter + Path A/B/C/D/E）
- 嚴格採用「模擬下單」模式（DRY_RUN / PAPER），但介面體驗與實盤等級一致
- 所有 UI 元件支援中英文顯示（`zh-TW` / `en`）

**技術選型：**

- 前端：React + TypeScript（建議用 Vite 或 Next.js）
- UI Framework：可考慮 MUI / Ant Design / Tailwind
- 圖表：ECharts 或 Plotly
- 通訊：WebSocket + REST（後端為 FastAPI / Uvicorn）
- 布局：可拖曳、多 Panel Dashboard（如 `react-grid-layout` 類型）

---

## 2. 介面區塊（對應 Gemini Step 8 類別）

整體畫面分為 4 大區塊：

- A. 市場與報價監控區（Market & Quote Monitoring）
- B. 策略與決策分析區（Strategy & Decision Analysis）
- C. 交易與訂單管理區（Execution & Audit Trail）
- D. 系統治理與控制區（Governance & Kill Switch）

此外，新增一個 **資料覆蓋 / 背填狀態面板**，讓使用者一眼看到：
- 哪些股票 / 日期已完成 100 指標計算
- 哪些仍缺資料

---

## 3. 各區塊詳細 Spec

### 3.1 A 區：市場與報價監控（Market & Quote Monitoring）

**組件 A1：自選股 / 宇宙清單 (Watchlist / Universe Board)**

- 顯示欄位（支援中英切換）：
  - Symbol（代號）
  - Name（名稱, zh/en）
  - Last Price（最新價）
  - Chg / Chg%（漲跌）
  - Volume（量）
  - Verdict（From `prediction_snapshots.verdict`）
  - Upside Score（From `prediction_snapshots.total_score`）
- 資料來源：
  - WebSocket `/ws/quotes`
  - REST `/api/predictions/{date}`
- 功能：
  - 篩選：只看 STRONG_BUY / SHORT 的標的
  - 按 Score 排序
  - 點擊某一檔 → 右側開啟該股詳細面板（K 線 + 指標）

---

**組件 A2：報價細節 + 深度 (Quote Detail & Order Book)**

- 顯示：
  - 即時報價
  - 買賣五檔 / 二十檔
  - 簡單流動性指標（例如 Spread、Liquidity Score）
- 資料來源：
  - WebSocket `/ws/quotes` / `/ws/orderbook`
- 功能：
  - 只支援「模擬下單」入口（連到 C 區的 Order Ticket）

---

**組件 A3：分時 & K 線（Intraday & K-Line Chart）**

- 顯示：
  - 分時走勢
  - 1 / 5 / 15 / 60 分 K 線
  - 疊加：
    - J-GOD Alpha 訊號點
    - 進場 / 出場 / 止損模擬點（從 `virtual_trades`）
- 資料來源：
  - REST `/api/bars/{symbol}`（歷史）
  - WebSocket `/ws/quotes`（即時更新）
  - REST `/api/virtual-trades?symbol=...`

---

### 3.2 B 區：策略與決策分析（Strategy & Decision Analysis）

**組件 B1：100 指標雷達圖 / 熱力圖**

- 顯示：
  - 100 指標分群視覺化（P/C/F/K/S/Q/X/M）
  - 顏色代表 normalized score 正負與強度
- 資料來源：
  - REST `/api/indicators/{symbol}/{date}`
- 功能：
  - 滑鼠移上去顯示：
    - 指標代碼（P01）
    - 中英文名稱
    - raw value / normalized / weight
  - 支援中英切換

---

**組件 B2：決策摘要 / 解釋 (Decision Summary & Explanation)**

- 顯示：
  - Verdict（STRONG_BUY / BUY / NEUTRAL / AVOID / SHORT）
  - Total Score
  - Top Positive Indicators（列表）
  - Top Negative Indicators（列表）
- 文字：中英文對照（例如：  
  - zh:「此標的屬於『明確做多』區間，原因來自：籌碼強、財報佳、題材有力。」  
  - en:「This stock is classified as 'Strong Buy' mainly due to strong capital flows, solid fundamentals, and positive catalysts.」）
- 資料來源：
  - REST `/api/predictions/{date}?symbol=...`

---

**組件 B3：Alpha 因子診斷（Factor Diagnostics, Optional for v2）**

- 連接你現有 Path B/C/D / Diagnosis Engine
- 顯示：
  - 因子 IC 時序
  - 因子衰減燈號（綠 / 黃 / 紅）
- 初版可以先預留 Panel，未必立刻實作。

---

### 3.3 C 區：交易與訂單管理（Execution & Audit Trail, Simulation Only）

> ⚠ **這區域所有操作都只會呼叫 Simulation API，不會真的下單。**

**組件 C1：模擬下單面板（Simulated Order Ticket）**

- 欄位：
  - Symbol
  - Side（Long / Short）
  - Quantity
  - Mode：DRY_RUN / PAPER（預設 PAPER）
  - Strategy Tag（下單策略標籤）
- 操作：
  - 按下「送出模擬單」：
    - 呼叫後端 `/api/simulated-orders`（會使用 Path E 的某種簡化流程）
- 限制：
  - 若 mode=LIVE，後端必須 reject 並回傳錯誤：「J-GOD is simulation-only. LIVE trading is disabled.」

---

**組件 C2：模擬訂單列表（Virtual Orders Board）**

- 顯示欄位：
  - Symbol
  - Side
  - Price
  - Status（NEW / FILLED / CANCELED）
  - Mode（DRY_RUN / PAPER）
  - P&L（若已平倉）
- 資料來源：
  - WebSocket `/ws/virtual-orders`
  - REST `/api/virtual-trades?from=...&to=...`

---

**組件 C3：歷史模擬績效（Simulated P&L & Equity Curve）**

- 顯示：
  - 淨值曲線（Portfolio Equity Curve）
  - 每日 P&L 欄位
  - Sharpe / Max Drawdown / Win Rate（可簡化）
- 資料來源：
  - REST `/api/portfolio/equity-curve?from=...&to=...`

---

### 3.4 D 區：系統治理與控制（Governance & Kill Switch）

**組件 D1：Kill Switch 狀態燈**

- 狀態：
  - 綠：System Normal（允許產生新策略信號與模擬單）
  - 黃：Warning（Sharpe 掉到某門檻、MaxDD 超標）
  - 紅：Kill（停止新信號與新模擬單，保留監控）
- 操作：
  - 人工可以按下「手動切換 Kill 狀態」，但：
    - 每一次切換都要記錄在後端 log
- 資料來源：
  - WebSocket `/ws/governance`
  - REST `/api/governance/status`

---

**組件 D2：壓力測試 & 情境模擬（簡化版）**

- 初版可以僅提供：
  - 顯示當前風險指標（Sharpe, MaxDD, Vol）
  - 顯示最近一次壓力測試結果（來自 Path C / Scenario Lab）

---

### 3.5 E 區：資料覆蓋 / 背填狀態面板（Data Coverage Panel）

> 這是你特別強調要的「知道哪些股票/日期還沒被抓齊」的面板。

**組件 E1：Coverage Heatmap**

- 顯示：
  - 橫軸：日期（可選：近 30 日、近 90 日）
  - 縱軸：股票（例如核心宇宙 50 檔）
  - 色塊：
    - 綠：該日期有完整 100 指標 + prediction + 回測
    - 黃：指標部分缺失（status = placeholder / missing）
    - 紅：完全沒有資料
- 資料來源：
  - REST `/api/universe/coverage`

---

## 4. 中英雙語設計（i18n）

- 每個 Panel、欄位、指標都有 `key`，搭配 i18n mapping：
  - 例如 `label.verdict.strong_buy` →
    - zh-TW: "強烈買進"
    - en: "Strong Buy"
- 建議：
  - 在前端建立 `locales/zh-TW.json`、`locales/en.json`
  - 所有 UI 文案以 key 驅動，不硬寫中文。

---

## 5. 安全與限制聲明

1. UI 所有「下單」操作僅對接：
   - 模擬 API（Simulation API）
   - 不允許任何實際券商 endpoint

2. 後端若收到任何 `mode="LIVE"`：
   - 必須回傳錯誤
   - 並 log 下嘗試行為

3. UI 需明確標示：
   - 頂部顯示「Simulation Mode Only / 僅模擬交易，不連結真實券商」

---

## 6. 與現有系統整合說明

- 這個 UI 不會直接讀取 FinMind，而是全部透過：
  - 你已經有的 Builder / Filter / Path A/B/C/D/E
  - Spec 1 所定義的 Database + API

- UI 只需要知道：
  - WebSocket endpoints
  - REST endpoints
  - Response 格式（之後再用 OpenAPI / pydantic 定義）

---

