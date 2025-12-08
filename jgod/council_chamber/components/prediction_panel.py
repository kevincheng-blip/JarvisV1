"""
Prediction Radar Tab 組件
"""
from typing import List, Optional, Dict, Any
import streamlit as st
import pandas as pd

from jgod.council_chamber.market_engine import MarketEngine
from jgod.council_chamber.ui_helpers import get_stock_price_change
from jgod.market.metadata import get_stock_display_name
from jgod.prediction.prediction_engine import PredictionResult


def render_prediction_radar_tab(sidebar_state: Dict) -> Optional[str]:
    """
    渲染 Prediction Radar Tab
    
    Args:
        sidebar_state: Sidebar 狀態字典
    
    Returns:
        選中的股票代號（如果有的話）
    """
    st.markdown("## 🔮 Prediction Radar")
    st.caption("使用規則型預測引擎，預測明日可能漲/跌最多的股票")
    
    # === 控制條件區 ===
    st.markdown("### 控制條件")
    
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
    
    st.divider()
    
    # === 執行預測 ===
    if st.button("🚀 執行預測", key="execute_prediction", type="primary"):
        with st.spinner(f"正在分析{'上漲' if direction == 'Up' else '下跌'}潛力股..."):
            try:
                market_engine = MarketEngine()
                results = market_engine.predict_top_movers(
                    direction=direction.lower(),
                    top_n=top_n,
                )
                
                # 儲存結果到 session state
                key = f"prediction_results_{direction.lower()}"
                st.session_state[key] = results
                
                if results:
                    st.success(f"✅ 找到 {len(results)} 檔{'上漲' if direction == 'Up' else '下跌'}潛力股")
                else:
                    st.info("目前沒有符合條件的股票")
            except Exception as e:
                st.error(f"預測失敗：{e}")
                st.exception(e)
    
    st.divider()
    
    # === 結果呈現區（兩個子 Tab）===
    tab_up, tab_down = st.tabs(["📈 上漲名單", "📉 下跌名單"])
    
    selected_symbol = None
    
    with tab_up:
        selected_symbol = _render_prediction_list(
            "up",
            top_n,
            sidebar_state,
        )
    
    with tab_down:
        if selected_symbol is None:
            selected_symbol = _render_prediction_list(
                "down",
                top_n,
                sidebar_state,
            )
    
    return selected_symbol


def _render_prediction_list(
    direction: str,
    top_n: int,
    sidebar_state: Dict,
) -> Optional[str]:
    """
    渲染預測列表
    
    Args:
        direction: "up" 或 "down"
        top_n: Top N 數量
        sidebar_state: Sidebar 狀態
    
    Returns:
        選中的股票代號
    """
    key = f"prediction_results_{direction}"
    results: List[PredictionResult] = st.session_state.get(key, [])
    
    if not results:
        st.info(f"點擊上方「執行預測」按鈕開始分析{'上漲' if direction == 'up' else '下跌'}潛力股")
        return None
    
    # 建立表格資料
    table_data = []
    for r in results:
        price_info = get_stock_price_change(r.symbol)
        
        if price_info:
            today_close, pct_change, _ = price_info
        else:
            today_close = 0
            pct_change = 0
        
        # 特徵摘要
        features_summary = []
        if r.features:
            if r.features.get("ma_5", 0) > r.features.get("ma_20", 0):
                features_summary.append("MA多頭")
            else:
                features_summary.append("MA空頭")
            
            if r.features.get("volume_ratio_5d", 1) > 1.2:
                features_summary.append("量能放大")
        
        table_data.append({
            "股票代號": r.symbol,
            "股票名稱": get_stock_display_name(r.symbol).split(" ", 1)[1] if " " in get_stock_display_name(r.symbol) else "",
            "今日漲跌幅": pct_change,
            "預測分數": r.score,
            "信心度": f"{r.probability:.0%}",
            "特徵摘要": ", ".join(features_summary) if features_summary else "-",
            "預測結果": r,  # 保留原始結果物件
        })
    
    # 建立 DataFrame
    df = pd.DataFrame(table_data)
    
    # 移除預測結果欄位（不顯示在表格中）
    display_df = df.drop(columns=["預測結果"]).copy()
    
    # 格式化今日漲跌幅（加入顏色標示）
    def format_change_pct(value):
        if value > 0:
            return f"🔴 +{value:.2f}%"
        elif value < 0:
            return f"🟢 {value:.2f}%"
        else:
            return f"⚪ {value:.2f}%"
    
    if "今日漲跌幅" in display_df.columns:
        display_df["今日漲跌幅"] = display_df["今日漲跌幅"].apply(format_change_pct)
    
    # 顯示表格（可排序）
    st.markdown(f"#### {'上漲' if direction == 'up' else '下跌'}名單（共 {len(results)} 檔）")
    
    # 使用 st.dataframe 顯示表格
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )
    
    # 使用 selectbox 讓使用者選擇股票
    st.markdown("**選擇股票查看詳細資訊：**")
    stock_options = [f"{row['股票代號']} {row['股票名稱']}" for row in table_data]
    
    if stock_options:
        selected_option = st.selectbox(
            "選擇股票",
            options=stock_options,
            key=f"stock_select_{direction}",
            label_visibility="collapsed",
        )
        
        if selected_option:
            # 從選項中提取股票代號
            selected_symbol = selected_option.split()[0]
            selected_idx = next(
                (i for i, row in enumerate(table_data) if row["股票代號"] == selected_symbol),
                None
            )
            
            if selected_idx is not None:
                st.session_state["selected_stock_symbol"] = selected_symbol
                st.session_state["selected_stock_prediction"] = table_data[selected_idx]["預測結果"]
                return selected_symbol
    
    # 如果沒有選中，嘗試從 session state 取得
    return st.session_state.get("selected_stock_symbol")
    
    return selected_symbol

