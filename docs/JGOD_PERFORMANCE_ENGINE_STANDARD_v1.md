# J-GOD Performance & Attribution Engine Standard v1

### Step 7 — 績效與歸因分析引擎標準規格

---

# 1. 模組定位與目標

## 1.1 模組名稱

**Performance & Attribution Engine v1**

## 1.2 主要任務

將 Path A / Execution Engine 產出的 NAV、交易、因子暴露，轉成「可閱讀的績效報告」。

**支援功能：**

- **Portfolio-level 績效統計**：累積報酬、CAGR、Sharpe Ratio、最大回落等
- **Sector / Symbol / Factor 歸因**：多層次績效分解
- **Timing vs Selection 分解**：簡化版 Brinson 歸因
- **專業報表生成**：CSV / Markdown 格式輸出

## 1.3 與現有模組的關係

### 輸入來源

- **PathABacktestResult**（Path A）
  - NAV 序列
  - Return 序列
  - Portfolio snapshots
  - Trade 列表

- **ExecutionEngine 產出**
  - Trade 物件列表
  - PortfolioState 序列

- **RiskModel**
  - 因子暴露（Factor exposures）
  - 因子報酬（Factor returns）

### 輸出用途

- **報表**：CSV / Markdown 格式的績效報告
- **ErrorLearningEngine**：提供「結果描述」作為錯誤分析的輸入
- **Path A 回測總結**：回測實驗的完整績效分析

---

# 2. 資料流（Data Flow）

## 2.1 資料流示意圖

```
┌─────────────────────────────────────────────────────────┐
│                 回測 / 實驗結果                          │
├─────────────────────────────────────────────────────────┤
│  • Daily NAV (portfolio_nav)                            │
│  • Daily portfolio returns                              │
│  • Benchmark returns (optional)                         │
│  • Daily holdings (PortfolioState)                      │
│  • Trades / Turnover                                    │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              風險與因子資料                              │
├─────────────────────────────────────────────────────────┤
│  • Daily factor returns                                 │
│  • Daily factor exposures (by portfolio)                │
│  • Sector / Industry mapping (by symbol)                │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│            Performance Engine                           │
├─────────────────────────────────────────────────────────┤
│  1. 計算績效指標                                        │
│     - Cumulative Return                                 │
│     - CAGR, Sharpe, Max Drawdown                        │
│     - Hit Rate, Calmar Ratio                            │
│                                                          │
│  2. 計算各層歸因                                        │
│     - Symbol Attribution                                │
│     - Sector Attribution (Brinson-style)                │
│     - Factor Attribution                                │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                    輸出                                  │
├─────────────────────────────────────────────────────────┤
│  • PerformanceSummary                                   │
│  • Breakdown by sector / symbol / factor                │
│  • AttributionReport (JSON / MD)                        │
└─────────────────────────────────────────────────────────┘
```

## 2.2 資料流程說明

### 輸入階段

1. **回測結果**：Path A 產生的 NAV、returns、holdings、trades
2. **風險資料**：Risk Model 提供的因子暴露和因子報酬
3. **市場資料**：Benchmark returns、sector mapping

### 處理階段

1. **績效計算**：從 NAV 和 returns 計算各種績效指標
2. **歸因分析**：將總報酬分解為不同來源（symbol、sector、factor）
3. **統計匯總**：生成績效摘要和診斷資訊

### 輸出階段

1. **PerformanceSummary**：高階績效指標
2. **AttributionReport**：詳細歸因報告
3. **報表檔案**：可匯出為 CSV / Markdown

---

# 3. 指標定義（Metrics）

## 3.1 Portfolio-level 指標

### 累積報酬（Cumulative Return）

\[
R_{\text{total}} = \frac{\text{NAV}_{\text{end}} - \text{NAV}_{\text{start}}}{\text{NAV}_{\text{start}}}
\]

### 年化報酬（CAGR）

\[
\text{CAGR} = \left(\frac{\text{NAV}_{\text{end}}}{\text{NAV}_{\text{start}}}\right)^{\frac{1}{T}} - 1
\]

其中 \(T\) 為年數。

### 年化波動度（Annualized Vol）

\[
\sigma_{\text{annual}} = \sigma_{\text{daily}} \times \sqrt{252}
\]

### Sharpe Ratio

\[
\text{Sharpe} = \frac{\bar{R} - R_f}{\sigma}
\]

其中：
- \(\bar{R}\)：平均日報酬率
- \(R_f\)：無風險利率（預設為 0）
- \(\sigma\)：日報酬標準差

### 最大回落（Max Drawdown）

\[
\text{MaxDD} = \max_t \left( \frac{\text{Peak}_t - \text{NAV}_t}{\text{Peak}_t} \right)
\]

其中 \(\text{Peak}_t\) 為時刻 t 之前的歷史最高 NAV。

