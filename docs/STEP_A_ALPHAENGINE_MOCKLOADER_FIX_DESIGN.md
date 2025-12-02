# Step A：修正 AlphaEngine + Mock Loader 設計文件

## (A) 目前資料流與錯誤原因分析

### A1. MockPathADataLoader 輸出格式

**price_frame 格式：**
- **index**: `DatetimeIndex` (date)
  - 例如：`DatetimeIndex(['2024-01-01', '2024-01-02', ...], dtype='datetime64[ns]', freq=None)`
- **columns**: `MultiIndex` (symbol, field)
  - Level 0: symbol（例如：`'2330.TW'`, `'2317.TW'`, `'2303.TW'`）
  - Level 1: field（例如：`'open'`, `'high'`, `'low'`, `'close'`, `'volume'`）
  - 形狀：`[(2330.TW, open), (2330.TW, high), ..., (2317.TW, open), ...]`

**feature_frame 格式：**
- **index**: `MultiIndex` (date, symbol)
  - Level 0: date（`DatetimeIndex`）
  - Level 1: symbol（字串）
  - 形狀：`[(2024-01-01, 2330.TW), (2024-01-01, 2317.TW), (2024-01-01, 2303.TW), (2024-01-02, 2330.TW), ...]`
- **columns**: feature names（例如：`['daily_return_1d', 'rolling_vol_5d']`）

### A2. Path A Backtest 傳給 AlphaEngine 的資料

**流程（path_a_backtest.py 第 202-210 行）：**
```python
# 從 feature_frame 提取特定日期的資料
if isinstance(feature_frame.index, pd.MultiIndex):
    date_mask = feature_frame.index.get_level_values(0) == current_date
    feature_slice = feature_frame.loc[date_mask]  # 取得該日期的所有股票
    alpha_input = feature_slice.droplevel(0)  # 移除 date level
```

**alpha_input 實際格式：**
- **index**: symbol（例如：`['2330.TW', '2317.TW', '2303.TW']`）
- **columns**: feature names（例如：`['daily_return_1d', 'rolling_vol_5d']`）
- **形狀**: (n_symbols, n_features)
- **範例**:
```
                 daily_return_1d  rolling_vol_5d
2330.TW         0.001234        0.012345
2317.TW         0.002345        0.013456
2303.TW        -0.000123        0.011234
```

### A3. AlphaEngine.compute_all() 的期望格式

**設計意圖（alpha_engine.py 第 98-118 行）：**
- **index**: `DatetimeIndex`（日期時間序列）
- **columns**: feature names（例如：`close`, `volume`, `daily_return_1d` 等）
- **形狀**: (n_dates, n_features)
- **用途**: 單一股票的時間序列資料

**範例期望輸入：**
```
            close    volume  daily_return_1d  rolling_vol_5d
2024-01-01  100.5    5000    0.001234        0.012345
2024-01-02  101.2    5200    0.006969        0.013456
2024-01-03  100.8    4800    -0.003953       0.014123
```

### A4. 錯誤發生點分析

**錯誤位置：alpha_engine.py 第 128-133 行**
```python
# Ensure index is datetime
if not isinstance(df.index, pd.DatetimeIndex):
    if 'date' in df.columns:
        df = df.set_index('date')
    else:
        df.index = pd.to_datetime(df.index)  # ← 這裡失敗！
```

**錯誤原因：**
1. Path A 傳入的 `alpha_input` 的 index 是 symbol（例如：`['2330.TW', '2317.TW', ...]`）
2. 不是 `DatetimeIndex`
3. `pd.to_datetime(['2330.TW', '2317.TW'])` 無法解析，產生警告：
   - `UserWarning: Could not infer format...`
   - `Unknown datetime string format, unable to parse: 2330.TW`

**後續影響：**
- 雖然警告後程式繼續執行，但 `df.index` 變成無效的 DatetimeIndex
- 各個 factor 的 `compute()` 方法都期望 DatetimeIndex，導致計算失敗
- 最終 fallback 到零 alpha

### A5. Risk Model Covariance Matrix 問題

