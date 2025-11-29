# J-GOD 股神作戰系統 · Python Interface Spec v0.9

> **目的**：定義 J-GOD 系統的「程式架構藍圖」，給工程師與 AI（Cursor）作為實作標準。

> **實作語言**：Python 3.11+

> **專案根目錄**：JarvisV1/jgod/

---

## 一、整體架構說明

J-GOD（Jarvis Global Operation of Delta）是一個「世界級 1% 個人自營商級別」的 AI 量化交易系統，整合了以下核心模組：

### 1.1 核心引擎層級

#### 第一層：資料與因子層
- **Factor Engine（因子引擎）**：計算所有量化因子（F_C 資金流、F_S 情緒、F_Inertia 慣性等）
- **Data Universe Engine（資料宇宙引擎）**：市場所有資料的管理、API、清洗、標準化

#### 第二層：決策與預測層
- **Signal Engine（訊號引擎）**：根據因子生成交易訊號
- **Model / Prediction Engine（模型/預測引擎）**：雙引擎架構（盤中當沖引擎 + 長線/中期預測引擎）
- **Path A Engine（Path A 引擎）**：歷史回測資料撈取與分析

#### 第三層：風險與執行層
- **Risk Engine（風控引擎）**：單筆/單日/單月風險控制、最大回撤監控
- **Execution Engine（執行引擎）**：訂單執行、滑價模型、成本模型、部位同步
- **Position Engine（倉位管理引擎）**：多策略資金分配、波動調整

#### 第四層：驗證與優化層
- **Backtest Engine（回測引擎）**：歷史回測、績效分析
- **Walk-Forward Engine（滾動式回測引擎）**：消除未來資料洩漏的滾動式驗證
- **RL Engine（強化學習引擎）**：自主參數優化、因子權重調整、策略進化

#### 第五層：整合與決策層
- **War Room / AI Council（AI 戰情室）**：多 AI 幕僚團整合、決策支援

---

## 二、模組 Interface Spec

### 2.1 Factor Engine（因子引擎）

**對應文件**：
- `股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md`：XQ 資金流因子 F_C、F_S 情緒因子設計
- `雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md`：因子計算與多策略模組

```python
from abc import ABC, abstractmethod
from typing import Dict, Optional, Union
import pandas as pd
import numpy as np

class FactorEngine(ABC):
    """
    因子引擎基類
    
    對應文件：股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md
    對應概念：因子計算模組（F_C、F_S、F_D、F_Inertia 等）
    
    功能：計算所有量化因子，為策略決策提供輸入
    """
    
    def __init__(self, config: Dict):
        """
        初始化因子引擎
        
        Args:
            config: 配置字典，包含因子計算所需參數
        """
        self.config = config
        self.historical_stats = None  # 歷史統計資料（用於 z-score 計算）
    
    @abstractmethod
    def compute_factor(self, 
                       market_data: pd.DataFrame,
                       xq_data: Optional[Dict] = None,
                       historical_weights: Optional[pd.Series] = None) -> Dict[str, float]:
        """
        計算單一因子值
        
        對應文件：股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md
        對應概念：F_C 核心因子 I（族群攻擊因子 SAI）、F_C 核心因子 II（主力單量失衡 MOI）
        
        Args:
            market_data: 市場資料 DataFrame（包含價格、成交量等）
            xq_data: XQ 資金流資料（可選）
            historical_weights: 歷史族群權重（用於計算 residual/z-score）
        
        Returns:
            Dict[str, float]: 因子名稱與值的映射
        """
        pass
    
    def compute_all_factors(self, market_data: pd.DataFrame) -> Dict[str, float]:
        """
        計算所有啟用的因子
        
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        對應概念：第一層：因子計算與多策略模組（Alpha Generation）
        
        Args:
            market_data: 市場資料 DataFrame
        
        Returns:
            Dict[str, float]: 所有因子名稱與值的映射
        """
        pass
    
    def update_historical_stats(self, historical_data: pd.DataFrame):
        """
        更新歷史統計資料（用於標準化計算）
        
        對應文件：股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md
        對應概念：歷史參數（族群成交比重的歷史統計）
        
        Args:
            historical_data: 歷史資料 DataFrame
        """
        pass


class CapitalFlowFactorEngine(FactorEngine):
    """
    XQ 資金流因子 F_C 引擎
    
    對應文件：股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md
    對應概念：CapitalFlowEngine - XQ 資金流因子 F_C
    """
    
    def compute_factor(self, 
                       market_data: pd.DataFrame,
                       xq_data: Optional[Dict] = None,
                       historical_weights: Optional[pd.Series] = None) -> Dict[str, float]:
        """
        計算 F_C（資金流因子）
        
        對應文件：股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md
        對應概念：F_C 核心因子 I（族群攻擊因子 SAI）、F_C 核心因子 II（主力單量失衡 MOI）
        
        實作要點：
        - SAI（Sector Attack Index）：計算族群資金占比的 residual/z-score
        - MOI（Major Order Imbalance）：計算主力買賣單失衡
        """
        pass


class SentimentFactorEngine(FactorEngine):
    """
    情緒因子 F_S 引擎
    
    對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
    對應概念：F_S（情緒）：NLP 綜合情緒指數、VIX、期指 OI
    """
    
    def compute_factor(self, 
                       market_data: pd.DataFrame,
                       xq_data: Optional[Dict] = None,
                       historical_weights: Optional[pd.Series] = None) -> Dict[str, float]:
        """
        計算 F_S（情緒因子）
        
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        對應概念：F_S 核心因子（NLP 情緒、VIX、期指 OI 宏觀情緒過濾）
        """
        pass
```

