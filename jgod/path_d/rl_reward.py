"""
Path D Reward Function

計算 RL Agent 的 reward，基於 Path B 的績效指標。
"""

from __future__ import annotations


def compute_reward(
    sharpe: float,
    max_drawdown: float,
    breach_ratio: float,
    avg_turnover: float,
) -> float:
    """
    計算 reward
    
    Reward 設計：
    - base = sharpe
    - 若 max_drawdown > 10, penalty_dd = -0.1 * ((max_drawdown - 10) / 5.0)
    - penalty_breach = -5.0 * breach_ratio
    - 若 avg_turnover > 80, penalty_turnover = -0.01 * (avg_turnover - 80)
    
    Args:
        sharpe: Sharpe Ratio
        max_drawdown: 最大回撤（百分比，例如 -26.87 表示 -26.87%）
        breach_ratio: Governance breach 比例 (0.0 ~ 1.0)
        avg_turnover: 平均換手率（年化）
    
    Returns:
        Reward 值（float）
    """
    # Base reward = Sharpe
    base = sharpe
    
    # Drawdown penalty（絕對值）
    max_dd_abs = abs(max_drawdown)
    if max_dd_abs > 10.0:
        penalty_dd = -0.1 * ((max_dd_abs - 10.0) / 5.0)
    else:
        penalty_dd = 0.0
    
    # Breach penalty（重要）
    penalty_breach = -5.0 * breach_ratio
    
    # Turnover penalty
    if avg_turnover > 80.0:
        penalty_turnover = -0.01 * (avg_turnover - 80.0)
    else:
        penalty_turnover = 0.0
    
    reward = base + penalty_dd + penalty_breach + penalty_turnover
    
    return reward

