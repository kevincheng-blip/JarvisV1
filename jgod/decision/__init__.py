"""
J-GOD Decision & Risk Engine v1

統一入口：從 DailySignalSet 產生目標部位配置表 PortfolioPlan。

設計目標：
- 讀取 Strategy & Signal Engine v1 產出的 DailySignalSet
- 套用簡單但合理的風險規則
- 計算每檔股票的 target_weight、多空總曝險等
- 未來 Path A / War Room / Execution 都只讀這裡
"""

from jgod.decision.decision_engine_v1 import (
    DecisionEngineV1,
    PositionPlan,
    PortfolioPlan,
    RiskConfig,
)

__all__ = [
    "DecisionEngineV1",
    "PositionPlan",
    "PortfolioPlan",
    "RiskConfig",
]

