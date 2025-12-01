# JGOD Execution Engine Spec v1

## 1. ExecutionRequest Schema（輸入）

```python
@dataclass
class ExecutionRequest:
    target_weights: Dict[str, float]      # 目標權重 {symbol: weight}
    prev_portfolio_state: PortfolioState  # 前一期組合狀態
    prices: Dict[str, float]              # 當前價格 {symbol: price}
    volumes: Optional[Dict[str, float]] = None  # 日成交量 {symbol: volume}
    cost_params: Dict[str, any] = None    # 成本參數
    slippage_params: Dict[str, any] = None  # 滑價參數
```

### 參數說明

- `target_weights`: Optimizer 產生的目標權重字典
- `prev_portfolio_state`: 執行前的組合狀態
- `prices`: 標的當前市場價格
- `volumes`: 日成交量（用於 Volume-Based Slippage，可選）
- `cost_params`: 成本參數（手續費率、稅率等）
- `slippage_params`: 滑價參數（滑價模型類型、參數等）

---

## 2. ExecutionResult Schema（輸出）

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

### 輸出說明

- `trades`: 完整的交易記錄列表
- `fills`: 所有成交記錄
- `new_portfolio_state`: 執行後的組合狀態
- `turnover`: 本次執行的換手率
- `transaction_costs`: 總交易成本（手續費 + 稅費）
- `diagnostics`: 診斷資訊（部分成交、滑價統計等）

---

## 3. 介面要求

### 3.1 ExecutionModel Interface（滑價模型介面）

```python
class ExecutionModel(Protocol):
    """滑價模型介面"""
    
    def apply_slippage(
        self,
        order: Order,
        market_price: float,
        market_data: Optional[Dict[str, any]] = None
    ) -> float:
        """計算考慮滑價後的成交價格
        
        Args:
            order: 交易訂單
            market_price: 市場價格
            market_data: 市場數據（成交量等，可選）
        
        Returns:
            考慮滑價後的成交價格
        """
        ...
```

**實作類別**：
- `FixedSlippageModel`
- `PercentageSlippageModel`
- `VolumeImpactSlippageModel`

---

### 3.2 CostModel Interface（成本模型介面）

```python
class CostModel(Protocol):
    """交易成本模型介面"""
    
    def compute_commission(
        self,
        order: Order,
        fill_price: float
    ) -> float:
        """計算手續費
        
        Args:
            order: 交易訂單
            fill_price: 成交價格
        
        Returns:
            手續費金額
        """
        ...
    
    def compute_tax(
        self,
        order: Order,
        fill_price: float
    ) -> float:
        """計算稅費
        
        Args:
            order: 交易訂單
            fill_price: 成交價格
        
        Returns:
            稅費金額（賣出時才收取）
        """
        ...
    
    def compute_total_cost(
        self,
        order: Order,
        fill_price: float
    ) -> float:
        """計算總交易成本
        
        Args:
            order: 交易訂單
            fill_price: 成交價格
        
        Returns:
            總成本（手續費 + 稅費）
        """
        ...
```

**實作類別**：
- `DefaultCostModel`: 預設成本模型（台股手續費 + 證交稅）

---

### 3.3 BrokerAdapter Interface（券商介面）

```python
class BrokerAdapter(Protocol):
    """券商介面（用於連接真實或模擬券商）"""
    
    def submit_order(self, order: Order) -> str:
        """提交訂單
        
        Args:
            order: 交易訂單
        
        Returns:
            訂單 ID
        """
        ...
    
    def check_order_status(self, order_id: str) -> str:
        """檢查訂單狀態
        
        Args:
            order_id: 訂單 ID
        
        Returns:
            訂單狀態（"pending", "filled", "cancelled" 等）
        """
        ...
    
    def get_fill(self, order_id: str) -> Optional[Fill]:
        """取得成交記錄
        
        Args:
            order_id: 訂單 ID
        
        Returns:
            成交記錄（如果已成交）
        """
        ...
```

**實作類別**：
- `MockBrokerAdapter`: 模擬券商（預設 100% 成交）

---

### 3.4 RebalanceEngine Interface（再平衡引擎介面）

```python
class RebalanceEngine(Protocol):
    """再平衡引擎介面"""
    
    def compute_target_trades(
        self,
        target_weights: Dict[str, float],
        current_portfolio: PortfolioState,
        prices: Dict[str, float],
        total_value: float
    ) -> List[Order]:
        """計算目標權重與當前持倉的差異，產生交易訂單
        
        Args:
            target_weights: 目標權重字典
            current_portfolio: 當前組合狀態
            prices: 當前價格
            total_value: 總資產價值
        
        Returns:
            交易訂單列表
        """
        ...
```

---

## 4. ExecutionEngine 核心介面

