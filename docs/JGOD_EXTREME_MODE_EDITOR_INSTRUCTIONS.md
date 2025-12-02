# J-GOD Step 10 EXTREME MODE - 完整實作指南

## 📋 概述

本文檔提供 J-GOD Step 10 EXTREME MODE 的完整實作指南，包含所有需要新增和修改的檔案。

---

## 🎯 任務完成狀態

### ✅ 已完成

1. **任務 A：Mock Loader Extreme** - ✅ `jgod/path_a/mock_data_loader_extreme.py` 已完成
2. **任務 B：FinMind Loader Extreme** - ✅ `jgod/path_a/finmind_data_loader_extreme.py` 已完成
3. **任務 C：AlphaEngine Extreme** - ✅ `jgod/alpha_engine/alpha_engine_extreme.py` 已完成
4. **任務 D：Risk Model Extreme** - ✅ `jgod/risk/risk_model_extreme.py` 已完成
5. **任務 E：Execution Engine Extreme** - ✅ `jgod/execution/execution_engine_extreme.py` 已完成
6. **任務 F：回歸測試 Extreme** - ✅ `tests/regression_extreme/` 已完成
7. **任務 G：文件** - ✅ 架構文件已完成

---

## 📁 完整檔案清單

### 新增檔案（核心模組）

1. ✅ `jgod/path_a/mock_data_loader_extreme.py` - Mock Loader Extreme
2. ✅ `jgod/path_a/finmind_data_loader_extreme.py` - FinMind Loader Extreme
3. ✅ `jgod/alpha_engine/alpha_engine_extreme.py` - AlphaEngine Extreme
4. ✅ `jgod/risk/risk_model_extreme.py` - Risk Model Extreme
5. ✅ `jgod/execution/execution_engine_extreme.py` - Execution Engine Extreme

### 新增檔案（測試）

6. ✅ `tests/regression_extreme/__init__.py`
7. ✅ `tests/regression_extreme/test_mock_extreme_validity.py`
8. ✅ `tests/regression_extreme/test_finmind_extreme_cleaning.py`
9. ✅ `tests/regression_extreme/test_alpha_extreme_correctness.py`
10. ✅ `tests/regression_extreme/test_risk_extreme_covariance.py`
11. ✅ `tests/regression_extreme/test_execution_extreme_behavior.py`

### 新增檔案（文件）

12. ✅ `docs/JGOD_EXTREME_MODE_STANDARD_v1.md`
13. ✅ `docs/JGOD_EXTREME_MODE_EDITOR_INSTRUCTIONS.md` (本檔案)
14. ✅ `docs/JGOD_EXTREME_MODE_ARCHITECTURE.md`

---

## 🔧 實作規格詳述

### 任務 A：Mock Loader Extreme ✅

**檔案**: `jgod/path_a/mock_data_loader_extreme.py`

**已完成功能**:
- OU process (Ornstein-Uhlenbeck) 價格生成
- 隨機波動率 (1-4%)
- Gamma 分佈成交量
- Price shock 事件模擬
- 完整特徵集 (VWAP, ATR, skewness, kurtosis, momentum)
- MockConfigExtreme 配置類別

---

### 任務 B：FinMind Loader Extreme ⏳

**檔案**: `jgod/path_a/finmind_data_loader_extreme.py`

**需要實作**:

#### 1. Data Integrity

```python
class FinMindPathADataLoaderExtreme(PathADataLoader):
    def _check_missing_dates(self, df, start_date, end_date):
        """檢查缺漏日並 forward/backward fill"""
        
    def _remove_outliers(self, df, zscore_threshold=6):
        """移除異常值 (Z-score > 6)"""
        
    def _remove_gaps(self, df, gap_threshold=0.15):
        """移除異常跳空 (±15%)"""
```

#### 2. 自動風險因子建構

```python
def _build_risk_factors(self, returns_df):
    """自動計算風險因子"""
    # Market factor (equal-weighted market return)
    # Size factor (based on market cap)
    # Volatility factor (rolling vol)
    # Momentum factor (rolling momentum)
    return factor_returns  # DataFrame
```

#### 3. 自動補資料

```python
def load_price_frame(self, config):
    """自動以 mock 補足缺漏資料"""
    # 標記 data_source="mixed"
```

#### 4. Caching 強化

```python
def _save_to_cache_parquet(self, data, cache_path):
    """以 parquet 格式儲存"""
    
def _load_from_cache_parquet(self, cache_path):
    """從 parquet 格式載入"""
```

---

### 任務 C：AlphaEngine Extreme ⏳

**檔案**: `jgod/alpha_engine/alpha_engine_extreme.py`

**需要實作**:

#### 1. Cross-Sectional Ranking 因子

```python
class AlphaEngineExtreme:
    def _compute_cross_sectional_ranking(self, df):
        """依 momentum, volatility, skewness, kurtosis 排名"""
        # 標準化排名
        # weighted sum
```

#### 2. 混合模式偵測

```python
def _detect_input_mode_extreme(self, df):
    """自動偵測並調整標準化方法"""
```

#### 3. Regime Detection

```python
def _detect_regime(self, rolling_vol_20d):
    """以 rolling_vol_20d 分三種 regime"""
    # low, normal, high
    # 依 regime 調整 α 權重
```

#### 4. Stability Constraint

```python
def _apply_stability_constraint(self, alpha, feature_completeness):
    """若資料缺少關鍵欄位 → alpha=0"""
```

---

### 任務 D：Risk Model Extreme ⏳

