# Factor Engine 模組

## 概述

Factor Engine 模組是創世紀量化系統的核心因子計算引擎，負責實作各種 Alpha 因子。

## 已實作模組

### 1. InfoTimeBarGenerator（信息時間引擎）- Step 2

**檔案**：`info_time_engine.py`

**功能**：
- 累積 UnifiedTick 數據，形成 Volume Bar（基於成交量，非時鐘時間）
- 計算 VWAP（Volume Weighted Average Price）
- 計算 F_InfoTime 因子：`F_InfoTime = current_interval / long_term_avg_freq`

**核心類別**：
- `VolumeBar`：Volume Bar 資料結構
- `InfoTimeBarGenerator`：Volume Bar 生成器

**使用範例**：

```python
from data_feed import MockSinopacAPI, SinopacConverter
from factor_engine import InfoTimeBarGenerator

# 1. 建立數據來源
mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)
converter = SinopacConverter()

# 2. 建立 Volume Bar 生成器
generator = InfoTimeBarGenerator(volume_bar_size=5_000_000)  # 5M volume per bar

# 3. 處理 Tick 並產生 VolumeBar
for i in range(100):
    raw_tick = mock_api.get_next_raw_tick()
    unified_tick = converter.convert_to_unified(raw_tick)
    
    volume_bar = generator.add_tick(unified_tick)
    
    if volume_bar:
        print(f"VolumeBar 產生: VWAP={volume_bar.vwap:.2f}, Volume={volume_bar.total_volume}")
        
        # 計算 F_InfoTime
        infotime = generator.calculate_infotime_factor()
        print(f"F_InfoTime: {infotime:.4f}")
```

### 2. OrderbookFactorEngine（微觀流動性因子引擎）- Step 3

**檔案**：`orderbook_factor.py`

**功能**：
- 基於 Bid1/Ask1 的即時計算（無狀態、硬體加速友善）
- 計算 Mid Price、Spread、相對價差（bp）、流動性成本指數（LCI）
- 嚴格驗證 Bid/Ask 合理性，避免錯價污染因子

**核心類別**：
- `OrderbookFactor`：F_Orderbook 因子資料結構
- `OrderbookFactorEngine`：無狀態因子計算引擎

**設計特點**：
- **完全無狀態**：每個 Tick 獨立計算，適合硬體加速與向量化
- **僅依賴 Bid1/Ask1**：不需要整本 Orderbook，也不需要歷史視窗
- **硬體友善接口**：提供 `calculate_from_bid_ask` 靜態方法，方便 C/CUDA/Numba 實作

**使用範例**：

```python
from data_feed import MockSinopacAPI, SinopacConverter
from factor_engine import OrderbookFactorEngine

# 1. 建立數據來源
mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)
converter = SinopacConverter()

# 2. 建立 OrderbookFactorEngine
engine = OrderbookFactorEngine(symbol="2330.TW")

# 3. 處理 Tick 並計算 F_Orderbook
for i in range(10):
    raw_tick = mock_api.get_next_raw_tick()
    unified_tick = converter.convert_to_unified(raw_tick)
    
    factor = engine.calculate_factor(unified_tick)
    if factor:
        print(f"F_Orderbook: Mid={factor.mid_price:.2f}, Spread={factor.spread:.2f}, LCI={factor.liquidity_cost_index:.2f} bp")
```

**硬體友善接口**：

```python
# 直接傳入數值，不依賴 UnifiedTick 結構
factor = OrderbookFactorEngine.calculate_from_bid_ask(
    timestamp=1234567890.0,
    symbol="2330.TW",
    bid_price=749.5,
    ask_price=750.5,
)
```

### 3. CapitalFlowEngine（資金流基礎因子引擎）- Step 4

**檔案**：`capital_flow_factor.py`

**功能**：
- 基於 Tick 的 price/volume 和 Bid/Ask 推估多空方向
- 計算 SAI（Smart Aggression Index）：視窗內資金多空不平衡程度
- 計算 MOI（Momentum of Imbalance）：視窗內不平衡的變化趨勢

**核心類別**：
- `CapitalFlowSample`：內部資金流樣本（已判斷多空方向）
- `CapitalFlowFactor`：F_C 因子資料結構（包含 SAI 和 MOI）
- `CapitalFlowEngine`：資金流基礎因子計算引擎

**設計特點**：
- **輕量狀態**：只保留最近 N 筆 CapitalFlowSample
- **不依賴特定 Tick 類型**：只要求欄位存在
- **適合硬體加速**：核心計算邏輯簡單，適合 Numba/C++/CUDA 平行化

