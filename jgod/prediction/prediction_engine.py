"""
規則型預測引擎：使用規則和打分機制預測明日可能漲/跌最多的股票
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal, List
import argparse

import pandas as pd

from .feature_builder import build_feature_frame


@dataclass
class PredictionResult:
    """預測結果"""
    symbol: str
    direction: Literal["up", "down"]
    score: float
    probability: float
    reasons: list[str]
    features: dict


class PredictionEngine:
    """
    規則型預測引擎
    
    功能：
    - 使用特徵建構器取得股票特徵
    - 根據規則對每檔股票打分
    - 預測明日可能漲/跌最多的股票
    """
    
    def __init__(
        self,
        symbols: list[str],
        as_of: date | None = None,
    ) -> None:
        """
        初始化預測引擎
        
        Args:
            symbols: 股票代號列表
            as_of: 基準日期（如果為 None 則使用今天）
        """
        self.symbols = symbols
        self.as_of = as_of or date.today()
    
    def build_features(self) -> pd.DataFrame:
        """
        建構特徵 DataFrame
        
        Returns:
            包含所有股票特徵的 DataFrame
        """
        return build_feature_frame(
            symbols=self.symbols,
            end_date=self.as_of,
            lookback_days=60,
        )
    
    def score_row_up(self, row: pd.Series) -> tuple[float, list[str]]:
        """
        為上漲方向打分
        
        Args:
            row: 單一股票的特徵 Series
        
        Returns:
            (分數, 理由列表)
        """
        score = 0.0
        reasons = []
        
        # 取得特徵值（處理可能的 NaN）
        pct_change_1d = float(row.get("pct_change_1d", 0.0) or 0.0)
        pct_change_5d = float(row.get("pct_change_5d", 0.0) or 0.0)
        close = float(row.get("close", 0.0) or 0.0)
        ma_5 = float(row.get("ma_5", close) or close)
        ma_20 = float(row.get("ma_20", close) or close)
        volume_ratio_5d = float(row.get("volume_ratio_5d", 1.0) or 1.0)
        rsi_14 = float(row.get("rsi_14", 50.0) or 50.0)
        
        # 短期動能
        if pct_change_5d > 0:
            score += 1.0
            reasons.append("近 5 日走勢偏強")
        
        if pct_change_1d < 0 and pct_change_5d > 0:
            score += 0.5
            reasons.append("短線回檔中的多頭")
        
        # 均線結構
        if ma_5 > ma_20:
            score += 1.5
            reasons.append("短期均線站上中期均線（多頭排列）")
        
        # 股價接近中期均線支撐（±2% 內）
        if ma_20 > 0:
            ma_distance_pct = abs((close - ma_20) / ma_20)
            if ma_distance_pct <= 0.02:
                score += 0.5
                reasons.append("股價接近中期均線支撐")
        
        # 量能
        if 1.2 <= volume_ratio_5d <= 3.0:
            score += 1.0
            reasons.append("量能放大但尚未過熱")
        elif volume_ratio_5d > 3.0:
            score -= 0.5
            reasons.append("量能過熱，留意隔日獲利了結")
        
        # RSI
        if 40 <= rsi_14 <= 65:
            score += 1.0
            reasons.append("RSI 落在健康多頭區")
        elif rsi_14 > 75:
            score -= 1.0
            reasons.append("RSI 過熱，有修正風險")
        
        return score, reasons
    
    def score_row_down(self, row: pd.Series) -> tuple[float, list[str]]:
        """
        為下跌方向打分
        
        Args:
            row: 單一股票的特徵 Series
        
        Returns:
            (分數, 理由列表)
        """
        score = 0.0
        reasons = []
        
        # 取得特徵值（處理可能的 NaN）
        pct_change_1d = float(row.get("pct_change_1d", 0.0) or 0.0)
        pct_change_5d = float(row.get("pct_change_5d", 0.0) or 0.0)
        close = float(row.get("close", 0.0) or 0.0)
        ma_5 = float(row.get("ma_5", close) or close)
        ma_20 = float(row.get("ma_20", close) or close)
        volume_ratio_5d = float(row.get("volume_ratio_5d", 1.0) or 1.0)
        rsi_14 = float(row.get("rsi_14", 50.0) or 50.0)
        
        # 短期動能（下跌）
        if pct_change_5d < 0:
            score += 1.0
            reasons.append("近 5 日走勢偏弱")
        
        if pct_change_1d > 0 and pct_change_5d < 0:
            score += 0.5
            reasons.append("短線反彈中的空頭")
        
        # 均線結構（空頭排列）
        if ma_5 < ma_20:
            score += 1.5
            reasons.append("短期均線跌破中期均線（空頭排列）")
        
        # 股價接近中期均線壓力（±2% 內）
        if ma_20 > 0:
            ma_distance_pct = abs((close - ma_20) / ma_20)
            if ma_distance_pct <= 0.02:
                score += 0.5
                reasons.append("股價接近中期均線壓力")
        
        # 量能（放量下跌）
        if volume_ratio_5d >= 1.2 and pct_change_1d < 0:
            score += 1.0
            reasons.append("放量下跌，賣壓沉重")
        elif volume_ratio_5d > 3.0 and pct_change_1d < 0:
            score += 0.5
            reasons.append("量能過熱且下跌，可能接近低點")
        
        # RSI（過熱或超賣）
        if rsi_14 < 30:
            # 已經殺過頭，扣一些分避免全部選到已經跌深股
            score -= 0.5
            reasons.append("RSI 超賣，可能接近低點")
        elif 35 <= rsi_14 <= 60:
            score += 1.0
            reasons.append("RSI 落在健康空頭區")
        elif rsi_14 > 70:
            score += 0.5
            reasons.append("RSI 過熱，有修正風險")
        
        return score, reasons
    
    def predict_top_movers(
        self,
        direction: Literal["up", "down"] = "up",
        top_n: int = 30,
    ) -> list[PredictionResult]:
        """
        預測明日可能漲/跌最多的股票
        
        Args:
            direction: 預測方向（"up" 或 "down"）
            top_n: 回傳前 N 名（預設：30）
        
        Returns:
            預測結果列表（已排序）
        """
        # 建構特徵
        df = self.build_features()
        
        if df.empty:
            return []
        
        results = []
        
        # 對每一列打分
        for _, row in df.iterrows():
            if direction == "up":
                score, reasons = self.score_row_up(row)
            else:  # direction == "down"
                score, reasons = self.score_row_down(row)
            
            # 若分數 <= 0，略過
            if score <= 0:
                continue
            
            # 計算機率
            if direction == "up":
                probability = min(0.9, 0.5 + score / 10)
            else:  # direction == "down"
                probability = min(0.9, 0.5 + score / 10)
            
            # 建立預測結果
            result = PredictionResult(
                symbol=str(row["symbol"]),
                direction=direction,
                score=score,
                probability=probability,
                reasons=reasons,
                features=row.to_dict(),
            )
            
            results.append(result)
        
        # 根據分數排序（由高到低）
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 回傳前 top_n 個
        return results[:top_n]


def main() -> None:
    """CLI 入口"""
    parser = argparse.ArgumentParser(
        description="Rule-based prediction engine for top movers."
    )
    parser.add_argument(
        "--direction",
        choices=["up", "down"],
        default="up",
        help="預測方向（up=上漲, down=下跌）",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="回傳前 N 名（預設：10）",
    )
    
    args = parser.parse_args()
    
    # 測試股票列表（未來可接完整 universe）
    test_symbols = ["2330", "2317", "1301"]
    
    engine = PredictionEngine(test_symbols)
    results = engine.predict_top_movers(direction=args.direction, top_n=args.top)
    
    print(f"Direction: {args.direction}, Top {args.top}\n")
    
    if not results:
        print("沒有符合條件的股票")
        return
    
    for r in results:
        print(f"{r.symbol} | score={r.score:.2f} | prob={r.probability:.2%}")
        for reason in r.reasons:
            print(f"  - {reason}")
        print()


if __name__ == "__main__":
    main()
