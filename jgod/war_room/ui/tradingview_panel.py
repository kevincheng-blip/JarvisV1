"""
TradingView K 線圖表面板
"""
import streamlit as st
from typing import Optional


def render_tradingview_chart(
    symbol: str,
    exchange: str = "TWSE",
    height: int = 500,
) -> None:
    """
    渲染 TradingView Widget（可互動 K 線圖）
    
    Args:
        symbol: 股票代號（例如：2330）
        exchange: 交易所（TWSE 台股、NASDAQ 美股等）
        height: 圖表高度
    """
    # 轉換為 TradingView 格式
    # 台股格式：TWSE:2330
    # 美股格式：NASDAQ:AAPL
    tv_symbol = f"{exchange}:{symbol}"
    
    # TradingView Widget HTML
    widget_html = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_{symbol}" style="height: {height}px;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "autosize": true,
        "symbol": "{tv_symbol}",
        "interval": "D",
        "timezone": "Asia/Taipei",
        "theme": "light",
        "style": "1",
        "locale": "zh_TW",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_{symbol}",
        "hide_side_toolbar": false,
        "studies": [
          "RSI@tv-basicstudies",
          "MACD@tv-basicstudies"
        ],
        "show_popup_button": true,
        "popup_width": "1000",
        "popup_height": "650"
      }}
      );
      </script>
    </div>
    """
    
    st.components.v1.html(widget_html, height=height + 50)


def render_lightweight_chart(
    symbol: str,
    data: list,  # [{time, open, high, low, close, volume}]
    height: int = 500,
) -> None:
    """
    使用 Lightweight Charts 渲染 K 線圖（備選方案）
    
    Args:
        symbol: 股票代號
        data: K 線資料
        height: 圖表高度
    """
    import json
    
    # 轉換資料格式
    chart_data = []
    for item in data:
        chart_data.append({
            "time": item.get("time", ""),
            "open": item.get("open", 0),
            "high": item.get("high", 0),
            "low": item.get("low", 0),
            "close": item.get("close", 0),
        })
    
    chart_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    </head>
    <body>
        <div id="chart_{symbol}" style="height: {height}px;"></div>
        <script>
            const chart = LightweightCharts.createChart(document.getElementById('chart_{symbol}'), {{
                width: document.getElementById('chart_{symbol}').clientWidth,
                height: {height},
                layout: {{
                    backgroundColor: '#ffffff',
                    textColor: '#333',
                }},
                grid: {{
                    vertLines: {{
                        color: '#f0f0f0',
                    }},
                    horzLines: {{
                        color: '#f0f0f0',
                    }},
                }},
                crosshair: {{
                    mode: LightweightCharts.CrosshairMode.Normal,
                }},
                rightPriceScale: {{
                    borderColor: '#cccccc',
                }},
                timeScale: {{
                    borderColor: '#cccccc',
                }},
            }});
            
            const candlestickSeries = chart.addCandlestickSeries({{
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            }});
            
            const data = {json.dumps(chart_data)};
            candlestickSeries.setData(data);
            
            chart.timeScale().fitContent();
        </script>
    </body>
    </html>
    """
    
    st.components.v1.html(chart_html, height=height + 50)

