"""
War Room Engine v5.0 - 共用型別定義
注意：角色與 Provider 設定已移至 jgod/war_room/config/roles.py
"""
from dataclasses import dataclass
from typing import Literal, Dict, List, Optional
from enum import Enum

# 從集中設定模組匯入
from jgod.war_room.config.roles import (
    ROLE_PROVIDER_MAP as CONFIG_ROLE_PROVIDER_MAP,
    ROLE_SYSTEM_PROMPTS as CONFIG_ROLE_SYSTEM_PROMPTS,
    MODE_PROVIDER_MAP as CONFIG_MODE_PROVIDER_MAP,
    ProviderKey,  # 直接使用集中設定的 ProviderKey
)


# 角色名稱
class RoleName(str, Enum):
    """戰情室角色名稱"""
    INTEL_OFFICER = "Intel Officer"
    SCOUT = "Scout"
    RISK_OFFICER = "Risk Officer"
    QUANT_LEAD = "Quant Lead"
    STRATEGIST = "Strategist"
    EXECUTION_OFFICER = "Execution Officer"


# 角色到 Provider 的映射（從集中設定匯入）
ROLE_PROVIDER_MAP: Dict[RoleName, ProviderKey] = {
    RoleName.INTEL_OFFICER: CONFIG_ROLE_PROVIDER_MAP["Intel Officer"],
    RoleName.SCOUT: CONFIG_ROLE_PROVIDER_MAP["Scout"],
    RoleName.RISK_OFFICER: CONFIG_ROLE_PROVIDER_MAP["Risk Officer"],
    RoleName.QUANT_LEAD: CONFIG_ROLE_PROVIDER_MAP["Quant Lead"],
    RoleName.STRATEGIST: CONFIG_ROLE_PROVIDER_MAP["Strategist"],
    RoleName.EXECUTION_OFFICER: CONFIG_ROLE_PROVIDER_MAP["Execution Officer"],
}

# 角色系統提示（從集中設定匯入）
ROLE_SYSTEM_PROMPTS: Dict[RoleName, str] = {
    RoleName.INTEL_OFFICER: CONFIG_ROLE_SYSTEM_PROMPTS["Intel Officer"],
    RoleName.SCOUT: CONFIG_ROLE_SYSTEM_PROMPTS["Scout"],
    RoleName.RISK_OFFICER: CONFIG_ROLE_SYSTEM_PROMPTS["Risk Officer"],
    RoleName.QUANT_LEAD: CONFIG_ROLE_SYSTEM_PROMPTS["Quant Lead"],
    RoleName.STRATEGIST: CONFIG_ROLE_SYSTEM_PROMPTS["Strategist"],
    RoleName.EXECUTION_OFFICER: CONFIG_ROLE_SYSTEM_PROMPTS["Execution Officer"],
}

# Mode 對應 Provider（從集中設定匯入）
MODE_PROVIDER_MAP: Dict[str, List[ProviderKey]] = CONFIG_MODE_PROVIDER_MAP


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

