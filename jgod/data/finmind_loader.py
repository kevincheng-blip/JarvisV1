import sys
from pathlib import Path

# 讓專案根目錄加入 PYTHONPATH
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

import datetime
from typing import Optional

import pandas as pd

from jgod.data.db import get_connection
from api_clients.finmind_client import FinMindClient


def _to_float_or_none(x) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def load_stock_daily(stock_id: str, start_date: str, end_date: str) -> int:
    """
    從 FinMind 抓取指定台股 stock_id 在 [start_date, end_date] 區間內的日線資料，
    寫入 tw_stock_daily 資料表。
    回傳實際寫入（insert or replace）的列數。
    """
    client = FinMindClient()
    # 使用 FinMindClient 的 loader 呼叫現有方法
    loader = getattr(client, "loader", None)
    if loader is None:
        # fallback to client's get_stock_daily method
        df = client.get_stock_daily(stock_id=stock_id, start_date=start_date, end_date=end_date)
    else:
        # 優先使用 taiwan_stock_daily
        if hasattr(loader, "taiwan_stock_daily"):
            df = loader.taiwan_stock_daily(stock_id=stock_id, start_date=start_date, end_date=end_date)
        else:
            # fallback
            df = client.get_stock_daily(stock_id=stock_id, start_date=start_date, end_date=end_date)

    # 確保為 pandas.DataFrame
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    # 標準欄位對應
    rows_to_insert = []
    now = datetime.datetime.utcnow().isoformat()

    for _, row in df.iterrows():
        trade_date = row.get("date")
        sid = row.get("stock_id") if "stock_id" in row.index else stock_id
        open_p = _to_float_or_none(row.get("open"))
        high_p = _to_float_or_none(row.get("max") or row.get("high"))
        low_p = _to_float_or_none(row.get("min") or row.get("low"))
        close_p = _to_float_or_none(row.get("close"))
        # volume 欄位可能為 Trading_Volume/Trading_Volume
        volume = _to_float_or_none(
            row.get("Trading_Volume")
            or row.get("Trading_Volume")
            or row.get("volume")
            or row.get("TradingVolume")
            or row.get("volume_traded")
        )
        turnover = _to_float_or_none(
            row.get("Trading_money") or row.get("Trading_money") or row.get("turnover") or row.get("Trading_turnover")
        )

        rows_to_insert.append((
            trade_date,
            sid,
            open_p,
            high_p,
            low_p,
            close_p,
            volume,
            turnover,
            now,
        ))

    if not rows_to_insert:
        return 0

    conn = get_connection()
    cur = conn.cursor()
    sql = (
        "INSERT OR REPLACE INTO tw_stock_daily"
        "(trade_date, stock_id, open, high, low, close, volume, turnover, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"
    )

    try:
        cur.executemany(sql, rows_to_insert)
        conn.commit()
        return cur.rowcount
    finally:
        cur.close()


def load_index_daily(index_id: str, start_date: str, end_date: str) -> int:
    """
    從 FinMind 抓取指定台股指數（例如 TAIEX / OTC）在區間內的日線資料，
    寫入 tw_index_daily 資料表。
    回傳實際寫入列數。
    """
    client = FinMindClient()
    loader = getattr(client, "loader", None)

    df = None
    if loader is not None:
        # 優先嘗試 taiwan_stock_index
        if hasattr(loader, "taiwan_stock_index"):
            df = loader.taiwan_stock_index(index_id=index_id, start_date=start_date, end_date=end_date)
        elif hasattr(loader, "taiwan_stock_index_daily"):
            df = loader.taiwan_stock_index_daily(index_id=index_id, start_date=start_date, end_date=end_date)

    # 若仍為 None，嘗試用 client 的 get_stock_daily（部分指數可能可用於此方法）
    if df is None:
        try:
            df = client.get_stock_daily(stock_id=index_id, start_date=start_date, end_date=end_date)
        except Exception:
            df = pd.DataFrame()

    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    now = datetime.datetime.utcnow().isoformat()
    rows_to_insert = []

    for _, row in df.iterrows():
        trade_date = row.get("date")
        idx = row.get("index_id") if "index_id" in row.index else index_id
        open_p = _to_float_or_none(row.get("open") or row.get("Open"))
        high_p = _to_float_or_none(row.get("max") or row.get("high"))
        low_p = _to_float_or_none(row.get("min") or row.get("low"))
        close_p = _to_float_or_none(row.get("close") or row.get("Close"))
        volume = _to_float_or_none(row.get("Trading_Volume") or row.get("volume") or row.get("volume_traded") )

        rows_to_insert.append((
            trade_date,
            idx,
            open_p,
            high_p,
            low_p,
            close_p,
            volume,
            now,
        ))

    if not rows_to_insert:
        return 0

    conn = get_connection()
    cur = conn.cursor()
    sql = (
        "INSERT OR REPLACE INTO tw_index_daily"
        "(trade_date, index_id, open, high, low, close, volume, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
    )

    try:
        cur.executemany(sql, rows_to_insert)
        conn.commit()
        return cur.rowcount
    finally:
        cur.close()


if __name__ == "__main__":
    # 測試：抓取台積電（2330）指定區間日線
    rows = load_stock_daily("2330", "2025-01-01", "2025-01-31")
    print(f"寫入 tw_stock_daily 列數：{rows}")
