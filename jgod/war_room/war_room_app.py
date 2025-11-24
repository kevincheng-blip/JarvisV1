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
from api_clients.anthropic_client import ClaudeProvider
from api_clients.openai_client import GPTProvider
from api_clients.gemini_client import GeminiProvider
from api_clients.perplexity_client import PerplexityProvider
# (duplicate imports removed - consolidated at file top)
# === 股票收盤價走勢圖 helper ===
def plot_price_series(df, stock_id: str):
    """
    用於顯示某檔股票的收盤價走勢圖（簡易版）。
    """
    if df.empty or "date" not in df.columns or "close" not in df.columns:
        st.warning("暫無足夠資料繪製價格走勢圖。")
        return

    fig, ax = plt.subplots()
    ax.plot(df["date"], df["close"])
    ax.set_title(f"{stock_id} 近期收盤價走勢")
    ax.set_xlabel("日期")
    ax.set_ylabel("收盤價")
    plt.xticks(rotation=45)
# 繪圖輸出到 Streamlit
    st.pyplot(fig)
# (duplicate imports removed - consolidated at file top)
# === FinMind 測試函式 ===
def test_finmind():
    from api_clients.finmind_client import FinMindClient, localize_ohlcv_columns
    client = FinMindClient()
    data = client.get_stock_daily(
        stock_id="2330",
        start_date="2024-12-01",
        end_date="2024-12-10"
    )
    localized = localize_ohlcv_columns(data)
    return localized.head() if hasattr(localized, "head") else localized[:5]
    # 戰情室模式選擇下方加測試按鈕
    if st.button("🔵 測試 FinMind 連線"):
        st.subheader("FinMind 測試結果（前 5 筆）")
        result = test_finmind()
        st.write(result)
# === FinMind 測試函式 ===
def test_finmind():
    from api_clients.finmind_client import FinMindClient
    client = FinMindClient()
    data = client.get_stock_daily(
        stock_id="2330",
        start_date="2024-12-01",
        end_date="2024-12-10"
    )
    return data.head() if hasattr(data, "head") else data[:5]

# (duplicate imports removed - consolidated at file top)
# 僅保留一個測試 FinMind 按鈕
if st.button("測試 FinMind 連線", key="test_finmind_button"):
    result = test_finmind()
    st.subheader("FinMind 測試結果（前 5 筆）")
    st.write(result)

# === 戰情室 UI 輔助函式 ===

# === 戰情室 UI 輔助函式 ===
def render_opinions(opinions: Any) -> None:
    """
    依照戰情室回傳的 opinions 結構，做比較好讀的 UI 呈現。
    - 如果是字串，就整段顯示在 text_area
    - 如果是 list[role]，每個角色用一個 expander 呈現，每個 provider 一個小區塊
    """
    # 情況 1：只是單純字串（例如一整份會議紀錄）
    if isinstance(opinions, str):
        st.text_area("戰情室會議紀錄（原始）", opinions, height=380)
        return

    # 情況 2：預期是 list[dict] 結構
    if isinstance(opinions, list):
        for role in opinions:
            # 依照本專案的意見結構自動對應
            role_name = role.get("display_name") or role.get("role_name") or role.get("name") or role.get("role_id") or role.get("role_key", "未命名角色")
            role_key = role.get("role_id") or role.get("role_key", "")
            header = f"{role_name}"
            if role_key:
                header += f"（{role_key}）"

            with st.expander(header, expanded=False):
                provider_opinions = [role] if "provider" in role else []
                # 若有多 provider 結構，嘗試從 role['opinions'] 或 role['provider_outputs'] 取出
                if not provider_opinions:
                    provider_opinions = role.get("opinions") or role.get("provider_outputs") or []

                for op in provider_opinions:
                    # op 可能是 dict，也可能是物件，先做防護
                    if isinstance(op, dict):
                        provider = op.get("provider", "unknown")
                        content = op.get("content", "")
                    else:
                        provider = getattr(op, "provider", "unknown")
                        content = getattr(op, "content", str(op))

                    st.markdown(f"**🤖 Provider：`{provider}`**")
                    st.write(content)
                    st.markdown("---")
        return

    # 其他異常型態，就直接轉字串顯示
    st.text_area("戰情室會議紀錄（raw）", str(opinions), height=380)


def render_final_consensus(consensus: str) -> None:
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

# 先把專案根目錄加進 sys.path（讓 config、jg​​od 都找得到）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# 先載入 .env（OpenAI、Claude、Perplexity、Gemini、FinMind 等金鑰）
load_env()

st.set_page_config(page_title="J-GOD 戰情室 v2.1", layout="wide")

st.title("🧠 J-GOD 多 AI 戰情室 v2.1")
st.write("輸入你想問戰情室的問題，系統會啟動多位 AI 幕僚討論，並由『股神總結人格』統整。")

st.markdown("### 📈 股票輸入")
stock_id = st.text_input(
    "想分析的股票代號（例如：2330）",
    value="2330",
    key="stock_id_main",
)

