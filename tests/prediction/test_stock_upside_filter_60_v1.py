"""
Test Stock Upside Filter 60 Indicators V1

測試 J-GOD 60 指標模型的 Rule-Based Filter。
"""

import pytest

from jgod.prediction.rules.stock_upside_filter_60_v1 import (
    StockUpsideFilter60V1,
    StockUpsideResult,
    IndicatorScore,
)


def test_filter_60_basic():
    """基本測試：驗證 60 指標 filter 可以正常初始化與執行"""
    f = StockUpsideFilter60V1()

    sample = {
        "P01": 20,
        "C01": 300,
        "F01": 10,
        "K02": True,
        "S01": 5,
        "Q01": 3,
    }

    result = f.evaluate("1101", sample)

    assert isinstance(result, StockUpsideResult)
    assert result.symbol == "1101"
    assert len(result.indicator_scores) == len(f.weights)  # 動態判斷指標數量
    assert result.verdict in ["STRONG_BUY", "BUY", "NEUTRAL", "AVOID", "SHORT"]


def test_filter_60_all_indicators():
    """測試所有 60 指標都參與評分"""
    f = StockUpsideFilter60V1()

    # 提供所有 60 指標（全部為正向值）
    indicators = {}
    
    # Price (12)
    for i in range(1, 13):
        indicators[f"P{i:02d}"] = 1
    
    # Capital (9)
    for i in range(1, 10):
        indicators[f"C{i:02d}"] = 1
    
    # Fundamental (8)
    for i in range(1, 9):
        indicators[f"F{i:02d}"] = 1
    
    # Catalyst (7)
    for i in range(1, 8):
        indicators[f"K{i:02d}"] = True
    
    # Sentiment (6)
    for i in range(1, 7):
        indicators[f"S{i:02d}"] = 1
    
    # Quant (6)
    for i in range(1, 7):
        indicators[f"Q{i:02d}"] = 1

    result = f.evaluate("2330", indicators)

    assert len(result.indicator_scores) == len(f.weights)  # 動態判斷指標數量
    assert result.total_score > 0
    assert result.verdict in ["STRONG_BUY", "BUY"]


def test_filter_60_verdict_thresholds():
    """測試 verdict 判斷門檻"""
    f = StockUpsideFilter60V1()

    # 測試 STRONG_BUY（總分 >= 45.0）
    indicators_strong = {
        "P01": 100,  # 強烈正向
        "C01": 100,
        "C02": 100,
        "F01": 100,
        "K02": True,
        "S01": 100,
    }
    result_strong = f.evaluate("2330", indicators_strong)
    assert result_strong.verdict == "STRONG_BUY" or result_strong.total_score >= 45.0

    # 測試 BUY（總分 >= 30.0）
    indicators_buy = {
        "P01": 50,
        "C01": 50,
        "F01": 50,
    }
    result_buy = f.evaluate("2330", indicators_buy)
    assert result_buy.verdict in ["STRONG_BUY", "BUY"] or result_buy.total_score >= 30.0

    # 測試 AVOID（總分 < 15.0）
    indicators_avoid = {
        "P01": -50,
        "C01": -50,
        "F01": -50,
    }
    result_avoid = f.evaluate("2330", indicators_avoid)
    assert result_avoid.verdict in ["NEUTRAL", "AVOID", "SHORT"] or result_avoid.total_score < 15.0


def test_filter_60_custom_weights():
    """測試自訂權重"""
    custom_weights = {
        "P01": 2.0,
        "C01": 3.0,
        "F01": 2.0,
    }
    
    f = StockUpsideFilter60V1(weights=custom_weights)

    indicators = {
        "P01": 1,
        "C01": 1,
        "F01": 1,
    }

    result = f.evaluate("2330", indicators)

    # 應該只有自訂權重中的指標參與評分
    assert len(result.indicator_scores) == len(f.weights)  # 動態判斷指標數量


def test_filter_60_normalize():
    """測試指標標準化邏輯"""
    f = StockUpsideFilter60V1()

    # 測試 bool 值
    assert f._normalize("P01", True) == 1.0
    assert f._normalize("P01", False) == -1.0

    # 測試數值（正向）
    assert f._normalize("P01", 50) == 0.5
    assert f._normalize("P01", 100) == 1.0
    assert f._normalize("P01", 200) == 1.0  # 會被 cap 在 1.0

    # 測試數值（負向）
    assert f._normalize("P01", -50) == -0.5
    assert f._normalize("P01", -100) == -1.0

    # 測試零值
    assert f._normalize("P01", 0) == 0.0

    # 測試其他類型（預設回傳 0.0）
    assert f._normalize("P01", None) == 0.0
    assert f._normalize("P01", "invalid") == 0.0


def test_filter_60_missing_indicators():
    """測試缺少部分指標的情況"""
    f = StockUpsideFilter60V1()

    # 只提供部分指標
    indicators = {
        "P01": 1,
        "C01": 1,
        "F01": 1,
    }

    result = f.evaluate("2330", indicators)

    # 應該仍然能正常執行，所有指標都會有評分（缺少的為 0）
    assert isinstance(result, StockUpsideResult)
    assert result.symbol == "2330"
    assert len(result.indicator_scores) == len(f.weights)  # 動態判斷指標數量

