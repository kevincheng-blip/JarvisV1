# J-GOD FINMIND LOADER STANDARD v1.0

> 版本：v1.0  
> 目的：定義「Path A v1 使用 FinMind 取得台股歷史資料」的標準結構、欄位 mapping 與實作原則。  
> 範圍：僅涵蓋日資料（Daily OHLCV + 籌碼／簡易基本面），用於 Validation Lab（Path A）。

---

## 1. 定位與原則

FinMind Loader 在 J-GOD 系統中的角色：

- 作為 `PathADataLoader` 的一個具體實作版本：`FinMindPathADataLoader`

- 只負責「資料取得與清洗」，不負責 Alpha/Risk/Optimizer 的邏輯

- 嚴格避免未來資訊洩漏（no future leak）

- 以「可重複、可回溯」為優先：同一組 config 應產生相同結果

---

## 2. 功能範圍

### 2.1 必須提供的兩個方法（對應 PathADataLoader Protocol）

1. `load_price_frame(config: PathAConfig) -> pd.DataFrame`

   - 回傳整個實驗期間的價格資料

   - 格式：

     - index: `date`（DatetimeIndex）

     - columns: MultiIndex (`symbol`, `field`)

       - `field ∈ { "open", "high", "low", "close", "volume" }`

   - 時間區間：`config.start_date` ～ `config.end_date`

   - Universe：`config.universe` 中的全部 symbol

2. `load_feature_frame(config: PathAConfig) -> pd.DataFrame`

   - 回傳對應的特徵矩陣（Features）

   - 格式：

     - index: MultiIndex (`date`, `symbol`)

     - columns: feature names（文字）

   - v1 需求：

     - `daily_return_1d`

     - `rolling_vol_5d`

   - 特徵計算不可使用未來資料（只能用「當日前的歷史」）

---

## 3. Universe 與 Symbol 規範

- Path A v1 建議 Universe：

  - 0050 成分股＋少數代表性金融／傳產股（合計約 50～60 檔）

- Symbol 格式：

  - 在系統內使用：`"2330.TW"`、`"2317.TW"` 這類字串

  - FinMind API 通常使用：`"2330"` 的 stock_id 字串

  - Loader 必須負責：

    - 把 `"2330.TW"` 轉成 `"2330"` 呼叫 FinMind

    - 回傳 DataFrame 時 column MultiIndex 的 symbol 要回到 `"2330.TW"` 形式

---

## 4. FinMind 欄位 Mapping（價格）

以 FinMind `taiwan_stock_daily` 資料表為例：

- FinMind 欄位：

  - `date`

  - `stock_id`

  - `open`

  - `max`

  - `min`

  - `close`

  - `Trading_Volume`

- Path A 標準欄位：

| Path A 欄位 | FinMind 欄位       | 說明                       |
|-------------|--------------------|----------------------------|
| open        | open               | 開盤價                     |
| high        | max                | 最高價                     |
| low         | min                | 最低價                     |
| close       | close              | 收盤價（或還原價）         |
| volume      | Trading_Volume     | 交易量（股數或張數，照原始）|

Loader 責任：

1. 對 `config.universe` 的每一個 symbol：

   - 轉成 stock_id（去除 `.TW` 後綴）

   - 呼叫 FinMind 對應 API（例如 `taiwan_stock_daily`）

2. 把各股票結果：

   - 填入統一的日期索引（缺值用 NaN）

   - 組成 MultiIndex columns：`(symbol, field)`

---

## 5. FinMind 欄位 Mapping（特徵來源）

v1 的 `feature_frame` 不要求直接把所有籌碼／基本面欄位放進去，  
而是先定義「最小可用版本」：

1. 必要特徵：

   - `daily_return_1d`：  

     - 由 close 價計算：`(close_t / close_{t-1} - 1)`

   - `rolling_vol_5d`：  

     - `daily_return_1d` 在 5 日窗口的標準差

2. 其他延伸特徵（之後版本）可以來自：

   - 籌碼（外資／投信／自營商）

   - 融資融券

   - 簡易基本面（PE, PB, ROE, ROA, market_cap）

   - 大盤／產業指數報酬

> v1 只要求 FinMind Loader 先能提供 **價格 → return / vol 特徵**，  
> 裡面怎麼計算籌碼／基本面可以之後在 Path A v2 版再擴充。

---

## 6. 資料品質與防呆

FinMind Loader 必須處理以下情況：

1. **缺值與停牌**

   - 若某日某股沒有資料：

     - 價格欄位：用 NaN

     - 特徵計算時：

       - `daily_return_1d` → 0 或以 forward-fill 價格後計算

       - `rolling_vol_5d` → 以現有資料計算，`min_periods=1`

2. **日期對齊**

   - Loader 必須建立一個「統一的交易日索引」：

     - 例如用所有股票的日期 union，再過濾為台股交易日

   - 所有股票的 OHLCV 都要對齊到這個 index

3. **時區與字串格式**

   - `config.start_date` / `config.end_date` 皆為 `"YYYY-MM-DD"` 字串

   - Loader 需負責將其轉為 FinMind 所需格式（通常相同）

---

## 7. 實作原則

1. **依賴注入（Dependency Injection）**

   - `FinMindPathADataLoader` 不直接在內部 new DataLoader，而是接受一個 `client`：

     - `client` 需符合一個簡單 Protocol，例如：

       - `taiwan_stock_daily(stock_id, start_date, end_date) -> DataFrame`

   - 這樣在測試中可以注入 Dummy FinMind client，而不需要打外部 API。

2. **不在 Loader 內做 Logics 過度延伸**

   - Loader 不負責：

     - Alpha 計算

     - 風險模型

     - Optimizer 決策

   - 只負責：

     - 把 FinMind 原始表 → Path A 的 `price_frame` + `feature_frame`

3. **與 MockPathADataLoader 對齊**

   - `load_price_frame` 與 `load_feature_frame` 的輸出格式  

     必須與 `MockPathADataLoader` 完全相容，  

     確保同一套 Path A backtest 可以切換不同 Loader。

---

## 8. 接下來的實作路線圖（v1）

1. 建立：

   - `jgod/path_a/finmind_loader.py`

   - 定義 `FinMindClient` Protocol

   - 實作 `FinMindPathADataLoader(PathADataLoader)`

2. 建立單元測試：

   - `tests/path_a/test_finmind_loader_skeleton.py`

   - 使用 Dummy FinMind client 回傳小型 DataFrame

   - 驗證：

     - `load_price_frame` 的 MultiIndex columns 正確

     - `load_feature_frame` 的 MultiIndex index 和 feature 欄位正確

3. 未來版本：

   - 逐步加入籌碼／基本面欄位，並寫入 feature frame

   - 讓 AlphaEngine 可以吃更多真實 signals