### 2.2 Signal Engine（訊號引擎）

**對應文件**：
- `J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md`：六大武功策略（主流突破、強勢回檔等）
- `雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md`：策略聯動、P1/P2 行動信號

```python
from typing import List, Dict, Optional
import pandas as pd
from enum import Enum

class SignalType(Enum):
    """訊號類型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    EXIT = "exit"
    NONE = "none"

class Signal:
    """交易訊號資料結構"""
    
    def __init__(self,
                 signal_type: SignalType,
                 symbol: str,
                 confidence: float,
                 strategy_tag: str,
                 entry_price: Optional[float] = None,
                 stop_loss: Optional[float] = None,
                 take_profit: Optional[float] = None,
                 position_size: Optional[float] = None):
        """
        初始化訊號
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：Watchlist 欄位設計（Setup_Condition、Entry_Price_Plan、Stop_Loss_Price、Target_Price）
        """
        self.signal_type = signal_type
        self.symbol = symbol
        self.confidence = confidence  # 0-1 信心分數
        self.strategy_tag = strategy_tag  # 策略標籤（主流突破、強勢回檔等）
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.position_size = position_size


class SignalEngine:
    """
    訊號引擎
    
    對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
    對應概念：六大武功策略（主流突破、強勢回檔、主力反轉、逆勢突襲、急攻狙擊、爆量警戒）
    """
    
    def __init__(self, config: Dict):
        """
        初始化訊號引擎
        
        Args:
            config: 配置字典，包含各策略參數
        """
        self.config = config
        self.active_strategies = []  # 啟用的策略列表
    
    def compute_signals(self,
                       market_data: pd.DataFrame,
                       factors: Dict[str, float],
                       indicators: Optional[pd.DataFrame] = None) -> List[Signal]:
        """
        根據因子與市場資料生成交易訊號
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：六大武功進場條件（Rules_Entry）與出場條件（Rules_Exit）
        
        Args:
            market_data: 市場資料 DataFrame
            factors: 因子字典（來自 FactorEngine）
            indicators: 技術指標 DataFrame（可選）
        
        Returns:
            List[Signal]: 生成的訊號列表
        """
        pass
    
    def check_entry_condition(self,
                             symbol: str,
                             strategy_tag: str,
                             market_data: pd.DataFrame,
                             factors: Dict[str, float]) -> bool:
        """
        檢查進場條件
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：六大武功 Rules_Entry（進場條件）
        
        實作範例：
        - 主流突破：檢查是否站上季線、突破壓力、量價同步
        - 強勢回檔：檢查是否拉回至支撐、量縮止穩、出現多方訊號
        """
        pass
    
    def check_exit_condition(self,
                            symbol: str,
                            strategy_tag: str,
                            current_position: Dict,
                            market_data: pd.DataFrame) -> bool:
        """
        檢查出場條件
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：六大武功 Rules_Exit（出場條件）、Stop_Loss（停損）
        """
        pass
```

### 2.3 Model / Prediction Engine（模型/預測引擎）

**對應文件**：
- `雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md`：雙引擎架構（盤中當沖引擎 + 長線預測引擎）

