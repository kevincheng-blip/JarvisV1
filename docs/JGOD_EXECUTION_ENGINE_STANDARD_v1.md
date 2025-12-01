# J-GOD Execution Engine Standard v1

### Step 6 — 交易執行引擎標準規格

---

# 1. Overview

J-GOD Execution Engine 是系統中負責將優化器產生的目標權重轉換為實際交易執行的核心模組。

## 1.1 Execution Engine 核心定義

**Execution Engine 的目標與角色：**

將 Optimizer 產生的目標投資組合權重（Target Weights）轉換為實際可執行的交易訂單（Orders），並模擬市場執行過程，產生成交記錄（Fills），最終更新投資組合狀態（PortfolioState）。

**核心流程：**

```
PortfolioState → Target Weights → Orders → Fills → Updated Portfolio
```

## 1.2 與其他模組的資料流

### 與 Optimizer 的整合

- **輸入**：Optimizer 產生的目標權重向量 `w*`
- **處理**：計算當前持倉與目標權重的差異，產生交易訂單

### 與 RiskModel 的整合

- **驗證**：執行前驗證交易是否符合風險限制
- **追蹤**：更新因子暴露和組合風險

### 與 Backtest / Path A 的整合

- **回測執行**：在歷史回測中模擬交易執行
- **績效計算**：根據執行結果計算實際報酬和成本

---

# 2. 交易物件模型（Trade Object Model）

## 2.1 Order（訂單）

**定義**：表示一個交易請求，包含買賣方向、標的、數量、價格等資訊。

**屬性**：
- `order_id`: 唯一訂單 ID
- `symbol`: 標的代碼
- `side`: 交易方向（"BUY" 或 "SELL"）
- `quantity`: 交易數量（股數）
- `order_type`: 訂單類型（"MARKET", "LIMIT" 等）
- `limit_price`: 限價（如果是限價單）
- `timestamp`: 訂單時間戳

## 2.2 Fill（成交）

**定義**：表示訂單的執行結果，包含實際成交價格、數量、成本等。

**屬性**：
- `fill_id`: 唯一成交 ID
- `order_id`: 對應的訂單 ID
- `symbol`: 標的代碼
- `side`: 交易方向
- `filled_quantity`: 實際成交數量
- `fill_price`: 實際成交價格（已含滑價）
- `slippage`: 滑價金額
- `commission`: 手續費
- `tax`: 稅費
- `timestamp`: 成交時間戳

## 2.3 Trade（交易）

**定義**：完整的交易記錄，包含訂單和成交資訊。

**屬性**：
- `trade_id`: 唯一交易 ID
- `order`: Order 物件
- `fill`: Fill 物件
- `total_cost`: 總成本（手續費 + 稅費）
- `net_amount`: 淨交易金額

## 2.4 Position（部位）

**定義**：表示單一標的的持倉狀態。

**屬性**：
- `symbol`: 標的代碼
- `quantity`: 持有數量（正數為多頭，負數為空頭）
- `avg_price`: 平均成本價格
- `current_price`: 當前市場價格
- `market_value`: 市值
- `unrealized_pnl`: 未實現損益

## 2.5 PortfolioState（投資組合狀態）

**定義**：表示整個投資組合的完整狀態。

**屬性**：
- `positions`: Dict[symbol, Position] - 所有持倉
- `cash`: 現金餘額
- `total_value`: 總資產價值
- `timestamp`: 狀態時間戳
- `turnover`: 換手率
- `transaction_costs`: 總交易成本

---

# 3. Rebalance Engine（核心流程）

## 3.1 核心流程

**步驟 1：計算目標權重差異**

```python
target_weights: Dict[symbol, weight]
current_portfolio_state: PortfolioState

for symbol in target_weights:
    target_value = target_weights[symbol] * total_portfolio_value
    current_value = current_portfolio_state.positions[symbol].market_value
    diff_value = target_value - current_value
    required_trades[symbol] = diff_value
```

**步驟 2：生成交易訂單**

