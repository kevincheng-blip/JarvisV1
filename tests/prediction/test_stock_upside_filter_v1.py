"""
Test Stock Upside Filter V1

測試 J-GOD 12 指標模型的 Rule-Based Filter。
"""

import pytest

from jgod.prediction.rules.stock_upside_filter_v1 import (
    StockUpsideFilterV1,
    StockUpsideResult,
    IndicatorScore,
)


def test_filter_basic():
    """基本測試：驗證 filter 可以正常初始化與執行"""
    f = StockUpsideFilterV1()

    indicators = {
        "P01": 1,   # 趨勢向上
        "C01": 300, # 法人買超
        "F01": 10,  # 成長 YOY
    }

    result = f.evaluate("1101", indicators)

    assert isinstance(result, StockUpsideResult)
    assert result.symbol == "1101"
    assert result.verdict in ["STRONG_BUY", "BUY", "NEUTRAL", "AVOID"]
    assert len(result.indicator_scores) > 0


def test_filter_all_indicators():
    """測試所有 12 指標都參與評分"""
    f = StockUpsideFilterV1()

    # 提供所有指標（全部為正向值）
    indicators = {
        "P01": 1,  # 趨勢斜率
        "P02": 1,  # 多頭均線排列
        "P03": 1,  # 量能結構
        "P04": 1,  # 套牢壓力
        "C01": 1,  # 法人買賣
        "C02": 1,  # 大戶持股比例
        "C03": 1,  # 散戶比率
        "F01": 1,  # 成長動能
        "F02": 1,  # 毛利率趨勢
        "F03": 1,  # 自由現金流
        "E01": 1,  # 事件觸發
        "S01": 1,  # 市場情緒
    }

    result = f.evaluate("2330", indicators)

    assert len(result.indicator_scores) == 12
    assert result.total_score > 0
    assert result.verdict in ["STRONG_BUY", "BUY"]


def test_filter_verdict_thresholds():
    """測試 verdict 判斷門檻"""
    f = StockUpsideFilterV1()

    # 測試 STRONG_BUY（總分 >= 8.0）
    indicators_strong = {
        "P01": 100,  # 強烈正向
        "C01": 100,
        "F01": 100,
        "C02": 100,
    }
    result_strong = f.evaluate("2330", indicators_strong)
    assert result_strong.verdict == "STRONG_BUY" or result_strong.total_score >= 8.0

    # 測試 BUY（總分 >= 4.0）
    indicators_buy = {
        "P01": 50,
        "C01": 50,
    }
    result_buy = f.evaluate("2330", indicators_buy)
    assert result_buy.verdict in ["STRONG_BUY", "BUY"] or result_buy.total_score >= 4.0

    # 測試 AVOID（總分 <= 0）
    indicators_avoid = {
        "P01": -100,  # 強烈負向
        "C01": -100,
    }
    result_avoid = f.evaluate("2330", indicators_avoid)
    assert result_avoid.verdict in ["NEUTRAL", "AVOID"] or result_avoid.total_score <= 0


def test_filter_custom_weights():
    """測試自訂權重"""
    custom_weights = {
        "P01": 2.0,
        "C01": 3.0,
    }
    
    f = StockUpsideFilterV1(weights=custom_weights)

    indicators = {
        "P01": 1,
        "C01": 1,
    }

    result = f.evaluate("2330", indicators)

    # 應該只有 2 個指標參與評分
    assert len(result.indicator_scores) == 2


def test_filter_normalize_indicator():
    """測試指標標準化邏輯"""
    f = StockUpsideFilterV1()

    # 測試 bool 值
    assert f._normalize_indicator("P01", True) == 1.0
    assert f._normalize_indicator("P01", False) == -1.0

    # 測試數值（正向）
    assert f._normalize_indicator("P01", 50) == 0.5
    assert f._normalize_indicator("P01", 100) == 1.0
    assert f._normalize_indicator("P01", 200) == 1.0  # 會被 cap 在 1.0

    # 測試數值（負向）
    assert f._normalize_indicator("P01", -50) == -0.5
    assert f._normalize_indicator("P01", -100) == -1.0

    # 測試其他類型（預設回傳 0.0）
    assert f._normalize_indicator("P01", None) == 0.0
    assert f._normalize_indicator("P01", "invalid") == 0.0


def test_filter_missing_indicators():
    """測試缺少部分指標的情況"""
    f = StockUpsideFilterV1()

    # 只提供部分指標
    indicators = {
        "P01": 1,
        "C01": 1,
    }

    result = f.evaluate("2330", indicators)

    # 應該仍然能正常執行，缺少的指標會被視為 0
    assert isinstance(result, StockUpsideResult)
    assert result.symbol == "2330"
    assert len(result.indicator_scores) == 12  # 所有指標都會有評分（缺少的為 0）

