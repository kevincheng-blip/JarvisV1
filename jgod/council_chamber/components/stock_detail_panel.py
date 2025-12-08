"""
個股細節 Panel 組件
"""
from typing import Optional, Dict, Any
from datetime import date, timedelta
import streamlit as st
import pandas as pd

from api_clients.finmind_client import FinMindClient
from jgod.council_chamber.ui_helpers import render_tradingview_chart, get_stock_price_change
from jgod.market.metadata import get_stock_display_name
from jgod.market.indicators import TechnicalIndicators


def render_stock_detail_panel(
    symbol: str,
    prediction_result: Optional[Any] = None,
) -> None:
    """
    渲染個股細節 Panel
    
    Args:
        symbol: 股票代號
        prediction_result: 預測結果（可選）
    """
    if not symbol:
        st.info("請選擇一檔股票")
        return
    
    st.markdown("---")
    st.markdown(f"### 📊 {get_stock_display_name(symbol)} 詳細資訊")
    
    # 取得基本資料
    try:
        client = FinMindClient()
        today = date.today()
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        
        df = client.get_stock_daily(
            stock_id=symbol,
            start_date=start_date,
            end_date=end_date,
        )
        
        if df.empty:
            st.warning("無法取得股票資料")
            return
        
        # 標準化欄位
        if "close" not in df.columns:
            if "Close" in df.columns:
                df["close"] = df["Close"]
            elif "close_price" in df.columns:
                df["close"] = df["close_price"]
        
        if "date" in df.columns:
            df = df.sort_values("date")
        else:
            df = df.sort_index()
        
        # 計算技術指標（如果可用）
        try:
            indicators = TechnicalIndicators()
            # 計算 MA5 和 MA20
            df["ma_5"] = indicators.calculate_ma(df, period=5)
            df["ma_20"] = indicators.calculate_ma(df, period=20)
            # 計算 RSI
            df["rsi_14"] = indicators.calculate_rsi(df, period=14)
        except Exception:
            # 如果技術指標計算失敗，繼續使用原始資料
            pass
        
        # 顯示今日基本資訊
        if len(df) > 0:
            latest = df.iloc[-1]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                close = float(latest.get("close", 0))
                st.metric("收盤價", f"{close:.2f}")
            
            with col2:
                if "open" in latest:
                    open_price = float(latest["open"])
                    st.metric("開盤價", f"{open_price:.2f}")
            
            with col3:
                if "high" in latest or "max" in latest:
                    high = float(latest.get("high") or latest.get("max", 0))
                    st.metric("最高價", f"{high:.2f}")
            
            with col4:
                if "low" in latest or "min" in latest:
                    low = float(latest.get("low") or latest.get("min", 0))
                    st.metric("最低價", f"{low:.2f}")
            
            # 顯示今日漲跌
            price_info = get_stock_price_change(symbol)
            if price_info:
                today_close, pct_change, _ = price_info
                st.markdown("---")
                
                if pct_change > 0:
                    st.markdown(f"**今日漲跌**: <span style='color: #ff4444; font-size: 1.2em;'>▲ +{pct_change:.2f}%</span>", unsafe_allow_html=True)
                elif pct_change < 0:
                    st.markdown(f"**今日漲跌**: <span style='color: #44ff44; font-size: 1.2em;'>▼ {pct_change:.2f}%</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"**今日漲跌**: ─ 0.00%")
        
        # 顯示預測資訊（如果有）
        if prediction_result:
            st.markdown("---")
            st.markdown("#### 🔮 預測資訊")
            st.markdown(f"**方向**: {prediction_result.direction}")
            st.markdown(f"**分數**: {prediction_result.score:.2f}")
            st.markdown(f"**機率**: {prediction_result.probability:.0%}")
            st.markdown("**理由**:")
            for reason in prediction_result.reasons:
                st.write(f"- {reason}")
        
        # K 線圖
        st.markdown("---")
        st.markdown("#### 📈 K 線圖")
        
        chart_tab1, chart_tab2 = st.tabs(["TradingView", "簡易走勢圖"])
        
        with chart_tab1:
            render_tradingview_chart(symbol)
        
        with chart_tab2:
            if len(df) > 0:
                import matplotlib.pyplot as plt
                
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
                
                # 價格走勢
                if "date" in df.columns:
                    dates = pd.to_datetime(df["date"])
                else:
                    dates = range(len(df))
                
                ax1.plot(dates, df["close"], label="收盤價", color="#1f77b4")
                if "ma_5" in df.columns:
                    ax1.plot(dates, df["ma_5"], label="MA5", color="#ff7f0e", alpha=0.7)
                if "ma_20" in df.columns:
                    ax1.plot(dates, df["ma_20"], label="MA20", color="#2ca02c", alpha=0.7)
                
                ax1.set_title(f"{symbol} 價格走勢")
                ax1.set_ylabel("價格")
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # 成交量
                if "volume" in df.columns:
                    ax2.bar(dates, df["volume"], alpha=0.6, color="#9467bd")
                    ax2.set_ylabel("成交量")
                    ax2.set_xlabel("日期")
                    ax2.grid(True, alpha=0.3)
                
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.warning("無法繪製走勢圖")
        
        # 技術指標摘要
        if len(df) > 0 and "rsi_14" in df.columns:
            st.markdown("---")
            st.markdown("#### 📊 技術指標")
            
            latest = df.iloc[-1]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                rsi = float(latest.get("rsi_14", 50))
                rsi_color = "normal"
                if rsi > 70:
                    rsi_color = "inverse"
                elif rsi < 30:
                    rsi_color = "normal"
                st.metric("RSI(14)", f"{rsi:.1f}", delta=None, delta_color=rsi_color)
            
            with col2:
                if "ma_5" in latest and "ma_20" in latest:
                    ma5 = float(latest["ma_5"])
                    ma20 = float(latest["ma_20"])
                    if ma5 > ma20:
                        st.success("📈 多頭排列 (MA5 > MA20)")
                    else:
                        st.error("📉 空頭排列 (MA5 < MA20)")
            
            with col3:
                if "volume" in latest:
                    volume = float(latest["volume"])
                    st.metric("成交量", f"{volume:,.0f}")
    
    except Exception as e:
        st.error(f"取得股票詳細資訊失敗：{e}")
        st.exception(e)

