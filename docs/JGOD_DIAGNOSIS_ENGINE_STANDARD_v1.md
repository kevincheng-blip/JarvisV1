# J-GOD Diagnosis & Repair Engine Standard v1

### Step 8 — 系統級診斷與修復規劃引擎標準規格

---

# 1. 模組定位與目標

## 1.1 模組名稱

**Diagnosis & Repair Engine v1**

## 1.2 主要任務

站在 Path A / Execution / Performance 上面，做「總體健康檢查 + 問題分類 + 修復建議」。

**核心功能：**

1. **收集全系統訊號**
   - Path A 回測結果
   - Execution Engine 交易成本、成交率、Turnover
   - Performance Engine 績效指標（Sharpe、Max Drawdown、IR、TE）
   - Optimizer 約束是否被頻繁卡住
   - Risk Model 因子暴露是否超標

2. **統一診斷事件**
   - 將「問題」轉換為標準的 `DiagnosticEvent` 格式
   - 分類問題類型、嚴重度、來源模組

3. **橋接到 ErrorLearningEngine**
   - 將某些 `DiagnosticEvent` 轉為 `ErrorEvent`
   - 對應 KNOWLEDGE_GAP、FORM_INSUFFICIENT、UTILIZATION_GAP

4. **產生修復建議**
   - 不直接改 code，只輸出 `RepairPlan`（建議）
   - 建議調整哪些 config、檢討哪些因子/策略

## 1.3 在整個 J-GOD 系統中的位置

```
┌─────────────────────────────────────────────────────────┐
│                    J-GOD System Flow                     │
└─────────────────────────────────────────────────────────┘

Path A Backtest
  ↓
Execution Engine → Trades, Fills, Costs
  ↓
Performance Engine → Metrics, Attribution
  ↓
┌─────────────────────────────────────────────────────────┐
│         Diagnosis & Repair Engine (Step 8)              │
│  • Collects signals from all modules                   │
│  • Generates DiagnosticEvents                          │
│  • Bridges to ErrorLearningEngine                      │
│  • Produces RepairPlan                                 │
└──────────────────┬──────────────────────────────────────┘
                   ↓
ErrorLearningEngine → Analyzes errors, generates knowledge
  ↓
Knowledge Brain → Stores learned rules/concepts
```

## 1.4 與其他模組的關係

### 輸入來源

- **PathABacktestResult**（Path A）
  - NAV 序列、Return 序列
  - Portfolio snapshots
  - Trade 列表

- **ExecutionEngine**
  - 交易成本統計
  - 成交率
  - Turnover

- **PerformanceEngine**
  - PerformanceSummary（Sharpe、Max Drawdown、IR、TE）
  - AttributionReport

- **Optimizer v2**
  - 約束違反統計
  - Infeasible 次數
  - Corner solutions

- **RiskModel**
  - 因子暴露歷史
  - 超標次數

### 輸出用途

- **ErrorLearningEngine**：提供 `ErrorEvent` 供分析
- **修復建議**：`RepairPlan` 供人類或系統參考
- **系統健康報告**：`SystemHealthSnapshot` 供監控

---

# 2. 資料流（Data Flow）

## 2.1 完整流程示意圖

```
┌─────────────────────────────────────────────────────────┐
│              Path A Backtest Result                      │
│  • nav_series, return_series                            │
│  • portfolio_snapshots                                  │
│  • trades                                               │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│          Execution Engine Results                        │
│  • transaction_costs                                    │
│  • turnover                                             │
│  • fills                                                │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│        Performance Engine Results                        │
│  • PerformanceSummary (Sharpe, MaxDD, IR, TE)          │
│  • AttributionReport                                    │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│           Optimizer / Risk Model Signals                 │
│  • constraint violations                                │
│  • factor exposure overruns                             │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│         Diagnosis Engine (Step 8)                        │
│                                                          │
│  1. Collect all signals                                 │
│  2. Generate DiagnosticEvents                           │
│  3. Analyze constraints                                 │
│  4. Analyze performance                                 │
│  5. Bridge to ErrorLearningEngine                       │
│  6. Build RepairPlan                                    │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐  ┌─────────▼────────────┐
│ ErrorLearning  │  │   RepairPlan         │
│    Engine      │  │   • Config changes   │
│  • ErrorEvent  │  │   • Factor reviews   │
│  • Analysis    │  │   • Priority actions │
└────────────────┘  └──────────────────────┘
        │
┌───────▼────────┐
│ Knowledge Brain│
│  • Rules       │
│  • Concepts    │
└────────────────┘
```