```python
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np

class PredictionEngine:
    """
    預測引擎基類
    
    對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
    對應概念：決策與執行模組（Execution and Risk Control）、策略聯動
    """
    
    def __init__(self, config: Dict):
        """
        初始化預測引擎
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.rl_weights = None  # RL 優化後的因子權重
    
    @abstractmethod
    def predict(self,
                factors: Dict[str, float],
                market_state: Optional[Dict] = None) -> Dict:
        """
        生成預測
        
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        對應概念：整合 F_C, F_S 因子，根據 RL 調整後的 Beta 權重計算最終預測
        
        Args:
            factors: 因子字典
            market_state: 市場狀態（可選）
        
        Returns:
            Dict: 預測結果（包含方向、幅度、信心分數等）
        """
        pass


class IntradayEngine(PredictionEngine):
    """
    盤中當沖預測引擎
    
    對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
    對應概念：盤中當沖預測引擎（Intraday Engine）- 極致速度，鎖定日內微觀行為
    
    核心功能：
    - 計算 RCNC（即時累積淨成本線）
    - 偵測主力掃貨頻率
    - 流動性枯竭警報
    """
    
    def predict(self,
                factors: Dict[str, float],
                market_state: Optional[Dict] = None) -> Dict:
        """
        生成盤中預測
        
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        對應概念：RCNC 計算、主力掃貨頻率偵測、流動性壓力因子
        """
        pass
    
    def compute_rcnc(self, tick_data: pd.DataFrame) -> pd.Series:
        """
        計算 RCNC（即時累積淨成本線）
        
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        對應概念：RCNC 基於主力大單（XQ）與逐筆成交數據，使用 Pandas cumsum 向量化計算
        """
        pass


class MacroEngine(PredictionEngine):
    """
    長線/中期預測引擎
    
    對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
    對應概念：長線/中期預測引擎（Macro Engine）- 模型深度，預測明日、本週、本季趨勢
    
    核心因子：
    - F_C（籌碼）：日級 LAC、籌碼集中度、融合盤中聚合後的 RCNC 波動
    - F_S（情緒）：NLP 綜合情緒指數、VIX、期指 OI
    - F_D（價值）：杜邦分析、行業 Beta
    """
    
    def predict(self,
                factors: Dict[str, float],
                market_state: Optional[Dict] = None) -> Dict:
        """
        生成長線預測
        
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        對應概念：整合 F_C, F_S 因子，根據 RL 調整後的 Beta 權重計算最終預測
        """
        pass
    
    def adjust_prediction_with_us_market(self,
                                        initial_prediction: Dict,
                                        us_market_signal: Dict) -> Dict:
        """
        根據美股連動調整預測（實時 Beta Adjustment）
        
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        對應概念：趨勢修正（實時 Beta Adjustment）- 在盤中，長線模型會監控美股連動
        """
        pass
```

### 2.4 Path A Engine（Path A 歷史回測資料引擎）

**對應文件**：
- `Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md`：歷史資料撈取規格

```python
from typing import List, Optional
import pandas as pd
from datetime import datetime, timedelta

class PathAEngine:
    """
    Path A 歷史回測資料引擎
    
    對應文件：Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md
    對應概念：歷史資料撈取清單、必須撈取的欄位、還原股價的重要性
    """
    
    def __init__(self, config: Dict):
        """
        初始化 Path A 引擎
        
        Args:
            config: 配置字典（包含資料來源、日期範圍等）
        """
        self.config = config
    
    def fetch_historical_data(self,
                             symbols: List[str],
                             start_date: datetime,
                             end_date: datetime,
                             fields: Optional[List[str]] = None) -> pd.DataFrame:
        """
        撈取歷史資料
        
        對應文件：Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md
        對應概念：必須撈取的欄位（Date、Adjusted Close Price、Open Price、Low Price、Trading Volume）
        
        關鍵要求：
        - 必須使用 Adjusted Close Price（還原收盤價）避免除權息影響
        - 必須是交易日序列，且無跳日
        """
        pass
    
    def adjust_price_for_dividend(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """
        還原股價（處理除權息）
        
        對應文件：Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md
        對應概念：還原股價的重要性 - 如果使用未還原的收盤價會導致錯誤的績效計算
        """
        pass
    
    def validate_data_integrity(self, data: pd.DataFrame) -> Dict[str, bool]:
        """
        驗證資料完整性
        
        對應文件：Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md
        對應概念：嚴格時間戳記隔離原則、確保無未來資料洩漏
        """
        pass
```

### 2.5 Risk Engine（風控引擎）

**對應文件**：
- `J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md`：風控規則（單筆/單日/單月）