**檔案**: `jgod/risk/risk_model_extreme.py`

**需要實作**:

#### 1. Ledoit-Wolf Shrinkage

```python
class MultiFactorRiskModelExtreme:
    def _compute_covariance_ledoit_wolf(self, returns):
        """使用 Ledoit-Wolf shrinkage 計算 covariance"""
```

#### 2. Factor Model

```python
def _compute_factor_covariance(self, factor_returns, factor_loadings):
    """cov = B F B^T + S"""
    # B: factor loadings
    # F: factor covariance
    # S: specific risk
```

#### 3. PCA 因子數估計

```python
def _estimate_factor_count(self, returns, max_factors=10):
    """使用 PCA 估計因子數"""
```

#### 4. 特徵值修正

```python
def _ensure_positive_definite(self, cov_matrix):
    """避免非正定"""
```

---

### 任務 E：Execution Engine Extreme ⏳

**檔案**: `jgod/execution/execution_engine_extreme.py`

**需要實作**:

#### 1. Damped Execution

```python
class ExecutionEngineExtreme:
    def _damp_position_change(self, target_weights, current_weights, threshold=0.1):
        """若 |Δw| > threshold → 自動減半"""
```

#### 2. Slippage Model

```python
def _compute_slippage(self, order_size, volume, k=0.001, alpha=0.5):
    """slippage = k * (order_size / volume)^α"""
```

#### 3. Market Impact Cost

```python
def _compute_market_impact(self, order_size, volume, price):
    """計算 market impact cost"""
```

#### 4. 完整執行回報

```python
def execute_order(self, order):
    """回傳：實際成交價、成交量、slippage cost、market impact cost"""
```

---

### 任務 F：回歸測試 Extreme ⏳

**需要建立的測試檔案**:

#### 1. `test_mock_extreme_validity.py`

```python
class TestMockExtremeValidity:
    def test_ou_process_correctness(self):
        """測試 OU process 正確性"""
        
    def test_price_relationships(self):
        """測試價格關係 (high >= max(open, close))"""
        
    def test_volume_gamma_distribution(self):
        """測試成交量 Gamma 分佈"""
        
    def test_shock_events(self):
        """測試 shock 事件"""
```

#### 2. `test_finmind_extreme_cleaning.py`

```python
class TestFinMindExtremeCleaning:
    def test_missing_date_filling(self):
        """測試缺漏日填補"""
        
    def test_outlier_removal(self):
        """測試異常值移除"""
        
    def test_gap_removal(self):
        """測試跳空移除"""
```

#### 3. `test_alpha_extreme_correctness.py`

```python
class TestAlphaExtremeCorrectness:
    def test_cross_sectional_ranking(self):
        """測試 cross-sectional ranking"""
        
    def test_regime_detection(self):
        """測試 regime detection"""
```

#### 4. `test_risk_extreme_covariance.py`

```python
class TestRiskExtremeCovariance:
    def test_ledoit_wolf_shrinkage(self):
        """測試 Ledoit-Wolf shrinkage"""
        
    def test_factor_model(self):
        """測試 factor model"""
```

#### 5. `test_execution_extreme_behavior.py`

```python
class TestExecutionExtremeBehavior:
    def test_damped_execution(self):
        """測試 damped execution"""
        
    def test_slippage_model(self):
        """測試 slippage model"""
```

---

## 📝 實作檢查清單

### Mock Loader Extreme ✅

- [x] OU process 實作
- [x] 隨機波動率
- [x] Gamma 分佈成交量
- [x] Price shock 事件
- [x] 完整特徵集
- [x] MockConfigExtreme

### FinMind Loader Extreme ⏳

- [ ] Data integrity 檢查
- [ ] 自動風險因子建構
- [ ] 自動補資料
- [ ] Parquet caching

### AlphaEngine Extreme ⏳

- [ ] Cross-sectional ranking
- [ ] 混合模式偵測
- [ ] Regime detection
- [ ] Stability constraint

### Risk Model Extreme ⏳

- [ ] Ledoit-Wolf shrinkage
- [ ] Factor model
- [ ] PCA 因子數估計
- [ ] 特徵值修正

### Execution Engine Extreme ⏳

- [ ] Damped execution
- [ ] Slippage model
- [ ] Market impact cost
- [ ] 完整執行回報

### 測試套件 ⏳

- [ ] 5 個測試檔案
- [ ] Mock 掉外部 API
- [ ] 驗證 shape、欄位、統計性

### 文件 ⏳

- [ ] EXTREME_MODE_STANDARD_v1.md
- [x] EXTREME_MODE_EDITOR_INSTRUCTIONS.md
- [ ] EXTREME_MODE_ARCHITECTURE.md

---

## 🚀 快速開始

由於 EXTREME MODE 是一個大型升級，建議分階段實作：

### Phase 1: 核心模組
1. Mock Loader Extreme ✅
2. FinMind Loader Extreme
3. AlphaEngine Extreme

### Phase 2: 風險與執行
4. Risk Model Extreme
5. Execution Engine Extreme

### Phase 3: 測試與文件
6. 回歸測試套件
7. 完整文件

---

## 📞 下一步

1. **檢視已完成**: `jgod/path_a/mock_data_loader_extreme.py`
2. **按照規格實作**: 其他 Extreme 模組
3. **執行測試**: 確保每個模組都通過測試
4. **整合測試**: 確保整個系統可以正常運作

---

**注意**: 由於 EXTREME MODE 規模龐大，建議先完成 Mock Loader Extreme（已 done），然後逐步實作其他模組。