# 日期範圍輸入：開始日期 / 結束日期（預設：開始 = 今天 - 3 天，結束 = 今天）
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

# 問題輸入欄位
question = st.text_input("請輸入你的問題：", "")

# Provider 選擇 UI（允許使用者勾選多個 provider）
PROVIDER_OPTIONS = {
    "GPT (OpenAI)": "gpt",
    "Claude（AI 第二大腦）": "claude",
    "Gemini（快取摘要）": "gemini",
    "Perplexity（情報官）": "perplexity",
}

selected_provider_labels = st.multiselect(
    "選擇要啟用的 AI Provider",
    options=list(PROVIDER_OPTIONS.keys()),
    default=["GPT (OpenAI)"],
)

selected_providers = [PROVIDER_OPTIONS[label] for label in selected_provider_labels]
if not selected_providers:
    selected_providers = ["gpt"]

# === Claude 測試區（獨立 debug，不經過戰情室） ===
st.markdown("### 🔬 Claude 測試區（不經過戰情室）")
if st.button("測試 Claude 回覆（Debug 用）", key="claude_debug_button"):
    try:
        claude = ClaudeProvider()
        test_system_prompt = "你是 J-GOD 股神作戰系統中的 Claude 助理，請用一句話自我介紹。"
        test_user_prompt = "簡短說明你現在已經連上系統，可以協助進行股市分析。"

        reply = claude.ask(
            system_prompt=test_system_prompt,
            user_prompt=test_user_prompt,
        )

        st.success("Claude 測試成功：")
        st.write(reply)
    except Exception as e:
        st.error("Claude 測試失敗，錯誤訊息如下：")
        st.exception(e)


st.markdown("### 🔬 GPT 測試區（不經過戰情室）")

if st.button("測試 GPT 回覆（Debug 用）", key="test_gpt_debug"):
    try:
        gpt = GPTProvider()
        test_system_prompt = "你是 J-GOD 股神作戰系統中的 GPT 助理，請用一句話自我介紹。"
        test_user_prompt = "簡短說明你現在已經連上系統，可以協助進行股市分析。"

        reply = gpt.ask(
            system_prompt=test_system_prompt,
            user_prompt=test_user_prompt,
        )

        st.success("GPT 測試成功：")
        st.write(reply)
    except Exception as e:
        st.error("GPT 測試失敗，錯誤訊息如下：")
        st.exception(e)


st.markdown("### 🔬 Gemini 測試區（不經過戰情室）")

if st.button("測試 Gemini 回覆（Debug 用）", key="test_gemini_debug"):
    try:
        gemini = GeminiProvider()
        test_system_prompt = "你是 J-GOD 股神作戰系統中的 Gemini 助理，請用一句話自我介紹。"
        test_user_prompt = "簡短說明你現在已經連上系統，可以協助進行摘要與輔助分析。"

        reply = gemini.ask(
            system_prompt=test_system_prompt,
            user_prompt=test_user_prompt,
        )

        st.success("Gemini 測試成功：")
        st.write(reply)
    except Exception as e:
        st.error("Gemini 測試失敗，錯誤訊息如下：")
        st.exception(e)


st.markdown("### 🔬 Perplexity 測試區（不經過戰情室）")

if st.button("測試 Perplexity 回覆（Debug 用）", key="test_perplexity_debug"):
    try:
        ppx = PerplexityProvider()
        test_system_prompt = "你是 J-GOD 股神作戰系統中的情報官，負責蒐集與整理市場資訊。"
        test_user_prompt = "請用一句很短的話做自我介紹。"

        reply = ppx.ask(
            system_prompt=test_system_prompt,
            user_prompt=test_user_prompt,
        )

        st.success("Perplexity 測試成功：")
        st.write(reply)
    except Exception as e:
        st.error("Perplexity 測試失敗，錯誤訊息如下：")
        st.exception(e)

# ⬇️ 取得即時市場資料（市場引擎）
jg_state = get_taiwan_market_data()

# 初始化市場引擎（用於預測功能）
market_engine = MarketEngine()

# === 明日預測區塊 ===
st.markdown("### 🔮 明日預測")
st.write("使用規則型預測引擎，預測明日可能漲/跌最多的股票")

col_pred_up, col_pred_down = st.columns(2)

with col_pred_up:
    if st.button("🔮 預測明日上漲 Top 20", key="predict_up_button"):
        with st.spinner("正在分析上漲潛力股..."):
            try:
                results = market_engine.predict_top_movers(direction="up", top_n=20)
                if results:
                    st.success(f"找到 {len(results)} 檔潛力上漲股")
                    for r in results:
                        with st.expander(f"{r.symbol} | score={r.score:.2f} | prob={r.probability:.0%}", expanded=False):
                            st.write(f"**分數**: {r.score:.2f}")
                            st.write(f"**機率**: {r.probability:.0%}")
                            st.write("**理由**:")
                            for reason in r.reasons:
                                st.write(f"- {reason}")
                else:
                    st.info("目前沒有符合條件的上漲潛力股")
            except Exception as e:
                st.error(f"預測失敗：{e}")
                st.exception(e)

