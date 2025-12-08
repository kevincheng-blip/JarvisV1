"""
聊天室面板：管理所有角色的聊天室風格顯示
"""
import streamlit as st
from typing import Dict, Optional, Callable
import time

from jgod.council_chamber.providers.base_provider import ProviderResult
from jgod.council_chamber.ui.role_panel import RolePanel


class ChatroomPanel:
    """聊天室面板：管理所有角色的聊天室風格顯示"""
    
    def __init__(self):
        self.role_panel = RolePanel()
        # 用於儲存 streaming 內容
        if "streaming_contents" not in st.session_state:
            st.session_state.streaming_contents = {}
    
    def render_all_roles(
        self,
        role_results: Dict[str, ProviderResult],
        is_loading: bool = False,
        enabled_roles: Optional[list] = None,
    ) -> None:
        """
        渲染所有角色的卡片
        
        Args:
            role_results: 角色結果字典
            is_loading: 是否正在載入
            enabled_roles: 啟用的角色列表
        """
        # 角色配置
        role_configs = [
            ("Intel Officer", "Perplexity Sonar"),
            ("Scout", "Gemini Flash 2.5"),
            ("Risk Officer", "Claude 3.5 Haiku"),
            ("Quant Lead", "Claude 3.5 Haiku"),
        ]
        
        # 第一行：Intel Officer, Scout
        col1, col2 = st.columns(2)
        
        with col1:
            role_name, provider_name = role_configs[0]
            result = role_results.get(role_name)
            streaming_content = st.session_state.streaming_contents.get(role_name)
            loading = is_loading and result is None
            self.role_panel.render_role_card(
                role_name, provider_name, result, loading, streaming_content
            )
        
        with col2:
            role_name, provider_name = role_configs[1]
            result = role_results.get(role_name)
            streaming_content = st.session_state.streaming_contents.get(role_name)
            loading = is_loading and result is None
            self.role_panel.render_role_card(
                role_name, provider_name, result, loading, streaming_content
            )
        
        # 第二行：Risk Officer, Quant Lead
        col3, col4 = st.columns(2)
        
        with col3:
            role_name, provider_name = role_configs[2]
            result = role_results.get(role_name)
            streaming_content = st.session_state.streaming_contents.get(role_name)
            loading = is_loading and result is None
            self.role_panel.render_role_card(
                role_name, provider_name, result, loading, streaming_content
            )
        
        with col4:
            role_name, provider_name = role_configs[3]
            result = role_results.get(role_name)
            streaming_content = st.session_state.streaming_contents.get(role_name)
            loading = is_loading and result is None
            self.role_panel.render_role_card(
                role_name, provider_name, result, loading, streaming_content
            )
    
    def update_streaming_content(self, role_name: str, chunk: str):
        """
        更新 streaming 內容（即時更新）
        
        Args:
            role_name: 角色名稱
            chunk: 新的 chunk
        """
        if role_name not in st.session_state.streaming_contents:
            st.session_state.streaming_contents[role_name] = ""
        st.session_state.streaming_contents[role_name] += chunk
    
    def clear_streaming_contents(self):
        """清除所有 streaming 內容"""
        st.session_state.streaming_contents = {}
    
    def render_strategist(
        self,
        strategist_result: Optional[ProviderResult],
        is_loading: bool = False,
    ) -> None:
        """
        渲染 Strategist 總結
        
        Args:
            strategist_result: Strategist 結果
            is_loading: 是否正在載入
        """
        st.markdown("### 🧭 Strategist 總結")
        
        streaming_content = st.session_state.streaming_contents.get("Strategist")
        
        if strategist_result:
            self.role_panel.render_role_card(
                "Strategist",
                "GPT-4o-mini",
                strategist_result,
                loading=False,
                streaming_content=streaming_content,
            )
        elif is_loading:
            self.role_panel.render_role_card(
                "Strategist",
                "GPT-4o-mini",
                None,
                loading=True,
                streaming_content=streaming_content,
            )
        else:
            self.role_panel.render_role_card(
                "Strategist",
                "GPT-4o-mini",
                None,
                loading=False,
            )

