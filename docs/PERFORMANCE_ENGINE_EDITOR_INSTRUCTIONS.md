# Performance Engine v1 Editor 指令包

本文檔包含建立 Step 7: Performance & Attribution Engine v1 所需的所有 Editor 指令，可直接複製貼上到 Cursor Editor 使用。

## 📋 處理步驟總覽

1. ✅ **建立標準文件** - `docs/JGOD_PERFORMANCE_ENGINE_STANDARD_v1.md`
2. ✅ **建立 Spec 文件** - `spec/JGOD_PerformanceEngine_Spec.md`
3. ✅ **建立模組目錄** - `jgod/performance/`
4. ✅ **建立類型定義** - `jgod/performance/performance_types.py`
5. ✅ **建立績效指標** - `jgod/performance/performance_metrics.py`
6. ✅ **建立歸因引擎** - `jgod/performance/attribution_engine.py`
7. ✅ **建立測試骨架** - `tests/performance/test_performance_engine_v1.py`
8. ✅ **建立 Editor 指令包** - `docs/PERFORMANCE_ENGINE_EDITOR_INSTRUCTIONS.md`

---

## 🎯 Editor 指令 1：驗證已建立的檔案

### 檢查所有建立的檔案

```bash
# 檢查標準文件
ls -lh docs/JGOD_PERFORMANCE_ENGINE_STANDARD_v1.md

# 檢查 Spec 文件
ls -lh spec/JGOD_PerformanceEngine_Spec.md

# 檢查程式檔案
ls -lh jgod/performance/performance_types.py
ls -lh jgod/performance/performance_metrics.py
ls -lh jgod/performance/attribution_engine.py

# 檢查測試檔案
ls -lh tests/performance/test_performance_engine_v1.py
```

---

## 🎯 Editor 指令 2：Linter 檢查

### 檢查所有程式檔案

```bash
# 檢查類型定義
python3 -m pylint jgod/performance/performance_types.py --disable=all --enable=import-error,undefined-variable

# 檢查績效指標
python3 -m pylint jgod/performance/performance_metrics.py --disable=all --enable=import-error,undefined-variable

# 檢查歸因引擎
python3 -m pylint jgod/performance/attribution_engine.py --disable=all --enable=import-error,undefined-variable

# 使用 mypy 檢查類型（如果已安裝）
python3 -m mypy jgod/performance/performance_types.py --ignore-missing-imports
python3 -m mypy jgod/performance/performance_metrics.py --ignore-missing-imports
python3 -m mypy jgod/performance/attribution_engine.py --ignore-missing-imports
```

---

## 🎯 Editor 指令 3：語法驗證

### 驗證 Python 語法

```bash
# 驗證所有 Python 檔案語法
for file in jgod/performance/*.py; do
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
    from jgod.performance import (
        PerformanceEngine,
        PerformanceEngineRequest,
        PerformanceSummary,
        AttributionReport,
        PerformanceEngineResult
    )
    print("✅ 所有模組導入成功")
except ImportError as e:
    print(f"❌ 導入失敗: {e}")
EOF
```

---

## 🎯 Editor 指令 5：基本功能測試

### 建立簡單測試腳本

```python
# 檔案：tests/performance/test_basic.py

"""基本功能測試"""

import pandas as pd
import numpy as np
from jgod.performance import (
    PerformanceEngine,
    PerformanceEngineRequest
)

def test_compute_summary_basic():
    """測試基本績效摘要計算"""
    # 建立簡單的報酬序列
    dates = pd.date_range("2024-01-01", periods=252, freq="D")
    returns = pd.Series(np.random.normal(0.001, 0.02, 252), index=dates)
    nav = (1 + returns).cumprod() * 100.0
    
    # 建立請求
    request = PerformanceEngineRequest(
        dates=dates,
        portfolio_nav=nav,
        portfolio_returns=returns,
    )
    
    # 計算摘要
    engine = PerformanceEngine()
    summary = engine.compute_summary(request)
    
    print(f"Total Return: {summary.total_return:.2%}")
    print(f"CAGR: {summary.cagr:.2%}")
    print(f"Sharpe: {summary.sharpe:.2f}")
    print(f"Max Drawdown: {summary.max_drawdown:.2%}")
    
    # 驗證
    assert summary.total_return != 0
    assert summary.sharpe != 0
    
    return summary

if __name__ == "__main__":
    test_compute_summary_basic()
```

