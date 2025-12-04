"""
Path D RL Agent (簡化版 Policy Gradient)

使用 numpy 實作的簡化 REINFORCE 演算法，不依賴深度學習框架。
"""

from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np
import json
import os

from jgod.path_d.path_d_types import Transition


class SimpleGaussianPolicyAgent:
    """
    簡化版高斯策略 Agent
    
    使用線性策略：action = W @ state + b + gaussian_noise
    
    NOTE: 這是簡化版實作，未來可以替換成更高級的 RL 演算法（例如 PPO、SAC）。
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        seed: int = 42,
    ):
        """
        初始化 Agent
        
        Args:
            state_dim: 狀態向量維度
            action_dim: 動作向量維度
            learning_rate: 學習率
            gamma: 折扣因子
            seed: 隨機種子
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.learning_rate = learning_rate
        self.gamma = gamma
        
        # 設定隨機種子
        np.random.seed(seed)
        
        # 初始化策略參數（線性層）
        # W: state_dim x action_dim
        self.W = np.random.randn(state_dim, action_dim) * 0.1
        # b: action_dim
        self.b = np.random.randn(action_dim) * 0.1
        
        # Episode buffer（用於 REINFORCE）
        self.episode_transitions: List[Transition] = []
        
        # 訓練統計
        self.train_step_count = 0
    
    def select_action(
        self,
        state: np.ndarray,
        deterministic: bool = False,
    ) -> np.ndarray:
        """
        選擇動作
        
        Args:
            state: 狀態向量
            deterministic: 是否使用確定性策略（測試時用）
        
        Returns:
            動作向量
        """
        # 線性映射
        mean_action = self.W.T @ state + self.b
        
        if deterministic:
            return mean_action
        
        # 加上高斯雜訊
        noise_scale = 0.1
        noise = np.random.randn(self.action_dim) * noise_scale
        action = mean_action + noise
        
        return action
    
    def observe(self, transition: Transition) -> None:
        """
        記錄一個 transition
        
        Args:
            transition: Transition 物件
        """
        self.episode_transitions.append(transition)
    
    def train_step(self) -> Dict[str, float]:
        """
        執行一個訓練步驟（REINFORCE）
        
        Returns:
            包含訓練指標的字典
        """
        if not self.episode_transitions:
            return {"episode_reward": 0.0, "mean_abs_weight": 0.0}
        
        # 計算每個 transition 的 return（discounted cumulative reward）
        returns = []
        G = 0.0
        for transition in reversed(self.episode_transitions):
            G = transition.reward + self.gamma * G
            returns.insert(0, G)
        
        # 標準化 returns（減均值除標準差）
        returns_array = np.array(returns)
        if len(returns_array) > 1:
            returns_array = (returns_array - returns_array.mean()) / (returns_array.std() + 1e-8)
        
        # REINFORCE 更新
        # 簡化版：對高 return 的 transition，增加其動作的機率
        for i, transition in enumerate(self.episode_transitions):
            state = transition.state
            action = transition.action
            advantage = returns_array[i]
            
            # 計算梯度（簡化版，只更新 W 和 b）
            # 這是一個非常簡化的版本，真正的 REINFORCE 需要更複雜的梯度計算
            # 這裡用簡單的優勢加權更新
            if advantage > 0:
                # 鼓勵這個動作
                delta_W = self.learning_rate * advantage * np.outer(state, action)
                delta_b = self.learning_rate * advantage * action
            else:
                # 懲罰這個動作
                delta_W = -self.learning_rate * abs(advantage) * np.outer(state, action) * 0.1
                delta_b = -self.learning_rate * abs(advantage) * action * 0.1
            
            self.W += delta_W
            self.b += delta_b
        
        # 計算統計指標
        episode_reward = sum(t.reward for t in self.episode_transitions)
        mean_abs_weight = np.abs(self.W).mean()
        
        # 清空 episode buffer
        self.episode_transitions = []
        self.train_step_count += 1
        
        return {
            "episode_reward": float(episode_reward),
            "mean_abs_weight": float(mean_abs_weight),
            "train_step": self.train_step_count,
        }
    
    def save(self, path: str) -> None:
        """
        儲存 Agent 的參數
        
        Args:
            path: 儲存路徑（.npz 格式）
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # 儲存參數
        np.savez(
            path,
            W=self.W,
            b=self.b,
            state_dim=self.state_dim,
            action_dim=self.action_dim,
            learning_rate=self.learning_rate,
            gamma=self.gamma,
        )
    
    @classmethod
    def load(cls, path: str) -> "SimpleGaussianPolicyAgent":
        """
        載入 Agent 參數
        
        Args:
            path: 載入路徑（.npz 格式）
        
        Returns:
            載入參數後的 Agent 實例
        """
        data = np.load(path, allow_pickle=True)
        
        agent = cls(
            state_dim=int(data["state_dim"]),
            action_dim=int(data["action_dim"]),
            learning_rate=float(data["learning_rate"]),
            gamma=float(data["gamma"]),
            seed=42,  # 載入時不需要 seed
        )
        
        agent.W = data["W"]
        agent.b = data["b"]
        
        return agent