**SAI 計算邏輯**：
- 根據 `price` 相對 `mid = (bid + ask) / 2` 的位置判斷多空方向
- `price > mid + tolerance` → 買方主動（side = +1）
- `price < mid - tolerance` → 賣方主動（side = -1）
- `price` 接近 `mid` → 中性（side = 0）
- `SAI = (buy_volume - sell_volume) / total_volume` ∈ [-1, 1]

**MOI 計算邏輯**：
- 將視窗拆成前半段和後半段
- 分別計算 `early_imbalance` 和 `recent_imbalance`
- `MOI = recent_imbalance - early_imbalance`
- `MOI > 0`：多方攻擊力「近期比過去更強」
- `MOI < 0`：空方攻擊力「近期比過去更強」

**使用範例**：

```python
from data_feed import MockSinopacAPI, SinopacConverter
from factor_engine import CapitalFlowEngine

# 1. 建立數據來源
mock_api = MockSinopacAPI(symbol="2330", base_price=750.0)
converter = SinopacConverter()

# 2. 建立 CapitalFlowEngine
engine = CapitalFlowEngine(symbol="2330.TW", window_size=20, min_points=10)

# 3. 處理 Tick 並計算 F_C
for i in range(30):
    raw_tick = mock_api.get_next_raw_tick()
    unified_tick = converter.convert_to_unified(raw_tick)
    
    factor = engine.update_from_tick(unified_tick)
    if factor:
        print(f"F_C: SAI={factor.smart_aggression_index:.4f}, MOI={factor.momentum_of_imbalance:.4f}")
```

### 4. CrossAssetFactorEngine（跨資產聯動因子引擎）- Step 5

**檔案**：`cross_asset_factor.py`

**功能**：
- 接收 VolumeBar（而非 Tick），計算跨市場聯動強度
- 計算 rolling correlation：衡量 target 與 reference 的近期聯動強度
- 計算 rolling beta：衡量 target 對 reference 的敏感度（風險/槓桿關係）
- 支援多個 reference symbols（例如：QQQ, ES, USD/TWD）

**核心類別**：
- `CrossAssetWindowConfig`：計算視窗與參考資產設定
- `CrossAssetFactor`：單一 target 對 reference 的因子輸出
- `CrossAssetFactorEngine`：跨資產因子計算引擎

**設計特點**：
- **基於 VolumeBar**：接收 InfoTime Bar 而非原始 Tick，與系統時間單位一致
- **Rolling Window**：使用固定長度的歷史視窗計算動態相關性
- **多 Reference 支援**：可同時追蹤多個參考資產的聯動關係

**計算邏輯**：
- **Rolling Correlation**：使用 `np.corrcoef` 計算 target 與 reference 的報酬相關性
- **Rolling Beta**：使用 `beta = Cov(x, y) / Var(x)` 計算線性回歸係數
- **Log Return**：使用對數報酬 `log(p_t / p_{t-1})` 計算價格變化

**使用範例**：

```python
from factor_engine import (
    CrossAssetWindowConfig,
    CrossAssetFactorEngine,
    VolumeBar,
)

# 1. 建立配置
config = CrossAssetWindowConfig(
    target_symbol="2330.TW",
    reference_symbols=["QQQ", "ES"],
    window_size=20,
)

# 2. 建立引擎
engine = CrossAssetFactorEngine(config)

# 3. 每次有新的 VolumeBar 時更新
bar = VolumeBar(...)  # 從 InfoTimeBarGenerator 取得
factors = engine.update_with_bar(bar)

if factors:
    for f in factors:
        print(f"Target: {f.target_symbol} vs Reference: {f.reference_symbol}")
        print(f"  Correlation: {f.rolling_corr:.4f}")
        print(f"  Beta: {f.rolling_beta:.4f}")
```

## VolumeBar 資料結構

```python
@dataclass
class VolumeBar:
    start_ts: float          # Volume Bar 開始時間戳
    end_ts: float            # Volume Bar 結束時間戳
    symbol: str              # 股票代號
    vwap: float              # Volume Weighted Average Price
    total_volume: int        # 累積成交量
    tick_count: int          # 包含的 Tick 數量
    open_price: float        # 開盤價
    high_price: float        # 最高價
    low_price: float         # 最低價
    close_price: float       # 收盤價
    avg_bid: float           # 平均買價
    avg_ask: float           # 平均賣價
```

## F_InfoTime 因子說明

F_InfoTime 衡量當前信息流的速度：

- **F_InfoTime > 1.0**：當前信息流較慢（市場沉寂）
- **F_InfoTime = 1.0**：正常信息流
- **F_InfoTime < 1.0**：當前信息流較快（市場活躍）

