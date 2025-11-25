"""
Pseudo-Live 機制 - v4.2
使用 Streamlit 的 Timer-based Async Refresh 實現類即時更新
"""
import time
import streamlit as st
from typing import Optional
import threading


def setup_autorefresh(interval_ms: int = 300) -> None:
    """
    設定自動刷新（Timer-based）
    
    Args:
        interval_ms: 刷新間隔（毫秒），預設 300ms
    """
    # 檢查是否正在執行
    if not st.session_state.get("war_room_running", False):
        return
    
    # 使用 st_autorefresh（如果已安裝）
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=interval_ms, key="war_room_autorefresh")
    except ImportError:
        # 如果沒有安裝 streamlit-autorefresh，使用手動 timer
        # 透過檢查時間戳記來決定是否 rerun
        last_refresh = st.session_state.get("_last_autorefresh", 0)
        current_time = time.time() * 1000  # 轉換為毫秒
        
        if current_time - last_refresh >= interval_ms:
            st.session_state["_last_autorefresh"] = current_time
            # 使用 st.rerun() 觸發重新執行
            try:
                st.rerun()
            except Exception:
                pass  # 忽略 rerun 錯誤


def start_war_room_session() -> None:
    """
    開始戰情室會話
    """
    st.session_state["war_room_running"] = True
    st.session_state["war_room_started_at"] = time.time()


def stop_war_room_session() -> None:
    """
    停止戰情室會話
    """
    st.session_state["war_room_running"] = False
    if "war_room_started_at" in st.session_state:
        elapsed = time.time() - st.session_state["war_room_started_at"]
        st.session_state["war_room_total_time"] = elapsed


def is_war_room_running() -> bool:
    """
    檢查戰情室是否正在執行
    
    Returns:
        是否正在執行
    """
    return st.session_state.get("war_room_running", False)


def should_autorefresh() -> bool:
    """
    檢查是否應該自動刷新
    
    Returns:
        是否應該自動刷新
    """
    if not is_war_room_running():
        return False
    
    # 檢查是否所有角色都已完成
    roles_state = st.session_state.get("war_room_roles", {})
    if not roles_state:
        return True  # 如果還沒有角色狀態，繼續刷新
    
    # 檢查是否所有角色都已完成或出錯
    all_done = all(
        role_state.get("status") in ["done", "error"]
        for role_state in roles_state.values()
    )
    
    if all_done:
        # 所有角色完成，停止自動刷新
        stop_war_room_session()
        return False
    
    return True

