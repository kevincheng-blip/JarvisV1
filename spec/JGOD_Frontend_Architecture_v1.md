# J-GOD 前端架構 v1

**文件版本：** 1.0  
**最後更新：** 2025-01-06  
**目標讀者：** 前端工程師、UI/UX 設計師

---

## 文件說明

本文檔描述 `trading-ui/jgod-trading-ui/` 前端架構，包括技術棧、頁面結構、組件設計、狀態管理與 API 整合。重點說明 War Room V2 UI 設計。

---

## 1. 技術棧與專案結構

### 1.1 技術棧

| 技術 | 版本/說明 | 用途 |
|------|-----------|------|
| React | 18 | UI 框架 |
| TypeScript | - | 型別安全 |
| Vite | - | 建置工具 |
| Recharts | - | 圖表庫 |
| Axios | - | HTTP 客戶端 |
| react-i18next | - | 國際化 |
| React Hooks | - | 狀態管理（目前） |

### 1.2 專案結構

```
trading-ui/jgod-trading-ui/
├── src/
│   ├── api/              # API 客戶端
│   ├── components/       # UI 組件
│   │   ├── war-room/     # War Room 專用組件
│   │   └── war-room-v2/  # War Room V2 組件
│   ├── hooks/            # 自訂 Hooks
│   ├── pages/            # 頁面組件
│   ├── store/            # 狀態管理（Zustand?）
│   ├── types/            # TypeScript 型別定義
│   └── i18n/             # 國際化資源
├── public/
└── package.json
```

---

## 2. 頁面結構

### 2.1 DashboardPage.tsx - 主儀表板

**路徑：** `/` 或 `/dashboard`

**功能模組：**
- **SmartWatchlist**：智能自選股列表（左側固定）
- **WatchlistPanel**：預測列表（表格）
- **PredictionSummaryPanel**：預測摘要
- **PredictionTimelinePanel**：預測時間序列圖表（Recharts）
- **SignalPanel**：最新預測訊號
- **CoverageHeatmapPanel**：覆蓋率熱力圖
- **PolicyPanel**：政策面板
- **ErrorDoctrinePanel**：錯誤教條面板

**狀態管理：**
- `selectedDate` - 選中的日期
- `predictions` - 預測列表
- `coverage` - 覆蓋率資料
- `selectedSymbol` - 選中的股票代號
- `timelineSymbol` - Timeline 顯示的股票（預設：2330）

**API 呼叫：**
- `api.getPredictions(date)`
- `api.getCoverage(universe, fromDate, toDate)`
- `api.getPredictionTimeline(symbol)`
- `api.getLatestPrediction(symbol)`

---

### 2.2 WarRoomPage.tsx - War Room 頁面

**路徑：** `/war-room`

**功能：** 整合 War Room V2 組件

**完整度：** ✅ 中

---

### 2.3 WarRoomV2Dashboard.tsx - War Room V2 儀表板

**路徑：** `/war-room-v2`

**功能模組：**
- **ExecutiveSummary**：執行摘要（頂部）
- **TopPredictionsPanel**：Top N 預測面板（左側主要內容）
- **SRankTrendCard**：S-Rank 趨勢卡片（右側）
- **PatchQueueCard**：Patch 佇列卡片（右側）
- **AbTestSummaryCard**：A/B 測試摘要卡片（右側）
- **DecisionContextDrawer**：決策上下文側邊欄（點擊預測項目時顯示）

**UI 佈局：**
```
┌─────────────────────────────────────────┐
│  ExecutiveSummary                       │
├──────────────────┬──────────────────────┤
│                  │  SRankTrendCard       │
│ TopPredictions   │  PatchQueueCard       │
│ Panel            │  AbTestSummaryCard     │
│                  │                       │
└──────────────────┴──────────────────────┘
```

**完整度：** ✅ 中高

---

### 2.4 DMC 頁面組（Doctrine Management Console）

#### DMCPage.tsx
**路徑：** `/dmc`

**功能：** Doctrine 條文列表與管理

#### DMCEditPage.tsx
**路徑：** `/dmc/edit/:section_id`