## 2.2 資料流程說明

### 階段 1：資料收集

1. **Path A 結果**：從 `PathABacktestResult` 取得 NAV、returns、snapshots、trades
2. **Execution 統計**：從 Execution Engine 取得成本、turnover 統計
3. **Performance 指標**：從 Performance Engine 取得完整績效摘要和歸因
4. **Optimizer / Risk 訊號**：從 Optimizer 和 Risk Model 取得約束違反和暴露資料

### 階段 2：診斷分析

1. **約束分析**：檢查 TE、Turnover、Sector/Factor 暴露是否頻繁超標
2. **績效分析**：根據 Sharpe、Max Drawdown、IR 判斷績效問題
3. **問題分類**：將問題轉換為 `DiagnosticEvent`

### 階段 3：錯誤橋接

1. **轉換為 ErrorEvent**：將符合條件的 `DiagnosticEvent` 轉為 `ErrorEvent`
2. **傳送給 ErrorLearningEngine**：讓 ErrorLearningEngine 分析錯誤

### 階段 4：修復規劃

1. **產生 RepairPlan**：根據診斷結果產生修復建議
2. **優先級排序**：標記高優先級行動

---

# 3. 指標門檻建議

## 3.1 Tracking Error 門檻

| 策略模式 | 建議 TE_max | 說明 |
|---------|-----------|------|
| 保守模式 | 3% | 低偏離、穩定追蹤基準 |
| 標準 Alpha 模式 | 4-5% | 平衡 Alpha 與追蹤 |
| 雙核心 Alpha 模式 | 5-8% | 高 Alpha、允許較大偏離 |

**診斷規則**：
- 如果 TE 經常 > TE_max → 觸發 `TE_EXCEEDED` DiagnosticEvent
- 如果 TE < TE_max/2 且 Sharpe < 0.5 → 可能 Alpha 不足

## 3.2 Turnover 門檻

| 策略類型 | 建議 T_max | 說明 |
|---------|-----------|------|
| 長期持有 | 0.10 (10%) | 低換手率 |
| 標準再平衡 | 0.20 (20%) | 月度/週度再平衡 |
| 高頻策略 | 0.50 (50%) | 高頻交易（v1 不支援） |

**診斷規則**：
- 如果 Turnover 經常 > T_max → 觸發 `TURNOVER_TOO_HIGH` DiagnosticEvent
- 如果 Turnover 過高且成本率 > 1% → 建議降低換手

## 3.3 最大回落門檻

| 風險等級 | 建議 MaxDD 門檻 | 說明 |
|---------|---------------|------|
| 低風險 | -0.10 (-10%) | 保守策略 |
| 中風險 | -0.15 (-15%) | 標準策略 |
| 高風險 | -0.20 (-20%) | 激進策略 |

**診斷規則**：
- 如果 MaxDD < -0.20 → 觸發 `DRAWDOWN_EXCEEDED` DiagnosticEvent
- 如果 MaxDD 大但 Sharpe > 1.0 → 可能需要風險控制優化

## 3.4 績效指標門檻

| 指標 | 良好 | 一般 | 不佳 |
|------|------|------|------|
| Sharpe Ratio | > 1.0 | 0.5 - 1.0 | < 0.5 |
| Information Ratio | > 0.5 | 0.2 - 0.5 | < 0.2 |
| Hit Rate | > 0.55 | 0.50 - 0.55 | < 0.50 |

**診斷規則**：
- 如果 Sharpe < 0.5 且 MaxDD < -0.2 且 TE < TE_max/2 → 懷疑 Alpha 不足

---

# 4. 診斷規則示例

## 4.1 Alpha 不足檢測

