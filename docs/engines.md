# 引擎說明

## Market Data Engine

### 功能

- 整合 FinMind 和 yfinance 取得台股/美股資料
- 價格快取機制，減少 API 呼叫
- 技術指標計算（MA、RSI、MACD）
- 市場開盤狀態判斷

### 使用範例

```python
from jgod.market import DataLoader, TechnicalIndicators, MarketStatus

# 載入資料
loader = DataLoader()
data = loader.load_taiwan_stock("2330", "2025-01-01", "2025-01-31")

# 計算指標
indicators = TechnicalIndicators()
data_with_indicators = indicators.add_all_indicators(data)

# 檢查市場狀態
market_status = MarketStatus()
status = market_status.get_market_status()
```

## Strategy Engine

### 功能

- 策略基類框架
- 突破策略實作
- AI 訊號橋接

### 使用範例

```python
from jgod.strategy import BreakoutStrategy, AISignalBridge

# 突破策略
strategy = BreakoutStrategy(ma_period=20)
signal = strategy.generate_signal("2330", data)

# AI 訊號橋接
ai_bridge = AISignalBridge(provider="gpt")
signal = ai_bridge.generate_signal("2330", data, question="這檔股票值得買嗎？")
```

## Risk Engine

### 功能

- 風險限制管理
- 投資組合追蹤
- 部位大小計算

### 使用範例

```python
from jgod.risk import RiskManager, Portfolio, PositionSizer

# 風險管理
risk_manager = RiskManager(initial_capital=1000000.0)
can_open, reason = risk_manager.can_open_position("2330", 100.0, 1000)

# 投資組合
portfolio = Portfolio(initial_cash=1000000.0)
portfolio.add_position("2330", 1000, 100.0)
summary = portfolio.get_summary()

# 部位大小
sizer = PositionSizer()
quantity = sizer.calculate_position_size(100.0, stop_loss_price=95.0)
```

## Execution Engine

### 功能

- 虛擬券商模擬
- 交易記錄
- 滑價模擬

### 使用範例

```python
from jgod.execution import VirtualBroker

broker = VirtualBroker(initial_cash=1000000.0)
fill = broker.buy("2330", 1000, price=100.0)
summary = broker.get_account_summary()
```

## War Room Engine

### 功能

- 多 AI 提供者整合
- AI 議會討論機制
- 決策引擎產生共識

### 使用範例

```python
from jgod.war_room import DecisionEngine

engine = DecisionEngine()
consensus = engine.make_decision(
    question="2330 值得買嗎？",
    stock_id="2330",
    selected_providers=["gpt", "claude"],
)
```

## Code Intelligence Engine

### 功能

- 專案掃描
- TODO 提取
- 系統洞察

### 使用範例

```python
from jgod.code_intel import scan_project, TodoExtractor, InsightEngine

# 掃描專案
files = scan_project()

# 提取 TODO
extractor = TodoExtractor()
todos = extractor.extract_from_directory(Path("."))

# 系統洞察
engine = InsightEngine()
report = engine.generate_insight_report()
```

