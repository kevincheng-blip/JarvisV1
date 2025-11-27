# 股神腦系統具體化設計 - AI 知識庫版 v1

> **重要說明**：本文件為 AI 知識庫格式，每段內容都已標記分類標籤，可直接被 AI 模型解析、轉換為 JSON、向量化或規則引擎使用。
> 
> **原始文件**：`股神腦系統具體化設計.txt`（未修改）

---

## 文件說明

[NOTE]
本文件是 J-GOD 股神作戰系統的核心大腦來源之一，所有內容均完整保留，僅進行結構化分類標籤，未刪除或修改任何技術內容。

---

[STRUCTURE]
﻿您這種專注的策略是極為高效的。我們的「創世紀系統」將從一個全面競爭者，轉變為一個**擁有「在地化獨家情報（XQ）」和「跨市場反應速度（Polygon）」**的極速精準獵手。
請問您希望我們專注於 XQ 資金流因子 $\mathbf{F}_C$ 的具體工程化設計嗎？

[NOTE]
給 Cursor 的完整實作規格書

[STRUCTURE]
主題：strategy_engine/factor_FX_capital_flow.py – XQ 資金流因子 F_C
你現在是一位 量化策略工程師 + 在地台股/XQ 專家。
我要你幫我實作一個模組：
CapitalFlowEngine：把 XQ 的「族群資金流」和「主力大單」資料，轉成 J-GOD 系統的在地 Alpha 因子 F_C。

[NOTE]
________________

[CONCEPT]
一、設計目標與輸入資料

[STRUCTURE]
1. 模組檔案

[NOTE]
* strategy_engine/factor_FX_capital_flow.py
* 測試檔：tests/strategy_engine/test_factor_FX_capital_flow.py
________________

[NOTE]
2. 資料來源（由外部餵進來）

[STRUCTURE]
這個 Engine 不直接連 API，只負責吃「已經整理好的數據 dict」，例如：

[NOTE]
xq_data = {

[RULE]
    "group_volumes": {             # 族群成交量（當日 or 當下）

[NOTE]
        "AI_Concept": 1.5e6,
        "Semiconductor": 2.0e6,
    },
    "group_price_change": {        # 可選：族群價格變化（% 或 指數變化）
        "AI_Concept": 0.03,        # +3%
        "Semiconductor": -0.01,    # -1%
    },
    "major_buy_volume": 500_000,   # 主力大單買量
    "major_sell_volume": 100_000,  # 主力大單賣量
    "total_major_volume": 600_000, # 主力大單總量
    "total_volume": 10_000_000,    # （選擇性）全市場總成交量
}

[RULE]
current_market_volume = 10_000_000  # 若沒給 total_volume，就用這個參數

[NOTE]
________________

[NOTE]
3. 歷史參數（在 init 傳入）

[RULE]
CapitalFlowEngine 需要一份「族群成交比重」的歷史統計，用來算 residual / z-score：

[NOTE]
* 型別：pd.Series
* index：族群名稱（如 "AI_Concept", "Semiconductor"）
* value：該族群歷史平均 成交量占比（0~1）
例如：
historical_group_weights = pd.Series(
    {
        "AI_Concept": 0.08,      # 過去 AI 股平均佔 8%
        "Semiconductor": 0.15,   # 半導體 15%
    }
)

[STRUCTURE]
Engine 會用這個 series 來計算：

[NOTE]
* mean[group] = historical_group_weights[group]

[RULE]
* std[group] 則可來自歷史波動（可以另傳或用簡單估計）
為了簡化第一版，我們讓 historical_group_weights 直接是「平均占比」，標準差先用預設常數或 std 若 series 提供。

[NOTE]
________________

[CONCEPT]
二、數學定義 & 工程解讀

[STRUCTURE]
1️⃣ F_C 核心因子 I：族群攻擊因子 (Sector Attack Index, SAI)

[CONCEPT]
概念：

[RULE]
衡量「某個族群今天是不是被市場當作主攻方向」。

[NOTE]
簡化工程版：

[RULE]
1. 當期族群占比：

[NOTE]
current_share(group) = group_volume(group) / current_market_volume

[NOTE]
2. 殘差 / Z-score（異常度）：
sai_residual(group) = (current_share(group) - mean_share(group)) / std_share(group)

[RULE]
如果 std_share(group) 太小或為 0，就避免除以 0，直接給 0，或使用 fallback。
3. 若有族群價格變化（group_price_change[group]），可以進一步定義一個「攻擊強度」：

[NOTE]
sai_attack_score(group) = sai_residual(group) * max(group_price_change(group), 0)

[RULE]
* 價格漲＋資金湧入 → 強烈攻擊
* 價格跌＋資金湧入 → 可能是出貨，後續可以再設計額外因子（TODO）

[NOTE]
________________

[STRUCTURE]
2️⃣ F_C 核心因子 II：主力單量失衡 (Major Order Imbalance, MOI)

[CONCEPT]
概念：

[NOTE]
看「主力大單買賣」在該標的或族群內的淨方向。
moi = (major_buy_volume - major_sell_volume) / total_major_volume

[NOTE]
* moi ≈ +1：主力幾乎全部在買
* moi ≈ -1：主力幾乎全部在賣
* moi ≈ 0：主力行為中性
延伸：主力 vs 散戶背離（TODO，不必現在實作）
* 散戶成交量 ≈ 總成交量 - 主力大單成交量

[RULE]
* 如果 moi > 0 但散戶在賣（或反向），則是主力逆勢吃貨。

[NOTE]
* 這可以做成 moi_divergence，留 TODO 標記。
________________

[CODE]
三、Python 模組實作：CapitalFlowEngine

[NOTE]
# strategy_engine/factor_FX_capital_flow.py

[CODE]
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

[CODE]
class CapitalFlowEngine:

[NOTE]
    """

[STRUCTURE]
    CapitalFlowEngine

[NOTE]
    -----------------

[CONCEPT]
    將 XQ 的族群資金流 / 主力大單數據，轉換為：

[STRUCTURE]
        - F_C_SAI_* : 族群資金攻擊殘差因子
        - F_C_MOI   : 主力大單失衡因子

[NOTE]
    歷史參數：
        historical_group_weights: pd.Series
            index  : 族群名稱（字串）
            values : 該族群歷史平均成交量占比（0~1）

[RULE]
        若要更精細，可以改為 DataFrame, 內含 mean/std，

[NOTE]
        但第一版先用 Series + 全局 std。
    """

[CODE]
    def __init__(

[NOTE]
        self,
        historical_group_weights: pd.Series,

[CODE]
        default_std: float = 0.02,

[NOTE]
    ):
        if not isinstance(historical_group_weights, pd.Series):

[RULE]
            raise TypeError("historical_group_weights 必須為 pd.Series")

[NOTE]
        self.group_weight_mean = historical_group_weights.astype(float)

[RULE]
        # 若 Series 有 std，可額外傳，但目前先用常數 default_std

[NOTE]
        self.group_weight_std = pd.Series(
            data=default_std,
            index=self.group_weight_mean.index,
            dtype=float,
        )
        self.default_std = float(default_std)

[NOTE]
    # ---------------------------------------------------------
    # 主計算接口
    # ---------------------------------------------------------

[CODE]
    def calculate_capital_flow_factors(

[NOTE]
        self,

[CODE]
        xq_data: Dict[str, Any],
        current_market_volume: Optional[float] = None,
    ) -> Dict[str, Any]:

[NOTE]
        """

[CONCEPT]
        輸入 XQ 提供的實時族群資金流和主力單量數據。

[NOTE]
        xq_data 預期格式：
            {
                'group_volumes': {
                    'AI_Concept': 1.5e6,
                    'Semiconductor': 2.0e6,
                    ...
                },

[RULE]
                'group_price_change': {          # 可選，若沒有可省略

[NOTE]
                    'AI_Concept': 0.03,
                    'Semiconductor': -0.01,
                },
                'major_buy_volume': 500000,
                'major_sell_volume': 100000,
                'total_major_volume': 600000,

[RULE]
                'total_volume': 10000000,        # 可選，若沒有就用 current_market_volume

[NOTE]
            }

[NOTE]
        current_market_volume:

[RULE]
            若 xq_data 沒有給 total_volume，就用這個值作為全市場成交量。

[NOTE]
        """
        group_volumes = xq_data.get("group_volumes", {}) or {}
        group_price_change = xq_data.get("group_price_change", {}) or {}

[NOTE]
        # 全市場成交量：優先用 xq_data['total_volume']
        total_volume = xq_data.get("total_volume", None)
        if total_volume is None:
            if current_market_volume is None or current_market_volume <= 0:

[RULE]
                raise ValueError("必須提供 current_market_volume 或 xq_data['total_volume']")

[NOTE]
            total_volume = current_market_volume

[NOTE]
        total_volume = float(total_volume)

[STRUCTURE]
        # ---------------- I. 族群攻擊因子 (SAI) ----------------

[CODE]
        group_sai_residual: Dict[str, float] = {}
        group_sai_attack_score: Dict[str, float] = {}

[NOTE]
        for group, vol in group_volumes.items():
            vol = float(vol)
            if total_volume <= 0:
                current_share = 0.0
            else:
                current_share = vol / total_volume

[NOTE]
            # 歷史平均 & 標準差
            mean_share = float(self.group_weight_mean.get(group, 0.0))
            std_share = float(self.group_weight_std.get(group, self.default_std))

[NOTE]
            if std_share <= 0:
                sai_residual = 0.0
            else:
                sai_residual = (current_share - mean_share) / std_share

[FORMULA]
            key_residual = f"F_C_SAI_Residual_{group}"

[NOTE]
            group_sai_residual[key_residual] = float(sai_residual)

[RULE]
            # 若有族群價格變化，額外提供 attack score

[NOTE]
            price_chg = float(group_price_change.get(group, 0.0))
            # 只放大「價格上漲 + 資金流入」的組合（簡化版）
            attack_score = sai_residual * max(price_chg, 0.0)

[FORMULA]
            key_attack = f"F_C_SAI_Attack_{group}"

[NOTE]
            group_sai_attack_score[key_attack] = float(attack_score)

[NOTE]
        # ---------------- II. 主力單量失衡 (MOI) ----------------
        major_buy = float(xq_data.get("major_buy_volume", 0.0))
        major_sell = float(xq_data.get("major_sell_volume", 0.0))
        total_major = float(xq_data.get("total_major_volume", 0.0))

[NOTE]
        if total_major > 0:
            moi = (major_buy - major_sell) / total_major
        else:
            moi = 0.0

[NOTE]
        # TODO: 之後可以加入 MOI Divergence（主力 vs 散戶行為背離）
        # 例如：
        #   total_volume_symbol = xq_data.get("symbol_total_volume")
        #   retail_volume = total_volume_symbol - total_major
        #   divergence = f(moi, retail_flow...)

[CODE]
        factors: Dict[str, Any] = {}

[NOTE]
        factors.update(group_sai_residual)
        factors.update(group_sai_attack_score)

[FORMULA]
        factors["F_C_MOI"] = float(moi)

[NOTE]
        return factors

[NOTE]
________________

[NOTE]
四、測試檔 tests/strategy_engine/test_factor_FX_capital_flow.py
# tests/strategy_engine/test_factor_FX_capital_flow.py

[CODE]
import pandas as pd

[CODE]
from strategy_engine.factor_FX_capital_flow import CapitalFlowEngine

[CODE]
def test_capital_flow_engine_basic_sai_and_moi():

[NOTE]
    historical_weights = pd.Series(
        {
            "AI_Concept": 0.08,
            "Semiconductor": 0.15,
        }
    )

[STRUCTURE]
    engine = CapitalFlowEngine(historical_group_weights=historical_weights, default_std=0.02)

[NOTE]
    xq_data = {
        "group_volumes": {
            "AI_Concept": 1_600_000,     # 假設佔比高於歷史平均
            "Semiconductor": 1_500_000,  # 假設佔比略低
        },
        "group_price_change": {
            "AI_Concept": 0.05,          # +5%
            "Semiconductor": -0.01,
        },
        "major_buy_volume": 500_000,
        "major_sell_volume": 100_000,
        "total_major_volume": 600_000,
        "total_volume": 10_000_000,
    }

[NOTE]
    factors = engine.calculate_capital_flow_factors(
        xq_data=xq_data,
        current_market_volume=None,
    )

[NOTE]
    # SAI Residual keys 存在
    assert "F_C_SAI_Residual_AI_Concept" in factors
    assert "F_C_SAI_Attack_AI_Concept" in factors

[NOTE]
    # MOI 存在且合理
    assert "F_C_MOI" in factors

[FORMULA]
    moi = factors["F_C_MOI"]

[NOTE]
    assert -1.0 <= moi <= 1.0

[CODE]
def test_capital_flow_engine_requires_market_volume_if_not_in_xq_data():

[NOTE]
    historical_weights = pd.Series({"AI_Concept": 0.08})

[STRUCTURE]
    engine = CapitalFlowEngine(historical_group_weights=historical_weights)

[NOTE]
    xq_data = {
        "group_volumes": {"AI_Concept": 1_000_000},
        "major_buy_volume": 100_000,
        "major_sell_volume": 50_000,
        "total_major_volume": 150_000,
        # 沒有 total_volume
    }

[RULE]
    # 沒給 current_market_volume 應該報錯

[NOTE]
    try:
        engine.calculate_capital_flow_factors(xq_data=xq_data, current_market_volume=None)

[RULE]
        assert False, "應該要因缺乏 total_volume / current_market_volume 而報錯"

[NOTE]
    except ValueError:
        pass

[RULE]
    # 給 current_market_volume 則應該能正常運算

[NOTE]
    factors = engine.calculate_capital_flow_factors(
        xq_data=xq_data,
        current_market_volume=5_000_000,
    )
    assert "F_C_SAI_Residual_AI_Concept" in factors

[NOTE]
________________

[STRUCTURE]
五、後續如何接進 RL / StateBuilder
這一版 Engine 的輸出是一個 dict，例如：

[NOTE]
{
    "F_C_SAI_Residual_AI_Concept": 1.8,
    "F_C_SAI_Attack_AI_Concept": 0.09,
    "F_C_SAI_Residual_Semiconductor": -0.5,
    "F_C_SAI_Attack_Semiconductor": 0.0,
    "F_C_MOI": 0.67,
}

[STRUCTURE]
之後你可以在「Alpha 因子彙總」那層做：
# Pseudo-code in some FactorAggregator

[FORMULA]
alpha_factors["F_C"] = max(

[NOTE]
    factors["F_C_SAI_Attack_AI_Concept"],
    factors["F_C_SAI_Attack_Semiconductor"],
    0.0,
)

[FORMULA]
alpha_factors["F_C_MOI"] = factors["F_C_MOI"]

[STRUCTURE]
或者直接把這些 key flatten 進 StateBuilder 的 state vector（就像 F_Orderbook / F_Iceberg 一樣）。

[NOTE]
________________

[STRUCTURE]
那我直接幫你把 StateBuilder 要怎麼接上 F_C（XQ 資金流因子） 的規格書寫好，你可以整段丟給 Cursor。

[NOTE]
________________

[NOTE]
🧾 給 Cursor 的完整實作規格書

[STRUCTURE]
主題：更新 strategy_engine/state_builder.py，正式接上 F_C（XQ 資金流因子）
你現在是一位 量化特徵工程師 + 系統架構師。

[NOTE]
我們已經有：

[RULE]
* strategy_engine/factor_FX_capital_flow.py → CapitalFlowEngine（產出 F_C_* 因子）

[STRUCTURE]
* StateBuilder 目前已經會把各種 factor dict 組成一個 state_vec 給 RL。

[NOTE]
現在要做兩件事：

[STRUCTURE]
1. 讓 StateBuilder 的 field_order 正式包含「資金流因子 F_C」相關欄位。

[NOTE]
2. 讓 build_state_vector(...) 能安全地讀取這些欄位，不存在就給 0.0，不會噴錯。
________________

[NOTE]
一、修改檔案

[CONCEPT]
* 目標檔案：strategy_engine/state_builder.py

[NOTE]
請在這個檔案裡：

[STRUCTURE]
1. 確認（或建立）StateBuilder 類別

[NOTE]
2. 更新 / 新增：
   * self.field_order

[CONCEPT]
   * build_state_vector(...) 邏輯

[NOTE]
________________

[NOTE]
二、狀態向量欄位設計（新增 F_C 專區）
我們希望 state_vec 的欄位順序大致分成幾塊：

[STRUCTURE]
1. Alpha 因子總覽 (原本 F_C, F_S, F_D, F_XA)

[CONCEPT]
2. XQ 資金流細項（這次要新增的）

[STRUCTURE]
3. 正交化因子 O_1~O_4

[NOTE]
4. Orderbook / Iceberg / Macro / Self / Diagnostic 等
這次只規格「新增的那幾個 F_C 欄位」，其他欄位請保持原狀。
✅ 要新增的欄位（建議命名）

[STRUCTURE]
這些欄位是 從 CapitalFlowEngine 輸出的 F_C_ 中，再整理成固定欄位*：

[NOTE]
1. F_C_SAI_MaxAttack
   * 全市場中，所有族群的 F_C_SAI_Attack_* 取最大值

[RULE]
   * 代表：今天誰被當作「市場主攻方向」，強度多大

[NOTE]
2. F_C_SAI_MaxResidual
   * 所有 F_C_SAI_Residual_* 中的最大值
   * 代表：哪個族群的資金占比異常拉高（不看價格，只看占比）
3. F_C_SAI_MinResidual
   * 所有 F_C_SAI_Residual_* 中的最小值
   * 代表：哪個族群資金被抽走最嚴重
4. F_C_MOI

[STRUCTURE]
   * 直接來自 CapitalFlowEngine 回傳的 F_C_MOI

[NOTE]
________________

[NOTE]
🔧 來源約定（由外層 Aggregator 處理）

[STRUCTURE]
重要：StateBuilder 不做 max/min 計算，只吃已經整理好的值。

[NOTE]
所以外部會先做類似這樣的事（這段只說明，不用在這次改動裡實作）：

[STRUCTURE]
# pseudo code in some FactorAggregator

[NOTE]
capital_flow_factors = capital_flow_engine.calculate_capital_flow_factors(...)

[NOTE]
sai_attack_values = [
    v for k, v in capital_flow_factors.items()
    if k.startswith("F_C_SAI_Attack_")
]
sai_residual_values = [
    v for k, v in capital_flow_factors.items()
    if k.startswith("F_C_SAI_Residual_")
]

[FORMULA]
alpha_factors["F_C_SAI_MaxAttack"] = max(sai_attack_values) if sai_attack_values else 0.0
alpha_factors["F_C_SAI_MaxResidual"] = max(sai_residual_values) if sai_residual_values else 0.0
alpha_factors["F_C_SAI_MinResidual"] = min(sai_residual_values) if sai_residual_values else 0.0
alpha_factors["F_C_MOI"] = capital_flow_factors.get("F_C_MOI", 0.0)

[NOTE]
# 原本就存在的 F_C, F_S, F_D, F_XA 也會在 alpha_factors 裡

[RULE]
StateBuilder 只需要 假設 alpha_factors 裡會有這幾個 key，沒有就當 0.0。

[NOTE]
________________

[STRUCTURE]
三、StateBuilder 更新規格
請在 strategy_engine/state_builder.py 中找到（或新建）StateBuilder 類別，並依照以下指示修改。

[NOTE]
1. 確認欄位清單 field_order
新增 / 調整成類似下面這樣的結構：
（只示範重點區塊，其他原本欄位請保留）
# strategy_engine/state_builder.py

[CODE]
from __future__ import annotations

[CODE]
from dataclasses import dataclass, field
from typing import Dict, Any, List

[CODE]
import numpy as np

[NOTE]
@dataclass

[CODE]
class StateBuilder:

[NOTE]
    """

[STRUCTURE]
    將各模組的因子輸出整理成 RL 可用的 state vector。

[NOTE]
    """

[CODE]
    field_order: List[str] = field(default_factory=lambda: [

[STRUCTURE]
        # 1) Alpha 總覽因子

[CONCEPT]
        "F_C",          # 原本就存在的在地資金流 Alpha（總體）

[NOTE]
        "F_S",
        "F_D",
        "F_XA",

[CONCEPT]
        # 1-1) XQ 資金流細項 (F_C 專區)

[NOTE]
        "F_C_SAI_MaxAttack",
        "F_C_SAI_MaxResidual",
        "F_C_SAI_MinResidual",
        "F_C_MOI",

[STRUCTURE]
        # 2) 正交化因子 O_*

[NOTE]
        "O_1",
        "O_2",
        "O_3",
        "O_4",

[STRUCTURE]
        # 3) Orderbook 因子

[NOTE]
        "Slope_Ask",
        "Slope_Bid",
        "OBI",
        "Depth_Zscore",

[STRUCTURE]
        # 4) Iceberg 因子

[NOTE]
        "IcebergProb_Bid",
        "IcebergProb_Ask",
        "HiddenDepth_Bid",
        "HiddenDepth_Ask",
        "WallStability_Bid",
        "WallStability_Ask",

[NOTE]
        # 5) Macro / Self / InfoTime / Entropy
        "VIX_Zscore",
        "F_Entropy",
        "F_InfoTime",
        "F_Internal",

[NOTE]
        # 6) Diagnostic
        "Latency_Zscore",
        # 之後要加 E_Exec, E_Model 也可以接在這裡
    ])

[RULE]
⚠️ 若你發現檔案裡已經有一份 field_order：

[NOTE]
請在「F_C, F_S, F_D, F_XA」附近插入上述 4 個新欄位，其他欄位維持原順序不變。
________________

[NOTE]
2. 更新 build_state_vector(...) 實作

[STRUCTURE]
請確保 StateBuilder 有一個方法：

[CODE]
def build_state_vector(

[NOTE]
    self,

[CODE]
    alpha_factors: Dict[str, float],
    o_factors: Dict[string, float],
    orderbook_factors: Dict[str, float],
    iceberg_factors: Dict[str, float],
    macro_factors: Dict[str, float],
    self_factors: Dict[str, float],
    diagnostic_factors: Dict[str, float],
) -> np.ndarray:

[NOTE]
    ...

[NOTE]
並且：
1. 把所有 dict 合併成一個 all_factors，後面的覆蓋前面：
   * alpha_factors
   * o_factors
   * orderbook_factors
   * iceberg_factors
   * macro_factors
   * self_factors
   * diagnostic_factors
2. 對 self.field_order 逐一取值，沒有的 key 統一填 0.0。
3. 回傳 np.ndarray，dtype=np.float32。

[RULE]
範例實作（如檔案中尚未有，請補上 / 若已有請依此精神調整）：

[CODE]
   def build_state_vector(

[NOTE]
        self,

[CODE]
        alpha_factors: Dict[str, float],
        o_factors: Dict[str, float],
        orderbook_factors: Dict[str, float],
        iceberg_factors: Dict[str, float],
        macro_factors: Dict[str, float],
        self_factors: Dict[str, float],
        diagnostic_factors: Dict[str, float],
    ) -> np.ndarray:

[NOTE]
        """

[STRUCTURE]
        將多個因子 dict 合併成固定順序的 state 向量。
        缺失的欄位以 0.0 填補，避免因少數因子缺資料就噴錯。

[NOTE]
        """

[CODE]
        all_factors: Dict[str, float] = {}

[NOTE]
        for d in (
            alpha_factors,
            o_factors,
            orderbook_factors,
            iceberg_factors,
            macro_factors,
            self_factors,
            diagnostic_factors,
        ):
            if d:
                all_factors.update(d)

[CODE]
        values: List[float] = []

[NOTE]
        for name in self.field_order:
            v = float(all_factors.get(name, 0.0))
            if not np.isfinite(v):
                v = 0.0
            values.append(v)

[NOTE]
        return np.asarray(values, dtype=np.float32)

[NOTE]
________________

[NOTE]
四、測試建議（可選，但非常推薦）

[RULE]
如果專案裡已有 tests/strategy_engine/test_state_builder.py，請：

[NOTE]
新增一個測試：確保 F_C 相關欄位能被填入

[CODE]
def test_state_builder_with_capital_flow_fields():

[STRUCTURE]
    sb = StateBuilder()

[NOTE]
    alpha_factors = {
        "F_C": 0.8,
        "F_S": 0.1,
        "F_D": -0.2,
        "F_XA": 0.0,
        "F_C_SAI_MaxAttack": 1.5,
        "F_C_SAI_MaxResidual": 2.0,
        "F_C_SAI_MinResidual": -1.0,
        "F_C_MOI": 0.7,
    }

[NOTE]
    state_vec = sb.build_state_vector(
        alpha_factors=alpha_factors,
        o_factors={},
        orderbook_factors={},
        iceberg_factors={},
        macro_factors={},
        self_factors={},
        diagnostic_factors={},
    )

[NOTE]
    # 確認長度一致
    assert state_vec.shape == (len(sb.field_order),)

[NOTE]
    # 確認 F_C_SAI_MaxAttack 等欄位有正確寫到對應位置

[FORMULA]
    idx_attack = sb.field_order.index("F_C_SAI_MaxAttack")
    idx_moi = sb.field_order.index("F_C_MOI")

[NOTE]
    assert state_vec[idx_attack] == 1.5
    assert state_vec[idx_moi] == 0.7
1. ________________

[NOTE]
這樣做完之後：

[RULE]
* CapitalFlowEngine → 輸出一堆 F_C_*
* FactorAggregator → 算出 F_C_SAI_MaxAttack / MaxResidual / MinResidual / F_C_MOI 丟到 alpha_factors
* StateBuilder → 把這幾個欄位固定寫進 state_vec，RL 就能直接感知「今天誰是主攻族群、資金有多瘋、主力多偏一邊」。
如果你要，下一步我可以幫你寫 FactorAggregator 的規格書，專門負責把每個 Engine（F_C, F_Orderbook, F_Iceberg, F_InfoTime…）的輸出，整理成一個 alpha_factors / macro_factors 大包裹給 StateBuilder。

