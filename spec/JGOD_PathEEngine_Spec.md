# J-GOD Path E Engine Specification

## 📋 概述

Path E Engine 是 J-GOD 系統中的**即時交易引擎（Live Trading Engine）**，負責在「現在」執行策略決策並管理實際的投資組合。Path E 是 Path A/B/C/D 的「生產環境」版本，將回測驗證過的策略轉換為實際交易指令。

---

## 🎯 核心角色與目的

### A. Path E Engine 的存在目的

1. **即時交易執行**
   - 從即時資料流（Live Data Feed）接收市場資料
   - 根據策略生成交易決策
   - 執行交易指令並更新投資組合狀態

2. **支援安全測試模式**
   - **DRY_RUN**: 只跑決策與 log，不建任何部位，用於測試決策邏輯
   - **PAPER**: 用模擬券商帳戶更新 PortfolioState，不碰真實 API，用於完整流程測試

3. **風險控制**
   - 即時監控投資組合風險
   - 透過 RiskGuard 過濾不符合風險要求的交易指令
   - 確保單檔部位、單筆下單金額等符合限制

4. **整合 Path D Policy**
   - 未來會整合 Path D RL 訓練好的 policy，自動調整策略參數
   - 目前 v1 使用簡單 placeholder 策略

---

## 🔌 Interface / API 規格

### 1. PathEConfig

```python
@dataclass
class PathEConfig:
    """Path E Engine 配置"""
    
    # 模式設定
    mode: Literal["DRY_RUN", "PAPER", "LIVE"]  # v1 只支援 DRY_RUN, PAPER
    
    # 交易標的
    symbols: List[str]  # 例如 ["2330", "2317", "2454"]
    
    # 初始資金
    initial_cash: float = 1000000.0
    
    # 風險限制
    max_position_pct: float = 0.2  # 單檔最大部位不超過淨值 X%
    max_order_pct: float = 0.05    # 單筆下單金額不超過淨值 Y%
    
    # 資料來源設定
    data_feed_type: Literal["mock", "live"] = "mock"  # v1 只支援 mock
    bar_interval: str = "1d"  # 資料頻率（"1d", "1h", "5m" 等）
    
    # 策略設定（v1 為 placeholder）
    signal_engine_type: str = "placeholder"
    
    # 執行設定
    execution_mode: Literal["sim", "real"] = "sim"  # v1 只支援 sim
    
    # 日誌設定
    log_dir: str = "logs/path_e"
```

### 2. LiveBar

```python
@dataclass
class LiveBar:
    """即時 K 線資料"""
    symbol: str
    ts: pd.Timestamp  # 時間戳記
    open: float
    high: float
    low: float
    close: float
    volume: float
```

### 3. LiveDecision

```python
@dataclass
class LiveDecision:
    """交易決策"""
    target_weights: Dict[str, float]  # 目標權重 {symbol: weight}
    meta: Dict[str, Any] = field(default_factory=dict)  # 額外資訊
```

### 4. PlannedOrder

```python
@dataclass
class PlannedOrder:
    """計劃中的訂單"""
    symbol: str
    side: Literal["buy", "sell"]
    qty: int  # 股數
    price_type: Literal["market", "limit"] = "market"
    ts: pd.Timestamp
    limit_price: Optional[float] = None
```

### 5. PortfolioState

```python
@dataclass
class PortfolioState:
    """投資組合狀態"""
    cash: float
    positions: Dict[str, int]  # {symbol: quantity}
    equity: float  # 總淨值
    pnl: float  # 損益
    max_drawdown: float
    timestamp: pd.Timestamp
    
    def revalue(self, market_prices: Dict[str, float]) -> None:
        """根據市場價格重新計算淨值"""
        ...
    
    def update_from_fill(self, order: PlannedOrder, fill_price: float) -> None:
        """根據成交記錄更新狀態"""
        ...
```

---

## 🏗️ 主要模組設計

### 1. LiveDataFeed（即時資料流）

**職責**: 提供即時市場資料（K 線、價格等）。

**v1 實作**: `MockLiveFeed` - 從歷史資料做 replay

**關鍵方法**:
- `get_next_bar(symbol: str) -> Optional[LiveBar]`: 取得下一個 bar
- `has_next(symbol: str) -> bool`: 是否還有資料
- `reset()`: 重置到起始位置

**與 Path A 的關係**: 
- v1 從 Path A 的歷史資料（DataFrame 或 CSV）做 replay
- 未來可以接真實的即時資料來源（例如 WebSocket API）

---

### 2. PortfolioState（投資組合狀態）

**職責**: 追蹤投資組合的當前狀態（現金、持倉、淨值、損益等）。

**關鍵方法**:
- `revalue(market_prices: Dict[str, float]) -> None`: 根據最新市場價格重新計算淨值
- `update_from_fill(order: PlannedOrder, fill_price: float) -> None`: 根據成交記錄更新現金與持倉
- `get_position_value(symbol: str, price: float) -> float`: 取得某標的的持倉價值
- `get_total_value(market_prices: Dict[str, float]) -> float`: 取得總淨值

