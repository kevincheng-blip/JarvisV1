# J-GOD Path A Engine Specification

## 📋 概述

Path A Engine 是 J-GOD 系統的**歷史回測引擎（Historical Backtest Engine）**，負責在單一時間視窗內執行完整的量化策略回測流程。Path A 是 Path B（Walk-Forward Analysis）的基礎，Path B 透過多次呼叫 Path A 來實現滾動視窗驗證。

---

## 🎯 核心角色與目的

### A. Path A Engine 的存在目的

1. **單視窗歷史回測**
   - 在指定的時間視窗內執行完整的回測流程
   - 從資料載入、因子計算、風險評估、優化、執行到績效評估
   - 提供單一視窗的完整回測結果

2. **整合多個核心模組**
   - **Data Loader**: 載入歷史價格與特徵資料
   - **Alpha Engine**: 計算 alpha 訊號
   - **Risk Model**: 建立風險模型與協方差矩陣
   - **Optimizer**: 優化投資組合權重
   - **Execution Engine**: 模擬交易執行
   - **Performance Metrics**: 計算績效指標

3. **為 Path B 提供基礎**
   - Path B 透過多次呼叫 Path A 來實現 Walk-Forward Analysis
   - 每個 window 的 train/test 階段都使用 Path A 執行

4. **支援 Basic 與 Extreme 模式**
   - Basic Mode: 標準回測流程
   - Extreme Mode: 更嚴格的風險控制與更複雜的因子計算

---

## 🔌 Interface / API 規格

### 1. PathAConfig

```python
@dataclass
class PathAConfig:
    """Path A Engine 配置"""
    
    start_date: str  # "YYYY-MM-DD"
    end_date: str    # "YYYY-MM-DD"
    universe: Sequence[str]  # 股票代碼列表
    rebalance_frequency: str = "M"  # "D", "W", "M"
    lookback_window_days: int = 252
    benchmark_symbol: Optional[str] = None
    initial_nav: float = 100.0
    transaction_cost_bps: float = 5.0
    slippage_bps: float = 0.0
    max_weight_per_symbol: float = 0.1
    min_weight_per_symbol: float = 0.0
    allow_short: bool = False
    experiment_name: str = "path_a_experiment"
    tags: Dict[str, str] = field(default_factory=dict)
```

### 2. PathABacktestResult

```python
@dataclass
class PathABacktestResult:
    """Path A 回測結果"""
    
    config: PathAConfig
    nav_series: pd.Series  # indexed by date
    return_series: pd.Series  # indexed by date
    portfolio_snapshots: List[PathAPortfolioSnapshot]
    trades: Optional[pd.DataFrame] = None
    error_events: Optional[List[object]] = None
    summary_stats: Dict[str, float] = field(default_factory=dict)
```

### 3. PathADataLoader Protocol

```python
class PathADataLoader(Protocol):
    """資料載入器介面"""
    
    def load_price_frame(self, config: PathAConfig) -> pd.DataFrame:
        """載入價格資料（OHLCV）"""
        ...
    
    def load_feature_frame(self, config: PathAConfig) -> pd.DataFrame:
        """載入或建構特徵資料"""
        ...
```

### 4. PathARunContext

```python
@dataclass
class PathARunContext:
    """Path A 執行上下文"""
    
    config: PathAConfig
    data_loader: PathADataLoader
    alpha_engine: AlphaEngine
    risk_model: MultiFactorRiskModel
    optimizer: OptimizerCore
    error_engine: ErrorLearningEngine
    error_bridge: Optional[PathAErrorBridge] = None
```

### 5. run_path_a_backtest()

```python
def run_path_a_backtest(ctx: PathARunContext) -> PathABacktestResult:
    """
    執行 Path A 回測
    
    Args:
        ctx: Path A 執行上下文
    
    Returns:
        PathABacktestResult 物件
    """
    ...
```

---

## 🏗️ 主要模組說明

### 1. Data Loader（資料載入器）

**位置**: `jgod/path_a/mock_data_loader.py`, `finmind_loader.py`, `finmind_data_loader.py`

**功能**:
- 載入歷史價格資料（OHLCV）
- 載入或建構特徵資料
- 支援 Mock 與 FinMind 兩種資料來源

**Input**:
- `PathAConfig`: 回測配置（日期範圍、universe 等）

**Output**:
- `price_frame`: 價格 DataFrame（index=date, columns=price fields）
- `feature_frame`: 特徵 DataFrame（index=MultiIndex(date, symbol)）

**關鍵方法**:
- `load_price_frame(config: PathAConfig) -> pd.DataFrame`
- `load_feature_frame(config: PathAConfig) -> pd.DataFrame`

---

### 2. Feature Engine（特徵引擎）

**位置**: `jgod/alpha_engine/`（部分功能）

