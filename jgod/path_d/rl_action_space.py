"""
Path D Action Space

定義和管理 RL Agent 的動作空間。
"""

from __future__ import annotations

from typing import Dict
import numpy as np

from jgod.path_d.path_d_types import PathDAction


def sample_initial_params() -> Dict[str, float]:
    """
    生成一組合理的起始治理參數
    
    Returns:
        包含以下鍵的字典：
        - "sharpe_floor"
        - "max_drawdown_limit"
        - "turnover_limit"
        - "te_max"
        - "mode"
    """
    return {
        "sharpe_floor": 1.0,
        "max_drawdown_limit": 15.0,  # 百分比
        "turnover_limit": 100.0,  # 年化換手上限
        "te_max": 4.0,  # 百分比
        "mode": "basic",
    }


def apply_action_to_params(
    current_params: Dict[str, float],
    action: PathDAction,
) -> Dict[str, float]:
    """
    將動作應用到當前參數，產生新的參數設定
    
    Args:
        current_params: 當前參數字典
        action: PathDAction 物件
    
    Returns:
        更新後的參數字典
    """
    # 小步長調整
    new_sharpe_floor = current_params.get("sharpe_floor", 1.0) + action.delta_sharpe_floor * 0.1
    new_max_drawdown_limit = current_params.get("max_drawdown_limit", 15.0) + action.delta_max_drawdown_limit * 1.0
    new_turnover_limit = current_params.get("turnover_limit", 100.0) + action.delta_turnover_limit * 5.0
    new_te_max = current_params.get("te_max", 4.0) + action.delta_te_max * 0.5
    
    # 決定 mode
    current_mode = current_params.get("mode", "basic")
    if action.delta_mode_logit > 0:
        new_mode = "extreme"
    else:
        new_mode = "basic"
    
    # Clip 到合理範圍
    new_sharpe_floor = np.clip(new_sharpe_floor, -1.0, 3.0)
    new_max_drawdown_limit = np.clip(new_max_drawdown_limit, 5.0, 40.0)
    new_turnover_limit = np.clip(new_turnover_limit, 10.0, 200.0)
    new_te_max = np.clip(new_te_max, 1.0, 10.0)
    
    return {
        "sharpe_floor": float(new_sharpe_floor),
        "max_drawdown_limit": float(new_max_drawdown_limit),
        "turnover_limit": float(new_turnover_limit),
        "te_max": float(new_te_max),
        "mode": new_mode,
    }

