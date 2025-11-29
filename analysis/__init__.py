"""
分析與績效模組。

目前包含：
- PerformanceAnalyzer：將 Walk-Forward 模擬結果 (F_Signal 訊號) 轉換為
  報酬序列與標準績效指標（Sharpe、Max Drawdown、CAGR、Hit Rate）。
"""

from .performance_analyzer import (
    DailyReturn,
    PerformanceMetrics,
    PerformanceAnalyzer,
)

__all__ = [
    "DailyReturn",
    "PerformanceMetrics",
    "PerformanceAnalyzer",
]