```python
from typing import Dict, Optional
import pandas as pd

class RiskEngine:
    """
    風控引擎
    
    對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
    對應概念：J-GOD Risk Engine – 風控 V1（單筆最大虧損 2%、單日最大虧損 2%、單月最大虧損 6%）
    """
    
    def __init__(self, config: Dict):
        """
        初始化風控引擎
        
        Args:
            config: 風控配置
                - max_loss_per_trade: 單筆最大虧損（預設 0.02 = 2%）
                - max_loss_per_day: 單日最大虧損（預設 0.02 = 2%）
                - max_loss_per_month: 單月最大虧損（預設 0.06 = 6%）
        """
        self.config = config
        self.daily_loss = 0.0
        self.monthly_loss = 0.0
        self.violation_count = 0
    
    def check_trade_risk(self,
                        symbol: str,
                        entry_price: float,
                        stop_loss_price: float,
                        position_size: float,
                        account_value: float) -> Dict[str, any]:
        """
        檢查單筆交易風險
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：單筆最大虧損 2% - 行為定義：跌到 -2% 必須砍單，不准猶豫
        
        Returns:
            Dict: {
                'allowed': bool,
                'max_loss_pct': float,
                'recommended_size': float,
                'violation': bool
            }
        """
        pass
    
    def check_daily_risk(self, today_pnl: float, account_value: float) -> Dict[str, any]:
        """
        檢查單日風險
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：單日最大虧損 2% - 行為定義：今天的所有虧損累計 -2% → 立即關機、不開新單
        
        Returns:
            Dict: {
                'allowed': bool,
                'daily_loss_pct': float,
                'must_shutdown': bool
            }
        """
        pass
    
    def check_monthly_risk(self, monthly_pnl: float, account_value: float) -> Dict[str, any]:
        """
        檢查單月風險
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：單月最大虧損 6% - 行為定義：若單月虧損達 -6%，整月停止新策略，只做模擬，檢討策略池
        
        Returns:
            Dict: {
                'allowed': bool,
                'monthly_loss_pct': float,
                'must_review': bool
            }
        """
        pass
    
    def calculate_position_size(self,
                               account_value: float,
                               entry_price: float,
                               stop_loss_price: float,
                               max_loss_pct: float = 0.02) -> float:
        """
        計算建議部位大小
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：Position_Sizing（部位大小規則）
        
        實作邏輯：
        - 根據停損距離與最大允許虧損百分比計算
        - 確保單筆最大虧損不超過設定值
        """
        pass
    
    def record_violation(self, violation_type: str, details: Dict):
        """
        記錄風控違規
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：風控紀律遵守率 > 95%、自動標記違規
        """
        pass
```

### 2.6 Execution Engine（執行引擎）

**對應文件**：
- `J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md`：Execution Engine（實單層）

```python
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
import pandas as pd

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"

@dataclass
class Order:
    """訂單資料結構"""
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    price: Optional[float] = None  # None 表示市價單
    strategy_tag: str = ""
    simulated: bool = True  # 是否為模擬單

@dataclass
class Fill:
    """成交資料結構"""
    order_id: str
    filled_price: float
    filled_quantity: int
    filled_time: pd.Timestamp
    slippage: float
    fees: float

class ExecutionEngine:
    """
    執行引擎
    
    對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
    對應概念：Execution Engine（實單層）- 券商 API、下單配置、滑價模型、成本模型、部位同步、停損自動化、風險斷路器
    """
    
    def __init__(self, config: Dict):
        """
        初始化執行引擎
        
        Args:
            config: 配置字典
                - broker_api: 券商 API 設定
                - slippage_model: 滑價模型參數
                - fee_model: 手續費模型參數
                - simulated: 是否為模擬模式
        """
        self.config = config
        self.is_simulated = config.get('simulated', True)
    
    def execute_order(self, order: Order, market_data: Optional[pd.DataFrame] = None) -> Fill:
        """
        執行訂單
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：Execution Engine - 下單、滑價模型、成本模型
        
        實作要點：
        - 模擬模式：使用滑價模型計算成交價
        - 實盤模式：透過券商 API 下單
        """
        pass
    
    def simulate_order(self, order: Order, order_book_snapshot: Dict) -> Fill:
        """
        模擬訂單執行（用於回測）
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：Execution Engine - 滑價模型、成本模型
        
        實作要點：
        - 根據訂單大小與市場流動性計算滑價
        - 計算手續費與交易成本
        """
        pass
    
    def check_pre_trade_risk(self, order: Order, current_positions: Dict) -> bool:
        """
        執行前風險檢查
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：Execution Engine - 風險斷路器
        
        Returns:
            bool: 是否允許執行
        """
        pass
    
    def sync_positions(self) -> Dict:
        """
        同步當前部位
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：Execution Engine - 部位同步
        
        Returns:
            Dict: 當前所有部位資訊
        """
        pass
    
    def auto_stop_loss(self, symbol: str, current_price: float, stop_loss_price: float) -> Optional[Order]:
        """
        自動停損
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：Execution Engine - 停損自動化
        
        Returns:
            Optional[Order]: 如果需要停損，返回停損訂單
        """
        pass
```

### 2.7 Backtest Engine（回測引擎）

**對應文件**：
- `J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md`：Backtest Engine（回測引擎）

