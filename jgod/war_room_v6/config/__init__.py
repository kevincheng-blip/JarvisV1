"""
War Room v6 設定模組
重用 v5 的角色與 Provider 設定
"""
# 直接從 v5 的設定模組匯入（避免重複定義）
from jgod.war_room.config.roles import (
    ROLE_PROVIDER_MAP,
    ROLE_CHINESE_NAMES,
    ROLE_TASKS,
    ROLE_SYSTEM_PROMPTS,
    MODE_PROVIDER_MAP,
    PROVIDER_DISPLAY_NAMES,
    PROVIDER_CHINESE_NAMES,
    ProviderKey,
)

__all__ = [
    "ROLE_PROVIDER_MAP",
    "ROLE_CHINESE_NAMES",
    "ROLE_TASKS",
    "ROLE_SYSTEM_PROMPTS",
    "MODE_PROVIDER_MAP",
    "PROVIDER_DISPLAY_NAMES",
    "PROVIDER_CHINESE_NAMES",
    "ProviderKey",
]

