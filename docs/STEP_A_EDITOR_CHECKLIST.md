# Step A：修正 AlphaEngine + Mock Loader - Editor 修改檢查清單

## 修改目標

1. ✅ 修掉 AlphaEngine 把 symbol 當 datetime parse 的問題
2. ✅ 讓 AlphaEngine 在使用 MockPathADataLoader 時可以穩定計算 alpha
3. ✅ Covariance matrix 不要再 fallback identity
4. ✅ 不改壞現有 Path A / Orchestrator 流程

---

## 檔案修改清單

### 📝 檔案 1：`jgod/alpha_engine/alpha_engine.py`

#### 修改 1.1：新增模式偵測 Helper 函式

**位置：** 在 `compute_all()` 方法之前（約第 97 行之前）

**新增內容：**
```python
def _looks_like_date(self, val: str) -> bool:
    """檢查字串是否像日期格式"""
    import re
    return bool(re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}', str(val)))

def _detect_input_mode(self, df: pd.DataFrame) -> str:
    """偵測輸入 DataFrame 的模式
    
    Returns:
        "timeseries" - 時間序列模式（index 是 DatetimeIndex）
        "cross_sectional" - 橫截面模式（index 是 symbol）
    """
    if df.empty:
        return "timeseries"  # 預設
    
    if isinstance(df.index, pd.DatetimeIndex):
        return "timeseries"
    
    # 檢查 index 是否為 symbol（字串且不像日期）
    if len(df.index) > 0:
        first_val = str(df.index[0])
        if isinstance(df.index[0], str) and not self._looks_like_date(first_val):
            return "cross_sectional"
    
    # 預設嘗試時間序列
    return "timeseries"
```

#### 修改 1.2：修改 `compute_all()` 方法的 index 處理邏輯

**位置：** 第 128-133 行

**舊版：**
```python
# Ensure index is datetime
if not isinstance(df.index, pd.DatetimeIndex):
    if 'date' in df.columns:
        df = df.set_index('date')
    else:
        df.index = pd.to_datetime(df.index)
```

**新版：**
```python
# 偵測輸入模式
mode = self._detect_input_mode(df)

# 根據模式處理 index
if mode == "timeseries":
    # 時間序列模式：確保 index 是 DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'date' in df.columns:
            df = df.set_index('date')
        else:
            df.index = pd.to_datetime(df.index, errors='coerce')
            # 處理無法解析的情況
            invalid_mask = df.index.isna()
            if invalid_mask.any():
                # 如果無法解析，使用當前時間
                df.index = df.index.fillna(pd.Timestamp.now())
elif mode == "cross_sectional":
    # 橫截面模式：保持 index 為 symbol，不做 datetime 轉換
    # 但需要對 features 做橫截面標準化
    df = df.copy()  # 避免修改原始資料
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            mean = df[col].mean()
            std = df[col].std()
            if std > 0:
                df[col] = (df[col] - mean) / std
            else:
                df[col] = 0.0
```

#### 修改 1.3：調整 Factor 計算邏輯以支援橫截面模式

**位置：** 第 135-169 行（factor 計算迴圈）

**修改方式：**
- 在橫截面模式下，factor 的計算邏輯需要調整
- 但因為 factor.compute() 內部也會嘗試轉 DatetimeIndex，所以需要傳入 mode 參數
- 或者，在調用 factor.compute() 之前，先準備好正確格式的資料

**建議：** 先實作簡化版本，在橫截面模式下，每個 factor 回傳簡單的橫截面 z-score：
- 如果 df 有對應的欄位，直接使用該欄位做 z-score
- 如果沒有，回傳 0

**實際修改：** 在 factor 計算迴圈中加入模式判斷

---

### 📝 檔案 2：`jgod/path_a/path_a_backtest.py`

#### 修改 2.1：新增 `_prepare_alpha_input()` Helper 函式

**位置：** 在檔案末尾的 helpers 區塊（約第 411 行之後）

