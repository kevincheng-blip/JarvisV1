"""
資料載入器：整合 FinMind 和 yfinance 抓取台股/美股資料
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from api_clients.finmind_client import FinMindClient


class DataLoader:
    """
    資料載入器
    
    功能：
    - 抓取台股資料（透過 FinMind）
    - 抓取美股資料（透過 yfinance）
    - 統一資料格式
    """
    
    def __init__(self):
        """初始化資料載入器"""
        self.finmind_client = FinMindClient()
        self._yfinance_available = self._check_yfinance()
    
    def _check_yfinance(self) -> bool:
        """檢查 yfinance 是否可用"""
        try:
            import yfinance
            return True
        except ImportError:
            return False
    
    def load_taiwan_stock(
        self,
        stock_id: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        載入台股資料
        
        Args:
            stock_id: 股票代號（例如：2330）
            start_date: 開始日期（YYYY-MM-DD）
            end_date: 結束日期（YYYY-MM-DD）
        
        Returns:
            包含 OHLCV 資料的 DataFrame
        """
        try:
            df = self.finmind_client.get_stock_daily(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if isinstance(df, pd.DataFrame) and not df.empty:
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"載入台股資料失敗 {stock_id}: {e}")
            return pd.DataFrame()
    
    def load_us_stock(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        載入美股資料
        
        Args:
            symbol: 股票代號（例如：AAPL）
            start_date: 開始日期（YYYY-MM-DD）
            end_date: 結束日期（YYYY-MM-DD）
        
        Returns:
            包含 OHLCV 資料的 DataFrame
        """
        if not self._yfinance_available:
            print("yfinance 未安裝，無法載入美股資料")
            return pd.DataFrame()
        
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                return pd.DataFrame()
            
            # 標準化欄位名稱
            df = df.reset_index()
            df.columns = [col.lower() if col != "Date" else "date" for col in df.columns]
            
            # 確保有 date 欄位
            if "date" not in df.columns and "Date" in df.columns:
                df["date"] = df["Date"]
            
            # 標準化欄位
            column_mapping = {
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
            }
            
            result_df = pd.DataFrame()
            for std_col, possible_cols in [
                ("date", ["date", "Date"]),
                ("open", ["open", "Open"]),
                ("high", ["high", "High"]),
                ("low", ["low", "Low"]),
                ("close", ["close", "Close"]),
                ("volume", ["volume", "Volume"]),
            ]:
                for col in possible_cols:
                    if col in df.columns:
                        result_df[std_col] = df[col]
                        break
            
            return result_df
        except Exception as e:
            print(f"載入美股資料失敗 {symbol}: {e}")
            return pd.DataFrame()
    
    def load_index(
        self,
        index_id: str,
        start_date: str,
        end_date: str,
        market: str = "taiwan",
    ) -> pd.DataFrame:
        """
        載入指數資料
        
        Args:
            index_id: 指數代號
            start_date: 開始日期
            end_date: 結束日期
            market: 市場（taiwan 或 us）
        
        Returns:
            包含指數資料的 DataFrame
        """
        if market == "taiwan":
            # 使用 FinMind 載入台股指數
            try:
                loader = getattr(self.finmind_client, "loader", None)
                if loader and hasattr(loader, "taiwan_stock_index"):
                    df = loader.taiwan_stock_index(
                        index_id=index_id,
                        start_date=start_date,
                        end_date=end_date
                    )
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        return df
            except Exception:
                pass
            
            # Fallback: 嘗試用 get_stock_daily
            return self.load_taiwan_stock(index_id, start_date, end_date)
        else:
            # 美股指數
            return self.load_us_stock(index_id, start_date, end_date)

