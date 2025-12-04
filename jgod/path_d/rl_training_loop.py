"""
Path D Training Loop

實作 RL 訓練迴圈，整合 Path B Engine 和 RL Agent。
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

import numpy as np

from jgod.path_d.path_d_types import (
    PathDTrainConfig,
    PathDTrainResult,
    PathDState,
    PathDAction,
    Transition,
)
from jgod.path_d.rl_state_encoder import (
    build_pathd_state_from_pathb,
    encode_state_to_vector,
)
from jgod.path_d.rl_action_space import (
    sample_initial_params,
    apply_action_to_params,
)
from jgod.path_d.rl_reward import compute_reward
from jgod.path_d.rl_agent import SimpleGaussianPolicyAgent
from jgod.path_b.path_b_engine import (
    PathBEngine,
    PathBConfig,
    PathBRunResult,
    PathBWindowResult,
)

logger = logging.getLogger(__name__)


def train_path_d(config: PathDTrainConfig) -> PathDTrainResult:
    """
    執行 Path D RL 訓練
    
    Args:
        config: 訓練配置
    
    Returns:
        訓練結果
    """
    logger.info(f"=== Path D Training: {config.experiment_name} ===")
    logger.info(f"Episodes: {config.episodes}, Steps per episode: {config.max_steps_per_episode}")
    
    # 初始化 Path B Engine
    path_b_engine = PathBEngine(
        data_source=config.data_source,
        mode=config.mode,
    )
    
    # 初始化 RL Agent
    state_dim = 12  # PathDState 有 12 個欄位
    action_dim = 5  # PathDAction 有 5 個欄位
    agent = SimpleGaussianPolicyAgent(
        state_dim=state_dim,
        action_dim=action_dim,
        learning_rate=config.learning_rate,
        gamma=config.gamma,
        seed=config.seed,
    )
    
    # 訓練迴圈
    episode_rewards: List[float] = []
    best_reward = float('-inf')
    best_policy_path = None
    
    for episode in range(1, config.episodes + 1):
        logger.info(f"[Episode {episode}/{config.episodes}]")
        
        # 初始化 episode
        current_params = sample_initial_params()
        episode_transitions: List[Transition] = []
        episode_reward = 0.0
        recent_windows: List[PathBWindowResult] = []
        
        for step in range(1, config.max_steps_per_episode + 1):
            logger.debug(f"  Step {step}/{config.max_steps_per_episode}")
            
            # 建立 Path B Config（使用當前參數更新治理門檻）
            path_b_config = _build_path_b_config(config.base_path_b_config, current_params)
            
            # 執行 Path B（限制 window 數量以加速訓練）
            try:
                path_b_result = _run_path_b_limited(path_b_engine, path_b_config, max_windows=3)
                
                if not path_b_result.window_results:
                    logger.warning(f"    No window results, skipping step {step}")
                    continue
                
                # 使用最後一個 window 結果
                latest_window = path_b_result.window_results[-1]
                recent_windows.append(latest_window)
                
                # 建立 state
                state = build_pathd_state_from_pathb(
                    window_result=latest_window,
                    current_params=current_params,
                    recent_windows=recent_windows[-5:],
                )
                state_vec = encode_state_to_vector(state)
                
                # Agent 選擇動作
                action_vec = agent.select_action(state_vec, deterministic=False)
                action = PathDAction(
                    delta_sharpe_floor=float(action_vec[0]),
                    delta_max_drawdown_limit=float(action_vec[1]),
                    delta_turnover_limit=float(action_vec[2]),
                    delta_te_max=float(action_vec[3]),
                    delta_mode_logit=float(action_vec[4]),
                )
                
                # 應用動作，得到 next_params
                next_params = apply_action_to_params(current_params, action)
                
                # 計算 reward
                sharpe = latest_window.sharpe_ratio
                max_dd = latest_window.max_drawdown
                turnover = latest_window.turnover_rate
                
                # 計算 breach ratio
                breach_ratio = 0.0
                if path_b_result.governance_summary:
                    breach_ratio = (
                        path_b_result.governance_summary.windows_with_any_breach /
                        max(path_b_result.governance_summary.total_windows, 1)
                    )
                
                reward = compute_reward(
                    sharpe=sharpe,
                    max_drawdown=max_dd,
                    breach_ratio=breach_ratio,
                    avg_turnover=turnover,
                )
                
                episode_reward += reward
                
                # 建立 next_state（使用 next_params 和相同的 window）
                next_state = build_pathd_state_from_pathb(
                    window_result=latest_window,
                    current_params=next_params,
                    recent_windows=recent_windows[-5:],
                )
                next_state_vec = encode_state_to_vector(next_state)
                
                # 記錄 transition
                transition = Transition(
                    state=state_vec,
                    action=action_vec,
                    reward=reward,
                    next_state=next_state_vec,
                    done=(step == config.max_steps_per_episode),
                )
                agent.observe(transition)
                episode_transitions.append(transition)
                
                # 更新 current_params
                current_params = next_params
                
            except Exception as e:
                logger.exception(f"    Step {step} failed: {e}")
                # 給一個負 reward
                reward = -10.0
                episode_reward += reward
                break
        
        # Episode 結束，訓練 Agent
        train_metrics = agent.train_step()
        episode_rewards.append(episode_reward)
        
        logger.info(
            f"  Episode {episode} completed: "
            f"reward={episode_reward:.2f}, "
            f"avg_reward={np.mean(episode_rewards[-10:]):.2f}"
        )
        
        # 儲存最佳 policy
        if episode_reward > best_reward:
            best_reward = episode_reward
            output_dir = Path("models/path_d") / config.experiment_name
            output_dir.mkdir(parents=True, exist_ok=True)
            best_policy_path = str(output_dir / "best_policy.npz")
            agent.save(best_policy_path)
            logger.info(f"  Saved best policy to {best_policy_path}")
    
    # 建立結果
    result = PathDTrainResult(
        config=config,
        episode_rewards=episode_rewards,
        metrics={
            "avg_reward": float(np.mean(episode_rewards)),
            "best_reward": float(best_reward),
            "final_reward": float(episode_rewards[-1]) if episode_rewards else 0.0,
        },
        best_policy_path=best_policy_path,
    )
    
    logger.info(f"Training completed. Best reward: {best_reward:.2f}")
    
    return result


def _build_path_b_config(
    base_config: Dict[str, Any],
    current_params: Dict[str, float],
) -> PathBConfig:
    """
    從 base_config 和 current_params 建立 PathBConfig
    
    Args:
        base_config: 基礎配置字典
        current_params: 當前 RL 參數
    
    Returns:
        PathBConfig 物件
    """
    # 複製基礎配置
    config_dict = base_config.copy()
    
    # 更新治理門檻
    config_dict["max_drawdown_threshold"] = -current_params.get("max_drawdown_limit", 15.0) / 100.0
    config_dict["sharpe_threshold"] = current_params.get("sharpe_floor", 1.0)
    config_dict["tracking_error_max"] = current_params.get("te_max", 4.0) / 100.0
    config_dict["turnover_max"] = current_params.get("turnover_limit", 100.0) / 100.0
    config_dict["mode"] = current_params.get("mode", "basic")
    
    # 建立 PathBConfig（假設 base_config 已包含所有必要欄位）
    return PathBConfig(**config_dict)


def _run_path_b_limited(
    path_b_engine: PathBEngine,
    config: PathBConfig,
    max_windows: int = 3,
) -> PathBRunResult:
    """
    執行 Path B，但限制 window 數量（用於加速訓練）
    
    Args:
        path_b_engine: Path B Engine 實例
        config: Path B 配置
        max_windows: 最大 window 數量
    
    Returns:
        PathBRunResult（可能只包含部分 windows）
    """
    # 執行完整 Path B
    result = path_b_engine.run(config)
    
    # 如果 window 數量超過限制，只保留前 N 個
    if len(result.window_results) > max_windows:
        result.window_results = result.window_results[:max_windows]
        if result.windows_governance:
            result.windows_governance = result.windows_governance[:max_windows]
    
    return result

