# J-GOD 系統架構

## 概述

J-GOD（股神作戰系統）是一個模組化、可部署的股票交易決策系統，整合了市場資料、策略引擎、風險管理、執行引擎和 AI 戰情室。

## 系統架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                      J-GOD 系統                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Market Data  │  │  Strategy    │  │    Risk      │      │
│  │   Engine     │→ │   Engine     │→ │   Engine     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                │                   │              │
│         └────────────────┼───────────────────┘              │
│                          │                                  │
│                  ┌───────▼───────┐                          │
│                  │  Execution    │                          │
│                  │    Engine     │                          │
│                  └───────┬───────┘                          │
│                          │                                  │
│         ┌────────────────┼─────────────────┐              │
│         │                 │                 │              │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐        │
│  │ War Room    │  │ Code Intel  │  │    CLI      │        │
│  │   Engine    │  │   Engine    │  │  System     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 核心模組

### 1. Market Data Engine (`jgod/market/`)

負責市場資料的取得、快取和技術指標計算。

- **data_loader.py**: 整合 FinMind 和 yfinance，載入台股/美股資料
- **price_cache.py**: 價格快取機制，減少 API 呼叫
- **indicators.py**: 技術指標計算（MA、RSI、MACD）
- **market_status.py**: 市場開盤狀態判斷

### 2. Strategy Engine (`jgod/strategy/`)

提供交易策略框架和實作。

- **base_strategy.py**: 策略基類，所有策略繼承此類
- **breakout_strategy.py**: 突破策略實作
- **ai_signal_bridge.py**: AI 訊號橋接器，將 AI 建議轉換為交易訊號

### 3. Risk Engine (`jgod/risk/`)

風險管理和投資組合管理。

- **risk_manager.py**: 風險管理器，控制最大虧損、最大持倉
- **portfolio.py**: 投資組合管理器，追蹤多標的持倉
- **sizing.py**: 部位大小計算器，根據風險計算適當持倉

### 4. Execution Engine (`jgod/execution/`)

模擬交易執行。

- **virtual_broker.py**: 虛擬券商，模擬交易執行
- **trade_recorder.py**: 交易記錄器，記錄到 CSV 和 SQLite
- **slippage.py**: 滑價模型，模擬實際交易滑價

### 5. War Room Engine (`jgod/war_room/`)

AI 戰情室，整合多個 AI 提供者。

- **war_room_app.py**: Streamlit Web UI
- **ai_council.py**: AI 議會，多 AI 討論機制
- **decision_engine.py**: 決策引擎，彙整 AI 意見產生共識

### 6. Code Intelligence Engine (`jgod/code_intel/`)

程式碼理解和分析工具。

- **scanner.py**: 專案掃描器
- **todo_extractor.py**: TODO 提取器
- **insight_engine.py**: 洞察引擎，分析系統弱點

## 資料流

1. **資料取得**: Market Data Engine 從 FinMind/yfinance 取得資料
2. **策略分析**: Strategy Engine 分析資料並產生訊號
3. **風險評估**: Risk Engine 評估風險並計算部位大小
4. **執行交易**: Execution Engine 模擬執行交易
5. **AI 諮詢**: War Room Engine 提供 AI 建議
6. **決策整合**: Decision Engine 整合所有意見產生最終決策

## 技術棧

- **Python 3.11+**
- **Streamlit**: Web UI 框架
- **FinMind**: 台股資料來源
- **yfinance**: 美股資料來源
- **SQLite**: 本地資料庫
- **多 AI 提供者**: OpenAI, Claude, Gemini, Perplexity

