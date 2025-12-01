# Diagnosis Engine v1 Editor 指令包

本文檔包含建立 Step 8: Diagnosis & Repair Engine v1 所需的所有 Editor 指令，可直接複製貼上到 Cursor Editor 使用。

## 📋 處理步驟總覽

1. ✅ **建立標準文件** - `docs/JGOD_DIAGNOSIS_ENGINE_STANDARD_v1.md`
2. ✅ **建立 Spec 文件** - `spec/JGOD_DiagnosisEngine_Spec.md`
3. ✅ **建立類型定義** - `jgod/diagnostics/diagnosis_types.py`
4. ✅ **建立核心引擎** - `jgod/diagnostics/diagnosis_engine.py`
5. ✅ **建立測試骨架** - `tests/diagnostics/test_diagnosis_engine_v1.py`
6. ✅ **建立 Editor 指令包** - `docs/DIAGNOSIS_ENGINE_EDITOR_INSTRUCTIONS.md`
7. ⏳ **更新 __init__.py** - 導出新模組

---

## 🎯 Editor 指令 1：驗證已建立的檔案

### 檢查所有建立的檔案

```bash
# 檢查標準文件
ls -lh docs/JGOD_DIAGNOSIS_ENGINE_STANDARD_v1.md

# 檢查 Spec 文件
ls -lh spec/JGOD_DiagnosisEngine_Spec.md

# 檢查程式檔案
ls -lh jgod/diagnostics/diagnosis_types.py
ls -lh jgod/diagnostics/diagnosis_engine.py

# 檢查測試檔案
ls -lh tests/diagnostics/test_diagnosis_engine_v1.py
```

---

## 🎯 Editor 指令 2：更新 __init__.py

### 更新 diagnostics 模組的 __init__.py

需要在 `jgod/diagnostics/__init__.py` 中添加：

```python
"""
Diagnostics Module - 系統診斷模組
包含健康檢查和診斷引擎功能
"""

# Legacy exports (v0)
from .health_check import HealthChecker, check_all_providers

# Diagnosis Engine v1
from .diagnosis_types import (
    DiagnosticEvent,
    SystemHealthSnapshot,
    RepairAction,
    RepairPlan,
    DiagnosisEngineResult,
)
from .diagnosis_engine import DiagnosisEngine

__all__ = [
    # Legacy exports (v0)
    "HealthChecker",
    "check_all_providers",
    # Diagnosis Engine v1 exports
    "DiagnosticEvent",
    "SystemHealthSnapshot",
    "RepairAction",
    "RepairPlan",
    "DiagnosisEngineResult",
    "DiagnosisEngine",
]
```

---

## 🎯 Editor 指令 3：Linter 檢查

### 檢查所有程式檔案

```bash
# 檢查類型定義
python3 -m pylint jgod/diagnostics/diagnosis_types.py --disable=all --enable=import-error,undefined-variable

# 檢查核心引擎
python3 -m pylint jgod/diagnostics/diagnosis_engine.py --disable=all --enable=import-error,undefined-variable

# 使用 mypy 檢查類型（如果已安裝）
python3 -m mypy jgod/diagnostics/diagnosis_types.py --ignore-missing-imports
python3 -m mypy jgod/diagnostics/diagnosis_engine.py --ignore-missing-imports
```

---

## 🎯 Editor 指令 4：語法驗證

### 驗證 Python 語法

```bash
# 驗證所有 Python 檔案語法
for file in jgod/diagnostics/diagnosis_*.py; do
    echo "Checking $file..."
    python3 -m py_compile $file && echo "  ✅ OK" || echo "  ❌ FAILED"
done
```

---

## 🎯 Editor 指令 5：模組導入測試

### 測試模組是否可以正確導入

```bash
# 測試導入
python3 << 'EOF'
try:
    from jgod.diagnostics import (
        DiagnosisEngine,
        DiagnosticEvent,
        SystemHealthSnapshot,
        RepairAction,
        RepairPlan,
        DiagnosisEngineResult
    )
    print("✅ 所有模組導入成功")
except ImportError as e:
    print(f"❌ 導入失敗: {e}")
EOF
```

---

## 🎯 Editor 指令 6：整合到 Path A + Performance

### 檢查 Path A 和 Performance Engine 如何使用 Diagnosis Engine

```bash
# 查看 Path A 和 Performance Engine 的結構
grep -r "PathABacktestResult\|PerformanceEngineResult" jgod/path_a/ jgod/performance/ --include="*.py" | head -10
```

### Path A + Performance + Diagnosis 整合範例

在 Path A 回測和 Performance Engine 分析完成後，可以這樣使用 Diagnosis Engine：

