from pathlib import Path
import sqlite3
from typing import Iterator


def get_connection() -> sqlite3.Connection:
    """
    回傳 SQLite 連線物件，資料庫檔案位於 project_root/data/jgod_tw_stock.db
    第一次呼叫時會自動建立下列四張表（若不存在）：
    - tw_stock_daily
    - tw_index_daily
    - tw_stock_institutional
    - tw_stock_fundamentals
    """
    # 定位專案根目錄（jgod 目錄的上上層）並建立 data 資料夾
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    db_path = data_dir / "jgod_tw_stock.db"

    conn = sqlite3.connect(str(db_path))
    # 建表語句（使用 IF NOT EXISTS）
    sql_tw_stock_daily = """
    CREATE TABLE IF NOT EXISTS tw_stock_daily (
        trade_date TEXT,
        stock_id TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL,
        turnover REAL,
        updated_at TEXT,
        PRIMARY KEY (trade_date, stock_id)
    );
    """

    sql_tw_index_daily = """
    CREATE TABLE IF NOT EXISTS tw_index_daily (
        trade_date TEXT,
        index_id TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL,
        updated_at TEXT,
        PRIMARY KEY (trade_date, index_id)
    );
    """

    sql_tw_stock_institutional = """
    CREATE TABLE IF NOT EXISTS tw_stock_institutional (
        trade_date TEXT,
        stock_id TEXT,
        foreign_buy REAL,
        foreign_sell REAL,
        dealer_buy REAL,
        dealer_sell REAL,
        investment_buy REAL,
        investment_sell REAL,
        updated_at TEXT,
        PRIMARY KEY (trade_date, stock_id)
    );
    """

    sql_tw_stock_fundamentals = """
    CREATE TABLE IF NOT EXISTS tw_stock_fundamentals (
        stock_id TEXT,
        quarter TEXT,
        revenue REAL,
        eps REAL,
        roe REAL,
        roa REAL,
        gross_margin REAL,
        operating_margin REAL,
        net_margin REAL,
        updated_at TEXT,
        PRIMARY KEY (stock_id, quarter)
    );
    """

    # 使用 executescript 一次建立所有表
    conn.executescript("\n".join([
        sql_tw_stock_daily,
        sql_tw_index_daily,
        sql_tw_stock_institutional,
        sql_tw_stock_fundamentals,
    ]))

    conn.commit()
    return conn


if __name__ == "__main__":
    conn = get_connection()
    print("DB 初始化成功")