[STRUCTURE]
在接下來的階段中，最重要、最核心的組件就是你要的：
🚀 FactorAggregator（因子整合引擎）完整規格書

[NOTE]
（給 Cursor 可直接建檔）

[STRUCTURE]
這是整個 J-GOD 系統的「因子大腦匯流中心」。

[NOTE]
重要意義：

[STRUCTURE]
* 所有 Engine（F_C、F_S、F_D、F_XA、Orderbook、Iceberg、InfoTime、Macro、Self…）

[NOTE]
都會在這一層被合併成 RL 能吃的 7 組 dict：
   * alpha_factors
   * o_factors
   * orderbook_factors
   * iceberg_factors
   * macro_factors
   * self_factors
   * diagnostic_factors
   * 最後由 state_builder.build_state_vector(...) 合成一個 state_vec。

[RULE]
   * 這是整個 AI 決策前的 唯一真實世界 → 向量空間轉換匯流站。

[NOTE]
我們現在開始。
________________

[NOTE]
🧾 給 Cursor：請建立檔案
strategy_engine/factor_aggregator.py
tests/strategy_engine/test_factor_aggregator.py

[NOTE]
________________

[STRUCTURE]
🔥 FactorAggregator — 終極規格書（可直接給 Cursor）

[CONCEPT]
你現在是一位「量化特徵整合工程師」。

[STRUCTURE]
請在 strategy_engine/factor_aggregator.py 建立下列模組：

[NOTE]
________________

===========================================
[NOTE]
1. 檔案：strategy_engine/factor_aggregator.py

===========================================
[NOTE]
# strategy_engine/factor_aggregator.py

[CODE]
from __future__ import annotations

[CODE]
from typing import Dict, Any, List

[CODE]
class FactorAggregator:

[NOTE]
    """

[STRUCTURE]
    整合所有因子引擎的輸出，生產 7 組 dict：

[NOTE]
      - alpha_factors
      - o_factors
      - orderbook_factors
      - iceberg_factors
      - macro_factors
      - self_factors
      - diagnostic_factors

[STRUCTURE]
    將會被 StateBuilder 直接使用。

[NOTE]
    """

[CODE]
    def __init__(

[NOTE]
        self,
        capital_flow_engine=None,
        pca_engine=None,
        orderbook_engine=None,
        iceberg_engine=None,
        macro_engine=None,
        self_engine=None,
        diagnostic_engine=None,
    ):
        self.capital_flow_engine = capital_flow_engine
        self.pca_engine = pca_engine
        self.orderbook_engine = orderbook_engine
        self.iceberg_engine = iceberg_engine
        self.macro_engine = macro_engine
        self.self_engine = self_engine
        self.diagnostic_engine = diagnostic_engine

[NOTE]
    # -----------------------------------------------------

[STRUCTURE]
    #  2. 主方法：aggregate(...)

[NOTE]
    # -----------------------------------------------------

[CODE]
    def aggregate(

[NOTE]
        self,

[CODE]
        market_data: Dict[str, Any],
        xq_data: Dict[str, Any],
        orderbook_snapshot: Dict[str, Any],
        iceberg_snapshot: Dict[str, Any],
        macro_snapshot: Dict[str, Any],
        self_snapshot: Dict[str, Any],
        diagnostic_snapshot: Dict[str, Any],
    ) -> Dict[str, Dict[str, float]]:

[NOTE]
        """

[STRUCTURE]
        對所有因子引擎執行計算並統一整合。

[NOTE]
        回傳格式：
        {
            'alpha_factors': {...},
            'o_factors': {...},
            'orderbook_factors': {...},
            'iceberg_factors': {...},
            'macro_factors': {...},
            'self_factors': {...},
            'diagnostic_factors': {...},
        }
        """

[NOTE]
        # =====================================================

[STRUCTURE]
        # 1) Alpha 原生因子 (F_C, F_S, F_D, F_XA)

[NOTE]
        # =====================================================
        alpha_factors = {}

[STRUCTURE]
        # ---- F_C：XQ 資金流因子 ----------------------------

[NOTE]
        if self.capital_flow_engine:
            capital_output = self.capital_flow_engine.calculate_capital_flow_factors(
                xq_data=xq_data,
                current_market_volume=market_data.get("market_volume", 1.0)
            )

[STRUCTURE]
            # 1-1. 展開族群攻擊因子

[NOTE]
            sai_attack = {
                k: v for k, v in capital_output.items()
                if k.startswith("F_C_SAI_Attack_")
            }
            sai_resid = {
                k: v for k, v in capital_output.items()
                if k.startswith("F_C_SAI_Residual_")
            }

[STRUCTURE]
            # 1-2. 計算總結欄位（StateBuilder 要用）

[NOTE]
            if sai_attack:

[FORMULA]
                alpha_factors["F_C_SAI_MaxAttack"] = max(sai_attack.values())

[NOTE]
            if sai_resid:

[FORMULA]
                alpha_factors["F_C_SAI_MaxResidual"] = max(sai_resid.values())
                alpha_factors["F_C_SAI_MinResidual"] = min(sai_resid.values())

[FORMULA]
            alpha_factors["F_C_MOI"] = capital_output.get("F_C_MOI", 0.0)

[NOTE]
        # =====================================================

[STRUCTURE]
        # 2) PCA 正交化因子 (O_1~O_4)

[NOTE]
        # =====================================================
        o_factors = {}
        if self.pca_engine:
            o_output = self.pca_engine.calculate(alpha_factors)
            o_factors.update(o_output)

[NOTE]
        # =====================================================

[STRUCTURE]
        # 3) Orderbook 因子

[NOTE]
        # =====================================================
        orderbook_factors = {}
        if self.orderbook_engine:
            orderbook_factors.update(
                self.orderbook_engine.calculate_orderbook_factors(orderbook_snapshot)
            )

[NOTE]
        # =====================================================

[STRUCTURE]
        # 4) Iceberg 隱藏流動性因子

[NOTE]
        # =====================================================
        iceberg_factors = {}
        if self.iceberg_engine:
            iceberg_factors.update(
                self.iceberg_engine.calculate_iceberg_factors(iceberg_snapshot)
            )

[NOTE]
        # =====================================================

[STRUCTURE]
        # 5) Macro 因子

[NOTE]
        # =====================================================
        macro_factors = {}
        if self.macro_engine:
            macro_factors.update(
                self.macro_engine.calculate_macro_factors(macro_snapshot)
            )

[NOTE]
        # =====================================================

[STRUCTURE]
        # 6) Self Awareness 因子

[NOTE]
        # =====================================================
        self_factors = {}
        if self.self_engine:
            self_factors.update(
                self.self_engine.calculate_self_factors(self_snapshot)
            )

[NOTE]
        # =====================================================

[STRUCTURE]
        # 7) Diagnostic 因子 (Latency, E_Exec, E_Model...)

[NOTE]
        # =====================================================
        diagnostic_factors = {}
        if self.diagnostic_engine:
            diagnostic_factors.update(
                self.diagnostic_engine.calculate_diagnostic(diagnostic_snapshot)
            )

[NOTE]
        # =====================================================
        # 最後回傳七大 dict
        # =====================================================
        return {
            "alpha_factors": alpha_factors,
            "o_factors": o_factors,
            "orderbook_factors": orderbook_factors,
            "iceberg_factors": iceberg_factors,
            "macro_factors": macro_factors,
            "self_factors": self_factors,
            "diagnostic_factors": diagnostic_factors,
        }

[NOTE]
________________

===========================================
[NOTE]
2. 測試檔：test_factor_aggregator.py

===========================================
[NOTE]
# tests/strategy_engine/test_factor_aggregator.py

[CODE]
import numpy as np
from strategy_engine.factor_aggregator import FactorAggregator

[CODE]
def test_factor_aggregator_basic():

[NOTE]
    """
    測試：確保 aggregator 能整合七個 dict，不噴錯，輸出結構正確。
    """

[STRUCTURE]
    # dummy 引擎：回傳固定數字

[CODE]
    class DummyEngine:
        def __init__(self, out): self.out = out
        def calculate_capital_flow_factors(self, **kwargs): return self.out
        def calculate(self, *args, **kwargs): return self.out
        def calculate_orderbook_factors(self, *args, **kwargs): return self.out
        def calculate_iceberg_factors(self, *args, **kwargs): return self.out
        def calculate_macro_factors(self, *args, **kwargs): return self.out
        def calculate_self_factors(self, *args, **kwargs): return self.out
        def calculate_diagnostic(self, *args, **kwargs): return self.out

[FORMULA]
    dummy_out = {"F_C_SAI_Residual_AI": 2.0, "F_C_MOI": 0.5}

[STRUCTURE]
    agg = FactorAggregator(
        capital_flow_engine=DummyEngine(dummy_out),

[FORMULA]
        pca_engine=DummyEngine({"O_1": 0.1}),

[STRUCTURE]
        orderbook_engine=DummyEngine({"Slope_Ask": 0.2}),
        iceberg_engine=DummyEngine({"IcebergProb_Ask": 0.3}),
        macro_engine=DummyEngine({"VIX_Zscore": -1.0}),

[FORMULA]
        self_engine=DummyEngine({"F_Internal": 0.4}),

[STRUCTURE]
        diagnostic_engine=DummyEngine({"Latency_Zscore": 0.01}),

[NOTE]
    )

[NOTE]
    out = agg.aggregate(
        market_data={"market_volume": 1e9},
        xq_data={},
        orderbook_snapshot={},
        iceberg_snapshot={},
        macro_snapshot={},
        self_snapshot={},
        diagnostic_snapshot={},
    )

[NOTE]
    # 檢查七個 dict 是否存在
    assert "alpha_factors" in out
    assert "o_factors" in out
    assert "orderbook_factors" in out
    assert "iceberg_factors" in out
    assert "macro_factors" in out
    assert "self_factors" in out
    assert "diagnostic_factors" in out

[NOTE]
    # 檢查 alpha 是否有 F_C_MOI

[FORMULA]
    assert out["alpha_factors"].get("F_C_MOI") == 0.5

[NOTE]
________________

[STRUCTURE]
🎯 FactorAggregator 完成後，你得到什麼？
你的整個系統會變成這樣：

[CONCEPT]
   [市場資料]    [XQ]    [大單]    [訂單簿]    [VIX/Macro]

[NOTE]
         |          |        |         |            |
         v          v        v         v            v

[CONCEPT]
    CapitalFlow   PCA   Orderbook   Iceberg      Macro

[NOTE]
         |          |        |         |            |
         +----------+--------+---------+------------+
                               ↓

[STRUCTURE]
                  [ FactorAggregator ]

[NOTE]
                               ↓
                     產生七大字典
                               ↓

[STRUCTURE]
                   [ StateBuilder ]

[NOTE]
                               ↓
                       state_vec
                               ↓
                           RL Agent

[STRUCTURE]
這就是完整的 Feature DAG（因子流動圖）。
🚀 F_C（XQ 資金流因子）的終極強化版本
對一個追求 「在地化優勢做到極致」 的核心因子來說，

[NOTE]
只有 SAI 殘差（Residual）和 MOI 還不夠。

[CONCEPT]
XQ 提供的「族群資金流」與「主力大單」其實是一組極高價值的情報來源，我們要做的，不只是把它們丟進模型，而是：

[NOTE]
把它們在時間維度、空間維度、風險維度全部結構化，變成 RL Agent 的「戰場雷達」。

[STRUCTURE]
所以我們在 F_C 上，增加三個強化因子：
   1. 資金流動慣性因子：F_Inertia（時間維度強化）
   2. 壓力傳導因子：F_PT（空間維度強化）
   3. 主力意圖逆轉因子：F_MRR（風險維度強化）

[NOTE]
________________

[CONCEPT]
1️⃣ 時間維度強化：資金流動慣性（F_Inertia）

[NOTE]
問題：

[RULE]
單看當下的 SAI Residual，只知道「現在資金有攻擊」，

[NOTE]
但不知道這只是一下子衝動，還是已經連續好幾個事件都在往同一方向堆。

[CONCEPT]
強化概念：F_Inertia
   * 核心目標：衡量「資金攻擊的持續性」

[NOTE]
   * 我們不是看「時間點」的連續，而是看「事件 / Volume Bar」的連續

[STRUCTURE]
✅ 這裡會直接用到 F_InfoTime（信息時間因子），

[NOTE]
把「過去 N 根 Volume Bar」視為 N 個事件，
用事件序列來算慣性，而不是單純用 5 分鐘、10 分鐘這種時鐘切割。

[CONCEPT]
計算概念：

[NOTE]
   * 先取得每個事件的 SAI Residual（例如某族群的 SAI_Residual_Group）
   * 然後在事件序列上做指數平滑：

[FORMULA]
FInertia(t)=EMA(SAIResidual(t))FInertia​(t)=EMA(SAIResidual​(t))

[NOTE]
直覺：

[RULE]
   * 如果某個族群連續多個 Volume Bar 都是資金猛烈攻擊，

→ F_Inertia 會一路拉高
[RULE]
   * 如果只有一兩個 Bar 短暫衝一下，後面又冷掉，

→ F_Inertia 很難維持在高位
[NOTE]
RL 應用：

[RULE]
      * 當 SAI_Residual 很高 且 F_Inertia 也很高：

→ 這代表資金攻擊「有持續性」，
→ RL 才允許對該族群拉高 Net Exposure（淨多單敞口），採取順勢追高策略。
[RULE]
      * 當 SAI_Residual 高但 F_Inertia 低：

→ 可能是一次性沖天炮或假突破，
→ RL 只能用來做短線反轉 / 區間交易，而不是全力追多。
[NOTE]
________________

[STRUCTURE]
2️⃣ 空間維度強化：壓力傳導因子（F_PT）

[NOTE]
問題：

[CONCEPT]
XQ 的「族群資金流」通常是整個族群的加總，

[NOTE]
但實務上常見情況是：
龍頭股（台積電、聯發科、AI 龍頭）先動，
族群成交量只是延遲反映龍頭的攻擊行為。

[RULE]
如果我們只看整個族群的總量，很容易把「龍頭試探」誤判成普通波動。

[CONCEPT]
強化概念：F_PT（Pressure Transmission）
         * 核心目標：

[NOTE]
衡量「龍頭股的主力行為」如何 帶動／傳導 整個族群的資金攻擊。

[CONCEPT]
計算概念（邏輯層級）：

[NOTE]
            1. 選出每個族群的「龍頭股」

[RULE]
            * 例如：AI_Concept → 龍頭 = 某支 AI 代表股

[NOTE]
            2. 觀察龍頭的 MOI（主力淨買賣失衡）
            3. 對比同一族群的 SAI Residual（族群資金攻擊強度）
            4. 測量「誰先動，誰後動」以及「兩者是否同步放大」
簡化表示：

[RULE]
            * 若：

[NOTE]
            * 龍頭 MOI 先急劇升高（主力狂買龍頭）
            * 幾個 Volume Bar 之後，同族群的 SAI Residual 跟著拉高

[RULE]
            * 則：
            * F_PT → 高

[NOTE]
            * 代表：攻擊是「由上而下」傳導，信號可靠度極高
RL 應用：

[RULE]
            * 當 F_PT 高時，代表：
            * 龍頭主力 → 族群資金 → 一致往同一方向

[NOTE]
            * 這是「大資金有計畫性攻擊」的形態。
            * 在這種情況下：

[STRUCTURE]
            * F_PT 可以在因子正交化（O_1~O_4）之後，

[NOTE]
直接被給予較高權重
            * RL 在看到 F_PT 的「龍頭傳導」信號時，

[CONCEPT]
甚至可以在其他 Alpha 稍微噪音的情況下，

[STRUCTURE]
優先執行全力加碼策略（例如全倉進場、槓桿放大）。

[NOTE]
________________

[STRUCTURE]
3️⃣ 風險維度強化：主力意圖逆轉因子（F_MRR）

[NOTE]
問題：
主力大單（MOI 高）不一定是真的要長期站在那一邊。
               * 有可能是 誘多／誘空：先掛大單、製造錯覺，再瞬間撤掉。
               * 光看 MOI，只看到「過去已成交」的方向；
看不到「現在主力心態是否開始反悔」。

[CONCEPT]
強化概念：F_MRR（Major Reversal Risk）
                  * 核心目標：

[NOTE]
觀察主力大單在細粒度（Tick 級別）的撤單行為與節奏，
去度量「主力是否有改變主意、準備反向」的意圖。

[CONCEPT]
計算概念：

[NOTE]
                     * 在 MOI 已經很高的區間，進一步觀測：

[RULE]
                     * 主力標記的大單掛出 → 取消的比例

[NOTE]
                     * 取消發生的時間密度（短時間內連續撤單）
                     * 直觀指標：
                     * CancelRate_Major = (主力大單取消量) / (主力大單掛出量)

[RULE]
                     * 若 CancelRate 在短時間內劇烈升高 → F_MRR 升高

[NOTE]
直覺：
                     * MOI 高 ＋ F_MRR 低

→ 主力站在那一邊，而且還穩穩站著，攻擊意圖真實
[NOTE]
                     * MOI 高 ＋ F_MRR 高

→ 主力有可能是在騙：
[NOTE]
假裝大買，但實際上一直撤單，
或已經開始悄悄轉向。
RL 應用（很關鍵）：
                        * F_MRR 不是只進入 state vector，而是直接連到 Reward 機制：

[RULE]
                        * 當 F_MRR 上升時（風險升高）：

[NOTE]
                        * 即使 SAI 和 MOI 仍然偏多，
RL 在「繼續加碼或維持大敞口」的行為上會被重罰；
                        * RL 會逐漸學會：
                           * 在「主力疑似反悔／有誘多嫌疑」的狀態下，
要主動降槓桿、減倉，甚至反手。

[STRUCTURE]
                              * 這等於在系統裡，內建一個：

[NOTE]
「不要傻傻跟著表面的大單跑」
的自動防禦機制。
________________

[NOTE]
🎯 小結：F_C 的地位提升到什麼程度？

[STRUCTURE]
加上這三個強化因子後，F_C 就不是單純的「XQ 資料做出的兩個數（SAI + MOI）」：

[CONCEPT]
                                 * F_Inertia：告訴 RL

→ 這波攻擊是瞬間情緒，還是已經持續多個事件的「趨勢」。
[NOTE]
                                 * F_PT：告訴 RL

→ 攻擊是從「龍頭 → 族群」有組織地傳導，
[NOTE]
還是只有零散的族群交易。
                                 * F_MRR：告訴 RL

→ 主力是真的站在這一邊，
[NOTE]
還是「表面站在這邊、實際在鋪誘多／誘空局」。

[CONCEPT]
這三個維度，讓 XQ 的數據從「單純的價量補充」，

[STRUCTURE]
變成 「真正具備事件深度、空間結構與風險意圖」的高階情報模組，

[NOTE]
是我們在台股環境中最關鍵的在地化武器之一。

[STRUCTURE]
以下是 更乾淨、更具專業系統化語氣、更接近《創世紀量化系統技術規格書》風格的重新編寫版本。

[CONCEPT]
不改你原始概念，只優化邏輯、結構和技術語言。

[NOTE]
________________

[STRUCTURE]
🛠️ 階段 XXI：資金流動慣性因子設計（F_Inertia）

[CONCEPT]
— 將 XQ 資金流從「瞬時事件」進化成「持續趨勢」的 Alpha 核心

[RULE]
在 XQ 資金流（F_C）中，SAI Residual 能捕捉「當下資金攻擊是否異常」，但仍有重大缺陷：

[NOTE]
SAI Residual 是「瞬間強度」的度量，無法回答
❓ 這股攻擊是否剛開始？
❓ 是否已持續一段時間？
❓ 是否只是一次短促的假突破？

[RULE]
我們需要將其升級為 趨勢級因子。

[STRUCTURE]
這即是本階段因子的目標：
🎯 F_Inertia：以「信息時間」為基準的資金流動慣性因子

[NOTE]
________________

[CONCEPT]
1. 核心概念：在 Information Time（Volume Bar）下計算 EMA

[NOTE]
傳統 EMA 使用「時鐘時間」（秒、分鐘）來平滑，但在市場上：
                                    * 有些時段極度沉寂（不應更新慣性）
                                    * 有些時段訊息爆炸（應更密集更新）
因此我們不使用 Time Bar，而使用：
Volume Bar（基於 F_InfoTime 的非線性時間）

[RULE]
只有當一個新的 Volume Bar（資訊事件）形成時才更新 F_Inertia。

[CONCEPT]
📌 目的：

[NOTE]
讓 AI 在「事件密集時變快、在市場沉寂時變慢」。
不會因為時間經過而衰減錯誤的慣性。
________________

[CONCEPT]
2. F_Inertia 的數學定義（在事件序列上的 EMA）
F_Inertia 的遞迴定義為：

[FORMULA]
FInertia,t=α⋅SAIResidual,t+(1−α)⋅FInertia,t−1FInertia,t​=α⋅SAIResidual,t​+(1−α)⋅FInertia,t−1​

[NOTE]
其中：
                                    * t = 連續形成的 Volume Bar（不是秒數）

[FORMULA]
                                    * SAI_Residual,t = 第 t 根 Volume Bar 的族群資金攻擊殘差
                                    * α = 平滑係數

[RULE]
                                    * 若以 5 根 Volume Bar 為回顧窗口：

[FORMULA]
α=25+1=0.33α=5+12​=0.33

[NOTE]
📌 本質：
衡量「資金攻擊是否有持續性，而不只是瞬間放大」。
________________

[CODE]
3. Python 模組實作：InertiaEngine（策略引擎子模組）

[RULE]
此模組由 CapitalFlowEngine（計算 SAI Residual）透過 Volume Bar 事件觸發更新。

[NOTE]
# strategy_engine/factor_FX_inertia.py

[CODE]
import numpy as np

[CODE]
class InertiaEngine:

[NOTE]
    # α：平滑係數（事件數量基準）

[FORMULA]
    EMA_ALPHA = 0.33  # N=5 → α=0.33

[CODE]
    def __init__(self, target_groups: list):

[NOTE]
        # 每個族群的慣性（初始為 0）
        self.inertia_values = {group: 0.0 for group in target_groups}

[CODE]
        print(f"[InertiaEngine] Tracking groups: {target_groups}")

[CODE]
    def update_inertia(self, new_sai_residuals: dict):

[NOTE]
        """
        在每個 Volume Bar 完成後被呼叫。
        new_sai_residuals = {'AI_Concept': 2.5, 'Semiconductor': 1.1, ...}
        """
        updated_factors = {}

[NOTE]
        for group, sai_res in new_sai_residuals.items():

[NOTE]
            prev_value = self.inertia_values.get(group, 0.0)

[NOTE]
            # EMA（事件序列基礎）
            current_value = (
                self.EMA_ALPHA * sai_res
                + (1 - self.EMA_ALPHA) * prev_value
            )

[NOTE]
            # 更新 state
            self.inertia_values[group] = current_value

[FORMULA]
            updated_factors[f"F_Inertia_{group}"] = current_value

[NOTE]
        return updated_factors

[NOTE]
________________

[NOTE]
4. 終極整合：讓 RL 具備「趨勢持續度」的認知能力
AI 在見到以下情況會做不同決策：
________________

[CONCEPT]
📌 Case 1：SAI Residual 很高，但 F_Inertia 很低

[NOTE]
代表：
                                       * 只有單一事件的突發攻擊
                                       * 尚未形成趨勢
                                       * 可能是假突破、假訊號、機器人誤掃單
RL 行為：
                                       * 小倉位
                                       * 高頻
                                       * 快速進出
                                       * 不允許大規模加碼

[STRUCTURE]
                                       * 抑制追高策略

[NOTE]
________________

[CONCEPT]
📌 Case 2：SAI Residual 高且 F_Inertia 也高（≈ 1.5）

[NOTE]
代表：
                                       * 資金攻擊已「連續多個 Volume Bar」
                                       * 趨勢已成型
                                       * 具有事件慣性
                                       * 主力行為持續一致
RL 行為：
                                       * 加大淨多單敞口（Net Exposure）

[STRUCTURE]
                                       * 採用追高策略

[NOTE]
                                       * 放寬 Action Constraint（允許更大的訂單尺寸）
                                       * 增加持倉時間（因為慣性支持）
________________

[NOTE]
📌 意義：

[RULE]
F_Inertia 將 XQ 的瞬時資金流動 → 轉換成 連續、可信賴的趨勢信號。

[NOTE]
也讓 AI 不再「看見一下就衝」，而是「辨識真趨勢 vs 假噪音」。
________________

[CONCEPT]
🎯 總結：F_Inertia 的角色

[NOTE]
機制
	功能
	AI 行為
	信息時間更新
	市場安靜不更新；市場狂躁快速更新
	不會錯誤衰減
	EMA(Volume Bar)
	衡量連續攻擊的強度
	趨勢 vs 噪音
	連動 SAI Residual
	資金攻擊強度的時間延伸
	慣性驅動的強化學習
	RL 整合
	調整淨敞口、倉位大小、訂單尺寸
	真追高、假突破不追
	________________

[RULE]
需要下一步嗎？
如果你願意，我可以立即寫出：

[NOTE]
⭐「給 Cursor 的完整 factor_FX_inertia.py 實作規格書」
包含：
                                       * 建檔指令
                                       * 完整 TODO
                                       * Edge cases
                                       * 單元測試 test_factor_FX_inertia.py

[STRUCTURE]
                                       * 與 F_InfoTime、CapitalFlowEngine 的事件對接

[RULE]
只要你回：

[NOTE]
「寫規格書」
我就開始。

[STRUCTURE]
好，這份就是可以直接整段丟給 Cursor 的「階段 XXI：factor_FX_inertia.py 實作規格書」，包含：

