"""J-GOD Performance & Attribution Engine v1

提供績效計算和歸因分析功能。

Reference:
- docs/JGOD_PERFORMANCE_ENGINE_STANDARD_v1.md
- spec/JGOD_PerformanceEngine_Spec.md
"""

from .performance_types import (
    PerformanceEngineRequest,
    PerformanceSummary,
    AttributionReport,
    PerformanceEngineResult,
)
from .performance_metrics import (
    compute_cumulative_return,
    compute_cagr,
    compute_annualized_vol,
    compute_sharpe,
    compute_max_drawdown,
    compute_calmar,
    compute_hit_rate,
    compute_avg_win_loss,
    compute_turnover,
)
from .attribution_engine import PerformanceEngine

__all__ = [
    # Types
    "PerformanceEngineRequest",
    "PerformanceSummary",
    "AttributionReport",
    "PerformanceEngineResult",
    # Metrics functions
    "compute_cumulative_return",
    "compute_cagr",
    "compute_annualized_vol",
    "compute_sharpe",
    "compute_max_drawdown",
    "compute_calmar",
    "compute_hit_rate",
    "compute_avg_win_loss",
    "compute_turnover",
    # Engine
    "PerformanceEngine",
]

