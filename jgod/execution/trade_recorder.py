"""
交易記錄器：記錄交易到 CSV 和 SQLite
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import csv
import sqlite3
import json

from .virtual_broker import Fill


class TradeRecorder:
    """
    交易記錄器
    
    功能：
    - 記錄交易到 CSV
    - 記錄交易到 SQLite
    - 讀取交易歷史
    """
    
    def __init__(
        self,
        csv_path: Optional[Path] = None,
        db_path: Optional[Path] = None,
    ):
        """
        初始化交易記錄器
        
        Args:
            csv_path: CSV 檔案路徑
            db_path: SQLite 資料庫路徑
        """
        if csv_path is None:
            csv_path = Path("data/trades.csv")
        if db_path is None:
            db_path = Path("data/trades.db")
        
        self.csv_path = csv_path
        self.db_path = db_path
        
        # 確保目錄存在
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化資料庫
        self._init_database()
    
    def _init_database(self) -> None:
        """初始化資料庫表格"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                slippage REAL DEFAULT 0.0,
                commission REAL DEFAULT 0.0,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_trade(self, fill: Fill) -> None:
        """
        記錄交易
        
        Args:
            fill: 成交記錄
        """
        # 記錄到 CSV
        self._write_csv(fill)
        
        # 記錄到 SQLite
        self._write_db(fill)
    
    def _write_csv(self, fill: Fill) -> None:
        """寫入 CSV"""
        file_exists = self.csv_path.exists()
        
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # 寫入標題（如果檔案不存在）
            if not file_exists:
                writer.writerow([
                    "timestamp", "symbol", "side", "quantity",
                    "price", "slippage", "commission", "filled_time"
                ])
            
            # 寫入資料
            writer.writerow([
                fill.order.timestamp.isoformat(),
                fill.order.symbol,
                fill.order.side,
                fill.filled_quantity,
                fill.filled_price,
                fill.slippage,
                fill.commission,
                fill.filled_time.isoformat(),
            ])
    
    def _write_db(self, fill: Fill) -> None:
        """寫入資料庫"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trades (
                timestamp, symbol, side, quantity, price,
                slippage, commission, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fill.order.timestamp.isoformat(),
            fill.order.symbol,
            fill.order.side,
            fill.filled_quantity,
            fill.filled_price,
            fill.slippage,
            fill.commission,
            json.dumps({}),
        ))
        
        conn.commit()
        conn.close()
    
    def get_trade_history(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        取得交易歷史
        
        Args:
            symbol: 股票代號（如果為 None 則取得所有）
            start_date: 開始日期
            end_date: 結束日期
        
        Returns:
            交易記錄列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_trade_summary(self) -> Dict[str, Any]:
        """
        取得交易摘要
        
        Returns:
            交易摘要字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 總交易數
        cursor.execute("SELECT COUNT(*) FROM trades")
        total_trades = cursor.fetchone()[0]
        
        # 買入/賣出統計
        cursor.execute("""
            SELECT side, COUNT(*), SUM(quantity * price)
            FROM trades
            GROUP BY side
        """)
        side_stats = {row[0]: {"count": row[1], "value": row[2]} for row in cursor.fetchall()}
        
        # 總手續費
        cursor.execute("SELECT SUM(commission) FROM trades")
        total_commission = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        return {
            "total_trades": total_trades,
            "side_stats": side_stats,
            "total_commission": total_commission,
        }