### Calmar Ratio

\[
\text{Calmar} = \frac{\text{CAGR}}{|\text{MaxDD}|}
\]

### Hit Rate（勝率）

\[
\text{Hit Rate} = \frac{\text{正報酬日數}}{\text{總交易日數}}
\]

### Average Win / Average Loss

\[
\text{Avg Win} = \frac{\sum_{r>0} r}{N_{\text{win}}}
\]

\[
\text{Avg Loss} = \frac{\sum_{r<0} |r|}{N_{\text{loss}}}
\]

### Turnover（平均換手率）

\[
\text{Turnover} = \frac{1}{T} \sum_{t} \text{Turnover}_t
\]

其中 \(\text{Turnover}_t = \sum_i |w_{i,t} - w_{i,t-1}|\)

---

## 3.2 Benchmark / Relative 指標

### Active Return（主動報酬）

\[
R_{\text{active},t} = R_{\text{portfolio},t} - R_{\text{benchmark},t}
\]

### Tracking Error（追蹤誤差）

\[
\text{TE} = \sqrt{\text{Var}(R_{\text{active}})} \times \sqrt{252}
\]

### Information Ratio（資訊比率）

\[
\text{IR} = \frac{\bar{R}_{\text{active}}}{\text{TE}}
\]

---

## 3.3 Attribution 指標

### Symbol Attribution

**每檔股票的貢獻**：

\[
\text{Contribution}_i = \bar{w}_i \times R_i
\]

其中：
- \(\bar{w}_i\)：平均權重
- \(R_i\)：總期間報酬

### Sector Attribution（簡化 Brinson-style）

**Allocation Effect**：

\[
\text{Allocation}_j = (w_{j,\text{fund}} - w_{j,\text{bench}}) \times R_{j,\text{bench}}
\]

**Selection Effect**：

\[
\text{Selection}_j = w_{j,\text{bench}} \times (R_{j,\text{fund}} - R_{j,\text{bench}})
\]

**Total Effect**：

\[
\text{Total}_j = \text{Allocation}_j + \text{Selection}_j
\]

### Factor Attribution

**因子貢獻**：

\[
\text{Factor Contribution}_k = \bar{E}_k \times R_{k,\text{factor}}
\]

其中：
- \(\bar{E}_k\)：平均因子暴露
- \(R_{k,\text{factor}}\)：因子報酬

**特質收益（Residual）**：

\[
R_{\text{residual}} = R_{\text{total}} - \sum_k \text{Factor Contribution}_k
\]

---

# 4. Attribution 方法

## 4.1 Sector Attribution（簡化 Brinson-style）

### Allocation Effect（配置效應）

**定義**：由於多配或少配某個 Sector 而產生的貢獻。

\[
\text{Allocation}_j = (w_{j,\text{fund}} - w_{j,\text{bench}}) \times R_{j,\text{bench}}
\]

**解釋**：
- 如果基金在某 Sector 的權重高於基準，且該 Sector 表現良好，則產生正的配置效應
- 如果基金在某 Sector 的權重低於基準，且該 Sector 表現良好，則產生負的配置效應

### Selection Effect（選股效應）

**定義**：由於在 Sector 內的選股能力而產生的貢獻。

\[
\text{Selection}_j = w_{j,\text{bench}} \times (R_{j,\text{fund}} - R_{j,\text{bench}})
\]

**解釋**：
- 如果基金在 Sector 內的選股表現優於基準，則產生正的選股效應
- 反之則為負

### Interaction Effect（交互效應）

**定義**：配置和選股效應的交互影響。

\[
\text{Interaction}_j = (w_{j,\text{fund}} - w_{j,\text{bench}}) \times (R_{j,\text{fund}} - R_{j,\text{bench}})
\]

**v1 處理方式**：
- 可選擇忽略（合併到 Selection Effect）
- 或獨立計算

---

## 4.2 Factor Attribution

### 因子暴露計算

使用 Risk Model 提供的因子暴露矩陣：

\[
E_{k,t} = \sum_i w_{i,t} \times B_{i,k}
\]

其中：
- \(w_{i,t}\)：時刻 t 標的 i 的權重
- \(B_{i,k}\)：標的 i 在因子 k 的暴露

### 因子報酬計算

使用 Risk Model 提供的因子報酬序列：

\[
R_{k,\text{factor},t} = \text{Factor Return}_{k,t}
\]

### 因子貢獻計算

\[
\text{Factor Contribution}_k = \sum_t \bar{E}_{k,t} \times R_{k,\text{factor},t}
\]

或使用平均暴露：

\[
\text{Factor Contribution}_k = \bar{E}_k \times \sum_t R_{k,\text{factor},t}
\]

### 特質收益（Residual）

\[
R_{\text{residual}} = R_{\text{total}} - \sum_k \text{Factor Contribution}_k
\]