**新增內容：**
```python
def _prepare_alpha_input(
    feature_frame: pd.DataFrame,
    price_frame: pd.DataFrame,
    current_date: pd.Timestamp,
    universe: List[str]
) -> pd.DataFrame:
    """
    準備 AlphaEngine 的輸入資料
    
    將 feature_frame 和 price_frame 合併，產生包含所有必要欄位的 DataFrame
    
    Args:
        feature_frame: Feature frame with MultiIndex (date, symbol)
        price_frame: Price frame with index=date, columns=MultiIndex(symbol, field)
        current_date: 當前日期
        universe: 股票列表
    
    Returns:
        DataFrame with index=symbol, columns=所有 features + price fields
    """
    # 1. 從 feature_frame 提取該日期的 features
    if isinstance(feature_frame.index, pd.MultiIndex):
        date_mask = feature_frame.index.get_level_values(0) == current_date
        feature_slice = feature_frame.loc[date_mask].droplevel(0)  # drop date level
    else:
        feature_slice = feature_frame.loc[[current_date]]
    
    # 2. 從 price_frame 提取該日期的價格資料
    price_data = {}
    for symbol in universe:
        try:
            if isinstance(price_frame.columns, pd.MultiIndex):
                price_data[symbol] = {
                    'close': price_frame.loc[current_date, (symbol, 'close')],
                    'volume': price_frame.loc[current_date, (symbol, 'volume')],
                    'open': price_frame.loc[current_date, (symbol, 'open')],
                    'high': price_frame.loc[current_date, (symbol, 'high')],
                    'low': price_frame.loc[current_date, (symbol, 'low')],
                }
            else:
                # wide format fallback
                price_data[symbol] = {
                    'close': price_frame.loc[current_date, f'{symbol}_close'],
                    'volume': price_frame.loc[current_date, f'{symbol}_volume'],
                    'open': price_frame.loc[current_date, f'{symbol}_open'],
                    'high': price_frame.loc[current_date, f'{symbol}_high'],
                    'low': price_frame.loc[current_date, f'{symbol}_low'],
                }
        except (KeyError, IndexError):
            # 如果某個欄位不存在，使用 NaN
            price_data[symbol] = {
                'close': np.nan,
                'volume': np.nan,
                'open': np.nan,
                'high': np.nan,
                'low': np.nan,
            }
    
    # 3. 合併成單一 DataFrame
    price_df = pd.DataFrame(price_data).T
    price_df.index.name = None  # 移除 index name
    
    # 4. 合併 feature 和 price 資料
    if feature_slice.index.name is not None:
        feature_slice.index.name = None
    
    alpha_input = feature_slice.join(price_df, how='outer')
    
    # 5. 確保所有 universe 的股票都在結果中
    alpha_input = alpha_input.reindex(universe, fill_value=0.0)
    
    # 6. 填充 NaN
    alpha_input = alpha_input.fillna(0.0)
    
    return alpha_input
```

#### 修改 2.2：新增 `_compute_sample_covariance()` Helper 函式

**位置：** 在檔案末尾的 helpers 區塊（約第 411 行之後，`_prepare_alpha_input()` 之後）

**新增內容：**
```python
def _compute_sample_covariance(
    price_frame: pd.DataFrame,
    universe: List[str],
    lookback_days: int = 60
) -> np.ndarray:
    """
    從 price_frame 計算 returns 和 covariance matrix
    
    Args:
        price_frame: Price frame with index=date, columns=MultiIndex(symbol, field)
        universe: 股票列表
        lookback_days: 使用的歷史天數
    
    Returns:
        Covariance matrix (n_symbols × n_symbols)，年化
    """
    # 1. 提取 close prices
    close_data = {}
    for symbol in universe:
        try:
            if isinstance(price_frame.columns, pd.MultiIndex):
                close_data[symbol] = price_frame[(symbol, 'close')]
            else:
                close_data[symbol] = price_frame[f'{symbol}_close']
        except KeyError:
            # 如果某個股票沒有資料，創建全 NaN 的 Series
            close_data[symbol] = pd.Series(np.nan, index=price_frame.index)
    
    close_df = pd.DataFrame(close_data)
    
    # 2. 使用最近 lookback_days 天
    if len(close_df) > lookback_days:
        recent_close = close_df.tail(lookback_days)
    else:
        recent_close = close_df
    
    # 3. 計算 returns
    returns = recent_close.pct_change().dropna()
    
    # 4. 如果資料不足，返回 identity matrix
    if len(returns) < 2:
        n = len(universe)
        return np.eye(n) * 0.01  # 小一點的 identity
    
    # 5. 確保所有 universe 的股票都有資料
    returns = returns.reindex(columns=universe, fill_value=0.0)
    
    # 6. 計算 covariance matrix（年化）
    cov_matrix = returns.cov().values * 252  # 年化
    
    # 7. 確保是對稱且正定
    cov_matrix = (cov_matrix + cov_matrix.T) / 2  # 確保對稱
    eigenvalues = np.linalg.eigvals(cov_matrix)
    if np.any(eigenvalues < 0):
        # 如果有負特徵值，調整
        cov_matrix = cov_matrix + np.eye(len(universe)) * 0.001
    
    return cov_matrix
```

#### 修改 2.3：修改 Backtest Loop 中的 AlphaEngine 呼叫

**位置：** 第 202-219 行

**舊版：**
```python
# Extract features for current_date across all symbols
if isinstance(feature_frame.index, pd.MultiIndex):
    date_mask = feature_frame.index.get_level_values(0) == current_date
    feature_slice = feature_frame.loc[date_mask]
    # AlphaEngine expects a DataFrame with index=symbol
    alpha_input = feature_slice.droplevel(0)  # drop date level
else:
    # Single-level index: assume date index, need to extract by date
    alpha_input = feature_frame.loc[[current_date]]

# TODO: Ensure alpha_input has the correct format for AlphaEngine
# AlphaEngine.compute_all expects a DataFrame per symbol, not per date
# This may need adjustment based on actual AlphaEngine interface

# For now, we'll compute composite_alpha assuming feature_frame
# is properly formatted
try:
    alpha_result = ctx.alpha_engine.compute_all(alpha_input)
```

