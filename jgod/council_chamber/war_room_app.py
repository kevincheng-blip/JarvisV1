"""
Jarvis8 - J-GOD 幕僚會議室 (AI Council Chamber)
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
from jgod.council_chamber.providers import ProviderManager
from jgod.council_chamber.providers.base_provider import ProviderResult
from jgod.council_chamber.components import (
    render_role_card,
    save_war_room_log,
    render_log_download_button,
    render_prediction_table,
    render_stock_detail_panel,
)
from jgod.council_chamber.market_engine import MarketEngine
from jgod.council_chamber.mode_provider_sync import (
    set_mode_and_providers,
    get_final_providers,
    MODE_PROVIDER_MAP,
    get_enabled_provider_keys,
)
from jgod.error_engine import log_error, attempt_auto_fix
from jgod.market.metadata import get_stock_display_name
from jgod.council_chamber.core.chat_engine import WarRoomEngine
from jgod.council_chamber.core.models import RoleName, ProviderKey
from jgod.council_chamber.utils.role_state_manager import (
    initialize_roles_state,
    update_role_state,
    append_role_content,
    mark_role_done,
    get_role_state,
    ROLE_CHINESE_NAMES,
)
from jgod.council_chamber.utils.pseudo_live import (
    start_war_room_session,
    stop_war_room_session,
    is_war_room_running,
    should_autorefresh,
    setup_autorefresh,
)

# === Logger 初始化 ===
import logging
logger = logging.getLogger("war_room")

# === 初始化 ===
# 確保專案根目錄在 Python 路徑中（用於載入 .env 等）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# jgod/council_chamber/war_room_app.py -> jgod/council_chamber -> jgod -> JarvisV1
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 載入環境變數
load_env()

# === 頁面設定 ===
st.set_page_config(
    page_title="Jarvis8 - J-GOD 幕僚會議室",
    layout="wide",
    initial_sidebar_state="expanded",
)

# === 主畫面 Tabs 定義（必須在所有使用之前）===
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏛️ 幕僚會議室",
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
    
    from jgod.council_chamber.mode_provider_sync import (
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
st.title("🧠 Jarvis8 - J-GOD 幕僚會議室 V2")
st.caption("專業券商級多 AI 分析儀表板")

# === Tab 1: 幕僚會議室 V2 ===
with tab1:
    st.markdown("## 🏛️ 幕僚會議室 V2")
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
    if st.button("🚀 啟動幕僚會議室分析", key="run_war_room", type="primary"):
        if not question.strip():
            st.warning("請先輸入問題！")
        else:
            # 初始化 AI Council Chamber Engine v4.0
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
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            logger.info(f"=== AI Council Chamber Engine v4.2 Execution ===")
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
            
            # v4.2: 啟動幕僚會議室會話（用於 Pseudo-Live）
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
            
            # v5.0: 定義即時 streaming 回調（每次 chunk 到達時立即寫入 session_state）
            def on_chunk(role: RoleName, chunk: str):
                """Streaming chunk 回調 - 立即更新 session_state"""
                role_key = role.value
                
                # Debug log
                logger.info(f"[STREAMLIT] Chunk received for role: {role_key}, chunk: {chunk[:40]}...")
                
                # v5.0: 立即寫入 session_state（這是唯一資料來源）
                append_role_content(role_key, chunk)
                update_role_state(role_key, "status", "running")
                
                # Debug: 顯示當前狀態
                roles_state = st.session_state.get("war_room_roles", {})
                logger.debug(f"[STREAMLIT] roles_state after update: {list(roles_state.keys())}")
            
            # v5.0: 準備日期字串
            start_date_str = start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else str(start_date)
            end_date_str = end_date.strftime("%Y-%m-%d") if hasattr(end_date, "strftime") else str(end_date)
            
            # v5.0: 使用 asyncio.create_task 非阻塞執行（Timer-based Async Refresh）
            async def engine_runner():
                """AI Council Chamber Engine 執行器（非阻塞背景任務）"""
                import time
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
                    
                    # 所有角色完成後，標記每個角色為 done
                    logger.info(f"[STREAMLIT] All roles completed, marking as done...")
                    for role, role_result in result.results.items():
                        role_key = role.value
                        logger.info(f"[STREAMLIT] Marking role {role_key} as done, success={role_result.success}")
                        mark_role_done(
                            role_key,
                            success=role_result.success,
                            error_message=role_result.error if not role_result.success else None,
                        )
                    
                    # 儲存結果到 session_state（用於後續處理）
                    st.session_state["_war_room_result"] = result
                    st.session_state["_war_room_completed"] = True
                    
                    # 檢查是否所有角色都已完成
                    roles_state = st.session_state.get("war_room_roles", {})
                    all_done = all(
                        role_state.get("status") in ["done", "error"]
                        for role_state in roles_state.values()
                    ) if roles_state else False
                    
                    logger.info(f"[STREAMLIT] Checking completion: all_done={all_done}, roles_state keys={list(roles_state.keys())}")
                    for role_name, state in roles_state.items():
                        logger.info(f"[STREAMLIT] Role {role_name}: status={state.get('status')}")
                    
                    if all_done:
                        # 停止自動刷新
                        logger.info(f"[STREAMLIT] All roles done, stopping session...")
                        stop_war_room_session()
                        
                        # 計算總耗時
                        if "war_room_started_at" in st.session_state:
                            total_time = time.time() - st.session_state["war_room_started_at"]
                            st.session_state["war_room_total_time"] = total_time
                            logger.info(f"[STREAMLIT] Total execution time: {total_time:.2f}s")
                        
                        logger.info(f"AI Council Chamber execution completed. Executed: {len(result.executed_roles)}, Failed: {len(result.failed_roles)}")
                    
                except Exception as e:
                    logger.error(f"AI Council Chamber execution error: {e}", exc_info=True)
                    st.session_state["_war_room_error"] = str(e)
                    st.session_state["_war_room_completed"] = True
                    stop_war_room_session()
            
            # v5.0: 啟動非阻塞背景任務（使用 asyncio.create_task）
            if "war_room_task" not in st.session_state or st.session_state.get("_war_room_completed", False):
                # 重置完成標記
                st.session_state["_war_room_completed"] = False
                st.session_state["_war_room_result"] = None
                st.session_state["_war_room_error"] = None
                
                # 建立並啟動背景任務（使用新的 event loop）
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                task = loop.create_task(engine_runner())
                st.session_state["war_room_task"] = task
                st.session_state["war_room_loop"] = loop
                
                # 在背景執行 loop（非阻塞）
                import threading
                def run_loop():
                    loop.run_until_complete(task)
                
                thread = threading.Thread(target=run_loop, daemon=True)
                thread.start()
                st.session_state["war_room_thread"] = thread
            
            # v5.0: 設定自動刷新（每 300ms）- Timer-based Async Refresh
            setup_autorefresh(interval_ms=300)
            
            # v5.0: 檢查執行結果（非阻塞檢查）
            if st.session_state.get("_war_room_completed", False):
                war_room_result = st.session_state.get("_war_room_result")
                war_room_error = st.session_state.get("_war_room_error")
                
                # 清理任務
                if "war_room_task" in st.session_state:
                    try:
                        st.session_state["war_room_task"].cancel()
                    except Exception:
                        pass
                    del st.session_state["war_room_task"]
                
                try:
                    if war_room_error:
                        st.error(f"❌ 幕僚會議室執行失敗：{war_room_error}")
                        st.session_state["war_room_loading"] = False
                        stop_war_room_session()
                    elif war_room_result is None:
                        st.error("❌ 分析超時或失敗")
                        st.session_state["war_room_loading"] = False
                        stop_war_room_session()
                    else:
                        # v5.0: 轉換結果格式（適配現有 UI）
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
                        
                        # 儲存結果到 session state（用於後續處理）
                        st.session_state["war_room_role_results"] = role_results_dict
                        st.session_state["war_room_loading"] = False
                        
                        # v5.0: 檢查結果
                        if not war_room_result.results:
                            logger.error("AI Council Chamber execution returned no results!")
                            st.error("❌ 幕僚會議室執行失敗：沒有取得任何結果")
                            st.info("請檢查 log 以了解詳細錯誤")
                        else:
                            # v5.0: 執行 Strategist 總結（使用現有邏輯）
                            try:
                                strategist_result = asyncio.run(
                                    provider_manager.run_strategist_summary(role_results_dict, question)
                                )
                                st.session_state["war_room_strategist_result"] = strategist_result
                            except Exception as e:
                                logger.error(f"Strategist summary failed: {e}")
                                st.warning("⚠️ Strategist 總結失敗，但其他角色分析已完成")
                            
                            # v5.0: 儲存會議紀錄
                            log_file = save_war_room_log(
                                question,
                                role_results_dict,
                                st.session_state.get("war_room_strategist_result"),
                                mode=current_mode,
                                enabled_providers=engine._get_enabled_providers(current_mode, custom_providers),
                            )
                            st.session_state["war_room_log_file"] = log_file
                            
                            # v5.0: 顯示完成訊息與總耗時
                            total_time = st.session_state.get("war_room_total_time", 0)
                            st.success(f"✅ 分析完成！執行 {len(war_room_result.executed_roles)} 個角色，{len(war_room_result.failed_roles)} 個失敗（總耗時：{total_time:.2f} 秒）")
                
                except Exception as e:
                    log_error(e, {
                        "context": "war_room_execution",
                        "mode": current_mode,
                    })
                    st.session_state["war_room_loading"] = False
                    st.error(f"❌ 幕僚會議室執行失敗：{e}")
                    st.info("系統已記錄錯誤，詳細內容請查看 logs/error/")
                    stop_war_room_session()
    
    st.divider()
    
    # v5.0: 顯示結果（完全以 session_state["war_room_roles"] 為唯一資料來源）
    roles_state = st.session_state.get("war_room_roles", {})
    is_loading = st.session_state.get("war_room_loading", False)
    is_running = is_war_room_running()
    
    # Debug log: 顯示當前狀態
    if roles_state:
        logger.debug(f"[STREAMLIT] roles_state keys: {list(roles_state.keys())}")
        for role_name, state in roles_state.items():
            logger.debug(f"[STREAMLIT] {role_name}: status={state.get('status')}, content_len={len(state.get('content', ''))}")
    
    # v5.0: 設定自動刷新（如果正在執行）
    if is_running:
        setup_autorefresh(interval_ms=300)
    
    # 角色卡片（固定顯示，即時更新）
    st.markdown("### 各角色意見")
    
    # v5.0: 完全以 roles_state 為唯一資料來源
    # 第一行：Intel Officer, Scout
    col1, col2 = st.columns(2)
    
    with col1:
        intel_state = roles_state.get("Intel Officer")
        
        # v5.0: 完全從 roles_state 讀取
        if intel_state:
            status = intel_state.get("status", "pending")
            content = intel_state.get("content", "")
            provider = intel_state.get("provider", "perplexity")
            error_message = intel_state.get("error_message")
            
            if status == "pending":
                render_role_card(
                    "Intel Officer",
                    "Perplexity Sonar",
                    None,
                    loading=True,
                )
            elif status == "running":
                # 顯示 streaming 內容
                render_role_card(
                    "Intel Officer",
                    "Perplexity Sonar",
                    ProviderResult(
                        success=True,
                        content=content,
                        provider_name=provider,
                        execution_time=intel_state.get("execution_time", 0.0),
                    ),
                    loading=False,
                )
            elif status == "done":
                render_role_card(
                    "Intel Officer",
                    "Perplexity Sonar",
                    ProviderResult(
                        success=True,
                        content=content,
                        provider_name=provider,
                        execution_time=intel_state.get("execution_time", 0.0),
                    ),
                    loading=False,
                )
            elif status == "error":
                render_role_card(
                    "Intel Officer",
                    "Perplexity Sonar",
                    ProviderResult(
                        success=False,
                        content=content,
                        error=error_message,
                        provider_name=provider,
                        execution_time=intel_state.get("execution_time", 0.0),
                    ),
                    loading=False,
                )
        else:
            render_role_card(
                "Intel Officer",
                "Perplexity Sonar",
                None,
                loading=is_loading,
            )
    
    with col2:
        scout_state = roles_state.get("Scout")
        
        # v5.0: 完全從 roles_state 讀取
        if scout_state:
            status = scout_state.get("status", "pending")
            content = scout_state.get("content", "")
            provider = scout_state.get("provider", "gemini")
            error_message = scout_state.get("error_message")
            
            if status == "pending":
                render_role_card("Scout", "Gemini Flash 2.5", None, loading=True)
            elif status in ["running", "done"]:
                render_role_card(
                    "Scout",
                    "Gemini Flash 2.5",
                    ProviderResult(
                        success=True,
                        content=content,
                        provider_name=provider,
                        execution_time=scout_state.get("execution_time", 0.0),
                    ),
                    loading=False,
                )
            elif status == "error":
                render_role_card(
                    "Scout",
                    "Gemini Flash 2.5",
                    ProviderResult(
                        success=False,
                        content=content,
                        error=error_message,
                        provider_name=provider,
                        execution_time=scout_state.get("execution_time", 0.0),
                    ),
                    loading=False,
                )
        else:
            render_role_card("Scout", "Gemini Flash 2.5", None, loading=is_loading)
    
    # 第二行：Risk Officer, Quant Lead
    col3, col4 = st.columns(2)
    
    with col3:
        risk_state = roles_state.get("Risk Officer")
        
        # v5.0: 完全從 roles_state 讀取
        if risk_state:
            status = risk_state.get("status", "pending")
            content = risk_state.get("content", "")
            provider = risk_state.get("provider", "claude")
            error_message = risk_state.get("error_message")
            
            if status == "pending":
                render_role_card("Risk Officer", "Claude 3.5 Haiku", None, loading=True)
            elif status in ["running", "done"]:
                render_role_card(
                    "Risk Officer",
                    "Claude 3.5 Haiku",
                    ProviderResult(
                        success=True,
                        content=content,
                        provider_name=provider,
                        execution_time=risk_state.get("execution_time", 0.0),
                    ),
                    loading=False,
                )
            elif status == "error":
                render_role_card(
                    "Risk Officer",
                    "Claude 3.5 Haiku",
                    ProviderResult(
                        success=False,
                        content=content,
                        error=error_message,
                        provider_name=provider,
                        execution_time=risk_state.get("execution_time", 0.0),
                    ),
                    loading=False,
                )
        else:
            render_role_card("Risk Officer", "Claude 3.5 Haiku", None, loading=is_loading)
    
    with col4:
        quant_state = roles_state.get("Quant Lead")
        
        # v5.0: 完全從 roles_state 讀取
        if quant_state:
            status = quant_state.get("status", "pending")
            content = quant_state.get("content", "")
            provider = quant_state.get("provider", "claude")
            error_message = quant_state.get("error_message")
            
            if status == "pending":
                render_role_card("Quant Lead", "Claude 3.5 Haiku", None, loading=True)
            elif status in ["running", "done"]:
                render_role_card(
                    "Quant Lead",
                    "Claude 3.5 Haiku",
                    ProviderResult(
                        success=True,
                        content=content,
                        provider_name=provider,
                        execution_time=quant_state.get("execution_time", 0.0),
                    ),
                    loading=False,
                )
            elif status == "error":
                render_role_card(
                    "Quant Lead",
                    "Claude 3.5 Haiku",
                    ProviderResult(
                        success=False,
                        content=content,
                        error=error_message,
                        provider_name=provider,
                        execution_time=quant_state.get("execution_time", 0.0),
                    ),
                    loading=False,
                )
        else:
            render_role_card("Quant Lead", "Claude 3.5 Haiku", None, loading=is_loading)
    
    st.divider()
    
    # v5.0: Strategist 總結（從 session_state 讀取）
    st.markdown("### 🧭 Strategist 總結")
    strategist_result = st.session_state.get("war_room_strategist_result")
    strategist_state = roles_state.get("Strategist")
    
    # v5.0: 優先使用 roles_state，如果沒有則使用 strategist_result
    if strategist_state:
        status = strategist_state.get("status", "pending")
        content = strategist_state.get("content", "")
        provider = strategist_state.get("provider", "gpt")
        error_message = strategist_state.get("error_message")
        
        if status == "pending":
            render_role_card("Strategist", "GPT-4o-mini", None, loading=True)
        elif status in ["running", "done"]:
            render_role_card(
                "Strategist",
                "GPT-4o-mini",
                ProviderResult(
                    success=True,
                    content=content,
                    provider_name=provider,
                    execution_time=strategist_state.get("execution_time", 0.0),
                ),
                loading=False,
            )
        elif status == "error":
            render_role_card(
                "Strategist",
                "GPT-4o-mini",
                ProviderResult(
                    success=False,
                    content=content,
                    error=error_message,
                    provider_name=provider,
                    execution_time=strategist_state.get("execution_time", 0.0),
                ),
                loading=False,
            )
    elif strategist_result:
        render_role_card("Strategist", "GPT-4o-mini", strategist_result, loading=False)
    elif is_loading or is_running:
        render_role_card("Strategist", "GPT-4o-mini", None, loading=True)
    
    # 下載會議紀錄
    log_file = st.session_state.get("war_room_log_file")
    if log_file:
        st.divider()
        render_log_download_button(log_file)
    
    # v5.0: 如果沒有任何結果且不在載入中，顯示提示
    if not roles_state and not is_loading and not is_running:
        st.info("👆 點擊上方「啟動幕僚會議室分析」按鈕開始分析")

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
