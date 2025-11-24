# 資料流說明

## 資料流向圖

```
外部資料源
    │
    ├─ FinMind (台股)
    └─ yfinance (美股)
    │
    ▼
┌─────────────────┐
│  Data Loader    │
│  (資料載入器)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Price Cache    │
│  (價格快取)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Indicators     │
│  (技術指標)     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│Strategy │ │ War Room │
│ Engine  │ │  Engine   │
└────┬────┘ └────┬─────┘
     │           │
     └─────┬─────┘
           │
           ▼
    ┌──────────────┐
    │ Risk Engine  │
    │ (風險評估)   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Execution    │
    │ Engine       │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Trade Record │
    │ (交易記錄)   │
    └──────────────┘
```

## 詳細流程

### 1. 資料取得階段

- **輸入**: 股票代號、日期範圍
- **處理**: DataLoader 從 FinMind/yfinance 取得原始資料
- **輸出**: 包含 OHLCV 的 DataFrame

### 2. 資料處理階段

- **快取**: PriceCache 檢查快取，減少 API 呼叫
- **指標計算**: TechnicalIndicators 計算 MA、RSI、MACD
- **輸出**: 包含技術指標的完整資料

### 3. 策略分析階段

- **輸入**: 處理後的資料
- **處理**: 
  - Strategy Engine 執行策略邏輯
  - War Room Engine 諮詢 AI 提供者
- **輸出**: 交易訊號（買入/賣出/持有）

### 4. 風險評估階段

- **輸入**: 交易訊號、當前持倉、帳戶狀態
- **處理**: 
  - RiskManager 檢查風險限制
  - PositionSizer 計算部位大小
- **輸出**: 核准的交易和建議部位

### 5. 執行階段

- **輸入**: 核准的交易
- **處理**: 
  - VirtualBroker 模擬執行
  - SlippageModel 應用滑價
- **輸出**: 成交記錄

### 6. 記錄階段

- **輸入**: 成交記錄
- **處理**: TradeRecorder 寫入 CSV 和 SQLite
- **輸出**: 交易歷史資料

## 資料格式

### 市場資料格式

```python
{
    "date": "2025-01-01",
    "open": 100.0,
    "high": 105.0,
    "low": 99.0,
    "close": 103.0,
    "volume": 1000000,
    "ma5": 102.0,
    "ma10": 101.0,
    "rsi": 55.0,
    "macd": 0.5,
}
```

### 交易訊號格式

```python
{
    "signal_type": "buy",  # "buy", "sell", "hold"
    "symbol": "2330",
    "timestamp": "2025-01-01T10:00:00",
    "price": 103.0,
    "confidence": 0.8,
    "reason": "價格突破 MA20",
}
```

### 交易記錄格式

```python
{
    "timestamp": "2025-01-01T10:00:00",
    "symbol": "2330",
    "side": "buy",
    "quantity": 100,
    "price": 103.0,
    "slippage": 0.1,
    "commission": 14.7,
}
```

