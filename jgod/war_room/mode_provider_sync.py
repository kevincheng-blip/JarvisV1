"""
Mode 與 Provider 同步邏輯
"""
from typing import List, Dict, Tuple
import streamlit as st


# Mode 對應的預設 Provider（內部鍵值）
MODE_PROVIDER_MAP: Dict[str, List[str]] = {
    "Lite": ["gpt"],
    "Pro": ["gpt", "claude"],
    "God": ["gpt", "claude", "gemini", "perplexity"],
    "Custom": [],  # Custom 模式不自動設定
}

# Mode 對應的預設 Provider（顯示名稱）
MODE_PROVIDER_DISPLAY_MAP: Dict[str, List[str]] = {
    "Lite": ["GPT-4o-mini"],
    "Pro": ["GPT-4o-mini", "Claude 3.5 Haiku"],
    "God": ["GPT-4o-mini", "Claude 3.5 Haiku", "Gemini Flash 2.5", "Perplexity Sonar"],
    "Custom": [],  # Custom 模式不自動設定
}

# Provider 顯示名稱到內部鍵值的映射
PROVIDER_DISPLAY_TO_KEY = {
    "GPT-4o-mini": "gpt",
    "Claude 3.5 Haiku": "claude",
    "Gemini Flash 2.5": "gemini",
    "Perplexity Sonar": "perplexity",
}

# Provider 內部鍵值到顯示名稱的映射
PROVIDER_KEY_TO_DISPLAY = {v: k for k, v in PROVIDER_DISPLAY_TO_KEY.items()}


def set_mode_and_providers(mode: str) -> None:
    """
    設定 Mode 並同步更新 Provider 選擇（自動同步）
    
    Args:
        mode: 模式名稱（Lite / Pro / God / Custom）
    """
    # 更新統一的 session state keys
    st.session_state["mode"] = mode
    st.session_state["last_mode"] = mode
    
    # 如果不是 Custom 模式，自動設定 Provider
    if mode != "Custom":
        # 使用顯示名稱列表（用於 UI）
        default_providers_display = MODE_PROVIDER_DISPLAY_MAP.get(mode, ["GPT-4o-mini"])
        st.session_state["enabled_providers"] = default_providers_display
        
        # 清除 multiselect 的 key，強制重新渲染
        if "provider_multiselect" in st.session_state:
            del st.session_state.provider_multiselect
    # Custom 模式：保留使用者選擇，不自動更新


def get_final_enabled_providers(mode: str) -> List[str]:
    """
    根據 Mode 取得最終要執行的 Provider 內部鍵值列表
    
    Args:
        mode: 當前模式
    
    Returns:
        Provider 內部鍵值列表（例如：['gpt', 'claude', 'gemini', 'perplexity']）
    """
    # 若 mode != "Custom"，強制使用 MODE_PROVIDER_MAP[mode]
    if mode != "Custom":
        return MODE_PROVIDER_MAP.get(mode, ["gpt"])
    
    # Custom 模式：使用 session state 中的選擇
    selected_providers_ui = st.session_state.get("enabled_providers", ["GPT-4o-mini"])
    return get_enabled_provider_keys(selected_providers_ui)


def get_enabled_provider_keys(selected_providers: List[str]) -> List[str]:
    """
    從選中的 Provider 顯示名稱轉換為內部鍵值
    
    Args:
        selected_providers: 選中的 Provider 顯示名稱列表
    
    Returns:
        Provider 內部鍵值列表
    """
    return [
        PROVIDER_DISPLAY_TO_KEY[p]
        for p in selected_providers
        if p in PROVIDER_DISPLAY_TO_KEY
    ]


def get_provider_display_names(provider_keys: List[str]) -> List[str]:
    """
    從 Provider 內部鍵值轉換為顯示名稱
    
    Args:
        provider_keys: Provider 內部鍵值列表
    
    Returns:
        Provider 顯示名稱列表
    """
    return [
        PROVIDER_KEY_TO_DISPLAY[k]
        for k in provider_keys
        if k in PROVIDER_KEY_TO_DISPLAY
    ]


def get_enabled_providers() -> List[str]:
    """
    從 session state 取得啟用的 Provider 內部鍵值列表
    
    Returns:
        Provider 內部鍵值列表（例如：['gpt', 'claude', 'gemini', 'perplexity']）
    """
    # 從 session state 取得 mode 和 selected_providers
    mode = st.session_state.get("mode", "Lite")
    selected_providers_ui = st.session_state.get("enabled_providers", [])
    
    # 如果 UI 沒有選擇，使用 Mode 預設值
    if not selected_providers_ui and mode != "Custom":
        selected_providers_ui = MODE_PROVIDER_MAP.get(mode, ["GPT-4o-mini"])
    
    # 如果還是空的，至少使用 GPT
    if not selected_providers_ui:
        selected_providers_ui = ["GPT-4o-mini"]
    
    # 轉換為內部鍵值
    provider_keys = get_enabled_provider_keys(selected_providers_ui)
    
    # 如果轉換後為空，至少使用 GPT
    if not provider_keys:
        provider_keys = ["gpt"]
    
    return provider_keys


def get_final_providers(mode: str, selected_providers: List[str]) -> Tuple[List[str], List[str]]:
    """
    計算最終要執行的 Provider 列表
    
    Args:
        mode: 當前模式
        selected_providers: UI 選中的 Provider 顯示名稱列表
    
    Returns:
        (Provider 顯示名稱列表, Provider 內部鍵值列表)
    """
    # 若 mode != "Custom"，強制使用 MODE_PROVIDER_MAP[mode]
    if mode != "Custom":
        provider_keys = MODE_PROVIDER_MAP.get(mode, ["gpt"])
        provider_display = MODE_PROVIDER_DISPLAY_MAP.get(mode, ["GPT-4o-mini"])
        return provider_display, provider_keys
    
    # Custom 模式：使用 session state 中的選擇
    if not selected_providers:
        selected_providers = ["GPT-4o-mini"]
    
    # 轉換為內部鍵值
    provider_keys = get_enabled_provider_keys(selected_providers)
    
    # 如果轉換後為空，至少使用 GPT
    if not provider_keys:
        provider_keys = ["gpt"]
        selected_providers = ["GPT-4o-mini"]
    
    return selected_providers, provider_keys

