"""
Test Indicator Builder 100

Smoke tests for StockIndicatorBuilder100.
"""

from datetime import date

from jgod.prediction.data.indicator_builder_100 import StockIndicatorBuilder100


def test_build_indicators_basic():
    """基本測試：驗證類別結構存在"""
    # v1 測試重點：函式可呼叫、回傳 dict、含有主要 code
    # 這裡不打 FinMind API，因為沒有 token 時會直接 raise，
    # 所以實際使用時要傳入你的 token。
    # 測試用只驗證類別結構存在即可。
    assert hasattr(StockIndicatorBuilder100, "build_indicators")


# 真正 hitting FinMind 的測試，需在本機手動開啟，避免 CI 失敗
def _manual_test_build_indicators_with_token():
    """手動測試：需要 FinMind token"""
    token = "YOUR_TOKEN_HERE"
    builder = StockIndicatorBuilder100(finmind_token=token)
    indicators = builder.build_indicators("1101", date.today())
    # 至少應該有 P01, C01, F01, Q02 等 key
    assert "P01" in indicators
    assert "C01" in indicators
    assert "F01" in indicators
    assert "Q02" in indicators

