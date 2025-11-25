"""
War Room Engine v4.0 - 共用型別定義
"""
from dataclasses import dataclass
from typing import Literal, Dict, List, Optional
from enum import Enum


# Provider 內部鍵值
ProviderKey = Literal["gpt", "claude", "gemini", "perplexity"]


# 角色名稱
class RoleName(str, Enum):
    """戰情室角色名稱"""
    INTEL_OFFICER = "Intel Officer"
    SCOUT = "Scout"
    RISK_OFFICER = "Risk Officer"
    QUANT_LEAD = "Quant Lead"
    STRATEGIST = "Strategist"
    EXECUTION_OFFICER = "Execution Officer"


# 角色到 Provider 的映射
ROLE_PROVIDER_MAP: Dict[RoleName, ProviderKey] = {
    RoleName.INTEL_OFFICER: "perplexity",
    RoleName.SCOUT: "gemini",
    RoleName.RISK_OFFICER: "claude",
    RoleName.QUANT_LEAD: "claude",
    RoleName.STRATEGIST: "gpt",
    RoleName.EXECUTION_OFFICER: "gpt",
}

# 角色系統提示
ROLE_SYSTEM_PROMPTS: Dict[RoleName, str] = {
    RoleName.INTEL_OFFICER: "你是 J-GOD 戰情室的情報官（Intel Officer），負責蒐集與整理市場資訊。",
    RoleName.SCOUT: "你是 J-GOD 戰情室的偵察兵（Scout），負責快速摘要與輔助分析。",
    RoleName.RISK_OFFICER: "你是 J-GOD 戰情室的風險官（Risk Officer），負責評估風險與提供風險建議。",
    RoleName.QUANT_LEAD: "你是 J-GOD 戰情室的量化主管（Quant Lead），負責技術分析與量化策略。",
    RoleName.STRATEGIST: "你是 J-GOD 戰情室的策略師（Strategist），負責統整所有意見並給出最終建議。",
    RoleName.EXECUTION_OFFICER: "你是 J-GOD 戰情室的執行官（Execution Officer），負責提供具體操作建議。",
}

# Mode 對應 Provider
MODE_PROVIDER_MAP: Dict[str, List[ProviderKey]] = {
    "Lite": ["gpt"],
    "Pro": ["gpt", "claude"],
    "God": ["gpt", "claude", "gemini", "perplexity"],
    "Custom": [],  # Custom 由 UI 決定 enabled_providers
}


@dataclass
class RoleResult:
    """單一角色的執行結果"""
    role: RoleName
    provider_key: ProviderKey
    success: bool
    content: str
    error: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class WarRoomResult:
    """War Room 完整執行結果"""
    results: Dict[RoleName, RoleResult]
    executed_roles: List[RoleName]
    failed_roles: List[RoleName]
    
    def __post_init__(self):
        """自動計算 executed_roles 和 failed_roles"""
        if not self.executed_roles:
            self.executed_roles = list(self.results.keys())
        if not self.failed_roles:
            self.failed_roles = [
                role for role, result in self.results.items()
                if not result.success
            ]