**功能**:
- 從價格資料計算技術指標
- 建構因子特徵（momentum, value, quality 等）
- 為 Alpha Engine 提供輸入

**Input**:
- 價格資料
- 歷史資料（用於計算 rolling 指標）

**Output**:
- 特徵 DataFrame

**註**: 特徵計算主要整合在 Data Loader 中，或由 Alpha Engine 直接處理。

---

### 3. Alpha Engine（Alpha 訊號引擎）

**位置**: `jgod/alpha_engine/alpha_engine.py`, `alpha_engine_extreme.py`

**功能**:
- 計算各股票的 alpha 訊號
- 整合多個因子（momentum, value, quality, flow 等）
- 輸出 composite alpha（組合後的 alpha 分數）

**Input**:
- 特徵 DataFrame（MultiIndex(date, symbol) 或 symbol index）
- 可選的歷史資料

**Output**:
- Alpha 訊號（pd.Series 或 pd.DataFrame），index 為 symbol

**關鍵方法**:
- `compute_all(feature_df: pd.DataFrame) -> pd.DataFrame`
  - 返回包含 `composite_alpha` 欄位的 DataFrame

**支援模式**:
- Basic Mode: 標準因子計算
- Extreme Mode: 更複雜的因子與風險調整

---

### 4. Risk Model（風險模型）

**位置**: `jgod/risk/risk_model.py`, `risk_model_extreme.py`

**功能**:
- 計算協方差矩陣
- 提供風險預測
- 支援多因子風險模型

**Input**:
- 歷史價格資料
- Universe 列表

**Output**:
- 協方差矩陣（np.ndarray）
- 風險預測（可選）

**關鍵方法**:
- `get_covariance_matrix() -> np.ndarray`
- `fit(price_data: pd.DataFrame, universe: List[str]) -> None`

**支援模式**:
- Basic Mode: 標準協方差估計
- Extreme Mode: 更複雜的風險模型（PCA 因子等）

---

### 5. Optimizer（投資組合優化器）

**位置**: `jgod/optimizer/optimizer_core_v2.py`

**功能**:
- 根據 alpha 訊號與風險模型優化投資組合權重
- 考慮約束條件（最大權重、換手率、追蹤誤差等）
- 輸出最優權重配置

**Input**:
- `expected_returns`: pd.Series（alpha 訊號，index=symbol）
- `risk_model`: MultiFactorRiskModel 實例
- `factor_exposure`: Optional[pd.DataFrame]（因子暴露）
- `benchmark_weights`: Optional[pd.Series]（基準權重）
- `sector_map`: Optional[Dict[str, str]]（產業分類）

**Output**:
- `OptimizerResult`: 包含權重、狀態、目標值等

**關鍵方法**:
- `optimize(expected_returns, risk_model, ...) -> OptimizerResult`

**約束條件**:
- 最大權重限制
- 換手率限制
- 追蹤誤差限制（若有基準）

---

### 6. Execution Engine（交易執行引擎）

**位置**: `jgod/execution/execution_engine.py`, `execution_engine_extreme.py`

**功能**:
- 模擬交易執行
- 計算交易成本（手續費、滑價）
- 記錄交易歷史

**Input**:
- 目標權重
- 當前權重
- 價格資料

**Output**:
- 執行後的實際權重
- 交易成本
- 交易記錄

**關鍵方法**:
- `execute_rebalance(current_weights, target_weights, prices) -> ExecutionResult`

**支援模式**:
- Basic Mode: 簡單的執行成本模型
- Extreme Mode: 更複雜的滑價模型

---

### 7. Backtest Runner（回測執行器）

**位置**: `jgod/path_a/path_a_backtest.py`

**功能**:
- 執行完整的回測循環
- 處理再平衡邏輯
- 追蹤 NAV 與績效

**流程**:
1. 載入資料（price_frame, feature_frame）
2. 建立再平衡日期表
3. 主回測循環：
   - 每日 mark-to-market
   - 再平衡日：計算 alpha → 風險模型 → 優化 → 執行
   - 更新 NAV 與權重
4. 建立結果物件

**關鍵函數**:
- `run_path_a_backtest(ctx: PathARunContext) -> PathABacktestResult`

---

### 8. Reporter（報告生成器）

**位置**: `jgod/performance/performance_metrics.py`（部分）

**功能**:
- 計算績效指標（Sharpe, Max Drawdown, Total Return 等）
- 生成回測報告

**目前狀態**: ⚠️ **部分實作**
- 有 `performance_metrics.py` 計算指標
- 缺少統一的報告生成器（Markdown/HTML 輸出）

**待補強**:
- 統一的報告生成器
- 視覺化圖表生成
- 完整的績效分析報告

---

## 🔗 Path A 與 Path B/C/D 的關係

