import os
import sys
from pathlib import Path
from datetime import date, timedelta
from typing import Any, List, Dict

import streamlit as st
import matplotlib.pyplot as plt

from api_clients.finmind_client import FinMindClient, build_market_context_text, build_candle_pattern_text
from config.env_loader import load_env
from jgod.war_room.ai_council import run_war_room, summarize_council_output, save_war_room_log
from jgod.war_room.market_engine import get_taiwan_market_data, MarketEngine
from jgod.war_room.ui_helpers import (
    render_tradingview_chart,
    get_stock_price_change,
)
from jgod.war_room.safe_provider import safe_call_provider
from jgod.market.metadata import get_stock_display_name
from jgod.diagnostics.health_check import HealthChecker
from api_clients.anthropic_client import ClaudeProvider
from api_clients.openai_client import GPTProvider
from api_clients.gemini_client import GeminiProvider
from api_clients.perplexity_client import PerplexityProvider


# === UI 輔助函式 ===
def plot_price_series(df, stock_id: str):
    """用於顯示某檔股票的收盤價走勢圖（簡易版）"""
    if df.empty or "date" not in df.columns or "close" not in df.columns:
        st.warning("暫無足夠資料繪製價格走勢圖。")
        return

    fig, ax = plt.subplots()
    ax.plot(df["date"], df["close"])
    ax.set_title(f"{stock_id} 近期收盤價走勢")
    ax.set_xlabel("日期")
    ax.set_ylabel("收盤價")
    plt.xticks(rotation=45)
    st.pyplot(fig)


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


def get_provider_list_for_mode(mode: str) -> List[str]:
    """根據模式取得 Provider 列表"""
    if "Lite" in mode:
        return ["gpt"]
    elif "Pro" in mode:
        return ["gpt", "claude"]
    elif "God" in mode:
        return ["gpt", "claude", "gemini", "perplexity"]
    else:
        return ["gpt"]


def detect_mode_from_providers(providers: List[str]) -> str:
    """從 Provider 列表偵測模式"""
    provider_set = set(providers)
    
    if provider_set == {"gpt"}:
        return "Lite"
    elif provider_set == {"gpt", "claude"}:
        return "Pro"
    elif provider_set == {"gpt", "claude", "gemini", "perplexity"}:
        return "God"
    else:
        return "Custom"


# === 初始化 ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

load_env()

st.set_page_config(page_title="J-GOD 戰情室 v2.1", layout="wide")

st.title("🧠 J-GOD 多 AI 戰情室 v2.1")
st.write("輸入你想問戰情室的問題，系統會啟動多位 AI 幕僚討論，並由『股神總結人格』統整。")

# === 側邊欄：系統診斷 ===
with st.sidebar:
    st.markdown("### 🔧 系統診斷")
    if st.button("執行健康檢查", key="health_check_button"):
        with st.spinner("正在檢查系統狀態..."):
            checker = HealthChecker()
            results = checker.check_all()
            
            st.markdown("#### Provider 狀態")
            for name, health in results.items():
                if health.ok:
                    st.success(f"✅ {health.name}")
                else:
                    st.error(f"❌ {health.name}: {health.error}")

# === 股票輸入 ===
st.markdown("### 📈 股票輸入")
stock_id = st.text_input(
    "想分析的股票代號（例如：2330）",
    value="2330",
    key="stock_id_main",
)

today = date.today()
default_start = today - timedelta(days=3)

start_date = st.date_input(
    "開始日期",
    value=default_start,
    key="start_date",
)

end_date = st.date_input(
    "結束日期",
    value=today,
    key="end_date",
)

# === 戰情室模式選擇 ===
st.markdown("### 🎯 戰情室模式")
PROVIDER_OPTIONS = {
    "GPT (OpenAI)": "gpt",
    "Claude（AI 第二大腦）": "claude",
    "Gemini（快取摘要）": "gemini",
    "Perplexity（情報官）": "perplexity",
}

# 模式選擇
mode_options = ["Lite（單 GPT，最穩）", "Pro（GPT+Claude）", "God（全開，最多 AI）", "Custom（自訂）"]
mode = st.radio(
    "請選擇戰情室模式：",
    mode_options,
    index=0,
    horizontal=True,
    key="war_room_mode",
)

# Provider 選擇（會根據模式自動更新）
# 使用 session state 保存模式，避免每次重新執行都重置
if "war_room_mode_state" not in st.session_state:
    st.session_state.war_room_mode_state = "Lite（單 GPT，最穩）"

# 如果模式改變，更新 session state
if mode != st.session_state.war_room_mode_state:
    st.session_state.war_room_mode_state = mode
    # 清除 Provider 選擇，讓它根據新模式更新
    if "provider_select_state" in st.session_state:
        del st.session_state.provider_select_state
    # 清除 multiselect 的 key，強制重新渲染
    if "provider_select" in st.session_state:
        del st.session_state.provider_select