**資料結構**:
- `cash`: 現金餘額
- `positions`: 持倉字典 {symbol: quantity}
- `equity`: 當前淨值
- `pnl`: 損益
- `max_drawdown`: 最大回撤

---

### 3. LiveSignalEngine（即時訊號引擎）

**職責**: 根據當前市場狀況與投資組合狀態，生成交易決策（目標權重）。

**v1 實作**: 簡單 placeholder 策略

**關鍵方法**:
- `generate_decision(portfolio_state: PortfolioState, latest_bars: Dict[str, LiveBar]) -> LiveDecision`: 生成交易決策

**v1 Placeholder 策略範例**:
- **現金策略**: 全部持有現金（`target_weights = {}`）
- **簡單均線策略**: 若當前 close > N 日均線，則持有小部位（例如 10%）

**與 Path D 的關係**:
- **未來擴充**: Path D 訓練好的 policy 會整合到 LiveSignalEngine
- Policy 會根據當前狀態（類似 Path D 的 State）生成決策（類似 Path D 的 Action）

---

### 4. RiskGuard（風險守衛）

**職責**: 過濾不符合風險要求的交易指令。

**關鍵方法**:
- `filter_orders(portfolio_state: PortfolioState, proposed_orders: List[PlannedOrder], latest_prices: Dict[str, float]) -> List[PlannedOrder]`: 過濾訂單

**v1 基本規則**:
1. **單檔最大部位限制**: `position_value <= equity * max_position_pct`
2. **單筆下單金額限制**: `order_value <= equity * max_order_pct`

**未來擴充**:
- 總曝險限制
- 集中度限制
- 流動性檢查
- 波動率限制

---

### 5. OrderPlanner（訂單規劃器）

**職責**: 根據目標權重與當前持倉，計算需要執行的訂單（買/賣多少股）。

**關鍵方法**:
- `plan_orders(portfolio_state: PortfolioState, target_weights: Dict[str, float], latest_prices: Dict[str, float]) -> List[PlannedOrder]`: 規劃訂單

**邏輯**:
1. 計算目標持倉價值 = `equity * target_weight`
2. 計算目標股數 = `target_value / price`
3. 計算需要調整的股數 = `target_qty - current_qty`
4. 產生 PlannedOrder（buy 或 sell）

---

### 6. BrokerClient（券商客戶端）

**職責**: 執行交易指令（提交訂單、查詢成交狀態等）。

**v1 實作**: `SimBrokerClient` - 模擬券商，只更新 PortfolioState，不呼叫任何外部 API

**介面** (Protocol 或 ABC):
```python
class BrokerClient(Protocol):
    def submit_order(self, order: PlannedOrder) -> Optional[Fill]:
        """提交訂單"""
        ...
    
    def get_order_status(self, order_id: str) -> OrderStatus:
        """查詢訂單狀態"""
        ...
```

**v1 SimBrokerClient**:
- 立即假設訂單以當前市價成交
- 計算滑價與手續費
- 更新 PortfolioState

**未來擴充**:
- 真實券商 API 整合
- 訂單狀態追蹤
- 部分成交處理

---

### 7. LiveTradingEngine（即時交易引擎）

**職責**: 協調所有模組，執行完整的即時交易循環。

**關鍵方法**:
- `run_loop() -> None`: 執行主要交易循環

**run_loop() 流程**:
1. **資料接收**: 從 LiveDataFeed 取得最新 bar（或一批 bars）
2. **淨值更新**: 用最新價格更新 PortfolioState 的市值
3. **決策生成**: 呼叫 LiveSignalEngine.generate_decision()
4. **訂單規劃**: 用 OrderPlanner 根據目標權重產生訂單
5. **風險過濾**: 用 RiskGuard 過濾不符合風險要求的訂單
6. **訂單執行**: 
   - DRY_RUN 模式: 只記錄決策與訂單，不執行
   - PAPER 模式: 用 SimBrokerClient 執行訂單
7. **狀態更新**: 更新 PortfolioState
8. **日誌記錄**: 記錄決策、訂單、成交等資訊（logging 或 CSV）

---

## 🔗 與 Path A/B/C/D 的關係

### Path E 與 Path A 的關係

**v1 階段**:
- Path E 從 Path A 的歷史資料做 replay（使用 MockLiveFeed）
- Path A 提供歷史資料格式（DataFrame 或 CSV）

**未來擴充**:
- Path E 可以使用 Path A 的資料載入器（FinMind Loader）取得即時資料

---

### Path E 與 Path B/C 的關係

**目前**: 
- Path E v1 尚未直接整合 Path B/C
- Path B/C 的驗證結果可以作為 Path E 策略選擇的參考

**未來擴充**:
- Path E 可以讀取 Path C 的最佳 Scenario 結果，自動選擇策略配置

---

### Path E 與 Path D 的關係

