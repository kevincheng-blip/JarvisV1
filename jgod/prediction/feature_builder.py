"""
特徵建構器：從市場資料中提取預測特徵
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional
import pandas as pd
import numpy as np

from jgod.market.data_loader import DataLoader
from jgod.market.indicators import TechnicalIndicators


@dataclass
class FeatureRow:
    """特徵資料列"""
    symbol: str
    trade_date: date
    close: float
    pct_change_1d: float
    pct_change_3d: float
    pct_change_5d: float
    volume: float
    volume_ratio_5d: float
    ma_5: float
    ma_20: float
    rsi_14: float


def _parse_date(date_input: date | str) -> date:
    """
    將日期輸入轉換為 date 物件
    
    Args:
        date_input: date 物件或 "YYYY-MM-DD" 字串
    
    Returns:
        date 物件
    """
    if isinstance(date_input, str):
        return date.fromisoformat(date_input)
    return date_input


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    標準化 DataFrame 欄位名稱
    
    Args:
        df: 原始 DataFrame
    
    Returns:
        標準化後的 DataFrame
    """
    if df.empty:
        return df
    
    result = df.copy()
    
    # 標準化日期欄位
    if "date" not in result.columns:
        # 嘗試其他可能的日期欄位名稱
        for col in ["Date", "trade_date", "TradeDate"]:
            if col in result.columns:
                result["date"] = result[col]
                break
    
    # 標準化價格欄位
    price_mapping = {
        "Close": "close",
        "close_price": "close",
        "max": "high",
        "Max": "high",
        "high_price": "high",
        "min": "low",
        "Min": "low",
        "low_price": "low",
        "Open": "open",
        "open_price": "open",
    }
    
    for old_col, new_col in price_mapping.items():
        if old_col in result.columns and new_col not in result.columns:
            result[new_col] = result[old_col]
    
    # 標準化成交量欄位
    volume_mapping = {
        "Trading_Volume": "volume",
        "Volume": "volume",
        "volume_traded": "volume",
    }
    
    for old_col, new_col in volume_mapping.items():
        if old_col in result.columns and new_col not in result.columns:
            result[new_col] = result[old_col]
    
    # 確保日期是 date 類型
    if "date" in result.columns:
        if result["date"].dtype == "object":
            result["date"] = pd.to_datetime(result["date"]).dt.date
        elif hasattr(result["date"].dtype, "tz"):
            result["date"] = pd.to_datetime(result["date"]).dt.date
    
    # 排序（由舊到新）
    if "date" in result.columns:
        result = result.sort_values("date").reset_index(drop=True)
    
    return result


