# JGOD Diagnosis Engine Spec v1

## 1. DiagnosticEvent Schema

```python
@dataclass
class DiagnosticEvent:
    """診斷事件資料結構"""
    
    id: str                          # 唯一識別碼
    timestamp: datetime              # 事件時間戳
    source_module: str               # 來源模組（PATH_A, EXECUTION, PERFORMANCE, OPTIMIZER, RISK_MODEL）
    issue_type: str                  # 問題類型（TE_EXCEEDED, DRAWDOWN_EXCEEDED, TURNOVER_TOO_HIGH, etc.）
    severity: str                    # 嚴重度（INFO, WARN, CRITICAL）
    message: str                     # 人類可讀描述
    metrics_before: Dict[str, float] = field(default_factory=dict)
    metrics_after: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    related_symbols: List[str] = field(default_factory=list)
    related_factors: List[str] = field(default_factory=list)
    related_error_event_id: Optional[str] = None
```

### issue_type 允許值

- `TE_EXCEEDED`：Tracking Error 超過上限
- `DRAWDOWN_EXCEEDED`：最大回落超過門檻
- `TURNOVER_TOO_HIGH`：換手率過高
- `CONSTRAINT_VIOLATION`：約束違反
- `ALPHA_UNDERPERFORM`：Alpha 表現不佳
- `RISK_CONTROL_FAILED`：風險控制失效
- `DATA_QUALITY`：資料品質問題
- `OPTIMIZER_INFEASIBLE`：優化器無解

---

## 2. SystemHealthSnapshot Schema

```python
@dataclass
class SystemHealthSnapshot:
    """系統健康快照資料結構"""
    
    experiment_name: str
    start_date: date
    end_date: date
    total_return: float
    cagr: float
    sharpe: float
    max_drawdown: float
    tracking_error: float
    turnover: float
    violated_constraints: List[str] = field(default_factory=list)
    error_event_counts: Dict[str, int] = field(default_factory=dict)  # {error_type: count}
```

---

## 3. RepairAction Schema

```python
@dataclass
class RepairAction:
    """修復行動資料結構"""
    
    action_id: str
    action_type: str                  # TUNE_CONFIG, CHECK_DATA, REVIEW_RULES, etc.
    target_module: str                # 目標模組
    description: str                  # 行動描述
    proposed_changes: Dict[str, Any] = field(default_factory=dict)  # 建議的變更
    priority: str                     # HIGH, MEDIUM, LOW
```

### action_type 允許值

- `TUNE_CONFIG`：調整配置參數
- `CHECK_DATA`：檢查資料品質
- `REVIEW_RULES`：檢討交易規則
- `ADJUST_FACTOR_WEIGHT`：調整因子權重
- `RELAX_CONSTRAINT`：放寬約束

---

## 4. RepairPlan Schema

```python
@dataclass
class RepairPlan:
    """修復計畫資料結構"""
    
    experiment_name: str
    summary: str                      # 計畫摘要
    actions: List[RepairAction] = field(default_factory=list)
```

---

## 5. DiagnosisEngineResult Schema

```python
@dataclass
class DiagnosisEngineResult:
    """Diagnosis Engine 完整輸出結果"""
    
    health: SystemHealthSnapshot
    diagnostic_events: List[DiagnosticEvent]
    repair_plan: RepairPlan
```

---

## 6. DiagnosisEngineRequest Schema

```python
@dataclass
class DiagnosisEngineRequest:
    """Diagnosis Engine 輸入請求資料結構"""
    
    # Path A 結果
    backtest_result: PathABacktestResult
    
    # Performance 結果
    performance_result: PerformanceEngineResult
    
    # Execution 統計（可選）
    execution_stats: Optional[Dict[str, Any]] = None
    
    # Optimizer / Risk 訊號（可選）
    optimizer_stats: Optional[Dict[str, Any]] = None
    
    # Config（包含所有門檻值）
    config: Dict[str, Any] = field(default_factory=dict)
```

---

## 7. API 定義

```python
class DiagnosisEngine:
    """Diagnosis & Repair Engine 核心類別"""
    
    def __init__(
        self,
        error_learning_engine: Optional[ErrorLearningEngine] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化 Diagnosis Engine
        
        Args:
            error_learning_engine: ErrorLearningEngine 實例（可選）
            config: 配置參數（門檻值等）
        """
        ...
    
    def from_path_a_and_performance(
        self,
        backtest_result: PathABacktestResult,
        performance_result: PerformanceEngineResult,
        execution_stats: Optional[Dict[str, Any]] = None,
        optimizer_stats: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> DiagnosisEngineResult:
        """從 Path A 和 Performance 結果進行診斷
        
        Args:
            backtest_result: Path A 回測結果
            performance_result: Performance Engine 結果
            execution_stats: Execution 統計（可選）
            optimizer_stats: Optimizer 統計（可選）
            config: 配置參數（可選）
        
        Returns:
            DiagnosisEngineResult 物件
        """
        ...
```

---

## 8. ErrorLearningEngine 串接方式

### 橋接方法

```python
def _bridge_to_error_engine(
    self,
    diagnostic_event: DiagnosticEvent
) -> Optional[ErrorEvent]:
    """將 DiagnosticEvent 轉換為 ErrorEvent
    
    Args:
        diagnostic_event: DiagnosticEvent 物件
    
    Returns:
        ErrorEvent 物件（如果應轉換），否則返回 None
    """
    ...
```

### 轉換規則

- **不修改 ErrorLearningEngine**：只使用其現有 API
- **只傳送符合條件的 Event**：根據 severity 和 issue_type 判斷
- **保持 ErrorEvent 格式**：確保轉換後的 ErrorEvent 符合 ErrorLearningEngine 的期望格式

---

**版本**：v1.0  
**狀態**：✅ Spec 規範已確立

