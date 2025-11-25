"""
Jarvis8 - J-GOD 戰情室 V2
專業券商級儀表板
"""
import os
import sys
from pathlib import Path
from datetime import date, timedelta
from typing import Dict, List, Optional
import asyncio

import streamlit as st

from jgod.config.env_loader import load_env
from jgod.war_room.providers import ProviderManager
from jgod.war_room.providers.base_provider import ProviderResult
from jgod.war_room.components import (
    render_role_card,
    save_war_room_log,
    render_log_download_button,
    render_prediction_table,
    render_stock_detail_panel,
)
from jgod.war_room.market_engine import MarketEngine
from jgod.war_room.mode_provider_sync import (
    set_mode_and_providers,
    get_final_providers,
    MODE_PROVIDER_MAP,
    get_enabled_provider_keys,
)
from jgod.error_engine import log_error, attempt_auto_fix
from jgod.market.metadata import get_stock_display_name
from jgod.war_room.core.chat_engine import WarRoomEngine
from jgod.war_room.core.models import RoleName, ProviderKey
from jgod.war_room.utils.role_state_manager import (
    initialize_roles_state,
    update_role_state,
    append_role_content,
    mark_role_done,
    get_role_state,
    ROLE_CHINESE_NAMES,
)
from jgod.war_room.utils.pseudo_live import (
    start_war_room_session,
    stop_war_room_session,
    is_war_room_running,
    should_autorefresh,
    setup_autorefresh,
)


# === 初始化 ===
# 確保專案根目錄在 Python 路徑中（用於載入 .env 等）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# jgod/war_room/war_room_app.py -> jgod/war_room -> jgod -> JarvisV1
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 載入環境變數
load_env()

# === 頁面設定 ===
st.set_page_config(
    page_title="Jarvis8 - J-GOD 戰情室",
    layout="wide",
    initial_sidebar_state="expanded",
)

# === 主畫面 Tabs 定義（必須在所有使用之前）===
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏛️ 戰情室",
    "🔮 預測面板",
    "💬 市場問答",
    "📊 個股深度分析",
    "📈 盤勢總覽",
    "🎯 交易策略生成器",
    "📉 策略回測系統",
])

# === 左側 Sidebar ===
with st.sidebar:
    st.markdown("# 🎯 J-GOD 控制面板")
    
    # 模式選擇
    st.markdown("### 📊 系統模式")
    
    # 初始化統一的 session state keys
    if "mode" not in st.session_state:
        st.session_state["mode"] = "Lite"
    if "enabled_providers" not in st.session_state:
        st.session_state["enabled_providers"] = ["GPT-4o-mini"]
    
    # 刪除舊的 session state keys（如果存在）
    for old_key in ["war_room_mode", "provider_selection", "providers", "provider_list", "final_providers"]:
        if old_key in st.session_state:
            del st.session_state[old_key]
    
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
    
    # Provider 顯示（Mode 是唯一真實來源）
    st.markdown("### 🤖 AI Provider")
    
    from jgod.war_room.mode_provider_sync import (
        MODE_PROVIDER_MAP,
        MODE_PROVIDER_DISPLAY_MAP,
        PROVIDER_KEY_TO_DISPLAY,
        get_enabled_provider_keys,
    )
    
    # 根據 Mode 決定顯示方式
    if mode in ["Lite", "Pro", "God"]:
        # 非 Custom 模式：只顯示唯讀資訊
        enabled_provider_keys = MODE_PROVIDER_MAP.get(mode, ["gpt"])
        enabled_provider_display = MODE_PROVIDER_DISPLAY_MAP.get(mode, ["GPT-4o-mini"])
        
        st.info(f"**目前啟用 Provider：** {', '.join(enabled_provider_display)}")
        st.caption(f"（{mode} 模式自動啟用，無法手動修改）")
        
        # 更新 session state（確保一致性）
        st.session_state["enabled_providers"] = enabled_provider_display
    else:
        # Custom 模式：顯示可互動的多選元件
        provider_options = [
            "GPT-4o-mini",
            "Claude 3.5 Haiku",
            "Gemini Flash 2.5",
            "Perplexity Sonar",
        ]
        
        # 取得當前選擇（如果沒有則預設 GPT）
        current_selection = st.session_state.get("enabled_providers", ["GPT-4o-mini"])
        
        selected_providers = st.multiselect(
            "選擇 Provider",
            options=provider_options,
            default=current_selection,
            key="provider_multiselect",
        )
        
        # 更新 session state
        st.session_state["enabled_providers"] = selected_providers if selected_providers else ["GPT-4o-mini"]
        
        # 轉換為內部鍵值
        enabled_provider_keys = get_enabled_provider_keys(st.session_state["enabled_providers"])
        
        if selected_providers:
            st.caption(f"✅ 已選擇: {', '.join(selected_providers)}")
        else:
            st.warning("⚠️ 至少需要選擇一個 Provider")
            enabled_provider_keys = ["gpt"]  # Fallback
    
    # 顯示 FinMind 狀態（如果未設定）
    try:
        import os
        finmind_token = os.getenv("FINMIND_TOKEN") or os.getenv("FINMIND_API_TOKEN")
        if not finmind_token:
            st.warning("⚠️ FinMind Token 未設定，相關功能將停用")
    except Exception:
        pass
    
    st.divider()
    
    # 全域條件
    st.markdown("### 📅 全域條件")
    
    today = date.today()
    default_start = today - timedelta(days=3)
    
    if "global_start_date" not in st.session_state:
        st.session_state.global_start_date = default_start
    if "global_end_date" not in st.session_state:
        st.session_state.global_end_date = today
    if "global_stock_id" not in st.session_state:
        st.session_state.global_stock_id = "2330"
    
    start_date = st.date_input(
        "開始日期",
        value=st.session_state.global_start_date,
        key="sidebar_start_date",
    )
    
    end_date = st.date_input(
        "結束日期",
        value=st.session_state.global_end_date,
        key="sidebar_end_date",
    )
    
    stock_id = st.text_input(
        "股票代號",
        value=st.session_state.global_stock_id,
        key="sidebar_stock_id",
    )
    
    st.session_state.global_start_date = start_date
    st.session_state.global_end_date = end_date
    st.session_state.global_stock_id = stock_id

