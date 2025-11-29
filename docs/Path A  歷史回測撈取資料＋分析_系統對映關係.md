# Path A 歷史回測撈取資料＋分析 × J-GOD 系統對映關係

> **整理日期**：2024-11-28  
> **來源文件**：`docs/Path A  歷史回測撈取資料＋分析.txt` / `docs/Path A  歷史回測撈取資料＋分析_AI知識庫版_v1.md`

---

## 📚 核心概念概述

「Path A 歷史回測撈取資料＋分析」定義了 J-GOD 系統的**「歷史數據需求」**完整規格，涵蓋：
- 核心交易與價格訊號數據
- 籌碼與資金流向數據
- 基本面與價值結構數據
- 宏觀與外部風險數據
- Citadel 與 Renaissance Technologies 的數據策略
- 嚴格時間戳記隔離原則

---

## 🗂️ 數據維度 × J-GOD 系統對映

### 一、I. 核心交易與價格訊號 (Core Price & Execution)

**核心概念**：計算所有技術因子和模擬交易的基礎

**J-GOD 系統對映**：

| 數據項目 | 頻率 | 對應模組 | 應用場景 | 狀態 |
|---------|------|---------|---------|------|
| **還原收盤價 (Adjusted Close)** | 日 | `data_pipeline/data_loader.py` | PnL 計算、F_C 因子 | 待實作 |
| **開盤價、最高價、最低價** | 日 | `data_pipeline/data_loader.py` | 模擬進場價、DQA 檢查 | 待實作 |
| **成交量 (Volume)** | 日 | `factor_engine/inertia_factor.py` | F_Inertia 因子計算 | ✅ 已實作 |
| **成交筆數 (Ticket Count)** | 日 | （規劃中）`factor_engine/noise_factor.py` | F_Noise 因子 | 待實作 |

**關鍵要求**：
- ✅ **還原股價是核心**：必須使用 FinMind API 的還原功能
- ✅ **時間戳記隔離**：計算 T 日因子時，只能使用 T-1 日及之前的數據

---

### 二、II. 籌碼與資金流向 (Capital Flow & Sentiment)

**核心概念**：捕捉市場參與者行為，支援 F_CapitalFlow 和 F_Noise 因子

**J-GOD 系統對映**：

| 數據項目 | 頻率 | 對應模組 | 應用場景 | 狀態 |
|---------|------|---------|---------|------|
| **三大法人買賣超** | 日 | `factor_engine/capital_flow_factor.py` | F_CapitalFlow 因子 | ✅ 已實作（需擴充） |
| **融資融券餘額** | 日 | （規劃中）`factor_engine/noise_factor.py` | F_Noise 因子（散戶情緒） | 待實作 |
| **股權分散表 (集保庫存)** | 週/雙週 | （規劃中）`factor_engine/value_factor.py` | F_Value 因子（籌碼結構） | 待實作 |
| **法人連續買超天數** | 衍生計算 | `factor_engine/inertia_factor.py` | F_Inertia 慣性訊號 | 需擴充 |
| **累積買賣超庫存** | 衍生計算 | `factor_engine/inertia_factor.py` | F_Inertia 累積壓力 | 需擴充 |

**衍生分析需求**：
```python
# 需要新增的功能
class CapitalFlowAnalyzer:
    def calculate_consecutive_buy_days(self, institution_type: str) -> int:
        """計算法人連續買超天數"""
        ...
    
    def calculate_accumulated_inventory(self, days: int = 5) -> float:
        """計算累積買賣超庫存（近 N 日）"""
        ...
```

---

### 三、III. 基本面與價值結構 (Fundamental & Quality)

**核心概念**：支援 F_Value 因子，評估公司長期價值與風險

**J-GOD 系統對映**：

| 數據項目 | 頻率 | 對應模組 | 應用場景 | 狀態 |
|---------|------|---------|---------|------|
| **ROE（股東權益報酬率）** | 季 | （規劃中）`factor_engine/value_factor.py` | F_Value（品質 Moat） | 待實作 |
| **P/E Ratio（本益比）** | 季/日 | （規劃中）`factor_engine/value_factor.py` | F_Value（價值安全邊際） | 待實作 |
| **營收年增率** | 月/季 | （規劃中）`factor_engine/value_factor.py` | F_Value（成長性） | 待實作 |
| **負債權益比** | 季 | （規劃中）`factor_engine/value_factor.py` | F_Value（財務健康） | 待實作 |

**萬物修復法則整合**：
- 在集中式學習日，如果 F_Value 顯示個股 P/E 過高，自動調低 F_C、F_Inertia 的決策權重

---

### 四、IV. 宏觀與外部風險 (Macro & Calendar)

**核心概念**：啟動 Regime-Switching Filter 和 RAROC 邏輯的核心數據

**J-GOD 系統對映**：