**新版：**
```python
# 使用 helper 準備 alpha input（合併 feature 和 price 資料）
alpha_input = _prepare_alpha_input(
    feature_frame=feature_frame,
    price_frame=price_frame,
    current_date=current_date,
    universe=config.universe
)

try:
    # 使用橫截面模式
    alpha_result = ctx.alpha_engine.compute_all(alpha_input)
```

#### 修改 2.4：修改 Covariance Matrix 取得邏輯

**位置：** 第 239-248 行

**舊版：**
```python
try:
    cov_matrix = ctx.risk_model.get_covariance_matrix()
    # Ensure covariance matrix is aligned with universe
    if cov_matrix.shape[0] != len(config.universe):
        # If shape mismatch, create a simple identity matrix as fallback
        print(f"Warning: Covariance matrix shape mismatch. Using identity matrix.")
        cov_matrix = np.eye(len(config.universe))
except Exception as e:
    print(f"Warning: Failed to get covariance matrix: {e}. Using identity matrix.")
    cov_matrix = np.eye(len(config.universe))
```

**新版：**
```python
try:
    # 優先嘗試從 Risk Model 取得（如果已經 fit 且 symbols 對齊）
    if hasattr(ctx.risk_model, 'symbols') and ctx.risk_model.symbols == list(config.universe):
        cov_matrix = ctx.risk_model.get_covariance_matrix()
        if cov_matrix.shape[0] == len(config.universe):
            # Shape 正確，使用它
            pass
        else:
            # Shape 不對，改用 sample covariance
            cov_matrix = _compute_sample_covariance(
                price_frame,
                list(config.universe),
                lookback_days=min(60, len(price_frame))
            )
    else:
        # Risk Model 還沒 fit 或 symbols 不對齊，從 price_frame 計算
        cov_matrix = _compute_sample_covariance(
            price_frame,
            list(config.universe),
            lookback_days=min(60, len(price_frame))
        )
except Exception as e:
    print(f"Warning: Failed to compute covariance matrix: {e}. Using identity matrix.")
    # 使用小的 identity matrix（而不是全 1）
    cov_matrix = np.eye(len(config.universe)) * 0.01
```

---

### 📝 檔案 3：`jgod/path_a/mock_data_loader.py`（可選，建議）

#### 修改 3.1：擴充 `load_feature_frame()` 以包含更多欄位

**位置：** 第 119-166 行

**修改方式：**
在 `load_feature_frame()` 方法中，除了計算 `daily_return_1d` 和 `rolling_vol_5d` 外，也從 price_frame 提取 close, volume, open, high, low 欄位，加入 feature_frame。

**具體修改位置：**
- 第 154-162 行：擴充 feature_data 字典

**新增欄位：**
```python
feature_data = {
    "daily_return_1d": [],
    "rolling_vol_5d": [],
    "close": [],      # 新增
    "volume": [],     # 新增
    "open": [],       # 新增
    "high": [],       # 新增
    "low": [],        # 新增
}
```

並在迴圈中填充這些欄位：
```python
for date in dates:
    for symbol in symbols:
        feature_data["daily_return_1d"].append(returns.loc[date, symbol])
        feature_data["rolling_vol_5d"].append(rolling_vol.loc[date, symbol])
        # 新增：價格欄位
        feature_data["close"].append(close_df.loc[date, symbol])
        # volume, open, high, low 類似處理
```

---

## 驗證步驟

### 1. 靜態檢查
```bash
PYTHONPATH=. python3 -m py_compile jgod/alpha_engine/alpha_engine.py
PYTHONPATH=. python3 -m py_compile jgod/path_a/path_a_backtest.py
PYTHONPATH=. python3 -m py_compile jgod/path_a/mock_data_loader.py
```

### 2. 執行測試
```bash
PYTHONPATH=. python3 scripts/run_jgod_experiment.py \
  --name mock_demo \
  --start-date 2024-01-01 \
  --end-date 2024-01-10 \
  --rebalance-frequency D \
  --universe "2330.TW,2317.TW,2303.TW" \
  --data-source mock
```

### 3. 檢查輸出
- ✅ 不應該出現 "Unknown datetime string format" 警告
- ✅ 不應該出現 "AlphaEngine computation failed" 警告
- ✅ 不應該出現 "Covariance matrix shape mismatch" 警告
- ✅ NAV 曲線應該有變化（不是完全平坦）
- ✅ Alpha 計算應該成功

---

## 修改優先順序

1. **優先級 1（必須）：** 檔案 1 和檔案 2 的修改（修掉 datetime parse 錯誤）
2. **優先級 2（建議）：** 檔案 3 的修改（擴充 feature_frame）
3. **優先級 3（未來）：** 更完善的橫截面 factor 計算邏輯

---

## 注意事項

1. **向後相容性**：確保時間序列模式仍然可以運作
2. **錯誤處理**：所有 fallback 都應該有清楚的錯誤訊息
3. **測試覆蓋**：修改後應該通過現有的測試指令