with col_pred_down:
    if st.button("⚠️ 預測明日下跌 Top 20", key="predict_down_button"):
        with st.spinner("正在分析下跌風險股..."):
            try:
                results = market_engine.predict_top_movers(direction="down", top_n=20)
                if results:
                    st.warning(f"找到 {len(results)} 檔下跌風險股")
                    for r in results:
                        with st.expander(f"{r.symbol} | score={r.score:.2f} | prob={r.probability:.0%}", expanded=False):
                            st.write(f"**分數**: {r.score:.2f}")
                            st.write(f"**機率**: {r.probability:.0%}")
                            st.write("**理由**:")
                            for reason in r.reasons:
                                st.write(f"- {reason}")
                else:
                    st.info("目前沒有符合條件的下跌風險股")
            except Exception as e:
                st.error(f"預測失敗：{e}")
                st.exception(e)

st.divider()

# === AI 短線多空判斷按鈕 ===
if st.button("🧭 用 AI 判斷短線多空"):
    if not stock_id:
        st.warning("請先輸入股票代號。")
    else:
        with st.spinner("AI 正在分析短線多空方向…"):
            today = date.today()
            start_date = (today - timedelta(days=40)).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")

            client = FinMindClient()
            df = client.get_stock_daily(stock_id=stock_id, start_date=start_date, end_date=end_date)
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
                start_date=str(start_date),
                end_date=str(end_date),
                jg_state=jg_state,
                selected_providers=selected_providers,
            )

            final_consensus = summarize_council_output(final_summary)

            st.markdown("### 🧭 短線多空研判結果")
            render_opinions(opinions)
            render_final_consensus(final_consensus)

# ===============================
# 👇 新增戰情模式選擇 + 按鈕觸發
# ===============================
mode = st.radio(
    "請選擇戰情室模式：",
    ["Lite（單 GPT，最穩）", "Pro（GPT+Claude）", "God（全開，最多 AI）"],
    index=0,
    horizontal=True,
)

if st.button("送出給戰情室"):
    if question.strip() == "":
        if st.button("送出給戰情室"):
            if question.strip() == "":
                st.warning("請先輸入問題！")
            else:
                with st.spinner("戰情室多 AI 討論中，請稍等 2～5 秒…"):
                    # 依照戰情模式決定要啟用哪些 provider（僅在使用者未選擇任何 provider 時生效）
                    if not selected_providers:
                        if "Lite" in mode:
                            selected_providers = ["gpt"]  # 單純、最穩
                        elif "Pro" in mode:
                            selected_providers = ["gpt", "claude"]
                        elif "God" in mode:
                            selected_providers = ["gpt", "claude", "gemini", "perplexity"]
                        else:
                            selected_providers = ["gpt"]  # 預設安全值

                    # 取得該股票近 20 個交易日行情摘要

                    try:
                        today = date.today()
                        start_date = (today - timedelta(days=40)).strftime("%Y-%m-%d")
                        end_date = today.strftime("%Y-%m-%d")
                        client = FinMindClient()
                        df = client.get_stock_daily(stock_id=stock_id, start_date=start_date, end_date=end_date)
                        market_context = build_market_context_text(stock_id, df, lookback_days=5)
                        candle_text = build_candle_pattern_text(stock_id, df, lookback_days=5)
                    except Exception as e:
                        market_context = f"（取得 {stock_id} 行情資料失敗：{e}）"
                        candle_text = ""

                    if candle_text:
                        full_question = f"{market_context}\n\n{candle_text}\n\n請在上述【近期行情摘要】與【K 線觀察】的基礎上，回答下列問題：\n{question}"
                    else:
                        full_question = f"{market_context}\n\n請在上述【近期行情摘要】的基礎上，回答下列問題：\n{question}"

                    opinions, final_summary = run_war_room(
                        question=full_question,
                        stock_id=str(stock_id),
                        start_date=str(start_date),
                        end_date=str(end_date),
                        jg_state=jg_state,
                        selected_providers=selected_providers,
                    )

                    final_consensus = summarize_council_output(final_summary)

                    st.markdown("## 🧠 戰情室會議結果")

                    # 左右欄：左邊詳細會議紀錄，右邊最終結論
                    col_left, col_right = st.columns([1.4, 1.0])

                    with col_left:
                        st.markdown("### 📋 角色發言與 AI 輸出")
                        render_opinions(opinions)

                    with col_right:
                        st.markdown("### 🔮 最終共識")
                        render_final_consensus(final_consensus)
                    st.divider()

                st.subheader("🏆 股神總結")
                st.write(final_summary)
            st.divider()

        st.subheader("🏆 股神總結")
        st.write(final_summary)
