# J-GOD Path C Engine Specification

## 📋 概述

Path C Engine 是 J-GOD 系統中用於執行 **批次場景驗證（Batch Scenario Validation）**的核心引擎。其目的是針對多組不同的設定組合（Scenario）進行批量測試，比較並排名哪些設定組合最適合作為正式策略候選。

---

## 🎯 核心角色與目的

### A. Path C Engine 的存在目的

1. **批次執行多組 Scenario**
   - 接收多組不同的設定組合（window/step, mode, data_source, universe, governance 門檻等）
   - 逐一呼叫 Path B Engine 執行每個 scenario
   - 收集所有 scenario 的執行結果

2. **結果彙總與排名**
   - 收集每個 scenario 的關鍵指標（Sharpe, Max DD, TE, breach 率等）
   - 按照預定義規則進行排名
   - 識別最佳 scenario 組合

3. **生成完整報告**
   - CSV 排名表
   - JSON 總結
   - Markdown 報告（包含前 3 名詳細資訊）

4. **與 Path B 的關係**
   - Path C **僅調用 Path B**，不重複實作回測邏輯
   - Path C 負責場景管理、批次執行、結果彙總與排名
   - Path B 負責實際的 walk-forward 分析與 governance 評估

---

## 🔌 Interface / API 規格

### 1. PathCScenarioConfig

```python
@dataclass
class PathCScenarioConfig:
    """Path C Scenario Configuration"""
    
    name: str
    description: str
    
    # Path B / Path A 相關設定
    start_date: str  # "YYYY-MM-DD"
    end_date: str    # "YYYY-MM-DD"
    rebalance_frequency: str  # "D", "W", "M"
    universe: List[str]
    
    # Path B 相關設定
    walkforward_window: str  # "6m", "1y" 等
    walkforward_step: str    # "1m", "3m" 等
    
    # 系統模式
    data_source: DataSourceType = "mock"  # "mock" | "finmind"
    mode: ModeType = "basic"  # "basic" | "extreme"
    
    # 治理門檻（可選，可覆寫 Path B 預設值）
    max_drawdown_limit: Optional[float] = None
    min_sharpe: Optional[float] = None
    max_tracking_error: Optional[float] = None
    max_turnover: Optional[float] = None
    
    # Tag 用於報表分類
    regime_tag: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)
```

### 2. PathCScenarioResult

```python
@dataclass
class PathCScenarioResult:
    """Path C Scenario Execution Result"""
    
    scenario: PathCScenarioConfig
    
    # 從 Path B Engine 回來的關鍵數字
    sharpe: float
    max_drawdown: float
    total_return: float
    governance_breach_ratio: float  # 0.0 - 1.0
    governance_breach_count: int
    windows_count: int
    
    # 原始 Path B 結果（或其子集）
    raw_path_b_summary: Dict
    raw_governance_summary: Dict
    
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None
```

### 3. PathCExperimentConfig

```python
@dataclass
class PathCExperimentConfig:
    """Path C Experiment Configuration"""
    
    name: str
    scenarios: List[PathCScenarioConfig]
    output_dir: str = "output/path_c"
    
    description: Optional[str] = None
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
```

### 4. PathCRunSummary

```python
@dataclass
class PathCRunSummary:
    """Path C Run Summary"""
    
    experiment_name: str
    scenarios: List[PathCScenarioResult]
    ranking_table: List[Dict]  # 已排序好的 scenario 排名列表
    best_scenarios: List[str]  # 名稱清單（例如前 3 名）
    created_at: str
    
    config_snapshot: Dict
    total_scenarios: int = 0
    successful_scenarios: int = 0
    failed_scenarios: int = 0
    output_files: List[str] = field(default_factory=list)
```

### 5. PathCEngine

```python
class PathCEngine:
    """Path C Engine - Validation Lab / Scenario Engine"""
    
    def __init__(
        self,
        path_b_engine: Optional[PathBEngine] = None,
    ):
        """初始化 Path C Engine"""
    
    def run_experiment(
        self,
        config: PathCExperimentConfig,
    ) -> PathCRunSummary:
        """
        執行完整的 Path C 實驗
        
        內部流程：
        1. 對每個 scenario：
           a. 將 PathCScenarioConfig 轉換為 PathBConfig
           b. 呼叫 PathBEngine.run(config)
           c. 提取關鍵指標並建立 PathCScenarioResult
        2. 排名所有 scenarios
        3. 生成報告檔案（CSV, JSON, Markdown）
        """
```

---

## 📊 排名規則

Path C 使用以下規則對 scenarios 進行排名：

1. **主要排序**：Sharpe Ratio（降冪，越高越好）
2. **次要排序**：Max Drawdown（升冪，越小越好）
3. **第三排序**：Governance Breach Ratio（升冪，越小越好）

失敗的 scenario 會被放在最後，不參與排名。

---

## 📁 輸出檔案結構

Path C 實驗輸出結構：

```
output/path_c/{experiment_name}/
├── scenarios_rankings.csv      # 排名表（CSV）
├── path_c_summary.json         # 完整總結（JSON）
├── path_c_report.md            # 報告（Markdown）
└── config.json                 # 配置快照（JSON）
```

---

## 🔗 與 Path A / Path B 的關係

- **Path A**: 單一回測引擎
- **Path B**: 針對「一組設定」做 walk-forward（多 window）＋治理規則評估
- **Path C**: 針對「多組 Scenario」批次呼叫 Path B，彙總結果、排名、輸出報告

Path C 僅調用 Path B，不重複實作回測邏輯。