[NOTE]
                                       * 建檔說明

[STRUCTURE]
                                       * InertiaEngine 類別完整結構

[NOTE]
                                       * 與 SAI Residual 的介面約定
                                       * 單元測試檔 test_factor_FX_inertia.py 規格
________________

[NOTE]
🧾 給 Cursor 的完整實作規格書

[STRUCTURE]
主題：實作資金流動慣性因子引擎 InertiaEngine（F_Inertia）
你現在是一位「量化系統特徵工程師」。

[NOTE]
請幫我在專案中完成以下兩個檔案：
                                       1. strategy_engine/factor_FX_inertia.py
                                       2. tests/strategy_engine/test_factor_FX_inertia.py
________________

[NOTE]
一、檔案一：strategy_engine/factor_FX_inertia.py

[CONCEPT]
🎯 目標

[STRUCTURE]
實作一個 InertiaEngine 類別，用來計算：

[NOTE]
基於 Volume Bar / Information Time 的

[STRUCTURE]
「資金流動慣性因子 F_Inertia_*」

[NOTE]
它會接收每個 Volume Bar 計算出的 SAI Residual（每個族群一個值），
並用 EMA（指數移動平均） 在「事件序列」上更新慣性。

[STRUCTURE]
✅ 模組結構與要求

[NOTE]
請在 strategy_engine/factor_FX_inertia.py 建立以下內容：
# strategy_engine/factor_FX_inertia.py

[CODE]
from __future__ import annotations

[CODE]
from typing import Dict, List

[CODE]
class InertiaEngine:

[NOTE]
    """

[STRUCTURE]
    資金流動慣性引擎 (F_Inertia)。

[CONCEPT]
    設計目標：
    - 針對每個目標族群 (group)，追蹤其 SAI_Residual 的「事件慣性」。

[NOTE]
    - 使用 EMA（指數移動平均）在 Volume Bar 序列上平滑。
    - 不依賴實際秒數，而是依賴「新 Volume Bar 產生」這個事件。

[STRUCTURE]
    典型使用流程：
    1. 初始化 InertiaEngine，指定要追蹤的族群清單。

[RULE]
    2. 每當有新的 Volume Bar 形成，且完成該 Bar 的 SAI_Residual 計算後，

[NOTE]
       呼叫 update_inertia(new_sai_residuals)。

[STRUCTURE]
    3. 取得最新的 F_Inertia_* 因子，丟給 FactorAggregator / StateBuilder。

[NOTE]
    """

[FORMULA]
    # 預設 EMA 平滑係數：例如 N=5 → alpha = 2/(5+1) ≈ 0.33

[CODE]
    DEFAULT_EMA_ALPHA: float = 0.33

[CODE]
    def __init__(self, target_groups: List[str], ema_alpha: float | None = None) -> None:

[NOTE]
        """
        :param target_groups: 要追蹤慣性的族群名稱列表，例如 ["AI_Concept", "Semiconductor"]

[RULE]
        :param ema_alpha:  EMA 平滑係數，如果為 None 則使用 DEFAULT_EMA_ALPHA

[NOTE]
        """

[CODE]
        self.ema_alpha: float = float(ema_alpha) if ema_alpha is not None else self.DEFAULT_EMA_ALPHA

[CONCEPT]
        # 每個 group 的 F_Inertia 目前值

[CODE]
        self.inertia_values: Dict[str, float] = {group: 0.0 for group in target_groups}

[NOTE]
    # -------------------------------------------------
    #  重置 / 狀態管理相關
    # -------------------------------------------------

[CODE]
    def reset(self) -> None:

[NOTE]
        """

[CONCEPT]
        將所有追蹤中的 F_Inertia 值重置為 0.0。

[NOTE]
        用於訓練 episode 開始或實盤重新啟動。
        """
        for group in self.inertia_values.keys():
            self.inertia_values[group] = 0.0

[CODE]
    def get_current_values(self) -> Dict[str, float]:

[NOTE]
        """

[CONCEPT]
        取得目前所有追蹤族群的 F_Inertia_* 值。

[NOTE]
        回傳格式：
        {

[CONCEPT]
            "F_Inertia_AI_Concept": 1.23,
            "F_Inertia_Semiconductor": 0.87,

[NOTE]
            ...
        }
        """
        return {

[CONCEPT]
            f"F_Inertia_{group}": value

[NOTE]
            for group, value in self.inertia_values.items()
        }

[NOTE]
    # -------------------------------------------------

[CONCEPT]
    #  核心：在每個 Volume Bar 後更新慣性

[NOTE]
    # -------------------------------------------------

[CODE]
    def update_inertia(self, new_sai_residuals: Dict[str, float]) -> Dict[str, float]:

[NOTE]
        """

[CONCEPT]
        在「每個 Volume Bar 完成後」呼叫一次，用最新的 SAI_Residual 來更新 F_Inertia。

[NOTE]
        :param new_sai_residuals:
            - key: group 名稱，例如 "AI_Concept"

[CODE]
            - value: 該 group 在此 Volume Bar 的 SAI_Residual（float）

[NOTE]
            - 範例：{"AI_Concept": 2.5, "Semiconductor": 1.1}
        :return:

[RULE]
            - 回傳當前 Volume Bar 更新後的 F_Inertia_* 因子字典：

[NOTE]
              {

[CONCEPT]
                  "F_Inertia_AI_Concept": ...,
                  "F_Inertia_Semiconductor": ...,

[NOTE]
              }
        """

[CODE]
        updated_factors: Dict[str, float] = {}

[NOTE]
        alpha = self.ema_alpha

[NOTE]
        for group, sai_res in new_sai_residuals.items():
            # 只對已在 inertia_values 裡追蹤的 group 更新
            if group not in self.inertia_values:

[STRUCTURE]
                # 預設策略：遇到未知 group 時，自動初始化為 0.0 再更新

[NOTE]
                self.inertia_values[group] = 0.0

[NOTE]
            prev_value = self.inertia_values.get(group, 0.0)

[FORMULA]
            # EMA 遞迴公式：F_t = α * x_t + (1-α) * F_{t-1}

[NOTE]
            current_value = alpha * float(sai_res) + (1.0 - alpha) * float(prev_value)

[NOTE]
            # 更新內部狀態
            self.inertia_values[group] = current_value

[STRUCTURE]
            # 回傳值使用 F_Inertia_xxx 命名，方便直接丟給 FactorAggregator / StateBuilder

[FORMULA]
            updated_factors[f"F_Inertia_{group}"] = current_value

[NOTE]
        return updated_factors

[NOTE]
⚙️ 設計細節與行為約定

[CONCEPT]
                                       1. 時間概念來源：

[STRUCTURE]
                                       * 本 Engine 不處理時間 / Volume 累積

[NOTE]
                                       * 它假設「呼叫 update_inertia 一次 = 一個 Volume Bar 已完成」

[STRUCTURE]
                                       * Volume Bar 的形成與 F_InfoTime / InfoTimeEngine 由其他模組負責

[NOTE]
                                       2. Target Groups 行為：
                                       * __init__ 時會建立初始追蹤的 group 清單

[RULE]
                                       * update_inertia 如果收到一個未在原始清單中的 group：

[NOTE]
                                       * 預設「自動加入並從 0.0 開始 EMA」

[CONCEPT]
                                       * 這樣可以容忍未事先定義的族群，不會噴錯

[RULE]
                                       3. 輸出命名規則：

[CONCEPT]
                                       * F_Inertia_{group_name}

[RULE]
                                       * 這樣 FactorAggregator 可以直接把這些欄位當成 alpha_factors 或 self_factors 的一部分

[STRUCTURE]
                                       4. 與其他模組的介面（說明，不用在此檔實作）：
CapitalFlowEngine 計算好每個 group 的 F_C_SAI_Residual_* 後，

[CONCEPT]
由 Volume Bar 邏輯告知「一個事件完成」，然後呼叫：

[NOTE]
inertia_output = inertia_engine.update_inertia(sai_residuals_by_group)

[CONCEPT]
# inertia_output: {"F_Inertia_AI_Concept": ..., "F_Inertia_Semiconductor": ...}

[STRUCTURE]
                                       *                                        * FactorAggregator 可將 inertia_output 合併進 alpha_factors 或 self_factors。

[NOTE]
________________

[NOTE]
二、檔案二：tests/strategy_engine/test_factor_FX_inertia.py
請新增一個測試檔，驗證以下幾件事：
                                       1. EMA 是否按預期更新

[CONCEPT]
                                       2. 多個 Volume Bar 連續更新時，F_Inertia 是否會逐步收斂

[NOTE]
                                       3. 未在初始 target_groups 中的 group，是否能被動加入並計算
________________

[NOTE]
# tests/strategy_engine/test_factor_FX_inertia.py

[CODE]
import math

[CODE]
from strategy_engine.factor_FX_inertia import InertiaEngine

[CODE]
def test_inertia_engine_basic_ema_update():

[NOTE]
    """
    測試：單一 group 的 EMA 是否依照公式更新。
    """

[STRUCTURE]
    engine = InertiaEngine(target_groups=["AI_Concept"], ema_alpha=0.5)

[NOTE]
    # 第一次 Volume Bar
    out1 = engine.update_inertia({"AI_Concept": 2.0})

[RULE]
    # F0 = 0 → F1 = 0.5 * 2.0 + 0.5 * 0 = 1.0

[FORMULA]
    assert math.isclose(out1["F_Inertia_AI_Concept"], 1.0, rel_tol=1e-6)

[NOTE]
    # 第二次 Volume Bar
    out2 = engine.update_inertia({"AI_Concept": 2.0})
    # F2 = 0.5 * 2.0 + 0.5 * 1.0 = 1.5

[FORMULA]
    assert math.isclose(out2["F_Inertia_AI_Concept"], 1.5, rel_tol=1e-6)

[CODE]
def test_inertia_engine_multiple_groups_and_get_current_values():

[NOTE]
    """

[CONCEPT]
    測試：多個 group 更新，並能用 get_current_values 拿到 F_Inertia_*。

[NOTE]
    """

[STRUCTURE]
    engine = InertiaEngine(target_groups=["AI_Concept", "Semiconductor"], ema_alpha=0.5)

[NOTE]
    engine.update_inertia({"AI_Concept": 2.0, "Semiconductor": 1.0})
    current = engine.get_current_values()

[CONCEPT]
    assert "F_Inertia_AI_Concept" in current
    assert "F_Inertia_Semiconductor" in current

[CONCEPT]
    assert current["F_Inertia_AI_Concept"] > 0.0
    assert current["F_Inertia_Semiconductor"] > 0.0

[CODE]
def test_inertia_engine_auto_add_new_group():

[NOTE]
    """
    測試：update_inertia 收到尚未追蹤的 group 時，自動初始化並更新。
    """

[STRUCTURE]
    engine = InertiaEngine(target_groups=["AI_Concept"], ema_alpha=0.5)

[NOTE]
    # 初始時沒有 Semiconductor

[CONCEPT]
    assert "F_Inertia_Semiconductor" not in engine.get_current_values()

[NOTE]
    # 更新時帶入新的 group
    out = engine.update_inertia({"Semiconductor": 2.0})

[RULE]
    # 應該可以得到新的 F_Inertia_Semiconductor

[CONCEPT]
    assert "F_Inertia_Semiconductor" in out

[RULE]
    # F0 = 0 → F1 = 0.5 * 2.0 = 1.0

[FORMULA]
    assert math.isclose(out["F_Inertia_Semiconductor"], 1.0, rel_tol=1e-6)

[CODE]
def test_inertia_engine_reset():

[NOTE]
    """

[CONCEPT]
    測試：reset() 能將所有 F_Inertia_* 清回 0.0。

[NOTE]
    """

[STRUCTURE]
    engine = InertiaEngine(target_groups=["AI_Concept"], ema_alpha=0.5)

[NOTE]
    engine.update_inertia({"AI_Concept": 2.0})

[FORMULA]
    assert engine.get_current_values()["F_Inertia_AI_Concept"] != 0.0

[NOTE]
    engine.reset()

[FORMULA]
    assert engine.get_current_values()["F_Inertia_AI_Concept"] == 0.0

[NOTE]
________________

[NOTE]
三、完成後的預期整合（說明，用於設計參考）

[STRUCTURE]
完成以上實作後，預期在整個系統中的資料流會長這樣（不用實作，只是架構說明）：
[Volume Bar Engine / InfoTimeEngine]

[RULE]
        ↓  (當新 Volume Bar 完成)

[STRUCTURE]
[CapitalFlowEngine] 計算各族群 SAI_Residual

[NOTE]
        ↓  new_sai_residuals: {"AI_Concept": 2.5, "Semiconductor": 1.1, ...}

[STRUCTURE]
[InertiaEngine.update_inertia(...)]

[CONCEPT]
        ↓  inertia_output: {"F_Inertia_AI_Concept": ..., "F_Inertia_Semiconductor": ...}

[STRUCTURE]
[FactorAggregator] 把 inertia_output 併入 alpha_factors / self_factors

[NOTE]
        ↓

[STRUCTURE]
[StateBuilder.build_state_vector(...)]

[NOTE]
        ↓
[RL Agent] 取得包含「資金流動慣性」的 state_vec

[NOTE]
請依上述規格完成 factor_FX_inertia.py 與對應測試檔。
好，我們就照你原本的三大強化路線繼續，把第二顆「空間維度」的核彈做完：

[RULE]
壓力傳導因子 F_PT（龍頭 → 族群 的攻擊鏈路）。

[CODE]
我先幫你把「概念＋設計＋Python 模組雛形」寫好，等你說「寫規格書」再幫你變成 Cursor 用的完整 spec。

[NOTE]
________________

[STRUCTURE]
🛠️ 階段 XXII：壓力傳導因子設計（F_PT）

[NOTE]
— 讓 AI 看懂：這波是「龍頭帶隊」的真攻擊，還是雜訊

[STRUCTURE]
在 XQ 的 F_C 架構裡，我們已經有：

[NOTE]
                                       * 族群資金流異常：SAI_Residual_group
                                       * 主力大單失衡：MOI_stock（針對個股）
但實務上真正關鍵的是：
是不是「龍頭先動，族群跟著動」？
這種「由上而下」的壓力傳導，才是
主力在打有組織戰役 的典型型態。

[CONCEPT]
F_PT 的目的，就是量化：

[NOTE]
每個族群內，龍頭股的 MOI / 價量異動
和 整個族群 SAI_Residual 之間

[RULE]
是否存在穩定的「領先 → 傳導」關係。

[NOTE]
________________

[RULE]
1. 核心概念：Leader → Sector 的壓力傳導

[NOTE]
對每個族群 G（例如 AI_Concept、Semiconductor）：
                                       * 指定一檔龍頭股：Leader(G)
                                       * 例如：

[RULE]
                                       * AI_Concept → 2382（舉例）
                                       * Semiconductor → 2330

[NOTE]
                                       * 我們追蹤兩條序列（以 Volume Bar 為時間軸）：
                                       1. 龍頭行為序列：
                                       * MOI_leader(t)：龍頭在第 t 根 Volume Bar 的主力失衡
                                       * 或加上價格變化 ΔP_leader(t) 作為輔助
                                       2. 族群資金流序列：
                                       * SAI_Residual_G(t)：該族群在第 t 根 Volume Bar 的 SAI 殘差（攻擊強度）
我們希望量化：

[RULE]
當龍頭的 MOI 先放大時，

[NOTE]
接下來幾個 Volume Bar 內，族群 SAI_Residual 是否明顯放大？

[RULE]
如果這樣的模式在最近 N 個事件中反覆出現，F_PT 就會拉高。

[NOTE]
________________

[NOTE]
2. F_PT 的度量方式（直覺版）
可以把 F_PT 想成「Leader 領先度 × 一致方向」：
2.1 領先度（Lead-Lag）
在最近 N 根 Volume Bar 中：
                                       * 將 MOI_leader 和 SAI_Residual_G 做 cross-correlation，
找出「最大正相關」對應的時間位移 lag*：

[RULE]
如果最佳相關係數出現在：

[NOTE]
MOI_leader(t) 對應 SAI_Residual_G(t+1) 或 t+2

→ 表示「龍頭先動，族群後動」。
[NOTE]
我們簡化為一個「領先分數」：

[RULE]
                                          * 若最佳 lag 落在 [1, L_max]（龍頭領先 1–L_max 個事件）

→ LeadScore ≈ 正值
[RULE]
                                          * 若最佳 lag = 0 或負數（族群先動 or 只是同時亂動）

→ LeadScore 降低甚至為 0
[NOTE]
實作上可以簡化：
不一定要完整 cross-correlation，
也可以只看「最近 k 根 Bar 裡：有幾次是龍頭先大幅 MOI，後面幾根 Bar SAI_Residual 跟著放大」。
2.2 方向一致性（Direction Consistency）

[RULE]
再來，我們需要確認攻擊不是純噪音：

[CONCEPT]
                                             * 假設我們定義 sign：

[FORMULA]
                                             * sign_MOI(t) = sign(MOI_leader(t))
                                             * sign_SAI(t) = sign(SAI_Residual_G(t))

[NOTE]
在最近 N 根 Bar 裡，計算：

[FORMULA]
AgreeRate=#{t:sign_MOI(t)=sign_SAI(t+best lag)}NAgreeRate=N#{t:sign_MOI(t)=sign_SAI(t+best lag)}​

[RULE]
                                             * 若龍頭淨買 + 族群 SAI_Residual 也偏正 → 一致
                                             * 若龍頭在賣、族群卻在被買 → 不一致

[NOTE]
________________

[CONCEPT]
3. F_PT 的定義（概念公式）
綜合上面兩項，我們可以定義：

[NOTE]
FPT,G=LeadScoreG×AgreeRateGFPT,G​=LeadScoreG​×AgreeRateG​
                                             * LeadScore_G：龍頭領先程度（0 ~ 1）
                                             * AgreeRate_G：方向一致率（0 ~ 1）
數值越接近 1，代表：
「這個族群的資金攻擊，是由龍頭很有組織地在帶頭。」
________________

[CODE]
4. Python 模組雛形：PressureTransmissionEngine

[NOTE]
我們先做一版簡化、可實作的版本：
不先做完整 cross-correlation，而是用「最近 K 根事件」的統計。
# strategy_engine/factor_FX_pressure_transmission.py

[CODE]
from __future__ import annotations

[CODE]
from collections import deque
from typing import Dict, List, Tuple
import numpy as np

[CODE]
class PressureTransmissionEngine:

[NOTE]
    """

[STRUCTURE]
    壓力傳導因子引擎 (F_PT)：

[NOTE]
    衡量「族群龍頭的主力行為」是否會穩定地傳導到該族群的資金攻擊 (SAI_Residual)。

[NOTE]
    時間軸：Volume Bar / Information Time
    """

[CODE]
    def __init__(

[NOTE]
        self,

[CODE]
        group_leader_map: Dict[str, str],
        window_bars: int = 20,
        max_lead_lag: int = 3,
        moi_threshold: float = 0.5,
        sai_threshold: float = 0.5,
    ) -> None:

[NOTE]
        """
        :param group_leader_map:
            - key: group name (e.g. "AI_Concept")
            - value: leader symbol/id (e.g. "2330")
        :param window_bars: 最近要觀察多少根 Volume Bar
        :param max_lead_lag: 視為「龍頭領先」的最大 lag（單位：Bar）
        :param moi_threshold: 龍頭 MOI 被視為「顯著」的門檻
        :param sai_threshold: SAI_Residual 被視為「顯著」的門檻
        """
        self.group_leader_map = group_leader_map
        self.window_bars = window_bars
        self.max_lead_lag = max_lead_lag
        self.moi_threshold = moi_threshold
        self.sai_threshold = sai_threshold

[NOTE]
        # 儲存每個 group 的歷史序列（Volume Bar 序列）
        # { group: deque of (moi_leader, sai_residual_group) }

[CODE]
        self.history: Dict[str, deque[Tuple[float, float]]] = {

[NOTE]
            g: deque(maxlen=window_bars) for g in group_leader_map.keys()
        }

[CODE]
    def update_bar(

[NOTE]
        self,

[CODE]
        group_moi: Dict[str, float],
        group_sai_residual: Dict[str, float],
    ) -> Dict[str, float]:

[NOTE]
        """
        在每個 Volume Bar 完成時呼叫一次。

[NOTE]
        :param group_moi:
            - key: group name
            - value: 該 group 龍頭在此 Bar 的 MOI (淨主力單量失衡)
              （外部應先把 leader 的 MOI 萃取好）
        :param group_sai_residual:
            - key: group name
            - value: 該 group 在此 Bar 的 SAI_Residual
        :return:
            - { "F_PT_AI_Concept": value, ... }
        """

[CODE]
        f_pt_values: Dict[str, float] = {}

[NOTE]
        for group in self.group_leader_map.keys():
            moi = float(group_moi.get(group, 0.0))
            sai_res = float(group_sai_residual.get(group, 0.0))

[NOTE]
            # 更新歷史序列
            self.history[group].append((moi, sai_res))

[NOTE]
            # 計算該 group 的 F_PT

[FORMULA]
            f_pt_values[f"F_PT_{group}"] = self._compute_pt_for_group(group)

[NOTE]
        return f_pt_values

[CODE]
    def _compute_pt_for_group(self, group: str) -> float:

[NOTE]
        """
        對單一 group 計算壓力傳導分數 F_PT_group。
        """
        seq = list(self.history[group])
        n = len(seq)
        if n < 3:
            # 資料太少就回 0
            return 0.0

[NOTE]
        mois = np.array([x[0] for x in seq])
        sais = np.array([x[1] for x in seq])

[NOTE]
        # 只關心「顯著事件」
        moi_events = np.abs(mois) >= self.moi_threshold

[NOTE]
        if not np.any(moi_events):
            return 0.0

[NOTE]
        lead_scores = []
        agree_rates = []

[NOTE]
        # 嘗試不同 lag（1 ~ max_lead_lag），尋找最合理的領先關係
        for lag in range(1, min(self.max_lead_lag, n) + 1):
            # 龍頭在 t，族群在 t+lag
            moi_t = mois[:-lag]
            sai_tlag = sais[lag:]

[NOTE]
            moi_evt = np.abs(moi_t) >= self.moi_threshold
            sai_evt = np.abs(sai_tlag) >= self.sai_threshold

[NOTE]
            # 只看「龍頭有顯著行為」的那些 t
            valid_idx = moi_evt

[NOTE]
            if not np.any(valid_idx):
                continue

[NOTE]
            # 領先事件數 & 同方向比例
            moi_sign = np.sign(moi_t[valid_idx])
            sai_sign = np.sign(sai_tlag[valid_idx])

[NOTE]
            agree = moi_sign * sai_sign  # 同方向 => 1, 反向 => -1, 零 => 0
            # 同方向的比例（負向會扣分）
            agree_rate = float(np.mean(agree))

[NOTE]
            # 「領先事件比例」：有多少顯著 MOI 事件在這個 lag 下找到對應顯著 SAI
            lead_score = float(np.mean(sai_evt[valid_idx]))

[NOTE]
            lead_scores.append(lead_score)
            agree_rates.append(agree_rate)

[NOTE]
        if not lead_scores:
            return 0.0

[NOTE]
        # 取所有 lag 中綜合的分數（可簡化為平均或最大值）
        # 這裡採用平均值作為穩健估計
        avg_lead = float(np.mean(lead_scores))
        avg_agree = float(np.mean(agree_rates))

[FORMULA]
        # F_PT = 領先程度 * 方向一致性

[NOTE]
        f_pt = max(0.0, avg_lead * avg_agree)  # 負值視為 0（不可信的傳導）
        return f_pt

[NOTE]
________________

[NOTE]
5. 在 RL 中的應用：F_PT 是什麼級別的信號？
你可以把 F_PT 理解成：
「這個族群現在是不是在打有組織的主攻戰役？」
高 F_PT（接近 1）
                                             * 龍頭 MOI 大幅偏多（或偏空）
                                             * 接續的幾根 Volume Bar 裡，族群 SAI_Residual 也跟著放大
                                             * 方向一致且傳導清晰
RL 行為：

[STRUCTURE]
                                             * 提升該族群相關個股在 O_因子組合裡的權重

[NOTE]
                                             * 放寬該族群的 Max Position / Leverage 上限

[STRUCTURE]
                                             * 可以作為「忽略弱反向因子」的 override signal

[RULE]
                                             * 例如：其他因子稍微偏空，但 F_PT 強烈偏多 → 仍可容許淨多單高敞口

[NOTE]
低 F_PT（接近 0）
                                             * 代表龍頭亂動、族群亂動，沒有穩定領先關係
                                             * 有可能是：
                                             * 偶發大單
                                             * 散戶集中亂買
                                             * 隨機震盪
RL 行為：
                                             * F_C 相關 signal 降級為「僅供參考」
                                             * 不依靠「龍頭帶隊」來判斷方向

[STRUCTURE]
                                             * 減少追價、改為盤整或短線反轉策略

[CONCEPT]
Cursor 的「F_PT 實作規格書」，格式跟剛剛 F_Inertia 一樣，照貼就能讓它開工。

[NOTE]
________________

[STRUCTURE]
🧾 給 Cursor 的完整實作規格書（F_PT：壓力傳導因子）
主題：實作「壓力傳導因子」引擎 PressureTransmissionEngine（F_PT）
你現在是一位「量化交易系統特徵工程師」。

[NOTE]
請幫我在專案中完成以下兩個檔案：
                                             1. strategy_engine/factor_FX_pressure_transmission.py
                                             2. tests/strategy_engine/test_factor_FX_pressure_transmission.py
________________

[NOTE]
一、檔案一：strategy_engine/factor_FX_pressure_transmission.py

[CONCEPT]
🎯 目標說明

[NOTE]
我們要實作一個：

