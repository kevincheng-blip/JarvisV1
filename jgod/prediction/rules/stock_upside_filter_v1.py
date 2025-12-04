"""
Stock Upside Filter V1

Rule-based filter for evaluating upside potential of a single stock
based on the J-GOD 12-indicator model (Price, Capital, Fundamental, Catalyst, Sentiment).

Reference:
- docs/JGOD_Stock_Upside_12_Indicators_v1.md
- docs/JGOD_Stock_Upside_12_Indicators_KB_v1.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class IndicatorScore:
    """單一指標的評分"""
    code: str
    name: str
    score: float     # -1.0 ~ +1.0
    weight: float
    reason: str


@dataclass
class StockUpsideResult:
    """股票上漲潛力評估結果"""
    symbol: str
    total_score: float
    indicator_scores: List[IndicatorScore]
    verdict: str  # "STRONG_BUY", "BUY", "NEUTRAL", "AVOID"
    summary: str


class StockUpsideFilterV1:
    """
    Rule-based filter for evaluating upside potential of a single stock
    based on the J-GOD 12-indicator model (Price, Capital, Fundamental, Catalyst, Sentiment).

    Usage:
        filter = StockUpsideFilterV1()
        indicators = {
            "P01": 1,   # 趨勢向上
            "C01": 300, # 法人買超
            "F01": 10,  # 成長 YOY
        }
        result = filter.evaluate("2330", indicators)
        print(result.verdict)  # "STRONG_BUY", "BUY", etc.
    """

    DEFAULT_WEIGHTS = {
        # 價格 Price
        "P01": 1.5,  # 趨勢斜率
        "P02": 1.5,  # 多頭均線排列
        "P03": 1.0,  # 量能結構
        "P04": 1.0,  # 套牢壓力
        
        # 籌碼 Capital
        "C01": 2.0,  # 法人買賣
        "C02": 2.0,  # 大戶持股比例
        "C03": 1.5,  # 散戶比率
        
        # 財報 Fundamental
        "F01": 2.0,  # 成長動能
        "F02": 1.5,  # 毛利率趨勢
        "F03": 1.5,  # 自由現金流
        
        # 事件 & 情緒
        "E01": 1.0,  # 事件觸發
        "S01": 1.0,  # 市場情緒
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化 StockUpsideFilterV1
        
        Args:
            weights: 自訂權重字典（如果為 None，使用 DEFAULT_WEIGHTS）
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    def _normalize_indicator(self, code: str, value: Any) -> float:
        """
        將原始指標值轉換成 -1.0 ~ +1.0
        
        真正細節可在 Path A/Path B 校正後優化。
        
        Args:
            code: 指標代碼（例如 "P01", "C01"）
            value: 原始指標值（可以是 bool, int, float, 或其他類型）
        
        Returns:
            標準化的分數（-1.0 ~ +1.0）
        """
        if isinstance(value, bool):
            return 1.0 if value else -1.0

        if isinstance(value, (int, float)):
            if value > 0:
                return min(value / 100.0, 1.0)
            else:
                return max(value / 100.0, -1.0)

        return 0.0

    def evaluate(self, symbol: str, indicators: Dict[str, Any]) -> StockUpsideResult:
        """
        評估股票的上漲潛力
        
        Args:
            symbol: 股票代碼（例如 "2330", "1101"）
            indicators: 指標字典 {code: value}
                - code: 指標代碼（例如 "P01", "C01"）
                - value: 原始指標值
        
        Returns:
            StockUpsideResult 物件
        """
        indicator_scores: List[IndicatorScore] = []
        total = 0.0

        for code, weight in self.weights.items():
            raw_value = indicators.get(code, 0)
            score = self._normalize_indicator(code, raw_value)
            weighted = score * weight

            indicator_scores.append(
                IndicatorScore(
                    code=code,
                    name=code,
                    score=score,
                    weight=weight,
                    reason=f"Input={raw_value}, normalized={score:.2f}"
                )
            )
            total += weighted

        # 根據總分判斷 verdict
        if total >= 8.0:
            verdict = "STRONG_BUY"
        elif total >= 4.0:
            verdict = "BUY"
        elif total > 0.0:
            verdict = "NEUTRAL"
        else:
            verdict = "AVOID"

        summary = (
            f"{symbol}: total_score={total:.2f}, verdict={verdict}. "
            "Model based on J-GOD 12-indicator rule-based filter."
        )

        return StockUpsideResult(
            symbol=symbol,
            total_score=total,
            indicator_scores=indicator_scores,
            verdict=verdict,
            summary=summary
        )

