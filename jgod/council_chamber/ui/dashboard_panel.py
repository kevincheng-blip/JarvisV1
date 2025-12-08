"""
市場總覽 Dashboard 面板（Bloomberg 風格）
"""
import streamlit as st
import pandas as pd
from typing import Optional, List, Dict
from datetime import date
import logging

from jgod.market.data_loader import DataLoader
from jgod.market.indicators import TechnicalIndicators
from jgod.council_chamber.utils.finmind_check import check_finmind_token


class DashboardPanel:
    """市場總覽 Dashboard"""
    
    def render_market_overview(
        self,
        stock_id: str,
        start_date: date,
        end_date: date,
    ) -> None:
        """
        渲染市場總覽 Dashboard
        
        Args:
            stock_id: 股票代號
            start_date: 開始日期
            end_date: 結束日期
        """
        st.markdown("## 📊 市場總覽 Dashboard")
        
        # 檢查 FinMind Token
        has_token, token_msg = check_finmind_token()
        
        # 顯示 Token 狀態（只顯示有/沒有，不顯示內容）
        if has_token:
            st.success("✅ FinMind Token: 已設定")
        else:
            st.warning("⚠️ FinMind Token: 未設定")
            st.info("💡 請在 .env 檔案中設定 FINMIND_TOKEN 以啟用市場資料功能")
            return
        
        # 取得市場資料
        try:
            logger = logging.getLogger("war_room.dashboard")
            logger.info(f"Loading market data for {stock_id} from {start_date} to {end_date}")
            
            data_loader = DataLoader()
            df = data_loader.load_taiwan_stock(
                stock_id=stock_id,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            )
            
            if df is None or df.empty:
                st.warning("⚠️ 無法取得市場資料（可能是日期範圍內無資料或 API 錯誤）")
                logger.warning(f"Failed to load market data for {stock_id}")
                return
            
            # 計算技術指標
            indicators = TechnicalIndicators()
            df["ma_5"] = indicators.calculate_ma(df, 5)
            df["ma_10"] = indicators.calculate_ma(df, 10)
            df["ma_20"] = indicators.calculate_ma(df, 20)
            df["ma_60"] = indicators.calculate_ma(df, 60)
            df["rsi_14"] = indicators.calculate_rsi(df, 14)
            macd_data = indicators.calculate_macd(df)
            if not macd_data.empty:
                df["macd"] = macd_data["macd"]
            
            # 最新資料
            latest = df.iloc[-1]
            
            # 第一行：關鍵指標
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "收盤價",
                    f"{latest['close']:.2f}",
                    delta=f"{latest.get('pct_change', 0):.2f}%",
                )
            
            with col2:
                st.metric(
                    "成交量",
                    f"{latest['volume']:,.0f}",
                )
            
            with col3:
                rsi = latest.get('rsi_14', 0)
                rsi_color = "🟢" if 30 <= rsi <= 70 else "🔴"
                st.metric(
                    "RSI(14)",
                    f"{rsi:.2f}",
                    delta=f"{rsi_color}",
                )
            
            with col4:
                ma5 = latest.get('ma_5', 0)
                ma20 = latest.get('ma_20', 0)
                trend = "🟢 多頭" if ma5 > ma20 else "🔴 空頭"
                st.metric(
                    "趨勢",
                    trend,
                )
            
            st.divider()
            
            # 第二行：技術指標表格
            st.markdown("### 技術指標")
            
            indicators_data = {
                "指標": ["MA5", "MA10", "MA20", "MA60", "RSI(14)", "MACD"],
                "數值": [
                    f"{latest.get('ma_5', 0):.2f}",
                    f"{latest.get('ma_10', 0):.2f}",
                    f"{latest.get('ma_20', 0):.2f}",
                    f"{latest.get('ma_60', 0):.2f}",
                    f"{latest.get('rsi_14', 0):.2f}",
                    f"{latest.get('macd', 0):.2f}",
                ],
            }
            indicators_df = pd.DataFrame(indicators_data)
            st.dataframe(indicators_df, use_container_width=True, hide_index=True)
            
            # 第三行：多空儀表（Gauge UI）
            st.markdown("### 多空儀表")
            self._render_bullish_bearish_gauge(df)
            
        except Exception as e:
            st.error(f"載入市場資料失敗：{e}")
    
    def _render_bullish_bearish_gauge(self, df: pd.DataFrame):
        """渲染多空儀表（Gauge UI）"""
        if df.empty:
            return
        
        latest = df.iloc[-1]
        rsi = latest.get('rsi_14', 50)
        ma5 = latest.get('ma_5', 0)
        ma20 = latest.get('ma_20', 0)
        
        # 簡單的多空分數（0-100）
        bullish_score = 50  # 基礎分數
        
        # RSI 影響
        if 30 <= rsi <= 70:
            bullish_score += 20
        elif rsi > 70:
            bullish_score -= 10
        elif rsi < 30:
            bullish_score += 10
        
        # 均線影響
        if ma5 > ma20:
            bullish_score += 20
        else:
            bullish_score -= 20
        
        bullish_score = max(0, min(100, bullish_score))
        bearish_score = 100 - bullish_score
        
        # 使用 HTML/CSS 渲染 Gauge
        gauge_html = f"""
        <div style="display: flex; justify-content: space-around; align-items: center; padding: 20px;">
            <div style="text-align: center;">
                <div style="font-size: 48px; font-weight: bold; color: #28a745;">{bullish_score}%</div>
                <div style="color: #28a745; font-weight: 600;">多頭</div>
            </div>
            <div style="width: 200px; height: 20px; background: linear-gradient(to right, #28a745 0%, #28a745 {bullish_score}%, #dc3545 {bullish_score}%, #dc3545 100%); border-radius: 10px;"></div>
            <div style="text-align: center;">
                <div style="font-size: 48px; font-weight: bold; color: #dc3545;">{bearish_score}%</div>
                <div style="color: #dc3545; font-weight: 600;">空頭</div>
            </div>
        </div>
        """
        
        st.markdown(gauge_html, unsafe_allow_html=True)
    
    def render_top_stocks(
        self,
        direction: str = "up",  # "up" or "down"
        top_n: int = 20,
    ) -> None:
        """
        渲染 Top 股票列表
        
        Args:
            direction: 方向（"up" 或 "down"）
            top_n: Top N
        """
        st.markdown(f"### 📈 {'漲幅' if direction == 'up' else '跌幅'} Top {top_n}")
        
        # TODO: 從 market_engine 取得資料
        st.info("此功能需要整合 market_engine.predict_top_movers()")