if mode != "Custom（自訂）":
    # 自動設定 Provider
    auto_providers = get_provider_list_for_mode(mode)
    auto_provider_labels = [
        label for label, key in PROVIDER_OPTIONS.items()
        if key in auto_providers
    ]
    
    # 如果 session state 中沒有或模式改變，使用自動設定
    if "provider_select_state" not in st.session_state:
        st.session_state.provider_select_state = auto_provider_labels
    elif mode != st.session_state.war_room_mode_state:
        st.session_state.provider_select_state = auto_provider_labels
    
    default_providers = st.session_state.provider_select_state
else:
    # Custom 模式：使用 session state 保存使用者選擇
    if "provider_select_state" not in st.session_state:
        st.session_state.provider_select_state = ["GPT (OpenAI)"]
    default_providers = st.session_state.provider_select_state

selected_provider_labels = st.multiselect(
    "選擇要啟用的 AI Provider",
    options=list(PROVIDER_OPTIONS.keys()),
    default=default_providers,
    key="provider_select",
)

# 更新 session state
st.session_state.provider_select_state = selected_provider_labels

# 如果使用者手動調整 Provider，檢查是否需要切換到 Custom 模式
selected_providers = [PROVIDER_OPTIONS[label] for label in selected_provider_labels]
detected_mode = detect_mode_from_providers(selected_providers)
if detected_mode == "Custom" and mode != "Custom（自訂）":
    # 不自動切換，只提示（避免 UI 跳動）
    pass

if not selected_providers:
    selected_providers = ["gpt"]
    st.warning("至少需要選擇一個 Provider，已預設為 GPT")

# === 問題輸入 ===
question = st.text_input("請輸入你的問題：", "")

# === 取得市場資料 ===
jg_state = get_taiwan_market_data()
market_engine = MarketEngine()

# === 明日預測區塊 ===
st.markdown("### 🔮 明日預測")
st.write("使用規則型預測引擎，預測明日可能漲/跌最多的股票")

# Top N 設定
top_n = st.number_input(
    "顯示前 N 名",
    min_value=5,
    max_value=50,
    value=30,
    step=5,
    key="prediction_top_n",
)

# 使用 session state 保存預測結果
if "prediction_results_up" not in st.session_state:
    st.session_state.prediction_results_up = None
if "prediction_results_down" not in st.session_state:
    st.session_state.prediction_results_down = None

# 預測按鈕（並排顯示）
col_pred_up, col_pred_down = st.columns(2)

with col_pred_up:
    if st.button("🔮 預測明日上漲", key="predict_up_button"):
        with st.spinner("正在分析上漲潛力股..."):
            try:
                results = market_engine.predict_top_movers(direction="up", top_n=top_n)
                st.session_state.prediction_results_up = results
            except Exception as e:
                st.error(f"預測失敗：{e}")
                st.exception(e)
                st.session_state.prediction_results_up = None

with col_pred_down:
    if st.button("⚠️ 預測明日下跌", key="predict_down_button"):
        with st.spinner("正在分析下跌風險股..."):
            try:
                results = market_engine.predict_top_movers(direction="down", top_n=top_n)
                st.session_state.prediction_results_down = results
            except Exception as e:
                st.error(f"預測失敗：{e}")
                st.exception(e)
                st.session_state.prediction_results_down = None

# 顯示預測結果（兩個區塊同時存在）
col_result_up, col_result_down = st.columns(2)

with col_result_up:
    st.markdown("#### 📈 預測明日上漲 Top N")
    if st.session_state.prediction_results_up:
        results = st.session_state.prediction_results_up
        st.success(f"找到 {len(results)} 檔潛力上漲股")
        
        for r in results:
            # 取得股票顯示名稱
            stock_display = get_stock_display_name(r.symbol)
            
            # 取得今日漲跌資訊
            price_info = get_stock_price_change(r.symbol)
            if price_info:
                today_close, pct_change, _ = price_info
                if pct_change > 0:
                    change_display = f"🔴 ▲ +{pct_change:.2f}%（收盤 {today_close:.0f}）"
                elif pct_change < 0:
                    change_display = f"🟢 ▼ {pct_change:.2f}%（收盤 {today_close:.0f}）"
                else:
                    change_display = f"⚪ ─ 0.00%（收盤 {today_close:.0f}）"
            else:
                change_display = ""
            
            expander_title = f"{stock_display} {change_display} | 分數：{r.score:.2f} | 上漲機率：{r.probability:.0%}"
            
            with st.expander(expander_title, expanded=False):
                st.markdown(f"**股票**: {get_stock_display_name(r.symbol)}")
                st.markdown(f"**分數**: {r.score:.2f}")
                st.markdown(f"**上漲機率**: {r.probability:.0%}")
                
                st.markdown("**理由**:")
                for reason in r.reasons:
                    st.write(f"- {reason}")
                
                # TradingView 圖表
                if st.button(f"顯示 {r.symbol} K 線圖", key=f"chart_{r.symbol}_up"):
                    render_tradingview_chart(r.symbol)
    else:
        st.info("點擊上方按鈕開始預測")

