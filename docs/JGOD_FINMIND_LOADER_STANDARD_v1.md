# J-GOD FinMind Loader Standard v1

## 📋 概述

本文檔定義 J-GOD Path A 系統中，FinMind 資料載入器（`FinMindPathADataLoader`）的標準介面、資料格式、與使用規範。

## 🎯 目標

1. **統一資料格式**：將 FinMind API 的資料轉換為 J-GOD 內部標準格式
2. **資料完整性**：處理資料缺漏、交易日對齊、異常值過濾
3. **穩定性**：提供 API caching、retry 機制、fallback 到 mock 資料
4. **擴展性**：支援未來擴充（權息調整、多資料源等）

---

## 📐 資料格式規範

### Input Format (FinMind API)

FinMind API 回傳的原始格式：
- **欄位**：`date`, `stock_id`, `open`, `high`, `low`, `close`, `Trading_Volume` (或其他變體)
- **型態**：`pd.DataFrame`
- **索引**：通常為 integer index，`date` 為欄位

### Output Format (J-GOD Internal)

#### Price Frame
```python
pd.DataFrame(
    index=pd.DatetimeIndex,  # 交易日（business days）
    columns=pd.MultiIndex.from_tuples([
        (symbol, "open"),
        (symbol, "high"),
        (symbol, "low"),
        (symbol, "close"),
        (symbol, "volume"),
    ], names=["symbol", "field"])
)
```

**範例：**
```
                    (2330.TW, open)  (2330.TW, high)  ...  (2317.TW, volume)
2024-01-01          550.0            555.0            ...  1000000.0
2024-01-02          552.0            558.0            ...  1100000.0
...
```

#### Feature Frame
```python
pd.DataFrame(
    index=pd.MultiIndex.from_product([
        dates,      # DatetimeIndex
        symbols     # List[str]
    ], names=["date", "symbol"]),
    columns=[
        "daily_return_1d",
        "rolling_vol_5d",
        "rolling_vol_20d",
        "momentum_5d",
        "momentum_20d",
        "turnover_rate",
        "close", "volume", "open", "high", "low"  # Price fields
    ]
)
```

**範例：**
```
                        daily_return_1d  rolling_vol_5d  ...  close
2024-01-01  2330.TW     0.0             0.0             ...  550.0
            2317.TW     0.0             0.0             ...  120.0
2024-01-02  2330.TW     0.0036          0.0012          ...  552.0
...
```

---

## 🔧 API 介面

### Class: `FinMindPathADataLoader`

#### Constructor
```python
FinMindPathADataLoader(
    client: Optional[FinMindClient] = None,
    config: Optional[FinMindLoaderConfig] = None,
)
```

**參數：**
- `client`: FinMindClient 實例。如果為 None，會自動建立（需要 FINMIND_TOKEN）
- `config`: Loader 配置。如果為 None，使用預設配置

#### Methods

##### `load_price_frame(config: PathAConfig) -> pd.DataFrame`
載入價格資料框架。

**輸入：**
- `config`: PathAConfig 物件，包含 `start_date`, `end_date`, `universe`

**輸出：**
- `pd.DataFrame`: 符合 J-GOD 格式的價格框架

**功能：**
- 從 FinMind API 取得資料
- 檢查 cache，避免重複呼叫
- 處理資料缺漏（forward fill）
- 對齊交易日曆
- 如果 FinMind 資料缺漏，fallback 到 mock 資料

##### `load_feature_frame(config: PathAConfig) -> pd.DataFrame`
載入特徵資料框架。

**輸入：**
- `config`: PathAConfig 物件

**輸出：**
- `pd.DataFrame`: 符合 J-GOD 格式的特徵框架

**功能：**
- 從 `load_price_frame()` 取得價格資料
- 計算所有必要特徵
- 處理 rolling window 的 NaN（允許前 N 天為 NaN）

##### `load_raw_finmind(symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]`
載入單一股票的原始 FinMind 資料（低階 API）。

**輸入：**
- `symbol`: 股票代號（例如："2330.TW"）
- `start_date`: 開始日期（YYYY-MM-DD）
- `end_date`: 結束日期（YYYY-MM-DD）

**輸出：**
- `pd.DataFrame` 或 `None`（如果無法取得）

**格式：**
```
  date        symbol    open    high    low     close   volume
2024-01-01  2330.TW    550.0   555.0   548.0   552.0   1000000
...
```

---

## ⚙️ 配置選項

### Class: `FinMindLoaderConfig`

```python
@dataclass
class FinMindLoaderConfig:
    cache_enabled: bool = True                    # 是否啟用 cache
    cache_dir: Path = Path("data_cache/finmind")  # Cache 目錄
    fallback_to_mock: bool = True                 # 是否 fallback 到 mock
    mock_config: Optional[MockConfig] = None      # Mock 配置
    max_retries: int = 3                          # 最大重試次數
    retry_delay: float = 1.0                      # 重試延遲（秒）
    min_data_days: int = 1                        # 最少需要的資料天數
    max_price_change: float = 0.20                # 最大單日價格變化（過濾異常值）
```

---

## 🔍 資料驗證與清理

### 驗證規則

1. **價格合理性**
   - `open > 0`, `high > 0`, `low > 0`, `close > 0`
   - `high >= max(open, close)`
   - `low <= min(open, close)`
   - `volume >= 0`

2. **異常值過濾**
   - 單日價格變化 > `max_price_change`（預設 20%）會被移除
   - 缺少必要欄位的資料會被移除

