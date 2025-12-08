"""
Experiment Config Loader

Utility for loading Path A experiment configuration from JSON/YAML files.

設計原則：
- 支援 JSON 格式（標準庫，無需額外依賴）
- 簡單的 YAML 解析（可選，不依賴 PyYAML）
- 清晰的錯誤訊息
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def load_experiment_config(path: str) -> Dict:
    """
    載入實驗配置檔
    
    支援格式：
    - JSON (.json)
    - YAML (.yaml, .yml) - 使用簡易 parser
    
    Args:
        path: 配置檔路徑
    
    Returns:
        Dict: 配置字典
    
    Raises:
        FileNotFoundError: 如果檔案不存在
        ValueError: 如果格式不正確
    """
    config_path = Path(path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Experiment config file not found: {path}")
    
    # 根據副檔名選擇解析方式
    suffix = config_path.suffix.lower()
    
    if suffix == ".json":
        return _load_json_config(config_path)
    elif suffix in [".yaml", ".yml"]:
        return _load_yaml_config(config_path)
    else:
        raise ValueError(f"Unsupported config file format: {suffix}. Use .json or .yaml")
    
    return config


def _load_json_config(path: Path) -> Dict:
    """載入 JSON 配置檔"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 驗證必要欄位
        _validate_config(config)
        
        logger.info(f"Experiment config loaded from JSON: {path}")
        return config
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {path}: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load JSON config from {path}: {e}")


def _load_yaml_config(path: Path) -> Dict:
    """載入 YAML 配置檔（使用簡易 parser）"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 使用簡易 YAML parser
        config = _parse_simple_yaml(content)
        
        # 驗證必要欄位
        _validate_config(config)
        
        logger.info(f"Experiment config loaded from YAML: {path}")
        return config
    
    except Exception as e:
        raise ValueError(f"Failed to load YAML config from {path}: {e}")


def _parse_simple_yaml(content: str) -> Dict:
    """
    簡易 YAML parser
    
    只支援基本的 dict + list 結構，符合我們的需求。
    """
    config = {}
    lines = content.splitlines()
    
    i = 0
    current_list = None
    current_dict = None
    
    while i < len(lines):
        line = lines[i].rstrip()
        
        # 跳過空行和註解
        if not line or line.strip().startswith("#"):
            i += 1
            continue
        
        # 解析鍵值對
        if ":" in line and not line.strip().startswith("-"):
            indent = len(line) - len(line.lstrip())
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            # 處理值
            if value == "":
                # 可能是列表或字典的開始
                i += 1
                # 檢查下一行
                if i < len(lines):
                    next_line = lines[i].strip()
                    if next_line.startswith("-"):
                        # 是列表
                        config[key] = []
                        current_list = config[key]
                        current_dict = None
                    else:
                        # 是字典
                        config[key] = {}
                        current_dict = config[key]
                        current_list = None
                continue
            
            # 轉換值類型
            parsed_value = _parse_value(value)
            
            if current_dict is not None:
                current_dict[key] = parsed_value
            else:
                config[key] = parsed_value
        
        # 解析列表項
        elif line.strip().startswith("-"):
            if current_list is None:
                raise ValueError(f"List item found but no list context at line {i+1}")
            
            item_line = line.strip()[1:].strip()
            if ":" in item_line:
                # 列表中的字典項
                if current_dict is None:
                    current_dict = {}
                    current_list.append(current_dict)
                
                key, value = item_line.split(":", 1)
                key = key.strip()
                value = value.strip()
                current_dict[key] = _parse_value(value)
            else:
                # 簡單列表項
                current_list.append(_parse_value(item_line))
                current_dict = None
        
        i += 1
    
    return config


def _parse_value(value: str):
    """解析 YAML 值（字串、數字、布林值）"""
    value = value.strip()
    
    # 移除引號
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    
    # 布林值
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    
    # 數字
    try:
        if "." in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        pass
    
    # 字串
    return value


def _validate_config(config: Dict):
    """驗證配置檔格式"""
    required_top_level = ["start_date", "end_date", "capital", "experiments"]
    for key in required_top_level:
        if key not in config:
            raise ValueError(f"Missing required top-level key: {key}")
    
    if not isinstance(config["experiments"], list):
        raise ValueError("'experiments' must be a list")
    
    required_experiment_keys = [
        "name", "long_budget", "short_budget",
        "max_weight_per_symbol", "min_score", "allow_short"
    ]
    
    for i, exp in enumerate(config["experiments"]):
        if not isinstance(exp, dict):
            raise ValueError(f"Experiment {i} must be a dict")
        
        for key in required_experiment_keys:
            if key not in exp:
                raise ValueError(f"Missing required key '{key}' in experiment {i}")

