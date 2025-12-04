"""
Path C v1 - Scenario Presets

This module provides preset scenario configurations for common use cases.
"""

from __future__ import annotations

from typing import List
from jgod.path_c.path_c_types import PathCScenarioConfig


def get_default_scenarios_for_taiwan_equities() -> List[PathCScenarioConfig]:
    """
    取得台股預設 scenarios
    
    包含：
    - Basic mode 不同 window/step 組合
    - Extreme mode 不同 window/step 組合
    - 不同治理門檻設定
    
    Returns:
        Scenario 配置列表
    """
    base_universe = ["2330.TW", "2317.TW", "1301.TW", "2454.TW"]
    
    scenarios: List[PathCScenarioConfig] = []
    
    # Scenario 1: Basic mode, 6m window, 1m step
    scenarios.append(PathCScenarioConfig(
        name="basic_6m_1m",
        description="Basic mode with 6-month window and 1-month step",
        start_date="2023-01-01",
        end_date="2023-12-31",
        rebalance_frequency="M",
        universe=base_universe,
        walkforward_window="6m",
        walkforward_step="1m",
        data_source="mock",
        mode="basic",
        regime_tag="default",
    ))
    
    # Scenario 2: Basic mode, 12m window, 3m step
    scenarios.append(PathCScenarioConfig(
        name="basic_12m_3m",
        description="Basic mode with 12-month window and 3-month step",
        start_date="2023-01-01",
        end_date="2023-12-31",
        rebalance_frequency="M",
        universe=base_universe,
        walkforward_window="12m",
        walkforward_step="3m",
        data_source="mock",
        mode="basic",
        regime_tag="default",
    ))
    
    # Scenario 3: Extreme mode, 6m window, 1m step
    scenarios.append(PathCScenarioConfig(
        name="extreme_6m_1m",
        description="Extreme mode with 6-month window and 1-month step",
        start_date="2023-01-01",
        end_date="2023-12-31",
        rebalance_frequency="M",
        universe=base_universe,
        walkforward_window="6m",
        walkforward_step="1m",
        data_source="mock",
        mode="extreme",
        regime_tag="extreme",
    ))
    
    return scenarios

