# Experiment Orchestrator v1 Editor 指令包

本文檔包含建立 Step 9: Path A Orchestrator & Reporting v1 所需的所有 Editor 指令，可直接複製貼上到 Cursor Editor 使用。

## 📋 處理步驟總覽

1. ✅ **建立標準文件** - `docs/JGOD_EXPERIMENT_ORCHESTRATOR_STANDARD_v1.md`
2. ✅ **建立 Spec 文件** - `spec/JGOD_ExperimentOrchestrator_Spec.md`
3. ✅ **建立類型定義** - `jgod/experiments/experiment_types.py`
4. ✅ **建立核心編排器** - `jgod/experiments/experiment_orchestrator.py`
5. ✅ **建立執行腳本** - `scripts/run_jgod_experiment.py`
6. ✅ **建立測試骨架** - `tests/experiments/test_experiment_orchestrator_v1.py`
7. ✅ **建立 Editor 指令包** - `docs/EXPERIMENT_ORCHESTRATOR_EDITOR_INSTRUCTIONS.md`

---

## 🎯 Editor 指令 1：驗證已建立的檔案

### 檢查所有建立的檔案

```bash
# 檢查標準文件
ls -lh docs/JGOD_EXPERIMENT_ORCHESTRATOR_STANDARD_v1.md

# 檢查 Spec 文件
ls -lh spec/JGOD_ExperimentOrchestrator_Spec.md

# 檢查程式檔案
ls -lh jgod/experiments/experiment_types.py
ls -lh jgod/experiments/experiment_orchestrator.py

# 檢查執行腳本
ls -lh scripts/run_jgod_experiment.py

# 檢查測試檔案
ls -lh tests/experiments/test_experiment_orchestrator_v1.py
```

---

## 🎯 Editor 指令 2：Linter 檢查

### 檢查所有程式檔案

```bash
# 檢查類型定義
python3 -m pylint jgod/experiments/experiment_types.py --disable=all --enable=import-error,undefined-variable

# 檢查核心編排器
python3 -m pylint jgod/experiments/experiment_orchestrator.py --disable=all --enable=import-error,undefined-variable

# 檢查執行腳本
python3 -m pylint scripts/run_jgod_experiment.py --disable=all --enable=import-error,undefined-variable
```

---

## 🎯 Editor 指令 3：語法驗證

### 驗證 Python 語法

```bash
# 驗證所有 Python 檔案語法
for file in jgod/experiments/*.py scripts/run_jgod_experiment.py; do
    echo "Checking $file..."
    python3 -m py_compile $file && echo "  ✅ OK" || echo "  ❌ FAILED"
done
```

---

## 🎯 Editor 指令 4：模組導入測試

### 測試模組是否可以正確導入

```bash
# 測試導入
python3 << 'EOF'
try:
    from jgod.experiments import (
        ExperimentOrchestrator,
        ExperimentConfig,
        ExperimentArtifacts,
        ExperimentReport,
        ExperimentRunResult
    )
    print("✅ 所有模組導入成功")
except ImportError as e:
    print(f"❌ 導入失敗: {e}")
EOF
```

---

## 🎯 Editor 指令 5：補齊 build_orchestrator() 實作

### 在 scripts/run_jgod_experiment.py 中補齊實作

需要在 `build_orchestrator()` 函數中初始化所有模組：

```python
def build_orchestrator() -> ExperimentOrchestrator:
    """建立 ExperimentOrchestrator 實例"""
    # 資料載入器
    if config.data_source == "finmind":
        from FinMind.data import DataLoader as FinMindDataLoader
        from jgod.path_a.finmind_loader import FinMindPathADataLoader
        finmind_client = FinMindDataLoader()
        data_loader = FinMindPathADataLoader(finmind_client)
    else:
        from jgod.path_a.mock_data_loader import MockPathADataLoader
        data_loader = MockPathADataLoader()
    
    # Alpha Engine
    from jgod.alpha_engine.alpha_engine import AlphaEngine
    alpha_engine = AlphaEngine()
    
    # Risk Model
    from jgod.risk.risk_model import MultiFactorRiskModel
    risk_model = MultiFactorRiskModel(...)
    
    # Optimizer
    from jgod.optimizer.optimizer_core_v2 import OptimizerCoreV2
    optimizer = OptimizerCoreV2()
    
    # Execution Engine
    from jgod.execution.execution_engine import ExecutionEngine
    from jgod.execution.execution_models import FixedSlippageModel
    from jgod.execution.cost_model import DefaultCostModel
    execution_model = FixedSlippageModel(...)
    cost_model = DefaultCostModel(...)
    execution_engine = ExecutionEngine(
        execution_model=execution_model,
        cost_model=cost_model
    )
    
    # Performance Engine
    from jgod.performance.attribution_engine import PerformanceEngine
    performance_engine = PerformanceEngine()
    
    # Diagnosis Engine
    from jgod.diagnostics.diagnosis_engine import DiagnosisEngine
    from jgod.learning.error_learning_engine import ErrorLearningEngine
    error_learning_engine = ErrorLearningEngine()
    diagnosis_engine = DiagnosisEngine(
        error_learning_engine=error_learning_engine
    )
    
    # Knowledge Brain
    from jgod.knowledge.knowledge_brain import KnowledgeBrain
    knowledge_brain = KnowledgeBrain()
    
    return ExperimentOrchestrator(
        data_loader=data_loader,
        alpha_engine=alpha_engine,
        risk_model=risk_model,
        optimizer=optimizer,
        execution_engine=execution_engine,
        performance_engine=performance_engine,
        diagnosis_engine=diagnosis_engine,
        knowledge_brain=knowledge_brain,
        error_learning_engine=error_learning_engine,
    )
```