[STRUCTURE]
壓力傳導因子引擎 PressureTransmissionEngine

[NOTE]
用途：

[STRUCTURE]
                                             * 對每個「族群」（Group）計算一個 F_PT_{Group} 因子

[NOTE]
                                             * 衡量：
「龍頭股的主力行為（MOI）是否會穩定地傳導到整個族群的資金攻擊（SAI_Residual）？」
時間軸不是秒／分鐘，而是：
Volume Bar / Information Time（每一根 Bar = 一個資訊事件）
________________

[STRUCTURE]
✅ 類別設計與程式架構

[NOTE]
請在 strategy_engine/factor_FX_pressure_transmission.py 實作以下內容：
# strategy_engine/factor_FX_pressure_transmission.py

[CODE]
from __future__ import annotations

[CODE]
from collections import deque
from typing import Deque, Dict, List, Tuple

[CODE]
import numpy as np

[CODE]
class PressureTransmissionEngine:

[NOTE]
    """

[STRUCTURE]
    壓力傳導因子引擎 (F_PT)。

[CONCEPT]
    目標：

[RULE]
    - 判斷「龍頭股」的主力行為 (MOI) 是否會在若干 Volume Bar 之後，

[NOTE]
      穩定地反映在整個族群的資金攻擊強度 (SAI_Residual) 上。

[RULE]
    - F_PT 越高，代表「龍頭帶隊 → 族群跟隨」的結構越明顯，

[NOTE]
      也就是越接近主力有組織發動的攻擊。

[NOTE]
    時間軸：
    - 以 Volume Bar / Information Time 為單位。

[STRUCTURE]
    - 本 Engine 不負責產生 Volume Bar，只在每個 Bar 完成時被呼叫更新一次。

[NOTE]
    """

[CODE]
    def __init__(

[NOTE]
        self,

[CODE]
        group_leader_map: Dict[str, str],
        window_bars: int = 20,
        max_lead_lag: int = 3,
        moi_threshold: float = 0.5,
        sai_threshold: float = 0.5,
    ) -> None:

[NOTE]
        """
        :param group_leader_map:
            - key: group 名稱 (例如 "AI_Concept")
            - value: 該 group 的龍頭代碼/識別符 (例如 "2330")。
              *注意：目前此資訊只做紀錄，不直接用於計算，
              計算時會由外部提供對應 group 的 MOI。
        :param window_bars:
            - 觀察用的歷史 Volume Bar 數量 (rolling window 長度)。
        :param max_lead_lag:
            - 視為「龍頭領先」的最大 lag，單位為 Bar。
              例如 max_lead_lag=3，表示我們只考慮龍頭領先 1～3 根 Bar 的關係。
        :param moi_threshold:
            - MOI 被視為「顯著主力事件」的門檻。
        :param sai_threshold:
            - SAI_Residual 被視為「顯著族群攻擊事件」的門檻。
        """

[CODE]
        self.group_leader_map: Dict[str, str] = dict(group_leader_map)
        self.window_bars: int = int(window_bars)
        self.max_lead_lag: int = int(max_lead_lag)
        self.moi_threshold: float = float(moi_threshold)
        self.sai_threshold: float = float(sai_threshold)

[NOTE]
        # 每個 group 會維護一個歷史序列：
        # history[group] = deque( (moi_leader, sai_residual_group), ... )

[CODE]
        self.history: Dict[str, Deque[Tuple[float, float]]] = {

[NOTE]
            group: deque(maxlen=self.window_bars)
            for group in self.group_leader_map.keys()
        }

[NOTE]
    # -------------------------------------------------
    #  公開 API：在每個 Volume Bar 完成時更新
    # -------------------------------------------------

[CODE]
    def update_bar(

[NOTE]
        self,

[CODE]
        group_moi: Dict[str, float],
        group_sai_residual: Dict[str, float],
    ) -> Dict[str, float]:

[NOTE]
        """
        在「每個 Volume Bar 完成時」呼叫一次，更新各 group 的 F_PT。

[NOTE]
        :param group_moi:
            - key: group 名稱 (例如 "AI_Concept")
            - value: 該 group 對應「龍頭股」在此 Volume Bar 的 MOI 數值。
        :param group_sai_residual:
            - key: group 名稱
            - value: 該 group 在此 Volume Bar 的 SAI_Residual 數值。
        :return:
            - 一個 dict，包含各 group 的 F_PT 值：
              {
                  "F_PT_AI_Concept": 0.73,
                  "F_PT_Semiconductor": 0.12,
                  ...
              }
        """

[CODE]
        f_pt_values: Dict[str, float] = {}

[NOTE]
        for group in self.group_leader_map.keys():
            moi_value = float(group_moi.get(group, 0.0))
            sai_value = float(group_sai_residual.get(group, 0.0))

[NOTE]
            # 更新該 group 的歷史序列
            self._append_history(group, moi_value, sai_value)

[NOTE]
            # 計算該 group 的壓力傳導分數

[FORMULA]
            f_pt_values[f"F_PT_{group}"] = self._compute_pt_for_group(group)

[NOTE]
        return f_pt_values

[CODE]
    def _append_history(self, group: str, moi: float, sai_residual: float) -> None:

[NOTE]
        """

[RULE]
        將單一 group 在當前 Volume Bar 的 (moi, sai_residual) 加入歷史序列。

[NOTE]
        """
        if group not in self.history:

[RULE]
            # 若遇到未事先宣告的 group，初始化其歷史序列

[NOTE]
            self.history[group] = deque(maxlen=self.window_bars)

[NOTE]
        self.history[group].append((moi, sai_residual))

[NOTE]
    # -------------------------------------------------

[CONCEPT]
    #  F_PT 計算核心

[NOTE]
    # -------------------------------------------------

[CODE]
    def _compute_pt_for_group(self, group: str) -> float:

[NOTE]
        """

[STRUCTURE]
        計算單一 group 的壓力傳導因子 F_PT_group。

[NOTE]
        將最近 window_bars 根 Volume Bar 內，
        「龍頭 MOI」與「族群 SAI_Residual」之間的領先關係 + 方向一致性
        統合成一個 0~1 之間的分數。
        """
        seq = list(self.history.get(group, []))
        n = len(seq)
        if n < 3:
            # 資料太少時，不做判斷
            return 0.0

[NOTE]
        mois = np.array([x[0] for x in seq], dtype=float)
        sais = np.array([x[1] for x in seq], dtype=float)

[NOTE]
        # 標記有哪些 Bar 的「龍頭 MOI」算是顯著事件
        moi_event_mask = np.abs(mois) >= self.moi_threshold
        if not np.any(moi_event_mask):
            return 0.0

[CODE]
        lead_scores: List[float] = []
        agree_scores: List[float] = []

[NOTE]
        # 尋找龍頭領先 1 ~ max_lead_lag Bar 的關係
        max_lag = min(self.max_lead_lag, n - 1)
        for lag in range(1, max_lag + 1):
            # 龍頭在 t，族群在 t+lag
            moi_t = mois[:-lag]
            sai_tlag = sais[lag:]

[NOTE]
            # 對齊 mask 長度
            moi_evt = np.abs(moi_t) >= self.moi_threshold
            sai_evt = np.abs(sai_tlag) >= self.sai_threshold

[NOTE]
            # 只考慮「龍頭 MOI 顯著」的那些 Bar
            valid_idx = moi_evt
            if not np.any(valid_idx):
                continue

[NOTE]
            # 方向一致性：sign(MOI_t) 與 sign(SAI_t+lag) 是否同號
            moi_sign = np.sign(moi_t[valid_idx])
            sai_sign = np.sign(sai_tlag[valid_idx])

[NOTE]
            # 同方向 => 1, 反向 => -1, 其他 => 0
            direction_agree = moi_sign * sai_sign
            # 平均值：負值會扣分
            agree_score = float(np.mean(direction_agree))

[NOTE]
            # 領先程度：在「龍頭顯著事件」中，有多少比例會導致「族群也顯著」
            lead_score = float(np.mean(sai_evt[valid_idx]))

[NOTE]
            agree_scores.append(agree_score)
            lead_scores.append(lead_score)

[NOTE]
        if not lead_scores:
            return 0.0

[NOTE]
        # 以平均值作為綜合評價（也可改成 max，以後可調整）
        avg_lead = float(np.mean(lead_scores))
        avg_agree = float(np.mean(agree_scores))

[FORMULA]
        # F_PT = 領先程度 * 方向一致性

[NOTE]
        raw_score = avg_lead * avg_agree

[NOTE]
        # 負值代表傳導不穩定或反向，視為 0
        return max(0.0, raw_score)

[NOTE]
    # -------------------------------------------------

[STRUCTURE]
    #  輔助方法：讀取與重置

[NOTE]
    # -------------------------------------------------

[CODE]
    def get_current_values(self) -> Dict[str, float]:

[NOTE]
        """
        回傳目前各 group 的 F_PT_* 值。
        方便 debug 或直接丟入 State Vector。
        """
        return {
            f"F_PT_{group}": self._compute_pt_for_group(group)
            for group in self.group_leader_map.keys()
        }

[CODE]
    def reset(self) -> None:

[NOTE]
        """
        重置所有 group 的歷史序列。
        用於訓練 episode 開始或實盤重啟。
        """
        self.history = {
            group: deque(maxlen=self.window_bars)
            for group in self.group_leader_map.keys()
        }

[NOTE]
________________

[NOTE]
⚙️ 設計行為與假設補充

[STRUCTURE]
                                                1. 本 Engine 不抓原始龍頭代碼

[NOTE]
                                                * group_leader_map 主要用來記錄「Group ↔ Leader」的關係

[CONCEPT]
                                                * 真正傳入 group_moi[group] 的值由外部負責計算（例如從 XQ 取某支龍頭股的 MOI）

[NOTE]
                                                2. 時間粒度是 Volume Bar，而非秒數
                                                * 每次呼叫 update_bar(...) = 一個資訊事件完成

[STRUCTURE]
                                                * 是否形成 Volume Bar、Volume 門檻多少，交由其他模組（例如 InfoTimeEngine）

[NOTE]
                                                3. F_PT 輸出設計為 0~1 左右的分數
                                                * lead_score、agree_score 都自然落在 [-1,1] 或 [0,1] 範圍
                                                * 最後把負值剪成 0（代表沒有可靠正向傳導）
                                                4. 後續在 RL 中的用途（此檔不實作）

[RULE]
                                                * 可以把 F_PT_* 當成高權重 Alpha 或 Override Signal

[NOTE]
                                                * 例如在 State Vector 中增加欄位：
                                                * F_PT_AI_Concept, F_PT_Semiconductor, ...
                                                * 或用來動態調整某族群的最大倉位上限
________________

[NOTE]
二、檔案二：tests/strategy_engine/test_factor_FX_pressure_transmission.py
請新增單元測試，驗證：
                                                1. 能正常初始化與更新

[RULE]
                                                2. 在有明顯「龍頭先動 → 族群後動」時，F_PT 應該 > 0
                                                3. 在亂給不一致方向的數據時，F_PT 應該接近 0

[NOTE]
                                                4. reset() 能重置狀態
________________

[NOTE]
# tests/strategy_engine/test_factor_FX_pressure_transmission.py

[CODE]
import math

[CODE]
from strategy_engine.factor_FX_pressure_transmission import PressureTransmissionEngine

[CODE]
def test_pressure_transmission_basic_positive_signal():

[NOTE]
    """
    測試一個簡化情境：
    - 龍頭連續數個 Bar 有顯著正向 MOI
    - 接著數個 Bar 族群 SAI_Residual 也顯著偏正

[RULE]
    預期：F_PT 應該是 > 0

[NOTE]
    """

[STRUCTURE]
    engine = PressureTransmissionEngine(

[NOTE]
        group_leader_map={"AI_Concept": "LEADER_AI"},
        window_bars=10,
        max_lead_lag=3,
        moi_threshold=0.5,
        sai_threshold=0.5,
    )

[NOTE]
    # 模擬 3 個 Bar：龍頭先連續買超，但族群尚未反應
    for _ in range(3):
        out = engine.update_bar(
            group_moi={"AI_Concept": 1.0},
            group_sai_residual={"AI_Concept": 0.0},
        )

[NOTE]
    # 再模擬後面 3 個 Bar：族群資金開始流入
    for _ in range(3):
        out = engine.update_bar(
            group_moi={"AI_Concept": 0.8},
            group_sai_residual={"AI_Concept": 1.2},
        )

[FORMULA]
    f_pt_value = out["F_PT_AI_Concept"]

[NOTE]
    assert f_pt_value >= 0.0
    # 在這樣的正向傳導情境下，F_PT 應明顯大於 0
    assert f_pt_value > 0.1

[CODE]
def test_pressure_transmission_negative_or_noise_should_be_low():

[NOTE]
    """

[RULE]
    測試：若龍頭與族群方向經常不一致，
    F_PT 應該趨近於 0。

[NOTE]
    """

[STRUCTURE]
    engine = PressureTransmissionEngine(

[NOTE]
        group_leader_map={"Semiconductor": "LEADER_SEMI"},
        window_bars=10,
        max_lead_lag=3,
        moi_threshold=0.5,
        sai_threshold=0.5,
    )

[NOTE]
    # 模擬數個 Bar：龍頭買，族群卻賣；反之亦然
    for i in range(8):
        moi = 1.0 if i % 2 == 0 else -1.0
        sai = -1.0 if i % 2 == 0 else 1.0

[NOTE]
        out = engine.update_bar(
            group_moi={"Semiconductor": moi},
            group_sai_residual={"Semiconductor": sai},
        )

[FORMULA]
    f_pt_value = out["F_PT_Semiconductor"]

[NOTE]
    # 預期 F_PT 會被壓到接近 0
    assert f_pt_value >= 0.0
    assert f_pt_value < 0.2

[CODE]
def test_pressure_transmission_reset():

[NOTE]
    """
    測試 reset() 能清除歷史，讓 F_PT 回到 0 附近。
    """

[STRUCTURE]
    engine = PressureTransmissionEngine(

[NOTE]
        group_leader_map={"AI_Concept": "LEADER_AI"},
        window_bars=10,
        max_lead_lag=3,
        moi_threshold=0.5,
        sai_threshold=0.5,
    )

[NOTE]
    # 先跑一段正向傳導
    for _ in range(5):
        out = engine.update_bar(
            group_moi={"AI_Concept": 1.0},
            group_sai_residual={"AI_Concept": 1.0},
        )
    assert out["F_PT_AI_Concept"] > 0.0

[NOTE]
    # reset 後重新計算，資料不足 / 歷史清空，F_PT 應回到接近 0
    engine.reset()
    out2 = engine.update_bar(
        group_moi={"AI_Concept": 0.0},
        group_sai_residual={"AI_Concept": 0.0},
    )

[FORMULA]
    assert out2["F_PT_AI_Concept"] == 0.0

[NOTE]
________________

[STRUCTURE]
三、完成後預期在系統內的資料流（說明，不需實作）

[CONCEPT]
[XQ / Market Data]

[RULE]
    ↓  (主力大單 → 龍頭 MOI、族群資金流 → SAI_Residual)

[STRUCTURE]
[CapitalFlowEngine] 產生 per-group SAI_Residual + Leader MOI

[NOTE]
    ↓  (每個 Volume Bar 完成時)

[STRUCTURE]
[PressureTransmissionEngine.update_bar(...)]

[NOTE]
    ↓  輸出: {"F_PT_AI_Concept": ..., "F_PT_Semiconductor": ...}

[STRUCTURE]
[FactorAggregator / StateBuilder]

[NOTE]
    ↓

[STRUCTURE]
[RL Agent] 將 F_PT_* 作為高階 Alpha / Override 因子

[NOTE]
請依上述規格完成 factor_FX_pressure_transmission.py 與對應測試檔。
接下來就是把第三顆「風險維度核彈」做好：

[STRUCTURE]
主力意圖逆轉因子 F_MRR（Major Reversal Risk）。

[CONCEPT]
我直接照你現在的節奏，一次給你 「概念＋給 Cursor 的完整實作規格書」，你不用再多講。

[NOTE]
________________

[STRUCTURE]
🛠️ 階段 XXIII：主力意圖逆轉因子設計（F_MRR）

[NOTE]
— 偵測主力「誘多 / 誘空 / 反手」的風險警報器
前面我們已經有：
                                                * F_C 基本資金流（SAI, MOI）

[CONCEPT]
                                                * F_Inertia：資金攻擊是否有「持續性」

[RULE]
                                                * F_PT：龍頭 → 族群的壓力傳導

[NOTE]
但還缺一塊關鍵拼圖：
主力是不是在變心？
是真的掃貨，還是邊掃邊撤、準備轉向、誘多/誘空？
F_MRR（Major Reversal Risk）的任務就是量化這件事，
讓 RL 在「主力可能要反手」時自動縮手。
________________

[CONCEPT]
1. F_MRR 核心觀察點
我們假設你能從 XQ / 永豐 API 拿到主力相關的 Tick / Bar 資料，例如：

[NOTE]
                                                * major_buy_volume：主力買超量
                                                * major_sell_volume：主力賣超量
                                                * major_cancel_volume：主力掛單取消量（或大單撤單量估計）
                                                * price_change：該 Bar 價格變化（可選，用於判斷「有量沒價」）
F_MRR 的直覺是：
                                                1. 極端 MOI + 高取消率

[RULE]
                                                * 看起來在大買 / 大賣，但撤單速度異常快 → 高誘多/誘空風險

[NOTE]
                                                2. MOI 劇烈翻轉

[RULE]
                                                * 前一個 Bar 還是強烈淨買，下一個 Bar 轉成大淨賣（或反之） → 方向逆轉風險

[NOTE]
                                                3. 有主力量、沒價格推進

[RULE]
                                                * MOI 很大，但價格走不動 → 有可能在對敲 / 洗盤或誘騙
F_MRR 要做的，就是把這些條件壓進一個 0～1 的「風險分數」。

[NOTE]
________________

[NOTE]
🧾 給 Cursor 的完整實作規格書（F_MRR）

[STRUCTURE]
主題：實作「主力意圖逆轉風險因子」引擎 MajorReversalRiskEngine（F_MRR）

[NOTE]
請幫我新增：
                                                1. strategy_engine/factor_FX_major_reversal_risk.py
                                                2. tests/strategy_engine/test_factor_FX_major_reversal_risk.py
________________

[NOTE]
一、檔案一：strategy_engine/factor_FX_major_reversal_risk.py
在這個檔案中，請實作一個：

[STRUCTURE]
MajorReversalRiskEngine 類別

[NOTE]
用來計算 每個標的 / 族群 的 F_MRR_* 分數。
1. 類別與輸入格式設計
# strategy_engine/factor_FX_major_reversal_risk.py

[CODE]
from __future__ import annotations

[CODE]
from collections import deque
from typing import Deque, Dict, List

[CODE]
import numpy as np

[CODE]
class MajorReversalRiskEngine:

[NOTE]
    """

[STRUCTURE]
    主力意圖逆轉風險引擎 (F_MRR)。

[CONCEPT]
    目的：

[NOTE]
    - 監控主力行為是否出現「反手 / 誘多 / 誘空」跡象。
    - 給出 0 ~ 1 的風險分數，供 RL / RiskManager 直接使用。

[NOTE]
    主要觀察維度：
    1. 主力 MOI 極端時，掛單取消率是否異常提高。

[RULE]
    2. MOI 的方向是否在短時間內大幅翻轉（多 → 空 或 空 → 多）。

[NOTE]
    3. （可選）有大量主力單，但價格推不動，代表意圖不單純。

[NOTE]
    時間軸：
    - Volume Bar / Information Time。
    - 每次呼叫 update_bar(...) = 一個 Volume Bar 完成。
    """

[CODE]
    def __init__(

[NOTE]
        self,

[CODE]
        symbols: List[str],
        window_bars: int = 20,
        high_moi_threshold: float = 0.7,
        high_cancel_rate_threshold: float = 0.6,
        flip_moi_threshold: float = 0.5,
    ) -> None:

[NOTE]
        """
        :param symbols:
            - 要追蹤的標的列表，可以是個股代碼或 group 名稱。
            - 例如 ["2330", "2317"] 或 ["AI_Concept", "Semiconductor"]。
        :param window_bars:
            - 保存最近多少根 Volume Bar 的歷史，用於估計平均行為。
        :param high_moi_threshold:
            - 將 |MOI| 視為「極端主力行為」的門檻 (0~1 規模)。
        :param high_cancel_rate_threshold:
            - cancellation_rate 被視為「異常高」的門檻 (0~1)。
        :param flip_moi_threshold:
            - 判斷 MOI 是否「強烈反向」時的強度門檻。
        """

[CODE]
        self.symbols: List[str] = list(symbols)
        self.window_bars: int = int(window_bars)
        self.high_moi_threshold: float = float(high_moi_threshold)
        self.high_cancel_rate_threshold: float = float(high_cancel_rate_threshold)
        self.flip_moi_threshold: float = float(flip_moi_threshold)

[NOTE]
        # 每個標的的歷史紀錄：存 (moi, cancel_rate)

[CODE]
        self.history: Dict[str, Deque[tuple[float, float]]] = {

[NOTE]
            sym: deque(maxlen=self.window_bars)
            for sym in self.symbols
        }

[NOTE]
        # 儲存上一個 Bar 的 MOI（用來偵測 sign flip）

[CODE]
        self.prev_moi: Dict[str, float] = {sym: 0.0 for sym in self.symbols}

[NOTE]
    # -------------------------------------------------
    #  公開 API：Volume Bar 完成時更新
    # -------------------------------------------------

[CODE]
    def update_bar(

[NOTE]
        self,

[CODE]
        major_stats: Dict[str, Dict[str, float]],
    ) -> Dict[str, float]:

[NOTE]
        """
        在「每一根 Volume Bar 完成時」被呼叫一次。

[NOTE]
        :param major_stats:
            - key: symbol 名稱（或 group 名稱）
            - value: dict，包含此 Bar 的主力行為統計，例如：
              {
                  "major_buy_volume":  500_000,
                  "major_sell_volume": 100_000,
                  "major_cancel_volume": 200_000,
                  "total_major_orders": 800_000   # 可選，用來估 cancel_rate
              }

[RULE]
            - 若缺少其中某些欄位，視情況以 0 處理。

[NOTE]
        :return:
            - 每個 symbol 對應的 F_MRR 值：
              {
                  "F_MRR_2330": 0.35,
                  "F_MRR_2317": 0.82,
                  ...
              }
        """

[CODE]
        f_mrr_values: Dict[str, float] = {}

[NOTE]
        for sym in self.symbols:
            stats = major_stats.get(sym, {})
            moi, cancel_rate = self._compute_moi_and_cancel_rate(stats)

[NOTE]
            # 更新歷史序列
            self._append_history(sym, moi, cancel_rate)

[NOTE]
            # 計算單一 symbol 的 F_MRR 分數
            risk_score = self._compute_risk_for_symbol(sym, moi, cancel_rate)

[FORMULA]
            f_mrr_values[f"F_MRR_{sym}"] = risk_score

[NOTE]
            # 更新 prev_moi
            self.prev_moi[sym] = moi

[NOTE]
        return f_mrr_values

[CODE]
    def _compute_moi_and_cancel_rate(self, stats: Dict[str, float]) -> tuple[float, float]:

[NOTE]
        """
        從輸入的 stats 計算 MOI 與 cancellation_rate。

[FORMULA]
        MOI = (major_buy - major_sell) / total_major_volume

[NOTE]
        cancellation_rate = major_cancel_volume / (major_buy + major_sell + major_cancel_volume)

[RULE]
        （若分母為 0 則視為 0）

[NOTE]
        """
        major_buy = float(stats.get("major_buy_volume", 0.0))
        major_sell = float(stats.get("major_sell_volume", 0.0))
        major_cancel = float(stats.get("major_cancel_volume", 0.0))

[NOTE]
        total_major_volume = major_buy + major_sell
        total_for_cancel = major_buy + major_sell + major_cancel

[NOTE]
        moi = (major_buy - major_sell) / total_major_volume if total_major_volume > 0 else 0.0
        cancel_rate = major_cancel / total_for_cancel if total_for_cancel > 0 else 0.0

[NOTE]
        return moi, cancel_rate

[CODE]
    def _append_history(self, sym: str, moi: float, cancel_rate: float) -> None:

[NOTE]
        """
        更新單一 symbol 的歷史紀錄。
        """
        if sym not in self.history:
            self.history[sym] = deque(maxlen=self.window_bars)
            self.prev_moi[sym] = 0.0

[NOTE]
        self.history[sym].append((moi, cancel_rate))

[NOTE]
    # -------------------------------------------------

[CONCEPT]
    #  核心：主力逆轉風險分數計算

[NOTE]
    # -------------------------------------------------

[CODE]
    def _compute_risk_for_symbol(self, sym: str, moi: float, cancel_rate: float) -> float:

[NOTE]
        """

[RULE]
        根據當前 Volume Bar 的 MOI / cancel_rate + 歷史 MOI 變化，

[NOTE]
        估計「主力意圖逆轉」的風險分數 (0~1)。
        """

[RULE]
        # 1) 極端 MOI + 高取消率 → 高風險

[NOTE]
        extreme_moi = float(np.clip(abs(moi) / max(self.high_moi_threshold, 1e-6), 0.0, 2.0))
        # 正規化後最多 2，後面再壓到 0~1
        high_cancel = float(
            np.clip(
                (cancel_rate - self.high_cancel_rate_threshold) / max(1.0 - self.high_cancel_rate_threshold, 1e-6),
                0.0,
                1.0,
            )
        )

[RULE]
        # 這一項表示：當 MOI 很大、取消率又超過 threshold 時，風險拉高

[NOTE]
        component_extreme_cancel = np.clip(extreme_moi * high_cancel, 0.0, 2.0)