with col_result_down:
    st.markdown("#### 📉 預測明日下跌 Top N")
    if st.session_state.prediction_results_down:
        results = st.session_state.prediction_results_down
        st.warning(f"找到 {len(results)} 檔下跌風險股")
        
        for r in results:
            # 取得股票顯示名稱
            stock_display = get_stock_display_name(r.symbol)
            
            # 取得今日漲跌資訊
            price_info = get_stock_price_change(r.symbol)
            if price_info:
                today_close, pct_change, _ = price_info
                if pct_change > 0:
                    change_display = f"🔴 ▲ +{pct_change:.2f}%（收盤 {today_close:.0f}）"
                elif pct_change < 0:
                    change_display = f"🟢 ▼ {pct_change:.2f}%（收盤 {today_close:.0f}）"
                else:
                    change_display = f"⚪ ─ 0.00%（收盤 {today_close:.0f}）"
            else:
                change_display = ""
            
            expander_title = f"{stock_display} {change_display} | 分數：{r.score:.2f} | 下跌機率：{r.probability:.0%}"
            
            with st.expander(expander_title, expanded=False):
                st.markdown(f"**股票**: {get_stock_display_name(r.symbol)}")
                st.markdown(f"**分數**: {r.score:.2f}")
                st.markdown(f"**下跌機率**: {r.probability:.0%}")
                
                st.markdown("**理由**:")
                for reason in r.reasons:
                    st.write(f"- {reason}")
                
                # TradingView 圖表
                if st.button(f"顯示 {r.symbol} K 線圖", key=f"chart_{r.symbol}_down"):
                    render_tradingview_chart(r.symbol)
    else:
        st.info("點擊上方按鈕開始預測")

st.divider()

# === AI 短線多空判斷 ===
st.markdown("### 🧭 AI 短線多空判斷")
if st.button("🧭 用 AI 判斷短線多空", key="ai_short_term_button"):
    if not stock_id:
        st.warning("請先輸入股票代號。")
    else:
        with st.spinner("AI 正在分析短線多空方向…"):
            try:
                today = date.today()
                start_date_str = (today - timedelta(days=40)).strftime("%Y-%m-%d")
                end_date_str = today.strftime("%Y-%m-%d")

                client = FinMindClient()
                df = client.get_stock_daily(stock_id=stock_id, start_date=start_date_str, end_date=end_date_str)
                market_context = build_market_context_text(stock_id, df, lookback_days=5)
                candle_text = build_candle_pattern_text(stock_id, df, lookback_days=5)

                ai_question = (
                    f"{market_context}\n\n{candle_text}\n\n"
                    "請你扮演專業量化交易顧問，"
                    "在上述資料的基礎上，給出未來 1～3 個交易日的多空研判、"
                    "風險提醒，以及具體操作建議（例如：偏多、偏空、觀望，建議倉位比例）。"
                )

                opinions, final_summary = run_war_room(
                    question=ai_question,
                    stock_id=str(stock_id),
                    start_date=start_date_str,
                    end_date=end_date_str,
                    jg_state=jg_state,
                    selected_providers=selected_providers,
                )

                final_consensus = summarize_council_output(final_summary)

                st.markdown("### 🧭 短線多空研判結果")
                render_opinions(opinions)
                render_final_consensus(final_consensus)
            except Exception as e:
                st.error(f"分析失敗：{e}")
                st.exception(e)

# === 戰情室主功能 ===
st.markdown("### 🧠 戰情室")
if st.button("送出給戰情室", key="submit_war_room_button"):
    if question.strip() == "":
        st.warning("請先輸入問題！")
    else:
        with st.spinner("戰情室多 AI 討論中，請稍等 2～5 秒…"):
            try:
                today = date.today()
                start_date_str = (today - timedelta(days=40)).strftime("%Y-%m-%d")
                end_date_str = today.strftime("%Y-%m-%d")

                # 取得市場資料
                try:
                    client = FinMindClient()
                    df = client.get_stock_daily(stock_id=stock_id, start_date=start_date_str, end_date=end_date_str)
                    market_context = build_market_context_text(stock_id, df, lookback_days=5)
                    candle_text = build_candle_pattern_text(stock_id, df, lookback_days=5)
                except Exception as e:
                    market_context = f"（取得 {stock_id} 行情資料失敗：{e}）"
                    candle_text = ""

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
                        selected_providers=selected_providers,
                    )

                success, result, error = safe_call_provider("War Room", _run_war_room_safe)
                
                if success:
                    opinions, final_summary = result
                    final_consensus = summarize_council_output(final_summary)

                    st.markdown("## 🧠 戰情室會議結果")

                    col_left, col_right = st.columns([1.4, 1.0])

                    with col_left:
                        st.markdown("### 📋 角色發言與 AI 輸出")
                        render_opinions(opinions)

                    with col_right:
                        st.markdown("### 🔮 最終共識")
                        render_final_consensus(final_consensus)
                else:
                    st.error(f"⚠️ 戰情室分析失敗：{error}")
                    st.info("請檢查 Provider 設定和網路連線")
            except Exception as e:
                st.error(f"戰情室執行失敗：{e}")
                st.exception(e)
