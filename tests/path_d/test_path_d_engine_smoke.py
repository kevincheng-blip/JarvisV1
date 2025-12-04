"""
Path D Engine Smoke Test

測試 Path D Engine 的基本初始化和執行流程。
"""

import pytest
from pathlib import Path

from jgod.path_d.path_d_engine import PathDEngine
from jgod.path_d.path_d_types import (
    PathDTrainConfig,
    PathDRunConfig,
)


@pytest.fixture
def mock_path_b_config():
    """建立一個 mock Path B 配置"""
    return {
        "train_start": "2020-01-01",
        "train_end": "2022-12-31",
        "test_start": "2023-01-01",
        "test_end": "2023-12-31",
        "walkforward_window": "6m",
        "walkforward_step": "3m",
        "universe": ["AAPL", "GOOGL", "MSFT"],
        "rebalance_frequency": "M",
        "alpha_config_set": [
            {
                "name": "strategy_1",
                "alpha_config": {},
            }
        ],
        "data_source": "mock",
        "mode": "basic",
        "experiment_name": "test_path_d",
    }


def test_path_d_engine_initialization():
    """測試 Path D Engine 初始化"""
    engine = PathDEngine()
    assert engine is not None
    assert engine.path_b_engine is None


def test_path_d_train_config_creation(mock_path_b_config):
    """測試 PathDTrainConfig 建立"""
    config = PathDTrainConfig(
        experiment_name="test_experiment",
        data_source="mock",
        mode="basic",
        base_path_b_config=mock_path_b_config,
        episodes=1,
        max_steps_per_episode=1,
        gamma=0.99,
        learning_rate=0.001,
        seed=42,
    )
    
    assert config.experiment_name == "test_experiment"
    assert config.episodes == 1
    assert config.max_steps_per_episode == 1


@pytest.mark.slow
def test_path_d_engine_train_minimal(mock_path_b_config):
    """
    測試 Path D Engine 訓練（最小配置）
    
    注意：這是一個 smoke test，只確保流程不報錯，不驗證結果品質。
    """
    config = PathDTrainConfig(
        experiment_name="smoke_test",
        data_source="mock",
        mode="basic",
        base_path_b_config=mock_path_b_config,
        episodes=1,
        max_steps_per_episode=1,
        gamma=0.99,
        learning_rate=0.001,
        seed=42,
    )
    
    engine = PathDEngine()
    
    # 執行訓練（應該不報錯）
    result = engine.train(config)
    
    # 檢查結果結構
    assert result is not None
    assert result.config == config
    assert len(result.episode_rewards) == 1
    assert "avg_reward" in result.metrics
    assert result.best_policy_path is not None
    
    # 檢查 policy 檔案是否存在
    assert Path(result.best_policy_path).exists()


def test_path_d_engine_eval_config_creation(mock_path_b_config, tmp_path):
    """測試 PathDRunConfig 建立"""
    policy_path = str(tmp_path / "test_policy.npz")
    
    config = PathDRunConfig(
        experiment_name="test_eval",
        data_source="mock",
        mode="basic",
        base_path_b_config=mock_path_b_config,
        eval_episodes=1,
        max_steps_per_episode=1,
        policy_path=policy_path,
    )
    
    assert config.experiment_name == "test_eval"
    assert config.eval_episodes == 1
    assert config.policy_path == policy_path