**錯誤位置：path_a_backtest.py 第 239-248 行**
```python
cov_matrix = ctx.risk_model.get_covariance_matrix()
if cov_matrix.shape[0] != len(config.universe):
    # Shape mismatch → fallback to identity matrix
    cov_matrix = np.eye(len(config.universe))
```

**問題原因：**
- `MultiFactorRiskModel` 還沒有被 fit 過，或者 symbols 沒有對齊
- `get_covariance_matrix()` 回傳的矩陣維度與 universe 大小不符
- 導致每次都 fallback 到 identity matrix

## (B) AlphaEngine 的「正式輸入規格」建議（格式契約）

### B1. 雙模式設計建議

AlphaEngine 應該支援兩種輸入模式：

**模式 1：時間序列模式（Time Series Mode）**
- **index**: `DatetimeIndex`（日期時間）
- **columns**: feature names
- **用途**: 單一股票的時間序列資料
- **輸出**: 每個時間點的 factor scores

**模式 2：橫截面模式（Cross-Sectional Mode）** ⭐ 新增
- **index**: symbol（字串）
- **columns**: feature names
- **用途**: 多個股票在同一日期的橫截面資料
- **輸出**: 每個股票的 factor scores

### B2. 建議的介面設計

```python
def compute_all(
    self, 
    df: pd.DataFrame,
    mode: str = "auto"  # "timeseries" | "cross_sectional" | "auto"
) -> pd.DataFrame:
    """
    Args:
        df: Input DataFrame
            - If mode="timeseries": index=DatetimeIndex, columns=features
            - If mode="cross_sectional": index=symbol, columns=features
            - If mode="auto": 自動偵測（檢查 index 類型）
        mode: 運算模式
    
    Returns:
        DataFrame with factor scores
            - index: 與輸入相同
            - columns: factor score columns + 'composite_alpha'
    """
```

### B3. 自動偵測邏輯（mode="auto"）

```python
if isinstance(df.index, pd.DatetimeIndex):
    # 時間序列模式
    mode = "timeseries"
elif isinstance(df.index, pd.Index) and all(isinstance(x, str) for x in df.index):
    # 可能是橫截面模式（symbol index）
    mode = "cross_sectional"
else:
    # 無法判斷，嘗試轉換
    # ... 處理邏輯
```

## (C) MockPathADataLoader 調整方案

### C1. 目前輸出格式（不需修改）

MockPathADataLoader 的輸出格式已經是合理的：
- `price_frame`: index=date, columns=MultiIndex(symbol, field) ✅
- `feature_frame`: index=MultiIndex(date, symbol), columns=features ✅

**建議：保持不變**，因為這個格式符合 Path A 的設計。

### C2. 可能需要增加的欄位

為了讓 AlphaEngine 能正常運作，`feature_frame` 可能需要包含更多欄位：

**目前只有：**
- `daily_return_1d`
- `rolling_vol_5d`

**建議增加（從 price_frame 衍生）：**
- `close`: 收盤價
- `volume`: 成交量
- `open`, `high`, `low`: 開高低價（某些 factor 需要）

這樣 AlphaEngine 的 factor 就能正常計算了。

## (D) AlphaEngine 修正方案

### D1. 修改 compute_all() 方法（alpha_engine.py）

**位置：第 98-169 行**

**修改點 1：加入模式偵測（第 128-133 行附近）**
```python
# 偵測輸入模式
if isinstance(df.index, pd.DatetimeIndex):
    mode = "timeseries"
elif isinstance(df.index, pd.Index) and len(df.index) > 0:
    # 檢查是否為 symbol index（橫截面模式）
    first_val = df.index[0]
    if isinstance(first_val, str) and not _looks_like_date(first_val):
        mode = "cross_sectional"
    else:
        # 嘗試轉換為 datetime
        mode = "timeseries"
        df.index = pd.to_datetime(df.index, errors='coerce')
else:
    mode = "auto"  # 無法判斷

def _looks_like_date(val: str) -> bool:
    """檢查字串是否像日期格式"""
    # 簡單檢查：是否包含數字和分隔符（例如：'2024-01-01'）
    import re
    return bool(re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}', str(val)))
```

