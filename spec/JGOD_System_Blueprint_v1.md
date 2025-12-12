# J-GOD 系統藍圖 v1

**文件版本：** 1.0  
**最後更新：** 2025-01-06  
**目標讀者：** 新進工程師、架構師、AI 助手

---

## 文件說明

本文檔是 J-GOD 系統的總覽文件，提供系統願景、核心哲學、全局架構與關鍵設計原則。建議所有新進人員先閱讀此文件，再深入其他規格文件。

---

## 1. 系統願景與哲學

### 1.1 系統定位

**J-GOD（股神作戰系統）** 是一個**模組化、多層次的量化交易決策系統**，整合了：

- 市場資料處理與因子計算
- 規則型預測引擎
- AI 增強的決策層
- 多策略路徑實驗框架
- 知識驅動的治理機制
- 虛擬交易執行與回測

### 1.2 核心哲學

#### 模組化設計
- 每個模組職責清晰，可獨立測試和部署
- 模組間透過明確的介面通信，降低耦合度
- 支援模組替換與擴展

#### 多路徑實驗
- 支援 Path A/B/C/D/E 等多種交易策略路徑
- 每個 Path 可獨立開發、測試、回測
- 透過 A/B 測試機制比較不同 Path 的表現

#### 知識驅動
- **Doctrine（教條）系統**作為知識庫，指導決策
- Doctrine 條文可版本控制、審核、修補
- Self-Repair Engine 可自動提出 Doctrine 修復建議

#### AI 增強
- 整合多個 LLM Provider（OpenAI, Claude, Gemini, Perplexity）
- War Room 採用多角色 AI 委員會模式，並行分析
- Decision Layer 使用 LLM 修正 Raw Score

#### 模擬優先
- **目前僅支援 DRY_RUN 和 PAPER 模式**
- 不進行實盤交易，所有交易為虛擬執行
- 所有交易記錄存入 SQLite，用於回測與分析

---

## 2. 系統大地圖：六大世界

J-GOD 系統可視為六個相對獨立但相互協作的「世界」：

### 2.1 數據 & 預測世界

**核心模組：** `jgod/market/`, `jgod/prediction/`, `jgod/storage/`

**職責：**
- 從外部資料源（FinMind）取得市場資料
- 建構 100 指標快照（P/C/F/K/S/Q/X/M 系列）
- 計算 Alpha 因子與技術因子
- 執行規則型預測，產生 Raw Score

**輸出：** `PredictionSnapshot`（包含 score, signal, factors, risk_flags）

### 2.2 決策 & 風險世界

**核心模組：** `jgod/decision/`, `jgod/risk/`, `jgod/strategy/`, `jgod/execution/`

**職責：**
- 將 Raw Score 轉換為 Final Score（Decision V1/V2）
- 查詢 Doctrine 知識庫，產生 Doctrine Flags
- 生成交易訊號（BUY/SELL/HOLD）
- 風險評估與部位大小計算
- 虛擬交易執行與記錄

**輸出：** `DecisionOutput`, `VirtualTrade`

### 2.3 知識 & 教條世界

**核心模組：** `jgod/knowledge/`, `jgod/doctrine_v2/`, `jgod/doctrine_alert/`

**職責：**
- 管理 Doctrine 條文（版本控制、審核流程）
- 監控 Doctrine 違規，觸發警報
- Self-Repair Engine 自動提出修復建議
- 知識提取與查詢

**輸出：** Doctrine 條文、警報事件、修復提案

### 2.4 實驗 & 模擬世界

**核心模組：** `jgod/path_a/` ~ `jgod/path_e/`, `jgod/backtest/`, `jgod/rule_sim/`, `jgod/decision_ab/`

**職責：**
- 實作多種交易策略路徑（Path A/B/C/D/E）
- 歷史資料回測與績效計算
- 規則變更的 A/B 測試（Rule Simulation）
- Decision Layer 的 A/B 測試

**輸出：** 回測報告、A/B 測試報告

### 2.5 觀察 & 戰情室世界

**核心模組：** `jgod/observer/`, `jgod/diagnostics/`, `jgod/council_chamber/`

**職責：**
- 系統狀態監控與異常偵測
- 錯誤診斷與自動修復嘗試
- War Room 多 AI 角色並行分析
- 提供決策建議與市場分析

**輸出：** 觀察報告、診斷報告、War Room 分析結果

### 2.6 前端 Command Center 世界

**核心模組：** `trading-ui/jgod-trading-ui/`

**職責：**
- Dashboard 儀表板（預測列表、時間序列圖表、訊號面板）
- War Room V2 統一控制中心
- Doctrine 管理控制台（DMC）
- 規則模擬與 A/B 測試 UI
- 知識治理儀表板

**輸出：** Web UI（React + TypeScript）

---

## 3. 高層級資料流

### 3.1 完整資料流圖

```
外部資料源 (FinMind/yfinance)
    ↓
[Data Loader] → Daily Bars (OHLCV)
    ↓
[Indicator Builder] → 100 指標快照 (P/C/F/K/S/Q/X/M 系列)
    ↓
[Feature Builder] → 特徵向量
    ↓
[Prediction Engine] → Raw Score (規則型打分)
    ↓
[Decision Engine] → Final Score (LLM/S-Rank 修正)
    ↓
[Strategy Engine] → 交易訊號 (BUY/SELL/HOLD)
    ↓
[Risk Engine] → 風險評估 + 部位大小
    ↓
[Execution Engine] → 虛擬交易執行
    ↓
[Trade Recorder] → 交易記錄 (SQLite)
    ↓
[Observer] → 監控與分析
    ↓
[Knowledge Engine] → 知識提取與 Doctrine 更新
```