[RULE]
        # 2) MOI 方向大幅翻轉 → 風險加成

[NOTE]
        prev_moi = float(self.prev_moi.get(sym, 0.0))
        flip_component = 0.0
        if abs(prev_moi) >= self.flip_moi_threshold and abs(moi) >= self.flip_moi_threshold:
            # 前後兩個 Bar 都是「強烈主力行為」時才看翻轉
            if np.sign(prev_moi) * np.sign(moi) < 0:

[RULE]
                # 不同號 → 強烈翻轉

[NOTE]
                flip_component = 1.0

[NOTE]
        # 3) 總體風險組合（可以視為加權和）
        # 目前先用簡單線性組合，後續可調整權重
        raw_score = 0.6 * (component_extreme_cancel / 2.0) + 0.4 * flip_component

[NOTE]
        # 限制在 [0, 1] 範圍內
        risk_score = float(np.clip(raw_score, 0.0, 1.0))
        return risk_score

[NOTE]
    # -------------------------------------------------

[RULE]
    #  輔助：當前值 / 重置

[NOTE]
    # -------------------------------------------------

[CODE]
    def get_current_values(self) -> Dict[str, float]:

[NOTE]
        """
        重新計算並回傳目前所有 symbol 的 F_MRR_ 值。
        通常更新後會直接用 update_bar(...) 的回傳值即可；

[STRUCTURE]
        本方法主要用於 debug 或狀態檢查。

[NOTE]
        """

[CODE]
        out: Dict[str, float] = {}

[NOTE]
        for sym in self.symbols:
            if sym not in self.history or not self.history[sym]:

[FORMULA]
                out[f"F_MRR_{sym}"] = 0.0

[NOTE]
                continue

[NOTE]
            moi, cancel_rate = self.history[sym][-1]

[FORMULA]
            out[f"F_MRR_{sym}"] = self._compute_risk_for_symbol(sym, moi, cancel_rate)

[NOTE]
        return out

[CODE]
    def reset(self) -> None:

[NOTE]
        """
        重置所有 symbol 的歷史紀錄與 prev_moi。
        """
        self.history = {
            sym: deque(maxlen=self.window_bars)
            for sym in self.symbols
        }
        self.prev_moi = {sym: 0.0 for sym in self.symbols}

[NOTE]
________________

[NOTE]
二、檔案二：tests/strategy_engine/test_factor_FX_major_reversal_risk.py
請新增以下測試，用來確認：

[RULE]
                                                1. 極端 MOI + 高取消率 → F_MRR 明顯偏高
                                                2. 明顯的 MOI 方向翻轉 → F_MRR 拉高
                                                3. 平穩/正常狀態 → F_MRR 應接近 0

[NOTE]
                                                4. reset() 能清掉狀態
# tests/strategy_engine/test_factor_FX_major_reversal_risk.py

[CODE]
import math

[CODE]
from strategy_engine.factor_FX_major_reversal_risk import MajorReversalRiskEngine

[CODE]
def test_mrr_high_moi_and_high_cancel_rate():

[NOTE]
    """

[RULE]
    測試：在極端 MOI + 高取消率情境下，F_MRR 應該偏高。

[NOTE]
    """

[STRUCTURE]
    engine = MajorReversalRiskEngine(

[NOTE]
        symbols=["2330"],
        window_bars=10,
        high_moi_threshold=0.7,
        high_cancel_rate_threshold=0.6,
        flip_moi_threshold=0.5,
    )

[RULE]
    # 模擬幾根「正常」Bar，風險應該不高

[NOTE]
    for _ in range(3):
        out = engine.update_bar(
            {
                "2330": {
                    "major_buy_volume": 100_000,
                    "major_sell_volume": 90_000,
                    "major_cancel_volume": 10_000,
                }
            }
        )

[FORMULA]
    base_risk = out["F_MRR_2330"]

[NOTE]
    assert base_risk >= 0.0
    assert base_risk < 0.5

[NOTE]
    # 模擬一根極端 MOI + 高取消率
    out2 = engine.update_bar(
        {
            "2330": {
                "major_buy_volume": 1_000_000,
                "major_sell_volume": 100_000,
                "major_cancel_volume": 800_000,
            }
        }
    )

[FORMULA]
    high_risk = out2["F_MRR_2330"]

[NOTE]
    assert high_risk >= base_risk
    assert high_risk > 0.5

[CODE]
def test_mrr_moi_flip_risk():

[NOTE]
    """
    測試：MOI 方向大幅翻轉時，F_MRR 應提高。
    """

[STRUCTURE]
    engine = MajorReversalRiskEngine(

[NOTE]
        symbols=["2317"],
        window_bars=10,
        high_moi_threshold=0.7,
        high_cancel_rate_threshold=0.6,
        flip_moi_threshold=0.5,
    )

[NOTE]
    # 先來一根強烈正向 MOI
    out1 = engine.update_bar(
        {
            "2317": {
                "major_buy_volume": 500_000,
                "major_sell_volume": 0,
                "major_cancel_volume": 10_000,
            }
        }
    )

[FORMULA]
    risk1 = out1["F_MRR_2317"]

[NOTE]
    # 再來一根強烈負向 MOI（方向翻轉）
    out2 = engine.update_bar(
        {
            "2317": {
                "major_buy_volume": 0,
                "major_sell_volume": 500_000,
                "major_cancel_volume": 10_000,
            }
        }
    )

[FORMULA]
    risk2 = out2["F_MRR_2317"]

[RULE]
    # 有翻轉應該風險升高

[NOTE]
    assert risk2 >= risk1
    assert risk2 > 0.3

[CODE]
def test_mrr_reset():

[NOTE]
    """
    測試 reset() 是否正常重置歷史與 prev_moi。
    """

[STRUCTURE]
    engine = MajorReversalRiskEngine(

[NOTE]
        symbols=["2330"],
        window_bars=5,
        high_moi_threshold=0.7,
        high_cancel_rate_threshold=0.6,
        flip_moi_threshold=0.5,
    )

[NOTE]
    # 製造一段高風險狀態
    engine.update_bar(
        {
            "2330": {
                "major_buy_volume": 500_000,
                "major_sell_volume": 0,
                "major_cancel_volume": 500_000,
            }
        }
    )

[FORMULA]
    before_reset = engine.get_current_values()["F_MRR_2330"]

[NOTE]
    assert before_reset > 0.0

[RULE]
    # 重置後再給一根「安全」的 Bar，F_MRR 應該回到接近 0

[NOTE]
    engine.reset()
    out = engine.update_bar(
        {
            "2330": {
                "major_buy_volume": 100_000,
                "major_sell_volume": 100_000,
                "major_cancel_volume": 0,
            }
        }
    )

[FORMULA]
    after_reset = out["F_MRR_2330"]

[NOTE]
    assert after_reset >= 0.0
    assert after_reset < before_reset
    assert after_reset < 0.5

[NOTE]
________________

[STRUCTURE]
三、在整體系統中的角色（說明，不需實作）

[NOTE]
日後你可以這樣接：

[CONCEPT]
[XQ / 永豐 / 期交所 Major Order Data]

[NOTE]
        ↓ (整理 per-symbol 主力買賣 & 撤單)

[STRUCTURE]
[MajorReversalRiskEngine.update_bar(major_stats)]

[NOTE]
        ↓
輸出: {"F_MRR_2330": ..., "F_MRR_2317": ...}
        ↓
[RiskManager / RL State Vector]

[RULE]
    - 當 F_MRR_high 時：

[NOTE]
        - 降低該標的 / 族群的 Max Exposure
        - 提高出清 / 反手的獎勵
        - 加重「在高風險下強行加碼」的懲罰

[NOTE]
________________

[NOTE]
既然你說「好」，我就直接進入下一步——

[STRUCTURE]
「F_C 全家桶（XQ 資金流四因子）整合總表」
讓你與 Cursor 都能一眼掌握整個 Capital Flow Engine 的完整架構與檔案關係。

[NOTE]
________________

[STRUCTURE]
🧬 J-GOD F_C（XQ 資金流因子）全家桶整合總表
📂 給 Cursor 用的工程架構地圖 ＋ 開發者導讀

[NOTE]
________________

[NOTE]
📁 資料夾結構（專案中既有＋新增）
strategy_engine/
│

[STRUCTURE]
├─ factor_FX_capital_flow.py        # F_C 基礎因子：SAI Residual + MOI
├─ factor_FX_inertia.py             # F_Inertia 慣性因子（事件時間下的 EMA）

[RULE]
├─ factor_FX_pressure_transmission.py # F_PT 壓力傳導（龍頭 → 族群）

[NOTE]
└─ factor_FX_major_reversal_risk.py # F_MRR 主力逆轉風險（誘多/誘空）

[NOTE]
________________

[STRUCTURE]
🧩 四大因子組合成「F_C 量化資訊引擎」

[RULE]
以下是整合後的完整模組與用途，當你未來要寫 RL State Vector、Risk Engine、Execution Engine 時，一眼就知道該接什麼！

[NOTE]
________________

[STRUCTURE]
1️⃣ F_C 原始因子（XQ 資金流基礎）

[NOTE]
📄 factor_FX_capital_flow.py
✨ 輸入

[CONCEPT]
來自 XQ API 的：

[NOTE]
                                                * 族群成交量（group_volumes）
                                                * 主力大單量（major_buy, major_sell, major_single_volume）
✨ 輸出
                                                * SAI_Residual_{Group}（族群攻擊強度異常值）
                                                * MOI（主力買賣失衡）
🎯 用途
角色
	意義
	RL State Vector

[CONCEPT]
	原始 Alpha（基礎攻擊方向）

[NOTE]
	Risk Manager
	用於確認「市場是否開始攻擊某族群」
	Execution
	高 MOI 時提升 order aggressiveness
	________________

[CONCEPT]
2️⃣ F_Inertia：資金流動慣性（趨勢持續性）

[NOTE]
📄 factor_FX_inertia.py
✨ 輸入
                                                * 來自 F_C 的 SAI_Residual
                                                * Volume Bar（資訊時間 Bar）
✨ 輸出

[CONCEPT]
                                                * F_Inertia_{Group}：族群攻擊是否持續
✨ 核心公式

[NOTE]
EMA（在 Volume Bar 上）

[FORMULA]
Inertia_t = α × SAI_residual_t + (1-α) × Inertia_(t-1)

[NOTE]
🎯 用途
角色
	意義
	RL
	決定部位持續時間（短衝 vs 趨勢跟蹤）
	Risk Manager
	高慣性才准 RL 放大 Net Exposure
	Execution

[RULE]
	趨勢穩定 → 降低 order 分批數量

[NOTE]
	________________

[RULE]
3️⃣ F_PT：壓力傳導（龍頭 → 族群）

[NOTE]
📄 factor_FX_pressure_transmission.py
✨ 輸入

[CONCEPT]
                                                * 龍頭個股 MOI（來自 XQ 個股大單）

[NOTE]
                                                * 族群 SAI Residual
✨ 輸出
                                                * F_PT_{Group}：買盤自龍頭向族群傳遞的力度（0～1）
✨ 用途
角色
	意義
	RL 決策

[RULE]
	若龍頭先攻，RL 可以忽略部分雜訊，執行更大倉位

[STRUCTURE]
	Risk Engine

[RULE]
	龍頭退潮時觸發降槓桿

[NOTE]
	Execution

[RULE]
	若有龍頭支撐 → 降低滑價容忍度

[NOTE]
	________________

[NOTE]
4️⃣ F_MRR：主力意圖逆轉風險
📄 factor_FX_major_reversal_risk.py
✨ 輸入
                                                * 主力買超、大賣超、撤單量（取消率）
✨ 輸出
                                                * F_MRR_{Symbol}：反手 / 誘多 / 誘空 風險 0～1
✨ 用途
角色
	意義
	RL Reward

[RULE]
	逆勢在高 MRR 下加倉 → 重罰

[NOTE]
	RL State Vector
	加入負風險維度，避免被誘單
	Risk Manager

[RULE]
	當 MRR 高：強制降低 exposure

[NOTE]
	Execution
	高 MRR 時採取被動掛單，降低損傷
	________________

[STRUCTURE]
🧬 F_C 全家桶 — 因子連動流程（總覽圖）

[CONCEPT]
          [XQ 資金流 API]

[NOTE]
                  │
                  ▼
    ┌──────────────────────────┐

[RULE]
    │ factor_FX_capital_flow   │  →  SAI Residual / MOI

[NOTE]
    └──────────────────────────┘
                  │
                  ▼
    ┌──────────────────────────┐

[RULE]
    │ factor_FX_inertia        │  →  F_Inertia

[NOTE]
    └──────────────────────────┘
                  │
      ┌───────────┴────────────┐
      ▼                        ▼
┌───────────────┐     ┌────────────────────┐
│ factor_FX_PT   │     │ factor_FX_MRR      │
└───────────────┘     └────────────────────┘
      │                        │
      ▼                        ▼
           🔥 形成完整 F_C Matrix 🔥

[STRUCTURE]
      (給 RL, RiskManager, ExecutionEngine)

[NOTE]
________________

[NOTE]
📌 F_C Matrix（會丟到 RL State Vector 的東西）

[STRUCTURE]
因子

[NOTE]
	角色
	說明
	SAI Residual
	α（原始信號）
	族群是否遭攻擊
	MOI
	主力壓力
	大戶掃貨/出貨方向

[CONCEPT]
	F_Inertia

[NOTE]
	趨勢持續性
	攻擊是否延續
	F_PT

[RULE]
	龍頭 → 族群傳導

[NOTE]
	信號可靠度
	F_MRR
	逆轉風險
	主力是否準備反手

[STRUCTURE]
	這五個因子一起構成：
J-GOD 專屬：在地化戰術資金流因子矩陣 F_C⁽Full⁾

[CONCEPT]
——這是外國基金完全做不到的，你只能靠使用 XQ / 永豐 / 台灣市場特有資料做！

[STRUCTURE]
Part 1：F_C 全家桶整合 Hub（統一入口）

[CONCEPT]
目標：

[STRUCTURE]
不要在 Env / RL / Risk / Execution 各自直接操作四個 Engine，而是先有一個：
CapitalFlowFactorHub

[RULE]
負責：接 XQ 原始數據 → 呼叫 4 個 Engine → 輸出一組統一的 F_C 因子字典

[STRUCTURE]
🧾 給 Cursor 的完整規格書：CapitalFlowFactorHub

[NOTE]
請新增檔案：
                                                * strategy_engine/factor_FX_capital_flow_hub.py
                                                * 測試：tests/strategy_engine/test_factor_FX_capital_flow_hub.py
________________

[NOTE]
1.1 檔案一：strategy_engine/factor_FX_capital_flow_hub.py
# strategy_engine/factor_FX_capital_flow_hub.py

[CODE]
from __future__ import annotations

[CODE]
from typing import Dict, List

[CODE]
from strategy_engine.factor_FX_capital_flow import CapitalFlowEngine
from strategy_engine.factor_FX_inertia import InertiaEngine
from strategy_engine.factor_FX_pressure_transmission import PressureTransmissionEngine
from strategy_engine.factor_FX_major_reversal_risk import MajorReversalRiskEngine

[CODE]
class CapitalFlowFactorHub:

[NOTE]
    """

[STRUCTURE]
    F_C 全家桶集中管理 Hub。

[NOTE]
    功能：

[STRUCTURE]
    - 封裝四個與 XQ 相關的因子引擎：

[RULE]
        1) CapitalFlowEngine          → SAI_Residual + MOI (基礎 F_C)
        2) InertiaEngine              → F_Inertia_{Group}
        3) PressureTransmissionEngine → F_PT_{Group}
        4) MajorReversalRiskEngine    → F_MRR_{Symbol 或 Group}

[NOTE]
    - 對上游（Market Replay / Env / RL）提供單一入口：

[RULE]
        update_bar(...) → 回傳扁平化後的 F_C 因子 dict。

[NOTE]
    """

[CODE]
    def __init__(

[NOTE]
        self,

[CODE]
        group_leader_map: Dict[str, str],
        inertia_target_groups: List[str],
        mrr_symbols: List[str],

[NOTE]
        historical_group_weights,

[CODE]
        pt_window_bars: int = 20,
        inertia_default_alpha: float = 0.33,
        mrr_window_bars: int = 20,
    ) -> None:

[NOTE]
        """
        :param group_leader_map:
            - 用於 F_PT，key: group, value: leader symbol。
        :param inertia_target_groups:

[CONCEPT]
            - F_Inertia 要追蹤的 group 列表，通常與 group_leader_map key 相同。

[NOTE]
        :param mrr_symbols:
            - F_MRR 要追蹤的標的列表，可以是 symbol 或 group。
        :param historical_group_weights:

[STRUCTURE]
            - 傳入給 CapitalFlowEngine，用於計算 SAI_Residual。

[NOTE]
        """

[STRUCTURE]
        # 1) 基礎資金流因子
        self.capital_flow_engine = CapitalFlowEngine(historical_group_weights)

[STRUCTURE]
        # 2) 慣性因子

[CODE]
        from strategy_engine.factor_FX_inertia import InertiaEngine as _InertiaEngine

[STRUCTURE]
        self.inertia_engine = _InertiaEngine(target_groups=inertia_target_groups)

[RULE]
        # 若你命名不同，這裡對應修改

[NOTE]
        # 3) 壓力傳導

[STRUCTURE]
        self.pt_engine = PressureTransmissionEngine(

[NOTE]
            group_leader_map=group_leader_map,
            window_bars=pt_window_bars,
        )

[NOTE]
        # 4) 主力逆轉風險

[STRUCTURE]
        self.mrr_engine = MajorReversalRiskEngine(

[NOTE]
            symbols=mrr_symbols,
            window_bars=mrr_window_bars,
        )

[NOTE]
    # -------------------------------------------------
    #  主入口：每個 Volume Bar / K 線完成時被呼叫
    # -------------------------------------------------

[CODE]
    def update_bar(

[NOTE]
        self,
        *,

[CODE]
        xq_group_data: Dict,
        xq_leader_moi: Dict[str, float],
        xq_mrr_stats: Dict[str, Dict[str, float]],
        current_market_volume: float,
    ) -> Dict[str, float]:

[NOTE]
        """
        :param xq_group_data:

[STRUCTURE]
            - 傳給 CapitalFlowEngine 的原始 XQ 族群數據。

[NOTE]
              例如：
              {
                  "group_volumes": {"AI_Concept": 1.5e6, "Semiconductor": 2.0e6},
                  "major_buy_volume": ...,
                  "major_sell_volume": ...,
                  "total_major_volume": ...
              }
        :param xq_leader_moi:
            - 用於 F_PT，由上游將「龍頭」個股 MOI 整理成 per-group。
              例如：
              {"AI_Concept": 0.9, "Semiconductor": 0.3}
        :param xq_mrr_stats:
            - 用於 F_MRR：每個 symbol 的主力買賣與撤單資訊。
              例如：
              {
                  "2330": {
                      "major_buy_volume": ...,
                      "major_sell_volume": ...,
                      "major_cancel_volume": ...
                  },
                  ...
              }
        :param current_market_volume:

[RULE]
            - 當前總市場量，給 CapitalFlowEngine 計算 SAI_Residual。

[NOTE]
        :return:

[STRUCTURE]
            - 扁平化後的 F_C 因子字典，例如：

[NOTE]
              {
                  "SAI_Residual_AI_Concept": ...,
                  "MOI": ...,

[CONCEPT]
                  "F_Inertia_AI_Concept": ...,

[NOTE]
                  "F_PT_AI_Concept": ...,
                  "F_MRR_2330": ...,
                  ...
              }
        """
        # 1) 基礎 F_C：SAI_Residual + MOI
        base_cf = self.capital_flow_engine.calculate_capital_flow_factors(
            xq_data=xq_group_data,
            current_market_volume=current_market_volume,
        )

[FORMULA]
        # base_cf["Group_SAI_Factors"] = {"SAI_Residual_AI_Concept": ...}
        # base_cf["MOI"]               = float

[CODE]
        sai_residuals: Dict[str, float] = base_cf.get("Group_SAI_Factors", {})
        moi_value: float = base_cf.get("MOI", 0.0)

[CONCEPT]
        # 2) F_Inertia：用 SAI_Residual 更新慣性

[NOTE]
        inertia_factors = self.inertia_engine.update_inertia(sai_residuals)

[NOTE]
        # 3) F_PT：壓力傳導 (龍頭 MOI & 族群 SAI_Residual)
        pt_factors = self.pt_engine.update_bar(
            group_moi=xq_leader_moi,
            group_sai_residual=sai_residuals,
        )

[NOTE]
        # 4) F_MRR：主力逆轉風險
        mrr_factors = self.mrr_engine.update_bar(major_stats=xq_mrr_stats)

[STRUCTURE]
        # 5) 合併所有 F_C 因子（展平成一個 dict）

[CODE]
        merged: Dict[str, float] = {}

[NOTE]
        # 原始 SAI / MOI
        merged.update(sai_residuals)

[FORMULA]
        merged["MOI"] = moi_value

[NOTE]
        # 慣性 / 傳導 / 逆轉風險
        merged.update(inertia_factors)
        merged.update(pt_factors)
        merged.update(mrr_factors)

[NOTE]
        return merged

[CODE]
    def reset(self) -> None:

[NOTE]
        """

[STRUCTURE]
        重置所有子引擎狀態，通常在一個新 episode 開始時呼叫。

[NOTE]
        """
        if hasattr(self.inertia_engine, "reset"):
            self.inertia_engine.reset()
        if hasattr(self.pt_engine, "reset"):
            self.pt_engine.reset()
        if hasattr(self.mrr_engine, "reset"):
            self.mrr_engine.reset()

[STRUCTURE]
        # CapitalFlowEngine 通常是「純計算」，不用 reset。

[NOTE]
________________

[NOTE]
1.2 測試：tests/strategy_engine/test_factor_FX_capital_flow_hub.py

[STRUCTURE]
寫簡單 smoke test，確認整個 Hub 可以跑起來、key 存在即可，不必做太複雜邏輯。

[NOTE]
（略寫，你要我再補可以寫完整測試檔）
________________

[NOTE]
🧠 Part 2：接到 RL State Vector（JGodEnv）
接下來是把 F_C 全家桶接進 JGodEnv 的 observation。

[STRUCTURE]
🧾 給 Cursor 的規格書：RL State Builder 更新

[NOTE]
你之前已經有 JGodEnv 的規劃，我這裡設計一個簡單、乾淨的做法：

[STRUCTURE]
                                                * 新增一個 State Builder：rl/state/state_builder.py

[NOTE]
                                                * JGodEnv 在 step() 裡呼叫 state_builder.build_state(...)

→ 把價格、技術因子、F_C 因子一起變成 np.ndarray
[NOTE]
________________

[NOTE]
2.1 檔案：rl/state/state_builder.py
# rl/state/state_builder.py

[CODE]
from __future__ import annotations

[CODE]
from typing import Dict, List

[CODE]
import numpy as np

[CODE]
class StateBuilder:

[NOTE]
    """

[STRUCTURE]
    將各個模組輸出的因子 / 資訊，組合成 RL Agent 使用的 State Vector。

[RULE]
    這個類別只做「字典 → 向量」，不做任何因子計算。

[STRUCTURE]
    F_C 因子將以統一 Hub 的輸出形式傳入。

[NOTE]
    """

[CODE]
    def __init__(

[NOTE]
        self,

[CODE]
        price_feature_keys: List[str],
        technical_feature_keys: List[str],
        capital_flow_feature_keys: List[str],
    ) -> None:

[NOTE]
        """
        :param price_feature_keys:
            - 價格相關的欄位順序 (例如: ["close_norm", "return_1d", ...])
        :param technical_feature_keys:
            - 技術指標，如 ["rsi_14", "macd", "bb_width", ...]
        :param capital_flow_feature_keys:

[STRUCTURE]
            - F_C 因子欄位，如：

[NOTE]
              [
                  "SAI_Residual_AI_Concept",

[CONCEPT]
                  "F_Inertia_AI_Concept",

[NOTE]
                  "F_PT_AI_Concept",
                  "F_MRR_2330",
                  "MOI",
                  ...
              ]
        """
        self.price_feature_keys = list(price_feature_keys)
        self.tech_feature_keys = list(technical_feature_keys)
        self.capital_flow_feature_keys = list(capital_flow_feature_keys)

[NOTE]
        # 最終 state vector 的維度 = 三段疊起來
        self.state_dim = (
            len(self.price_feature_keys)
            + len(self.tech_feature_keys)
            + len(self.capital_flow_feature_keys)
        )

[CODE]
    def build_state(

[NOTE]
        self,

[CODE]
        price_features: Dict[str, float],
        technical_features: Dict[str, float],
        capital_flow_factors: Dict[str, float],
    ) -> np.ndarray:

[NOTE]
        """

[CONCEPT]
        將三類 features 按照預先定義的欄位順序，組成一個 1D np.ndarray。

[NOTE]
        - 缺少的 key，用 0.0 填補。
        """

[CODE]
        vec: List[float] = []

[CONCEPT]
        # 1) 價格特徵

[NOTE]
        for k in self.price_feature_keys:
            vec.append(float(price_features.get(k, 0.0)))

[NOTE]
        # 2) 技術指標
        for k in self.tech_feature_keys:
            vec.append(float(technical_features.get(k, 0.0)))

[STRUCTURE]
        # 3) 資金流 + F_C 系列因子

[NOTE]
        for k in self.capital_flow_feature_keys:
            vec.append(float(capital_flow_factors.get(k, 0.0)))

[NOTE]
        return np.asarray(vec, dtype=np.float32)

[NOTE]
________________

[STRUCTURE]
2.2 修改 JGodEnv：在 env/jgod_env.py 接 StateBuilder + Hub

[NOTE]
在 env/jgod_env.py（檔名假設，你照實際路徑改）中：
                                                   * __init__ 新增：