**修改點 2：橫截面模式的處理邏輯**

在橫截面模式下，不需要轉換 index 為 DatetimeIndex，而是：
1. 直接對每一行（每個 symbol）計算 factor scores
2. 因子計算時使用橫截面邏輯（例如：與其他股票的比較）

**修改點 3：移除強制 DatetimeIndex 轉換**

```python
# 舊版（錯誤）：
if not isinstance(df.index, pd.DatetimeIndex):
    df.index = pd.to_datetime(df.index)  # ← 會失敗

# 新版（正確）：
if mode == "timeseries":
    if not isinstance(df.index, pd.DatetimeIndex):
        # 只在確定是時間序列模式時才轉換
        if 'date' in df.columns:
            df = df.set_index('date')
        else:
            df.index = pd.to_datetime(df.index, errors='coerce')
            df.index = df.index.fillna(pd.Timestamp.now())  # 處理無法解析的情況
elif mode == "cross_sectional":
    # 橫截面模式：保持 index 為 symbol
    pass  # 不做轉換
```

### D2. 修改各個 Factor 的 compute() 方法

**問題：** 所有 factor（FlowFactor, DivergenceFactor 等）都假設輸入是時間序列格式。

**解決方案選項：**

**選項 A：在 AlphaEngine 層統一處理**
- AlphaEngine 在調用 factor.compute() 之前，先轉換資料格式
- Factor 不需要修改

**選項 B：讓 Factor 支援雙模式**
- 修改 FactorBase.compute() 接受 mode 參數
- 每個 factor 自己處理兩種模式

**建議：選項 A**（在 AlphaEngine 層處理）

### D3. 橫截面模式的因子計算邏輯

在橫截面模式下，factor 的計算邏輯需要調整：

**時間序列模式（原始邏輯）：**
- 計算時間序列的統計量（例如：rolling mean, rolling std）
- 比較當前期與歷史期

**橫截面模式（新邏輯）：**
- 計算橫截面統計量（例如：cross-sectional mean, cross-sectional std）
- 比較當前股票與其他股票
- 例如：`z_score = (value - cross_sectional_mean) / cross_sectional_std`

**實作建議：**
```python
if mode == "cross_sectional":
    # 對每個 feature 做橫截面標準化
    for col in df.columns:
        if col in factor_required_features:
            mean = df[col].mean()
            std = df[col].std()
            if std > 0:
                df[col] = (df[col] - mean) / std
            else:
                df[col] = 0.0
```

## (E) Path A Backtest 中介層的修正方案

### E1. 不需要修改

Path A Backtest 目前的資料提取邏輯是正確的：
- 從 feature_frame 提取特定日期
- drop date level，得到 symbol-indexed DataFrame
- 傳給 AlphaEngine

**建議：保持不變**

### E2. 可能需要增加資料轉換 helper

**位置：path_a_backtest.py 新增 helper 函式**

```python
def _prepare_alpha_input(
    feature_frame: pd.DataFrame,
    price_frame: pd.DataFrame,
    current_date: pd.Timestamp,
    universe: List[str]
) -> pd.DataFrame:
    """
    準備 AlphaEngine 的輸入資料
    
    將 feature_frame + price_frame 合併，產生包含所有必要欄位的 DataFrame
    """
    # 1. 從 feature_frame 提取該日期的 features
    if isinstance(feature_frame.index, pd.MultiIndex):
        date_mask = feature_frame.index.get_level_values(0) == current_date
        feature_slice = feature_frame.loc[date_mask].droplevel(0)
    else:
        feature_slice = feature_frame.loc[[current_date]]
    
    # 2. 從 price_frame 提取該日期的價格資料
    price_data = {}
    for symbol in universe:
        if isinstance(price_frame.columns, pd.MultiIndex):
            price_data[symbol] = {
                'close': price_frame.loc[current_date, (symbol, 'close')],
                'volume': price_frame.loc[current_date, (symbol, 'volume')],
                'open': price_frame.loc[current_date, (symbol, 'open')],
                'high': price_frame.loc[current_date, (symbol, 'high')],
                'low': price_frame.loc[current_date, (symbol, 'low')],
            }
    
    # 3. 合併成單一 DataFrame
    price_df = pd.DataFrame(price_data).T
    alpha_input = feature_slice.join(price_df, how='outer')
    
    return alpha_input
```

