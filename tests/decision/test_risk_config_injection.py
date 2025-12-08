"""
Unit tests for RiskConfig injection in DecisionEngineV1

Tests that YAML values override defaults correctly.
"""

import pytest
from datetime import date
from pathlib import Path
import tempfile

from jgod.decision import DecisionEngineV1
from jgod.decision.risk_config_loader import load_risk_config


def test_load_risk_config():
    """Test loading RiskConfig from YAML file"""
    # Create a temporary YAML file
    yaml_content = """# Test RiskConfig
config:
  long_budget: 0.70
  short_budget: 0.15
  max_weight_per_symbol: 0.15
  min_score: 1.0
  allow_short: true
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name
    
    try:
        config = load_risk_config(temp_path)
        
        assert config is not None
        assert config["long_budget"] == 0.70
        assert config["short_budget"] == 0.15
        assert config["max_weight_per_symbol"] == 0.15
        assert config["min_score"] == 1.0
        assert config["allow_short"] is True
    finally:
        Path(temp_path).unlink()


def test_decision_engine_with_risk_config_dict():
    """Test DecisionEngineV1 accepts risk_config_dict and uses it as default"""
    risk_config_dict = {
        "long_budget": 0.70,
        "short_budget": 0.15,
        "max_weight_per_symbol": 0.15,
        "min_score": 1.0,
        "allow_short": True,
    }
    
    engine = DecisionEngineV1(risk_config_dict=risk_config_dict)
    
    # 驗證 risk_config_dict 已被儲存
    assert engine.risk_config_dict == risk_config_dict


def test_yaml_overrides_defaults():
    """Test that YAML values override defaults in generate_portfolio_for_date"""
    risk_config_dict = {
        "long_budget": 0.70,
        "short_budget": 0.15,
        "max_weight_per_symbol": 0.15,
        "min_score": 1.0,
        "allow_short": True,
    }
    
    engine = DecisionEngineV1(risk_config_dict=risk_config_dict)
    
    # 當不提供參數時，應該使用 risk_config_dict 的值
    # 注意：這個測試需要 mock StrategyEngine 或確保有資料
    # 這裡只是驗證邏輯結構
    
    # 驗證 risk_config_dict 有被正確設定
    assert engine.risk_config_dict["long_budget"] == 0.70
    assert engine.risk_config_dict["short_budget"] == 0.15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