### 3.2 各階段詳解

#### 階段 1：資料取得與處理
- **輸入**：股票代號、日期範圍
- **處理**：`jgod/data/finmind_loader.py` 從 FinMind API 取得資料
- **輸出**：`DailyBar`, `IndicatorSnapshot` 存入 SQLite

#### 階段 2：因子計算
- **輸入**：Daily Bars + Indicators
- **處理**：`jgod/alpha_engine/` 計算 Alpha 因子，`factor_engine/` 計算技術因子
- **輸出**：因子向量

#### 階段 3：預測生成
- **輸入**：特徵向量
- **處理**：`jgod/prediction/prediction_engine.py` 規則打分
- **輸出**：`PredictionSnapshot`（score, signal, factors, risk_flags）

#### 階段 4：決策修正
- **輸入**：Raw Score
- **處理**：
  - Decision V1：LLM 修正
  - Decision V2：S-Rank 加權修正
  - Doctrine 查詢
- **輸出**：Final Score + Doctrine Flags

#### 階段 5：策略執行
- **輸入**：Final Score + 交易訊號
- **處理**：策略生成 → 風險評估 → 虛擬執行
- **輸出**：`VirtualTrade` 記錄

#### 階段 6：觀察與知識提取
- **輸入**：交易記錄、系統日誌
- **處理**：Observer 監控、Knowledge Engine 提取知識
- **輸出**：觀察報告、知識條文

---

## 4. 關鍵設計原則

### 4.1 模組化原則

- **單一職責**：每個模組只負責一個明確的功能領域
- **介面明確**：模組間透過明確的介面（函數簽名、資料模型）通信
- **低耦合**：模組間依賴關係清晰，避免循環依賴

### 4.2 多路徑實驗原則

- **路徑獨立**：每個 Path 可獨立開發、測試、部署
- **統一介面**：所有 Path 實作相同的 Strategy Interface（建議）
- **A/B 測試**：透過 Rule Simulation 和 Decision AB Test 比較不同路徑

### 4.3 Doctrine 驅動原則

- **知識版本化**：Doctrine 條文支援版本控制與審核流程
- **自動修復**：Self-Repair Engine 可自動提出 Doctrine 修復建議
- **違規監控**：Doctrine Alert 系統監控違規並觸發警報

### 4.4 AI 戰情室原則

- **多角色並行**：War Room 採用多角色 AI 委員會模式，各角色並行分析
- **Provider 抽象**：支援多個 LLM Provider，可切換與組合
- **決策整合**：Strategist 角色整合所有角色意見，產生最終建議

---

## 5. 關鍵限制

### 5.1 模擬模式限制

**目前系統僅支援模擬模式：**

- **DRY_RUN 模式**：完全模擬，不產生任何交易記錄
- **PAPER 模式**：虛擬交易，產生交易記錄但不實際下單
- **LIVE 模式**：**目前不支援**，未來可能實作

### 5.2 資料來源限制

- **台股資料**：目前主要使用 FinMind API
- **美股資料**：yfinance 支援（可能未完全整合）
- **資料節流**：FinMind API 目前設定為每秒 1 次請求

### 5.3 技術棧限制

- **後端**：Python 3.11+, FastAPI, SQLAlchemy, SQLite
- **前端**：React 18, TypeScript, Vite
- **AI**：OpenAI, Anthropic, Google Gemini, Perplexity

---

## 6. 版本標記說明

### 6.1 目前階段

**v0.2.0-war-room-v2**

- **核心功能**：War Room V2 統一控制中心已實作
- **Decision Layer**：V1 和 V2 並存，V2 使用 S-Rank 加權
- **Doctrine 系統**：V2 版本控制系統已實作
- **前端**：War Room V2 Dashboard 已實作
- **資料完整性**：部分股票資料不完整（需補齊）

### 6.2 版本軸線預測

- **v0.2.x**：War Room V2 完善、資料補齊
- **v0.3.x**：Decision V2 完整整合、Path 引擎統一
- **v0.4.x**：回測系統增強、Observer 完善
- **v0.5.x**：知識庫擴充、ML 整合準備
- **v1.0.0**：實盤交易準備、多市場支援

---

## 7. 系統入口點

### 7.1 CLI 入口

**檔案：** `jgod/cli.py`

**命令：**
- `status` - 顯示系統狀態
- `scan` - 掃描專案
- `warroom` - AI 戰情室（CLI 模式）
- `todo` - 提取 TODO
- `insight` - 系統洞察

### 7.2 Streamlit UI

**檔案：** `jgod/council_chamber/war_room_app.py`

**功能：** War Room V2 多 AI 幕僚會議室（本機開發用）

### 7.3 FastAPI 後端

**檔案：** `jgod/api/main.py`

**端口：** 8000

**功能：** REST API 服務，提供所有後端功能

### 7.4 前端 React App

**目錄：** `trading-ui/jgod-trading-ui/`

**功能：** 現代化 Web UI，包含 Dashboard、War Room V2、DMC 等

---

## 8. 相關文件

- [後端模組地圖](./JGOD_Backend_Module_Map_v1.md) - 詳細的後端模組說明
- [前端架構](./JGOD_Frontend_Architecture_v1.md) - 前端架構與組件說明
- [API 映射](./JGOD_API_Map_v1.md) - 完整的 API 端點列表
- [路線圖](./JGOD_Roadmap_v1.md) - 開發路線圖與版本規劃
- [架構風險與治理](./JGOD_Architecture_Risks_and_Governance_v1.md) - 技術債務與改進建議

---

**文件結束**