### E3. 在 Backtest Loop 中使用 helper

**修改位置：path_a_backtest.py 第 202-210 行**

```python
# 使用 helper 準備 alpha input
alpha_input = _prepare_alpha_input(
    feature_frame=feature_frame,
    price_frame=price_frame,
    current_date=current_date,
    universe=config.universe
)

# 傳給 AlphaEngine（使用橫截面模式）
alpha_result = ctx.alpha_engine.compute_all(alpha_input, mode="cross_sectional")
```

## (F) Risk Model Covariance Matrix 修正方案

### F1. 問題分析

**問題：** Risk Model 沒有被 fit 過，所以 covariance matrix 的 shape 不對。

**解決方案：**

**選項 A：在 Backtest 開始前 fit Risk Model**
- 使用歷史資料（例如：前 252 天）fit Risk Model
- 需要提供 returns 資料

**選項 B：使用簡化的 covariance 計算**
- 在 Path A Backtest 中，直接用 price_frame 計算 returns
- 計算 sample covariance matrix

**建議：選項 B（簡化實作）**

### F2. 在 Path A Backtest 中計算 Covariance

**新增 helper 函式：path_a_backtest.py**

```python
def _compute_sample_covariance(
    price_frame: pd.DataFrame,
    universe: List[str],
    lookback_days: int = 60
) -> np.ndarray:
    """
    從 price_frame 計算 returns 和 covariance matrix
    
    Returns:
        Covariance matrix (n_symbols × n_symbols)
    """
    # 1. 提取 close prices
    close_prices = {}
    for symbol in universe:
        if isinstance(price_frame.columns, pd.MultiIndex):
            close_prices[symbol] = price_frame[(symbol, 'close')]
        else:
            close_prices[symbol] = price_frame[f'{symbol}_close']
    
    close_df = pd.DataFrame(close_prices)
    
    # 2. 計算 returns（使用最近 lookback_days 天）
    recent_close = close_df.tail(lookback_days)
    returns = recent_close.pct_change().dropna()
    
    # 3. 計算 covariance matrix（年化）
    cov_matrix = returns.cov().values * 252  # 年化
    
    # 4. 確保與 universe 對齊
    symbol_order = list(universe)
    cov_matrix = cov_matrix.loc[symbol_order, symbol_order].values
    
    return cov_matrix
```

### F3. 在 Backtest Loop 中使用

**修改位置：path_a_backtest.py 第 239-248 行**

```python
# 計算 covariance matrix
try:
    # 方法1：使用 Risk Model（如果已經 fit）
    if ctx.risk_model.symbols == config.universe:
        cov_matrix = ctx.risk_model.get_covariance_matrix()
    else:
        # 方法2：從 price_frame 計算（簡化版）
        cov_matrix = _compute_sample_covariance(
            price_frame, 
            config.universe,
            lookback_days=60
        )
except Exception as e:
    print(f"Warning: Failed to compute covariance: {e}. Using identity matrix.")
    cov_matrix = np.eye(len(config.universe)) * 0.01  # 小一點的 identity
```

## (G) 完整的「給 Editor 用的修改 Checklist」

### G1. 檔案修改清單

#### 檔案 1：`jgod/alpha_engine/alpha_engine.py`

**修改項目：**
1. **修改 `compute_all()` 方法（第 98-169 行）**
   - 新增模式偵測邏輯（時間序列 vs 橫截面）
   - 新增 helper 函式 `_detect_input_mode(df: pd.DataFrame) -> str`
   - 新增 helper 函式 `_looks_like_date(val: str) -> bool`
   - 修改 index 處理邏輯，只在時間序列模式下才轉換為 DatetimeIndex
   - 橫截面模式下，保持 index 為 symbol，不做 datetime 轉換
   - 橫截面模式下，對 factor 計算做橫截面標準化處理