**條件**：
- Sharpe Ratio < 0.5
- Max Drawdown < -0.2
- Tracking Error < TE_max / 2（表示沒有主動偏離，可能是 Alpha 不足）

**診斷事件**：
```python
DiagnosticEvent(
    source_module="PERFORMANCE",
    issue_type="ALPHA_UNDERPERFORM",
    severity="WARN",
    message="Sharpe Ratio 偏低，可能 Alpha 不足",
    ...
)
```

**修復建議**：
- 檢討 Alpha Engine 的因子選擇
- 考慮增加新的 Alpha 因子
- 檢視 Alpha 訊號的預測能力

## 4.2 約束頻繁違反檢測

**條件**：
- TE 經常 > TE_max（例如：> 50% 的時間）
- Turnover 經常 > T_max
- Factor exposure 頻繁 hitting boundary

**診斷事件**：
```python
DiagnosticEvent(
    source_module="OPTIMIZER",
    issue_type="CONSTRAINT_VIOLATION",
    severity="WARN",
    message="Tracking Error 頻繁超過上限",
    ...
)
```

**修復建議**：
- 調整 TE_max（如果策略性質允許）
- 檢討 Optimizer 的約束設定
- 考慮放寬某些約束或加強其他約束

## 4.3 風險控制問題檢測

**條件**：
- Max Drawdown < -0.25（嚴重虧損）
- Sharpe Ratio < 0（負報酬）

**診斷事件**：
```python
DiagnosticEvent(
    source_module="PERFORMANCE",
    issue_type="RISK_CONTROL_FAILED",
    severity="CRITICAL",
    message="最大回落超過門檻，風險控制失效",
    ...
)
```

**修復建議**：
- 加強風險控制規則
- 檢討停損機制
- 檢視是否有風控規則未執行

---

# 5. RepairPlan 產出原則

## 5.1 不直接改程式

**原則**：Diagnosis Engine 只產生建議，不直接修改程式碼或配置。

**輸出格式**：`RepairPlan` 包含：
- `RepairAction` 列表
- 每個 Action 包含：action_type、target_module、proposed_changes、priority

## 5.2 修復行動類型

### TUNE_CONFIG

**說明**：調整配置參數

**範例**：
```python
RepairAction(
    action_type="TUNE_CONFIG",
    target_module="OPTIMIZER",
    description="調整 Tracking Error 上限",
    proposed_changes={"optimizer.params.TE_max": 0.06},
    priority="MEDIUM"
)
```

### CHECK_DATA

**說明**：檢查資料品質

**範例**：
```python
RepairAction(
    action_type="CHECK_DATA",
    target_module="PATH_A",
    description="檢查因子資料的完整性和準確性",
    proposed_changes={},
    priority="HIGH"
)
```

### REVIEW_RULES

**說明**：檢討交易規則

**範例**：
```python
RepairAction(
    action_type="REVIEW_RULES",
    target_module="ALPHA_ENGINE",
    description="檢討 Alpha 因子選擇和權重",
    proposed_changes={},
    priority="HIGH"
)
```

### ADJUST_FACTOR_WEIGHT

**說明**：調整因子權重

**範例**：
```python
RepairAction(
    action_type="ADJUST_FACTOR_WEIGHT",
    target_module="ALPHA_ENGINE",
    description="調整特定因子的權重",
    proposed_changes={"factor_weights.FLOW": 0.3},
    priority="MEDIUM"
)
```

### RELAX_CONSTRAINT

**說明**：放寬約束

**範例**：
```python
RepairAction(
    action_type="RELAX_CONSTRAINT",
    target_module="OPTIMIZER",
    description="放寬 Sector 暴露限制",
    proposed_changes={"optimizer.params.sector_limits.TECH": 0.25},
    priority="LOW"
)
```

---

# 6. ErrorLearningEngine 橋接

## 6.1 DiagnosticEvent → ErrorEvent 轉換

### 轉換規則

