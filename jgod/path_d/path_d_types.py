"""
Path D 型別定義

定義所有 Path D RL Engine 使用的資料結構和型別。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal, Any
import numpy as np


@dataclass
class PathDState:
    """
    Path D RL 狀態空間
    
    包含從 Path B Window Result 提取的績效指標和當前參數設定。
    """
    
    # 最後一個 window 的績效指標
    sharpe_last: float = 0.0
    max_drawdown_last: float = 0.0
    breach_ratio_last: float = 0.0
    
    # 最近 3 個 window 的平均值
    avg_sharpe_3: float = 0.0
    avg_breach_ratio_3: float = 0.0
    
    # 最近 5 個 window 的平均值
    avg_sharpe_5: float = 0.0
    avg_breach_ratio_5: float = 0.0
    
    # 當前治理參數
    current_sharpe_floor: float = 0.0
    current_max_drawdown_limit: float = 0.0
    current_turnover_limit: float = 0.0
    current_te_max: float = 0.0
    
    # Mode ID: 0 = basic, 1 = extreme
    mode_id: int = 0


@dataclass
class PathDAction:
    """
    Path D RL 動作空間
    
    對治理參數的調整量（delta）。
    """
    
    # 對各參數的調整量
    delta_sharpe_floor: float = 0.0
    delta_max_drawdown_limit: float = 0.0
    delta_turnover_limit: float = 0.0
    delta_te_max: float = 0.0
    
    # Mode 傾向：>0 傾向 extreme, <0 傾向 basic
    delta_mode_logit: float = 0.0


@dataclass
class Transition:
    """
    RL 轉換記錄
    
    用於儲存 (state, action, reward, next_state, done) 的經驗。
    """
    
    state: np.ndarray
    action: np.ndarray
    reward: float
    next_state: np.ndarray
    done: bool


@dataclass
class PathDTrainConfig:
    """
    Path D 訓練配置
    """
    
    experiment_name: str
    data_source: Literal["mock", "finmind"]
    mode: Literal["basic", "extreme"]
    
    # 用來生成 PathBConfig 的基礎參數
    base_path_b_config: Dict[str, Any]
    
    # RL 訓練參數
    episodes: int = 100
    max_steps_per_episode: int = 10
    gamma: float = 0.99
    learning_rate: float = 0.001
    seed: int = 42


@dataclass
class PathDRunConfig:
    """
    Path D 評估配置
    """
    
    experiment_name: str
    data_source: Literal["mock", "finmind"]
    mode: Literal["basic", "extreme"]
    
    # 用來生成 PathBConfig 的基礎參數
    base_path_b_config: Dict[str, Any]
    
    # 評估參數
    eval_episodes: int = 5
    max_steps_per_episode: int = 10
    
    # 載入的 policy 路徑
    policy_path: Optional[str] = None


@dataclass
class PathDTrainResult:
    """
    Path D 訓練結果
    """
    
    config: PathDTrainConfig
    episode_rewards: List[float] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    best_policy_path: Optional[str] = None


@dataclass
class PathDRunResult:
    """
    Path D 評估結果
    """
    
    config: PathDRunConfig
    episode_rewards: List[float] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)