```python
class ExecutionEngine:
    """Execution Engine 核心類別"""
    
    def __init__(
        self,
        execution_model: ExecutionModel,
        cost_model: CostModel,
        broker_adapter: Optional[BrokerAdapter] = None
    ):
        """初始化 Execution Engine
        
        Args:
            execution_model: 滑價模型
            cost_model: 成本模型
            broker_adapter: 券商介面（可選，預設使用 MockBrokerAdapter）
        """
        ...
    
    def rebalance_to_weights(
        self,
        target_weights: Dict[str, float],
        prev_portfolio: PortfolioState,
        prices: Dict[str, float],
        volumes: Optional[Dict[str, float]] = None
    ) -> ExecutionResult:
        """執行再平衡到目標權重
        
        Args:
            target_weights: 目標權重字典
            prev_portfolio: 前一期的組合狀態
            prices: 當前價格
            volumes: 日成交量（可選）
        
        Returns:
            ExecutionResult 物件
        """
        ...
    
    def execute_orders(
        self,
        orders: List[Order],
        prices: Dict[str, float],
        volumes: Optional[Dict[str, float]] = None
    ) -> ExecutionResult:
        """執行訂單列表
        
        Args:
            orders: 訂單列表
            prices: 當前價格
            volumes: 日成交量（可選）
        
        Returns:
            ExecutionResult 物件
        """
        ...
    
    def compute_turnover(
        self,
        target_weights: Dict[str, float],
        current_portfolio: PortfolioState
    ) -> float:
        """計算換手率
        
        Args:
            target_weights: 目標權重
            current_portfolio: 當前組合狀態
        
        Returns:
            換手率（0-1）
        """
        ...
```

---

## 5. 資料結構定義

### 5.1 Order

```python
@dataclass
class Order:
    order_id: str                          # 唯一訂單 ID
    symbol: str                            # 標的代碼
    side: str                              # "BUY" 或 "SELL"
    quantity: float                        # 交易數量（股數）
    order_type: str = "MARKET"            # "MARKET" 或 "LIMIT"
    limit_price: Optional[float] = None   # 限價（如果是限價單）
    timestamp: datetime                    # 訂單時間戳
```

### 5.2 Fill

```python
@dataclass
class Fill:
    fill_id: str                           # 唯一成交 ID
    order_id: str                          # 對應的訂單 ID
    symbol: str                            # 標的代碼
    side: str                              # 交易方向
    filled_quantity: float                 # 實際成交數量
    fill_price: float                      # 實際成交價格（已含滑價）
    slippage: float                        # 滑價金額
    commission: float                      # 手續費
    tax: float                             # 稅費
    timestamp: datetime                    # 成交時間戳
```

### 5.3 Trade

```python
@dataclass
class Trade:
    trade_id: str                          # 唯一交易 ID
    order: Order                           # 訂單物件
    fill: Fill                             # 成交物件
    total_cost: float                      # 總成本（手續費 + 稅費）
    net_amount: float                      # 淨交易金額
```

### 5.4 Position

```python
@dataclass
class Position:
    symbol: str                            # 標的代碼
    quantity: float                        # 持有數量（正數為多頭）
    avg_price: float                       # 平均成本價格
    current_price: float                   # 當前市場價格
    market_value: float                    # 市值
    unrealized_pnl: float                  # 未實現損益
```

### 5.5 PortfolioState

```python
@dataclass
class PortfolioState:
    positions: Dict[str, Position]         # 所有持倉
    cash: float                            # 現金餘額
    total_value: float                     # 總資產價值
    timestamp: datetime                    # 狀態時間戳
    turnover: float = 0.0                  # 換手率
    transaction_costs: float = 0.0         # 總交易成本
```

---

## 6. 預設參數

### 成本參數（台股）

```python
DEFAULT_COST_PARAMS = {
    "commission_rate": 0.001425,          # 手續費率 0.1425%
    "min_commission": 20.0,               # 最低手續費 20 元
    "tax_rate": 0.003,                    # 證交稅率 0.3%（僅賣出）
}
```

### 滑價參數

```python
DEFAULT_SLIPPAGE_PARAMS = {
    "model": "fixed",                     # "fixed", "percentage", "volume"
    "fixed_slippage": 0.1,               # 固定滑價 0.1 元
    "slippage_pct": 0.001,               # 百分比滑價 0.1%
    "base_slippage": 0.001,              # 基礎滑價 0.1%
    "impact_factor": 1.0,                # 市場衝擊係數
}
```

---

## 7. 錯誤處理

### 錯誤類型

- `InsufficientCashError`: 現金不足
- `InsufficientPositionError`: 持倉不足（賣出時）
- `InvalidOrderError`: 無效訂單（例如：數量為 0）
- `ExecutionError`: 執行失敗

### 錯誤處理策略

- 記錄錯誤但不中斷整個執行流程
- 返回部分執行的結果
- 在 diagnostics 中標記錯誤

---

**版本**：v1.0  
**狀態**：✅ Spec 規範已確立