| 數據項目 | 頻率 | 對應模組 | 應用場景 | 狀態 |
|---------|------|---------|---------|------|
| **大盤指數報酬率** | 日 | `factor_engine/cross_asset_factor.py` | F_Beta、F_Correlation | ✅ 已實作（需擴充） |
| **10 年期公債殖利率** | 日 | （規劃中）`macro/raroc_calculator.py` | RAROC Logic、無風險利率 R_f | 待實作 |
| **VIX 代理指標** | 日 | （規劃中）`macro/market_regime_detector.py` | Regime-Switching Filter | 待實作 |
| **外國主要指數日報酬** | 日 | `factor_engine/cross_asset_factor.py` | F_Macro（跨市場傳導） | 需擴充 |
| **財報/除權息日期** | 事件 | （規劃中）`data_feed/data_validator.py` | DQA、F_Calendar | 待實作 |

**Regime-Switching Filter 整合**：
```python
# 當 VIX 代理指標飆升時
if volatility_proxy > 2.0 * long_term_avg:
    # 立即進入低風險模式
    enter_low_risk_mode()
    reduce_all_positions(ratio=0.5)
    pause_learning_engine()
```

---

## 🏗️ DataFetcher 模組設計

### 核心職責

**J-GOD 系統對映**：

| 功能 | 對應模組 | 實施方式 | 狀態 |
|------|---------|---------|------|
| **歷史數據批量撈取** | （規劃中）`data_pipeline/data_fetcher.py` | 一次性撈取 2023/10/01 ~ 2024/12/31 所有數據 | 待實作 |
| **還原股價處理** | （規劃中）`data_pipeline/data_fetcher.py` | 使用 FinMind API 還原功能 | 待實作 |
| **時間戳記驗證** | （規劃中）`data_feed/data_validator.py` | 確保無未來函數洩漏 | 待實作 |
| **數據品質保證 (DQA)** | （規劃中）`data_feed/data_validator.py` | 檢查極端變動、日期連續性 | 待實作 |
| **數據儲存** | （規劃中）`data_pipeline/storage_manager.py` | Parquet/HDF5 格式，分層儲存 | 待實作 |

---

### DataFetcher 類別設計建議

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd

@dataclass
class DataFetchConfig:
    """數據撈取配置"""
    start_date: datetime
    end_date: datetime
    symbols: List[str]  # ["TSE001", "2330.TW"]
    data_dimensions: List[str]  # ["price", "capital_flow", "fundamental", "macro"]
    use_adjusted_price: bool = True  # 必須使用還原股價