**功能：** 編輯 Doctrine 條文

#### DMCPatchPage.tsx
**路徑：** `/dmc/patch`

**功能：** Patch 管理與審核

#### DMCReviewPage.tsx
**路徑：** `/dmc/review`

**功能：** Doctrine 條文審核工作流

**完整度：** ✅ 中

---

### 2.5 DecisionABTestPage.tsx

**路徑：** `/decision-ab-test`

**功能：** Decision Layer A/B 測試儀表板

**完整度：** ✅ 中

---

### 2.6 RuleSimListPage.tsx / RuleSimDetailPage.tsx

**路徑：** `/rule-sim` / `/rule-sim/:experiment_id`

**功能：** 規則模擬實驗列表與詳情

**完整度：** ✅ 中

---

### 2.7 KnowledgeGovernanceDashboard.tsx

**路徑：** `/knowledge-governance`

**功能：** 知識庫治理與監控

**完整度：** ✅ 中

---

## 3. 核心共用組件

### 3.1 SmartWatchlist.tsx

**位置：** `src/components/SmartWatchlist.tsx`

**功能：**
- 智能自選股列表
- 收藏功能（localStorage 持久化）
- 最近使用記錄（最多 20 個）
- 智能排序：收藏 → 最近使用 → 全部

**Props：**
```typescript
{
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
}
```

---

### 3.2 PredictionTimelinePanel.tsx

**位置：** `src/components/PredictionTimelinePanel.tsx`

**功能：**
- Recharts 折線圖顯示預測分數時間序列
- Signal-based 顏色編碼（BUY/STRONG_BUY/SHORT/AVOID）
- 自訂 Tooltip（顯示日期、分數、訊號）
- 高度：300px，響應式寬度

**Props：**
```typescript
{
  symbol: string;
  startDate: string;
  endDate: string;
}
```

---

### 3.3 SignalPanel.tsx

**位置：** `src/components/SignalPanel.tsx`

**功能：**
- 顯示最新預測結果
- **主訊號區塊**：signal, score, 日期
- **Positive/Negative Factors**：只顯示 code，hover 顯示完整內容
- **Risk Flags**：顯示 message 和 severity
- **J-GOD 建議**：人性化中文建議文字

**Props：**
```typescript
{
  symbol: string;
}
```

---

### 3.4 WatchlistPanel.tsx

**位置：** `src/components/WatchlistPanel.tsx`

**功能：**
- 顯示指定日期的所有股票預測列表
- 表格格式：symbol, name, verdict, total_score, sector

**Props：**
```typescript
{
  predictions: Prediction[];
  loading: boolean;
}
```

---

### 3.5 CoverageHeatmapPanel.tsx

**位置：** `src/components/CoverageHeatmapPanel.tsx`

**功能：** 股票覆蓋率熱力圖

**完整度：** ⚠️ 可能未完全實作

---

### 3.6 PolicyPanel.tsx

**位置：** `src/components/PolicyPanel.tsx`

**功能：** 政策面板（顯示政策配置與健康度）

---

### 3.7 ErrorDoctrinePanel.tsx

**位置：** `src/components/ErrorDoctrinePanel.tsx`

**功能：** 錯誤教條面板（顯示 Doctrine 違規與錯誤）

---

## 4. War Room / War Room V2 專用組件

### 4.1 War Room 組件（`src/components/war-room/`）

#### macro/ - 總體層級組件
- **AggregateRisk.tsx**：總體風險
- **EquityCurve.tsx**：權益曲線
- **ExposureHeatmap.tsx**：曝險熱力圖
- **FinalOrders.tsx**：最終訂單
- **PolicyHealthV2.tsx**：政策健康度

#### micro/ - 微觀層級組件
- **MicrostructureFactors.tsx**：微觀結構因子
- **SignalConflictMap.tsx**：訊號衝突圖
- **SRankRankingCard.tsx**：S-Rank 排名卡片
- **StrategyRadarMini.tsx**：策略雷達（迷你版）
- **TopLongPanel.tsx**：Top Long 面板
- **TopShortPanel.tsx**：Top Short 面板