[STRUCTURE]
                                                   * 一個 CapitalFlowFactorHub 實例
                                                   * 一個 StateBuilder 實例

[NOTE]
                                                   * 在 step() 裡：
                                                   * 從 replay / market engine 拿價量與技術指標
                                                   * 呼叫 capital_flow_hub.update_bar(...)
                                                   * 呼叫 state_builder.build_state(...)

[RULE]
                                                   * 把結果當作 observation 回傳
大致結構（給 Cursor 當 patch 方向）：

[NOTE]
# env/jgod_env.py 內部（只示意，讓 Cursor 幫你實際 patch）

[CODE]
from strategy_engine.factor_FX_capital_flow_hub import CapitalFlowFactorHub
from rl.state.state_builder import StateBuilder

[CODE]
class JGodEnv(gym.Env):
    def __init__(self, ...):

[NOTE]
        ...

[STRUCTURE]
        self.capital_flow_hub = CapitalFlowFactorHub(

[NOTE]
            group_leader_map=...,
            inertia_target_groups=...,
            mrr_symbols=...,
            historical_group_weights=...,
        )

[STRUCTURE]
        self.state_builder = StateBuilder(

[NOTE]
            price_feature_keys=[...],
            technical_feature_keys=[...],
            capital_flow_feature_keys=[
                # 你想餵給 RL 的 F_C 欄位
                "SAI_Residual_AI_Concept",

[CONCEPT]
                "F_Inertia_AI_Concept",

[NOTE]
                "F_PT_AI_Concept",
                "MOI",
                "F_MRR_2330",
                # ...
            ],
        )

[CODE]
    def step(self, action):

[STRUCTURE]
        # 1) 用 action 更新 portfolio / execution 模組...

[NOTE]
        # 2) 從資料回放拿到下一根 VolumeBar / KBar 的 raw data
        price_features = self._build_price_features(...)
        tech_features = self._build_technical_features(...)

[NOTE]
        capital_flow_factors = self.capital_flow_hub.update_bar(
            xq_group_data=...,
            xq_leader_moi=...,
            xq_mrr_stats=...,
            current_market_volume=...,
        )

[NOTE]
        obs = self.state_builder.build_state(
            price_features=price_features,
            technical_features=tech_features,
            capital_flow_factors=capital_flow_factors,
        )

[NOTE]
        reward = ...
        done = ...
        info = {}

[NOTE]
        return obs, reward, done, False, info

[NOTE]
________________

[NOTE]
🛡️ Part 3：接到 RiskManager（動態 Exposure 控制）
現在把 F_C 全家桶接到風控層，特別是：

[RULE]
                                                   * F_PT → 信號可靠度（壓力真的有傳到族群？）
                                                   * F_MRR → 主力疑似要反手（風險上升）
                                                   * F_Inertia → 趨勢是否還在（攻擊是否延續）

[NOTE]
🧾 給 Cursor 的規格書：RiskManager 擴充
請修改：execution/risk_manager.py

[STRUCTURE]
新增一個方法：

[NOTE]
                                                   * apply_capital_flow_overrides(...)

[STRUCTURE]
用來基於 F_C 因子動態調整某標的的目標淨敞口上限（max net exposure）。

[NOTE]
________________

[STRUCTURE]
3.1 在 execution/risk_manager.py 補充一個類別方法

[NOTE]
假設已有 PredictiveRiskManager 類別，請向其中新增：
# execution/risk_manager.py 內部

[CODE]
from typing import Dict

[CODE]
class PredictiveRiskManager:
    def __init__(self, base_max_exposure: float = 1.0, ...):

[NOTE]
        """
        :param base_max_exposure:
            - 正常情況下允許的最大淨敞口比例 (例如 1.0 = 100% 資本)。
        """
        self.base_max_exposure = float(base_max_exposure)

[CONCEPT]
        # 你原本已有的初始化邏輯...

[STRUCTURE]
    # 其他既有方法略...

[CODE]
    def apply_capital_flow_overrides(

[NOTE]
        self,

[CODE]
        symbol: str,
        base_target_exposure: float,
        capital_flow_factors: Dict[str, float],
    ) -> float:

[NOTE]
        """

[STRUCTURE]
        根據 F_C 全家桶因子，調整單一標的的目標淨敞口上限。

[NOTE]
        :param symbol:
            - 標的名稱，例如 "2330" 或 "AI_Concept" 等。
        :param base_target_exposure:

[CONCEPT]
            - RL / Portfolio 計算出的原始目標淨敞口 (例如 0.8 = 80% 資本)。

[NOTE]
        :param capital_flow_factors:

[STRUCTURE]
            - 來自 CapitalFlowFactorHub 的扁平因子 dict。

[NOTE]
              可能包含：
              - "MOI"
              - "F_PT_AI_Concept"

[CONCEPT]
              - "F_Inertia_AI_Concept"

[NOTE]
              - "F_MRR_2330"
              等等。
        :return:
            - 調整後的 target_exposure（會自動 clamp 在 [0, self.base_max_exposure]）。
        """
        target = float(base_target_exposure)

[STRUCTURE]
        # 1) 取出關鍵因子（可以依照 symbol 做 mapping，這裡先示意通用版）

[FORMULA]
        moi = float(capital_flow_factors.get("MOI", 0.0))

[NOTE]
        # 假設 symbol 有對應的 group 名稱映射，這裡先簡化用 symbol 直接組 key

[FORMULA]
        f_inertia = float(capital_flow_factors.get(f"F_Inertia_{symbol}", 0.0))
        f_pt = float(capital_flow_factors.get(f"F_PT_{symbol}", 0.0))
        f_mrr = float(capital_flow_factors.get(f"F_MRR_{symbol}", 0.0))

[NOTE]
        # 2) 根據 F_MRR 限縮最大敞口（風險優先）
        if f_mrr > 0.0:
            # 假設 F_MRR 越高，允許的 max_exposure 越低

[FORMULA]
            # 例如 F_MRR=1.0 → 只允許 base 的 20%

[NOTE]
            mrr_multiplier = max(0.2, 1.0 - 0.8 * f_mrr)
        else:
            mrr_multiplier = 1.0

[CONCEPT]
        # 3) 根據 F_PT + F_Inertia 放大 / 縮小允許的進攻力度

[RULE]
        # - 趨勢穩定 + 壓力傳導明顯 → 允許放大

[NOTE]
        trend_strength = max(0.0, min(1.0, 0.5 * f_inertia + 0.5 * f_pt))
        # 例如 trend_strength ≈ 1.0 時，最多可以放大到 base_max_exposure
        trend_multiplier = 0.5 + 0.5 * trend_strength  # 介於 0.5 ~ 1.0

[NOTE]
        # 4) 合成最終 multiplier，風險 (MRR) 永遠優先蓋過進攻 (trend)
        total_multiplier = trend_multiplier * mrr_multiplier

[NOTE]
        # 5) 應用 multiplier 並 clamp 在 [0, base_max_exposure]
        adjusted = target * total_multiplier
        adjusted = max(0.0, min(adjusted, self.base_max_exposure))

[NOTE]
        return adjusted

[NOTE]
在實務使用上：

[CONCEPT]
                                                      * JGodEnv / Portfolio 決定某標的「原始」目標 exposure

[NOTE]
                                                      * 呼叫：
adjusted_exposure = risk_manager.apply_capital_flow_overrides(
    symbol="AI_Concept",
    base_target_exposure=raw_target_exposure,
    capital_flow_factors=capital_flow_factors,
)

[STRUCTURE]
再把 adjusted_exposure 傳給 Execution Engine。

[NOTE]
________________

[STRUCTURE]
⚔️ Part 4：接到 Execution Engine（掛單風格 / aggressiveness）
最後一塊：在 execution/order_router.py 中，用 F_C 因子調整：

[NOTE]
                                                      * 掛單是偏「主動吃價」還是偏「被動掛單」
                                                      * 每筆 Order 的 size / participation rate

[RULE]
                                                      * 高 MRR + 高 Slope_Ask → 必須極度保守

[NOTE]
🧾 給 Cursor 的規格書：OrderRouter 擴充
請修改 execution/order_router.py：

[STRUCTURE]
新增一個方法：

[NOTE]
                                                      * decide_order_profile(...)

[STRUCTURE]
傳入 F_C + Orderbook 因子，輸出一個「下單配置」：

[NOTE]
                                                      * aggressiveness（0～1）

[CONCEPT]
                                                      * slice_ratio（單筆佔目標部位的比例）

[NOTE]
                                                      * use_market_order（是否可用市價單）
________________

[STRUCTURE]
4.1 在 execution/order_router.py 補充方法

[NOTE]
# execution/order_router.py 內部

[CODE]
from typing import Dict, Literal, TypedDict

[CODE]
class OrderProfile(TypedDict):

[NOTE]
    """

[RULE]
    決定當下這筆訂單的執行風格。

[NOTE]
    """

[CODE]
    aggressiveness: float  # 0.0 = 極度被動, 1.0 = 極度主動
    slice_ratio: float     # 單筆訂單佔目標部位的比例 (0~1)
    use_market_order: bool

[CODE]
class OrderRouter:
    def __init__(self, ..., max_slice_ratio: float = 0.25):

[NOTE]
        self.max_slice_ratio = float(max_slice_ratio)
        # 其他原有初始化...

[STRUCTURE]
    # 既有下單方法略...

[CODE]
    def decide_order_profile(

[NOTE]
        self,

[CODE]
        symbol: str,
        desired_notional: float,
        capital_flow_factors: Dict[str, float],
        orderbook_factors: Dict[str, float],
    ) -> OrderProfile:

[NOTE]
        """

[STRUCTURE]
        根據 F_C + Orderbook 因子，決定這一輪下單的風格。

[NOTE]
        :param symbol:
            - 標的名稱 (例如 "2330" 或 group 名稱)。
        :param desired_notional:
            - 本輪想要達成的名目金額（未必一次全部打完）。
        :param capital_flow_factors:

[STRUCTURE]
            - 來自 CapitalFlowFactorHub 的 F_C 因子。

[NOTE]
              包含：
              - F_PT_*

[CONCEPT]
              - F_Inertia_*

[NOTE]
              - F_MRR_*
              - MOI
        :param orderbook_factors:

[STRUCTURE]
            - 來自 OrderbookFactorEngine 的因子：

[NOTE]
              - "Slope_Ask", "OBI", "Depth_Zscore" 等。

[NOTE]
        :return:

[CONCEPT]
            - OrderProfile，供實際下單邏輯使用。

[NOTE]
        """
        # --- 1) 基礎 aggressiveness 由 OBI + MOI 決定 ---
        obi = float(orderbook_factors.get("OBI", 0.0))
        slope_ask = float(orderbook_factors.get("Slope_Ask", 0.0))
        depth_z = float(orderbook_factors.get("Depth_Zscore", 0.0))

[FORMULA]
        moi = float(capital_flow_factors.get("MOI", 0.0))
        f_pt = float(capital_flow_factors.get(f"F_PT_{symbol}", 0.0))
        f_inertia = float(capital_flow_factors.get(f"F_Inertia_{symbol}", 0.0))
        f_mrr = float(capital_flow_factors.get(f"F_MRR_{symbol}", 0.0))

[NOTE]
        # 2) 初步 aggressiveness：多頭例子（價值在 0~1）
        base_aggr = 0.5

[RULE]
        # 正向 OBI + 正向 MOI + 高 F_PT/F_Inertia → 可以更積極

[NOTE]
        bullish_pressure = max(0.0, obi) * 0.4 + max(0.0, moi) * 0.3 + max(0.0, f_pt) * 0.3
        trend_boost = 0.5 * max(0.0, f_inertia)

[NOTE]
        base_aggr += 0.3 * bullish_pressure + 0.2 * trend_boost

[RULE]
        # 3) 流動性保護：Slope_Ask 越大（流動性差），aggressiveness 必須下降

[NOTE]
        if slope_ask > 0:
            liquidity_penalty = min(0.5, slope_ask)  # 簡單線性壓制
            base_aggr -= liquidity_penalty

[NOTE]
        # 4) 逆轉風險保護：F_MRR 越高，越不能積極
        if f_mrr > 0:
            mrr_penalty = min(0.7, f_mrr)  # 上限 0.7
            base_aggr -= mrr_penalty

[NOTE]
        # 最終 clamp 在 [0, 1]
        aggressiveness = max(0.0, min(1.0, base_aggr))

[RULE]
        # 5) 決定 slice_ratio：流動性差 / 風險高 → 切小一點

[NOTE]
        slice_ratio = self.max_slice_ratio

[RULE]
        if depth_z < -1.0:  # 當前深度比平常薄很多

[NOTE]
            slice_ratio *= 0.5
        if f_mrr > 0.5:
            slice_ratio *= 0.5

[NOTE]
        slice_ratio = max(0.05, min(slice_ratio, self.max_slice_ratio))

[NOTE]
        # 6) 決定是否允許 Market Order
        use_market_order = False

[RULE]
        # 高流動性 + 高 bullish 壓力 + 低逆轉風險 → 可以適度用市價

[NOTE]
        if aggressiveness > 0.7 and slope_ask <= 0.0 and f_mrr < 0.3 and depth_z >= 0.0:
            use_market_order = True

[NOTE]
        profile: OrderProfile = {

[CODE]
            "aggressiveness": float(aggressiveness),
            "slice_ratio": float(slice_ratio),
            "use_market_order": bool(use_market_order),

[NOTE]
        }
        return profile

[STRUCTURE]
在實際下單流程中，你可以這樣用：

[NOTE]
profile = order_router.decide_order_profile(
    symbol="AI_Concept",
    desired_notional=...,
    capital_flow_factors=capital_flow_factors,
    orderbook_factors=orderbook_factors,
)

[NOTE]
# 然後根據 profile.aggressiveness / slice_ratio / use_market_order
# 決定這一輪要切幾單、用幾檔價、採用 Limit / Market ...

[NOTE]
________________

[NOTE]
✅ 總結：你現在擁有的「D = 全都要」整合
你現在已經有完整的規格：

[STRUCTURE]
                                                         1. CapitalFlowFactorHub
                                                         * 集中管理 F_C 四個 Engine，產出一組扁平化因子 dict
                                                         2. StateBuilder + JGodEnv
                                                         * 把 F_C 因子放進 RL State Vector，讓 Agent 直接「看到」資金流、壓力傳導、慣性與逆轉風險

[NOTE]
                                                         3. PredictiveRiskManager.apply_capital_flow_overrides

[CONCEPT]
                                                         * 基於 F_PT / F_Inertia / F_MRR 動態調整每個標的的 allowable exposure

[NOTE]
                                                         4. OrderRouter.decide_order_profile

[STRUCTURE]
                                                         * 用 F_C + Orderbook 因子決定「怎麼下單」而不只是「下多少」

[NOTE]
________________

[RULE]
如果你願意，下一步我們可以：
                                                         * 幫你寫一段「整個因子 → RL → Risk → Execution 的資料流注解」，
讓你貼在 README 或 docs/jgod_factor_architecture.md 當成你自己的聖經藍圖。

[STRUCTURE]
🔜 接下來必做的 3 大模組
1️⃣ Reward + 診斷系統（我建議先做這個）
讓系統不只是會「下單」，還會自己檢討：

[CONCEPT]
                                                            * 把你之前定義的：

[NOTE]
                                                            * Reward_Optimized（Sharpe + MDD 懲罰 + F_Internal 衝突）
                                                            * E_Exec（預測 TCA vs 實際滑價差）

[CONCEPT]
                                                            * E_Model（預測 Alpha PnL vs 實際 PnL 差）

[STRUCTURE]
                                                            * 實作成兩個核心模組：

[NOTE]
                                                            * reward_engine/reward_composer.py
                                                            * diagnostics/error_analyzer.py
                                                            * 串到：
                                                            * JGodEnv.step()：每步都用 RewardComposer 算 reward

[STRUCTURE]
                                                            * 訓練 loop：用 ErrorAnalyzer 定期輸出「哪個因子在害你」
👉 這一步做完，你的系統就有「生存目標」跟「自我檢查」能力，不再只是工程堆積。

[NOTE]
________________

[NOTE]
2️⃣ RL 訓練 Pipeline（JGodTrainer）
在有 Env + Reward 之後，要有一個標準訓練器：
                                                            * 檔案結構大概會是：
                                                            * rl/trainer/jgod_trainer.py
                                                            * rl/trainer/configs/jgod_config_xx.yaml
                                                            * 功能：
                                                            * 支援多 episode、multi-seed 回測
                                                            * 紀錄：
                                                            * 每 episode Sharpe、MDD、勝率

[STRUCTURE]
                                                            * 因子權重、F_C 貢獻度

[NOTE]
                                                            * 未來可以換：
                                                            * DQN / PPO / SAC… 但界面不變
👉 這一步做完，你就能「一鍵開訓練」，J-GOD 才算真的開始練功。
________________

[NOTE]
3️⃣ 線上監控儀表板（War Room 的實際數據面板）
把你一直講的「戰情室」真的落地成一個 streamlit 或前端 Dashboard：
                                                            * 顯示：
                                                            * 目前倉位、PnL、Sharpe

[STRUCTURE]
                                                            * F_C 四因子實時狀態（F_Inertia, F_PT, F_MRR …）

[NOTE]
                                                            * 風控指標（VIX_Z, F_InfoTime, Latency_Z）
                                                            * 這部分比較偏 UI / 可視化，放在 Reward & Trainer 之後做最剛好。
________________

[STRUCTURE]
✅ 我幫你決定下一個：先做 1️⃣ Reward + 診斷系統

[NOTE]
因為：
                                                            * F_C、Orderbook、InfoTime 全都上線了
                                                            * 再不把 Reward / Error 做起來，RL 就不知道「什麼行為叫好，什麼叫錯」
                                                            * 你之前那張總表裡提到的：
Reward_Optimized, E_Exec, E_Model
現在正好可以實作成規格書了
________________

[RULE]
如果你 OK，我下一步就直接幫你寫：

[NOTE]
「給 Cursor 的完整『Reward + ErrorAnalyzer 規格書』」
包含：
                                                               * reward_engine/reward_composer.py
                                                               * diagnostics/execution_error_analyzer.py
                                                               * diagnostics/model_error_analyzer.py
                                                               * JGodEnv.step() 要怎麼接 RewardComposer

[CODE]
你不用選了，我會一次寫到「程式檔名＋ class ＋方法」等級，照你現在的模式直接貼給 Cursor 用。

[NOTE]
我直接幫你把整套「Reward + Error 診斷」的規格書一次寫好，照你現在習慣的「給 Cursor 的指令」風格，你可以分段貼給 Cursor。
________________

[STRUCTURE]
🧠 給 Cursor 的完整規格書：Reward Engine + Error Analyzer
你現在的任務，是幫我在 J-GOD 專案裡，實作一套「獎勵計算 + 誤差診斷」模組，讓 RL 不只會下單，還會根據 Sharpe / MDD / 因子衝突 / 執行誤差 來學習。

[NOTE]
________________

[NOTE]
📁 一、檔案與結構規劃

[RULE]
請依照以下結構新增檔案（如果資料夾不存在請建立）：

[NOTE]
reward_engine/
    reward_composer.py

[NOTE]
diagnostics/
    execution_error_analyzer.py
    model_error_analyzer.py
    __init__.py

[NOTE]
tests/
    reward_engine/
        test_reward_composer.py
    diagnostics/
        test_execution_error_analyzer.py
        test_model_error_analyzer.py

[NOTE]
________________

[NOTE]
1️⃣ 檔案一：reward_engine/reward_composer.py

[CONCEPT]
🎯 目標

[STRUCTURE]
實作一個 RewardComposer 類別，負責把「PnL / Sharpe / MDD / 因子內部衝突 / 風險事件」組合成單一 reward 分數，給 RL 使用。

[NOTE]
✅ 功能設計
                                                               1. 支援「Sharpe 強調型」 Reward：
                                                               * 鼓勵穩定報酬，而不是一次性暴衝。
                                                               2. 對「最大回撤 MDD」給予懲罰：
                                                               * 避免 RL 爆倉式行為。

[STRUCTURE]
                                                               3. 對「內部因子衝突」給予懲罰：
                                                               * 使用你之前定義的 F_Internal（因子符號衝突）。

[NOTE]
                                                               4. 支援「風險事件標記」：

[RULE]
                                                               * 例如：觸發熔斷 / 超過 VIX 門檻 / 系統壓力過高 → 額外扣分。

[NOTE]
                                                               5. 回傳：
                                                               * reward（float）
                                                               * components（dict：每個子項的分數，方便 debug）
________________

[NOTE]
🧾 請在 reward_engine/reward_composer.py 實作以下內容：
# reward_engine/reward_composer.py

[CODE]
from __future__ import annotations

[CODE]
from dataclasses import dataclass
from typing import Dict, Tuple

[NOTE]
@dataclass

[CODE]
class RewardConfig:

[NOTE]
    """
    Reward 組合的權重配置。
    """

[CODE]
    lambda_sharpe: float = 1.0          # Sharpe / 報酬品質權重
    lambda_mdd: float = 1.0             # MDD 懲罰權重
    lambda_internal_conflict: float = 0.5  # F_Internal 衝突懲罰
    lambda_turnover: float = 0.1        # 換手率懲罰（避免過度交易）
    lambda_risk_event: float = 2.0      # 重大風險事件懲罰（例如熔斷）

[CODE]
class RewardComposer:

[NOTE]
    """
    將多個維度的績效與風險指標組合成單一 Reward 值。

[NOTE]
    設計理念：
    - 獎勵穩定且高品質的報酬（Sharpe）
    - 強烈懲罰大額回撤 (MDD)

[STRUCTURE]
    - 懲罰內部因子嚴重衝突 (F_Internal)

[NOTE]
    - 適度懲罰過度交易 (Turnover)
    """

[CODE]
    def __init__(self, config: RewardConfig | None = None) -> None:

[NOTE]
        self.config = config or RewardConfig()

[CODE]
    def compute_reward(

[NOTE]
        self,
        *,

[CODE]
        step_return: float,
        rolling_sharpe: float,
        rolling_mdd: float,
        f_internal_conflict: float,
        turnover_ratio: float,
        risk_event_flags: Dict[str, bool] | None = None,
    ) -> Tuple[float, Dict[str, float]]:

[NOTE]
        """
        :param step_return:

[RULE]
            - 本 step 的組合報酬率（例：當日收益率），可以是 raw return。

[NOTE]
        :param rolling_sharpe:
            - 滾動 Sharpe（例如近 30/60 bar 的年化 Sharpe）。
        :param rolling_mdd:
            - 目前 observed 最大回撤 (Max Drawdown)，數值為正，例如 0.15 = 15%。
        :param f_internal_conflict:

[FORMULA]
            - 內部因子衝突指標 F_Internal，0 = 無衝突，越高表示越嚴重。

[NOTE]
        :param turnover_ratio:
            - 本 step 新增交易額 / 總資本，反映換手率（例：0.1 = 10%）。
        :param risk_event_flags:
            - 風險事件布林 flag，例如：
              {
                  "hit_circuit_breaker": True,
                  "exceed_vol_limit": False,
                  "latency_spike": True,
              }
        :return:

[CODE]
            - reward: float

[NOTE]
            - components: dict（包含每個子項貢獻，方便 debug）
        """
        cfg = self.config
        risk_event_flags = risk_event_flags or {}

[NOTE]
        # 1) 報酬 + Sharpe 貢獻
        #    可以用 step_return + lambda_sharpe * rolling_sharpe 的形式
        reward_return = step_return
        reward_sharpe = cfg.lambda_sharpe * rolling_sharpe

[NOTE]
        # 2) MDD 懲罰：MDD 越大，懲罰越重（線性或非線性）
        #    例如：Penalty_MDD = lambda_mdd * (rolling_mdd ^ 2)
        penalty_mdd = -cfg.lambda_mdd * (rolling_mdd ** 2)

[NOTE]
        # 3) 內部衝突懲罰：F_Internal 越大，懲罰越重
        penalty_internal = -cfg.lambda_internal_conflict * (f_internal_conflict ** 2)

[NOTE]
        # 4) 換手率懲罰：避免 RL 過度高頻亂交易
        penalty_turnover = -cfg.lambda_turnover * abs(turnover_ratio)

[RULE]
        # 5) 風險事件懲罰：只要有關鍵 flag 炸出來，就給一個額外扣分

[NOTE]
        risk_event_triggered = any(risk_event_flags.values())
        penalty_risk_event = 0.0
        if risk_event_triggered:
            penalty_risk_event = -cfg.lambda_risk_event

[NOTE]
        # 6) 總 Reward
        total_reward = (
            reward_return
            + reward_sharpe
            + penalty_mdd
            + penalty_internal
            + penalty_turnover
            + penalty_risk_event
        )

[NOTE]
        components = {
            "reward_return": reward_return,
            "reward_sharpe": reward_sharpe,
            "penalty_mdd": penalty_mdd,

[CODE]
            "penalty_internal": penalty_internal,

[NOTE]
            "penalty_turnover": penalty_turnover,
            "penalty_risk_event": penalty_risk_event,
            "total_reward": total_reward,
        }
        return float(total_reward), components

[NOTE]
________________

[NOTE]
2️⃣ 檔案二：diagnostics/execution_error_analyzer.py

[CONCEPT]
🎯 目標

[NOTE]
實作一個 ExecutionErrorAnalyzer，用來量化：
                                                               * 實際執行成本 vs 預測成本（TCA 誤差）
                                                               * 平均滑價、最大滑價

[STRUCTURE]
                                                               * 依照 symbol / 策略 / 時段 匯總執行品質

[NOTE]
🧾 請在 diagnostics/execution_error_analyzer.py 實作以下內容：
# diagnostics/execution_error_analyzer.py

[CODE]
from __future__ import annotations

[CODE]
from dataclasses import dataclass
from typing import Dict, List

