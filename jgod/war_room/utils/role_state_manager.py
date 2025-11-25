"""
角色狀態管理器 - v4.2
用於管理戰情室角色的狀態（pending / running / done / error）
"""
import time
from typing import Dict, Optional
from datetime import datetime
import streamlit as st


# 角色到 Provider 的映射
ROLE_PROVIDER_MAP = {
    "Intel Officer": "perplexity",
    "Scout": "gemini",
    "Risk Officer": "claude",
    "Quant Lead": "claude",
    "Strategist": "gpt",
    "Execution Officer": "gpt",
}

# 角色中文名稱映射
ROLE_CHINESE_NAMES = {
    "Intel Officer": "情報官",
    "Scout": "斥候",
    "Risk Officer": "風控長",
    "Quant Lead": "量化長",
    "Strategist": "策略統整",
    "Execution Officer": "執行官",
}


def initialize_roles_state(enabled_providers: list) -> Dict[str, Dict]:
    """
    初始化角色狀態
    
    Args:
        enabled_providers: 啟用的 Provider 列表（例如：['gpt', 'claude', 'gemini', 'perplexity']）
    
    Returns:
        角色狀態字典
    """
    roles_state = {}
    
    for role_name, provider_key in ROLE_PROVIDER_MAP.items():
        if provider_key in enabled_providers:
            roles_state[role_name] = {
                "role_key": role_name.lower().replace(" ", "_"),
                "provider": provider_key,
                "status": "pending",
                "content": "",
                "error_message": None,
                "started_at": None,
                "finished_at": None,
                "execution_time": 0.0,
            }
    
    return roles_state


def update_role_state(role_name: str, field: str, value) -> None:
    """
    更新角色狀態的特定欄位
    
    Args:
        role_name: 角色名稱
        field: 欄位名稱
        value: 新值
    """
    if "war_room_roles" not in st.session_state:
        st.session_state["war_room_roles"] = {}
    
    if role_name not in st.session_state["war_room_roles"]:
        st.session_state["war_room_roles"][role_name] = {
            "role_key": role_name.lower().replace(" ", "_"),
            "provider": "",
            "status": "pending",
            "content": "",
            "error_message": None,
            "started_at": None,
            "finished_at": None,
            "execution_time": 0.0,
        }
    
    st.session_state["war_room_roles"][role_name][field] = value


def append_role_content(role_name: str, new_text: str) -> None:
    """
    追加角色內容（用於 streaming）
    
    Args:
        role_name: 角色名稱
        new_text: 新文字
    """
    if "war_room_roles" not in st.session_state:
        st.session_state["war_room_roles"] = {}
    
    if role_name not in st.session_state["war_room_roles"]:
        update_role_state(role_name, "status", "running")
        update_role_state(role_name, "started_at", datetime.now().isoformat())
    
    role_state = st.session_state["war_room_roles"][role_name]
    
    # 如果是第一次收到內容，標記為 running
    if role_state["status"] == "pending":
        role_state["status"] = "running"
        role_state["started_at"] = datetime.now().isoformat()
    
    # 追加內容
    role_state["content"] += new_text
    st.session_state["war_room_roles"][role_name] = role_state


def mark_role_done(role_name: str, success: bool = True, error_message: Optional[str] = None) -> None:
    """
    標記角色為完成
    
    Args:
        role_name: 角色名稱
        success: 是否成功
        error_message: 錯誤訊息（如果有）
    """
    if "war_room_roles" not in st.session_state:
        return
    
    if role_name not in st.session_state["war_room_roles"]:
        return
    
    role_state = st.session_state["war_room_roles"][role_name]
    role_state["status"] = "done" if success else "error"
    role_state["finished_at"] = datetime.now().isoformat()
    
    if error_message:
        role_state["error_message"] = error_message
    
    # 計算執行時間
    if role_state["started_at"]:
        try:
            started = datetime.fromisoformat(role_state["started_at"])
            finished = datetime.fromisoformat(role_state["finished_at"])
            role_state["execution_time"] = (finished - started).total_seconds()
        except Exception:
            pass
    
    st.session_state["war_room_roles"][role_name] = role_state


def get_role_state(role_name: str) -> Optional[Dict]:
    """
    取得角色狀態
    
    Args:
        role_name: 角色名稱
    
    Returns:
        角色狀態字典，如果不存在則返回 None
    """
    if "war_room_roles" not in st.session_state:
        return None
    
    return st.session_state["war_room_roles"].get(role_name)


def get_all_roles_state() -> Dict[str, Dict]:
    """
    取得所有角色狀態
    
    Returns:
        所有角色狀態字典
    """
    if "war_room_roles" not in st.session_state:
        return {}
    
    return st.session_state["war_room_roles"]

