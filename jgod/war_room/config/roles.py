"""
角色與 Provider 設定 - 集中管理
供 Streamlit 與 FastAPI 共用
"""
from typing import Dict, List, Literal

# 角色到 Provider 的映射
ROLE_PROVIDER_MAP: Dict[str, str] = {
    "Intel Officer": "perplexity",
    "Scout": "gemini",
    "Risk Officer": "claude",
    "Quant Lead": "claude",
    "Strategist": "gpt",
    "Execution Officer": "gpt",
}

# 角色中文名稱映射
ROLE_CHINESE_NAMES: Dict[str, str] = {
    "Intel Officer": "情報官",
    "Scout": "斥候",
    "Risk Officer": "風控長",
    "Quant Lead": "量化長",
    "Strategist": "策略統整",
    "Execution Officer": "執行官",
}

# 角色任務描述
ROLE_TASKS: Dict[str, str] = {
    "Intel Officer": "市場資訊蒐集",
    "Scout": "快速偵查分析",
    "Risk Officer": "風險評估",
    "Quant Lead": "量化技術分析",
    "Strategist": "統整決策建議",
    "Execution Officer": "執行策略",
}

# Provider 內部鍵值
ProviderKey = Literal["gpt", "claude", "gemini", "perplexity"]

# 模式到 Provider 列表的映射
MODE_PROVIDER_MAP: Dict[str, List[ProviderKey]] = {
    "Lite": ["gpt"],
    "Pro": ["gpt", "claude"],
    "God": ["gpt", "claude", "gemini", "perplexity"],
    "Custom": [],  # Custom 由 UI 決定 enabled_providers
}

# Provider 顯示名稱映射
PROVIDER_DISPLAY_NAMES: Dict[str, str] = {
    "gpt": "GPT-4o-mini",
    "claude": "Claude 3.5 Haiku",
    "gemini": "Gemini Flash 2.5",
    "perplexity": "Perplexity Sonar",
}

# Provider 中文名稱映射
PROVIDER_CHINESE_NAMES: Dict[str, str] = {
    "gpt": "GPT",
    "claude": "Claude",
    "gemini": "Gemini",
    "perplexity": "Perplexity",
}

# 角色系統提示範本
ROLE_SYSTEM_PROMPTS: Dict[str, str] = {
    "Intel Officer": "你是 J-GOD 戰情室的情報官（Intel Officer），負責蒐集與整理市場資訊。",
    "Scout": "你是 J-GOD 戰情室的偵察兵（Scout），負責快速摘要與輔助分析。",
    "Risk Officer": "你是 J-GOD 戰情室的風險官（Risk Officer），負責評估風險與提供風險建議。",
    "Quant Lead": "你是 J-GOD 戰情室的量化主管（Quant Lead），負責技術分析與量化策略。",
    "Strategist": "你是 J-GOD 戰情室的策略師（Strategist），負責統整所有意見並給出最終建議。",
    "Execution Officer": "你是 J-GOD 戰情室的執行官（Execution Officer），負責提供具體操作建議。",
}