# === 主標題 ===
st.title("🧠 Jarvis8 - J-GOD 戰情室 V2")
st.caption("專業券商級多 AI 分析儀表板")

# === Tab 1: 戰情室 V2 ===
with tab1:
    st.markdown("## 🏛️ 戰情室 V2")
    st.caption("多角色 AI 委員會並行分析")
    
    # 輸入區域
    col1, col2 = st.columns([2, 1])
    
    with col1:
        question = st.text_area(
            "請輸入你的問題",
            value="請分析這檔股票未來一週的多空風險與操作建議",
            height=100,
            key="war_room_question",
        )
    
    with col2:
        st.markdown("**分析條件**")
        st.write(f"股票代號: {stock_id}")
        st.write(f"日期區間: {start_date} ~ {end_date}")
    
    # 執行按鈕
    if st.button("🚀 啟動戰情室分析", key="run_war_room", type="primary"):
        if not question.strip():
            st.warning("請先輸入問題！")
        else:
            # 初始化 War Room Engine v4.0
            provider_manager = ProviderManager()
            engine = WarRoomEngine(provider_manager)
            
            # Mode 是唯一真實來源
            current_mode = st.session_state.get("mode", "Lite")
            
            # 計算 Custom 模式的 Provider（如果需要的話）
            custom_providers: Optional[List[ProviderKey]] = None
            if current_mode == "Custom":
                selected_providers_ui = st.session_state.get("enabled_providers", ["GPT-4o-mini"])
                custom_providers = get_enabled_provider_keys(selected_providers_ui)
            
            # 記錄 Mode 和 Provider 選擇（用於 log）
            import logging
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            logger = logging.getLogger("war_room")
            logger.info(f"=== War Room Engine v4.2 Execution ===")
            logger.info(f"Mode: {current_mode}")
            if custom_providers:
                logger.info(f"Custom Providers: {custom_providers}")
            
            # v4.2: 初始化結果狀態（Pseudo-Live 模式）
            st.session_state["war_room_role_results"] = {}
            st.session_state["war_room_strategist_result"] = None
            st.session_state["war_room_loading"] = True
            st.session_state["war_room_streaming_contents"] = {}  # 用於 streaming 內容
            
            # v4.2: 使用新的角色狀態管理器初始化
            enabled_provider_keys = engine._get_enabled_providers(current_mode, custom_providers)
            st.session_state["war_room_roles"] = initialize_roles_state(enabled_provider_keys)
            
            # v4.2: 啟動戰情室會話（用於 Pseudo-Live）
            start_war_room_session()
            
            # 提前取得市場資料（非阻塞，避免阻塞 AI Provider）
            market_context = ""
            candle_text = ""
            try:
                from api_clients.finmind_client import FinMindClient, build_market_context_text, build_candle_pattern_text
                client = FinMindClient()
                start_date_str = start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else str(start_date)
                end_date_str = end_date.strftime("%Y-%m-%d") if hasattr(end_date, "strftime") else str(end_date)
                df = client.get_stock_daily(
                    stock_id=stock_id,
                    start_date=start_date_str,
                    end_date=end_date_str,
                )
                market_context = build_market_context_text(stock_id, df, lookback_days=5)
                candle_text = build_candle_pattern_text(stock_id, df, lookback_days=5)
            except ValueError as e:
                market_context = f"（FinMind Token 未設定，無法取得 {stock_id} 行情資料）"
                candle_text = ""
                logger.warning(f"FinMind not configured: {e}")
            except Exception as e:
                market_context = f"（取得 {stock_id} 行情資料失敗：{str(e)[:50]}）"
                candle_text = ""
                logger.warning(f"FinMind data fetch failed: {e}")
            
            # 組合市場上下文
            if candle_text:
                combined_market_context = f"{market_context}\n\n{candle_text}"
            else:
                combined_market_context = market_context
            
            # v4.2: 定義即時 streaming 回調（使用新的狀態管理器）
            def on_chunk(role: RoleName, chunk: str):
                """Streaming chunk 回調 - 即時更新 session_state"""
                role_key = role.value
                
                # 更新 streaming_contents（向後兼容）
                if role_key not in st.session_state["war_room_streaming_contents"]:
                    st.session_state["war_room_streaming_contents"][role_key] = ""
                st.session_state["war_room_streaming_contents"][role_key] += chunk
                
                # v4.2: 使用新的狀態管理器追加內容
                append_role_content(role_key, chunk)
            
            # v4.2: 準備日期字串
            start_date_str = start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else str(start_date)
            end_date_str = end_date.strftime("%Y-%m-%d") if hasattr(end_date, "strftime") else str(end_date)
            
            # v4.2: 使用 background task 執行（非阻塞）
            import threading
            import queue
            
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            async def run_war_room_async():
                """執行 War Room 分析（async 版本）"""
                try:
                    result = await engine.run_war_room(
                        mode=current_mode,
                        custom_providers=custom_providers,
                        stock_id=stock_id,
                        start_date=start_date_str,
                        end_date=end_date_str,
                        user_question=question,
                        market_context=combined_market_context,
                        streaming_callback=on_chunk,
                    )
                    result_queue.put(result)
                except Exception as e:
                    exception_queue.put(e)
            
            def run_in_thread():
                """在背景執行緒中執行 async 函數"""
                try:
                    asyncio.run(run_war_room_async())
                except Exception as e:
                    exception_queue.put(e)
            
            # 啟動背景執行緒
            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()
            
            # v4.2: 設定自動刷新（每 300ms）
            from jgod.war_room.utils.pseudo_live import setup_autorefresh
            setup_autorefresh(interval_ms=300)
            
            # 等待執行完成（非阻塞，讓 UI 可以更新）
            import time
            max_wait_time = 120  # 最多等待 120 秒
            start_wait = time.time()
            war_room_result = None
            
            while time.time() - start_wait < max_wait_time:
                if not result_queue.empty():
                    war_room_result = result_queue.get()
                    break
                if not exception_queue.empty():
                    exception = exception_queue.get()
                    raise exception
                
                # 檢查是否所有角色都已完成
                roles_state = st.session_state.get("war_room_roles", {})
                all_done = all(
                    role_state.get("status") in ["done", "error"]
                    for role_state in roles_state.values()
                ) if roles_state else False
                
                if all_done and thread.is_alive():
                    # 等待執行緒完成
                    thread.join(timeout=5)
                    if not result_queue.empty():
                        war_room_result = result_queue.get()
                        break
                
                time.sleep(0.1)  # 短暫等待，避免 CPU 過載
            
            # 如果超時，顯示警告
            if war_room_result is None:
                if thread.is_alive():
                    st.warning("⏱️ 分析時間較長，仍在執行中...")
                    # 繼續等待
                    thread.join(timeout=30)
                    if not result_queue.empty():
                        war_room_result = result_queue.get()
            
            # 執行 War Room 分析（使用新引擎）
            try:
                if war_room_result is None:
                    st.error("❌ 分析超時或失敗")
                    st.session_state["war_room_loading"] = False
                    stop_war_room_session()
                else:
                    # 轉換結果格式（適配現有 UI）
                    role_results_dict = {}
                    for role, role_result in war_room_result.results.items():
                        # 轉換為 ProviderResult 格式（適配現有 render_role_card）
                        provider_result = ProviderResult(
                            success=role_result.success,
                            content=role_result.content,
                            error=role_result.error,
                            provider_name=role_result.provider_key,
                            execution_time=role_result.execution_time,
                        )
                        role_results_dict[role.value] = provider_result
                        
                        # v4.2: 使用新的狀態管理器標記完成
                        role_key = role.value
                        mark_role_done(
                            role_key,
                            success=role_result.success,
                            error_message=role_result.error if not role_result.success else None,
                        )
                    
                    # 儲存結果到 session state
                    st.session_state["war_room_role_results"] = role_results_dict
                    st.session_state["war_room_loading"] = False
                    
                    # v4.2: 停止戰情室會話
                    stop_war_room_session()
                    
                    # 檢查結果
                    if not war_room_result.results:
                        logger.error("War Room execution returned no results!")
                        st.error("❌ 戰情室執行失敗：沒有取得任何結果")
                        st.info("請檢查 log 以了解詳細錯誤")
                    else:
                        # 執行 Strategist 總結（使用現有邏輯）
                        try:
                            strategist_result = asyncio.run(
                                provider_manager.run_strategist_summary(role_results_dict, question)
                            )
                            st.session_state["war_room_strategist_result"] = strategist_result
                        except Exception as e:
                            logger.error(f"Strategist summary failed: {e}")
                            st.warning("⚠️ Strategist 總結失敗，但其他角色分析已完成")
                        
                        # 儲存會議紀錄
                        log_file = save_war_room_log(
                            question,
                            role_results_dict,
                            st.session_state.get("war_room_strategist_result"),
                            mode=current_mode,
                            enabled_providers=engine._get_enabled_providers(current_mode, custom_providers),
                        )
                        st.session_state["war_room_log_file"] = log_file
                        
                        # 記錄完成
                        logger.info(f"War Room execution completed. Executed: {len(war_room_result.executed_roles)}, Failed: {len(war_room_result.failed_roles)}")
                        
                        st.success(f"✅ 分析完成！執行 {len(war_room_result.executed_roles)} 個角色，{len(war_room_result.failed_roles)} 個失敗")
                    
            except Exception as e:
                log_error(e, {
                    "context": "war_room_execution",
                    "mode": current_mode,
                })
                st.session_state["war_room_loading"] = False
                st.error(f"❌ 戰情室執行失敗：{e}")
                st.info("系統已記錄錯誤，詳細內容請查看 logs/error/")
    
    st.divider()
    
    # v4.1: 顯示結果（即時 streaming 模式）
    role_results = st.session_state.get("war_room_role_results", {})
    strategist_result = st.session_state.get("war_room_strategist_result")
    is_loading = st.session_state.get("war_room_loading", False)
    roles_state = st.session_state.get("war_room_roles", {})
    
    # 角色卡片（固定顯示，即時更新）
    st.markdown("### 各角色意見")
    
    # v4.1: 使用 roles_state 來顯示即時 streaming 內容
    # 第一行：Intel Officer, Scout
    col1, col2 = st.columns(2)
    
    with col1:
        intel_state = roles_state.get("Intel Officer")
        intel_result = role_results.get("Intel Officer")
        
        # 如果有 streaming 內容，優先顯示
        if intel_state and intel_state.get("status") == "running":
            # 顯示 streaming 內容
            streaming_content = intel_state.get("content", "")
            if streaming_content:
                render_role_card(
                    "Intel Officer",
                    "Perplexity Sonar",
                    ProviderResult(
                        success=True,
                        content=streaming_content,
                        provider_name="perplexity",
                        execution_time=0.0,
                    ),
                    loading=False,
                )
            else:
                render_role_card(
                    "Intel Officer",
                    "Perplexity Sonar",
                    None,
                    loading=True,
                )
        else:
            render_role_card(
                "Intel Officer",
                "Perplexity Sonar",
                intel_result,
                loading=is_loading and intel_result is None,
            )
    
    with col2:
        scout_state = roles_state.get("Scout")
        scout_result = role_results.get("Scout")
        
        if scout_state and scout_state.get("status") == "running":
            streaming_content = scout_state.get("content", "")
            if streaming_content:
                render_role_card(
                    "Scout",
                    "Gemini Flash 2.5",
                    ProviderResult(
                        success=True,
                        content=streaming_content,
                        provider_name="gemini",
                        execution_time=0.0,
                    ),
                    loading=False,
                )
            else:
                render_role_card(
                    "Scout",
                    "Gemini Flash 2.5",
                    None,
                    loading=True,
                )
        else:
            render_role_card(
                "Scout",
                "Gemini Flash 2.5",
                scout_result,
                loading=is_loading and scout_result is None,
            )
    
    # 第二行：Risk Officer, Quant Lead
    col3, col4 = st.columns(2)
    
    with col3:
        risk_state = roles_state.get("Risk Officer")
        risk_result = role_results.get("Risk Officer")
        
        if risk_state and risk_state.get("status") == "running":
            streaming_content = risk_state.get("content", "")
            if streaming_content:
                render_role_card(
                    "Risk Officer",
                    "Claude 3.5 Haiku",
                    ProviderResult(
                        success=True,
                        content=streaming_content,
                        provider_name="claude",
                        execution_time=0.0,
                    ),
                    loading=False,
                )
            else:
                render_role_card(
                    "Risk Officer",
                    "Claude 3.5 Haiku",
                    None,
                    loading=True,
                )
        else:
            render_role_card(
                "Risk Officer",
                "Claude 3.5 Haiku",
                risk_result,
                loading=is_loading and risk_result is None,
            )
    
    with col4:
        quant_state = roles_state.get("Quant Lead")
        quant_result = role_results.get("Quant Lead")
        
        if quant_state and quant_state.get("status") == "running":
            streaming_content = quant_state.get("content", "")
            if streaming_content:
                render_role_card(
                    "Quant Lead",
                    "Claude 3.5 Haiku",
                    ProviderResult(
                        success=True,
                        content=streaming_content,
                        provider_name="claude",
                        execution_time=0.0,
                    ),
                    loading=False,
                )
            else:
                render_role_card(
                    "Quant Lead",
                    "Claude 3.5 Haiku",
                    None,
                    loading=True,
                )
        else:
            render_role_card(
                "Quant Lead",
                "Claude 3.5 Haiku",
                quant_result,
                loading=is_loading and quant_result is None,
            )
    
    st.divider()
    
    # Strategist 總結
    st.markdown("### 🧭 Strategist 總結")
    if strategist_result:
        render_role_card(
            "Strategist",
            "GPT-4o-mini",
            strategist_result,
            loading=False,
        )
    elif is_loading:
        render_role_card(
            "Strategist",
            "GPT-4o-mini",
            None,
            loading=True,
        )
    else:
        render_role_card(
            "Strategist",
            "GPT-4o-mini",
            None,
            loading=False,
        )
    
    # 下載會議紀錄
    log_file = st.session_state.get("war_room_log_file")
    if log_file:
        st.divider()
        render_log_download_button(log_file)
    
    # 如果沒有任何結果且不在載入中，顯示提示
    if not role_results and not is_loading:
        st.info("👆 點擊上方「啟動戰情室分析」按鈕開始分析")

