"""
Path D Engine

RL-based Governance / Hyper-Parameter Tuner 主引擎。
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
import logging

from jgod.path_d.path_d_types import (
    PathDTrainConfig,
    PathDRunConfig,
    PathDTrainResult,
    PathDRunResult,
)
from jgod.path_d.rl_training_loop import train_path_d
from jgod.path_d.rl_agent import SimpleGaussianPolicyAgent
from jgod.path_d.rl_state_encoder import (
    build_pathd_state_from_pathb,
    encode_state_to_vector,
)
from jgod.path_d.rl_action_space import (
    sample_initial_params,
    apply_action_to_params,
)
from jgod.path_d.rl_reward import compute_reward
from jgod.path_b.path_b_engine import (
    PathBEngine,
    PathBConfig,
    PathBRunResult,
)

logger = logging.getLogger(__name__)


class PathDEngine:
    """Path D Engine - RL-based Governance / Hyper-Parameter Tuner"""
    
    def __init__(
        self,
        path_b_engine: Optional[PathBEngine] = None,
    ):
        """
        初始化 Path D Engine
        
        Args:
            path_b_engine: Path B Engine 實例（可選，若為 None 則在執行時建立）
        """
        self.path_b_engine = path_b_engine
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def train(self, config: PathDTrainConfig) -> PathDTrainResult:
        """
        執行 Path D RL 訓練
        
        Args:
            config: 訓練配置
        
        Returns:
            訓練結果
        """
        self.logger.info(f"Path D Training: {config.experiment_name}")
        return train_path_d(config)
    
    def evaluate(
        self,
        run_config: PathDRunConfig,
    ) -> PathDRunResult:
        """
        評估已訓練的 policy
        
        Args:
            run_config: 評估配置
        
        Returns:
            評估結果
        """
        self.logger.info(f"Path D Evaluation: {run_config.experiment_name}")
        
        # 載入 policy
        try:
            agent = SimpleGaussianPolicyAgent.load(run_config.policy_path)
            self.logger.info(f"Loaded policy from {run_config.policy_path}")
        except Exception as e:
            self.logger.error(f"Failed to load policy: {e}")
            raise
        
        # 初始化 Path B Engine
        if self.path_b_engine is None:
            self.path_b_engine = PathBEngine(
                data_source=run_config.data_source,
                mode=run_config.mode,
            )
        
        # 評估迴圈
        episode_rewards: List[float] = []
        all_metrics: List[Dict[str, float]] = []
        
        for episode in range(1, run_config.eval_episodes + 1):
            self.logger.info(f"[Eval Episode {episode}/{run_config.eval_episodes}]")
            
            # 初始化參數
            current_params = sample_initial_params()
            episode_reward = 0.0
            
            for step in range(1, run_config.max_steps_per_episode + 1):
                # 建立 Path B Config
                path_b_config = self._build_path_b_config(
                    run_config.base_path_b_config,
                    current_params,
                )
                
                # 執行 Path B
                try:
                    path_b_result = self.path_b_engine.run(path_b_config)
                    
                    if not path_b_result.window_results:
                        self.logger.warning(f"  No window results, skipping step {step}")
                        continue
                    
                    # 使用最後一個 window
                    latest_window = path_b_result.window_results[-1]
                    
                    # 建立 state
                    state = build_pathd_state_from_pathb(
                        window_result=latest_window,
                        current_params=current_params,
                        recent_windows=path_b_result.window_results[-5:],
                    )
                    state_vec = encode_state_to_vector(state)
                    
                    # Agent 選擇動作（確定性模式）
                    from jgod.path_d.path_d_types import PathDAction
                    action_vec = agent.select_action(state_vec, deterministic=True)
                    action = PathDAction(
                        delta_sharpe_floor=float(action_vec[0]),
                        delta_max_drawdown_limit=float(action_vec[1]),
                        delta_turnover_limit=float(action_vec[2]),
                        delta_te_max=float(action_vec[3]),
                        delta_mode_logit=float(action_vec[4]),
                    )
                    
                    # 計算 reward
                    sharpe = latest_window.sharpe_ratio
                    max_dd = latest_window.max_drawdown
                    turnover = latest_window.turnover_rate
                    
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
                    
                    # 更新參數
                    current_params = apply_action_to_params(current_params, action)
                    
                except Exception as e:
                    self.logger.exception(f"  Step {step} failed: {e}")
                    break
            
            episode_rewards.append(episode_reward)
            
            # 收集最終 metrics（使用最後一個 window）
            if path_b_result.window_results:
                final_window = path_b_result.window_results[-1]
                all_metrics.append({
                    "sharpe": final_window.sharpe_ratio,
                    "max_drawdown": final_window.max_drawdown,
                    "total_return": final_window.total_return,
                    "turnover": final_window.turnover_rate,
                    "breach_ratio": breach_ratio,
                })
        
        # 計算平均 metrics
        avg_metrics = {}
        if all_metrics:
            for key in all_metrics[0].keys():
                avg_metrics[f"avg_{key}"] = float(
                    sum(m[key] for m in all_metrics) / len(all_metrics)
                )
        
        result = PathDRunResult(
            config=run_config,
            episode_rewards=episode_rewards,
            metrics=avg_metrics,
        )
        
        self.logger.info(
            f"Evaluation completed. "
            f"Avg reward: {sum(episode_rewards) / len(episode_rewards):.2f}"
        )
        
        return result
    
    def _build_path_b_config(
        self,
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
        config_dict = base_config.copy()
        
        # 更新治理門檻
        config_dict["max_drawdown_threshold"] = -current_params.get("max_drawdown_limit", 15.0) / 100.0
        config_dict["sharpe_threshold"] = current_params.get("sharpe_floor", 1.0)
        config_dict["tracking_error_max"] = current_params.get("te_max", 4.0) / 100.0
        config_dict["turnover_max"] = current_params.get("turnover_limit", 100.0) / 100.0
        config_dict["mode"] = current_params.get("mode", "basic")
        
        return PathBConfig(**config_dict)