2. **新增橫截面模式處理邏輯**
   - 在橫截面模式下，對每個 feature 做 cross-sectional z-score
   - Factor 計算時使用橫截面統計量而非時間序列統計量

**具體修改位置：**
- 第 128-133 行：修改 index 檢查邏輯
- 第 135-169 行：新增模式分支處理

#### 檔案 2：`jgod/path_a/path_a_backtest.py`

**修改項目：**
1. **新增 helper 函式 `_prepare_alpha_input()`（在檔案末尾，helpers 區塊）**
   - 合併 feature_frame 和 price_frame 的資料
   - 確保 alpha_input 包含所有必要欄位（close, volume, open, high, low, daily_return_1d, rolling_vol_5d）

2. **新增 helper 函式 `_compute_sample_covariance()`（在檔案末尾，helpers 區塊）**
   - 從 price_frame 計算 returns
   - 計算 sample covariance matrix（年化）

3. **修改 Backtest Loop 中的 AlphaEngine 呼叫（第 202-219 行）**
   - 使用 `_prepare_alpha_input()` 準備輸入
   - 明確指定 `mode="cross_sectional"` 傳給 `compute_all()`

4. **修改 Covariance Matrix 取得邏輯（第 239-248 行）**
   - 優先使用 Risk Model（如果已 fit）
   - Fallback 到 `_compute_sample_covariance()` 從 price_frame 計算

**具體修改位置：**
- 第 202-219 行：修改 alpha input 準備和呼叫
- 第 239-248 行：修改 covariance matrix 取得
- 第 411 行之後：新增兩個 helper 函式

#### 檔案 3：`jgod/path_a/mock_data_loader.py`

**修改項目（可選，但建議）：**
1. **擴充 `load_feature_frame()` 方法（第 119-166 行）**
   - 從 price_frame 提取更多欄位（close, volume, open, high, low）
   - 加入 feature_frame 中，讓 AlphaEngine 有足夠的資料

**具體修改位置：**
- 第 154-157 行：擴充 feature_data 字典，加入 price 相關欄位

#### 檔案 4：`jgod/alpha_engine/factor_base.py`（可選）

**修改項目：**
- 如果選擇讓 factor 自己處理橫截面模式，可以在這裡新增 helper 方法
- 但建議在 AlphaEngine 層統一處理，所以這個檔案可能不需要修改

### G2. 測試驗證步驟

1. **執行原有測試指令**
   ```bash
   PYTHONPATH=. python3 scripts/run_jgod_experiment.py \
     --name mock_demo \
     --start-date 2024-01-01 \
     --end-date 2024-01-10 \
     --rebalance-frequency D \
     --universe "2330.TW,2317.TW,2303.TW" \
     --data-source mock
   ```

2. **檢查輸出**
   - 不應該再出現 "Unknown datetime string format" 警告
   - 不應該再出現 "AlphaEngine computation failed" 警告
   - 不應該再出現 "Covariance matrix shape mismatch" 警告
   - Alpha 計算應該成功（composite_alpha 不應該全是 0）

3. **檢查結果**
   - NAV 曲線應該有變化（不是完全平坦）
   - Portfolio snapshots 應該有合理的權重分配

### G3. 注意事項

1. **向後相容性**
   - 確保現有的時間序列模式（如果有的話）仍然可以正常運作
   - `mode="auto"` 應該能正確偵測兩種模式

2. **FinMind Loader 相容性**
   - 確保未來的 FinMindPathADataLoader 也能產生相同格式的資料
   - MockPathADataLoader 和 FinMindPathADataLoader 應該輸出相同結構的 DataFrame

3. **Error Handling**
   - 如果模式偵測失敗，應該有明確的錯誤訊息
   - 如果 covariance 計算失敗，fallback 到合理的預設值

## 總結

核心問題是 **AlphaEngine 期望時間序列格式，但 Path A 傳入的是橫截面格式**。

解決方案是讓 **AlphaEngine 支援雙模式**：
- 時間序列模式：單一股票的時間序列（原始設計）
- 橫截面模式：多股票在同一日期（Path A 需求）

這樣既不會破壞原有設計，又能滿足 Path A 的需求。

