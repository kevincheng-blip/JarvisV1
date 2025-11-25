"""
Jarvis8 - J-GOD 戰情室 V3（完整版）
專業券商級多 AI 分析儀表板 | Bloomberg Terminal 風格
"""
import os
import sys
from pathlib import Path
from datetime import date, timedelta
from typing import Dict, Optional
import asyncio
import time
import threading

import streamlit as st

from jgod.config.env_loader import load_env
from jgod.war_room.providers import ProviderManager
from jgod.war_room.providers.base_provider import ProviderResult
from jgod.war_room.core.role_manager import RoleManager
from jgod.war_room.ui.layout import WarRoomLayout
from jgod.war_room.ui.chatroom_panel import ChatroomPanel
from jgod.war_room.utils.logger import WarRoomLogger
from jgod.war_room.utils.timing import TimingMonitor
from jgod.war_room.utils.error_handler import ErrorHandler
from jgod.war_room.components import (
    save_war_room_log,
    render_log_download_button,
    render_prediction_table,
    render_stock_detail_panel,
)
from jgod.war_room.market_engine import MarketEngine
from jgod.war_room.mode_provider_sync import get_final_enabled_providers
from jgod.error_engine import log_error
from jgod.market.metadata import get_stock_display_name


# === 初始化 ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_env()

# 記錄 FinMind Token 狀態
import logging
logger_init = logging.getLogger("war_room.init")
from jgod.war_room.utils.finmind_check import check_finmind_token
has_finmind, finmind_msg = check_finmind_token()
logger_init.info(f"FinMind Token status: {finmind_msg}")

# === 頁面設定 ===
st.set_page_config(
    page_title="Jarvis8 - J-GOD 戰情室 V3",
    layout="wide",
    initial_sidebar_state="expanded",
)

# === 初始化組件 ===
war_room_layout = WarRoomLayout()
chatroom_panel = ChatroomPanel()
war_room_logger = WarRoomLogger()
timing_monitor = TimingMonitor()
error_handler = ErrorHandler()

# === 初始化 Session State ===
if "war_room_role_results" not in st.session_state:
    st.session_state["war_room_role_results"] = {}
if "war_room_strategist_result" not in st.session_state:
    st.session_state["war_room_strategist_result"] = None
if "war_room_loading" not in st.session_state:
    st.session_state["war_room_loading"] = False
if "streaming_contents" not in st.session_state:
    st.session_state["streaming_contents"] = {}
if "war_room_execution_start_time" not in st.session_state:
    st.session_state["war_room_execution_start_time"] = None

# === 左側 Sidebar ===
with st.sidebar:
    today = date.today()
    default_start = today - timedelta(days=3)
    
    if "global_start_date" not in st.session_state:
        st.session_state.global_start_date = default_start
    if "global_end_date" not in st.session_state:
        st.session_state.global_end_date = today
    if "global_stock_id" not in st.session_state:
        st.session_state.global_stock_id = "2330"
    
    mode, enabled_providers, stock_id, start_date, end_date = war_room_layout.render_sidebar_controls(
        mode=st.session_state.get("mode", "Lite"),
        enabled_providers=st.session_state.get("enabled_providers", ["GPT-4o-mini"]),
        stock_id=st.session_state.global_stock_id,
        start_date=st.session_state.global_start_date,
        end_date=st.session_state.global_end_date,
    )
    
    st.session_state.global_start_date = start_date
    st.session_state.global_end_date = end_date
    st.session_state.global_stock_id = stock_id

# === 主標題 ===
st.title("🧠 Jarvis8 - J-GOD 戰情室 V3")
st.caption("專業券商級多 AI 分析儀表板 | Bloomberg Terminal 風格")

# === 主畫面 Tabs ===
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏛️ 戰情室",
    "🔮 預測面板",
    "💬 市場問答",
    "📊 個股深度分析",
    "📈 盤勢總覽",
    "🎯 交易策略生成器",
    "📉 策略回測系統",
])