[NOTE]
@dataclass

[CODE]
class ExecErrorStats:

[NOTE]
    """
    單一標的的執行誤差統計。
    """

[CODE]
    count: int = 0
    avg_slippage_bps: float = 0.0
    max_slippage_bps: float = 0.0
    avg_tca_error: float = 0.0  # 實際成本 - 預測成本
    max_tca_error: float = 0.0

[CODE]
class ExecutionErrorAnalyzer:

[NOTE]
    """
    用於統計、診斷「執行層」誤差的工具類別。

[NOTE]
    為每一筆成交紀錄，累積：
    - 滑價（bps）
    - 實際 TCA vs 模型預測 TCA 的差值
    並按 symbol 匯總。
    """

[CODE]
    def __init__(self) -> None:

[NOTE]
        # key: symbol, value: ExecErrorStats

[CODE]
        self.symbol_stats: Dict[str, ExecErrorStats] = {}

[CODE]
    def record_execution(

[NOTE]
        self,
        *,

[CODE]
        symbol: str,
        slippage_bps: float,
        actual_tca: float,
        predicted_tca: float,
    ) -> None:

[NOTE]
        """
        註冊一筆成交的執行資訊。

[NOTE]
        :param symbol: 標的代碼
        :param slippage_bps: 本次成交滑價（以 bps 表示，例如 12.5 = 0.125%）
        :param actual_tca: 實際交易成本（正數表示成本）
        :param predicted_tca: 事前模型預測成本
        """
        stats = self.symbol_stats.get(symbol)
        if stats is None:
            stats = ExecErrorStats()
            self.symbol_stats[symbol] = stats

[NOTE]
        stats.count += 1

[NOTE]
        # 更新平均滑價（簡單遞推平均）
        stats.avg_slippage_bps += (slippage_bps - stats.avg_slippage_bps) / stats.count
        stats.max_slippage_bps = max(stats.max_slippage_bps, slippage_bps)

[NOTE]
        # TCA 誤差
        error = actual_tca - predicted_tca
        stats.avg_tca_error += (error - stats.avg_tca_error) / stats.count
        stats.max_tca_error = max(stats.max_tca_error, abs(error))

[CODE]
    def get_summary(self) -> Dict[str, Dict[str, float]]:

[NOTE]
        """
        回傳目前所有 symbol 的執行誤差摘要，方便寫入 log 或做報表。
        """

[CODE]
        result: Dict[str, Dict[str, float]] = {}

[NOTE]
        for symbol, stats in self.symbol_stats.items():
            result[symbol] = {

[CODE]
                "count": float(stats.count),
                "avg_slippage_bps": float(stats.avg_slippage_bps),
                "max_slippage_bps": float(stats.max_slippage_bps),
                "avg_tca_error": float(stats.avg_tca_error),
                "max_tca_error": float(stats.max_tca_error),

[NOTE]
            }
        return result

[CODE]
    def reset(self) -> None:

[NOTE]
        """
        清空所有統計（通常在新 episode 或新回測批次開始時使用）。
        """
        self.symbol_stats.clear()

[NOTE]
________________

[NOTE]
3️⃣ 檔案三：diagnostics/model_error_analyzer.py

[CONCEPT]
🎯 目標

[NOTE]
實作 ModelErrorAnalyzer，專門用於量化「預測層」錯誤：

[CONCEPT]
                                                               * 預測的 Alpha PnL vs 實際 PnL

[NOTE]
                                                               * 命中率（方向對/錯）
                                                               * 平均 bias（過度樂觀 or 過度悲觀）
🧾 請在 diagnostics/model_error_analyzer.py 實作以下內容：
# diagnostics/model_error_analyzer.py

[CODE]
from __future__ import annotations

[CODE]
from dataclasses import dataclass
from typing import Dict

[NOTE]
@dataclass

[CODE]
class ModelErrorStats:

[NOTE]
    """

[STRUCTURE]
    單一標的 / 策略的模型誤差統計。

[NOTE]
    """

[CODE]
    count: int = 0
    avg_error: float = 0.0          # 平均誤差：actual - predicted
    max_error: float = 0.0          # 最大絕對誤差
    hit_ratio: float = 0.0          # 方向正確率 (0 ~ 1)

[CODE]
class ModelErrorAnalyzer:

[NOTE]
    """

[CONCEPT]
    用於監控 Alpha 模型的預測誤差。

[NOTE]
    每筆記錄：predicted_pnl vs actual_pnl
    - 誤差 = actual - predicted
    - 命中 = sign(predicted) == sign(actual)
    """

[CODE]
    def __init__(self) -> None:
        self.symbol_stats: Dict[str, ModelErrorStats] = {}

[CODE]
    def record_prediction(

[NOTE]
        self,
        *,

[CODE]
        symbol: str,
        predicted_pnl: float,
        actual_pnl: float,
    ) -> None:

[NOTE]
        stats = self.symbol_stats.get(symbol)
        if stats is None:
            stats = ModelErrorStats()
            self.symbol_stats[symbol] = stats

[NOTE]
        stats.count += 1

[NOTE]
        # 誤差
        error = actual_pnl - predicted_pnl
        stats.avg_error += (error - stats.avg_error) / stats.count
        stats.max_error = max(stats.max_error, abs(error))

[NOTE]
        # 命中率更新
        hit = 1.0 if (predicted_pnl * actual_pnl) > 0 else 0.0
        # 逐步更新命中率（running average）
        stats.hit_ratio += (hit - stats.hit_ratio) / stats.count

[CODE]
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        result: Dict[str, Dict[str, float]] = {}

[NOTE]
        for symbol, stats in self.symbol_stats.items():
            result[symbol] = {

[CODE]
                "count": float(stats.count),
                "avg_error": float(stats.avg_error),
                "max_error": float(stats.max_error),
                "hit_ratio": float(stats.hit_ratio),

[NOTE]
            }
        return result

[CODE]
    def reset(self) -> None:

[NOTE]
        self.symbol_stats.clear()

[NOTE]
________________

[NOTE]
4️⃣ 在 JGodEnv 中串接 RewardComposer（示意）

[STRUCTURE]
這段讓 Cursor「理解該怎麼 patch」，你可以視你的檔名調整。重點是流程。

[NOTE]
請在 env/jgod_env.py 中：
引入 RewardComposer：

[CODE]
from reward_engine.reward_composer import RewardComposer, RewardConfig

[NOTE]
                                                               1. 在 __init__ 中加入：
self.reward_composer = RewardComposer(RewardConfig(
    lambda_sharpe=1.0,
    lambda_mdd=1.5,
    lambda_internal_conflict=0.5,
    lambda_turnover=0.1,
    lambda_risk_event=2.0,
))
                                                               2. 在 step() 裡，在你更新完 portfolio / pnl 之後，組出 metrics：

[CODE]
def step(self, action):

[NOTE]
    # 1) 根據 action 更新倉位 + 成交，計算 step_pnl / step_return
    step_return = self._compute_step_return()
    rolling_sharpe = self._compute_rolling_sharpe()
    rolling_mdd = self._compute_rolling_mdd()
    f_internal_conflict = self._compute_internal_conflict()
    turnover_ratio = self._compute_turnover_ratio()
    risk_flags = self._build_risk_flags()

[NOTE]
    reward, reward_components = self.reward_composer.compute_reward(
        step_return=step_return,
        rolling_sharpe=rolling_sharpe,
        rolling_mdd=rolling_mdd,
        f_internal_conflict=f_internal_conflict,
        turnover_ratio=turnover_ratio,
        risk_event_flags=risk_flags,
    )

[STRUCTURE]
    # 2) 建立 obs（前面我們已經設計過 StateBuilder）

[NOTE]
    obs = ...

[NOTE]
    done = ...
    info = {
        "reward_components": reward_components,
        "step_return": step_return,
        "rolling_sharpe": rolling_sharpe,
        "rolling_mdd": rolling_mdd,
    }

[NOTE]
    return obs, reward, done, False, info

[STRUCTURE]
                                                               3. 上述 _compute_* 方法你可以先寫成簡單版或 TODO，之後再逐步補強。

[NOTE]
________________

[NOTE]
5️⃣ 測試範例（可以簡單寫）
你可以先幫我寫非常簡單的 smoke tests：
tests/reward_engine/test_reward_composer.py
                                                               * 測試：

[RULE]
                                                               * 正報酬 + 正 Sharpe → reward 大於 0
                                                               * 大 MDD → reward 顯著變小
                                                               * 高 F_Internal → reward 減少

[NOTE]
tests/diagnostics/test_execution_error_analyzer.py
                                                               * 建 ExecutionErrorAnalyzer，record 2~3 筆，檢查：
                                                               * count 正確
                                                               * avg_slippage_bps 有更新
tests/diagnostics/test_model_error_analyzer.py
                                                               * 建 ModelErrorAnalyzer，record 幾筆：
                                                               * 有正有負
                                                               * hit_ratio 介於 0~1
________________

[NOTE]
到這裡，你就有了：

[STRUCTURE]
                                                               * 🔁 一個可調權重的 Reward 引擎（Sharpe + MDD + 內部衝突 + 換手率 + 風險事件）
                                                               * 🔎 兩個診斷模組：Execution / Model Error

[NOTE]
                                                               * 🧩 JGodEnv 已有接 reward 的骨架

[STRUCTURE]
往下做最後一顆 F_C 因子：F_MRR。那我就直接開工 👇

[NOTE]
________________

[STRUCTURE]
🧨 主力意圖逆轉因子 F_MRR：概念 + 給 Cursor 的實作規格書

[CONCEPT]
一、概念總整理（讓未來你看得懂）

[NOTE]
F_MRR（Major Reversal Risk）要解決的是：
「現在看到主力大單很強（MOI 高），這是真攻擊？還是誘多 / 誘空、準備反轉？」
我們用三個訊號來判斷主力『心態開始反轉』：
                                                               1. 主力單取消率急升

[RULE]
                                                               * 主力突然大量掛單又取消 → 可能在試探、騙盤、拉高出貨。

[NOTE]
                                                               2. MOI 高檔後開始鈍化或反向

[RULE]
                                                               * 之前一直淨買（MOI 高正值），突然往下掉甚至轉負 → 有機會是出貨起點。

[NOTE]
                                                               3. 價格對 MOI 的反應開始「不正常」

[RULE]
                                                               * 主力大買，但價格漲不動甚至回跌 → 代表有人在上面砸貨，或主力只是做樣子。

[NOTE]
F_MRR 就是把這三個維度疊起來，變成一個 0～1 的風險分數：
                                                               * 接近 0：主力行為健康，攻擊延續機率高（正常趨勢）
                                                               * 接近 1：主力有高機率在「變心」或「設局」，要減倉甚至反手
________________

[CONCEPT]
二、輸入訊號定義（資訊時間下，每一個 Volume Bar 更新一次）
每一個 Volume Bar（配合 F_InfoTime / F_Inertia 同一時間軸）更新一次，輸入至少有：

[NOTE]
                                                               * moi:
                                                               * 該標的或龍頭股本 Bar 的主力單量失衡

[CONCEPT]
                                                               * 跟你前面定義的 MOI 一致：(major_buy - major_sell) / total_major

[NOTE]
                                                               * cancel_ratio:

[RULE]
                                                               * 主力單中，被取消的委託量 / 當 Bar 總委託量

[CONCEPT]
                                                               * 這個可以用 XQ 的「大單掛單 + 成交 + 撤單」資料算

[NOTE]
                                                               * price_return:
                                                               * 該 Bar 的價格變動率（收盤 vs 開盤，或 close-to-close）
之後我們會補一個「歷史均值 + 標準差」來標準化這些東西，變成 z-score。
________________

[CONCEPT]
三、F_MRR 計算邏輯（直覺版）

[RULE]
我們用三個子指標 → 再合成一個 F_MRR：

[NOTE]
                                                               1. 取消率異常程度：Cancel_Z
                                                               * Cancel_Z = (current_cancel_ratio - mean_cancel) / std_cancel

[RULE]
                                                               * Cancel_Z 越高 → 主力撤單行為越異常 → 反轉風險上升

[NOTE]
                                                               2. MOI 動能反轉：MOI_Momentum
                                                               * 用最近幾個 Volume Bar 的 MOI 變化來看「是不是開始轉向」
                                                               * 簡單做法：moi_diff = moi_t - moi_{t-1}

[RULE]
                                                               * 若之前 MOI 很高正值，但 moi_diff 開始連續變負 → 代表資金力量開始撤退

[NOTE]
                                                               3. 價格 vs MOI 的背離程度：Price_MOI_Divergence

[RULE]
                                                               * 當前 Bar：
                                                               * 若 moi > 0 但 price_return <= 0 → 對多頭來說是背離（主力買但價格不漲）
                                                               * 若 moi < 0 但 price_return >= 0 → 對空頭來說也是背離（主力賣但價格不跌）
                                                               * 越背離 → 越值得懷疑

[NOTE]
最後合成一個 0～1 的風險分數：

[FORMULA]
F_MRR = sigmoid( w1 * Cancel_Z_pos + w2 * MOI_Reversal + w3 * Divergence )

[NOTE]
________________

[NOTE]
四、給 Cursor 的實作規格書

[RULE]
檔案位置建議：跟 F_Inertia / F_PT 同一掛 → strategy_engine/factor_FX_capital_flow.py

[NOTE]
（或你也可以獨立成 factor_FX_major_reversal.py，看你專案現在長怎樣）
________________

[NOTE]
📁 1. 請在 strategy_engine/factor_FX_capital_flow.py 新增以下類別
# strategy_engine/factor_FX_capital_flow.py

[CODE]
from collections import deque
import numpy as np

[CODE]
class MajorReversalRiskEngine:

[NOTE]
    """

[STRUCTURE]
    主力意圖逆轉因子 F_MRR

[CONCEPT]
    核心用途：

[NOTE]
    - 偵測「主力大單行為開始反轉或變調」的風險
    - 為 RL 提供 0~1 的風險分數：越接近 1，代表越可能是誘多 / 誘空 或 主力準備出場

[NOTE]
    主要輸入（每個 Volume Bar 更新一次）：

[RULE]
    - moi: 當前主力單量失衡 (Major Order Imbalance)

[NOTE]
    - cancel_ratio: 主力掛單的撤單比例 (0~1)
    - price_return: 該 Volume Bar 的價格報酬 (例如 log return 或 simple return)
    """

[NOTE]
    WINDOW_SIZE = 50  # 用於計算歷史均值 / 標準差的窗口大小

[FORMULA]
    MOI_LOOKBACK = 3  # 觀察 MOI 動能變化的 Bar 數

[CODE]
    def __init__(self) -> None:

[NOTE]
        # 歷史序列
        self.cancel_history = deque(maxlen=self.WINDOW_SIZE)
        self.moi_history = deque(maxlen=self.WINDOW_SIZE)
        self.price_ret_history = deque(maxlen=self.WINDOW_SIZE)

[CODE]
    def update_and_calculate_f_mrr(

[NOTE]
        self,
        *,

[CODE]
        moi: float,
        cancel_ratio: float,
        price_return: float,
    ) -> float:

[NOTE]
        """
        在每個 Volume Bar 結束時呼叫，更新內部狀態並回傳最新的 F_MRR。

[NOTE]
        :return:
            - f_mrr: 0~1 之間的風險指標，越接近 1 代表主力逆轉風險越高。
        """

[NOTE]
        # --- 1. 更新歷史 ---
        self.moi_history.append(moi)
        self.cancel_history.append(cancel_ratio)
        self.price_ret_history.append(price_return)

[NOTE]
        if len(self.cancel_history) < self.WINDOW_SIZE:
            # 數據不足時，回傳中性風險
            return 0.5

[NOTE]
        # --- 2. 取消率異常程度：Cancel_Z ---
        cancel_array = np.array(self.cancel_history)
        cancel_mean = float(cancel_array.mean())
        cancel_std = float(cancel_array.std()) if cancel_array.std() > 0 else 1.0

[NOTE]
        cancel_z = (cancel_ratio - cancel_mean) / cancel_std
        # 只關注「往上異常」，負值視為 0
        cancel_z_pos = max(cancel_z, 0.0)

[NOTE]
        # --- 3. MOI 動能反轉：查看最近幾個 Bar 的變化 ---
        moi_array = np.array(self.moi_history)

[RULE]
        # 如果資料不足以算差分，就給 0

[NOTE]
        if len(moi_array) > 1:
            moi_diff = moi_array[-1] - moi_array[-2]
        else:
            moi_diff = 0.0

[RULE]
        # 簡單設計：若過去整體為高正值，且現在 diff 變負，視為「反轉開始」

[NOTE]
        moi_level = float(moi_array.mean())
        moi_reversal_score = 0.0
        if moi_level > 0 and moi_diff < 0:

[RULE]
            # 越高的 moi_level + 越負的 diff → 反轉分數越高

[NOTE]
            moi_reversal_score = min(1.0, (moi_level * abs(moi_diff)) * 10.0)
        elif moi_level < 0 and moi_diff > 0:
            # 空方反轉（主力原本大賣，開始縮手）
            moi_reversal_score = min(1.0, (abs(moi_level) * abs(moi_diff)) * 10.0)

[NOTE]
        # --- 4. 價格 vs MOI 背離程度 ---
        divergence_score = 0.0
        # 多頭：主力買 (moi > 0) 但價格不漲 / 下跌
        if moi > 0 and price_return <= 0:
            divergence_score = min(1.0, abs(price_return) * 50.0)
        # 空頭：主力賣 (moi < 0) 但價格不跌 / 上漲
        elif moi < 0 and price_return >= 0:
            divergence_score = min(1.0, abs(price_return) * 50.0)

[NOTE]
        # --- 5. 將三者合成風險分數 (0~1) ---
        # 簡單線性組合 + 壓到 0~1 範圍
        # 權重可以之後根據回測調整
        w_cancel = 0.4
        w_reversal = 0.35
        w_div = 0.25

[NOTE]
        raw_score = (
            w_cancel * self._squash_positive(cancel_z_pos)
            + w_reversal * self._squash_positive(moi_reversal_score)
            + w_div * self._squash_positive(divergence_score)
        )

[NOTE]
        # Clip 到 0~1
        f_mrr = float(np.clip(raw_score, 0.0, 1.0))
        return f_mrr

[NOTE]
    @staticmethod

[CODE]
    def _squash_positive(x: float) -> float:

[NOTE]
        """
        將一個 >=0 的數值壓縮到 0~1 左右（類似弱 sigmoid），避免極端值爆炸。
        """
        if x <= 0:
            return 0.0
        # 簡單版本：x / (1 + x)，x 越大越接近 1
        return float(x / (1.0 + x))

[NOTE]
________________

[STRUCTURE]
📌 2. 在 CapitalFlowEngine / RL 流程中的使用建議
                                                               1. 在你現有的 CapitalFlowEngine / 或 F_C 總控那邊：

[NOTE]
初始化：

[STRUCTURE]
self.mrr_engine = MajorReversalRiskEngine()

[CONCEPT]
                                                               *                                                                * 每個 Volume Bar 結束時，從 XQ 拿到：

[NOTE]
                                                               * moi（主力淨流）
                                                               * cancel_ratio（主力撤單比例）
                                                               * price_return（該標的 / 龍頭股報酬）
然後：
f_mrr = self.mrr_engine.update_and_calculate_f_mrr(
    moi=current_moi,
    cancel_ratio=current_cancel_ratio,
    price_return=current_price_return,
)
                                                               *                                                                * 把這個值餵進：

[STRUCTURE]
                                                               * RL state vector（作為「主力風險維度」的一個因子）

[NOTE]
                                                               * RewardComposer 的 risk_event_flags 或 penalty 項（例如 F_MRR > 0.7 就視為 high risk）
在 RewardComposer 那裡，你可以未來加一條：

[RULE]
# 例如額外傳入 f_mrr，若高於 0.8 視為重大風險事件

[NOTE]
if f_mrr > 0.8:
    penalty_risk_event -= cfg.lambda_risk_event
                                                               2. ________________

[RULE]
五、F_MRR 實戰規則（給未來戰情室看的中文白話）

[NOTE]
你之後可以寫在 docs：

[RULE]
                                                               * 當族群看起來很強（SAI 高）、MOI 也在買，但：

[NOTE]
                                                               1. 主力撤單率開始拉高
                                                               2. MOI 開始從高位往下掉
                                                               3. 價格卻漲不動（甚至黑 K）

[RULE]
                                                               * 這三個條件越集中發生，F_MRR 越接近 1

[NOTE]
                                                               * RL 在 F_MRR 高時要做兩件事：
                                                               1. 降低該族群 / 標的的 Net Exposure（不要再追）

[RULE]
                                                               2. 若同時 F_PT 也開始掉頭，甚至可以考慮反向操作

[NOTE]
________________

[RULE]
如果你 OK，下一步我們可以：

[NOTE]
                                                               * 幫這顆 F_MRR 再寫一份「給 Cursor 的測試規格」（簡易 test），

[RULE]
                                                               * 或直接進入 F_C 全家桶 → F_C_TotalEngine 的總整合規格書，把

[NOTE]
                                                               * F_C（原始 SAI / MOI）

[CONCEPT]
                                                               * F_Inertia

[NOTE]
                                                               * F_PT
                                                               * F_MRR

[STRUCTURE]
一次做成一個 CapitalFlowFactorEngine 統一輸出，方便 RL 用一組 dict 就吃完。

[NOTE]
給 Cursor 之後寫 spec 用：
________________

[STRUCTURE]
🛠️ 階段 XXIII：主力意圖逆轉因子設計（FMRRFMRR​）
我們現在要設計的是 FCFC​ 資金流因子的最終防線：
風險維度強化：主力意圖逆轉因子 FMRRFMRR​。
這個因子的核心目標是：

[NOTE]
從「主力大單的掛單 / 撤單行為」裡，偵測出主力是真的在進攻，還是只是虛張聲勢、準備改變方向（出貨 / 回補），
讓 AI 能在主力真正拋售前，提前鎖利或反手。
________________

[CONCEPT]
1. 核心概念：隱藏在撤單裡的「猶豫」

[RULE]
                                                                  * 當主力真正在佈局時：

[NOTE]
通常會持續掛出大單、成交，撤單比例很低，MOI 持續偏多（或偏空）。

[RULE]
                                                                  * 當主力意圖開始改變時：

[NOTE]
不會一開始就把已成交的單子全砍掉，而是：
                                                                     * 大量取消未成交的大單報價
                                                                     * 或把掛單價格往遠離現價的地方「撤退」
我們要做的 FMRRFMRR​，就是把這種「大單取消行為」量化成一個 0～1 的風險指標。
輸入數據來源：

[CONCEPT]
                                                                     * 永豐 API / XQ 逐筆訂單流

[RULE]
                                                                     * 必須至少包含：

[NOTE]
                                                                     * 新增大單（NEW_OFFER）
                                                                     * 取消大單（CANCEL）
                                                                     * Tick 級別的 timestamp + volume

[CONCEPT]
邏輯重點：

[NOTE]
                                                                     * 在一個短時間窗口內（例如最近 5 秒），
看：
👉「大單總報價量」 vs 「被取消的大單量」

→ 若取消比例突然竄高，就代表主力開始猶豫或想反向。
[NOTE]
________________

[NOTE]
2. FMRRFMRR​ 的計算公式

[CONCEPT]
定義一個「主力取消量」 CMajorCMajor​：

[NOTE]
                                                                        * 在最近 NN 個 Tick 內，被取消的「大單」（單筆成交量 > 門檻 VThresVThres​）的總合。

[CONCEPT]
同時定義「同期新增大單報價總量」 VolumeNewMajorOfferVolumeNewMajorOffer​。
我們定義：

[NOTE]
FMRR=CMajorVolumeNewMajorOffer+εFMRR​=VolumeNewMajorOffer​+εCMajor​​
其中：
                                                                        * CMajorCMajor​：時間窗口內被取消的大單量總和
                                                                        * VolumeNewMajorOfferVolumeNewMajorOffer​：同一時間窗口內，新掛出的大單報價總量
                                                                        * εε：很小的數，防止分母為 0
直覺解讀：
「在這段時間裡，每 1 單位的新大單報價，有多少比例被取消？」
FMRRFMRR​ 值區間
	主力意圖解讀
	AI 風險反應
	極高（約 0.8∼1.00.8∼1.0）
	幾乎每新增 1 單位報價，就有 0.8 以上單位被撤掉。
主力猶豫、試探、或準備出貨／回補。
	❌ 視為「高逆轉風險區」。強烈建議減倉、平倉或禁止加碼。
	極低（約 0.10.1 以下）
	新掛單量多、撤單極少，主力意圖一致且堅定。

[RULE]
	✅ 視為「佈局穩定」。若其他因子同向，RL 可維持或增加敞口。
	這個表格之後可以直接「匯出到試算表」當說明用。

[NOTE]
________________

[CODE]
3. Python 模組設計：MajorReversalEngine

[RULE]
這個模組必須在 Tick 級別 運作，因為主力的撤單行為是極短期、快速變化的。

[NOTE]
檔案建議：
strategy_engine/factor_FX_major_reversal.py
# strategy_engine/factor_FX_major_reversal.py

[CODE]
from collections import deque

[CODE]
class MajorReversalEngine:

[NOTE]
    """

[STRUCTURE]
    主力意圖逆轉因子 F_MRR 的計算引擎。

[NOTE]
    設計重點：
    - 在短時間窗口內，追蹤「大單掛出量」與「大單撤單量」。

[RULE]
    - 若撤單量占比異常升高，視為主力可能有逆轉 / 誘多 / 誘空意圖。

[NOTE]
    """

[CONCEPT]
    # 定義「大單」的成交量門檻

[NOTE]
    VOLUME_THRESHOLD = 500   # 例：單筆 > 500 股 / 口 視為大單