```python
for symbol, trade_value in required_trades.items():
    if trade_value > threshold:
        # 買入
        quantity = trade_value / current_price
        order = Order(symbol=symbol, side="BUY", quantity=quantity)
    elif trade_value < -threshold:
        # 賣出
        quantity = abs(trade_value) / current_price
        order = Order(symbol=symbol, side="SELL", quantity=quantity)
```

**步驟 3：訂單排序與批次處理**

- 按照優先級排序（例如：流動性、Alpha 強度）
- 批次執行以減少市場衝擊

---

# 4. Execution Model（滑價模型）

## 4.1 Fixed Slippage Model（固定滑價）

**定義**：固定金額的滑價，不考慮市場條件。

**公式**：
```
fill_price = order_price + fixed_slippage * direction
```

其中：
- `direction = +1`（買入）或 `-1`（賣出）

**參數**：
- `fixed_slippage`: 固定滑價金額（例如：0.1 元）

## 4.2 Percentage Slippage Model（百分比滑價）

**定義**：按訂單價格的百分比計算滑價。

**公式**：
```
fill_price = order_price * (1 + slippage_pct * direction)
```

**參數**：
- `slippage_pct`: 滑價百分比（例如：0.001 表示 0.1%）

## 4.3 Volume-Based Slippage Model（成交量基礎滑價）

**定義**：根據交易量與市場成交量的比例計算滑價。

**公式**：
```
volume_ratio = order_quantity / daily_volume
slippage = base_slippage * (1 + impact_factor * volume_ratio^2)
fill_price = order_price * (1 + slippage * direction)
```

**參數**：
- `base_slippage`: 基礎滑價百分比
- `impact_factor`: 市場衝擊係數
- `daily_volume`: 日成交量

---

# 5. Cost Model（交易成本模型）

## 5.1 Commission（手續費）

**台股手續費計算**：

```
commission = max(
    trade_amount * commission_rate,
    min_commission
)
```

**參數**：
- `commission_rate`: 手續費率（例如：0.001425，即 0.1425%）
- `min_commission`: 最低手續費（例如：20 元）

## 5.2 Tax（稅費）

**證交稅（賣出時）**：

```
tax = sell_amount * tax_rate  # 僅賣出時收取
```

**參數**：
- `tax_rate`: 證交稅率（例如：0.003，即 0.3%）

**期貨交易稅**（如果是期貨）：

```
tax = contract_value * futures_tax_rate
```

## 5.3 最低費用邏輯

**實務處理**：

- 手續費有最低收費（例如：20 元）
- 小額交易可能導致成本率過高
- 需要設定最小交易金額門檻

---

# 6. Execution Pipeline（7 Steps）

## Step 1: 接收目標權重

```python
target_weights: Dict[symbol, weight]  # 來自 Optimizer
current_portfolio: PortfolioState      # 當前組合狀態
```

## Step 2: 計算換手量

```python
turnover = compute_turnover(target_weights, current_portfolio)
```

計算換手率：
```
turnover = 0.5 * sum(|target_weight[i] - current_weight[i]|)
```

## Step 3: 生成 Orders

```python
orders = generate_orders(target_weights, current_portfolio, prices)
```

- 計算每個標的需要的交易金額
- 轉換為交易數量（考慮最小交易單位）
- 生成 Order 物件列表

## Step 4: 套用 ExecutionModel

```python
for order in orders:
    fill_price = execution_model.apply_slippage(order, market_data)
```

根據選擇的滑價模型計算實際成交價格。

## Step 5: 套用 CostModel

```python
for order, fill_price in zip(orders, fill_prices):
    commission = cost_model.compute_commission(order, fill_price)
    tax = cost_model.compute_tax(order, fill_price)
    total_cost = commission + tax
```

## Step 6: 生成 Fills / Trades

```python
fills = []
for order, fill_price, total_cost in zip(orders, fill_prices, costs):
    fill = Fill(
        order_id=order.order_id,
        fill_price=fill_price,
        filled_quantity=order.quantity,
        commission=commission,
        tax=tax,
        timestamp=timestamp
    )
    fills.append(fill)
```

## Step 7: 更新 PortfolioState