### Path A → Path B

Path B 透過多次呼叫 Path A 來實現 Walk-Forward Analysis：

```
Path B Window 1 (Train: 2020-2021, Test: 2022)
  └─> 呼叫 Path A (Test: 2022) → PathABacktestResult
  
Path B Window 2 (Train: 2020-2022, Test: 2023)
  └─> 呼叫 Path A (Test: 2023) → PathABacktestResult
  
Path B Window N ...
  └─> 呼叫 Path A → PathABacktestResult
```

Path B 收集所有 window 的 `PathABacktestResult`，並進行：
- 彙總統計（平均 Sharpe、MaxDD 等）
- Governance 評估
- 穩定性分析

### Path A → Path C

Path C 透過呼叫 Path B 間接使用 Path A。Path C 是場景驗證實驗，每個 scenario 都執行完整的 Path B（包含多次 Path A 呼叫）。

### Path A → Path D

Path D（RL Engine）在訓練過程中，每個 step 都會執行 Path B（間接使用 Path A）來評估當前治理參數的效果。

---

## 📊 資料流圖

```
┌─────────────────┐
│  Data Loader    │
│  (Mock/FinMind) │
└────────┬────────┘
         │
         ├─> price_frame (OHLCV)
         └─> feature_frame (特徵)
                │
                ▼
┌─────────────────┐
│  Alpha Engine   │
│  (計算 alpha)   │
└────────┬────────┘
         │
         ├─> composite_alpha (Series)
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Risk Model     │     │   Optimizer     │
│  (協方差矩陣)   │────>│  (優化權重)     │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ├─> optimized_weights
                                 │
                                 ▼
┌─────────────────┐
│ Execution Engine│
│  (執行交易)     │
└────────┬────────┘
         │
         ├─> 更新 NAV
         ├─> 記錄交易
         └─> 更新權重
                │
                ▼
        ┌───────────────┐
        │  Backtest     │
        │  Runner       │
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │  Performance  │
        │  Metrics      │
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │  PathABacktest│
        │  Result       │
        └───────────────┘
```

---

## 🔧 實作細節

### 再平衡邏輯

Path A 支援多種再平衡頻率：
- **"D"**: 每日再平衡
- **"W"**: 每週再平衡（最後一個交易日）
- **"M"**: 每月再平衡（最後一個交易日）

### 交易成本

Path A 在再平衡時計算交易成本：
- `transaction_cost_bps`: 每邊手續費（basis points）
- `slippage_bps`: 滑價成本（basis points）
- 成本 = turnover * (transaction_cost_bps / 1e4)

### Error Learning Integration

Path A 支援 Error Learning Engine 整合：
- 透過 `PathAErrorBridge` 將回測結果轉換為 ErrorEvent
- 用於策略自我學習與改進

---

## 📝 檔案結構

```
jgod/path_a/
├── __init__.py
├── path_a_schema.py          # 資料結構定義
├── path_a_config.py          # 配置相關
├── path_a_backtest.py        # 主回測執行器
├── path_a_error_bridge.py    # Error Learning 橋接
├── mock_data_loader.py       # Mock 資料載入器
├── mock_data_loader_extreme.py  # Mock Extreme 載入器
├── finmind_loader.py         # FinMind 載入器
├── finmind_data_loader.py    # FinMind 資料載入器（完整版）
└── finmind_data_loader_extreme.py  # FinMind Extreme 載入器
```

---

## 🧪 測試策略

### 單元測試

- `test_path_a_schema.py`: 測試資料結構
- `test_finmind_loader_skeleton.py`: 測試資料載入器（skeleton）

### 整合測試

- `test_path_a_backtest_skeleton.py`: 測試完整回測流程（skeleton）
- `test_path_a_integration_smoke.py`: **待補齊** - 最小可運作的整合測試
- `test_path_a_extreme_mode_smoke.py`: **待補齊** - Extreme Mode 整合測試

---

## 📚 參考文件

- `docs/J-GOD_PATH_A_STANDARD_v1.md`: Path A 標準文件（非技術版本）
- `jgod/path_a/path_a_backtest.py`: 主回測執行器實作
- `jgod/path_b/path_b_engine.py`: Path B 如何使用 Path A

---

## ⚠️ 注意事項

1. **報告生成**: Path A 目前缺少統一的報告生成器，只有 metrics 計算。建議未來補齊。

2. **Error Bridge**: Error Bridge 是可選的，用於整合 Error Learning Engine。

3. **Extreme Mode**: Extreme Mode 使用更複雜的 Data Loader、Alpha Engine、Risk Model 和 Execution Engine。

4. **與 Path B 的關係**: Path A 專注於單一視窗回測，Path B 負責 Walk-Forward 分析與 Governance 評估。