def _calculate_features_for_symbol(
    symbol: str,
    end_date: date,
    lookback_days: int,
    min_data_days: int = 20,
) -> Optional[FeatureRow]:
    """
    為單一股票計算特徵
    
    Args:
        symbol: 股票代號
        end_date: 結束日期
        lookback_days: 回看天數
        min_data_days: 最少需要的資料天數
    
    Returns:
        FeatureRow 物件，如果資料不足則回傳 None
    """
    # 計算開始日期
    start_date = end_date - timedelta(days=lookback_days + 10)  # 多抓一些以確保有足夠資料
    
    # 載入資料
    loader = DataLoader()
    df = loader.load_taiwan_stock(
        stock_id=symbol,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )
    
    if df.empty:
        print(f"skip {symbol}, not enough data")
        return None
    
    # 標準化欄位
    df = _normalize_dataframe(df)
    
    # 過濾到 end_date 之前的資料
    if "date" in df.columns:
        df = df[df["date"] <= end_date].copy()
    
    if df.empty or len(df) < min_data_days:
        print(f"skip {symbol}, not enough data")
        return None
    
    # 確保有必要的欄位
    required_columns = ["date", "close"]
    if not all(col in df.columns for col in required_columns):
        print(f"skip {symbol}, missing required columns")
        return None
    
    # 計算技術指標
    indicators = TechnicalIndicators()
    
    # 計算移動平均線
    df["ma_5"] = indicators.calculate_ma(df, period=5, column="close")
    df["ma_20"] = indicators.calculate_ma(df, period=20, column="close")
    
    # 計算 RSI
    df["rsi_14"] = indicators.calculate_rsi(df, period=14, column="close")
    
    # 取得最後一筆資料（end_date 當天或之前最後一個交易日）
    last_row = df.iloc[-1]
    last_date = last_row["date"]
    
    # 如果最後一筆不是 end_date，檢查是否有足夠資料
    if last_date < end_date - timedelta(days=5):
        print(f"skip {symbol}, data too old (last date: {last_date})")
        return None
    
    # 計算價格變化率
    close = float(last_row["close"])
    
    # pct_change_1d
    if len(df) >= 2:
        prev_close_1d = float(df.iloc[-2]["close"])
        pct_change_1d = (close / prev_close_1d - 1) if prev_close_1d > 0 else 0.0
    else:
        pct_change_1d = 0.0
    
    # pct_change_3d
    if len(df) >= 4:
        prev_close_3d = float(df.iloc[-4]["close"])
        pct_change_3d = (close / prev_close_3d - 1) if prev_close_3d > 0 else 0.0
    else:
        pct_change_3d = 0.0
    
    # pct_change_5d
    if len(df) >= 6:
        prev_close_5d = float(df.iloc[-6]["close"])
        pct_change_5d = (close / prev_close_5d - 1) if prev_close_5d > 0 else 0.0
    else:
        pct_change_5d = 0.0
    
    # 計算成交量比率
    volume = float(last_row.get("volume", 0.0))
    
    if "volume" in df.columns and len(df) >= 6:
        # 過去 5 日平均成交量（不包含今天）
        volume_5d_avg = df.iloc[-6:-1]["volume"].mean()
        volume_ratio_5d = (volume / volume_5d_avg) if volume_5d_avg > 0 else 1.0
    else:
        volume_ratio_5d = 1.0
    
    # 取得技術指標值
    ma_5 = float(last_row.get("ma_5", close))
    ma_20 = float(last_row.get("ma_20", close))
    rsi_14 = float(last_row.get("rsi_14", 50.0))
    
    # 處理 NaN 值
    if pd.isna(ma_5):
        ma_5 = close
    if pd.isna(ma_20):
        ma_20 = close
    if pd.isna(rsi_14):
        rsi_14 = 50.0
    
    return FeatureRow(
        symbol=symbol,
        trade_date=last_date,
        close=close,
        pct_change_1d=pct_change_1d,
        pct_change_3d=pct_change_3d,
        pct_change_5d=pct_change_5d,
        volume=volume,
        volume_ratio_5d=volume_ratio_5d,
        ma_5=ma_5,
        ma_20=ma_20,
        rsi_14=rsi_14,
    )


def build_feature_frame(
    symbols: List[str],
    end_date: date | str,
    lookback_days: int = 60,
) -> pd.DataFrame:
    """
    為多檔股票建構特徵 DataFrame
    
    每一列是一檔股票在某一天的特徵（只保留最後一個交易日）
    
    Args:
        symbols: 股票代號列表
        end_date: 結束日期（date 或 "YYYY-MM-DD" 字串）
        lookback_days: 回看天數（預設：60）
    
    Returns:
        包含所有股票特徵的 DataFrame，欄位包含：
        symbol, trade_date, close, pct_change_1d, pct_change_3d, pct_change_5d,
        volume, volume_ratio_5d, ma_5, ma_20, rsi_14
    """
    # 轉換日期格式
    end_date_obj = _parse_date(end_date)
    
    # 為每檔股票計算特徵
    feature_rows = []
    
    for symbol in symbols:
        feature_row = _calculate_features_for_symbol(
            symbol=symbol,
            end_date=end_date_obj,
            lookback_days=lookback_days,
        )
        
        if feature_row is not None:
            feature_rows.append(feature_row)
    
    # 轉換為 DataFrame
    if not feature_rows:
        # 回傳空的 DataFrame，但包含所有欄位
        return pd.DataFrame(columns=[
            "symbol", "trade_date", "close",
            "pct_change_1d", "pct_change_3d", "pct_change_5d",
            "volume", "volume_ratio_5d",
            "ma_5", "ma_20", "rsi_14",
        ])
    
    # 將 FeatureRow 物件轉換為字典列表
    data = [
        {
            "symbol": row.symbol,
            "trade_date": row.trade_date,
            "close": row.close,
            "pct_change_1d": row.pct_change_1d,
            "pct_change_3d": row.pct_change_3d,
            "pct_change_5d": row.pct_change_5d,
            "volume": row.volume,
            "volume_ratio_5d": row.volume_ratio_5d,
            "ma_5": row.ma_5,
            "ma_20": row.ma_20,
            "rsi_14": row.rsi_14,
        }
        for row in feature_rows
    ]
    
    df = pd.DataFrame(data)
    
    return df


if __name__ == "__main__":
    # 簡單測試：對幾檔股票做 feature 建構
    test_symbols = ["2330", "2317", "1301"]
    df = build_feature_frame(test_symbols, date.today())
    print(df.head())
    print(f"\n總共 {len(df)} 檔股票的特徵資料")
