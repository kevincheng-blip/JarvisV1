"""
Risk Config Loader

Utility functions for loading RiskConfig from YAML files.

設計原則：
- 不依賴 PyYAML（使用純文字解析，簡單 YAML 格式）
- 支援 policy/risk_config_suggested_v1.yaml 格式
- 返回簡單的 dict，供 DecisionEngineV1 使用
"""

import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def load_risk_config(path: str) -> Optional[Dict]:
    """
    從 YAML 檔案載入 RiskConfig
    
    支援的 YAML 格式：
    ```yaml
    config:
      long_budget: 0.60
      short_budget: 0.20
      max_weight_per_symbol: 0.10
      min_score: 0.00
      allow_short: true
    ```
    
    Args:
        path: YAML 檔案路徑
    
    Returns:
        Dict: RiskConfig 參數字典，如果載入失敗則回傳 None
    
    Raises:
        FileNotFoundError: 如果檔案不存在
    """
    config_path = Path(path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"RiskConfig file not found: {path}")
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 簡單的 YAML 解析（不依賴 PyYAML）
        # 尋找 config: 區塊
        config_dict = {}
        
        in_config_section = False
        for line in content.splitlines():
            line = line.strip()
            
            # 跳過註解和空行
            if not line or line.startswith("#"):
                continue
            
            # 檢查是否進入 config 區塊
            if line.startswith("config:"):
                in_config_section = True
                continue
            
            # 如果在 config 區塊內，解析鍵值對
            if in_config_section:
                # 檢查是否離開 config 區塊（遇到新的頂層鍵）
                if line and not line[0].isspace() and ":" in line:
                    # 這是新的頂層鍵，離開 config 區塊
                    break
                
                # 解析鍵值對（例如 "  long_budget: 0.60"）
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value_str = parts[1].strip()
                        
                        # 轉換值
                        if value_str.lower() in ["true", "yes"]:
                            value = True
                        elif value_str.lower() in ["false", "no"]:
                            value = False
                        else:
                            try:
                                # 嘗試轉換為 float
                                value = float(value_str)
                            except ValueError:
                                # 保持字串
                                value = value_str
                        
                        config_dict[key] = value
        
        if not config_dict:
            logger.warning(f"No config parameters found in {path}")
            return None
        
        logger.info(f"RiskConfig loaded from YAML: {path}")
        logger.debug(f"Loaded config: {config_dict}")
        
        return config_dict
    
    except Exception as e:
        logger.error(f"Failed to load RiskConfig from {path}: {e}")
        return None