---

## 🎯 Editor 指令 6：基本使用範例

### 在 REPL / script 裡呼叫 ExperimentOrchestrator

```python
from jgod.experiments import ExperimentOrchestrator, ExperimentConfig

# 建立實驗設定
config = ExperimentConfig(
    name="demo_experiment",
    start_date="2024-01-01",
    end_date="2024-06-30",
    rebalance_frequency="M",
    universe=["2330.TW", "2317.TW", "2454.TW"],
    data_source="finmind",
    optimizer_params={
        "lambda": 1.0,
        "TE_max": 0.05,
        "T_max": 0.20,
    },
    execution_params={
        "slippage_model": "fixed",
        "fixed_slippage": 0.1,
    },
    diagnosis_params={
        "TE_max": 0.05,
        "sharpe_threshold": 0.5,
        "max_drawdown_threshold": -0.20,
    },
    notes="測試 Experiment Orchestrator"
)

# 建立 Orchestrator（需要先初始化所有模組）
orchestrator = build_orchestrator()  # 需要實作此函數

# 執行實驗
result = orchestrator.run_experiment(config)

# 檢視結果
print(f"Total Return: {result.report.summary['total_return']:.2%}")
print(f"Sharpe Ratio: {result.report.summary['sharpe']:.2f}")

for highlight in result.report.highlights:
    print(f"  • {highlight}")

print(f"\nFiles generated: {len(result.report.files_generated)}")
```

---

## 🎯 Editor 指令 7：執行腳本測試

### 測試執行腳本（需要先補齊實作）

```bash
# 使用 mock data 測試
python3 scripts/run_jgod_experiment.py \
    --name test_mock \
    --start-date 2024-01-01 \
    --end-date 2024-01-31 \
    --rebalance-frequency M \
    --universe "2330.TW,2317.TW" \
    --data-source mock

# 檢查輸出
ls -lh output/experiments/test_mock/
```

---

## 🎯 Editor 指令 8：執行測試

### 執行 Experiment Orchestrator 測試

```bash
# 執行所有測試
pytest tests/experiments/test_experiment_orchestrator_v1.py -v

# 執行特定測試
pytest tests/experiments/test_experiment_orchestrator_v1.py::test_run_experiment_basic -v

# 執行並顯示輸出
pytest tests/experiments/test_experiment_orchestrator_v1.py -v -s
```

---

## 🎯 Editor 指令 9：檢查輸出目錄

### 檢查實驗輸出

```bash
# 列出所有實驗
ls -la output/experiments/

# 檢視特定實驗的輸出
ls -lh output/experiments/{experiment_name}/

# 檢視報告
cat output/experiments/{experiment_name}/performance_report.md
cat output/experiments/{experiment_name}/diagnosis_report.md
cat output/experiments/{experiment_name}/repair_plan.md
```

---

## 📋 檢查清單

執行完成後，確認以下項目：

- [x] 標準文件已建立：`docs/JGOD_EXPERIMENT_ORCHESTRATOR_STANDARD_v1.md`
- [x] Spec 文件已建立：`spec/JGOD_ExperimentOrchestrator_Spec.md`
- [x] 類型定義已建立：`jgod/experiments/experiment_types.py`
- [x] 核心編排器已建立：`jgod/experiments/experiment_orchestrator.py`
- [x] 執行腳本已建立：`scripts/run_jgod_experiment.py`
- [x] 測試骨架已建立：`tests/experiments/test_experiment_orchestrator_v1.py`
- [x] Editor 指令包已建立：`docs/EXPERIMENT_ORCHESTRATOR_EDITOR_INSTRUCTIONS.md`
- [x] `__init__.py` 已建立
- [ ] 所有檔案通過 Linter 檢查
- [ ] `build_orchestrator()` 已補齊實作
- [ ] 基本功能測試通過

---

## 🚀 後續步驟

### 1. 補齊 build_orchestrator() 實作

- 在 `scripts/run_jgod_experiment.py` 中補齊所有模組的初始化邏輯
- 確保所有依賴都正確導入

### 2. 完善 ErrorBridge 整合

- 在 `_run_path_a_backtest()` 中實作 ErrorBridge
- 確保錯誤事件能正確傳遞給 ErrorLearningEngine

### 3. 擴充報告生成

- 完善 `_write_performance_report()` 的內容
- 完善 `_write_diagnosis_report()` 的內容
- 考慮添加圖表生成功能

### 4. 擴充測試

- 補充完整的單元測試
- 建立整合測試
- 測試檔案輸出功能

---

**版本**：v1.0  
**狀態**：✅ Editor 指令包已建立