```python
from typing import Dict, List, Optional, Callable
import pandas as pd
import numpy as np

class BacktestResult:
    """回測結果資料結構"""
    
    def __init__(self):
        self.total_return: float = 0.0
        self.annualized_return: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.max_drawdown: float = 0.0
        self.win_rate: float = 0.0
        self.profit_factor: float = 0.0
        self.total_trades: int = 0
        self.winning_trades: int = 0
        self.trades_df: Optional[pd.DataFrame] = None
        self.equity_curve: Optional[pd.DataFrame] = None

class BacktestEngine:
    """
    回測引擎
    
    對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
    對應概念：Backtest Engine（回測引擎）- 回測、回撤、回報、年度績效
    
    功能：
    - 單策略回測
    - 多策略回測
    - 參數優化
    - 績效指標計算
    """
    
    def __init__(self, config: Dict):
        """
        初始化回測引擎
        
        Args:
            config: 配置字典
                - initial_capital: 初始資金
                - commission: 手續費率
                - slippage_model: 滑價模型
        """
        self.config = config
        self.initial_capital = config.get('initial_capital', 1000000)
    
    def run_backtest(self,
                    historical_data: pd.DataFrame,
                    strategy: Callable,
                    start_date: Optional[pd.Timestamp] = None,
                    end_date: Optional[pd.Timestamp] = None) -> BacktestResult:
        """
        執行回測
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：Backtest Engine - 回測、回撤、回報、年度績效
        
        Args:
            historical_data: 歷史資料 DataFrame
            strategy: 策略函數（接收 market_data, 返回 signals）
            start_date: 開始日期
            end_date: 結束日期
        
        Returns:
            BacktestResult: 回測結果
        """
        pass
    
    def calculate_performance_metrics(self, trades_df: pd.DataFrame, equity_curve: pd.DataFrame) -> Dict:
        """
        計算績效指標
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：勝率、報酬率、最大回撤、策略績效分析
        
        計算指標：
        - 總報酬率
        - 年化報酬率（CAGR）
        - Sharpe Ratio
        - 最大回撤（Max Drawdown）
        - 勝率（Win Rate）
        - 平均賺賠比（Profit Factor）
        """
        pass
    
    def calculate_max_drawdown(self, equity_curve: pd.Series) -> float:
        """
        計算最大回撤
        
        對應文件：Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md
        對應概念：最大回撤（Max Drawdown）計算公式
        
        公式：
        1. 計算累積淨值序列：C_t = ∏(1 + r_i)
        2. 計算歷史最高點：P_t = max(C_1, ..., C_t)
        3. 計算回撤：D_t = (P_t - C_t) / P_t
        4. 最大回撤 = max(D_1, ..., D_T)
        """
        pass
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """
        計算 Sharpe Ratio
        
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        對應概念：Sharpe Ratio 標準公式
        
        公式：Sharpe = (R_p - R_f) / σ_p
        年化 Sharpe = 日 Sharpe × √252
        """
        pass
```

### 2.8 Walk-Forward Engine（滾動式回測引擎）

**對應文件**：
- `滾動式分析_AI知識庫版_v1_CORRECTED.md`：滾動式調整（Walk-Forward Analysis）

```python
from typing import Dict, List, Optional, Callable
import pandas as pd
from datetime import datetime, timedelta

class WalkForwardResult:
    """Walk-Forward 回測結果"""
    
    def __init__(self):
        self.train_windows: List[Dict] = []  # 訓練視窗列表
        self.test_results: List[Dict] = []  # 測試結果列表
        self.overall_performance: Dict = {}  # 整體績效

class WalkForwardEngine:
    """
    滾動式回測引擎（Walk-Forward Engine）
    
    對應文件：滾動式分析_AI知識庫版_v1_CORRECTED.md
    對應概念：滾動式調整（Walk-Forward Analysis）基本概念 - 時間核心，確保每天的預測都只使用「當天以前」的數據
    
    目的：消除未來數據洩漏（Data Leakage）的風險，模擬最真實的實戰狀態
    """
    
    def __init__(self, config: Dict):
        """
        初始化 Walk-Forward 引擎
        
        Args:
            config: 配置字典
                - train_window_days: 訓練視窗天數（例如 90）
                - test_window_days: 測試視窗天數（例如 1，即逐日滾動）
                - step_size_days: 滾動步長（例如 1）
        """
        self.config = config
        self.train_window_days = config.get('train_window_days', 90)
        self.test_window_days = config.get('test_window_days', 1)
        self.step_size_days = config.get('step_size_days', 1)
    
    def run_walkforward(self,
                       historical_data: pd.DataFrame,
                       strategy_factory: Callable,
                       start_date: datetime,
                       end_date: datetime) -> WalkForwardResult:
        """
        執行 Walk-Forward 回測
        
        對應文件：滾動式分析_AI知識庫版_v1_CORRECTED.md
        對應概念：滾動式調整實施範例
        
        流程：
        1. 第一天：訓練視窗 2024/01/01～03/31，預測日 2024/04/01
        2. 第二天：訓練視窗 2024/01/02～04/01，預測日 2024/04/02
        3. 以此類推，滾動到結束日期
        
        Args:
            historical_data: 歷史資料 DataFrame（必須包含足夠的緩衝期）
            strategy_factory: 策略工廠函數（接收訓練資料，返回策略實例）
            start_date: 開始日期
            end_date: 結束日期
        
        Returns:
            WalkForwardResult: Walk-Forward 回測結果
        """
        pass
    
    def get_train_window(self,
                        current_date: datetime,
                        historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        獲取當前日期的訓練視窗資料
        
        對應文件：滾動式分析_AI知識庫版_v1_CORRECTED.md
        對應概念：訓練視窗：永遠只用「當下之前」的 N 天（不洩漏未來）
        
        重要：必須確保訓練資料的結束日期 < 預測日期
        """
        pass
    
    def validate_no_data_leakage(self,
                                 train_end: datetime,
                                 test_start: datetime) -> bool:
        """
        驗證無未來資料洩漏
        
        對應文件：滾動式分析_AI知識庫版_v1_CORRECTED.md
        對應概念：嚴格時間戳記隔離原則
        
        Returns:
            bool: 是否通過驗證
        """
        pass
```

