# JGOD Performance Engine Spec v1

## 1. PerformanceEngineRequest Schema（輸入）

```python
@dataclass
class PerformanceEngineRequest:
    """Performance Engine 輸入請求資料結構"""
    
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
    factor_returns: Optional[pd.DataFrame] = None  # columns = factor, indexed by date
    factor_exposures_by_date: Optional[Dict[date, pd.Series]] = None  # {date: {factor: exposure}}
    
    # Sector mapping
    sector_map: Optional[Dict[str, str]] = None  # {symbol: sector}
    
    # Config
    config: Dict[str, Any] = None  # window, periods_per_year, risk_free_rate, etc.
```

### 參數說明

- `dates`: 時間序列索引
- `portfolio_nav`: 投資組合淨值序列（以日期為索引）
- `portfolio_returns`: 投資組合報酬序列（以日期為索引）
- `benchmark_nav`: 基準淨值序列（可選）
- `benchmark_returns`: 基準報酬序列（可選）
- `weights_by_date`: 每個日期的權重字典
- `trades_by_date`: 每個日期的交易列表
- `factor_returns`: 因子報酬 DataFrame（可選）
- `factor_exposures_by_date`: 每個日期的因子暴露（可選）
- `sector_map`: 標的到 Sector 的映射（可選）
- `config`: 配置參數（年化基數、無風險利率等）

---

## 2. PerformanceSummary Schema（輸出）

```python
@dataclass
class PerformanceSummary:
    """績效摘要資料結構"""
    
    # Portfolio-level
    total_return: float                      # 累積報酬
    cagr: float                             # 年化報酬
    vol_annualized: float                   # 年化波動度
    sharpe: float                           # Sharpe Ratio
    max_drawdown: float                     # 最大回落
    calmar: float                           # Calmar Ratio
    hit_rate: float                         # 勝率
    avg_win: float                          # 平均獲利
    avg_loss: float                         # 平均虧損
    turnover_annualized: float              # 年化換手率
    
    # Benchmark / Relative（可選）
    active_return: Optional[float] = None   # 主動報酬
    tracking_error: Optional[float] = None  # 追蹤誤差
    information_ratio: Optional[float] = None  # 資訊比率
```

---

## 3. AttributionReport Schema（輸出）

```python
@dataclass
class AttributionReport:
    """歸因報告資料結構"""
    
    # Symbol-level
    by_symbol: pd.DataFrame
    # columns: [symbol, return_contrib, weight_avg, sector, ...]
    
    # Sector-level
    by_sector: pd.DataFrame
    # columns: [sector, allocation_effect, selection_effect, total_effect]
    
    # Factor-level
    by_factor: pd.DataFrame
    # columns: [factor, factor_return, factor_contribution, exposure_avg]
    
    residual: float  # 非解釋部分（特質收益）
```

### DataFrame 欄位說明

#### by_symbol

- `symbol`: 標的代碼
- `return_contrib`: 報酬貢獻（平均權重 × 總報酬）
- `weight_avg`: 平均權重
- `sector`: 所屬 Sector（如果有 sector_map）

#### by_sector

- `sector`: Sector 名稱
- `allocation_effect`: 配置效應
- `selection_effect`: 選股效應
- `total_effect`: 總效應

#### by_factor

- `factor`: 因子名稱
- `factor_return`: 因子總報酬
- `factor_contribution`: 因子貢獻
- `exposure_avg`: 平均暴露

---

## 4. PerformanceEngineResult Schema（完整輸出）

```python
@dataclass
class PerformanceEngineResult:
    """Performance Engine 完整輸出結果"""
    
    summary: PerformanceSummary
    attribution: AttributionReport
    raw_frames: Dict[str, pd.DataFrame] = None  # for debugging
```

---

## 5. API 定義

```python
class PerformanceEngine:
    """Performance & Attribution Engine 核心類別"""
    
    def __init__(
        self,
        periods_per_year: int = 252,
        risk_free_rate: float = 0.0
    ):
        """初始化 Performance Engine
        
        Args:
            periods_per_year: 年化基數（台股通常為 252）
            risk_free_rate: 無風險利率
        """
        ...
    
    def compute_summary(
        self,
        request: PerformanceEngineRequest
    ) -> PerformanceSummary:
        """計算績效摘要
        
        Args:
            request: PerformanceEngineRequest 物件
        
        Returns:
            PerformanceSummary 物件
        """
        ...
    
    def compute_attribution(
        self,
        request: PerformanceEngineRequest
    ) -> AttributionReport:
        """計算歸因報告
        
        Args:
            request: PerformanceEngineRequest 物件
        
        Returns:
            AttributionReport 物件
        """
        ...
    
    def compute_full_report(
        self,
        request: PerformanceEngineRequest
    ) -> PerformanceEngineResult:
        """計算完整報告（績效摘要 + 歸因報告）
        
        Args:
            request: PerformanceEngineRequest 物件
        
        Returns:
            PerformanceEngineResult 物件
        """
        ...
```

---

## 6. Helper 方法

### 從 PathABacktestResult 建立 Request

```python
@classmethod
def from_path_a_result(
    cls,
    path_a_result: PathABacktestResult,
    benchmark_returns: Optional[pd.Series] = None,
    factor_returns: Optional[pd.DataFrame] = None,
    factor_exposures_by_date: Optional[Dict] = None,
    sector_map: Optional[Dict[str, str]] = None
) -> PerformanceEngineRequest:
    """從 PathABacktestResult 建立 PerformanceEngineRequest
    
    Args:
        path_a_result: Path A 回測結果
        benchmark_returns: 基準報酬序列（可選）
        factor_returns: 因子報酬 DataFrame（可選）
        factor_exposures_by_date: 因子暴露字典（可選）
        sector_map: Sector 映射（可選）
    
    Returns:
        PerformanceEngineRequest 物件
    """
    ...
```

---

## 7. 預設參數

```python
DEFAULT_CONFIG = {
    "periods_per_year": 252,      # 台股交易日數
    "risk_free_rate": 0.0,        # 無風險利率
    "min_trade_threshold": 0.001,  # 最小交易門檻
}
```

---

**版本**：v1.0  
**狀態**：✅ Spec 規範已確立

