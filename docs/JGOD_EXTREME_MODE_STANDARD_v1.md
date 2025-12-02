# J-GOD EXTREME MODE Standard v1

## 📋 概述

本文檔定義 J-GOD EXTREME MODE 的標準規範，包含所有 Extreme 模組的介面、資料格式、與使用規範。

---

## 🎯 EXTREME MODE 目標

EXTREME MODE 旨在提供專業量化基金等級的功能：

1. **更高品質的資料**：完整的資料清洗、異常值處理、缺漏填補
2. **更精確的 Alpha**：橫截面排序、Regime detection、多因子組合
3. **更穩定的風險估計**：Ledoit-Wolf shrinkage、PCA 因子提取
4. **更真實的執行模擬**：Volume-based slippage、Market impact、Damped execution

---

## 📐 資料格式規範

### Price Frame（統一格式）

所有 Extreme Loaders 必須回傳統一格式：

```python
pd.DataFrame(
    index=pd.DatetimeIndex,  # Business days
    columns=pd.MultiIndex.from_tuples([
        (symbol, "open"),
        (symbol, "high"),
        (symbol, "low"),
        (symbol, "close"),
        (symbol, "volume"),
    ], names=["symbol", "field"])
)
```

**價格關係要求**：
- `high >= max(open, close)`
- `low <= min(open, close)`
- `high - low >= min_price_gap`
- 所有價格 > 0

### Feature Frame（Extreme 格式）

```python
pd.DataFrame(
    index=pd.MultiIndex.from_product([
        dates,      # DatetimeIndex
        symbols     # List[str]
    ], names=["date", "symbol"]),
    columns=[
        # Returns
        "daily_return_1d",
        # Volatility
        "rolling_vol_5d", "rolling_vol_20d",
        # Momentum
        "rolling_momentum_3d", "rolling_momentum_5d", "rolling_momentum_10d",
        # Market microstructure
        "ATR_14", "VWAP_14", "turnover_rate",
        # Higher moments
        "rolling_skew", "rolling_kurtosis",
        # Price fields (for AlphaEngine)
        "close", "volume", "open", "high", "low",
    ]
)
```

---

## 🔧 API 規範

### Mock Loader Extreme

```python
from jgod.path_a.mock_data_loader_extreme import (
    MockPathADataLoaderExtreme,
    MockConfigExtreme,
    VolatilityRegime,
)

loader = MockPathADataLoaderExtreme(
    config=MockConfigExtreme(
        seed=42,
        volatility_regime=VolatilityRegime.MID,
        allow_shocks=True,
        shock_probability=0.02,
    )
)

price_frame = loader.load_price_frame(config)
feature_frame = loader.load_feature_frame(config)
```

### FinMind Loader Extreme

```python
from jgod.path_a.finmind_data_loader_extreme import (
    FinMindPathADataLoaderExtreme,
    FinMindLoaderConfigExtreme,
)

loader = FinMindPathADataLoaderExtreme(
    config=FinMindLoaderConfigExtreme(
        cache_enabled=True,
        use_parquet_cache=True,
        fallback_to_mock_extreme=True,
        zscore_threshold=6.0,
        gap_threshold=0.15,
    )
)

price_frame = loader.load_price_frame(config)
feature_frame = loader.load_feature_frame(config)

# Access risk factors
risk_factors = feature_frame.risk_factors  # DataFrame
```

### AlphaEngine Extreme

```python
from jgod.alpha_engine.alpha_engine_extreme import (
    AlphaEngineExtreme,
    AlphaEngineExtremeConfig,
)

engine = AlphaEngineExtreme(
    config=AlphaEngineExtremeConfig(
        momentum_weight=0.30,
        volatility_weight=0.20,
        # ...
    )
)

# Cross-sectional mode (recommended)
alpha_result = engine.compute_all(alpha_input)  # index=symbol
composite_alpha = alpha_result['composite_alpha']
```

### Risk Model Extreme

```python
from jgod.risk.risk_model_extreme import (
    MultiFactorRiskModelExtreme,
    RiskModelExtremeConfig,
)

risk_model = MultiFactorRiskModelExtreme(
    config=RiskModelExtremeConfig(
        max_factor_count=10,
        factor_explained_variance=0.85,
    )
)

# Fit from returns
returns_df = extract_returns(price_frame)  # date × symbol
risk_model.fit_from_returns(returns_df)

# Get covariance matrix
cov_matrix = risk_model.get_covariance_matrix(symbols)

# Get factor exposures
factor_exposures = risk_model.get_factor_exposures(symbols)
```

### Execution Engine Extreme

```python
from jgod.execution.execution_engine_extreme import (
    ExecutionEngineExtreme,
    ExecutionEngineExtremeConfig,
)

execution_engine = ExecutionEngineExtreme(
    config=ExecutionEngineExtremeConfig(
        damp_threshold=0.1,
        slippage_k=0.001,
        slippage_alpha=0.5,
    )
)

fills, stats = execution_engine.rebalance_to_weights(
    target_weights=target_weights,
    current_weights=current_weights,
    prices=prices,
    volumes=volumes,
    portfolio_value=nav,
)

# Access statistics
slippage = stats.realized_slippage
impact = stats.market_impact_cost
fill_ratio = stats.fill_ratio
```

---

## ✅ 驗證要求

所有 Extreme 模組必須通過：

1. **語法檢查**：`python3 -m py_compile`
2. **回歸測試**：`pytest tests/regression_extreme -q`
3. **資料格式檢查**：符合上述格式規範
4. **API 一致性**：與 Basic 版本 API 相容（盡可能）

---

## 📚 相關文件

- `docs/JGOD_EXTREME_MODE_ARCHITECTURE.md` - 架構說明
- `docs/JGOD_EXTREME_MODE_EDITOR_INSTRUCTIONS.md` - 實作指引