#### anomaly/ - 異常監控組件
- **DoctrineAlertPanel.tsx**：Doctrine 警報
- **ErrorReplayPanel.tsx**：錯誤重播面板
- **ErrorReplayViewer.tsx**：錯誤重播檢視器
- **KnowledgeGovernancePanel.tsx**：知識治理面板
- **PositionHealthPanel.tsx**：部位健康度
- **SentimentGauge.tsx**：情緒指標
- **SystemLogStream.tsx**：系統日誌流

---

### 4.2 War Room V2 組件（`src/components/war-room-v2/`）

#### ExecutiveSummary.tsx
**功能：** 執行摘要（系統狀態、關鍵指標總覽）

#### TopPredictionsPanel.tsx
**功能：** Top N 預測面板（顯示 Top Long/Short 列表）

**Props：**
```typescript
{
  onPredictionClick: (symbol: string, item: TopLongItem | TopShortItem) => void;
}
```

#### SRankTrendCard.tsx
**功能：** S-Rank 趨勢卡片（顯示 S-Rank 排名趨勢）

#### PatchQueueCard.tsx
**功能：** Patch 佇列卡片（顯示待審核的 Doctrine Patches）

#### AbTestSummaryCard.tsx
**功能：** A/B 測試摘要卡片（顯示 Decision AB Test 摘要）

---

## 5. 狀態管理策略

### 5.1 目前狀態

**混合模式：**
- **本地狀態**：大部分頁面使用 `useState`（如 DashboardPage）
- **集中式 Store**：`src/store/warRoomStore.ts`（可能使用 Zustand）
- **自訂 Hooks**：封裝 API 呼叫與狀態邏輯

### 5.2 自訂 Hooks（`src/hooks/`）

| Hook | 功能 | 對應 API |
|------|------|----------|
| `useDecisionAbTest.ts` | Decision A/B 測試 | `/api/v1/decision-ab/*` |
| `useDoctrineAlerts.ts` | Doctrine 警報 | `/api/v1/doctrine/alerts` |
| `useDoctrinePatches.ts` | Doctrine Patches | `/api/v1/doctrine/patches` |
| `useDoctrineV2.ts` | Doctrine V2 | `/api/v2/doctrine/*` |
| `useErrorReplay.ts` | 錯誤重播 | `/api/v1/error-replay/*` |
| `useErrorReview.ts` | 錯誤審查 | `/api/v1/error-review/*` |
| `useObserver.ts` | Observer | `/api/v1/observer/*` |
| `useRuleSim.ts` | 規則模擬 | `/api/v1/rule-sim/*` |
| `useSignalConflicts.ts` | 訊號衝突 | `/api/v1/predictions/conflicts` |
| `useSRankFactors.ts` | S-Rank 因子 | `/api/v1/s-rank/factors` |

**War Room Hooks（`src/hooks/war-room/`）：**
- `useConflicts.ts`
- `useDoctrineAlerts.ts`
- `useEquityCurve.ts`
- `useMicrostructure.ts`
- `useOrders.ts`
- `usePolicy.ts`
- `usePositionHealth.ts`
- `usePredictions.ts`
- `useRisk.ts`
- `useSentiment.ts`
- `useSystemLogs.ts`

### 5.3 未來建議

**統一狀態管理：**
- 考慮使用 **Zustand** 或 **Redux Toolkit** 統一狀態管理
- 將跨頁面共享狀態移到 Store
- 保持本地狀態用於組件內部狀態

---

## 6. API 客戶端與型別

### 6.1 API 客戶端（`src/api/client.ts`）

**主要方法：**

```typescript
// Predictions
getPredictions(date: string): Promise<Prediction[]>
getPrediction(symbol: string, date: string): Promise<Prediction>
getPredictionTimeline(symbol: string): Promise<PredictionTimelineResponse>
getLatestPrediction(symbol: string): Promise<LatestPrediction>

// Indicators
getIndicators(symbol: string, date: string): Promise<IndicatorSnapshot>

// Universe
getCoverage(universe: string, fromDate: string, toDate: string): Promise<CoverageResponse>
getCoverageDetail(...): Promise<CoverageDetailResponse>
```

