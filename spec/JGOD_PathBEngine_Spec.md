# J-GOD Path B Engine Specification

## 📋 概述

Path B Engine 是 J-GOD 系統中用於執行 **In-Sample / Out-of-Sample 測試**與 **Walk-Forward Analysis** 的核心引擎。其目的是驗證策略在未來世界能否存活，並提供策略穩定性的嚴格評估。

---

## 🎯 核心角色與目的

### A. Path B Engine 的存在目的

1. **執行 In-Sample / Out-of-Sample 測試**
   - 將資料分為訓練集（In-Sample）與測試集（Out-of-Sample）
   - 在訓練集上優化策略參數
   - 在測試集上驗證策略表現
   - 避免資料窺探（data snooping）偏差

2. **執行 Walk-Forward Analysis**
   - 採用滾動視窗方式進行多次訓練/測試
   - 每個 window 包含獨立的 train 與 test 階段
   - 收集所有 window 的績效統計，評估策略穩定性

3. **支援多策略、多因子組合**
   - 可同時測試多組 alpha engine 配置
   - 比較不同策略組合在不同市場環境下的表現
   - 支援因子歸因分析

4. **自動收集每個 window 的績效、風險、TE、因子歸因**
   - Sharpe Ratio、Maximum Drawdown、Turnover Rate
   - Tracking Error、Information Ratio
   - Factor Attribution（各因子貢獻度）
   - Alpha Stability Metrics

5. **支援 Governance Rule Simulation**
   - **Alpha Sunset**: 當 alpha 衰減時自動停用
   - **Regime Switch**: 市場環境變化時調整策略
   - **Kill Switch**: 觸發風險閾值時立即停止
   - 模擬這些規則對策略表現的影響

---

## 🔌 Interface / API 規格

### 1. PathBConfig

```python
@dataclass
class PathBConfig:
    """Path B Engine 配置"""
    
    # Window 設定
    train_start: str  # "YYYY-MM-DD"
    train_end: str    # "YYYY-MM-DD"
    test_start: str   # "YYYY-MM-DD"
    test_end: str     # "YYYY-MM-DD"
    
    # Walk-Forward 參數
    walkforward_window: str  # 例如 "6m" (6 months), "12m"
    walkforward_step: str    # 例如 "1m" (1 month), "3m"
    
    # 基本設定
    universe: Sequence[str]
    rebalance_frequency: str  # "D", "W", "M"
    
    # 多策略配置
    alpha_config_set: List[Dict[str, Any]]  # 多組 alpha engine 配置
    
    # Governance Rules
    governance_rules: Optional[Dict[str, Any]] = None
    # 例如：
    # {
    #     "alpha_sunset": {"threshold": 0.5, "lookback": 60},
    #     "kill_switch": {"max_drawdown": -0.20, "sharpe_threshold": 0.0},
    #     "regime_manager": {"enabled": True}
    # }
    
    # 其他設定
    data_source: str = "mock"  # "mock", "finmind"
    mode: str = "basic"  # "basic", "extreme"
    initial_nav: float = 100.0
    transaction_cost_bps: float = 5.0
    slippage_bps: float = 0.0
```

### 2. PathBWindowResult

```python
@dataclass
class PathBWindowResult:
    """單一 Window 的測試結果"""
    
    window_id: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    
    # Train 階段結果
    train_result: Optional[PathABacktestResult] = None
    
    # Test 階段結果
    test_result: PathABacktestResult
    
    # Governance Rule 觸發紀錄
    governance_events: List[Dict[str, Any]] = field(default_factory=list)
    # 例如：
    # [
    #     {"rule": "alpha_sunset", "triggered": True, "date": "2024-03-15"},
    #     {"rule": "kill_switch", "triggered": False}
    # ]
    
    # 績效統計（Test 階段）
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    turnover_rate: float
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None
    
    # 因子歸因
    factor_attribution: Optional[Dict[str, float]] = None
```

### 3. PathBRunResult

```python
@dataclass
class PathBRunResult:
    """完整的 Path B 執行結果"""
    
    config: PathBConfig
    
    # 所有 Window 結果
    window_results: List[PathBWindowResult]
    
    # 彙總統計
    summary: Dict[str, Any]
    # 包含：
    # - 所有 window 的平均 Sharpe
    # - 所有 window 的平均 Max Drawdown
    # - Window 間一致性（Sharpe 標準差）
    # - Alpha Stability Score
    
    # Governance 分析
    governance_analysis: Dict[str, Any]
    # 包含：
    # - 每個 rule 的觸發次數
    # - 觸發時的市場環境特徵
    
    # 輸出檔案路徑
    output_files: List[str] = field(default_factory=list)
```

### 4. PathBEngine

