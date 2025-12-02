# J-GOD Path B Standard v1

## 📋 概述

Path B Engine 是 J-GOD 系統中用於執行 **In-Sample / Out-of-Sample 測試**與 **Walk-Forward Analysis** 的核心引擎。Path B 的目的是嚴格驗證策略是否在未來世界能存活，避免資料窺探偏差，並提供策略穩定性的客觀評估。

---

## 🎯 Path A vs Path B 的差別

### Path A: Validation Lab（驗證實驗室）

**目的**:
- 快速原型開發與策略驗證
- 單一時間範圍的回測
- 找出有潛力的策略方向

**特點**:
- 使用全部歷史資料進行回測
- 適合探索性分析
- 快速迭代與測試

**產出**:
- 單一回測結果
- 績效報告、風險分析
- 診斷報告與修復建議

### Path B: Production Readiness Test（生產就緒測試）

**目的**:
- 嚴格驗證策略穩定性
- 模擬真實部署環境
- 評估策略在未來世界的表現

**特點**:
- 採用 Walk-Forward Analysis
- 分割訓練集與測試集
- 多 window 一致性評估

**產出**:
- 多 window 測試結果
- Alpha Stability Report
- Governance Rule 觸發分析

### 對照表

| 面向 | Path A | Path B |
|------|--------|--------|
| **資料使用** | 全部歷史資料 | 分割 Train/Test |
| **時間範圍** | 單一連續範圍 | 多個滾動 Window |
| **評估重點** | 策略潛力 | 策略穩定性 |
| **主要風險** | 資料窺探 | 過度優化 |
| **適用階段** | 開發階段 | 上線前驗證 |

---

## 🎯 Path B 的目的：驗證策略是否在未來世界能存活

### 核心問題

在策略開發過程中，最關鍵的問題是：

> **「這個策略在未來還能有效嗎？」**

Path B 透過以下機制回答這個問題：

### 1. Out-of-Sample Testing

- 將資料分割為訓練集（In-Sample）與測試集（Out-of-Sample）
- 在訓練集上優化策略
- 在測試集上驗證策略表現
- **核心假設**: 如果策略在測試集上表現良好，則較可能在未來有效

### 2. Walk-Forward Analysis

- 採用滾動視窗方式進行多次訓練/測試
- 每個 window 都是獨立的實驗
- 評估策略在不同市場環境下的穩定性
- **核心假設**: 如果策略在多個 window 中都表現穩定，則較可能在不同市場環境下有效

### 3. Consistency Metrics

- 計算跨 window 的一致性（例如 Sharpe 標準差）
- 評估策略表現的穩定性
- 識別過度優化的策略

---

## 🔗 Path B 與 Step 6 的結合方式

Path B 與 J-GOD Step 6（Governance Rules）緊密整合，在 Walk-Forward Analysis 中模擬各種治理規則的觸發與影響。

### Walk-Forward 中如何測 Alpha Sunset

**Alpha Sunset** 是當 Alpha 衰減到一定程度時，自動停用策略的機制。

在 Path B 中：

1. **每個 Window 的 Test 階段**:
   - 計算 Alpha 在測試期的衰減率
   - 比較訓練期與測試期的 Alpha 表現
   - 如果衰減超過閾值，觸發 Alpha Sunset

2. **觸發記錄**:
   - 記錄觸發日期
   - 記錄觸發時的市場環境（volatility、regime 等）
   - 分析觸發後的表現影響

3. **跨 Window 分析**:
   - 統計各 window 的 Alpha Sunset 觸發頻率
   - 識別容易觸發的市場環境
   - 評估 Alpha Sunset 規則的有效性

### Walk-Forward 中如何測 Regime Switch

**Regime Switch** 是當市場環境變化時，自動調整策略參數的機制。

在 Path B 中：

1. **每個 Window**:
   - 檢測 Train 與 Test 階段的市場環境變化
   - 識別 Regime 切換事件
   - 評估 Regime Switch 規則的觸發時機

2. **Regime Detection**:
   - 使用 volatility、momentum 等指標
   - 分類為低波動、正常、高波動等 regime
   - 記錄各 window 的 regime 分布

3. **策略調整**:
   - 模擬 Regime Switch 觸發後的策略參數調整
   - 比較調整前後的表現差異
   - 評估 Regime Switch 規則的有效性

### Walk-Forward 中如何測 Kill Switch

**Kill Switch** 是當風險指標超過閾值時，立即停止交易的機制。

在 Path B 中：

1. **每個 Window 的 Test 階段**:
   - 監控最大回落、Sharpe Ratio 等風險指標
   - 如果超過閾值，觸發 Kill Switch
   - 記錄觸發日期與觸發原因