### 6.2 Universe API（`src/api/universeApi.ts`）

```typescript
fetchUniverseStocks(): Promise<Stock[]>
```

### 6.3 型別定義（`src/types/`）

**主要型別：**
- `Prediction` - 預測結果
- `Indicator` / `IndicatorSnapshot` - 指標資料
- `CoverageItem` / `CoverageSummary` / `CoverageResponse` - 覆蓋率
- `PredictionTimelinePoint` / `PredictionTimelineResponse` - 時間序列
- `LatestPrediction` - 最新預測（包含 factors 和 risk flags）
- `TopLongItem` / `TopShortItem` - Top N 預測項目
- `WarRoomV2Data` - War Room V2 資料結構

**模組化型別：**
- `decisionAb.ts` - Decision AB Test 型別
- `doctrineAlert.ts` - Doctrine Alert 型別
- `doctrinePatch.ts` - Doctrine Patch 型別
- `doctrineV2.ts` - Doctrine V2 型別
- `errorReview.ts` - Error Review 型別
- `observer.ts` - Observer 型別
- `ruleSim.ts` - Rule Simulation 型別
- `signalConflict.ts` - Signal Conflict 型別
- `sRank.ts` - S-Rank 型別
- `warRoom.ts` - War Room 型別
- `warRoomV2.ts` - War Room V2 型別

---

## 7. War Room V2 設計理解

### 7.1 設計理念

**War Room V2** 是統一的控制中心，整合四大核心：

1. **Decision Layer V2**：Top N Predictions（使用 Final Score V2）
2. **Knowledge Observer**：治理監控（Doctrine 違規、異常偵測）
3. **Doctrine Patch Queue**：Patch 審核與部署流程
4. **Decision AB Test Dashboard**：Decision Layer 的 A/B 測試結果

### 7.2 UI 佈局

```
┌─────────────────────────────────────────────────────┐
│  ExecutiveSummary (系統狀態、關鍵指標)              │
├──────────────────────────┬──────────────────────────┤
│                          │  SRankTrendCard          │
│  TopPredictionsPanel     │  (S-Rank 趨勢)           │
│  (Top Long/Short 列表)    │                          │
│                          │  PatchQueueCard          │
│  - 點擊項目顯示           │  (Patch 佇列)            │
│    DecisionContextDrawer │                          │
│                          │  AbTestSummaryCard       │
│                          │  (A/B 測試摘要)          │
└──────────────────────────┴──────────────────────────┘
```

### 7.3 Decision Context Drawer

**觸發：** 點擊 TopPredictionsPanel 中的預測項目

**顯示內容：**
- Symbol & Name
- Final Score / Raw Score
- S-Rank Level & Weighted Score
- Strategy Scores
- Conflict Summary
- Doctrine Alerts

---

## 8. 未來擴充建議

### 8.1 K 線圖

**建議：** 使用 TradingView Charting Library 或自訂實作

**用途：**
- 顯示股票價格走勢
- 技術指標疊加
- 交易訊號標記

### 8.2 訂單票據（Order Ticket）

**功能：**
- 模擬下單介面（目前為模擬模式）
- 訂單確認與取消
- 訂單歷史查詢

**注意：** 目前系統僅支援模擬模式，此功能需在實盤模式準備時實作

### 8.3 實盤接入後 UI 變化

**預期變化：**
- 加入實盤/模擬模式切換
- 實盤訂單管理介面
- 風險控制面板（實盤專用）
- 交易日誌與審計介面

### 8.4 即時更新（WebSocket）

**建議：** 整合 WebSocket 實現即時更新

**應用場景：**
- War Room V2 即時分析結果
- Observer 即時監控數據
- 系統日誌流

---

## 9. 相關文件

- [系統藍圖](./JGOD_System_Blueprint_v1.md) - 系統總覽
- [API 映射](./JGOD_API_Map_v1.md) - 完整的 API 端點列表
- [後端模組地圖](./JGOD_Backend_Module_Map_v1.md) - 後端模組說明

---

**文件結束**

