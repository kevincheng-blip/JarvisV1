"""
戰情室 UI 輔助函式
"""
from typing import Optional, Tuple
import streamlit as st
import streamlit.components.v1 as components
from datetime import date, timedelta
import pandas as pd

from api_clients.finmind_client import FinMindClient
from jgod.market.metadata import get_stock_display_name


def render_tradingview_chart(symbol: str) -> None:
    """
    渲染 TradingView 圖表
    
    Args:
        symbol: 股票代號（例如：2330）
    """
    # TradingView 台股格式：TPE:2330
    tradingview_symbol = f"TPE:{symbol}"
    
    html = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_{symbol}"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
      "autosize": true,
      "symbol": "{tradingview_symbol}",
      "interval": "D",
      "timezone": "Asia/Taipei",
      "theme": "dark",
      "style": "1",
      "locale": "zh_TW",
      "toolbar_bg": "#f1f3f6",
      "enable_publishing": false,
      "allow_symbol_change": true,
      "container_id": "tradingview_{symbol}"
      }}
      );
      </script>
    </div>
    """
    
    components.html(html, height=600)


def get_stock_price_change(
    symbol: str,
    trade_date: Optional[date] = None,
) -> Optional[Tuple[float, float, float]]:
    """
    取得股票今日漲跌資訊
    
    Args:
        symbol: 股票代號
        trade_date: 交易日期（如果為 None 則使用今天）
    
    Returns:
        (今日收盤價, 漲跌百分比, 昨日收盤價) 或 None（如果無法取得）
    """
    if trade_date is None:
        trade_date = date.today()
    
    try:
        client = FinMindClient()
        
        # 取得最近 2 天的資料
        start_date = (trade_date - timedelta(days=5)).strftime("%Y-%m-%d")
        end_date = trade_date.strftime("%Y-%m-%d")
        
        df = client.get_stock_daily(
            stock_id=symbol,
            start_date=start_date,
            end_date=end_date,
        )
        
        if df.empty or len(df) < 2:
            return None
        
        # 標準化欄位名稱
        if "close" not in df.columns:
            if "Close" in df.columns:
                df["close"] = df["Close"]
            else:
                return None
        
        # 排序並取得最後兩筆
        if "date" in df.columns:
            df = df.sort_values("date")
        else:
            df = df.sort_index()
        
        df = df.tail(2)
        
        today_close = float(df.iloc[-1]["close"])
        yesterday_close = float(df.iloc[-2]["close"])
        
        if yesterday_close == 0:
            return None
        
        pct_change = ((today_close - yesterday_close) / yesterday_close) * 100
        
        return (today_close, pct_change, yesterday_close)
    except Exception:
        return None


def format_stock_display_with_change(symbol: str) -> str:
    """
    格式化股票顯示（包含今日漲跌）
    
    Args:
        symbol: 股票代號
    
    Returns:
        格式化字串（例如："2330 台積電 ▲ +2.5%（收盤 1375）"）
    """
    display_name = get_stock_display_name(symbol)
    price_info = get_stock_price_change(symbol)
    
    if price_info:
        today_close, pct_change, _ = price_info
        
        if pct_change > 0:
            arrow = "▲"
            color_class = "price-up"
            pct_str = f"+{pct_change:.2f}%"
        elif pct_change < 0:
            arrow = "▼"
            color_class = "price-down"
            pct_str = f"{pct_change:.2f}%"
        else:
            arrow = "─"
            color_class = "price-neutral"
            pct_str = "0.00%"
        
        return f"{display_name} {arrow} {pct_str}（收盤 {today_close:.0f}）"
    else:
        return display_name


def render_stock_with_change_markdown(symbol: str) -> str:
    """
    產生包含顏色標示的 Markdown 字串
    
    Args:
        symbol: 股票代號
    
    Returns:
        Markdown 字串
    """
    display_name = get_stock_display_name(symbol)
    price_info = get_stock_price_change(symbol)
    
    if price_info:
        today_close, pct_change, _ = price_info
        
        if pct_change > 0:
            arrow = "▲"
            pct_str = f"+{pct_change:.2f}%"
            color = "#ff4444"  # 紅色
        elif pct_change < 0:
            arrow = "▼"
            pct_str = f"{pct_change:.2f}%"
            color = "#44ff44"  # 綠色
        else:
            arrow = "─"
            pct_str = "0.00%"
            color = "#888888"  # 灰色
        
        return f"**{display_name}** <span style='color: {color};'>{arrow} {pct_str}</span>（收盤 {today_close:.0f}）"
    else:
        return f"**{display_name}**"