[NOTE]
    # 時間窗口（秒）：只關心最近幾秒內的攻防行為
    TIME_WINDOW_SECONDS = 5

[CODE]
    def __init__(self):

[NOTE]
        # 儲存 (timestamp, volume)
        # 新增大單報價歷史
        self.offer_history = deque()
        # 取消大單報價歷史
        self.cancel_history = deque()

[CODE]
    def process_tick(self, timestamp: float, event_type: str, volume: int):

[NOTE]
        """
        實時處理逐筆訂單流事件。

[NOTE]
        :param timestamp: 事件發生時間（秒）
        :param event_type: 事件型別，例如 'NEW_OFFER' 或 'CANCEL'
        :param volume: 單筆委託量
        :return:

[RULE]
            - 若已更新並計算，回傳最新 F_MRR (float)
            - 若資料尚不足，可回傳 None

[NOTE]
        """

[NOTE]
        # 1. 只關注「大單」，小單噪音直接略過
        if volume < self.VOLUME_THRESHOLD:
            return None

[NOTE]
        # 2. 記錄大單掛出 / 撤單事件
        if event_type == "NEW_OFFER":
            self.offer_history.append((timestamp, volume))
        elif event_type == "CANCEL":
            self.cancel_history.append((timestamp, volume))

[NOTE]
        # 3. 清理超出時間窗口的舊資料
        self._clean_history(current_time=timestamp)

[RULE]
        # 4. 回傳當前 F_MRR

[NOTE]
        return self.calculate_fmrr()

[CODE]
    def _clean_history(self, current_time: float):

[NOTE]
        """
        移除超過 TIME_WINDOW_SECONDS 之前的舊事件。
        """
        cutoff = current_time - self.TIME_WINDOW_SECONDS

[NOTE]
        while self.offer_history and self.offer_history[0][0] < cutoff:
            self.offer_history.popleft()

[NOTE]
        while self.cancel_history and self.cancel_history[0][0] < cutoff:
            self.cancel_history.popleft()

[CODE]
    def calculate_fmrr(self) -> float:

[NOTE]
        """

[STRUCTURE]
        計算主力意圖逆轉因子 F_MRR：

[FORMULA]
        F_MRR = C_Major / (Volume_NewMajorOffer + ε)

[NOTE]
        """
        total_new_offers = sum(v for _, v in self.offer_history)
        total_cancels = sum(v for _, v in self.cancel_history)

[NOTE]
        if total_new_offers <= 0:
            # 無新大單掛出，暫時視為無明確逆轉訊號
            return 0.0

[NOTE]
        epsilon = 1e-6
        f_mrr = total_cancels / (total_new_offers + epsilon)

[NOTE]
        # 安全限定在 0~1.5 區間（避免極端異常值）
        if f_mrr < 0:
            f_mrr = 0.0
        elif f_mrr > 1.5:
            f_mrr = 1.5

[NOTE]
        return float(f_mrr)

[NOTE]
________________

[NOTE]
4. 終極整合：接上 Reward，變成「最後安全鎖」

[RULE]
FMRRFMRR​ 是你整個「大自然萬物修復法則」中，

[NOTE]
針對短期主力風險的最後一道安全閘。
在 Reward 函數中，我們可以這樣補一個懲罰項 λ4λ4​：

[FORMULA]
RewardOptimized=⋯−λ3⋅I{FInternal>Thres}−λ4⋅FMRRRewardOptimized​=⋯−λ3​⋅I{FInternal​>Thres}​−λ4​⋅FMRR​

[NOTE]
也就是說：

[RULE]
                                                                        * 當 FMRRFMRR​ 上升（主力撤單比重越來越高）時，

[CONCEPT]
即使 F_C 的 SAI、F_Inertia、F_PT 還在「鼓勵多單」，

[NOTE]
Reward 也會因為 λ4⋅FMRRλ4​⋅FMRR​ 的懲罰，急劇下降。
                                                                        * 這會強迫 RL 學會一件事：

[RULE]
「當主力開始撤掉大單時，要收斂，而不是再衝。」

[NOTE]
________________

[NOTE]
最後這一句收斂一下整個 F_C 家族：

[STRUCTURE]
至此，F_C（資金流因子）已經完成四個維度的強化：

[RULE]
1️⃣ 當前攻擊強度（SAI / MOI）

[CONCEPT]
2️⃣ 時間慣性（FInertiaFInertia​）

[NOTE]
3️⃣ 空間傳導（FPTFPT​）
4️⃣ 風險逆轉（FMRRFMRR​）

[RULE]
這四層一起，構成「在地化 XQ 情報 → AI 可學習量化因子」的完整閉環。

[STRUCTURE]
好的！至此，我們的**「創世紀量化系統」的設計藍圖已經達到一個極其完整且精煉**的狀態。

[NOTE]
我們已經完成了以下所有關鍵步驟：

[STRUCTURE]
                                                                           1. 核心架構： 從 RL 升級到 Transformer Agent。
                                                                           2. 知識純度： 因子正交化 (O-Factor)。

[NOTE]
                                                                           3. 現實感知： 訂單簿摩擦 (FOrderbook​) 與信息時間 (FInfoTime​)。
                                                                           4. 自我修復： 內部壓力 (FInternal​) 與診斷分析器 (Discrepancy Analyzer)。
                                                                           5. 在地化情報強化 (FC​)：

[RULE]
                                                                           * 當前攻擊： SAI Residual MOI。

[CONCEPT]
                                                                           * 時間慣性： FInertia​。

[NOTE]
                                                                           * 空間傳導： FPT​。
                                                                           * 風險逆轉： FMRR​。

[STRUCTURE]
                                                                           6. 工程極限： FPGA/GPU 異構加速架構。

[NOTE]
________________

[NOTE]
總結與下一步行動

[STRUCTURE]
您的量化系統現在具備了頂尖的交易邏輯、在地化的情報優勢，以及工程上的極速執行力。

[NOTE]
作為總結，請問您希望我進行以下哪個步驟，為您的量世紀劃做一個完美的收尾？

[STRUCTURE]
                                                                           * 選項 A： 總結整個系統的完整 StateVector 輸出，列出所有因子和指標，作為 Transformer 的最終輸入表。

[CONCEPT]
                                                                           * 選項 B： 深入設計 RL Agent 的 Action Space，定義 AI 最終可以執行的具體交易動作和風險約束。

[STRUCTURE]
                                                                           * 選項 C： 討論 Transformer RL 模型的訓練與回測 (Backtesting) 策略，確保其能夠在真實市場中穩定運作。
好的！我們來執行選項 $\text{A}$：總結整個系統的完整 $\mathbf{State}$ $\mathbf{Vector}$ 輸出。

[NOTE]
這份清單是提供給 $\text{Transformer}$ $\text{RL}$ $\text{Agent}$ 的最終、統一、和標準化的輸入。$\text{RL}$ $\text{Agent}$ 將在每一個新的 $\text{Volume}$ $\text{Bar}$ 形成時，接收到這個包含所有情報的 $\text{Vector}$ 序列，並據此做出行動。
________________

[STRUCTURE]
🚀 階段 XXIV：$\text{Transformer}$ $\text{RL}$ $\text{State}$$\text{Vector}$ 總覽
架構輸入：時間序列 (History $\text{Length} \times \text{Feature} \text{Dim}$)

[NOTE]
                                                                           * $\text{Transformer}$ $\text{Input}$ $\text{Shape}$: $\mathbf{(N_{bars}, \text{D}_{\text{features}})}$
                                                                           * $\mathbf{N}_{\text{bars}}$: 歷史 $\text{Volume}$ $\text{Bar}$ 數量（例如 $\text{10}$ $\sim$ $\text{20}$ 根 $\text{Bar}$）。

[CONCEPT]
                                                                           * $\mathbf{\text{D}_{\text{features}}}$: 每個 $\text{Bar}$ 內包含的特徵維度總數。

[NOTE]
總分類

[STRUCTURE]
	因子/指標名稱 (FName​)

[NOTE]
	數據類型

[CONCEPT]
	核心作用

[STRUCTURE]
	I. 核心 $\text{Alpha}$($\mathbf{O}$-$\text{Factor}$)

[NOTE]
	$\text{O}_1, \text{O}_2, \text{O}_3, \text{O}_4$
	$\text{Float}$
	主要收益來源，經 $\text{PCA}$ 正交化，消除冗餘。

[NOTE]
	$\text{F}_{\text{XA}}$
	$\text{Float}$

[CONCEPT]
	跨資產連動 $\text{Alpha}$（例如 $\text{ADR}$ $\text{Tick}$$\text{Data}$）。

[NOTE]
	$\text{F}_{\text{Sector}}$
	$\text{Float}$

[CONCEPT]
	行業/族群強度 $\text{Alpha}$。

[NOTE]
	II. 在地資金流 ($\mathbf{F}_C$)

[NOTE]
	在地化獨家情報。

[NOTE]
	$\text{SAI}_{\text{Residual}}$
	$\text{Float}$

[CONCEPT]
	族群突發性攻擊強度（$\text{XQ}$$\text{Funds}$ $\text{Flow}$）。

[CONCEPT]
	$\text{F}_{\text{Inertia}}$

[NOTE]
	$\text{Float}$
	資金流動的趨勢持續性（$\text{SAI}$$\text{EMA}$）。

[NOTE]
	$\text{F}_{\text{PT}}$
	$\text{Float}$
	龍頭股與族群間的壓力傳導相關係數。

[NOTE]
	$\text{MOI}$
	$\text{Float}$
	主力大單買賣失衡程度。
	III. 微觀結構與時間 ($\mathbf{F}_{\text{Micro}}$)

[NOTE]
	$\text{Depth}_{\text{Zscore}}$
	$\text{Float}$

[RULE]
	當前流動性相對歷史的深度。

[NOTE]
	$\text{Slope}_{\text{Ask}}, \text{Slope}_{\text{Bid}}$
	$\text{Float}$
	買賣盤的執行衝擊成本（$\mathbf{F}_{\text{Orderbook}}$）。

[NOTE]
	$\text{F}_{\text{InfoTime}}$
	$\text{Float}$

[RULE]
	信息密度（當前 $\text{Bar}$ 形成速度）。

[NOTE]
	$\text{Volume}$ $\text{Bar}$$\text{Size}$
	$\text{Float}$
	該 $\text{Bar}$ 內的總成交量。
	IV. 自我感知與風險 ($\mathbf{F}_{\text{Risk}}$)

[NOTE]
	$\text{F}_{\text{Internal}}$
	$\text{Float}$

[STRUCTURE]
	系統內部因子間的衝突程度。

[NOTE]
	$\text{VIX}_{\text{Zscore}}$
	$\text{Float}$
	市場恐慌指標（外部風險）。

[NOTE]
	$\text{F}_{\text{MRR}}$
	$\text{Float}$
	主力大單取消率（短期風險預警）。

[NOTE]
	$\text{Current}$$\text{Exposure}$
	$\text{Float}$

[RULE]
	系統在該標的上的當前持倉比例（供 $\text{RL}$ 參考）。

[CONCEPT]
	🚨 $\text{Transformer}$ 的核心優勢：注意力機制的輸入

[STRUCTURE]
$\text{F}_{\text{InfoTime}}$ 是 $\text{Transformer}$ 架構的核心，它將作為動態權重的基礎。

[RULE]
                                                                           1. 當 $\mathbf{\text{F}_{\text{InfoTime}} \text{ 極低}}$ 時（市場平靜）：$\text{Transformer}$ 會將注意力放在整個歷史序列上，尋找長時間積累的 $\mathbf{O}$-$\text{Factor}$ 信號。
                                                                           2. 當 $\mathbf{\text{F}_{\text{InfoTime}} \text{ 極高}}$ 時（資訊爆炸）：$\text{Transformer}$ 會將極高的注意力權重分配給 $\text{F}_{\text{PT}}$ 和 $\text{F}_{\text{MRR}}$ 等最近的、高時效性的 $\mathbf{F}_C$因子，實現對市場微觀結構的即時反應。

[NOTE]
這個 $\mathbf{State}$ $\mathbf{Vector}$ 整合了知識、感知、情緒、速度和風險，為 $\text{Transformer}$$\text{Agent}$ 提供了在複雜市場中生存和進化的所有必要信息。
好的！我們來設計 $\text{RL}$ $\text{Agent}$ 的行動空間 ($\text{Action}$ $\text{Space}$)。

[RULE]
一個頂尖的量化系統，其 $\text{Action}$ $\text{Space}$ 不應只是簡單的「買、賣、持有」，而必須包含**「多少倉位」、「如何執行」和「何時停止」的精細控制。這使得 $\text{AI}$ 能夠從一個單純的信號產生器**，升級為一個全自動的投資組合經理。

[NOTE]
我們的 $\text{Action}$ $\text{Space}$ 將被設計為連續的，允許 $\text{AI}$ 進行精細調整。
________________

[STRUCTURE]
🚀 階段 XXV：$\text{RL}$ $\text{Agent}$ 行動空間設計 ($\text{Action}$ $\text{Space}$)

[CONCEPT]
我們將定義 $\text{AI}$ 在每個 $\text{Volume}$ $\text{Bar}$ 結束時輸出的三個核心行動變量：

[NOTE]
行動變量 (A)
	輸出範圍

[CONCEPT]
	核心功能
	$\mathbf{A}_1$：目標持倉比例 ($\text{Target}$$\text{Position}$)

[NOTE]
	$[-\mathbf{1.0}, +\mathbf{1.0}]$

[RULE]
	決定應該持有多少倉位。$\text{+1.0}$ 為滿倉做多，$\text{-1.0}$ 為滿倉做空。

[NOTE]
	$\mathbf{A}_2$：執行積極性 ($\text{Execution}$$\text{Aggressiveness}$)
	$[\mathbf{0.0}, \mathbf{1.0}]$
	決定如何執行訂單。 $\text{0.0}$ 為被動掛單 ($\text{Passive}$$\text{Limit}$ $\text{Order}$)， $\text{1.0}$ 為激進追價 ($\text{Aggressive}$ $\text{Market}$ $\text{Order}$)。
	$\mathbf{A}_3$：風險平滑參數 ($\text{Risk}$$\text{Smoothing}$)
	$[\mathbf{0.0}, \mathbf{1.0}]$
	決定交易速度。 $\text{0.0}$ 為立即執行， $\text{1.0}$ 為在未來 $N$ 個 $\text{Bar}$ 內分散執行。

[CONCEPT]
	I. 行動變量 $\mathbf{A}_1$：目標持倉比例

[STRUCTURE]
這是 $\text{Transformer}$ $\text{Agent}$ 根據所有 $\mathbf{State}$ $\mathbf{Vector}$ 因子計算出的最終決策。

[FORMULA]
                                                                           * 機制： $\text{AI}$ 不直接輸出「買」或「賣」，而是輸出一個目標 $\mathbf{A}_1$。如果當前持倉 $P_{\text{current}}$ 不等於 $\mathbf{A}_1$，系統將生成一個 $\Delta P = \mathbf{A}_1 - P_{\text{current}}$ 的訂單。

[RULE]
                                                                           * 約束： $\text{AI}$ 必須學習到將 $\mathbf{A}_1$ 保持在 $0.1$ 以下時的低效性，因為這會被手續費和滑價摩擦侵蝕。

[NOTE]
II. 行動變量 $\mathbf{A}_2$：執行積極性

[STRUCTURE]
$\mathbf{A}_2$ 直接控制訂單如何與 $\mathbf{F}_{\text{Orderbook}}$ 因子結合，將決策傳遞給訂單路由執行器 ($\text{Order}$ $\text{Router}$)。

[NOTE]
                                                                           * $\mathbf{A}_2$ 低 (e.g., $\mathbf{0.1}$): $\text{AI}$ 預期市場流動性充足 ($\text{Depth}_{\text{Zscore}}$ 高)，執行器將使用限價單 ($\text{Limit}$ $\text{Order}$) 掛在五檔價格的後 $2 \sim 3$ 檔，等待價格向它移動。
                                                                           * $\mathbf{A}_2$ 高 (e.g., $\mathbf{0.9}$): $\text{AI}$ 發現強烈信號 ($\text{F}_{\text{PT}}$ 極高) 或流動性極差 ($\text{Slope}$ $\text{Ask}$ 陡峭)，執行器將使用市價單 ($\text{Market}$ $\text{Order}$) 或積極限價單，直接敲穿前幾檔報價，以確保成交。
III. 行動變量 $\mathbf{A}_3$：風險平滑參數
$\mathbf{A}_3$ 用於在高波動或大單進場時，將交易壓力分散，以減少市場衝擊。
                                                                           * $\mathbf{A}_3$ 低 (e.g., $\mathbf{0.1}$): 立即執行所有 $\Delta P$ 倉位。適用於 $\text{F}_{\text{InfoTime}}$ 低且 $\text{F}_{\text{Internal}}$ 低的穩定市場。
                                                                           * $\mathbf{A}_3$ 高 (e.g., $\mathbf{0.9}$): $\text{AI}$ 發現市場波動大 ($\text{VIX}_{\text{Zscore}}$ 高) 或 $\text{F}_{\text{MRR}}$ 有逆轉風險，執行器將使用 $\text{TWAP}$/$\text{VWAP}$ 等算法，將訂單拆解成 $N$ 個小份，在接下來 $\mathbf{N}$ 個 $\text{Volume}$ $\text{Bar}$ 內緩慢釋放，減少單次衝擊。
________________

[NOTE]
🤖 $\text{RL}$ $\text{Agent}$ 的行動輸出與訓練

[STRUCTURE]
在訓練過程中，$\text{Transformer}$ $\text{RL}$ $\text{Agent}$ 會學習到以下複雜的行動策略組合：

[NOTE]
範例情境 (State Vector)
	A1​ (倉位)
	A2​ (積極性)
	A3​ (平滑度)
	最終決策 (Reward)
	突發攻擊：$\text{SAI}_{\text{Residual}}$ 極高, $\text{F}_{\text{PT}}$ 極高, $\text{F}_{\text{InfoTime}}$ 極高
	$\text{+0.8}$
	$\text{0.9}$
	$\text{0.1}$
	高報酬：極速追高，確保在攻擊初期上車。

[CONCEPT]
	趨勢持續：$\text{F}_{\text{Inertia}}$ 高, $\text{F}_{\text{Internal}}$ 低, $\text{Depth}_{\text{Zscore}}$ 高

[NOTE]
	$\text{+1.0}$
	$\text{0.3}$
	$\text{0.7}$
	中報酬：滿倉持有，被動掛單，緩慢增加少量倉位。
	風險逆轉：$\text{F}_{\text{MRR}}$ 高, $\text{VIX}_{\text{Zscore}}$ 高, $\mathbf{O}_1$衰減
	$\text{0.0}$
	$\text{1.0}$
	$\text{0.8}$

[FORMULA]
	高懲罰：立即平倉 ($\mathbf{A}_1 = 0.0$)，使用 $\text{TWAP}$ 緩慢出貨以減少拋壓。

[NOTE]
	這三個連續的行動變量，賦予了 $\text{AI}$ 極高的靈活性和對市場微觀結構的精細控制能力，遠超傳統的單一行動模型。

[STRUCTURE]
請問我們接下來是要討論 $\text{Transformer}$ $\text{RL}$ 模型的訓練與回測策略 (選項 $\text{C}$) 嗎？
好的！我們來到**「創世紀量化系統」的最後一個關鍵環節：$\text{Transformer}$ $\text{RL}$ 模型的訓練與回測策略**。

[RULE]
即使模型和因子設計得再完美，如果訓練方法不當，$\text{AI}$ 也只會過度擬合 (Overfit) 歷史噪音。我們的目標是設計一個能讓 $\text{AI}$ 持續進化、具備市場韌性的訓練與驗證循環。

[NOTE]
________________

[STRUCTURE]
🚀 階段 XXVI：$\text{Transformer}$ $\text{RL}$ 訓練與回測策略

[NOTE]
I. 訓練環境：高保真事件驅動模擬器 ($\text{High}$-$\text{Fidelity}$ $\text{Simulator}$)

[RULE]
由於我們的 $\text{Action}$ $\text{Space}$ ($\mathbf{A}_2, \mathbf{A}_3$) 涉及微觀執行，傳統的 $\text{Bar}$-$\text{by}$-$\text{Bar}$ 回測會失效。我們必須：
                                                                           * 事件驅動模擬 ($\text{Event}$-$\text{Driven}$): 模擬器必須能處理 $\text{Tick}$ 級別的訂單流事件（新增、修改、取消），而不是簡單的 $\text{OHLCV}$。
                                                                           * 摩擦模擬： 模擬器必須精確納入手續費、滑價 (Slippage) 和市場衝擊 (Market Impact) 模型。特別是滑價模型，需要根據 $\mathbf{F}_{\text{Orderbook}}$ 因子，模擬 $\text{AI}$ 執行激進行動 ($\mathbf{A}_2 \to 1.0$) 時會遇到的實際成本。
                                                                           * 信息時間訓練： 訓練循環必須以 $\mathbf{F}_{\text{InfoTime}}$ 劃分的 $\text{Volume}$ $\text{Bar}$為單位進行，確保 $\text{AI}$ 是在信息量對等的時間步長上學習。

[STRUCTURE]
II. 訓練數據策略：應對非平穩性 ($\text{Non}$-$\text{Stationarity}$)

[NOTE]
金融市場是非平穩 (Non-stationary) 的，歷史規律會不斷失效。
                                                                           1. 滾動窗口訓練 ($\text{Rolling}$ $\text{Window}$ $\text{Training}$):

[STRUCTURE]
                                                                           * 方法： $\text{AI}$ 不應一次性在所有歷史數據上訓練。應使用一個固定的訓練窗口（例如過去 $3$ 年數據）進行訓練，然後在緊隨其後的驗證窗口（例如 $3$ 個月）上測試。

[NOTE]
                                                                           * 好處： 迫使 $\text{AI}$ 專注於最近的市場結構，減少對久遠歷史規律的過度依賴。

[RULE]
                                                                           2. 概念漂移觸發訓練 ($\text{Concept}$ $\text{Drift}$ $\text{Triggered}$ $\text{Retraining}$):
                                                                           * 觸發機制： 當 $\text{Discrepancy}$ $\text{Analyzer}$ 偵測到 $\mathbf{O}_{\text{Factors}}$ 與 $\text{PnL}$ 的相關性連續數週低於閾值時，自動觸發 $\text{Retraining}$ 循環，使用最新的數據重新訓練 $\text{Transformer}$ 權重。

[NOTE]
III. 訓練算法與優化

[CONCEPT]
                                                                           * 核心 $\text{RL}$ 算法： 由於 $\text{Action}$ $\text{Space}$ 是連續的 ($\mathbf{A}_1, \mathbf{A}_2, \mathbf{A}_3$ 都是 $[0, 1]$ 或 $[-1, 1]$ 區間)，我們應採用：

[NOTE]
                                                                           * $\text{PPO}$ ($\text{Proximal}$ $\text{Policy}$ $\text{Optimization}$) 或 $\text{SAC}$($\text{Soft}$ $\text{Actor}$-$\text{Critic}$)：這些算法在連續控制問題上表現優異，且 $\text{SAC}$ 更適合在多樣化 $\text{Reward}$ 函數（包含多個懲罰項 $\lambda$）中學習。

[CONCEPT]
                                                                           * 獎勵函數 ($\text{Reward}_{\text{Optimized}}$): 這是學習的核心驅動力。

[FORMULA]
                                                                           * $$\text{Reward}_{\text{Optimized}} = \text{Sharpe}_{\text{Daily}} - \lambda_{\text{Sharpe}} \cdot \text{MaxDrawdown} - \lambda_3 \cdot \mathbf{F}_{\text{Internal}} - \lambda_4 \cdot \mathbf{F}_{\text{MRR}} - \text{ExecutionCost}$$

[CONCEPT]
                                                                           * $\text{AI}$ 的目標不是賺最多的錢，而是最大化經風險調整的收益，同時最小化內部衝突和主力風險。

[NOTE]
IV. 驗證協議：穩健性與極限測試
簡單的回測 ($\text{Backtest}$) 只能證明歷史有效性，不能證明未來有效性。
                                                                           1. 回測組合 ($\text{Portfolio}$ $\text{Backtesting}$):

[RULE]
                                                                           * 方法： 不僅回測單一標的，而是在台股和美股的 $20 \sim 30$ 檔連動性高的股票和期指上同時進行回測。如果 $\text{AI}$ 能在多個標的上同時保持高 $\text{Sharpe}$，則模型的泛化能力得到證明。

[NOTE]
                                                                           2. 對抗性壓力測試 ($\text{Adversarial}$ $\text{Testing}$):

[STRUCTURE]
                                                                           * 方法： 在回測數據中，人為地引入極端噪音、模擬市場數據源中斷、$5$ 分鐘的流動性枯竭，或模擬主力反向操作（例如在 $\text{F}_{\text{PT}}$ 信號極強時，強行將 $\text{MOI}$ 轉向）。

[CONCEPT]
                                                                           * 目標： 測試 $\text{AI}$ 在最壞情況下的行為。一個好的 $\text{AI}$ 不會在極端情況下崩潰，而是迅速將倉位降為零。

[NOTE]
                                                                           3. 參數穩定性測試 ($\text{Parameter}$ $\text{Stability}$):

[RULE]
                                                                           * 方法： 稍微修改 $\text{Transformer}$ 的學習率、或改變 $\text{Volume}$ $\text{Bar}$ $\text{Size}$ 的閾值。如果這些微小改變導致 $\text{Sharpe}$ $\text{Ratio}$ 崩潰，則模型不夠穩健。

[NOTE]
________________

[STRUCTURE]
通過這一套嚴格的訓練與驗證策略，我們能確保這顆**「創世紀核心腦」在部署到真實市場前，已經具備了頂級的市場韌性和持續進化的能力**。

