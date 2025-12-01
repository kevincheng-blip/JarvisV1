"""Tests for Performance Engine v1

Unit tests for J-GOD Performance & Attribution Engine v1.

Reference:
- docs/JGOD_PERFORMANCE_ENGINE_STANDARD_v1.md
- spec/JGOD_PerformanceEngine_Spec.md
"""

from __future__ import annotations

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Test file placeholder - tests will be added later

# 測試案例規劃：
# 1. test_compute_summary_basic()
#    - 建立簡單的 returns / nav 時序
#    - 呼叫 PerformanceEngine.compute_summary
#    - 檢查：
#      - total_return > 0
#      - cagr 合理
#      - max_drawdown 在合理範圍
#
# 2. test_compute_attribution_by_symbol_and_sector()
#    - 構造小型 universe（3-5 檔股票 + sector map）
#    - 設定簡單報酬
#    - 確認：
#      - by_symbol / by_sector 的總貢獻 ≈ portfolio total return（容許微小誤差）
#
# 3. test_compute_full_report_roundtrip()
#    - 建立一個簡單的 PerformanceEngineRequest
#    - 呼叫 compute_full_report
#    - 確認 summary 和 attribution 都有值