### 2.9 RL Engine（強化學習引擎）

**對應文件**：
- `雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md`：強化學習 (RL) 模型設計

```python
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from enum import Enum

class Regime(Enum):
    """市場風格（Regime）"""
    BULL_TREND = "bull_trend"
    BEAR_TREND = "bear_trend"
    RANGE = "range"
    MOMENTUM_BLOWOFF = "momentum_blowoff"
    LOW_VOLUME_DRIFT = "low_volume_drift"
    PANIC_SELLING = "panic_selling"
    NEWS_DRIVEN = "news_driven"
    CHOPPY = "choppy"

class RLState:
    """RL 狀態空間"""
    
    def __init__(self):
        # 策略績效
        self.sharpe_ratio_7d: float = 0.0
        self.mdd_30d: float = 0.0
        self.strategy_correlation: float = 0.0
        
        # 診斷與誤差
        self.residual: float = 0.0
        self.fc_contribution: float = 0.0
        self.fs_contribution: float = 0.0
        
        # 市場情境
        self.vix: float = 0.0
        self.vix_volatility: float = 0.0
        self.market_atr: float = 0.0
        
        # 籌碼健康度
        self.lac_dist: float = 0.0  # LAC 偏離度
        self.dealer_tier_ratio: float = 0.0

class RLAction:
    """RL 行動空間（參數調整）"""
    
    def __init__(self):
        # 因子權重調整
        self.beta_c: float = 1.0  # 籌碼權重
        self.beta_s: float = 1.0  # 情緒權重
        
        # 買入/賣出閾值
        self.t_fear: float = 20.0  # 恐懼買入閾值
        self.t_runup_dev: float = 0.3  # 跑飛偏差賣出閾值
        
        # 風險敞口
        self.position_weight: float = 1.0  # 部位權重

class RLEngine:
    """
    強化學習引擎（RL Engine）
    
    對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
    對應概念：強化學習 (RL) 模型設計 - 情境參數化與自主優化
    
    核心功能：
    - 定義 RL 的「狀態」（State）空間
    - 定義 RL 的「行動」（Action）空間（參數化）
    - 定義「獎勵」（Reward）函數
    - 迭代與學習（Model Calibration Engine）
    """
    
    def __init__(self, config: Dict):
        """
        初始化 RL 引擎
        
        Args:
            config: 配置字典
                - learning_rate: 學習率
                - exploration_rate: 探索率
                - reward_lambda: 獎勵函數懲罰係數
        """
        self.config = config
        self.agent = None  # RL 代理（可使用 Stable-Baselines3、Ray RLlib 等）
    
    def define_state_space(self, market_data: pd.DataFrame, strategy_performance: Dict) -> RLState:
        """
        定義 RL 狀態空間
        
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        對應概念：步驟 1：定義 RL 的「狀態」（State）空間
        
        狀態類別：
        - I. 策略績效（Sharpe Ratio 7 Day, MDD 30 Day, A/B 策略相關性）
        - II. 診斷與誤差（Residual, FC 貢獻度, FS 貢獻度）
        - III. 市場情境（VIX, VIX 波動率, 市場 ATR 均值）
        - IV. 籌碼健康度（L_LAC_dist, Dealer Tier Ratio）
        """
        pass
    
    def define_action_space(self) -> List[RLAction]:
        """
        定義 RL 行動空間（參數化）
        
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        對應概念：步驟 2：定義 RL 的「行動」（Action）空間（參數化）
        
        行動類別：
        - I. 因子權重調整（BetaC, BetaS）
        - II. 買入/賣出閾值（TFear, TRunUp_Dev）
        - III. 風險敞口（Position_Weight）
        """
        pass
    
    def calculate_reward(self,
                        sharpe_ratio: float,
                        max_drawdown: float,
                        lambda_penalty: float = 1.0) -> float:
        """
        計算獎勵函數
        
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        對應概念：步驟 3：定義「獎勵」（Reward）函數
        
        公式：Reward = Sharpe Ratio 30 Day - λ × (Max Drawdown 30 Day)
        
        - Sharpe Ratio 30 Day：主要的獎勵來源，鼓勵高收益、低波動
        - Max Drawdown 30 Day：主要的懲罰來源，λ 是懲罰係數，確保 AI 嚴格控制風險
        """
        pass
    
    def train(self,
              historical_states: List[RLState],
              historical_actions: List[RLAction],
              historical_rewards: List[float]) -> Dict:
        """
        訓練 RL 模型
        
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        對應概念：步驟 4：迭代與學習（Model Calibration Engine）
        
        流程：
        1. 偵測狀態：系統偵測到 Sharpe Ratio 下降，同時 Residual 貢獻度高且 VIX 高漲
        2. RL 決策：RL 代理人根據歷史經驗，發現當這種狀態出現時，降低 BetaS 和提高 TFear 的行動帶來最高的 Reward
        3. 執行校準：系統將 RL 建議的新 Beta 權重寫入並更新到實盤交易模型
        """
        pass
    
    def predict_action(self, current_state: RLState) -> RLAction:
        """
        根據當前狀態預測最佳行動
        
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        對應概念：RL 決策 - 根據歷史經驗輸出最佳參數調整
        
        Returns:
            RLAction: 建議的參數調整
        """
        pass
    
    def update_model(self,
                    state: RLState,
                    action: RLAction,
                    reward: float,
                    next_state: RLState):
        """
        更新 RL 模型（Q-learning / Policy Gradient 等）
        
        對應文件：雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md
        對應概念：RL 學習循環
        """
        pass
```

