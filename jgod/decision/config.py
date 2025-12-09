"""
Decision Layer v1 - Configuration

定義 Decision Layer 的設定參數
"""

from dataclasses import dataclass


@dataclass
class DecisionConfig:
    """Decision Layer 配置"""
    llm_model: str = "gpt-4o-mini"  # 預設模型
    max_correction: float = 1.5      # 最大修正係數
    min_correction: float = 0.5      # 最小修正係數
    doctrine_top_k: int = 5          # Doctrine 查詢數量
    enable_doctrine: bool = True     # 是否啟用 Doctrine 查詢
    enable_llm: bool = True          # 是否啟用 LLM 仲裁
    llm_timeout: int = 30            # LLM 呼叫超時（秒）
    llm_max_retries: int = 2         # LLM 最大重試次數
    fallback_correction_factor: float = 1.0  # LLM 失敗時的 fallback 係數

