# Execution Engine v1 Editor 指令包

本文檔包含建立 Step 6: Execution Engine v1 所需的所有 Editor 指令，可直接複製貼上到 Cursor Editor 使用。

## 📋 處理步驟總覽

1. ✅ **建立標準文件** - `docs/JGOD_EXECUTION_ENGINE_STANDARD_v1.md`
2. ✅ **建立 Spec 文件** - `spec/JGOD_ExecutionEngine_Spec.md`
3. ✅ **建立類型定義** - `jgod/execution/execution_types.py`
4. ✅ **建立滑價模型** - `jgod/execution/execution_models.py`
5. ✅ **建立成本模型** - `jgod/execution/cost_model.py`
6. ✅ **建立券商介面** - `jgod/execution/broker_adapter.py`
7. ✅ **建立核心引擎** - `jgod/execution/execution_engine.py`
8. ✅ **建立測試骨架** - `tests/execution/test_execution_engine_v1.py`
9. ✅ **建立 Editor 指令包** - `docs/EXECUTION_ENGINE_EDITOR_INSTRUCTIONS.md`

---

## 🎯 Editor 指令 1：驗證已建立的檔案

### 檢查所有建立的檔案

```bash
# 檢查標準文件
ls -lh docs/JGOD_EXECUTION_ENGINE_STANDARD_v1.md

# 檢查 Spec 文件
ls -lh spec/JGOD_ExecutionEngine_Spec.md

# 檢查程式檔案
ls -lh jgod/execution/execution_types.py
ls -lh jgod/execution/execution_models.py
ls -lh jgod/execution/cost_model.py
ls -lh jgod/execution/broker_adapter.py
ls -lh jgod/execution/execution_engine.py

# 檢查測試檔案
ls -lh tests/execution/test_execution_engine_v1.py
```

---

## 🎯 Editor 指令 2：Linter 檢查

### 檢查所有程式檔案

```bash
# 檢查類型定義
python3 -m pylint jgod/execution/execution_types.py --disable=all --enable=import-error,undefined-variable

# 檢查滑價模型
python3 -m pylint jgod/execution/execution_models.py --disable=all --enable=import-error,undefined-variable

# 檢查成本模型
python3 -m pylint jgod/execution/cost_model.py --disable=all --enable=import-error,undefined-variable

# 檢查券商介面
python3 -m pylint jgod/execution/broker_adapter.py --disable=all --enable=import-error,undefined-variable

# 檢查核心引擎
python3 -m pylint jgod/execution/execution_engine.py --disable=all --enable=import-error,undefined-variable

# 使用 mypy 檢查類型（如果已安裝）
python3 -m mypy jgod/execution/execution_types.py --ignore-missing-imports
python3 -m mypy jgod/execution/execution_engine.py --ignore-missing-imports
```

---

## 🎯 Editor 指令 3：語法驗證

### 驗證 Python 語法

```bash
# 驗證所有 Python 檔案語法
for file in jgod/execution/execution_*.py jgod/execution/cost_model.py jgod/execution/broker_adapter.py; do
    echo "Checking $file..."
    python3 -m py_compile $file && echo "  ✅ OK" || echo "  ❌ FAILED"
done
```

---

## 🎯 Editor 指令 4：更新 __init__.py

### 檢查並更新 execution 模組的 __init__.py

```bash
# 查看現有的 __init__.py
cat jgod/execution/__init__.py

# 更新 __init__.py 以導出新的模組
```

需要在 `jgod/execution/__init__.py` 中添加：

```python
# Execution Engine v1
from .execution_types import Order, Fill, Trade, Position, PortfolioState
from .execution_models import (
    ExecutionModel,
    FixedSlippageModel,
    PercentageSlippageModel,
    VolumeImpactSlippageModel
)
from .cost_model import CostModel, DefaultCostModel
from .broker_adapter import BrokerAdapter, MockBrokerAdapter
from .execution_engine import ExecutionEngine, ExecutionRequest, ExecutionResult

__all__ = [
    # v1 exports
    "Order",
    "Fill",
    "Trade",
    "Position",
    "PortfolioState",
    "ExecutionModel",
    "FixedSlippageModel",
    "PercentageSlippageModel",
    "VolumeImpactSlippageModel",
    "CostModel",
    "DefaultCostModel",
    "BrokerAdapter",
    "MockBrokerAdapter",
    "ExecutionEngine",
    "ExecutionRequest",
    "ExecutionResult",
]
```

---

## 🎯 Editor 指令 5：整合到 Path A

### 檢查 Path A 是否需要更新

