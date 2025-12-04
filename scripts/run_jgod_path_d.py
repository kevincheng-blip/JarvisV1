#!/usr/bin/env python3
"""
Path D CLI

執行 Path D RL Engine 的訓練和評估。

Usage:
    # Training
    PYTHONPATH=. python3 scripts/run_jgod_path_d.py train \
        --name my_experiment \
        --config configs/path_d/train_config.json \
        --output-dir output/path_d

    # Evaluation
    PYTHONPATH=. python3 scripts/run_jgod_path_d.py eval \
        --name my_experiment \
        --config configs/path_d/eval_config.json \
        --policy-path models/path_d/my_experiment/best_policy.npz \
        --output-dir output/path_d
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from jgod.path_d.path_d_engine import PathDEngine
from jgod.path_d.path_d_types import (
    PathDTrainConfig,
    PathDRunConfig,
)


def load_train_config(json_path: str) -> Dict[str, Any]:
    """載入訓練配置 JSON"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_eval_config(json_path: str) -> Dict[str, Any]:
    """載入評估配置 JSON"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_default_train_config() -> Dict[str, Any]:
    """取得預設訓練配置"""
    return {
        "experiment_name": "path_d_default",
        "data_source": "mock",
        "mode": "basic",
        "base_path_b_config": {
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
        },
        "episodes": 10,
        "max_steps_per_episode": 5,
        "gamma": 0.99,
        "learning_rate": 0.001,
        "seed": 42,
    }


def parse_args():
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description="Path D RL Engine CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Train 子命令
    train_parser = subparsers.add_parser("train", help="Train Path D RL Agent")
    train_parser.add_argument("--name", required=True, help="Experiment name")
    train_parser.add_argument("--config", help="Path to config JSON file (optional)")
    train_parser.add_argument("--output-dir", default="output/path_d", help="Output directory")
    
    # Eval 子命令
    eval_parser = subparsers.add_parser("eval", help="Evaluate trained Path D RL Agent")
    eval_parser.add_argument("--name", required=True, help="Experiment name")
    eval_parser.add_argument("--config", help="Path to config JSON file (optional)")
    eval_parser.add_argument("--policy-path", required=True, help="Path to trained policy file (.npz)")
    eval_parser.add_argument("--output-dir", default="output/path_d", help="Output directory")
    
    return parser.parse_args()


def main():
    """主函數"""
    args = parse_args()
    
    if args.command == "train":
        # 載入配置
        if args.config:
            config_dict = load_train_config(args.config)
        else:
            config_dict = get_default_train_config()
            print("Using default config (use --config to specify custom config)")
        
        config_dict["experiment_name"] = args.name
        
        # 建立配置物件
        config = PathDTrainConfig(**config_dict)
        
        # 執行訓練
        engine = PathDEngine()
        result = engine.train(config)
        
        # 輸出結果
        output_dir = Path(args.output_dir) / args.name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 儲存訓練結果 JSON
        result_json = {
            "experiment_name": result.config.experiment_name,
            "episode_rewards": result.episode_rewards,
            "metrics": result.metrics,
            "best_policy_path": result.best_policy_path,
        }
        
        result_path = output_dir / "train_result.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, indent=2)
        
        print(f"\n=== Training Completed ===")
        print(f"Experiment: {result.config.experiment_name}")
        print(f"Episodes: {len(result.episode_rewards)}")
        print(f"Best reward: {result.metrics.get('best_reward', 0.0):.2f}")
        print(f"Avg reward: {result.metrics.get('avg_reward', 0.0):.2f}")
        print(f"Best policy: {result.best_policy_path}")
        print(f"Results saved to: {result_path}")
    
    elif args.command == "eval":
        # 載入配置
        if args.config:
            with open(args.config, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
        else:
            # 使用預設配置
            config_dict = get_default_train_config().copy()
            print("Using default config (use --config to specify custom config)")
        
        # 移除訓練專用欄位，避免 PathDRunConfig 收到不認得的 key
        TRAIN_ONLY_FIELDS = [
            "episodes",
            "max_steps_per_episode",
            "gamma",
            "learning_rate",
            "seed",
        ]
        for field in TRAIN_ONLY_FIELDS:
            config_dict.pop(field, None)
        
        config_dict["experiment_name"] = args.name
        config_dict["policy_path"] = args.policy_path
        
        # 建立配置物件
        config = PathDRunConfig(**config_dict)
        
        # 執行評估
        engine = PathDEngine()
        result = engine.evaluate(config)
        
        # 輸出結果
        output_dir = Path(args.output_dir) / args.name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 儲存評估結果 JSON
        result_json = {
            "experiment_name": result.config.experiment_name,
            "episode_rewards": result.episode_rewards,
            "metrics": result.metrics,
        }
        
        result_path = output_dir / "eval_result.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, indent=2)
        
        print(f"\n=== Evaluation Completed ===")
        print(f"Experiment: {result.config.experiment_name}")
        print(f"Episodes: {len(result.episode_rewards)}")
        print(f"Avg reward: {sum(result.episode_rewards) / len(result.episode_rewards):.2f}")
        print(f"Metrics: {result.metrics}")
        print(f"Results saved to: {result_path}")
    
    else:
        print("Error: Please specify a command (train or eval)")
        sys.exit(1)


if __name__ == "__main__":
    main()