# === Tab 1: 戰情室 V3 ===
with tab1:
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
        st.write(f"模式: {mode}")
        st.write(f"Provider: {', '.join(enabled_providers)}")
    
    # 執行按鈕
    if st.button("🚀 啟動戰情室分析", key="run_war_room", type="primary"):
        if not question.strip():
            st.warning("請先輸入問題！")
        else:
            # 初始化
            manager = ProviderManager()
            role_manager = RoleManager(manager.providers)
            
            # Mode 是唯一真實來源，直接從 Mode 取得 Provider
            current_mode = st.session_state.get("mode", "Lite")
            final_provider_keys = get_final_enabled_providers(current_mode)
            
            # 記錄 Mode 和 Provider 選擇（用於 log）
            import logging
            logger = logging.getLogger("war_room.execution")
            logger.info(f"=== War Room Execution ===")
            logger.info(f"Mode: {current_mode}")
            logger.info(f"Enabled Providers (Keys): {final_provider_keys}")
            
            # 記錄開始時間
            execution_start_time = time.time()
            st.session_state["war_room_execution_start_time"] = execution_start_time
            timing_monitor.reset()
            
            # 記錄執行資訊
            war_room_logger.log_execution(
                mode=current_mode,
                enabled_providers=final_provider_keys,
                question=question,
                execution_time=0.0,
                results={},
            )
            
            # 初始化結果狀態
            st.session_state["war_room_role_results"] = {}
            st.session_state["war_room_strategist_result"] = None
            st.session_state["war_room_loading"] = True
            st.session_state["streaming_contents"] = {}
            
            # 提前取得市場資料（非阻塞）
            market_context = ""
            candle_text = ""
            try:
                from api_clients.finmind_client import FinMindClient, build_market_context_text, build_candle_pattern_text
                client = FinMindClient()
                start_date_str = start_date.strftime("%Y-%m-%d")
                end_date_str = end_date.strftime("%Y-%m-%d")
                df = client.get_stock_daily(
                    stock_id=stock_id,
                    start_date=start_date_str,
                    end_date=end_date_str,
                )
                market_context = build_market_context_text(stock_id, df, lookback_days=5)
                candle_text = build_candle_pattern_text(stock_id, df, lookback_days=5)
            except Exception as e:
                market_context = f"（取得 {stock_id} 行情資料失敗：{str(e)[:50]}）"
                candle_text = ""
            
            # 組合完整提示
            if candle_text:
                full_prompt = f"{market_context}\n\n{candle_text}\n\n問題: {question}"
            else:
                full_prompt = f"{market_context}\n\n問題: {question}"
            
            # 定義 streaming chunk 回調
            def on_chunk(role_name: str, chunk: str):
                """Streaming chunk 回調"""
                if role_name not in st.session_state["streaming_contents"]:
                    st.session_state["streaming_contents"][role_name] = ""
                st.session_state["streaming_contents"][role_name] += chunk
                
                # 記錄第一個 chunk 時間
                timing_monitor.record_first_chunk(role_name)
                
                # 觸發 rerun（使用 thread-safe 方式）
                if hasattr(st, 'rerun'):
                    # 在背景執行 rerun（避免阻塞）
                    threading.Thread(target=lambda: time.sleep(0.1) or None, daemon=True).start()
            
            # 定義角色完成回調
            def on_role_complete(role_name: str, result: ProviderResult):
                """角色完成回調"""
                st.session_state["war_room_role_results"][role_name] = result
                timing_monitor.complete_role(role_name)
                war_room_logger.log_role_complete(
                    role_name=role_name,
                    success=result.success,
                    execution_time=result.execution_time,
                )
                
                # 觸發 rerun（使用 thread-safe 方式）
                if hasattr(st, 'rerun'):
                    try:
                        st.rerun()
                    except Exception:
                        pass  # 忽略 rerun 錯誤
            
            # 執行分析（先使用穩定版本 run_all_roles，確保結果正確）
            try:
                # 初始化結果字典
                st.session_state["war_room_role_results"] = {}
                
                # 定義回調函數：每當一個角色完成時，立即更新 session state
                def on_role_complete_simple(role_name: str, result: ProviderResult):
                    """角色完成時的回調函數（穩定版本）"""
                    st.session_state["war_room_role_results"][role_name] = result
                    status = "Success" if result.success else "Failed"
                    logger.info(f"Role {role_name} completed: {status}, updating UI...")
                    if not result.success:
                        logger.warning(f"Role {role_name} error: {result.error}")
                
                # 使用穩定版本執行所有角色（先確保基本功能正常）
                async def run_war_room():
                    # 執行所有角色（使用穩定版本 run_all_roles）
                    results = await manager.run_all_roles(
                        full_prompt, 
                        final_provider_keys
                    )
                    
                    # 確保所有結果都寫入 session_state
                    for role_name, result in results.items():
                        st.session_state["war_room_role_results"][role_name] = result
                        # 也呼叫回調（如果有的話）
                        on_role_complete_simple(role_name, result)
                    
                    logger.info(f"run_war_room completed. Results keys: {list(results.keys())}")
                    return results
                
                # 執行分析
                role_results = asyncio.run(run_war_room())
                
                # 確保結果已寫入 session_state
                if role_results:
                    for role_name, result in role_results.items():
                        st.session_state["war_room_role_results"][role_name] = result
                    logger.info(f"Final role_results keys: {list(role_results.keys())}")
                else:
                    logger.error("role_results is empty! This should not happen.")
                    st.error("❌ 戰情室執行失敗：沒有取得任何結果")
                    st.session_state["war_room_loading"] = False
                    return
                
                # 執行 Strategist 總結
                strategist_result = asyncio.run(
                    manager.run_strategist_summary(role_results, question)
                )
                
                # 儲存最終結果
                st.session_state["war_room_role_results"] = role_results
                st.session_state["war_room_strategist_result"] = strategist_result
                st.session_state["war_room_loading"] = False
                
                # 計算總執行時間
                total_time = time.time() - execution_start_time
                
                # 儲存會議紀錄
                log_file = save_war_room_log(
                    question,
                    role_results,
                    strategist_result,
                    mode=current_mode,
                    enabled_providers=final_provider_keys,
                )
                st.session_state["war_room_log_file"] = log_file
                
                # 記錄完成
                war_room_logger.log_execution(
                    mode=current_mode,
                    enabled_providers=final_provider_keys,
                    question=question,
                    execution_time=total_time,
                    results=role_results,
                )
                
                # 顯示時序摘要
                timing_summary = timing_monitor.get_summary()
                st.success(f"✅ 分析完成！總執行時間: {total_time:.2f} 秒")
                
                # 顯示時序指標
                with st.expander("⏱️ 效能指標", expanded=False):
                    for role_name, metrics in timing_summary.items():
                        st.write(f"**{role_name}**:")
                        st.write(f"  - 第一個 chunk: {metrics['time_to_first_chunk']:.2f}s")
                        st.write(f"  - 總執行時間: {metrics['total_duration']:.2f}s")
                        st.write(f"  - 總 chunks: {metrics['total_chunks']}")
                
            except Exception as e:
                log_error(e, {
                    "context": "war_room_execution",
                    "mode": current_mode,
                    "enabled_providers": final_provider_keys,
                })
                st.session_state["war_room_loading"] = False
                st.error(f"❌ 戰情室執行失敗：{e}")
                st.info("系統已記錄錯誤，詳細內容請查看 logs/error/")
    
    st.divider()
    
    # 顯示結果（使用新架構的 Layout）
    role_results = st.session_state.get("war_room_role_results", {})
    strategist_result = st.session_state.get("war_room_strategist_result")
    is_loading = st.session_state.get("war_room_loading", False)
    
    # 使用 Layout 渲染戰情室
    war_room_layout.render_war_room_tab(
        role_results=role_results,
        strategist_result=strategist_result,
        is_loading=is_loading,
        stock_id=stock_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    # 下載會議紀錄
    log_file = st.session_state.get("war_room_log_file")
    if log_file:
        st.divider()
        render_log_download_button(log_file)
    
    # 如果沒有任何結果且不在載入中，顯示提示
    if not role_results and not is_loading:
        st.info("👆 點擊上方「啟動戰情室分析」按鈕開始分析")

# === Tab 2-7: 其他面板（保持原有功能）===
with tab2:
    st.markdown("## 🔮 預測面板")
    st.caption("規則型預測引擎 - 預測明日可能漲/跌最多的股票")
    
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
            index=2,
            key="prediction_top_n",
        )
    
    if st.button("🚀 執行預測", key="execute_prediction", type="primary"):
        with st.spinner(f"正在分析{'上漲' if direction == 'Up' else '下跌'}潛力股..."):
            try:
                market_engine = MarketEngine()
                results = market_engine.predict_top_movers(
                    direction=direction.lower(),
                    top_n=top_n,
                )
                
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
    
    if selected_symbol or st.session_state.get("selected_stock_symbol"):
        symbol = selected_symbol or st.session_state.get("selected_stock_symbol")
        result = selected_result or st.session_state.get("selected_stock_result")
        
        st.divider()
        render_stock_detail_panel(symbol, result)

with tab3:
    st.markdown("## 💬 市場問答")
    st.caption("自然語言市場分析問答")
    
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
                    
                    prompt = f"""
股票代號: {stock_id}
日期區間: {start_date} ~ {end_date}

問題: {qa_question}
"""
                    
                    current_enabled_providers_ui_qa = st.session_state.get("enabled_providers", ["GPT-4o-mini"])
                    current_mode_qa = st.session_state.get("mode", "Lite")
                    
                    from jgod.war_room.mode_provider_sync import get_final_providers
                    _, final_provider_keys_qa = get_final_providers(current_mode_qa, current_enabled_providers_ui_qa)
                    
                    result = asyncio.run(
                        manager.run_role("Strategist", prompt, final_provider_keys_qa)
                    )
                    
                    st.session_state["qa_result"] = result
                    st.success("✅ 分析完成！")
                except Exception as e:
                    log_error(e, {"context": "market_qa"})
                    st.error(f"❌ 分析失敗：{e}")
    
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
        st.info("自動修復功能開發中...")