# === Tab 2: 預測面板 ===
with tab2:
    st.markdown("## 🔮 預測面板")
    st.caption("規則型預測引擎 - 預測明日可能漲/跌最多的股票")
    
    # 控制條件
    col1, col2 = st.columns([1, 1])
    
    with col1:
        direction = st.radio(
            "預測方向",
            options=["Up", "Down"],
            index=0,
            horizontal=True,
            key="prediction_direction",
        )
    
    with col2:
        top_n = st.selectbox(
            "Top N",
            options=[10, 20, 30, 50],
            index=2,  # 預設 30
            key="prediction_top_n",
        )
    
    # 執行預測
    if st.button("🚀 執行預測", key="execute_prediction", type="primary"):
        with st.spinner(f"正在分析{'上漲' if direction == 'Up' else '下跌'}潛力股..."):
            try:
                market_engine = MarketEngine()
                results = market_engine.predict_top_movers(
                    direction=direction.lower(),
                    top_n=top_n,
                )
                
                # 儲存結果
                key = f"prediction_results_{direction.lower()}"
                st.session_state[key] = results
                
                if results:
                    st.success(f"✅ 找到 {len(results)} 檔{'上漲' if direction == 'Up' else '下跌'}潛力股")
                else:
                    st.info("目前沒有符合條件的股票")
            except Exception as e:
                log_error(e, {"context": "prediction_execution"})
                st.error(f"預測失敗：{e}")
    
    st.divider()
    
    # 顯示結果（兩個子 Tab）
    tab_up, tab_down = st.tabs(["📈 上漲名單", "📉 下跌名單"])
    
    selected_symbol = None
    selected_result = None
    
    with tab_up:
        results_up = st.session_state.get("prediction_results_up", [])
        if results_up:
            st.markdown(f"#### 上漲名單（共 {len(results_up)} 檔）")
            
            def on_stock_select_up(symbol, result):
                st.session_state["selected_stock_symbol"] = symbol
                st.session_state["selected_stock_result"] = result
            
            selected_symbol = render_prediction_table(
                results_up,
                "up",
                on_stock_select_up,
            )
            if selected_symbol:
                selected_result = st.session_state.get("selected_stock_result")
        else:
            st.info("點擊上方「執行預測」按鈕開始分析上漲潛力股")
    
    with tab_down:
        results_down = st.session_state.get("prediction_results_down", [])
        if results_down:
            st.markdown(f"#### 下跌名單（共 {len(results_down)} 檔）")
            
            def on_stock_select_down(symbol, result):
                st.session_state["selected_stock_symbol"] = symbol
                st.session_state["selected_stock_result"] = result
            
            if not selected_symbol:
                selected_symbol = render_prediction_table(
                    results_down,
                    "down",
                    on_stock_select_down,
                )
                if selected_symbol:
                    selected_result = st.session_state.get("selected_stock_result")
        else:
            st.info("點擊上方「執行預測」按鈕開始分析下跌風險股")
    
    # 顯示個股詳細資訊
    if selected_symbol or st.session_state.get("selected_stock_symbol"):
        symbol = selected_symbol or st.session_state.get("selected_stock_symbol")
        result = selected_result or st.session_state.get("selected_stock_result")
        
        st.divider()
        render_stock_detail_panel(symbol, result)