**v1 階段**:
- Path E v1 尚未接 Path D policy
- 使用簡單 placeholder 策略

**未來擴充（Path E v2）**:
- Path D 訓練好的 policy 會整合到 LiveSignalEngine
- Policy 會根據當前 PortfolioState 與市場狀態生成決策
- 類似 Path D 的 State → Action 映射，但應用於即時交易

**整合架構（未來）**:
```
Path D Policy (訓練好的 RL Agent)
    ↓
LiveSignalEngine (整合 Path D Policy)
    ↓
生成 LiveDecision (目標權重)
    ↓
OrderPlanner → RiskGuard → BrokerClient
```

---

## 📊 執行模式說明

### DRY_RUN 模式

**特點**:
- 只跑決策與 log，不建任何部位
- 不會更新 PortfolioState 的現金或持倉
- 用於測試決策邏輯是否正常運作

**輸出**:
- 決策日誌（每次決策的目標權重）
- 訂單日誌（計劃的訂單）
- 但不會有實際成交記錄

---

### PAPER 模式

**特點**:
- 用 SimBrokerClient 模擬執行訂單
- 更新 PortfolioState（現金、持倉、淨值等）
- 完整模擬交易流程，但不接觸真實 API

**輸出**:
- 完整的決策日誌
- 訂單日誌
- 成交記錄
- PortfolioState 的完整演進歷史

**用途**:
- 在真實市場資料上測試完整交易流程
- 驗證風險控制機制
- 觀察策略在即時環境下的表現

---

### LIVE 模式（未來擴充）

**特點**:
- 連接真實券商 API
- 執行真實交易
- 需要額外的安全機制（例如人工確認、每日交易限額等）

**v1 不支援**，需在 v2+ 才實作。

---

## 🔧 實作細節

### 資料格式

**LiveBar**: 
- 與 Path A 的 `PathADailyInput` 類似，但簡化為單一標的的單一 bar

**PortfolioState**:
- 追蹤當前時點的完整投資組合狀態
- 每次收到新 bar 時需要 `revalue()` 更新淨值

### 決策頻率

**v1 預設**: 每個 bar 都生成一次決策（例如每日）

**未來擴充**: 可以設定決策頻率（例如每 N 個 bar 或特定時間）

### 日誌格式

**決策日誌**:
```csv
timestamp,symbol,target_weight,decision_type
2024-01-01 09:00:00,2330,0.2,PLACEHOLDER_STRATEGY
```

**訂單日誌**:
```csv
timestamp,symbol,side,qty,price_type,status
2024-01-01 09:05:00,2330,buy,100,market,PLANNED
```

**成交記錄**:
```csv
timestamp,symbol,side,qty,fill_price,slippage,commission
2024-01-01 09:05:01,2330,buy,100,550.5,0.2,157.5
```

---

## 🎯 v1 限制與未來擴充

### v1 限制

1. **未整合 Path D Policy**: 使用簡單 placeholder 策略
2. **未連接真實 API**: 只支援 MockLiveFeed 和 SimBrokerClient
3. **未整合 Path B/C 結果**: 策略選擇需手動配置
4. **簡化的風險控制**: 只有基本的部位與下單金額限制

### 未來擴充（Path E v2+）

1. **整合 Path D Policy**
   - LiveSignalEngine 整合 Path D 訓練好的 policy
   - 根據當前狀態生成動態決策

2. **真實資料來源**
   - 連接即時市場資料 API（WebSocket）
   - 支援多種資料頻率（tick, 1m, 5m, 1h, 1d）

3. **真實券商整合**
   - 支援真實券商 API（例如富邦、元大等）
   - 訂單狀態追蹤與部分成交處理

4. **進階風險控制**
   - 總曝險限制
   - 集中度限制
   - 流動性檢查
   - 波動率限制

5. **整合 Path B/C 結果**
   - 自動讀取 Path C 的最佳 Scenario
   - 根據驗證結果選擇策略配置

---

## 📝 檔案結構

```
jgod/path_e/
├── __init__.py
├── live_types.py              # 資料結構定義
├── live_data_feed.py          # LiveDataFeed, MockLiveFeed
├── portfolio_state.py         # PortfolioState
├── live_signal_engine.py      # LiveSignalEngine (placeholder)
├── risk_guard.py              # RiskGuard
├── order_planner.py           # OrderPlanner
├── broker_client.py           # BrokerClient Protocol, SimBrokerClient
└── live_trading_engine.py     # LiveTradingEngine
```

---

## 📚 參考文件

- `spec/JGOD_PathAEngine_Spec.md`: Path A 資料格式參考
- `spec/JGOD_PathDEngine_Spec.md`: Path D Policy 整合參考（未來）
- `docs/JGOD_System_Map_v1.md`: 系統架構總覽
- `docs/JGOD_GOVERNANCE_STANDARD_v1.md`: 風險控制標準（未來擴充參考）

---

**最後更新**: 2025-12-04