```python
class PathBEngine:
    """Path B Engine 主類別"""
    
    def __init__(
        self,
        data_loader: Optional[PathADataLoader] = None,
        alpha_engine_factory: Optional[Callable] = None,
        risk_model_factory: Optional[Callable] = None,
        optimizer_factory: Optional[Callable] = None,
        execution_engine_factory: Optional[Callable] = None,
    ):
        """初始化 Path B Engine"""
        pass
    
    def run(self, config: PathBConfig) -> PathBRunResult:
        """
        執行完整的 Path B 分析
        
        Returns:
            PathBRunResult 物件
        """
        pass
    
    def _generate_windows(
        self,
        config: PathBConfig
    ) -> List[Tuple[str, str, str, str]]:
        """
        根據 walkforward 參數生成所有 window
        
        Returns:
            List of (train_start, train_end, test_start, test_end) tuples
        """
        pass
    
    def _run_single_window(
        self,
        window_id: int,
        train_start: str,
        train_end: str,
        test_start: str,
        test_end: str,
        config: PathBConfig
    ) -> PathBWindowResult:
        """
        執行單一 window 的訓練與測試
        
        Returns:
            PathBWindowResult 物件
        """
        pass
    
    def _apply_governance_rules(
        self,
        window_result: PathBWindowResult,
        config: PathBConfig
    ) -> List[Dict[str, Any]]:
        """
        套用 Governance Rules 並記錄觸發事件
        
        Returns:
            List of governance events
        """
        pass
```

---

## ⚙️ 設定參數詳述

### Window 切割參數

- **train_start, train_end**: 第一個 window 的訓練集日期範圍
- **test_start, test_end**: 第一個 window 的測試集日期範圍
- **walkforward_window**: 每個 window 的總長度（例如 "6m" = 6 個月）
- **walkforward_step**: Window 的滾動步長（例如 "1m" = 每個月移動一次）

### 多策略配置

- **alpha_config_set**: 
  ```python
  [
      {"name": "strategy_1", "alpha_config": {...}},
      {"name": "strategy_2", "alpha_config": {...}},
  ]
  ```

### Governance Rules

- **alpha_sunset**: 
  - `threshold`: Alpha 衰減閾值（例如 0.5 = 50% 衰減）
  - `lookback`: 回看期（例如 60 天）
  
- **kill_switch**:
  - `max_drawdown`: 最大回落閾值（例如 -0.20）
  - `sharpe_threshold`: Sharpe 下限（例如 0.0）
  
- **regime_manager**:
  - `enabled`: 是否啟用 regime 檢測
  - `regime_factors`: Regime 因子列表

---

## 🔄 五大流程

### Step 1: Window 切割

根據 `walkforward_window` 與 `walkforward_step` 參數，將整個時間範圍切割成多個不重疊或部分重疊的 window。

每個 window 包含：
- Train 階段（In-Sample）
- Test 階段（Out-of-Sample）

### Step 2: Train 模式（IS）

對每個 window 的訓練集：
1. 載入訓練資料
2. 使用指定的 alpha engine 配置進行訓練
3. 優化策略參數（如果需要）
4. 記錄訓練階段的基本統計（不納入最終評估）

### Step 3: Test 模式（OOS）

對每個 window 的測試集：
1. 載入測試資料
2. 使用訓練好的策略參數執行回測
3. 計算績效、風險、TE 等指標
4. 進行因子歸因分析

### Step 4: Governance Rules Simulation

對每個 window 的測試結果：
1. 檢查 Alpha Sunset 條件
2. 檢查 Kill Switch 條件
3. 執行 Regime Detection
4. 記錄所有觸發事件

### Step 5: Combine & Export

彙總所有 window 結果：
1. 計算跨 window 的一致性統計
2. 分析 Governance 規則觸發模式
3. 生成 Alpha Stability Report
4. 輸出所有結果檔案

---

## 📊 產出格式

### Window 結果報告

每個 window 的 CSV/JSON 包含：
- Window ID、日期範圍
- Train/Test 階段績效統計
- Governance 事件時間軸
- 因子歸因表

### 彙總報告

- 所有 window 的平均 Sharpe、Max DD
- Window 間一致性（標準差）
- Alpha Stability Score
- Governance 觸發統計
- Regime 分析

---

## 🔗 與其他模組的整合

- **Path A**: 使用 Path A Backtest 執行每個 window
- **AlphaHealthMonitor**: 監控 Alpha 衰減
- **RegimeManager**: 檢測市場環境變化
- **KillSwitchController**: 執行風險控制

---

## 📚 參考文件

- `docs/JGOD_PATH_B_STANDARD_v1.md` - Path B 標準文件
- `docs/JGOD_PATHA_STANDARD_v1.md` - Path A 標準文件