計算公式：
```
F_InfoTime = current_interval / long_term_avg_interval
```

其中：
- `current_interval`：當前 Volume Bar 的間隔時間
- `long_term_avg_interval`：長期平均間隔時間（最近 N 個 Bar 的平均）

## 資料結構

### OrderbookFactor

```python
@dataclass(frozen=True)
class OrderbookFactor:
    timestamp: float              # 時間戳
    symbol: str                  # 股票代號
    mid_price: float             # 買賣中點價格 = (Bid + Ask) / 2
    spread: float                 # 絕對價差 = Ask - Bid
    rel_spread_bp: float         # 相對價差（Basis Points）= (spread / mid_price) * 10000
    liquidity_cost_index: float   # 流動性成本指數（目前 = rel_spread_bp）
```

### CapitalFlowFactor

```python
@dataclass(frozen=True)
class CapitalFlowFactor:
    timestamp: float                      # 時間戳
    symbol: str                          # 股票代號
    window_trades: int                   # 視窗內筆數
    window_volume: float                 # 視窗內總成交量
    buy_volume: float                    # 買方成交量
    sell_volume: float                   # 賣方成交量
    net_signed_volume: float             # 淨簽名成交量 = buy_volume - sell_volume
    smart_aggression_index: Optional[float]  # SAI ∈ [-1, 1]
    momentum_of_imbalance: Optional[float]  # MOI = recent_imbalance - early_imbalance
```

### CrossAssetFactor

```python
@dataclass(frozen=True)
class CrossAssetFactor:
    target_symbol: str                   # 目標資產代號
    reference_symbol: str                 # 參考資產代號
    timestamp: float                      # 因子計算時間戳
    rolling_corr: float                   # 近期報酬的 rolling correlation（-1 到 1）
    rolling_beta: float                   # 以 ref 為自變數的回歸 beta
    spread_zscore: Optional[float]       # 價差 Z-score（目前為 None，待未來實作）
```

## 依賴關係

### Step 2 (F_InfoTime)
- **輸入**：`UnifiedTick`（來自 `data_feed.tick_handler`）
- **輸出**：`VolumeBar`（用於後續因子計算）
- **後續依賴**：
  - F_Inertia：需要 VolumeBar 事件序列
  - F_PT：需要 VolumeBar 事件序列
  - F_MRR：需要 VolumeBar 事件序列

### Step 3 (F_Orderbook)
- **輸入**：`UnifiedTick`（需要 bid_price、ask_price）
- **輸出**：`OrderbookFactor`（用於後續因子計算）
- **後續依賴**：
  - 因子正交化（O-Factor）：需要 F_Orderbook 作為輸入
  - State Vector：需要 F_Orderbook 作為特徵

### Step 4 (F_C)
- **輸入**：`UnifiedTick`（需要 price、volume、bid_price、ask_price）
- **輸出**：`CapitalFlowFactor`（包含 SAI 和 MOI）
- **後續依賴**：
  - F_Inertia：需要 SAI_Residual（可從 SAI 衍生）
  - F_PT：需要 MOI 和 SAI_Residual
  - 因子正交化（O-Factor）：需要 F_C 作為輸入

### Step 5 (F_CrossAsset)
- **輸入**：`VolumeBar`（來自 Step 2 的 InfoTimeBarGenerator）
- **輸出**：`CrossAssetFactor`（包含 rolling_corr 和 rolling_beta）
- **後續依賴**：
  - 因子正交化（O-Factor）：需要 F_CrossAsset 作為輸入
  - State Vector：需要 F_CrossAsset 作為跨市場特徵

## 測試

執行測試：

```bash
# Step 2 測試
PYTHONPATH=. python3 tests/factor_engine/test_info_time_engine.py

# Step 3 測試
PYTHONPATH=. python3 tests/factor_engine/test_orderbook_factor.py

# Step 4 測試
PYTHONPATH=. python3 tests/factor_engine/test_capital_flow_factor.py

# Step 5 測試
PYTHONPATH=. python3 tests/factor_engine/test_cross_asset_factor.py
```

## 後續步驟

完成 Step 2-5 後，可以進行：

1. **Step 6**：資金流慣性因子（F_Inertia）- 需要 VolumeBar 事件序列 + SAI_Residual
2. **Step 7**：壓力傳導因子（F_PT）- 需要 MOI + SAI_Residual + VolumeBar 事件序列
3. **Step 8**：主力意圖逆轉因子（F_MRR）- 需要訂單事件序列
4. **Step 9**：因子正交化引擎（O-Factor）- 需要 F_C、F_Orderbook、F_CrossAsset 作為輸入

