"""
預測表格組件
"""
from typing import List, Optional, Callable, Any
import streamlit as st
import pandas as pd

from jgod.prediction.prediction_engine import PredictionResult
from jgod.war_room.ui_helpers import get_stock_price_change
from jgod.market.metadata import get_stock_display_name


def render_prediction_table(
    results: List[PredictionResult],
    direction: str,
    on_stock_select: Optional[Callable[[str, PredictionResult], None]] = None,
) -> Optional[str]:
    """
    渲染預測表格
    
    Args:
        results: 預測結果列表
        direction: 方向（"up" 或 "down"）
        on_stock_select: 股票選擇回調函式
    
    Returns:
        選中的股票代號
    """
    if not results:
        st.info(f"目前沒有{'上漲' if direction == 'up' else '下跌'}預測結果")
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
        
        # 取得股票名稱
        display_name = get_stock_display_name(r.symbol)
        stock_name = display_name.split(" ", 1)[1] if " " in display_name else ""
        
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
            "股票名稱": stock_name,
            "今日漲跌幅": pct_change,
            "預測分數": r.score,
            "信心度": f"{r.probability:.0%}",
            "特徵摘要": ", ".join(features_summary) if features_summary else "-",
            "_result": r,  # 保留原始結果
        })
    
    # 建立 DataFrame
    df = pd.DataFrame(table_data)
    display_df = df.drop(columns=["_result"]).copy()
    
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
    
    # 顯示表格
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )
    
    # 股票選擇
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
            selected_symbol = selected_option.split()[0]
            selected_result = next(
                (row["_result"] for row in table_data if row["股票代號"] == selected_symbol),
                None,
            )
            
            if selected_result and on_stock_select:
                on_stock_select(selected_symbol, selected_result)
            
            return selected_symbol
    
    return None

