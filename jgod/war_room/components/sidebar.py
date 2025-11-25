"""
左側 Sidebar 組件：模式選擇、Provider 勾選、全域條件
"""
from typing import Dict, List, Tuple
from datetime import date, timedelta
import streamlit as st

from jgod.diagnostics.health_check import HealthChecker


PROVIDER_OPTIONS = {
    "GPT-4o-mini": "gpt",
    "Claude 3.5 Haiku": "claude",
    "Gemini Flash 2.5": "gemini",
    "Perplexity Sonar": "perplexity",
}

MODE_PROVIDER_MAP = {
    "Lite": ["gpt", "gemini"],  # 快速回應，只用 GPT 和 Gemini
    "Pro": ["gpt", "claude", "gemini"],  # GPT + Claude + Gemini
    "God": ["gpt", "claude", "gemini", "perplexity"],  # 全開
}


def get_provider_list_for_mode(mode: str) -> List[str]:
    """根據模式取得 Provider 列表"""
    return MODE_PROVIDER_MAP.get(mode, ["gpt"])


def detect_mode_from_providers(providers: List[str]) -> str:
    """從 Provider 列表偵測模式"""
    provider_set = set(providers)
    
    if provider_set == set(MODE_PROVIDER_MAP["Lite"]):
        return "Lite"
    elif provider_set == set(MODE_PROVIDER_MAP["Pro"]):
        return "Pro"
    elif provider_set == set(MODE_PROVIDER_MAP["God"]):
        return "God"
    else:
        return "Custom"