2. **觸發分析**:
   - 分析觸發前的市場特徵
   - 評估觸發後的損失控制效果
   - 比較有/無 Kill Switch 的表現差異

3. **跨 Window 統計**:
   - 統計各 window 的 Kill Switch 觸發次數
   - 識別容易觸發的市場條件
   - 優化 Kill Switch 參數設定

---

## 📊 Path B 的產出報告格式

### 1. 每 Window 的績效報告

**CSV 格式** (`window_results.csv`):

```csv
window_id,train_start,train_end,test_start,test_end,sharpe,max_drawdown,total_return,turnover_rate,tracking_error,information_ratio
1,2023-01-01,2023-06-30,2023-07-01,2023-12-31,1.25,-0.15,0.18,0.45,0.08,0.75
2,2023-02-01,2023-07-31,2023-08-01,2024-01-31,1.10,-0.18,0.15,0.50,0.09,0.65
...
```

**JSON 格式** (`window_results.json`):

```json
{
  "window_results": [
    {
      "window_id": 1,
      "train_start": "2023-01-01",
      "train_end": "2023-06-30",
      "test_start": "2023-07-01",
      "test_end": "2023-12-31",
      "sharpe": 1.25,
      "max_drawdown": -0.15,
      "total_return": 0.18,
      "turnover_rate": 0.45,
      "tracking_error": 0.08,
      "information_ratio": 0.75
    }
  ]
}
```

### 2. Governance Rule 觸發紀錄

**CSV 格式** (`governance_events.csv`):

```csv
window_id,rule_name,triggered,trigger_date,trigger_reason
1,alpha_sunset,True,2023-10-15,alpha_decay:0.52
1,kill_switch,False,,
2,regime_switch,True,2023-09-20,regime:high_volatility
...
```

### 3. Alpha Stability Report

**Markdown 格式** (`alpha_stability_report.md`):

```markdown
# Alpha Stability Report

## Summary Statistics

- Average Sharpe Ratio: 1.18
- Sharpe Ratio Std Dev: 0.12
- Consistency Score: 0.85

## Window-by-Window Analysis

### Window 1 (2023-01-01 to 2023-12-31)
- Sharpe: 1.25
- Max DD: -0.15
- ...

## Governance Rule Analysis

### Alpha Sunset
- Triggered: 3 times
- Average trigger date: Day 45 of test period
- Impact: -2.3% return reduction

### Kill Switch
- Triggered: 1 time
- Prevented: -5.2% additional loss
```

### 4. Regime 分析

**CSV 格式** (`regime_analysis.csv`):

```csv
window_id,test_period,regime,volatility_level,sharpe,max_drawdown
1,2023-07-01 to 2023-12-31,normal,0.02,1.25,-0.15
2,2023-08-01 to 2024-01-31,high,0.04,0.95,-0.22
...
```

### 5. 滑價 / Beta 更新分析

**CSV 格式** (`slippage_beta_analysis.csv`):

```csv
window_id,avg_slippage_bps,avg_turnover,beta_stability_score,beta_update_frequency
1,5.2,0.45,0.92,monthly
2,6.1,0.50,0.88,monthly
...
```

---

## 🔄 執行流程

### 完整流程圖

```
1. Window 切割
   ↓
2. For each window:
   ├─ Train 階段（IS）
   │   └─ 策略優化
   │
   ├─ Test 階段（OOS）
   │   ├─ 執行回測
   │   ├─ 計算績效
   │   └─ 因子歸因
   │
   └─ Governance Rules
       ├─ Alpha Sunset 檢測
       ├─ Regime Switch 檢測
       └─ Kill Switch 檢測
   ↓
3. Combine & Export
   ├─ 跨 window 統計
   ├─ Alpha Stability 分析
   ├─ Governance 分析
   └─ 生成報告
```

---

---

## 🔄 目前在 J-GOD 中的使用方式

### 目前支援功能（Step B2）

Path B Engine 目前實作了 **最小可用版本**，可以執行：

1. **多 Window Walk-Forward Backtest**
   - 自動切割 train/test windows
   - 對每個 window 執行 Path A backtest
   - 收集所有 window 的績效統計

2. **基本績效指標收集**
   - Sharpe Ratio
   - Maximum Drawdown
   - Total Return
   - Turnover Rate

3. **跨 Window 一致性分析**
   - 平均績效指標
   - 標準差（穩定性）
   - 基本彙總統計

### 使用範例

