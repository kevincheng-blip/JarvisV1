"""
頂部 Summary Bar 組件
"""
from typing import Dict, List
from datetime import date
import streamlit as st

from jgod.diagnostics.health_check import HealthChecker


def render_summary_bar(sidebar_state: Dict) -> None:
    """
    渲染頂部 Summary Bar
    
    Args:
        sidebar_state: Sidebar 狀態字典
    """
    # 取得大盤指數
    try:
        from jgod.war_room.market_engine import get_taiwan_market_data
        market_data = get_taiwan_market_data()
        
        taiex_close = market_data.get("taiex_close", "N/A")
        taiex_change = market_data.get("taiex_change", 0)
    except Exception:
        taiex_close = "N/A"
        taiex_change = 0
    
    # 檢查 Provider 狀態
    provider_status = {}
    try:
        checker = HealthChecker()
        health_results = checker.check_all()
        for name, health in health_results.items():
            provider_status[name] = health.ok
    except Exception:
        pass
    
    # 建立 Summary Bar
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        st.metric(
            "日期",
            date.today().strftime("%Y-%m-%d"),
        )
    
    with col2:
        if taiex_close != "N/A":
            change_color = "normal"
            if isinstance(taiex_change, (int, float)):
                if taiex_change > 0:
                    change_color = "inverse"  # 紅色（上漲）
                elif taiex_change < 0:
                    change_color = "normal"  # 綠色（下跌）
                else:
                    change_color = "off"  # 灰色（無變化）
            
            st.metric(
                "加權指數",
                f"{taiex_close:,.0f}" if isinstance(taiex_close, (int, float)) else str(taiex_close),
                delta=f"{taiex_change:+.0f}" if isinstance(taiex_change, (int, float)) else "N/A",
                delta_color=change_color,
            )
        else:
            st.metric("加權指數", "N/A")
    
    with col3:
        mode = sidebar_state.get("mode", "Lite")
        mode_icons = {"Lite": "⚡", "Pro": "🚀", "God": "👑"}
        st.markdown(f"**模式**: {mode_icons.get(mode, '')} {mode}")
    
    with col4:
        providers = sidebar_state.get("provider_labels", [])
        provider_count = len(providers)
        
        # 檢查是否有 Provider 不可用
        unavailable = []
        for label in providers:
            provider_key = label.split()[0].lower() if label else ""
            if provider_key == "gpt-4o-mini" or provider_key == "gpt":
                key = "openai"
            elif "claude" in provider_key.lower():
                key = "claude"
            elif "gemini" in provider_key.lower():
                key = "gemini"
            elif "perplexity" in provider_key.lower():
                key = "perplexity"
            else:
                key = provider_key
            
            if not provider_status.get(key, True):
                unavailable.append(label)
        
        if unavailable:
            st.warning(f"⚠️ {len(unavailable)} 個 Provider 不可用")
        else:
            st.success(f"✅ {provider_count} 個 Provider 就緒")