```python
from jgod.diagnostics import DiagnosisEngine
from jgod.path_a import PathABacktestResult
from jgod.performance import PerformanceEngineResult
from jgod.learning.error_learning_engine import ErrorLearningEngine

# Path A 回測完成
backtest_result: PathABacktestResult = run_path_a_backtest(...)

# Performance Engine 分析完成
performance_result: PerformanceEngineResult = performance_engine.compute_full_report(...)

# 初始化 ErrorLearningEngine（可選）
error_learning_engine = ErrorLearningEngine()

# 建立 Diagnosis Engine
diagnosis_engine = DiagnosisEngine(
    error_learning_engine=error_learning_engine,
    config={
        "TE_max": 0.05,
        "T_max": 0.20,
        "max_drawdown_threshold": -0.20,
        "sharpe_threshold": 0.5,
    }
)

# 執行診斷
diagnosis_result = diagnosis_engine.from_path_a_and_performance(
    backtest_result=backtest_result,
    performance_result=performance_result,
    execution_stats=execution_stats,  # 可選
    optimizer_stats=optimizer_stats,  # 可選
)

# 輸出結果
print(f"系統健康狀況：")
print(f"  Total Return: {diagnosis_result.health.total_return:.2%}")
print(f"  Sharpe Ratio: {diagnosis_result.health.sharpe:.2f}")
print(f"  Max Drawdown: {diagnosis_result.health.max_drawdown:.2%}")

print(f"\n診斷事件數量：{len(diagnosis_result.diagnostic_events)}")
for event in diagnosis_result.diagnostic_events:
    print(f"  [{event.severity}] {event.issue_type}: {event.message}")

print(f"\n修復建議數量：{len(diagnosis_result.repair_plan.actions)}")
for action in diagnosis_result.repair_plan.actions:
    print(f"  [{action.priority}] {action.description}")
```

---

## 🎯 Editor 指令 7：基本功能測試

### 建立簡單測試腳本

```python
# 檔案：tests/diagnostics/test_basic.py

"""基本功能測試"""

from jgod.diagnostics import DiagnosisEngine, DiagnosticEvent

def test_basic_diagnosis():
    """測試基本診斷功能"""
    # 建立 Diagnosis Engine
    engine = DiagnosisEngine()
    
    # 建立測試用的 DiagnosticEvent
    event = DiagnosticEvent(
        source_module="PERFORMANCE",
        issue_type="ALPHA_UNDERPERFORM",
        severity="WARN",
        message="Sharpe Ratio 偏低",
        metrics_after={"sharpe": 0.3},
    )
    
    print(f"診斷事件：{event.message}")
    print(f"嚴重度：{event.severity}")
    print(f"問題類型：{event.issue_type}")
    
    return event

if __name__ == "__main__":
    test_basic_diagnosis()
```

執行測試：

```bash
python3 tests/diagnostics/test_basic.py
```

---

## 🎯 Editor 指令 8：執行測試

### 執行 Diagnosis Engine 測試

```bash
# 執行所有 Diagnosis Engine 測試
pytest tests/diagnostics/test_diagnosis_engine_v1.py -v

# 執行特定測試
pytest tests/diagnostics/test_diagnosis_engine_v1.py::test_healthy_scenario -v

# 執行並顯示輸出
pytest tests/diagnostics/test_diagnosis_engine_v1.py -v -s
```

---

## 🎯 Editor 指令 9：檢查依賴

### 檢查是否需要額外的 Python 套件

```bash
# 檢查依賴
python3 << 'EOF'
import sys
required_modules = [
    "pandas",
    "numpy",
    "dataclasses",
    "typing",
    "uuid",
    "datetime",
]

missing = []
for module in required_modules:
    try:
        __import__(module)
        print(f"✅ {module}: OK")
    except ImportError:
        missing.append(module)
        print(f"❌ {module}: Missing")

if missing:
    print(f"\n需要安裝：pip install {' '.join(missing)}")
else:
    print("\n✅ 所有依賴已滿足")
EOF
```

---

## 📋 檢查清單

執行完成後，確認以下項目：

- [x] 標準文件已建立：`docs/JGOD_DIAGNOSIS_ENGINE_STANDARD_v1.md`
- [x] Spec 文件已建立：`spec/JGOD_DiagnosisEngine_Spec.md`
- [x] 類型定義已建立：`jgod/diagnostics/diagnosis_types.py`
- [x] 核心引擎已建立：`jgod/diagnostics/diagnosis_engine.py`
- [x] 測試骨架已建立：`tests/diagnostics/test_diagnosis_engine_v1.py`
- [x] Editor 指令包已建立：`docs/DIAGNOSIS_ENGINE_EDITOR_INSTRUCTIONS.md`
- [ ] `__init__.py` 已更新以導出新模組
- [ ] 所有檔案通過 Linter 檢查
- [ ] 基本功能測試通過
- [ ] 可以成功整合到 Path A + Performance

---

## 🚀 後續步驟

### 1. 補齊診斷邏輯

- 實作更完整的約束分析邏輯
- 實作更精確的績效分析規則
- 處理邊界情況

### 2. 擴充修復建議

- 產生更詳細的修復建議
- 根據不同問題類型產生不同類型的修復行動

### 3. 整合到 Path A

- 在 Path A 回測流程中整合 Diagnosis Engine
- 自動生成診斷報告

### 4. 擴充測試

- 補充完整的單元測試
- 建立整合測試
- 測試 ErrorLearningEngine 橋接功能

---

**版本**：v1.0  
**狀態**：✅ Editor 指令包已建立