class DataFetcher:
    """Path A 歷史數據撈取器"""
    
    def __init__(self, config: DataFetchConfig):
        self.config = config
        self._ensure_no_lookahead_bias = True  # 嚴格時間戳記隔離
    
    def fetch_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        一次性撈取所有歷史數據
        
        Returns:
            Dict[str, pd.DataFrame]:
            - "price": OHLCV + 還原收盤價
            - "capital_flow": 三大法人買賣超、融資融券
            - "fundamental": ROE, P/E, 營收年增率
            - "macro": 公債殖利率、VIX 代理、外國指數
            - "calendar": 財報日期、除權息日期、假期
        """
        ...
    
    def _fetch_price_data(self, symbol: str) -> pd.DataFrame:
        """撈取價格數據（必須包含還原收盤價）"""
        ...
    
    def _fetch_capital_flow_data(self, symbol: str) -> pd.DataFrame:
        """撈取籌碼與資金流向數據"""
        ...
    
    def _fetch_fundamental_data(self, symbol: str) -> pd.DataFrame:
        """撈取基本面數據（注意：季度數據需要時間戳記隔離）"""
        ...
    
    def _fetch_macro_data(self) -> pd.DataFrame:
        """撈取宏觀數據"""
        ...
    
    def _fetch_calendar_events(self) -> pd.DataFrame:
        """撈取交易日曆與外部衝擊日期"""
        ...
```

---

## 🔗 與其他系統模組的整合

### 與「滾動式分析」的整合

| 滾動式分析概念 | Path A 數據需求對應 | 整合方式 |
|--------------|-------------------|---------|
| **訊號預生成與集中式模型迭代** | 一次性批量撈取所有歷史數據 | DataFetcher 在 Walk-Forward 開始前完成數據撈取 |
| **嚴格時間戳記隔離** | 所有數據必須標記「已知時間戳記」 | DataValidator 檢查並標記數據的「可用時間」 |
| **實戰滑價與延遲成本模擬** | 開盤價、最高價、最低價 | PerformanceAnalyzer 使用這些數據模擬真實成本 |

---

### 與「邏輯版操作說明書」的整合

| 邏輯版操作說明書需求 | Path A 數據需求對應 | 整合方式 |
|-------------------|-------------------|---------|
| **多時間框架預測引擎** | 需要日、週、月、季等多頻率數據 | DataFetcher 支援多頻率數據撈取 |
| **Mode 2 萬分之三機制** | 需要精確的價格數據用於偏差計算 | 還原收盤價確保偏差計算準確 |
| **三重審查決策樹** | 需要籌碼數據輔助決策 | 法人買賣超數據作為審查輸入 |

---

### 與「萬物修復法則」的整合

| 修復層面 | Path A 數據需求對應 | 整合方式 |
|---------|-------------------|---------|
| **價格與空間的修復** | 還原收盤價、開高低價 | DQA 檢查異常價格變動 |
| **時間與週期的修復** | 交易日曆、財報日期 | 避免在特殊日期觸發錯誤修復 |
| **系統與模型的修復** | 所有數據用於 PerformanceAnalyzer | 績效分析需要完整數據 |
| **情緒與行為的修復** | 融資融券、法人買賣超 | F_Noise 和 F_CapitalFlow 因子 |

---

## 📊 數據儲存架構建議

### 分層儲存設計

```
data/
├── raw/              # 原始數據（從 API 撈取後未處理）
│   ├── price/
│   ├── capital_flow/
│   ├── fundamental/
│   └── macro/
├── processed/        # 處理後數據（還原股價、時間戳記標記）
│   ├── price/
│   ├── capital_flow/
│   ├── fundamental/
│   └── macro/
└── cache/            # 因子快取（供 Walk-Forward 使用）
    ├── factors/
    └── signals/
```

---

### 數據格式建議

| 數據類型 | 儲存格式 | 理由 |
|---------|---------|------|
| **價格數據** | Parquet | 高效壓縮、快速讀取 |
| **籌碼數據** | Parquet | 時間序列數據，Parquet 效率高 |
| **基本面數據** | Parquet + JSON | 季度數據較少，JSON 便於查詢 |
| **宏觀數據** | Parquet | 時間序列數據 |
| **交易日曆** | JSON/CSV | 事件數據，結構簡單 |

---

## 🎯 實施優先級建議

### 第一階段（高優先級）

| 模組 | 優先級 | 理由 |
|------|--------|------|
| `data_pipeline/data_fetcher.py` | 🔴 高 | 所有數據撈取的基礎 |
| `data_pipeline/data_loader.py` | 🔴 高 | Walk-Forward Pipeline 需要 |
| **還原股價處理** | 🔴 高 | 核心要求，影響所有績效計算 |
| `data_feed/data_validator.py` | 🔴 高 | DQA 和時間戳記驗證 |

### 第二階段（中優先級）

| 模組 | 優先級 | 理由 |
|------|--------|------|
| `factor_engine/value_factor.py` | 🟡 中 | F_Value 因子（基本面） |
| `factor_engine/noise_factor.py` | 🟡 中 | F_Noise 因子（散戶情緒） |
| `macro/market_regime_detector.py` | 🟡 中 | Regime-Switching Filter |
| `macro/raroc_calculator.py` | 🟡 中 | RAROC Logic |

### 第三階段（低優先級）

| 模組 | 優先級 | 理由 |
|------|--------|------|
| 衍生分析功能 | 🟢 低 | 法人連續買超天數等衍生指標 |
| 跨市場數據整合 | 🟢 低 | 外國指數日報酬等 |

---

## 💡 設計原則

在設計/調整任何數據撈取邏輯時，都要問：

1. **這段程式碼是否遵循「嚴格時間戳記隔離」？**
   - 計算 T 日因子時，是否只使用 T-1 日及之前的數據？
   - 季度財報數據是否正確標記「公告日期」？

2. **數據是否經過「還原股價」處理？**
   - 所有價格相關計算是否使用還原收盤價？
   - 是否避免假性獲利導致的績效誤判？

3. **數據品質是否通過 DQA 檢查？**
   - 極端價格變動是否有檢查？
   - 日期序列是否連續？

---

## 📋 數據撈取檢查清單

在開始 Walk-Forward 回測前，確認：

- [ ] ✅ 所有價格數據已還原（Adjusted Close）
- [ ] ✅ 時間範圍涵蓋：2023/10/01 ~ 2024/12/31
- [ ] ✅ 核心標的數據完整（TSE001, 2330.TW）
- [ ] ✅ 籌碼數據包含三大法人買賣超
- [ ] ✅ 基本面數據已標記「公告日期」
- [ ] ✅ 宏觀數據包含 VIX 代理、公債殖利率
- [ ] ✅ 交易日曆包含財報、除權息、假期日期
- [ ] ✅ 所有數據通過 DQA 檢查
- [ ] ✅ 數據已存入 Parquet 格式，供 Walk-Forward 使用

---

*本文件作為 J-GOD 系統開發的核心指導原則，所有數據撈取設計都應遵循「Path A 歷史回測撈取資料＋分析」的規格。*