3. **交易日對齊**
   - 使用 `pd.date_range(freq='B')` 產生完整交易日曆
   - 缺失的交易日會 forward fill（使用前一日的價格）
   - 如果一開始就缺失，會 backward fill

---

## 🔄 Fallback 機制

### 觸發條件

1. **FinMind API 無法初始化**
   - 缺少 `FINMIND_TOKEN`
   - Token 無效

2. **資料缺漏**
   - 某個股票完全無法取得資料
   - 部分日期缺少資料（會先嘗試 forward fill）

### Fallback 行為

1. **API 初始化失敗**
   - 如果 `fallback_to_mock=True`，使用 `MockPathADataLoader`
   - 輸出警告訊息

2. **資料缺漏**
   - 對於完全缺漏的股票，使用 mock 資料補洞
   - 對於部分缺漏，使用 forward fill 補洞

---

## 💾 Cache 機制

### Cache 位置
- 預設：`data_cache/finmind/`
- 格式：`{symbol}_{start_date}_{end_date}.pkl`

### Cache 策略
1. **讀取**：在呼叫 FinMind API 前先檢查 cache
2. **寫入**：API 回應後立即寫入 cache
3. **失效**：手動刪除 cache 檔案來更新資料

### 使用建議
- **開發階段**：建議啟用 cache 減少 API 呼叫
- **生產階段**：可以禁用 cache 或定期清理 cache

---

## 📊 特徵計算

### 支援的特徵

1. **daily_return_1d**
   - 計算方式：`close.pct_change()`
   - 第一日為 0.0

2. **rolling_vol_5d**
   - 計算方式：`returns.rolling(5).std()`
   - 前 4 日使用 `min_periods=1`，可能為 NaN（允許）

3. **rolling_vol_20d**
   - 計算方式：`returns.rolling(20).std()`
   - 前 19 日使用 `min_periods=1`，可能為 NaN（允許）

4. **momentum_5d**
   - 計算方式：`close / close.shift(5) - 1`
   - 前 5 日為 0.0

5. **momentum_20d**
   - 計算方式：`close / close.shift(20) - 1`
   - 前 20 日為 0.0

6. **turnover_rate**
   - 計算方式：`volume / market_cap`
   - Market cap 為估算值（基於價格與成交量模式）

---

## 🔐 環境變數

### 必要變數
- `FINMIND_TOKEN`: FinMind API Token

### 設定方式
```bash
export FINMIND_TOKEN="your_token_here"
```

或在 `.env` 檔案中：
```
FINMIND_TOKEN=your_token_here
```

---

## 📝 使用範例

### 基本使用

```python
from jgod.path_a.finmind_data_loader import FinMindPathADataLoader
from jgod.path_a.path_a_schema import PathAConfig

# 建立 loader
loader = FinMindPathADataLoader()

# 建立 config
config = PathAConfig(
    start_date="2024-01-01",
    end_date="2024-01-31",
    universe=["2330.TW", "2317.TW", "2454.TW"],
    rebalance_frequency="D",
)

# 載入價格框架
price_frame = loader.load_price_frame(config)

# 載入特徵框架
feature_frame = loader.load_feature_frame(config)
```

### 自訂配置

```python
from jgod.path_a.finmind_data_loader import FinMindPathADataLoader, FinMindLoaderConfig
from pathlib import Path

config = FinMindLoaderConfig(
    cache_enabled=True,
    cache_dir=Path("custom_cache/"),
    fallback_to_mock=True,
    max_retries=5,
)

loader = FinMindPathADataLoader(config=config)
```

### 低階 API（單一股票）

```python
# 載入單一股票的原始資料
raw_data = loader.load_raw_finmind(
    symbol="2330.TW",
    start_date="2024-01-01",
    end_date="2024-01-31",
)

print(raw_data.head())
```

---

## 🚨 錯誤處理

### 常見錯誤與處理

1. **`ImportError: FinMind client not available`**
   - **原因**：未安裝 FinMind 套件或匯入失敗
   - **處理**：檢查套件安裝，或使用 mock 資料源

2. **`ValueError: FINMIND_TOKEN not found`**
   - **原因**：環境變數未設定
   - **處理**：設定 `FINMIND_TOKEN`，或使用 `fallback_to_mock=True`

3. **資料缺漏警告**
   - **原因**：FinMind API 回傳空資料或部分日期缺漏
   - **處理**：自動 fallback 到 mock 或 forward fill

4. **異常值過濾警告**
   - **原因**：偵測到異常價格變化
   - **處理**：自動移除異常值並記錄警告

---

## 🔮 未來擴充

### v2 規劃

1. **權息調整**
   - 支援復權價格計算
   - 處理除權除息事件

2. **本地資料庫快取**
   - 使用 SQLite 儲存歷史資料
   - 減少 API 呼叫

3. **多資料源支援**
   - 支援其他資料源（Yahoo Finance、其他 API）
   - 資料源優先級設定

4. **更精確的 Market Cap 計算**
   - 整合基本面資料
   - 即時市值計算

---

## 📚 相關文件

- `jgod/path_a/mock_data_loader.py` - Mock 資料載入器
- `jgod/path_a/path_a_schema.py` - Path A 資料結構定義
- `api_clients/finmind_client.py` - FinMind API 客戶端

---

## ✅ 測試建議

1. **單元測試**
   - 測試資料格式轉換
   - 測試 cache 機制
   - 測試 fallback 機制

2. **整合測試**
   - 測試完整資料載入流程
   - 測試與 AlphaEngine 的整合

3. **回歸測試**
   - 確認資料格式一致性
   - 確認無 NaN（除了允許的 rolling NaN）