# === Tab 3: 市場問答 ===
with tab3:
    st.markdown("## 💬 市場問答")
    st.caption("自然語言市場分析問答")
    
    # 輸入區域
    qa_question = st.text_area(
        "請輸入你的問題",
        value="請分析台積電（2330）近期的走勢與未來展望",
        height=100,
        key="market_qa_question",
    )
    
    if st.button("🚀 送出問題", key="submit_qa", type="primary"):
        if not qa_question.strip():
            st.warning("請先輸入問題！")
        else:
            with st.spinner("AI 正在分析中..."):
                try:
                    manager = ProviderManager()
                    
                    # 使用啟用的 Provider 回答
                    prompt = f"""
股票代號: {stock_id}
日期區間: {start_date} ~ {end_date}

問題: {qa_question}
"""
                    
                    # 從 session state 取得啟用的 Provider
                    current_enabled_providers_ui_qa = st.session_state.get("enabled_providers", ["GPT-4o-mini"])
                    current_mode_qa = st.session_state.get("mode", "Lite")
                    
                    # 計算最終 Provider
                    _, final_provider_keys_qa = get_final_providers(current_mode_qa, current_enabled_providers_ui_qa)
                    
                    # 使用 Strategist 回答（可擴充為多 Provider）
                    result = asyncio.run(
                        manager.run_role("Strategist", prompt, final_provider_keys_qa)
                    )
                    
                    st.session_state["qa_result"] = result
                    st.success("✅ 分析完成！")
                except Exception as e:
                    log_error(e, {"context": "market_qa"})
                    st.error(f"❌ 分析失敗：{e}")
    
    # 顯示結果
    qa_result = st.session_state.get("qa_result")
    if qa_result:
        st.divider()
        if qa_result.success:
            st.markdown("### 📋 分析結果")
            st.markdown(qa_result.content)
        else:
            st.error(f"❌ 錯誤：{qa_result.error}")
    else:
        st.info("👆 點擊上方「送出問題」按鈕開始分析")

# === Tab 4-7: 未來面板（空版）===
with tab4:
    st.markdown("## 📊 個股深度分析")
    st.info("此功能將在後續版本中實作")

with tab5:
    st.markdown("## 📈 盤勢總覽 Dashboard")
    st.info("此功能將在後續版本中實作")

with tab6:
    st.markdown("## 🎯 交易策略生成器")
    st.info("此功能將在後續版本中實作")

with tab7:
    st.markdown("## 📉 策略回測系統")
    st.info("此功能將在後續版本中實作")

# === 錯誤提示 ===
if st.session_state.get("error_detected"):
    st.error("⚠️ 系統偵測到錯誤，詳細內容請查看 logs/error/")
    if st.button("嘗試自動修復", key="auto_fix"):
        # TODO: 實作自動修復
        st.info("自動修復功能開發中...")