---

# 5. Required Inputs & Outputs

## 5.1 Inputs

### PerformanceEngineRequest

```python
@dataclass
class PerformanceEngineRequest:
    # 時間序列
    dates: Sequence[pd.Timestamp]
    
    # Portfolio 績效
    portfolio_nav: pd.Series  # indexed by date
    portfolio_returns: pd.Series  # indexed by date
    
    # Benchmark（可選）
    benchmark_nav: Optional[pd.Series] = None
    benchmark_returns: Optional[pd.Series] = None
    
    # Holdings
    weights_by_date: Dict[date, pd.Series]  # {date: {symbol: weight}}
    
    # Trades
    trades_by_date: Dict[date, List[Trade]]  # {date: [Trade, ...]}
    
    # Factor data（可選）
    factor_returns: Optional[pd.DataFrame] = None  # columns = factor
    factor_exposures_by_date: Optional[Dict[date, pd.Series]] = None
    
    # Sector mapping
    sector_map: Optional[Dict[str, str]] = None  # {symbol: sector}
    
    # Config
    config: Dict[str, Any] = None  # window, periods_per_year, etc.
```

---

## 5.2 Outputs

### PerformanceSummary

```python
@dataclass
class PerformanceSummary:
    # Portfolio-level
    total_return: float
    cagr: float
    vol_annualized: float
    sharpe: float
    max_drawdown: float
    calmar: float
    hit_rate: float
    avg_win: float
    avg_loss: float
    turnover_annualized: float
    
    # Benchmark / Relative
    active_return: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None
```

### AttributionReport

```python
@dataclass
class AttributionReport:
    # Symbol-level
    by_symbol: pd.DataFrame
    # columns: [symbol, return_contrib, weight_avg, sector, ...]
    
    # Sector-level
    by_sector: pd.DataFrame
    # columns: [sector, allocation_effect, selection_effect, total_effect]
    
    # Factor-level
    by_factor: pd.DataFrame
    # columns: [factor, factor_return, factor_contribution, exposure_avg]
    
    residual: float  # 非解釋部分
```

---

# 6. 實作架構

## 6.1 模組結構

```
jgod/performance/
├── __init__.py
├── performance_types.py      # 資料結構定義
├── performance_metrics.py    # 純績效指標計算
└── attribution_engine.py     # 歸因分析和主要引擎
```

## 6.2 設計原則

- **模組化設計**：績效計算與歸因分析分離
- **協議導向**：使用 Protocol 定義介面
- **可測試性**：所有函式都可以獨立測試
- **可擴展性**：預留未來擴充介面（例如：更複雜的歸因方法）

---

# 7. Integration with Path A

## 7.1 Path A 整合點

Performance Engine 在 Path A 回測流程中的角色：

```
Path A Backtest Loop:
  1. Alpha Engine → expected returns
  2. Risk Model → covariance matrix
  3. Optimizer → target weights w*
  4. Execution Engine → executes trades
  5. Update portfolio → calculate returns
  6. Performance Engine → analyze performance
```

## 7.2 使用範例

```python
from jgod.performance import PerformanceEngine
from jgod.path_a import PathABacktestResult

# Path A 回測完成後
backtest_result = run_path_a_backtest(...)

# 建立 Performance Engine Request
request = PerformanceEngineRequest.from_path_a_result(backtest_result)

# 計算績效
performance_engine = PerformanceEngine()
summary = performance_engine.compute_summary(request)
attribution = performance_engine.compute_attribution(request)

# 輸出報表
print(f"Total Return: {summary.total_return:.2%}")
print(f"Sharpe Ratio: {summary.sharpe:.2f}")
print(f"Max Drawdown: {summary.max_drawdown:.2%}")
```

---

# 8. Implementation Notes

## 8.1 實作優先順序

### 必須實作（Must Have）

1. **基礎績效指標**：CAGR, Sharpe, Max Drawdown, Hit Rate
2. **Symbol Attribution**：每檔股票的貢獻
3. **Sector Attribution**：簡化版 Brinson 歸因

### 建議實作（Should Have）

1. **Benchmark Comparison**：Active Return, Tracking Error, IR
2. **Factor Attribution**：因子貢獻分解

### 可選實作（Nice to Have）

1. **更複雜的歸因方法**：完整 Brinson 歸因（包含 Interaction）
2. **時間序列分析**：滾動視窗績效
3. **視覺化輸出**：圖表生成

## 8.2 錯誤處理

- **缺失資料處理**：對缺失的 benchmark 或 factor 資料進行適當處理
- **除零錯誤**：確保所有除法操作都有適當的檢查
- **資料驗證**：驗證輸入資料的格式和完整性

---

**版本**：v1.0  
**最後更新**：2025-12-02  
**狀態**：✅ 標準規範已確立