```python
new_portfolio = update_portfolio(
    current_portfolio,
    fills,
    current_prices
)
```

- 更新每個標的的持倉數量
- 更新現金餘額
- 計算新的組合市值
- 更新未實現損益

---

# 7. Required Inputs & Outputs

## 7.1 Required Inputs

### ExecutionRequest

```python
@dataclass
class ExecutionRequest:
    target_weights: Dict[str, float]      # 目標權重
    prev_portfolio_state: PortfolioState  # 前一期組合狀態
    prices: Dict[str, float]              # 當前價格
    volumes: Dict[str, float]             # 日成交量（可選）
    cost_params: Dict[str, any]           # 成本參數
    slippage_params: Dict[str, any]       # 滑價參數
```

### 必要參數說明

- `target_weights`: Optimizer 產生的目標權重字典
- `prev_portfolio_state`: 執行前的組合狀態
- `prices`: 標的當前市場價格
- `volumes`: 日成交量（用於 Volume-Based Slippage）
- `cost_params`: 包含手續費率、稅率、最低費用等
- `slippage_params`: 包含滑價模型類型和參數

## 7.2 Outputs

### ExecutionResult

```python
@dataclass
class ExecutionResult:
    trades: List[Trade]                    # 所有交易記錄
    fills: List[Fill]                      # 所有成交記錄
    new_portfolio_state: PortfolioState    # 更新後的組合狀態
    turnover: float                        # 換手率
    transaction_costs: float               # 總交易成本
    diagnostics: Dict[str, any]            # 診斷資訊
```

### 輸出項目說明

- `trades`: 完整的交易記錄列表
- `fills`: 所有成交記錄
- `new_portfolio_state`: 執行後的組合狀態
- `turnover`: 本次執行的換手率
- `transaction_costs`: 總交易成本（手續費 + 稅費）
- `diagnostics`: 診斷資訊（例如：部分成交、滑價統計等）

---

# 8. Integration with Path A

## 8.1 Path A 整合點

Execution Engine 在 Path A 回測流程中的角色：

```
Path A Backtest Loop:
  1. Alpha Engine → expected returns
  2. Risk Model → covariance matrix
  3. Optimizer → target weights w*
  4. Execution Engine → executes trades
  5. Update portfolio → calculate returns
```

## 8.2 使用範例

```python
from jgod.execution import ExecutionEngine
from jgod.execution.execution_models import FixedSlippageModel
from jgod.execution.cost_model import DefaultCostModel

# 初始化
execution_engine = ExecutionEngine(
    execution_model=FixedSlippageModel(slippage=0.1),
    cost_model=DefaultCostModel()
)

# 執行再平衡
result = execution_engine.rebalance_to_weights(
    target_weights=optimizer_result.weights,
    prev_portfolio=current_portfolio,
    prices=current_prices,
    volumes=daily_volumes
)

# 更新組合狀態
new_portfolio = result.new_portfolio_state
```

---

# 9. Implementation Notes

## 9.1 設計原則

- **模組化設計**：ExecutionModel、CostModel、BrokerAdapter 可獨立替換
- **協議導向**：使用 Protocol 定義介面，支援多種實作
- **可測試性**：所有組件都可以獨立測試

## 9.2 錯誤處理

- **部分成交**：處理訂單無法完全成交的情況
- **流動性不足**：當交易量超過市場流動性時的處理
- **價格異常**：檢測價格跳動過大的情況

## 9.3 效能考量

- **向量化計算**：使用 NumPy 進行批量計算
- **批次處理**：將多個訂單批次處理以提升效率

---

# 10. Future Enhancements

## v2 預定功能

- **訂單拆分**：大單拆分為多個小單執行
- **時間加權平均價格（TWAP）**：分散執行降低市場衝擊
- **成交量加權平均價格（VWAP）**：按照市場成交量分佈執行
- **實時市場數據整合**：連接真實市場數據源
- **訂單簿模擬**：模擬訂單簿深度和流動性

---

**版本**：v1.0  
**最後更新**：2025-12-02  
**狀態**：✅ 標準規範已確立

