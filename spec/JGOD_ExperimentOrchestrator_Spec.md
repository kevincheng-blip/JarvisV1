# JGOD Experiment Orchestrator Spec v1

## 1. ExperimentConfig Schema

```python
@dataclass
class ExperimentConfig:
    """實驗設定資料結構"""
    
    name: str                         # 實驗名稱
    start_date: str                   # 開始日期 "YYYY-MM-DD"
    end_date: str                     # 結束日期 "YYYY-MM-DD"
    rebalance_frequency: str          # 再平衡頻率 "D" / "W" / "M"
    universe: List[str]               # 標的列表
    data_source: str                  # 資料來源 "finmind" / "mock"
    
    # 優化器參數
    optimizer_params: Dict[str, Any] = field(default_factory=dict)
    # 包含：lambda, TE_max, T_max, factor_limits, sector_limits, etc.
    
    # 執行參數
    execution_params: Dict[str, Any] = field(default_factory=dict)
    # 包含：slippage, cost model 設定
    
    # 診斷參數
    diagnosis_params: Dict[str, Any] = field(default_factory=dict)
    # 包含：TE_max, sharpe_threshold, max_drawdown_threshold, etc.
    
    notes: Optional[str] = None       # 實驗備註
```

### 預設參數

```python
DEFAULT_OPTIMIZER_PARAMS = {
    "lambda": 1.0,
    "TE_max": 0.05,
    "T_max": 0.20,
}

DEFAULT_EXECUTION_PARAMS = {
    "slippage_model": "fixed",
    "fixed_slippage": 0.1,
    "commission_rate": 0.001425,
    "tax_rate": 0.003,
}

DEFAULT_DIAGNOSIS_PARAMS = {
    "TE_max": 0.05,
    "T_max": 0.20,
    "max_drawdown_threshold": -0.20,
    "sharpe_threshold": 0.5,
    "ir_threshold": 0.2,
}
```

---

## 2. ExperimentArtifacts Schema

```python
@dataclass
class ExperimentArtifacts:
    """實驗中間產物資料結構"""
    
    path_a_result: PathABacktestResult
    performance_result: PerformanceEngineResult
    diagnosis_result: DiagnosisEngineResult
    execution_stats: Dict[str, Any] = field(default_factory=dict)
    optimizer_stats: Dict[str, Any] = field(default_factory=dict)
```

---

## 3. ExperimentReport Schema

```python
@dataclass
class ExperimentReport:
    """實驗報告資料結構"""
    
    summary: Dict[str, Any]           # 績效摘要
    # 包含：total_return, sharpe, max_drawdown, TE, turnover, etc.
    
    highlights: List[str]              # 亮點摘要（供人類閱讀）
    
    diagnosis_summary: str             # 診斷摘要
    
    repair_actions: List[RepairAction] = field(default_factory=list)
    
    files_generated: List[str] = field(default_factory=list)
    # 路徑：NAV csv、returns csv、performance_report md、diagnosis_report md 等
```

---

## 4. ExperimentRunResult Schema

```python
@dataclass
class ExperimentRunResult:
    """實驗執行結果資料結構"""
    
    config: ExperimentConfig
    artifacts: ExperimentArtifacts
    report: ExperimentReport
```

---

## 5. API 定義

```python
class ExperimentOrchestrator:
    """Experiment Orchestrator 核心類別"""
    
    def __init__(
        self,
        data_loader: PathADataLoader,
        alpha_engine: AlphaEngine,
        risk_model: MultiFactorRiskModel,
        optimizer: OptimizerCoreV2,
        execution_engine: ExecutionEngine,
        performance_engine: PerformanceEngine,
        diagnosis_engine: DiagnosisEngine,
        knowledge_brain: KnowledgeBrain,
        error_learning_engine: ErrorLearningEngine,
    ):
        """初始化 Experiment Orchestrator
        
        Args:
            data_loader: 資料載入器
            alpha_engine: Alpha Engine
            risk_model: Risk Model
            optimizer: Optimizer Core v2
            execution_engine: Execution Engine
            performance_engine: Performance Engine
            diagnosis_engine: Diagnosis Engine
            knowledge_brain: Knowledge Brain
            error_learning_engine: Error Learning Engine
        """
        ...
    
    def run_experiment(
        self,
        config: ExperimentConfig
    ) -> ExperimentRunResult:
        """執行完整實驗
        
        Args:
            config: 實驗設定
        
        Returns:
            ExperimentRunResult 物件
        """
        ...
```

---

## 6. 依賴介面要求

### PathADataLoader

必須實作：
- `load_price_frame(config: PathAConfig) -> pd.DataFrame`
- `load_feature_frame(config: PathAConfig) -> pd.DataFrame`

### AlphaEngine

必須實作：
- `compute_all(features: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame`

### MultiFactorRiskModel

必須實作：
- `get_covariance_matrix() -> np.ndarray`
- `get_symbols() -> List[str]`

### OptimizerCoreV2

必須實作：
- `solve(request: OptimizerRequest) -> OptimizerResult`

### ExecutionEngine

必須實作：
- `rebalance_to_weights(...) -> ExecutionResult`

### PerformanceEngine

必須實作：
- `compute_full_report(request: PerformanceEngineRequest) -> PerformanceEngineResult`

### DiagnosisEngine

必須實作：
- `from_path_a_and_performance(...) -> DiagnosisEngineResult`

---

**版本**：v1.0  
**狀態**：✅ Spec 規範已確立

