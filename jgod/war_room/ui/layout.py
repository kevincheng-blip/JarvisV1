"""
戰情室 Layout：統一管理整體 UI 佈局
"""
import streamlit as st
from typing import Dict, Optional
from datetime import date

from jgod.war_room.providers.base_provider import ProviderResult
from jgod.war_room.ui.chatroom_panel import ChatroomPanel
from jgod.war_room.ui.dashboard_panel import DashboardPanel
from jgod.war_room.ui.tradingview_panel import render_tradingview_chart


class WarRoomLayout:
    """戰情室 Layout：統一管理整體 UI 佈局（Bloomberg 風格）"""
    
    def __init__(self):
        self.chatroom_panel = ChatroomPanel()
        self.dashboard_panel = DashboardPanel()
    
    def render_war_room_tab(
        self,
        role_results: Dict[str, ProviderResult],
        strategist_result: Optional[ProviderResult],
        is_loading: bool,
        stock_id: str,
        start_date: date,
        end_date: date,
    ) -> None:
        """
        渲染戰情室主 Tab
        
        Args:
            role_results: 角色結果字典
            strategist_result: Strategist 結果
            is_loading: 是否正在載入
            stock_id: 股票代號
            start_date: 開始日期
            end_date: 結束日期
        """
        # 主標題
        st.markdown("## 🏛️ 戰情室 V3 - Multi-AI 協作分析")
        st.caption("專業券商級多 AI 分析儀表板 | Bloomberg Terminal 風格")
        
        # 使用 Tabs 分為：聊天室、市場數據、K 線圖
        tab_chat, tab_market, tab_chart = st.tabs([
            "💬 AI 聊天室",
            "📊 市場數據",
            "📈 K 線圖表",
        ])
        
        # Tab 1: AI 聊天室
        with tab_chat:
            st.markdown("### 💬 AI 聊天室")
            st.caption("多角色 AI 並行分析，逐字 streaming 輸出")
            
            # 渲染所有角色
            self.chatroom_panel.render_all_roles(role_results, is_loading)
            
            st.divider()
            
            # Strategist 總結
            self.chatroom_panel.render_strategist(strategist_result, is_loading)
        
        # Tab 2: 市場數據
        with tab_market:
            self.dashboard_panel.render_market_overview(stock_id, start_date, end_date)
        
        # Tab 3: K 線圖表
        with tab_chart:
            st.markdown("### 📈 K 線圖表")
            st.caption("TradingView 可互動 K 線圖")
            
            # 渲染 TradingView 圖表
            render_tradingview_chart(symbol=stock_id, exchange="TWSE", height=600)
    
    def render_sidebar_controls(
        self,
        mode: str,
        enabled_providers: list,
        stock_id: str,
        start_date: date,
        end_date: date,
    ) -> None:
        """
        渲染 Sidebar 控制面板
        
        Returns:
            (mode, enabled_providers, stock_id, start_date, end_date)
        """
        st.markdown("# 🎯 J-GOD 控制面板")
        
        # 模式選擇
        st.markdown("### 📊 系統模式")
        
        from jgod.war_room.mode_provider_sync import (
            set_mode_and_providers,
            MODE_PROVIDER_DISPLAY_MAP,
        )
        
        # 初始化
        if "mode" not in st.session_state:
            st.session_state["mode"] = "Lite"
        if "enabled_providers" not in st.session_state:
            st.session_state["enabled_providers"] = ["GPT-4o-mini"]
        
        mode = st.radio(
            "選擇模式",
            options=["Lite", "Pro", "God", "Custom"],
            index=["Lite", "Pro", "God", "Custom"].index(st.session_state["mode"]) if st.session_state["mode"] in ["Lite", "Pro", "God", "Custom"] else 0,
            key="mode_radio",
        )
        
        # 如果模式改變，執行同步函式
        if mode != st.session_state.get("mode"):
            set_mode_and_providers(mode)
            st.session_state["mode"] = mode
        
        mode_descriptions = {
            "Lite": "⚡ 快速回應（GPT-4o-mini）",
            "Pro": "🚀 平衡模式（GPT + Claude）",
            "God": "👑 深度分析（全 Provider）",
            "Custom": "🔧 自訂模式（手動選擇 Provider）",
        }
        st.caption(mode_descriptions.get(mode, ""))
        
        st.divider()
        
        # Provider 勾選
        st.markdown("### 🤖 AI Provider")
        
        provider_options = [
            "GPT-4o-mini",
            "Claude 3.5 Haiku",
            "Gemini Flash 2.5",
            "Perplexity Sonar",
        ]
        
        # 取得預設 Provider（根據 Mode）
        if mode != "Custom":
            default_providers = MODE_PROVIDER_DISPLAY_MAP.get(mode, ["GPT-4o-mini"])
        else:
            default_providers = st.session_state.get("enabled_providers", ["GPT-4o-mini"])
        
        # 如果模式改變，更新預設值
        if mode != st.session_state.get("last_mode", ""):
            if mode != "Custom":
                st.session_state["enabled_providers"] = MODE_PROVIDER_DISPLAY_MAP.get(mode, ["GPT-4o-mini"])
                default_providers = st.session_state["enabled_providers"]
                if "provider_multiselect" in st.session_state:
                    del st.session_state.provider_multiselect
            st.session_state["last_mode"] = mode
        
        selected_providers = st.multiselect(
            "選擇 Provider",
            options=provider_options,
            default=default_providers,
            key="provider_multiselect",
        )
        
        # 更新 session state
        st.session_state["enabled_providers"] = selected_providers if selected_providers else ["GPT-4o-mini"]
        
        # 顯示當前選擇
        if selected_providers:
            st.caption(f"✅ 已選擇: {', '.join(selected_providers)}")
        else:
            st.warning("⚠️ 至少需要選擇一個 Provider")
        
        st.divider()
        
        # 全域條件
        st.markdown("### 📅 全域條件")
        
        start_date = st.date_input(
            "開始日期",
            value=start_date,
            key="sidebar_start_date",
        )
        
        end_date = st.date_input(
            "結束日期",
            value=end_date,
            key="sidebar_end_date",
        )
        
        stock_id = st.text_input(
            "股票代號",
            value=stock_id,
            key="sidebar_stock_id",
        )
        
        return mode, st.session_state["enabled_providers"], stock_id, start_date, end_date