執行測試：

```bash
python3 tests/performance/test_basic.py
```

---

## 🎯 Editor 指令 6：整合到 Path A

### 檢查 Path A 如何使用 Performance Engine

```bash
# 查看 Path A 如何使用 Performance Engine
grep -r "performance\|Performance" jgod/path_a/ tests/path_a/ --include="*.py"

# 檢查 Path A backtest 結果結構
cat jgod/path_a/path_a_schema.py | grep -A 20 "class PathABacktestResult"
```

### Path A 整合範例

在 Path A 回測完成後，可以這樣使用 Performance Engine：

```python
from jgod.performance import PerformanceEngine, PerformanceEngineRequest
from jgod.path_a import PathABacktestResult

# Path A 回測完成後
backtest_result: PathABacktestResult = run_path_a_backtest(...)

# 建立 Performance Engine Request
request = PerformanceEngineRequest.from_path_a_result(
    backtest_result,
    benchmark_returns=benchmark_returns,  # 可選
    sector_map=sector_map,                # 可選
)

# 計算績效
engine = PerformanceEngine()
result = engine.compute_full_report(request)

# 輸出報表
print(f"Total Return: {result.summary.total_return:.2%}")
print(f"Sharpe Ratio: {result.summary.sharpe:.2f}")
print(f"Max Drawdown: {result.summary.max_drawdown:.2%}")

# 歸因分析
print("\nSymbol Attribution:")
print(result.attribution.by_symbol)

if result.attribution.by_sector is not None:
    print("\nSector Attribution:")
    print(result.attribution.by_sector)
```

---

## 🎯 Editor 指令 7：如何補齊 performance_metrics.py 的數學實作

### 檢查數學函式的實作

```bash
# 查看 performance_metrics.py 中的函式
grep -n "^def " jgod/performance/performance_metrics.py
```

### 補齊實作的重點

1. **CAGR 計算**：確保正確處理負報酬的情況
2. **Sharpe Ratio**：確保分母不為 0
3. **Max Drawdown**：使用累積最大值計算
4. **Hit Rate**：正確計算正報酬比例

---

## 🎯 Editor 指令 8：執行測試

### 執行 Performance Engine 測試

```bash
# 執行所有 Performance Engine 測試
pytest tests/performance/test_performance_engine_v1.py -v

# 執行特定測試
pytest tests/performance/test_performance_engine_v1.py::test_compute_summary_basic -v

# 執行並顯示輸出
pytest tests/performance/test_performance_engine_v1.py -v -s
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

- [x] 標準文件已建立：`docs/JGOD_PERFORMANCE_ENGINE_STANDARD_v1.md`
- [x] Spec 文件已建立：`spec/JGOD_PerformanceEngine_Spec.md`
- [x] 類型定義已建立：`jgod/performance/performance_types.py`
- [x] 績效指標已建立：`jgod/performance/performance_metrics.py`
- [x] 歸因引擎已建立：`jgod/performance/attribution_engine.py`
- [x] 測試骨架已建立：`tests/performance/test_performance_engine_v1.py`
- [x] Editor 指令包已建立：`docs/PERFORMANCE_ENGINE_EDITOR_INSTRUCTIONS.md`
- [x] `__init__.py` 已建立並導出新模組
- [ ] 所有檔案通過 Linter 檢查
- [ ] 基本功能測試通過
- [ ] 可以成功從 Path A 結果建立 Request

---

## 🚀 後續步驟

### 1. 補齊數學實作

- 確保所有 performance_metrics.py 中的函式都有正確的數學實作
- 處理邊界情況（例如：除零、負值等）

### 2. 擴充歸因分析

- 實作完整的 Brinson 歸因（包含 Interaction Effect）
- 實作更精確的 Symbol Attribution（需要標的的個別報酬）

### 3. 整合到 Path A

- 在 Path A 回測流程中整合 Performance Engine
- 自動生成績效報告

### 4. 擴充測試

- 補充完整的單元測試
- 建立整合測試

---

**版本**：v1.0  
**狀態**：✅ Editor 指令包已建立

