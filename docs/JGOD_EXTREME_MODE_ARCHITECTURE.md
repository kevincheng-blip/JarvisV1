# J-GOD EXTREME MODE Architecture

## 📋 概述

J-GOD EXTREME MODE 是針對專業量化基金需求的進階版本，提供更高品質的資料處理、Alpha 計算、風險建模與執行模擬。

---

## 🏗️ 整體架構

### 資料流圖

```
┌─────────────────────────────────────────────────────────────┐
│                     EXTREME MODE Pipeline                    │
└─────────────────────────────────────────────────────────────┘

1. Data Loading Phase
   ┌──────────────────┐         ┌──────────────────┐
   │ MockLoader       │         │ FinMindLoader    │
   │ Extreme          │         │ Extreme          │
   └────────┬─────────┘         └────────┬─────────┘
            │                            │
            └────────────┬───────────────┘
                         │
              Enhanced Data Integrity:
              - Missing date filling
              - Outlier removal (Z-score > 6)
              - Gap removal (±15%)
              - Risk factor construction
              ↓
   ┌──────────────────────────────────────┐
   │         Price Frame                  │
   │   (date × (symbol, field))          │
   └──────────────────┬───────────────────┘
                      │
   ┌──────────────────────────────────────┐
   │        Feature Frame                 │
   │   ((date, symbol) × features)       │
   │   + Risk Factors (market/size/vol)  │
   └──────────────────┬───────────────────┘

2. Alpha Generation Phase
                      │
                      ↓
   ┌──────────────────────────────────────┐
   │    AlphaEngine Extreme               │
   │   - Cross-sectional ranking          │
   │   - Regime detection                 │
   │   - Multi-factor alpha               │
   └──────────────────┬───────────────────┘
                      │
                      ↓
              composite_alpha
                      │

3. Risk Modeling Phase
                      │
                      ↓
   ┌──────────────────────────────────────┐
   │  RiskModel Extreme                   │
   │   - Ledoit-Wolf shrinkage            │
   │   - PCA factor extraction            │
   │   - Factor model: cov = B F B^T + S  │
   └──────────────────┬───────────────────┘
                      │
                      ↓
              Covariance Matrix
              Factor Exposures
                      │

4. Optimization Phase
                      │
                      ↓
   ┌──────────────────────────────────────┐
   │    OptimizerCore                     │
   │   (uses existing optimizer)          │
   └──────────────────┬───────────────────┘
                      │
                      ↓
              Optimal Weights
                      │

5. Execution Phase
                      │
                      ↓
   ┌──────────────────────────────────────┐
   │  ExecutionEngine Extreme             │
   │   - Damped execution                 │
   │   - Volume-based slippage            │
   │   - Market impact cost               │
   └──────────────────┬───────────────────┘
                      │
                      ↓
              Executed Trades
              (with detailed statistics)
                      │

6. Performance & Diagnosis Phase
                      │
                      ↓
   ┌──────────────────────────────────────┐
   │  PerformanceEngine                   │
   │  DiagnosisEngine                     │
   │  (uses existing engines)             │
   └──────────────────────────────────────┘
```

---

## 🔧 模組關係

### 核心 Extreme 模組

1. **Mock Loader Extreme** (`jgod/path_a/mock_data_loader_extreme.py`)
   - 輸入：`PathAConfig`
   - 輸出：`price_frame`, `feature_frame`
   - 特色：OU process、Gamma 成交量、Price shocks

2. **FinMind Loader Extreme** (`jgod/path_a/finmind_data_loader_extreme.py`)
   - 輸入：`PathAConfig`
   - 輸出：`price_frame`, `feature_frame`（含 risk factors）
   - 特色：資料清洗、自動補資料、Parquet cache

3. **AlphaEngine Extreme** (`jgod/alpha_engine/alpha_engine_extreme.py`)
   - 輸入：`feature_frame`（cross-sectional 格式）
   - 輸出：`composite_alpha`
   - 特色：橫截面排序、Regime detection、穩定性約束

4. **Risk Model Extreme** (`jgod/risk/risk_model_extreme.py`)
   - 輸入：`price_frame`（returns）
   - 輸出：`covariance_matrix`, `factor_exposures`, `factor_cov`
   - 特色：Ledoit-Wolf shrinkage、PCA 因子提取