@st.cache_data(ttl=300)  # 快取 5 分鐘
def get_market_index() -> Dict[str, any]:
    """取得大盤指數資訊（簡化版）"""
    try:
        from api_clients.finmind_client import FinMindClient
        client = FinMindClient()
        
        today = date.today()
        start_date = (today - timedelta(days=5)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        
        # 取得加權指數（TAIEX）
        df = client.get_stock_daily(
            stock_id="TAIEX",
            start_date=start_date,
            end_date=end_date,
        )
        
        if df.empty or len(df) < 2:
            return {"available": False}
        
        # 標準化欄位
        if "close" not in df.columns and "Close" in df.columns:
            df["close"] = df["Close"]
        
        if "date" in df.columns:
            df = df.sort_values("date")
        else:
            df = df.sort_index()
        
        df = df.tail(2)
        today_close = float(df.iloc[-1]["close"])
        yesterday_close = float(df.iloc[-2]["close"])
        pct_change = ((today_close - yesterday_close) / yesterday_close) * 100 if yesterday_close > 0 else 0.0
        
        return {
            "available": True,
            "index": today_close,
            "change_pct": pct_change,
        }
    except Exception:
        return {"available": False}


def render_sidebar() -> Dict[str, any]:
    """
    渲染左側 Sidebar
    
    Returns:
        包含所有 Sidebar 狀態的字典
    """
    st.sidebar.markdown("# 🎯 J-GOD 控制面板")
    
    # === 系統模式 ===
    st.sidebar.markdown("### 📊 系統模式")
    
    # 初始化 session state
    if "war_room_mode" not in st.session_state:
        st.session_state.war_room_mode = "Lite"
    
    mode = st.sidebar.radio(
        "選擇模式",
        options=["Lite", "Pro", "God"],
        index=["Lite", "Pro", "God"].index(st.session_state.war_room_mode) if st.session_state.war_room_mode in ["Lite", "Pro", "God"] else 0,
        key="sidebar_mode",
    )
    
    st.session_state.war_room_mode = mode
    
    # 模式說明
    mode_descriptions = {
        "Lite": "快速回應，使用 GPT + Gemini",
        "Pro": "平衡模式，使用 GPT + Claude + Gemini",
        "God": "深度分析，使用所有 Provider",
    }
    st.sidebar.caption(mode_descriptions.get(mode, ""))
    
    st.sidebar.divider()
    
    # === AI Provider 勾選 ===
    st.sidebar.markdown("### 🤖 AI Provider")
    
    # 根據模式自動設定 Provider
    auto_providers = get_provider_list_for_mode(mode)
    auto_provider_labels = [
        label for label, key in PROVIDER_OPTIONS.items()
        if key in auto_providers
    ]
    
    # 如果模式改變，更新 Provider 選擇
    if "last_mode" not in st.session_state or st.session_state.last_mode != mode:
        st.session_state.last_mode = mode
        st.session_state.provider_selection = auto_provider_labels
    
    # 如果 session state 中沒有，使用自動設定
    if "provider_selection" not in st.session_state:
        st.session_state.provider_selection = auto_provider_labels
    
    selected_provider_labels = st.sidebar.multiselect(
        "選擇 Provider",
        options=list(PROVIDER_OPTIONS.keys()),
        default=st.session_state.provider_selection,
        key="sidebar_providers",
    )
    
    # 更新 session state
    st.session_state.provider_selection = selected_provider_labels
    
    # 檢查是否需要切換到 Custom 模式
    selected_providers = [PROVIDER_OPTIONS[label] for label in selected_provider_labels]
    detected_mode = detect_mode_from_providers(selected_providers)
    if detected_mode == "Custom" and mode != "Custom":
        st.sidebar.info("💡 已切換到自訂模式")
    
    if not selected_providers:
        selected_providers = ["gpt"]
        st.sidebar.warning("⚠️ 至少需要選擇一個 Provider")
    
    st.sidebar.divider()
    
    # === 全域條件 ===
    st.sidebar.markdown("### 📅 全域條件")
    
    today = date.today()
    default_start = today - timedelta(days=3)
    
    if "global_start_date" not in st.session_state:
        st.session_state.global_start_date = default_start
    if "global_end_date" not in st.session_state:
        st.session_state.global_end_date = today
    if "global_stock_id" not in st.session_state:
        st.session_state.global_stock_id = "2330"
    
    start_date = st.sidebar.date_input(
        "開始日期",
        value=st.session_state.global_start_date,
        key="sidebar_start_date",
    )
    
    end_date = st.sidebar.date_input(
        "結束日期",
        value=st.session_state.global_end_date,
        key="sidebar_end_date",
    )
    
    stock_id = st.sidebar.text_input(
        "股票代號",
        value=st.session_state.global_stock_id,
        key="sidebar_stock_id",
    )
    
    # 更新 session state
    st.session_state.global_start_date = start_date
    st.session_state.global_end_date = end_date
    st.session_state.global_stock_id = stock_id
    
    st.sidebar.divider()
    
    # === 系統診斷 ===
    st.sidebar.markdown("### 🔧 系統診斷")
    if st.sidebar.button("執行健康檢查", key="sidebar_health_check"):
        with st.sidebar.spinner("檢查中..."):
            try:
                checker = HealthChecker()
                results = checker.check_all()
                
                st.sidebar.markdown("#### Provider 狀態")
                for name, health in results.items():
                    if health.ok:
                        st.sidebar.success(f"✅ {health.name}")
                    else:
                        st.sidebar.error(f"❌ {health.name}")
                        st.sidebar.caption(f"   {health.error[:50]}...")
            except Exception as e:
                st.sidebar.error(f"健康檢查失敗：{e}")
    
    # 回傳 Sidebar 狀態
    return {
        "mode": mode,
        "providers": selected_providers,
        "provider_labels": selected_provider_labels,
        "start_date": start_date,
        "end_date": end_date,
        "stock_id": stock_id,
    }


def get_sidebar_state() -> Dict[str, any]:
    """取得當前 Sidebar 狀態（不重新渲染）"""
    return {
        "mode": st.session_state.get("war_room_mode", "Lite"),
        "providers": [
            PROVIDER_OPTIONS[label]
            for label in st.session_state.get("provider_selection", ["GPT-4o-mini"])
        ],
        "provider_labels": st.session_state.get("provider_selection", ["GPT-4o-mini"]),
        "start_date": st.session_state.get("global_start_date", date.today() - timedelta(days=3)),
        "end_date": st.session_state.get("global_end_date", date.today()),
        "stock_id": st.session_state.get("global_stock_id", "2330"),
    }