| DiagnosticEvent.issue_type | ErrorEvent 分類 | 說明 |
|---------------------------|----------------|------|
| ALPHA_UNDERPERFORM + 知識不足 | KNOWLEDGE_GAP | 沒有足夠的 Alpha 知識 |
| ALPHA_UNDERPERFORM + 規則不足 | FORM_INSUFFICIENT | 只有概念，缺少可執行規則 |
| RISK_CONTROL_FAILED + 規則未用 | UTILIZATION_GAP | 風控規則存在但未執行 |
| CONSTRAINT_VIOLATION + 規則未用 | UTILIZATION_GAP | 約束規則存在但未執行 |

### 轉換方法

```python
def _bridge_to_error_engine(
    self,
    diagnostic_event: DiagnosticEvent
) -> Optional[ErrorEvent]:
    """將 DiagnosticEvent 轉換為 ErrorEvent"""
    
    # 判斷是否應轉換
    if diagnostic_event.severity == "INFO":
        return None  # INFO 級別不轉換
    
    # 建立 ErrorEvent
    error_event = ErrorEvent(
        id=f"err_{diagnostic_event.id}",
        timestamp=diagnostic_event.timestamp,
        symbol=diagnostic_event.related_symbols[0] if diagnostic_event.related_symbols else "PORTFOLIO",
        timeframe="1d",
        predicted_outcome=diagnostic_event.message,
        actual_outcome="",  # 系統級問題，沒有具體交易結果
        error_type=diagnostic_event.issue_type,
        tags=diagnostic_event.tags,
        context={"source_module": diagnostic_event.source_module},
    )
    
    return error_event
```

---

# 7. 診斷流程（7 Steps）

## Step 1: 收集系統訊號

從 Path A、Execution、Performance、Optimizer、Risk Model 收集所有訊號。

## Step 2: 建立 SystemHealthSnapshot

計算總體健康指標：
- Total Return、CAGR、Sharpe、Max Drawdown
- Tracking Error、Turnover
- 約束違反統計
- Error Event 計數

## Step 3: 約束分析

檢查：
- TE 是否經常超過上限
- Turnover 是否過高
- Sector/Factor 暴露是否頻繁 hitting boundary

## Step 4: 績效分析

根據績效指標判斷問題：
- Alpha 是否不足
- 風險控制是否失效
- 策略是否匹配市場環境

## Step 5: 生成 DiagnosticEvents

將問題轉換為標準的 `DiagnosticEvent` 格式。

## Step 6: 橋接到 ErrorLearningEngine

將符合條件的 `DiagnosticEvent` 轉為 `ErrorEvent` 並送給 ErrorLearningEngine。

## Step 7: 產生 RepairPlan

根據診斷結果產生修復建議，包含：
- 配置調整建議
- 因子/策略檢討建議
- 優先級排序

---

# 8. Required Inputs & Outputs

## 8.1 Inputs

### DiagnosisEngineRequest

```python
@dataclass
class DiagnosisEngineRequest:
    # Path A 結果
    backtest_result: PathABacktestResult
    
    # Performance 結果
    performance_result: PerformanceEngineResult
    
    # Execution 統計（可選）
    execution_stats: Optional[Dict[str, Any]] = None
    
    # Optimizer / Risk 訊號（可選）
    optimizer_stats: Optional[Dict[str, Any]] = None
    
    # Config
    config: Dict[str, Any] = None  # TE_max, T_max, thresholds, etc.
```

## 8.2 Outputs

### DiagnosisEngineResult

```python
@dataclass
class DiagnosisEngineResult:
    health: SystemHealthSnapshot
    diagnostic_events: List[DiagnosticEvent]
    repair_plan: RepairPlan
```

---

# 9. Implementation Notes

## 9.1 設計原則

- **不可修改現有模組介面**：只使用現有模組的輸出，不修改其介面
- **只產生建議**：不直接改 code 或 config，只輸出 RepairPlan
- **所有參數可設定**：所有門檻值都從 config 讀取，不寫死
- **模組化設計**：診斷邏輯與修復規劃分離

## 9.2 錯誤處理

- **缺失資料處理**：對缺失的資料進行適當處理（標記為 INFO 或跳過）
- **異常檢測**：檢測異常的指標值並標記
- **日誌記錄**：記錄所有診斷過程

---

**版本**：v1.0  
**最後更新**：2025-12-02  
**狀態**：✅ 標準規範已確立