5. **Execution Engine Extreme** (`jgod/execution/execution_engine_extreme.py`)
   - 輸入：`target_weights`, `prices`, `volumes`
   - 輸出：`fills`, `execution_statistics`
   - 特色：Damped execution、Volume-based slippage、Market impact

---

## 📊 資料格式約定

### Price Frame
```
index: pd.DatetimeIndex (business days)
columns: pd.MultiIndex.from_tuples([
    (symbol, "open"),
    (symbol, "high"),
    (symbol, "low"),
    (symbol, "close"),
    (symbol, "volume"),
], names=["symbol", "field"])
```

### Feature Frame (Extreme)
```
index: pd.MultiIndex.from_product([
    dates,      # DatetimeIndex
    symbols     # List[str]
], names=["date", "symbol"])

columns: [
    "daily_return_1d",
    "rolling_vol_5d", "rolling_vol_20d",
    "rolling_momentum_3d", "rolling_momentum_5d", "rolling_momentum_10d",
    "ATR_14",
    "rolling_skew", "rolling_kurtosis",
    "VWAP_14",
    "turnover_rate",
    "close", "volume", "open", "high", "low",  # Price fields
]
```

---

## 🎯 使用情境

### 何時使用 Basic 模式

- **開發階段**：快速原型驗證
- **簡單測試**：基本功能驗證
- **教學/示範**：理解系統運作

### 何時使用 Extreme 模式

- **生產環境**：實際資金運作
- **專業研究**：需要高品質資料與模型
- **風險敏感**：需要準確的風險估計
- **大規模回測**：需要穩定的長期回測

---

## 🔄 模組間整合

### Path A Backtest 整合

```python
# 1. Load data
loader = MockPathADataLoaderExtreme()  # or FinMindPathADataLoaderExtreme
price_frame = loader.load_price_frame(config)
feature_frame = loader.load_feature_frame(config)

# 2. Compute alpha
alpha_engine = AlphaEngineExtreme()
alpha_input = _prepare_alpha_input(feature_frame, price_frame, date, universe)
alpha_result = alpha_engine.compute_all(alpha_input)
composite_alpha = alpha_result['composite_alpha']

# 3. Build risk model
risk_model = MultiFactorRiskModelExtreme()
returns_df = extract_returns(price_frame)
risk_model.fit_from_returns(returns_df)
cov_matrix = risk_model.get_covariance_matrix(symbols)

# 4. Optimize
optimizer = OptimizerCore(...)
optimal_weights = optimizer.optimize(...)

# 5. Execute
execution_engine = ExecutionEngineExtreme()
fills, stats = execution_engine.rebalance_to_weights(
    target_weights=optimal_weights,
    current_weights=current_weights,
    prices=prices,
    volumes=volumes,
    portfolio_value=nav,
)
```

---

## 🔐 設計原則

1. **向後相容**：Extreme 模組不破壞現有 Basic 模組
2. **API 一致**：Extreme 模組盡量與 Basic 模組 API 一致
3. **可選升級**：可以逐步將 Basic 模組替換為 Extreme 模組
4. **模組化設計**：每個 Extreme 模組可以獨立使用

---

## 📚 相關文件

- `docs/JGOD_EXTREME_MODE_STANDARD_v1.md` - EXTREME MODE 標準規範
- `docs/JGOD_EXTREME_MODE_EDITOR_INSTRUCTIONS.md` - 實作指引
- `docs/JGOD_FINMIND_LOADER_STANDARD_v1.md` - FinMind Loader 標準

---

## 🔮 未來擴充

### v2 規劃

1. **更進階的資料處理**
   - 權息調整
   - 多資料源整合
   - 即時資料串流

2. **更複雜的 Alpha 模型**
   - 深度學習因子
   - 非線性因子組合
   - 動態權重調整

3. **更精確的風險模型**
   - 多層級因子模型
   - 尾部風險估計
   - 流動性風險

4. **更真實的執行模擬**
   - 限價單模型
   - 時間加權平均價格 (TWAP)
   - 成交量加權平均價格 (VWAP)