```bash
# 查看 Path A 如何使用 Execution Engine
grep -r "execution\|Execution" jgod/path_a/ tests/path_a/ --include="*.py"

# 檢查 Path A backtest 是否需要整合 Execution Engine
cat jgod/path_a/path_a_backtest.py | grep -A 10 -B 10 "execution\|Execution"
```

### Path A 整合範例

在 `jgod/path_a/path_a_backtest.py` 中，可以這樣整合：

```python
from jgod.execution import (
    ExecutionEngine,
    FixedSlippageModel,
    DefaultCostModel
)

# 在 run_path_a_backtest 中初始化
execution_model = FixedSlippageModel(slippage=0.1)
cost_model = DefaultCostModel()
execution_engine = ExecutionEngine(
    execution_model=execution_model,
    cost_model=cost_model
)

# 在 rebalance 時使用
result = execution_engine.rebalance_to_weights(
    target_weights=optimizer_result.weights_dict,
    prev_portfolio=current_portfolio_state,
    prices=current_prices,
    volumes=daily_volumes
)

# 更新組合狀態
current_portfolio_state = result.new_portfolio_state
```

---

## 🎯 Editor 指令 6：基本功能測試

### 建立簡單測試腳本

```python
# 檔案：tests/execution/test_basic.py

"""基本功能測試"""

from jgod.execution import (
    ExecutionEngine,
    FixedSlippageModel,
    DefaultCostModel,
    PortfolioState,
    Position
)

def test_basic_execution():
    """測試基本執行流程"""
    # 初始化
    execution_model = FixedSlippageModel(slippage=0.1)
    cost_model = DefaultCostModel()
    engine = ExecutionEngine(
        execution_model=execution_model,
        cost_model=cost_model
    )
    
    # 建立初始組合狀態
    portfolio = PortfolioState(
        cash=1000000.0,
        positions={
            "2330.TW": Position(
                symbol="2330.TW",
                quantity=1000,
                avg_price=500.0,
                current_price=510.0
            )
        }
    )
    
    # 目標權重
    target_weights = {
        "2330.TW": 0.5,
        "2317.TW": 0.5
    }
    
    # 價格
    prices = {
        "2330.TW": 510.0,
        "2317.TW": 150.0
    }
    
    # 執行再平衡
    result = engine.rebalance_to_weights(
        target_weights=target_weights,
        prev_portfolio=portfolio,
        prices=prices
    )
    
    print(f"換手率: {result.turnover}")
    print(f"交易成本: {result.transaction_costs}")
    print(f"新組合總價值: {result.new_portfolio_state.total_value}")
    
    return result

if __name__ == "__main__":
    test_basic_execution()
```

執行測試：

```bash
python3 tests/execution/test_basic.py
```

---

## 🎯 Editor 指令 7：檢查依賴

### 檢查是否需要額外的 Python 套件

```bash
# 檢查是否有缺失的依賴
python3 << 'EOF'
try:
    import uuid
    print("✅ uuid: OK")
except ImportError as e:
    print(f"❌ uuid: {e}")

try:
    from dataclasses import dataclass
    print("✅ dataclasses: OK")
except ImportError as e:
    print(f"❌ dataclasses: {e}")

try:
    from typing import Protocol
    print("✅ typing.Protocol: OK")
except ImportError as e:
    print(f"❌ typing.Protocol: {e}")
EOF
```

---

## 📋 檢查清單

執行完成後，確認以下項目：

- [x] 標準文件已建立：`docs/JGOD_EXECUTION_ENGINE_STANDARD_v1.md`
- [x] Spec 文件已建立：`spec/JGOD_ExecutionEngine_Spec.md`
- [x] 類型定義已建立：`jgod/execution/execution_types.py`
- [x] 滑價模型已建立：`jgod/execution/execution_models.py`
- [x] 成本模型已建立：`jgod/execution/cost_model.py`
- [x] 券商介面已建立：`jgod/execution/broker_adapter.py`
- [x] 核心引擎已建立：`jgod/execution/execution_engine.py`
- [x] 測試骨架已建立：`tests/execution/test_execution_engine_v1.py`
- [x] Editor 指令包已建立：`docs/EXECUTION_ENGINE_EDITOR_INSTRUCTIONS.md`
- [ ] `__init__.py` 已更新以導出新模組
- [ ] 所有檔案通過 Linter 檢查
- [ ] 基本功能測試通過

---

## 🚀 後續步驟

### 1. 更新 __init__.py

需要更新 `jgod/execution/__init__.py` 以導出新的模組。

### 2. 整合到 Path A

在 Path A 回測流程中整合 Execution Engine。

### 3. 擴充測試

補充完整的單元測試和整合測試。

### 4. 文件完善

補充使用範例和 API 文件。

---

**版本**：v1.0  
**狀態**：✅ Editor 指令包已建立

