"""
AI War Room Tab 組件
"""
from typing import Dict, Any, List
from datetime import date, timedelta
import streamlit as st

from api_clients.finmind_client import FinMindClient, build_market_context_text, build_candle_pattern_text
from jgod.war_room.ai_council import run_war_room, summarize_council_output
from jgod.war_room.market_engine import get_taiwan_market_data
from jgod.war_room.safe_provider import safe_call_provider


def render_opinions(opinions: Any) -> None:
    """依照戰情室回傳的 opinions 結構，做比較好讀的 UI 呈現"""
    if isinstance(opinions, str):
        st.text_area("戰情室會議紀錄（原始）", opinions, height=380)
        return

    if isinstance(opinions, list):
        for role in opinions:
            role_name = role.get("display_name") or role.get("role_name") or role.get("name") or role.get("role_id") or role.get("role_key", "未命名角色")
            role_key = role.get("role_id") or role.get("role_key", "")
            header = f"{role_name}"
            if role_key:
                header += f"（{role_key}）"

            with st.expander(header, expanded=False):
                provider_opinions = [role] if "provider" in role else []
                if not provider_opinions:
                    provider_opinions = role.get("opinions") or role.get("provider_outputs") or []

                for op in provider_opinions:
                    if isinstance(op, dict):
                        provider = op.get("provider", "unknown")
                        content = op.get("content", "")
                        is_error = op.get("is_error", False)
                    else:
                        provider = getattr(op, "provider", "unknown")
                        content = getattr(op, "content", str(op))
                        is_error = getattr(op, "is_error", False)

                    if is_error:
                        st.error(f"⚠️ **{provider}** 分析失敗：{content}")
                    else:
                        st.markdown(f"**🤖 Provider：`{provider}`**")
                        st.write(content)
                    st.markdown("---")
        return

    st.text_area("戰情室會議紀錄（raw）", str(opinions), height=380)


def render_final_consensus(consensus: str) -> None:
    """渲染最終共識"""
    if not consensus:
        st.info("目前沒有最終共識輸出。")
        return

    st.markdown(
        f"""
        <div style="
                padding: 1.2rem;
                border-radius: 0.9rem;
                border: 1px solid rgba(255,255,255,0.18);
                background: #111827;
                box-shadow: 0 18px 35px rgba(0,0,0,0.55);
                margin-top: 0.8rem;
                margin-bottom: 1.2rem;
                color: #F9FAFB;
        ">
            <div style="font-size: 0.9rem; opacity: 0.85; margin-bottom: 0.3rem;">
                🧭 J-GOD 戰情室 · 最終共識
            </div>
            <div style="white-space: pre-line; line-height: 1.7; font-size: 0.98rem;">
                {consensus}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_war_room_tab(sidebar_state: Dict) -> None:
    """
    渲染 AI War Room Tab
    
    Args:
        sidebar_state: Sidebar 狀態字典
    """
    st.markdown("## 🧠 AI War Room")
    st.caption("多 AI 幕僚討論與統整分析")
    
    # === 輸入欄位 ===
    st.markdown("### 分析條件")
    
    # 顯示全域設定（可在此覆蓋）
    col1, col2 = st.columns([1, 1])
    
    with col1:
        stock_id = st.text_input(
            "股票代號",
            value=sidebar_state.get("stock_id", "2330"),
            key="war_room_stock_id",
        )
    
    with col2:
        today = date.today()
        default_start = (today - timedelta(days=40)).strftime("%Y-%m-%d")
        default_end = today.strftime("%Y-%m-%d")
        
        date_range = st.date_input(
            "日期區間",
            value=(
                sidebar_state.get("start_date", today - timedelta(days=40)),
                sidebar_state.get("end_date", today),
            ),
            key="war_room_date_range",
        )
        
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date = date_range[0]
            end_date = date_range[1]
        else:
            start_date = sidebar_state.get("start_date", today - timedelta(days=40))
            end_date = sidebar_state.get("end_date", today)
    
    question = st.text_area(
        "請輸入你的問題",
        value="請分析這檔股票未來一週的多空風險與操作建議",
        height=100,
        key="war_room_question",
    )
    
    st.divider()
    
    # === 執行分析 ===
    if st.button("🚀 送出戰情室分析", key="submit_war_room", type="primary"):
        if not question.strip():
            st.warning("請先輸入問題！")
            return
        
        if not stock_id:
            st.warning("請先輸入股票代號！")
            return
        
        with st.spinner("戰情室多 AI 討論中，請稍等 2～5 秒…"):
            try:
                # 取得市場資料
                jg_state = get_taiwan_market_data()
                
                try:
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
                except Exception as e:
                    market_context = f"（取得 {stock_id} 行情資料失敗：{e}）"
                    candle_text = ""
                    st.warning(f"⚠️ 無法取得完整市場資料：{e}")

                # 組合完整問題
                if candle_text:
                    full_question = f"{market_context}\n\n{candle_text}\n\n請在上述【近期行情摘要】與【K 線觀察】的基礎上，回答下列問題：\n{question}"
                else:
                    full_question = f"{market_context}\n\n請在上述【近期行情摘要】的基礎上，回答下列問題：\n{question}"

                # 使用 safe_call_provider 包裝戰情室呼叫
                def _run_war_room_safe():
                    return run_war_room(
                        question=full_question,
                        stock_id=str(stock_id),
                        start_date=start_date_str,
                        end_date=end_date_str,
                        jg_state=jg_state,
                        selected_providers=sidebar_state.get("providers", ["gpt"]),
                    )

                success, result, error = safe_call_provider("War Room", _run_war_room_safe)
                
                if success:
                    opinions, final_summary = result
                    final_consensus = summarize_council_output(final_summary)

                    # 儲存結果到 session state
                    st.session_state["war_room_opinions"] = opinions
                    st.session_state["war_room_consensus"] = final_consensus
                    
                    st.success("✅ 分析完成")
                else:
                    st.error(f"⚠️ 戰情室分析失敗：{error}")
                    st.info("請檢查 Provider 設定和網路連線")
                    st.session_state["war_room_opinions"] = None
                    st.session_state["war_room_consensus"] = None
                    
            except Exception as e:
                st.error(f"戰情室執行失敗：{e}")
                st.exception(e)
                st.session_state["war_room_opinions"] = None
                st.session_state["war_room_consensus"] = None
    
    st.divider()
    
    # === 顯示結果 ===
    opinions = st.session_state.get("war_room_opinions")
    consensus = st.session_state.get("war_room_consensus")
    
    if opinions or consensus:
        st.markdown("### 📋 戰情室會議結果")
        
        col_left, col_right = st.columns([1.4, 1.0])

        with col_left:
            st.markdown("#### 角色發言與 AI 輸出")
            if opinions:
                render_opinions(opinions)
            else:
                st.info("目前沒有角色發言記錄")

        with col_right:
            st.markdown("#### 🔮 最終共識")
            if consensus:
                render_final_consensus(consensus)
            else:
                st.info("目前沒有最終共識")
    else:
        st.info("👆 點擊上方「送出戰情室分析」按鈕開始分析")