### 2.10 War Room / AI Council（AI 戰情室）

**對應文件**：
- `J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md`：AI 戰情室（多 AI 幕僚團 + GPT 總結）

```python
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import pandas as pd

class WarRoomRole(Enum):
    """戰情室角色"""
    QUANT_CHIEF = "quant_chief"  # 量化總監
    RISK_OFFICER = "risk_officer"  # 風控長
    MARKET_STRATEGIST = "market_strategist"  # 盤勢分析官
    INTEL_OFFICER = "intel_officer"  # 情報官
    TRADE_TACTICIAN = "trade_tactician"  # 策略顧問
    BUSINESS_ADVISOR = "business_advisor"  # 商業顧問

@dataclass
class AIOpinion:
    """AI 意見資料結構"""
    role_id: str
    model_name: str  # "gpt-4" / "claude" / "gemini" 等
    content: str  # 完整回答
    key_points: List[str]  # 關鍵要點
    stance: str  # "偏多" / "偏空" / "中性" / "觀望"
    confidence: float  # 0-1 信心分數

@dataclass
class WarRoomSummary:
    """戰情室總結資料結構"""
    consensus: str  # 共識
    disagreements: List[str]  # 分歧點
    recommended_action: str  # 建議行動
    risk_points: List[str]  # 風險提醒
    suggested_position_size: float  # 建議部位大小
    priority_sectors: List[str]  # 優先關注族群

class WarRoom:
    """
    AI 戰情室（War Room / AI Council）
    
    對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
    對應概念：AI 戰情室（多 AI 幕僚團 + GPT 總結）
    
    功能：
    - 多 AI 幕僚團討論
    - 整合各引擎的數據與建議
    - 生成最終決策建議
    """
    
    def __init__(self, config: Dict):
        """
        初始化戰情室
        
        Args:
            config: 配置字典
                - ai_providers: AI 提供者列表（例如 ["gpt-4", "claude"]）
                - active_roles: 啟用的角色列表
        """
        self.config = config
        self.active_roles = config.get('active_roles', list(WarRoomRole))
        self.ai_providers = config.get('ai_providers', {})
    
    def build_context(self,
                     market_state: Optional[Dict] = None,
                     strategy_stats: Optional[Dict] = None,
                     virtual_trades_summary: Optional[Dict] = None,
                     recent_errors: Optional[List[Dict]] = None,
                     system_alerts: Optional[List[Dict]] = None) -> str:
        """
        建立戰情 context
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：戰情室資料層（J-GOD Engines）- Market Engine、Strategy/Edge Engine、Error Learning Engine、Global Watch Engine
        
        整合：
        - Market Engine：大盤/族群/Regime
        - Strategy/Edge Engine：各策略勝率、R 倍數
        - Error Learning Engine：最近常犯錯誤 & 禁區
        - Global Watch Engine：制度變更 & 重大事件
        """
        pass
    
    def run_council(self,
                   question: str,
                   context: str,
                   jgod_state: Optional[Dict] = None) -> Tuple[List[AIOpinion], WarRoomSummary]:
        """
        執行 AI 議會討論
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：多 AI 戰情室 - 各幕僚基於 J-GOD 數據給意見，最後「總架構師人格」幫你彙整成結論
        
        流程：
        1. 第一輪：每個幕僚各自發言（不看別人意見）
        2. 第二輪：讓每位幕僚看到「其他人的重點」再補充一次
        3. 總結：交給 Master Summarizer（股神總結人格）整合
        
        Args:
            question: 使用者的問題
            context: 戰情 context（由 build_context 生成）
            jgod_state: J-GOD 系統狀態（可選）
        
        Returns:
            Tuple[List[AIOpinion], WarRoomSummary]: (幕僚意見列表, 總結)
        """
        pass
    
    def ask_role(self,
                role: WarRoomRole,
                question: str,
                context: str,
                previous_opinions: Optional[List[AIOpinion]] = None) -> AIOpinion:
        """
        詢問特定角色
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：戰情室幕僚團（量化總監、風控長、盤勢分析官、情報官、策略顧問、商業顧問）
        
        Args:
            role: 角色
            question: 問題
            context: 上下文
            previous_opinions: 其他角色的意見（用於第二輪討論）
        
        Returns:
            AIOpinion: 該角色的意見
        """
        pass
    
    def summarize_for_user(self,
                          question: str,
                          context: str,
                          opinions: List[AIOpinion]) -> WarRoomSummary:
        """
        為使用者生成總結建議
        
        對應文件：J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md
        對應概念：Master Summarizer 層（總架構師 / 股神總結）
        
        輸出：
        - 共識整理
        - 分歧點
        - 機率判斷
        - 風險清單
        - 行動建議（幾成部位、做/不做、優先族群）
        """
        pass
```