```python
from jgod.path_b.path_b_engine import PathBEngine, PathBConfig

# 建立 Path B Engine
engine = PathBEngine()

# 建立配置
config = PathBConfig(
    train_start="2024-01-01",
    train_end="2024-06-30",
    test_start="2024-07-01",
    test_end="2024-12-31",
    walkforward_window="6m",
    walkforward_step="1m",
    universe=["2330.TW", "2317.TW"],
    rebalance_frequency="M",
    alpha_config_set=[],
    data_source="mock",
    mode="basic",
)

# 執行 Walk-Forward Analysis
result = engine.run(config)

# 查看結果
print(f"Number of windows: {result.summary['num_windows']}")
print(f"Average Sharpe: {result.summary.get('avg_sharpe', 'N/A')}")

for window_result in result.window_results:
    print(f"Window {window_result.window_id}: "
          f"Sharpe={window_result.sharpe_ratio:.2f}, "
          f"DD={window_result.max_drawdown:.2%}")
```

### 之後延伸（Step B3+）

- **Alpha Sunset / Regime / Kill Switch 模擬**
- **完整的 Train 階段策略優化**
- **因子歸因分析**
- **詳細的報告生成**

---

## 🛡️ Governance & Kill-Switch Simulation via Path B

Path B 每個 window 會套用 Step 6 的核心治理規則，可以統計與模擬治理規則在不同市場視窗下的觸發頻率。

### 基礎治理規則

Path B 目前實作以下基礎治理規則（參考 Step 6 V2.1）：

1. **MAX_DRAWDOWN_BREACH**
   - 條件：`max_drawdown <= max_drawdown_threshold`
   - 預設門檻：-15%
   - 用途：偵測過大的回撤風險

2. **SHARPE_TOO_LOW**
   - 條件：`sharpe < sharpe_threshold`
   - 預設門檻：2.0
   - 用途：偵測風險調整後報酬不足

3. **TE_BREACH**
   - 條件：`tracking_error > tracking_error_max`
   - 預設門檻：4%
   - 用途：偵測追蹤誤差過大

4. **TURNOVER_TOO_HIGH**
   - 條件：`turnover > turnover_max`
   - 預設門檻：100%
   - 用途：偵測過度交易

### Governance 統計功能

Path B 可以統計：

- **有多少個 window 會觸發 kill-switch 類型條件**
  - 透過 `governance_summary.windows_with_any_breach` 取得
  
- **哪些 rule 最常被觸發**
  - 透過 `governance_summary.rule_hit_counts` 取得
  - 例如：`{"MAX_DRAWDOWN_BREACH": 3, "SHARPE_TOO_LOW": 5}`

- **整體 Sharpe / DD 在多視窗下的穩定度**
  - 透過 `governance_summary.global_metrics` 取得
  - 包含：`avg_sharpe`, `avg_max_drawdown`, `avg_tracking_error` 等

- **最多連續多少個 window 都觸發了 rule**
  - 透過 `governance_summary.max_consecutive_breach_windows` 取得
  - 用於評估策略是否在特定市場環境下持續失效

### 使用範例

```python
from jgod.path_b.path_b_engine import PathBEngine, PathBConfig

engine = PathBEngine()

config = PathBConfig(
    train_start="2024-01-01",
    train_end="2024-06-30",
    test_start="2024-07-01",
    test_end="2024-12-31",
    walkforward_window="6m",
    walkforward_step="1m",
    universe=["2330.TW", "2317.TW"],
    rebalance_frequency="M",
    # Governance 門檻設定
    max_drawdown_threshold=-0.15,  # -15%
    sharpe_threshold=2.0,
    tracking_error_max=0.04,  # 4%
    turnover_max=1.0,  # 100%
)

result = engine.run(config)

# 查看 governance 結果
print(f"總 window 數：{result.governance_summary.total_windows}")
print(f"觸發 breach 的 window 數：{result.governance_summary.windows_with_any_breach}")
print(f"規則觸發次數：{result.governance_summary.rule_hit_counts}")
print(f"最多連續 breach window 數：{result.governance_summary.max_consecutive_breach_windows}")

# 查看每個 window 的 governance 結果
for window_gov in result.windows_governance:
    if window_gov.rules_triggered:
        print(f"Window {window_gov.window_id} 觸發規則：{window_gov.rules_triggered}")
```

### 未來擴充

Step B3+ 將加入：
- **Alpha IC / Alpha Sunset**：監控 Alpha 衰減
- **Regime/Stress hits**：市場環境變化檢測
- **Kill switch 模擬**：完整風險控制機制

---

## 📚 相關文件

- `spec/JGOD_PathBEngine_Spec.md` - Path B Engine 規格文件
- `docs/JGOD_PATHA_STANDARD_v1.md` - Path A 標準文件

