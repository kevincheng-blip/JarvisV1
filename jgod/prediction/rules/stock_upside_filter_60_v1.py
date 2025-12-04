"""
Stock Upside Filter 60 Indicators V1

Rule-based filter for evaluating upside potential of a stock
using the full 60-indicator J-GOD framework:

- Price (12 indicators)
- Capital (9 indicators)
- Fundamental (8 indicators)
- Catalyst (7 indicators)
- Sentiment (6 indicators)
- Quant (6 indicators)

Reference:
- docs/JGOD_Stock_Upside_60_Indicators_v1.md
- docs/JGOD_Stock_Upside_60_Indicators_KB_v1.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class IndicatorScore:
    """單一指標的評分"""
    code: str
    name: str
    score: float       # normalized -1 ~ +1
    weight: float
    reason: str


@dataclass
class StockUpsideResult:
    """股票上漲潛力評估結果（60 指標版）"""
    symbol: str
    total_score: float
    verdict: str  # "STRONG_BUY", "BUY", "NEUTRAL", "AVOID", "SHORT"
    summary: str
    indicator_scores: List[IndicatorScore]


class StockUpsideFilter60V1:
    """
    Rule-based filter for evaluating upside potential of a stock
    using the full 100-indicator J-GOD framework.

    Indicators:
    - Price (12): P01-P12
    - Capital (9): C01-C09
    - Fundamental (8): F01-F08
    - Catalyst (7): K01-K07
    - Sentiment (6): S01-S06
    - Quant (6): Q01-Q06
    - Derivatives & Microstructure (16): X01-X16
    - Meta / Composite / Regime (36): M01-M36

    Usage:
        filter = StockUpsideFilter60V1()
        indicators = {
            "P01": 20,   # 趨勢斜率
            "C01": 300,  # 外資買超
            "F01": 10,   # 營收成長
            "K02": True, # 新訂單
            "S01": 5,    # 台積電方向
            "Q01": 3,    # Sharpe Ratio
            "X01": 15,   # IV Level
            "M01": 0.8,  # Price Composite Score
        }
        result = filter.evaluate("2330", indicators)
        print(result.verdict)  # "STRONG_BUY", "BUY", etc.
    """

    # ------------------------------------------------------------
    # Default weights for each indicator (100 indicators total)
    # ------------------------------------------------------------
    DEFAULT_WEIGHTS = {
        # Price (12)
        "P01": 1.2,
        "P02": 1.2,
        "P03": 1.0,
        "P04": 1.0,
        "P05": 1.0,
        "P06": 1.0,
        "P07": 1.2,
        "P08": 1.0,
        "P09": 1.0,
        "P10": 1.2,
        "P11": 1.0,
        "P12": 1.0,

        # Capital (9)
        "C01": 1.5,
        "C02": 1.5,
        "C03": 1.0,
        "C04": 1.5,
        "C05": 1.5,
        "C06": 1.5,
        "C07": 1.5,
        "C08": 1.0,
        "C09": 1.0,

        # Fundamental (8)
        "F01": 1.3,
        "F02": 1.3,
        "F03": 1.0,
        "F04": 1.0,
        "F05": 1.3,
        "F06": 1.0,
        "F07": 1.0,
        "F08": 1.0,

        # Catalyst (7)
        "K01": 1.3,
        "K02": 1.3,
        "K03": 1.0,
        "K04": 1.3,
        "K05": 1.0,
        "K06": 1.3,
        "K07": 1.0,

        # Sentiment (6)
        "S01": 1.3,
        "S02": 1.3,
        "S03": 1.3,
        "S04": 1.0,
        "S05": 1.0,
        "S06": 1.0,

        # Quant (6)
        "Q01": 1.2,
        "Q02": 1.0,
        "Q03": 1.2,
        "Q04": 1.0,
        "Q05": 1.2,
        "Q06": 1.0,

        # Derivatives & Microstructure (X 系列：16 顆)
        "X01": 1.0,
        "X02": 1.0,
        "X03": 1.0,
        "X04": 1.0,
        "X05": 1.0,
        "X06": 1.0,
        "X07": 1.0,
        "X08": 1.0,
        "X09": 1.0,
        "X10": 1.0,
        "X11": 1.0,
        "X12": 1.0,
        "X13": 1.0,
        "X14": 1.0,
        "X15": 1.0,
        "X16": 1.0,

        # Meta / Composite / Regime (M 系列：36 顆)
        "M01": 0.8,
        "M02": 0.8,
        "M03": 0.8,
        "M04": 0.8,
        "M05": 0.8,
        "M06": 0.8,
        "M07": 0.8,
        "M08": 0.8,
        "M09": 0.8,
        "M10": 0.8,
        "M11": 0.8,
        "M12": 0.8,
        "M13": 0.8,
        "M14": 0.8,
        "M15": 0.8,
        "M16": 0.8,
        "M17": 0.8,
        "M18": 0.8,
        "M19": 0.8,
        "M20": 0.8,
        "M21": 0.8,
        "M22": 0.8,
        "M23": 0.8,
        "M24": 0.8,
        "M25": 0.8,
        "M26": 0.8,
        "M27": 0.8,
        "M28": 0.8,
        "M29": 0.8,
        "M30": 0.8,
        "M31": 0.8,
        "M32": 0.8,
        "M33": 0.8,
        "M34": 0.8,
        "M35": 0.8,
        "M36": 0.8,
    }

    # ------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化 StockUpsideFilter60V1
        
        Args:
            weights: (optional) override default indicator weights
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    # ------------------------------------------------------------
    # Normalization function: converts raw indicator to -1 ~ +1
    # ------------------------------------------------------------
    def _normalize(self, code: str, value: Any) -> float:
        """
        Normalize any raw indicator to range -1.0 ~ +1.0.
        
        Default logic:
        - Boolean: True=1.0, False=-1.0
        - Numeric: clipped to [-1, 1] based on dividing by 100
        
        Args:
            code: 指標代碼（例如 "P01", "C01"）
            value: 原始指標值
        
        Returns:
            標準化的分數（-1.0 ~ +1.0）
        """
        if isinstance(value, bool):
            return 1.0 if value else -1.0

        if isinstance(value, (int, float)):
            if value == 0:
                return 0.0
            norm = value / 100.0
            return max(-1.0, min(1.0, norm))

        # Unknown or empty
        return 0.0

    # ------------------------------------------------------------
    # Main evaluate function
    # ------------------------------------------------------------
    def evaluate(self, symbol: str, indicators: Dict[str, Any]) -> StockUpsideResult:
        """
        評估股票的上漲潛力（60 指標版）
        
        Args:
            symbol: 股票代碼（例如 "2330", "1101"）
            indicators: 指標字典 {code: value}
                - code: 指標代碼（例如 "P01", "C01", "F01"）
                - value: 原始指標值（可以是 bool, int, float）
        
        Returns:
            StockUpsideResult 物件
        """
        indicator_scores: List[IndicatorScore] = []
        total_score = 0.0

        for code, weight in self.weights.items():
            raw = indicators.get(code, 0)
            normalized = self._normalize(code, raw)
            weighted = normalized * weight

            indicator_scores.append(
                IndicatorScore(
                    code=code,
                    name=code,
                    score=normalized,
                    weight=weight,
                    reason=f"raw={raw}, normalized={normalized:.2f}"
                )
            )

            total_score += weighted

        # --------------------------------------------------------
        # Verdict based on total_score (empirical thresholds)
        # --------------------------------------------------------
        if total_score >= 45.0:
            verdict = "STRONG_BUY"
        elif total_score >= 30.0:
            verdict = "BUY"
        elif total_score >= 15.0:
            verdict = "NEUTRAL"
        elif total_score >= 0.0:
            verdict = "AVOID"
        else:
            verdict = "SHORT"

        summary = (
            f"{symbol} total_score={total_score:.2f}, verdict={verdict}. "
            "Evaluation based on J-GOD 60-Indicator Upside Framework."
        )

        return StockUpsideResult(
            symbol=symbol,
            total_score=total_score,
            verdict=verdict,
            summary=summary,
            indicator_scores=indicator_scores,
        )

