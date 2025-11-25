import pandas as pd


def build_candle_pattern_text(stock_id: str, df: pd.DataFrame, lookback_days: int = 5) -> str:
    """
    做一個簡單版的 K 線文字解析，描述近幾日是長紅、長黑、十字、量縮、量增等。
    這個文字會附加在戰情室 prompt 裡。
    """
    if df.empty:
        return ""

    tail = df.tail(lookback_days)

    lines = [f"【K 線觀察】標的：{stock_id}，最近 {lookback_days} 日："]

    for _, row in tail.iterrows():
        d = row["date"]
        o = float(row["open"])
        c = float(row["close"])
        h = float(row["max"])
        l = float(row["min"])
        body = abs(c - o)
        range_ = max(h - l, 1e-6)
        upper_shadow = h - max(c, o)
        lower_shadow = min(c, o) - l

        if body / range_ < 0.2:
            shape = "十字線或實體極小"
        elif c > o:
            shape = "偏多方長紅"
        else:
            shape = "偏空方長黑"

        lines.append(f"{d}：{shape}，開盤約 {o:.1f}，收盤約 {c:.1f}，高點約 {h:.1f}，低點約 {l:.1f}")

    return "\n".join(lines)
import pandas as pd

def build_market_context_text(
    stock_id: str,
    df: pd.DataFrame,
    lookback_days: int = 5,
) -> str:
    """
    將近幾日的價格與成交狀況整理成一段給戰情室用的文字。
    只用來當作 LLM 的前情資訊，不做精確交易決策。
    """
    if df.empty:
        return f"目前無法取得 {stock_id} 的近期行情資料。"

    tail = df.tail(lookback_days)

    latest = tail.iloc[-1]
    first = tail.iloc[0]

    try:
        last_close = float(latest["close"])
        first_close = float(first["close"])
        change_abs = last_close - first_close
        change_pct = (change_abs / first_close) * 100 if first_close != 0 else 0.0
    except Exception:
        last_close = first_close = change_abs = change_pct = 0.0

    avg_volume = None
    if "Trading_Volume" in tail.columns:
        avg_volume = int(tail["Trading_Volume"].mean())

    lines = []
    lines.append(f"標的：{stock_id}")
    lines.append(f"觀察區間：最近 {lookback_days} 個交易日")
    lines.append(f"起始收盤價：約 {first_close:.2f}")
    lines.append(f"最新收盤價：約 {last_close:.2f}")
    lines.append(f"區間漲跌：約 {change_abs:.2f} 點（約 {change_pct:.2f}%）")
    if avg_volume is not None:
        lines.append(f"最近平均成交量：約 {avg_volume:,} 股")

    context_text = "；".join(lines)
    return "【近期行情摘要】" + context_text
import pandas as pd

def build_market_context_text(
    stock_id: str,
    df: pd.DataFrame,
    lookback_days: int = 5,
) -> str:
    """
    將近幾日的價格與成交狀況整理成一段給戰情室用的文字。
    只用來當作 LLM 的前情資訊，不做精確交易決策。
    """
    if df.empty:
        return f"目前無法取得 {stock_id} 的近期行情資料。"

    tail = df.tail(lookback_days)

    latest = tail.iloc[-1]
    first = tail.iloc[0]

    try:
        last_close = float(latest["close"])
        first_close = float(first["close"])
        change_abs = last_close - first_close
        change_pct = (change_abs / first_close) * 100 if first_close != 0 else 0.0
    except Exception:
        last_close = first_close = change_abs = change_pct = 0.0

    avg_volume = int(tail["Trading_Volume"].mean()) if "Trading_Volume" in tail.columns else None

    lines = []
    lines.append(f"標的：{stock_id}")
    lines.append(f"觀察區間：最近 {lookback_days} 個交易日")
    lines.append(f"起始收盤價：約 {first_close:.2f}")
    lines.append(f"最新收盤價：約 {last_close:.2f}")
    lines.append(f"區間漲跌：約 {change_abs:.2f} 點（約 {change_pct:.2f}%）")

    if avg_volume is not None:
        lines.append(f"最近平均成交量：約 {avg_volume:,} 股")

    context_text = "；".join(lines)
    return "【近期行情摘要】" + context_text

import pandas as pd

FINMIND_COLUMN_ZH_MAP = {
    "date": "日期",
    "stock_id": "股票代號",
    "open": "開盤價",
    "close": "收盤價",
    "max": "最高價",
    "min": "最低價",
    "Trading_Volume": "成交量",
    "Trading_money": "成交金額",
    "spread": "價差",
    "Trading_turnover": "成交筆數",
}

def localize_ohlcv_columns(df: pd.DataFrame, lang: str = "zh") -> pd.DataFrame:
    """
    只用來做「顯示用」的欄位中文化。
    底層計算請仍然使用原始英文欄位，避免相容性問題。
    """
    if lang != "zh":
        return df

    renamed = df.rename(columns={
        eng: zh for eng, zh in FINMIND_COLUMN_ZH_MAP.items() if eng in df.columns
    })
    return renamed
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from FinMind.data import DataLoader

# 找到專案根目錄（JarvisV1）底下的 .env
ROOT_DIR = Path(__file__).resolve().parents[1]
DOTENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=DOTENV_PATH)

class FinMindClient:
    def __init__(self, api_token: Optional[str] = None) -> None:
        # 統一使用 FINMIND_TOKEN（支援 FINMIND_API_TOKEN 作為 fallback）
        token = api_token or os.getenv("FINMIND_TOKEN") or os.getenv("FINMIND_API_TOKEN")
        if not token:
            raise ValueError("FINMIND_TOKEN not found in environment variables.")

        self.loader = DataLoader()
        self.loader.login_by_token(token)

    def get_stock_daily(
        self,
        stock_id: str,
        start_date: str,
        end_date: Optional[str] = None,
    ):
        """取得台股日 K 資料。日期格式：YYYY-MM-DD"""
        params = {
            "stock_id": stock_id,
            "start_date": start_date,
        }
        if end_date:
            params["end_date"] = end_date

        data = self.loader.taiwan_stock_daily(**params)
        return data
