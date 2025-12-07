# J-GOD 股神作戰系統架構藍圖 v1.0

> **定位**：本文件為 J-GOD 系統的最上層架構藍圖，面向「未來的我 + 任何工程師 + AI 協作」  
> **目標**：避免「寫死」設計，支援未來多市場、多產品、長期演進的架構戰略

---

## 目錄

1. [J-GOD 全局總覽](#1-j-god-全局總覽)
2. [三大 Tier：Presentation / Application / Data](#2-三大-tier-presentation--application--data)
3. [六個邏輯 Layer（L0~L5）](#3-六個邏輯-layer-l0l5)
4. [七個 Microservices](#4-七個-microservices)
5. [AI Policy & Narration Service](#5-ai-policy--narration-service)
6. [訊息佇列 / 非同步通訊](#6-訊息佇列--非同步通訊)
7. [與現有 JarvisV1 的對照表](#7-與現有-jarvisv1-的對照表)
8. [Roadmap：從原型到七服務架構](#8-roadmap從原型到七服務架構)

---

## 1. J-GOD 全局總覽

### 架構公式

```
J-GOD = 3 Tiers × 6 Logical Layers × 7 Microservices + 1 AI Policy & Narration Service
```

### 高層級架構圖

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Presentation Tier                                   │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  Trading UI (React) + War Room UI (Next.js)                        │    │
│  │  只負責顯示：四大作戰清單、盤前作戰報告、即時事件流                 │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ WebSocket / REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Application Tier                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Data Quality │  │   Factor     │  │  Prediction  │  │  Strategy &  │  │
│  │   & Event    │→ │   Engine     │→ │   Service    │→ │   Signal     │  │
│  │   Service    │  │   Service    │  │              │  │   Service    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  │                  │         │
│         └──────────────────┼──────────────────┼──────────────────┘         │
│                            │                  │                             │
│                  ┌─────────▼──────────┐  ┌───▼──────────────────────┐     │
│                  │  Decision & Risk   │  │  Execution & Broker      │     │
│                  │      Service       │→ │      Service             │     │
│                  └────────────────────┘  └──────────────────────────┘     │
│                            │                                               │
│                  ┌─────────▼───────────────────────────────────────┐       │
│                  │    AI Policy & Narration Service                │       │
│                  │    (Policy Engine + Narration Engine)           │       │
│                  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 讀取/寫入
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Data Tier                                         │
│  ┌──────────────────────┐  ┌──────────────────────┐                        │
│  │   Raw Data DB        │  │   Feature Store      │                        │
│  │   (Daily Bars,       │  │   (100+ Factors      │                        │
│  │    Indicators, etc.) │  │    with versioning)  │                        │
│  └──────────────────────┘  └──────────────────────┘                        │
│  ┌──────────────────────┐  ┌──────────────────────┐                        │
│  │   Prediction DB      │  │   Policy DB          │                        │
│  │   (Predictions,      │  │   (Factor Weights,   │                        │
│  │    Snapshots)        │  │    Strategy Config,  │                        │
│  │                      │  │    Risk Config)      │                        │
│  └──────────────────────┘  └──────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 設計理念

- **避免寫死**：所有策略權重、風險參數、因子配置都由 Policy DB 管理，而非硬編碼
- **支援多市場**：透過抽象化 Data Ingestion Service，可接入台股、美股、期貨等不同市場
- **長期演進**：每個服務獨立部署、獨立擴展，允許逐步優化而不影響整體系統
- **職責分離**：Presentation 層不做運算，Application 層不做資料持久化，Data 層不包含業務邏輯

---

## 2. 三大 Tier：Presentation / Application / Data

### 2.1 Presentation Tier（展示層）

**職責**：只負責 UI 呈現與使用者互動，不做任何運算或業務邏輯

**組成**：
- **Trading UI**（React + TypeScript）
  - Dashboard 頁面
  - 四大作戰清單顯示（SmartWatchlist、PredictionTimelinePanel、SignalPanel 等）
  - 即時資料更新（透過 WebSocket）
- **War Room UI**（Next.js + Tailwind）
  - 多 AI 角色戰情室介面
  - 盤前作戰報告顯示
  - 即時事件串流（WebSocket）

**通訊方式**：
- REST API：取得初始資料、提交使用者指令
- WebSocket：接收即時事件流（預測更新、策略訊號、風險警示等）

**現況對照**：
- ✅ 已有：`trading-ui/jgod-trading-ui/`、`jgod/war_room_backend_v6/` 前端
- ⚠️ 暫時混在一起：部分業務邏輯仍在 UI 層（未來需移到 Application Tier）

---

### 2.2 Application Tier（應用層）

**職責**：所有 quant 運算、策略決策、API 服務都在這層

**設計原則**：
- 一組**獨立服務**（Microservices），而非單一 monolith
- 每個服務可獨立部署、擴展、重啟
- 服務間透過 Message Queue 或 REST API 通訊（避免直接資料庫耦合）

**組成**：
1. Data Ingestion Service
2. Data Quality & Event Service
3. Factor Engine Service
4. Prediction Service
5. Strategy & Signal Service
6. Decision & Risk Service
7. Execution & Broker Service
8. AI Policy & Narration Service（獨立於其他七個服務）

**現況對照**：
- ✅ 已有部分模組：`jgod/prediction/`、`jgod/factor/`、`jgod/risk/`、`jgod/execution/`
- ⚠️ 目前仍是 monolith：所有模組在同一 Python 專案中，未來需拆解成獨立服務
- 🔄 遷移方向：逐步將各模組抽離成獨立 FastAPI 服務，部署到不同容器

---

### 2.3 Data Tier（資料層）

**職責**：資料儲存、因子儲存、品質控管

**組成**：

#### 2.3.1 Raw Data Database
- **儲存內容**：原始市場資料（daily_bars、indicator_snapshots、metadata 等）
- **讀取者**：Data Ingestion Service、Factor Engine Service
- **寫入者**：Data Ingestion Service（從 FinMind、券商 API 等來源匯入）

#### 2.3.2 Feature Store（因子資產中樞）⭐

**定位**：J-GOD 的「因子資產中樞」，是 Layer 2/3 的唯一因子輸入管道

**核心設計理念**：
- Feature Store 是專門存放**已計算完成**的因子資料庫，不是一般資料表
- 它是 Factor Engine Service 與 Prediction/Strategy Service 之間的**唯一橋樑**

**儲存內容**：
- 已計算完成的 100+ 個因子（含 timestamp、symbol、版本號 version）
- 因子元資料（計算來源、參數、歷史統計等）
- 因子品質指標（例如：因子穩定度、相關性等）

**資料流向（單向）**：
```
Raw Data DB → [Factor Engine Service] → Feature Store → [Prediction/Strategy Service]
```

**讀取者**：
- Prediction Service：**只讀 Feature Store，不重新計算因子**
- Strategy & Signal Service：**只讀 Feature Store，不重新計算因子**

**寫入者**：
- Factor Engine Service：**只負責「算因子 → 寫入 Feature Store」**

**設計原則**：
- **完全解耦**：Factor Engine Service 與 Prediction/Strategy Service **完全解耦**
- **單一來源**：Prediction Service 不應直接存取 Raw Data DB，只能從 Feature Store 讀取因子
- **版本化支援**：Feature Store 支援版本化，允許因子演算法迭代而不影響歷史資料
- **資產化**：Feature Store 是 J-GOD 的「因子資產中樞」，所有已計算的因子都是可重用的資產

#### 2.3.3 Prediction Database
- **儲存內容**：預測結果（prediction_snapshots、ranking、概率分佈等）
- **讀取者**：Strategy & Signal Service、Decision & Risk Service、War Room UI
- **寫入者**：Prediction Service

#### 2.3.4 Policy Database（獨立配置儲存區）⭐
- **儲存內容**：
  - `factor_weights.json`：因子權重配置
  - `strategy_policy.yaml`：策略參數配置
  - `risk_config.json`：風險限制配置
- **讀取者**：所有 Application Tier 服務（啟動時讀取配置，而非硬編碼）
- **寫入者**：AI Policy & Narration Service 的 Policy Engine（根據回測與真實績效回饋自動更新）
- **設計原則**：
  - Policy Engine 的運作是「閉環」：根據回測與真實績效回饋，決定「明天」的策略與權重
  - Policy Engine 只寫入 Policy DB，不直接操作其他服務的運算資料庫

**現況對照**：
- ✅ 已有：`data/jgod_tw_stock.db`（SQLite，包含 daily_bars、indicator_snapshots、prediction_snapshots）
- ⚠️ **目前 Feature Store 概念尚未明確分離**：因子計算結果直接寫入 `indicator_snapshots`，與 Raw Data 混在一起
- 🔄 **遷移方向**：
  - **立即行動**：將 `indicator_snapshots` 重新定位為 Feature Store（或建立獨立的 `feature_store` 資料表）
  - 明確區分：Raw Data DB（只存原始市場資料）vs Feature Store（只存已計算的因子）
  - 建立 `policy_db` 或 `config_db`，儲存 Policy Engine 輸出的配置檔案（`factor_weights.json`、`strategy_policy.yaml`、`risk_config.json`）

---

## 3. 六個邏輯 Layer（L0~L5）

### L0：Raw Data（原始資料層）

**職責**：從外部來源取得原始市場資料

**資料來源**：
- FinMind API（台股歷史資料、即時報價）
- 券商 API（真實交易資料）
- 國際市場資料來源（美股、期貨等）

**現有模組對照**：
- `jgod/data/finmind_loader.py`
- `jgod/path_a/finmind_data_loader.py`
- `jgod/api_clients/finmind_client.py`

**狀態**：✅ 已有基礎實作

---

### L1：Factor / Indicator（因子計算層）

**職責**：將原始資料轉換為可用的因子（Factor）

**因子分類**（100+ 個因子）：
- **P 類**：價格相關因子（Price Factors）
- **C 類**：成交量相關因子（Volume Factors）
- **F 類**：財務相關因子（Fundamental Factors）
- **K 類**：技術指標因子（Technical Indicators）
- **S 類**：統計因子（Statistical Factors）
- **Q 類**：品質因子（Quality Factors）
- **X 類**：其他因子（Extra Factors）
- **M 類**：市場相關因子（Market Factors）

**現有模組對照**：
- `jgod/factor/factor_engine.py`
- `jgod/alpha_engine/`（各種因子實作：flow_factor.py、inertia_factor.py 等）
- `jgod/prediction/feature_builder.py`

**狀態**：✅ 已有基礎實作，但因子計算邏輯分散在多個檔案

**未來方向**：
- 統一透過 Factor Engine Service 計算所有因子
- 計算結果寫入 **Feature Store**（而非直接寫入 Raw DB）

---

### L2：Prediction Engine（預測引擎層）

**職責**：根據因子輸出預測結果

**輸出內容**：
- `Upside`：預期上漲幅度
- `Downside`：預期下跌幅度
- `Prob_up`：上漲概率
- `Prob_down`：下跌概率

**現有模組對照**：
- `jgod/prediction/prediction_engine.py`
- `jgod/prediction/ranking.py`

**狀態**：✅ 已有基礎實作

**設計原則**：
- **只從 Feature Store 讀取因子**，不直接存取 Raw Data DB
- 預測結果寫入 Prediction DB

---

### L3：Strategy & Signal（策略與訊號層）

**職責**：根據預測結果與策略規則，產生交易訊號

**策略類型**（10+ 策略）：
- StockUpsideFilter60V1
- 其他自訂策略

**輸出內容**：
- 策略訊號（買入/賣出/持有）
- `risk_flags`：風險旗標
- `positive_factors`：正向因子列表
- `negative_factors`：負向因子列表

**現有模組對照**：
- `jgod/strategy/`（策略模組）
- `jgod/signal/signal_engine.py`

**狀態**：✅ 已有部分實作

**設計原則**：
- **只從 Feature Store 讀取因子**，不重新計算
- 從 Prediction DB 讀取預測結果
- 策略參數從 Policy DB 讀取（而非硬編碼）

---

### L4：Decision & Risk（決策與風險層）

**職責**：整合策略訊號，計算最適投資組合（w*），執行風險控管

**功能**：
- Mean-Variance 優化
- 計算最適權重向量（w*）
- Regime 切換邏輯（市場狀態判斷）
- 風險參數 λ 調整
- 四大作戰清單排序

**現有模組對照**：
- `jgod/optimizer/`（Mean-Variance 優化）
- `jgod/risk/risk_engine.py`、`jgod/risk/risk_model.py`
- `jgod/path_a/path_a_backtest.py`（回測與評估）

**狀態**：⚠️ 有部分實作，但尚未完整整合

**未來方向**：
- 整合 Backtest / Path A 回測報表到 Decision & Risk Service
- 風險參數從 Policy DB 讀取

---

### L5：Visualization & Execution（視覺化與執行層）

**職責**：呈現結果給使用者，執行交易指令

**組成**：
- **Visualization**：War Room UI + Trading UI（Presentation Tier）
- **Execution**：Execution & Broker Service（Application Tier）

**現有模組對照**：
- `jgod/war_room_backend/`、`jgod/war_room_backend_v6/`（War Room 後端）
- `trading-ui/jgod-trading-ui/`（Trading UI 前端）
- `jgod/execution/execution_engine.py`、`jgod/execution/virtual_broker.py`

**狀態**：✅ 已有基礎實作（War Room v5/v6、Trading UI v1）

---

## 4. 七個 Microservices

### 4.1 Data Ingestion Service（資料匯入服務）

**角色定位**：資料警備司令

**職責**：
- 從外部來源（FinMind、券商 API）取得原始市場資料
- 資料清洗與標準化
- 寫入 Raw Data Database

**輸入**：
- FinMind API 回應
- 券商 API 回應
- 國際市場資料來源

**輸出**：
- 寫入 Raw Data DB（daily_bars、metadata 等）
- 發送資料事件到 Message Queue（`J-GOD_DATA_ALERT`）

**對應 Layer / Tier**：
- Layer：L0（Raw Data）
- Tier：Application Tier → Data Tier

**現有模組對照**：
- `jgod/data/finmind_loader.py`
- `jgod/path_a/finmind_data_loader.py`
- `scripts/backfill_*.py`（Backfill 腳本）

**未來方向**：
- 獨立成 FastAPI 服務
- 支援排程執行（每日自動匯入前一日資料）
- 透過 MQ 通知其他服務資料已更新

---

### 4.2 Data Quality & Event Service（資料品質與事件服務）

**角色定位**：資料品質監控中心

**職責**：
- 監控 Raw Data DB 資料品質（缺失值、異常值、時序連續性）
- 產生資料品質報告
- 發送資料品質事件到 Message Queue

**輸入**：
- 監聽 Raw Data DB 變更
- 接收 Data Ingestion Service 的資料事件

**輸出**：
- 資料品質報告（寫入資料庫或檔案）
- 發送事件到 MQ（`J-GOD_DATA_ALERT`）

**對應 Layer / Tier**：
- Layer：L0 → L1（資料品質檢查）
- Tier：Application Tier

**現有模組對照**：
- `jgod/diagnostics/diagnosis_engine.py`
- `jgod/diagnostics/health_check.py`

**未來方向**：
- 獨立成服務，持續監控資料品質
- 異常時自動發送告警

---

### 4.3 Factor Engine Service（因子引擎服務）

**角色定位**：因子研究員

**職責**：
- 從 Raw Data DB 讀取原始資料
- 計算 100+ 個因子（P/C/F/K/S/Q/X/M 類）
- **寫入 Feature Store**（因子資產中樞）

**輸入**：
- 讀取 Raw Data DB（daily_bars、indicator_snapshots 等）
- 接收資料更新事件（從 MQ）

**輸出**：
- **只寫入 Feature Store**（含 timestamp、symbol、版本號）
- 不直接提供給 Prediction/Strategy Service（這些服務應從 Feature Store 讀取）
- 發送 Feature Store 更新事件到 MQ（`J-GOD_FEATURE_UPDATE`）

**對應 Layer / Tier**：
- Layer：L1（Factor / Indicator）
- Tier：Application Tier → Data Tier（Feature Store）

**現有模組對照**：
- `jgod/factor/factor_engine.py`
- `jgod/alpha_engine/`（各種因子實作：flow_factor.py、inertia_factor.py 等）
- `jgod/prediction/feature_builder.py`

**設計原則**：
- **只負責計算因子 → 寫入 Feature Store**
- 與 Prediction/Strategy Service **完全解耦**（這些服務不應知道因子如何計算）
- Factor Engine Service 是 Feature Store 的**唯一寫入者**，確保因子資料的一致性

---

### 4.4 Prediction Service（預測服務）

**角色定位**：模型總審查官

**職責**：
- **從 Feature Store 讀取因子**（不重新計算）
- 執行預測模型，計算 Upside / Downside / Prob_up / Prob_down
- 寫入 Prediction DB

**輸入**：
- **只讀 Feature Store**（不直接存取 Raw Data DB）
- 接收 Feature Store 更新事件（從 MQ）

**輸出**：
- 寫入 Prediction DB（prediction_snapshots、ranking 等）
- 發送預測事件到 MQ

**對應 Layer / Tier**：
- Layer：L2（Prediction Engine）
- Tier：Application Tier → Data Tier（Prediction DB）

**現有模組對照**：
- `jgod/prediction/prediction_engine.py`
- `jgod/prediction/ranking.py`

**設計原則**：
- **只從 Feature Store 讀取因子**，不重新計算
- 預測邏輯參數從 Policy DB 讀取（而非硬編碼）

---

### 4.5 Strategy & Signal Service（策略與訊號服務）

**角色定位**：策略指揮官

**職責**：
- **從 Feature Store 讀取因子**（不重新計算）
- 從 Prediction DB 讀取預測結果
- 根據策略規則產生交易訊號
- 輸出 risk_flags、positive_factors、negative_factors

**輸入**：
- **只讀 Feature Store**（不直接存取 Raw Data DB）
- 讀取 Prediction DB
- 讀取 Policy DB（策略參數配置）

**輸出**：
- 策略訊號（寫入資料庫或發送到 MQ）
- 發送訊號事件到 MQ（`J-GOD_SIGNAL_UPDATE`）

**對應 Layer / Tier**：
- Layer：L3（Strategy & Signal）
- Tier：Application Tier

**現有模組對照**：
- `jgod/strategy/`（策略模組）
- `jgod/signal/signal_engine.py`

**設計原則**：
- **只從 Feature Store 讀取因子**，不重新計算
- 策略規則從 Policy DB 讀取（而非硬編碼）

---

### 4.6 Decision & Risk Service（決策與風險服務）

**角色定位**：智能裁判官

**職責**：
- 整合策略訊號
- 執行 Mean-Variance 優化，計算最適權重向量（w*）
- 執行風險控管（Regime 切換、風險參數 λ 調整）
- 產生四大作戰清單排序

**輸入**：
- 讀取策略訊號（從 Strategy & Signal Service 或 MQ）
- 讀取 Policy DB（風險參數配置、優化目標函數參數）
- 讀取 Backtest / Path A 回測結果（用於 Regime 判斷）

**輸出**：
- 最適權重向量（w*）
- 風險評估報告
- 四大作戰清單（寫入資料庫或發送到 MQ）
- 發送決策事件到 MQ（`J-GOD_OPTIMAL_WEIGHTS`）

**對應 Layer / Tier**：
- Layer：L4（Decision & Risk）
- Tier：Application Tier

**現有模組對照**：
- `jgod/optimizer/`（Mean-Variance 優化）
- `jgod/risk/risk_engine.py`、`jgod/risk/risk_model.py`
- `jgod/path_a/path_a_backtest.py`（回測與評估）

**未來方向**：
- 整合 Backtest / Path A 回測報表到本服務
- 風險參數從 Policy DB 讀取（而非硬編碼）

---

### 4.7 Execution & Broker Service（執行與券商服務）

**角色定位**：行動執行官 + **最後一道煞車**（硬風控否決權）⭐

**職責**：
- 接收 Decision & Risk Service 輸出的 w*（最適權重建議）
- **執行獨立的「硬風控檢查」**（在實際送出交易指令之前）
- 將交易指令發送到券商 API 或虛擬券商

#### 硬風控檢查項目（否決權）⭐

即使 Decision & Risk Service 已經輸出了 w*，Execution Service 在實際送出交易指令之前，**必須執行一套獨立的「硬風控檢查」**，有權否決任何違反硬風控規則的下單指令。

**硬風控規則範例**：
- **單一股票持股比例上限**：例如單一股票不得超過總資產的 20%
- **總曝險上限**：Gross Exposure / Net Exposure 不得超過設定值
- **單日最大虧損限制**：例如單日虧損不得超過總資產的 2%
- **禁止交易名單**：黑名單標的、法規限制標的（例如：ST 股、暫停交易標的）
- **流動性限制**：例如日均成交量不得低於某個門檻

**設計原則**：
- **Decision & Risk Service 是「最佳解建議」**：它根據 Mean-Variance 優化與風險模型，提供理論上的最適權重
- **Execution Service 是「最後一道煞車」**：它必須確保任何實際執行的交易指令都符合硬風控規則
- 如果 w* 違反硬風控規則，Execution Service **應拒絕執行**，並回報錯誤原因

**輸入**：
- 接收 Decision & Risk Service 的 w*（從 MQ 或 REST API）
- 讀取 Policy DB（硬風控規則配置）
- 讀取當前持倉狀態（從資料庫）

**輸出**：
- 實際交易指令（發送到券商 API 或虛擬券商）
- 交易記錄（寫入資料庫）
- 發送交易事件到 MQ（`J-GOD_POSITION_UPDATE`）
- 如果硬風控檢查失敗，發送拒絕事件到 MQ

**對應 Layer / Tier**：
- Layer：L5（Execution）
- Tier：Application Tier

**現有模組對照**：
- `jgod/execution/execution_engine.py`
- `jgod/execution/virtual_broker.py`
- `jgod/execution/broker_adapter.py`
- `jgod/path_e/risk_guard.py`（部分硬風控邏輯）

**未來方向**：
- 強化硬風控檢查邏輯（獨立於 Decision & Risk Service）
- 硬風控規則從 Policy DB 讀取（而非硬編碼）
- 支援真實券商 API 對接

---

## 5. AI Policy & Narration Service（第 8 個服務）

**定位**：J-GOD 的「腦中腦」——不負責直接算 K 線 / 分數，而是負責「策略進化」與「結果詮釋」

**設計理念**：
- 讓 J-GOD 既穩定又會自己進化
- 所有策略權重、因子配置、風險參數都由 Policy Engine 動態調整，而非寫死
- Narration Engine 將機器輸出轉換成人類可理解的「盤前作戰報告」

---

### 5.1 Policy Engine（政策引擎）

**職責**：根據回測與真實績效回饋，動態調整策略參數

#### 輸入（Input）

Policy Engine 從以下來源讀取資料：

1. **Path A / Backtest & Evaluation 服務或模組**：
   - 策略績效報告（Strategy Performance Log）
   - 因子貢獻度 / 因子歸因（Factor Attribution）
   - 回測結果（Sharpe Ratio、Max Drawdown、Win Rate 等）

2. **Execution & Broker Service**：
   - 實際交易績效（Real-time Performance）
   - 硬風控觸發記錄（哪些交易被拒絕、原因為何）

#### 輸出（Output）

Policy Engine **只寫入 Policy DB**（或 config 儲存區），不直接操作其他服務的運算資料庫。

**輸出檔案範例**：
- `factor_weights.json`：因子權重配置
  ```json
  {
    "factor_P001": 0.15,
    "factor_C002": 0.12,
    "factor_F003": 0.08,
    ...
  }
  ```
- `strategy_policy.yaml`：策略參數配置
  ```yaml
  strategies:
    StockUpsideFilter60V1:
      enabled: true
      min_score: 0.7
      max_holdings: 20
  ```
- `risk_config.json`：風險參數配置
  ```json
  {
    "lambda": 0.5,
    "max_single_stock_weight": 0.2,
    "max_gross_exposure": 1.5,
    "daily_loss_limit": 0.02
  }
  ```

#### 閉環運作機制

Policy Engine 的運作是「閉環」：
1. 讀取回測與真實績效資料
2. 分析因子貢獻度、策略表現、風險指標
3. 決定「明天」的策略與權重（寫入 Policy DB）
4. 其他服務（Factor Engine、Prediction、Strategy、Decision、Execution）在啟動時讀取 Policy DB
5. 執行一段時間後，Policy Engine 再次分析績效，調整參數，形成閉環

**設計原則**：
- Policy Engine **只寫入 Policy DB**，不直接操作其他服務的運算資料庫
- 其他服務在啟動時或定期重新載入 Policy DB 的配置
- 這樣設計可以讓 Policy Engine 獨立演進，而不影響其他服務的穩定性

---

### 5.2 Narration Engine（敘述引擎）

**職責**：將機器輸出轉換成人類可理解的「盤前作戰報告」與「個股說明」

**輸入**：
- 四大作戰清單（從 Decision & Risk Service）
- 最適權重向量 w*（從 Decision & Risk Service）
- 風險旗標（從 Strategy & Signal Service）
- 回測績效（從 Backtest / Path A）
- 因子貢獻度（從 Performance Attribution）

**輸出**：
- **盤前作戰報告**（Markdown 格式）：整體市場觀點、策略建議、風險警示
- **個股說明**（JSON 格式）：每檔股票的買入理由、風險提示、目標價位
- 發送到 War Room UI（透過 WebSocket 或 REST API）

**現有模組對照**：
- `jgod/war_room/`（War Room 的 AI 角色系統）
- War Room v5/v6 的「多角色戰情室」可視為 Narration Engine 的前身

**設計原則**：
- Narration Engine **不負責計算**（不計算 K 線、分數、權重）
- 只負責「詮釋」與「呈現」
- 可透過 LLM（GPT、Claude、Gemini）生成自然語言報告

---

### 5.3 為什麼這樣設計？

**穩定 + 進化**：
- 其他 7 個服務專注於「穩定執行」：讀取配置、執行運算、輸出結果
- Policy Engine 專注於「策略進化」：分析績效、調整參數、優化配置
- 兩者分離，讓系統既穩定又能自動優化

**避免寫死**：
- 所有策略參數、風險配置都由 Policy DB 管理
- 工程師不需要修改程式碼，只需要調整 Policy DB 的配置檔案
- Policy Engine 可以自動根據績效調整配置

---

## 6. 訊息佇列 / 非同步通訊（Decoupling Strategy）

### 設計理念

未來服務之間應盡量用 **Message Queue**（Kafka / RabbitMQ）溝通，而不是彼此硬 call REST API。

**優點**：
- **避免寫死耦合**：服務不需要知道其他服務的 IP/Port，只需要知道 MQ Topic
- **水平擴展**：可以啟動多個服務實例，MQ 自動分配訊息
- **容錯性**：如果某個服務暫時掛掉，訊息會保留在 MQ 中，服務重啟後可以繼續處理
- **解耦**：服務可以獨立演進，只要訊息格式不變，內部實作可以任意修改

---

### 關鍵 Message Queue Topics

#### `J-GOD_DATA_ALERT`
- **發送者**：Data Ingestion Service、Data Quality & Event Service
- **內容**：資料更新事件（例如：新的一日資料已匯入、資料品質異常）
- **訂閱者**：Factor Engine Service（收到事件後開始計算因子）

#### `J-GOD_FEATURE_UPDATE`
- **發送者**：Factor Engine Service
- **內容**：Feature Store 更新事件（例如：新的因子計算完成）
- **訂閱者**：Prediction Service、Strategy & Signal Service（收到事件後開始預測/策略計算）

#### `J-GOD_PREDICTION_UPDATE`
- **發送者**：Prediction Service
- **內容**：預測結果更新事件
- **訂閱者**：Strategy & Signal Service、War Room UI

#### `J-GOD_SIGNAL_UPDATE`
- **發送者**：Strategy & Signal Service
- **內容**：策略訊號更新事件
- **訂閱者**：Decision & Risk Service

#### `J-GOD_OPTIMAL_WEIGHTS`
- **發送者**：Decision & Risk Service
- **內容**：最適權重向量 w*、四大作戰清單
- **訂閱者**：Execution & Broker Service、War Room UI

#### `J-GOD_POSITION_UPDATE`
- **發送者**：Execution & Broker Service
- **內容**：實際交易執行結果、持倉變更
- **訂閱者**：Decision & Risk Service（用於下次優化）、Policy Engine（用於績效分析）、War Room UI

---

### 現況與未來方向

**現況**：
- ⚠️ 目前服務之間主要透過直接呼叫函數或 REST API，尚未使用 Message Queue
- ✅ 部分模組已有事件機制（例如：War Room 的 WebSocket 事件流）

**未來方向**：
- Phase 1：先讓服務間透過 REST API 通訊（已在進行）
- Phase 2：引入 RabbitMQ 或 Kafka，逐步將同步呼叫改為非同步訊息
- Phase 3：所有服務間通訊都透過 MQ，REST API 僅用於對外提供服務

---

## 7. 與現有 JarvisV1 的對照表

| 現有模組 / 檔案 | 對應 Service | 對應 Layer | 對應 Tier | 狀態 |
|---|---|---|---|---|
| `jgod/data/finmind_loader.py` | Data Ingestion Service | L0 | Application → Data | ✅ 已有基礎，未來需獨立成服務 |
| `jgod/path_a/finmind_data_loader.py` | Data Ingestion Service | L0 | Application → Data | ✅ 已有基礎 |
| `scripts/backfill_*.py` | Data Ingestion Service | L0 | Application → Data | ✅ 已有基礎，Backfill 腳本 |
| `jgod/diagnostics/diagnosis_engine.py` | Data Quality & Event Service | L0 → L1 | Application | ✅ 已有基礎，未來需獨立成服務 |
| `jgod/factor/factor_engine.py` | Factor Engine Service | L1 | Application → Data (Feature Store) | ✅ 已有基礎，需強化 Feature Store 概念 |
| `jgod/alpha_engine/` | Factor Engine Service | L1 | Application → Data (Feature Store) | ✅ 已有基礎，因子實作分散 |
| `jgod/prediction/feature_builder.py` | Factor Engine Service | L1 | Application → Data (Feature Store) | ✅ 已有基礎 |
| `jgod/prediction/prediction_engine.py` | Prediction Service | L2 | Application → Data (Prediction DB) | ✅ 已有基礎，需改為只讀 Feature Store |
| `jgod/prediction/ranking.py` | Prediction Service | L2 | Application → Data (Prediction DB) | ✅ 已有基礎 |
| `jgod/strategy/` | Strategy & Signal Service | L3 | Application | ✅ 已有基礎，需強化策略配置管理 |
| `jgod/signal/signal_engine.py` | Strategy & Signal Service | L3 | Application | ✅ 已有基礎 |
| `jgod/optimizer/` | Decision & Risk Service | L4 | Application | ✅ 已有基礎，需整合 Backtest |
| `jgod/risk/risk_engine.py` | Decision & Risk Service | L4 | Application | ✅ 已有基礎 |
| `jgod/risk/risk_model.py` | Decision & Risk Service | L4 | Application | ✅ 已有基礎 |
| `jgod/path_a/path_a_backtest.py` | Decision & Risk Service + Policy Engine | L4 | Application | ✅ 已有基礎，需整合到 Decision Service |
| `jgod/execution/execution_engine.py` | Execution & Broker Service | L5 | Application | ✅ 已有基礎，需強化硬風控 |
| `jgod/execution/virtual_broker.py` | Execution & Broker Service | L5 | Application | ✅ 已有基礎 |
| `jgod/path_e/risk_guard.py` | Execution & Broker Service | L5 | Application | ⚠️ 部分硬風控邏輯，需整合 |
| `jgod/war_room/` | Narration Engine（部分） | L5 | Application | ✅ 已有基礎，AI 角色系統 |
| `jgod/war_room_backend/` | War Room Backend | L5 | Application → Presentation | ✅ 已有基礎，FastAPI + WebSocket |
| `jgod/war_room_backend_v6/` | War Room Backend v6 | L5 | Application → Presentation | ✅ 已有基礎 |
| `trading-ui/jgod-trading-ui/` | Trading UI | L5 | Presentation | ✅ 已有基礎，React + TypeScript |
| `data/jgod_tw_stock.db` | Raw Data DB + Feature Store + Prediction DB | L0 → L5 | Data | ✅ 已有基礎，需明確分離 Feature Store |
| `jgod/api/main.py` | API Gateway（部分） | - | Application | ✅ 已有基礎，REST API |

### 狀態說明

- ✅ **已有基礎**：現有模組已經符合未來架構的一部分，但可能需要重構或強化
- ⚠️ **暫時先當 monolith**：目前與其他模組混在一起，未來需要拆分
- 🔄 **未來需拆分**：目前是單一服務的一部分，未來需獨立成服務

---

## 8. Roadmap：從原型到七服務架構

### Phase 1：Layer 邏輯分清楚（**目前階段**）

**目標**：在 monolith 裡把 Layer 邏輯分清楚

**工作項目**：
- ✅ 明確區分 L0~L5 各層職責
- ✅ 建立 Feature Store 概念（將 `indicator_snapshots` 重新定位為 Feature Store）
- ✅ 強化 Factor Engine → Feature Store 的資料流
- ✅ 確保 Prediction Service 只從 Feature Store 讀取因子
- ✅ 建立 Policy DB 概念（獨立配置儲存區）

**狀態**：🔄 進行中

---

### Phase 2：整合 Backtest / Path A 到 Decision & Risk Service

**目標**：把 Backtest / Path A / 回測報表納入 Decision & Risk Service 的範圍

**工作項目**：
- 整合 `jgod/path_a/path_a_backtest.py` 到 Decision & Risk Service
- 建立回測結果 → Policy Engine 的資料流
- Policy Engine 開始讀取回測績效，自動調整策略參數

**預估時間**：1-2 個月

---

### Phase 3：抽離 Data Ingestion / Factor Engine 成獨立服務

**目標**：將 Data Ingestion 與 Factor Engine 獨立成 FastAPI 服務

**工作項目**：
- 將 `jgod/data/`、`jgod/path_a/finmind_data_loader.py` 抽離成 Data Ingestion Service
- 將 `jgod/factor/`、`jgod/alpha_engine/` 抽離成 Factor Engine Service
- 建立服務間 REST API 通訊機制
- 部署到獨立容器（Docker）

**預估時間**：2-3 個月

---

### Phase 4：導入 Message Queue，開始拆 War Room / Execution

**目標**：引入 MQ，逐步將同步呼叫改為非同步訊息

**工作項目**：
- 引入 RabbitMQ 或 Kafka
- 定義關鍵 Topic（`J-GOD_DATA_ALERT`、`J-GOD_OPTIMAL_WEIGHTS` 等）
- 將部分服務間通訊改為 MQ 訊息
- 獨立 Execution & Broker Service
- 強化 Execution Service 的硬風控檢查（否決權）

**預估時間**：3-4 個月

---

### Phase 5：完整七服務架構 + AI Policy Service

**目標**：所有服務獨立部署，Policy Engine 開始自動調整策略

**工作項目**：
- 所有 7 個服務獨立部署
- Policy Engine 完整實作（讀取回測績效、自動調整配置）
- Narration Engine 完整實作（生成盤前作戰報告）
- 完整 MQ 架構
- 監控與日誌系統

**預估時間**：6-12 個月

---

## 附錄：關鍵設計原則總結

1. **Feature Store 是因子資產中樞**：Factor Engine 只負責計算並寫入，Prediction/Strategy 只從 Feature Store 讀取
2. **Policy Engine 是閉環核心**：根據績效回饋自動調整配置，其他服務只讀取 Policy DB
3. **Execution Service 有硬風控否決權**：即使 Decision Service 輸出 w*，Execution 仍可拒絕違反硬風控的交易
4. **服務間透過 MQ 解耦**：避免寫死耦合，支援水平擴展
5. **Presentation 層不做運算**：只負責 UI 呈現，所有業務邏輯在 Application Tier

---

**文件版本**：v1.0  
**最後更新**：2024-12  
**維護者**：J-GOD 系統總架構師