---

## 三、模組間協作流程

### 3.1 典型交易流程

```
1. PathAEngine.fetch_historical_data() → 歷史資料
2. FactorEngine.compute_all_factors() → 因子字典
3. SignalEngine.compute_signals() → 交易訊號列表
4. RiskEngine.check_trade_risk() → 風控檢查
5. PredictionEngine.predict() → 預測結果
6. ExecutionEngine.execute_order() → 訂單執行
7. BacktestEngine.run_backtest() → 回測驗證
8. WalkForwardEngine.run_walkforward() → 滾動式驗證
9. RLEngine.train() → 模型優化
10. WarRoom.run_council() → 決策支援
```

### 3.2 雙引擎協作流程

**對應文件**：`雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md`

```
盤中引擎（IntradayEngine）：
- 計算 RCNC、偵測主力掃貨
- 收盤時聚合結果傳給長線引擎

長線引擎（MacroEngine）：
- 接收盤中引擎的聚合結果作為新因子
- 使用 RL 優化後的 Beta 權重整合 F_C, F_S 因子
- 生成明日/本週/本季預測
```

---

## 四、資料結構規範

### 4.1 市場資料結構

```python
# market_data DataFrame 標準欄位
columns = [
    'date',           # 日期（datetime）
    'symbol',         # 股票代號
    'open',           # 開盤價
    'high',           # 最高價
    'low',            # 最低價
    'close',          # 收盤價
    'adj_close',      # 還原收盤價（重要！）
    'volume',         # 成交量
    'turnover',       # 成交金額
]
```

### 4.2 因子資料結構

```python
# factors Dict 標準格式
factors = {
    'F_C': float,      # 資金流因子
    'F_S': float,      # 情緒因子
    'F_D': float,      # 價值因子
    'F_Inertia': float, # 慣性因子
    # ... 其他因子
}
```

---

## 五、實作注意事項

### 5.1 效能要求

- **向量化計算**：所有因子計算必須使用 NumPy/Pandas 向量化，避免 Python 迴圈
- **資料緩存**：歷史統計資料應緩存，避免重複計算
- **非同步處理**：高頻資料流使用 AsyncIO

### 5.2 資料完整性

- **還原股價**：必須使用 Adjusted Close Price，避免除權息影響
- **時間隔離**：嚴格遵守「只用當天以前資料」原則，避免未來資料洩漏
- **資料驗證**：所有資料輸入必須驗證完整性

### 5.3 錯誤處理

- **優雅降級**：當某個模組失敗時，系統應能優雅降級，不影響其他模組
- **錯誤記錄**：所有錯誤都應記錄，用於 Error Learning Engine
- **重試機制**：API 呼叫應有重試機制

---

## 六、版本資訊

- **版本**：v0.9
- **建立日期**：2024-11-29
- **最後更新**：2024-11-29
- **對應知識庫版本**：所有 `*_CORRECTED.md` 文件

---

## 七、參考文件

本 Interface Spec 完全基於以下知識庫文件設計：

1. `J-GOD 股市聖經系統1_AI知識庫版_v1_CORRECTED.md`
2. `雙引擎與自主演化閉環_AI知識庫版_v1_CORRECTED.md`
3. `股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md`
4. `Path A  歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md`
5. `滾動式分析_AI知識庫版_v1_CORRECTED.md`
6. `JGOD_原始開發藍圖_清整強化版_AI知識庫版_v1_CORRECTED.md`
7. 其他相關 `*_CORRECTED.md` 文件

---

**End of Interface Spec**

