"""
Reward Function 測試
"""

import pytest

from jgod.path_d.rl_reward import compute_reward


def test_reward_increases_with_sharpe():
    """測試 Sharpe 增加時，reward 上升"""
    base_reward = compute_reward(
        sharpe=1.0,
        max_drawdown=-10.0,
        breach_ratio=0.0,
        avg_turnover=50.0,
    )
    
    higher_reward = compute_reward(
        sharpe=2.0,
        max_drawdown=-10.0,
        breach_ratio=0.0,
        avg_turnover=50.0,
    )
    
    assert higher_reward > base_reward


def test_reward_decreases_with_max_drawdown():
    """測試 MaxDD 變大時，reward 下降"""
    base_reward = compute_reward(
        sharpe=1.5,
        max_drawdown=-10.0,
        breach_ratio=0.0,
        avg_turnover=50.0,
    )
    
    lower_reward = compute_reward(
        sharpe=1.5,
        max_drawdown=-20.0,
        breach_ratio=0.0,
        avg_turnover=50.0,
    )
    
    assert lower_reward < base_reward


def test_reward_decreases_with_breach_ratio():
    """測試 breach_ratio 從 0 增加時，reward 明顯下降"""
    no_breach_reward = compute_reward(
        sharpe=1.5,
        max_drawdown=-10.0,
        breach_ratio=0.0,
        avg_turnover=50.0,
    )
    
    with_breach_reward = compute_reward(
        sharpe=1.5,
        max_drawdown=-10.0,
        breach_ratio=1.0,
        avg_turnover=50.0,
    )
    
    # Breach penalty 應該很明顯（-5.0 * breach_ratio）
    assert with_breach_reward < no_breach_reward
    assert (no_breach_reward - with_breach_reward) > 4.0


def test_reward_turnover_penalty():
    """測試 turnover penalty"""
    low_turnover_reward = compute_reward(
        sharpe=1.5,
        max_drawdown=-10.0,
        breach_ratio=0.0,
        avg_turnover=50.0,
    )
    
    high_turnover_reward = compute_reward(
        sharpe=1.5,
        max_drawdown=-10.0,
        breach_ratio=0.0,
        avg_turnover=100.0,
    )
    
    # High turnover 應該有 penalty
    assert high_turnover_reward < low_turnover_reward


def test_reward_no_penalty_when_under_thresholds():
    """測試當指標都在閾值內時，沒有額外 penalty"""
    reward = compute_reward(
        sharpe=2.0,
        max_drawdown=-5.0,  # < 10%
        breach_ratio=0.0,
        avg_turnover=50.0,  # < 80
    )
    
    # Reward 應該接近 base (Sharpe)
    assert reward > 1.5
    assert reward < 2.5

