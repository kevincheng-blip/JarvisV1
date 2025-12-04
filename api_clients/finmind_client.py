"""
FinMind API Client

Thin wrapper around FinMind.DataLoader for J-GOD stock indicator pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

import pandas as pd

try:
    # 假設已安裝 FinMind 官方套件
    from FinMind.data import DataLoader
except ImportError:  # pragma: no cover
    DataLoader = None


@dataclass
class FinMindClientConfig:
    api_token: Optional[str] = None
    # 預留：未來可加入 proxy、timeout 等設定


class FinMindClient:
    """
    Thin wrapper around FinMind.DataLoader
    for J-GOD stock indicator pipeline.
    """

    def __init__(self, config: FinMindClientConfig):
        if DataLoader is None:
            raise ImportError("FinMind package not installed. Please `pip install FinMind` first.")

        self.config = config
        self.loader = DataLoader()
        if config.api_token:
            self.loader.login_by_token(api_token=config.api_token)

    # -------------------- 基本價量 --------------------
    def get_daily_price(
        self,
        stock_id: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        df = self.loader.taiwan_stock_daily(
            stock_id=stock_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        # 統一欄位名稱
        if not df.empty:
            df = df.rename(
                columns={
                    "date": "date",
                    "open": "open",
                    "max": "high",
                    "min": "low",
                    "close": "close",
                    "Trading_Volume": "volume",
                }
            )
            df["date"] = pd.to_datetime(df["date"])
        return df

    # -------------------- 三大法人 --------------------
    def get_institutional_investors(
        self,
        stock_id: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        df = self.loader.taiwan_stock_institutional_investors(
            stock_id=stock_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

    # -------------------- 融資券 --------------------
    def get_margin_short(
        self,
        stock_id: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        df = self.loader.taiwan_stock_margin_purchase_short_sale(
            stock_id=stock_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

    # -------------------- 大戶/散戶持股 --------------------
    def get_shareholding(
        self,
        stock_id: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        df = self.loader.taiwan_stock_shareholding(
            stock_id=stock_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

    # -------------------- 當沖比率 --------------------
    def get_day_trading(
        self,
        stock_id: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        df = self.loader.taiwan_stock_day_trading(
            stock_id=stock_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

    # -------------------- 月營收 --------------------
    def get_month_revenue(
        self,
        stock_id: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        df = self.loader.taiwan_stock_month_revenue(
            stock_id=stock_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

    # -------------------- 財報：損益、資產負債、現金流 --------------------
    def get_financial_statement(
        self,
        stock_id: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        # FinMind 會回多種報表，這裡先全部取回，IndicatorBuilder 再拆
        df = self.loader.taiwan_stock_financial_statement(
            stock_id=stock_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

    def get_balance_sheet(
        self,
        stock_id: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        df = self.loader.taiwan_stock_balance_sheet(
            stock_id=stock_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

    def get_cash_flow(
        self,
        stock_id: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        df = self.loader.taiwan_stock_cash_flows_statement(
            stock_id=stock_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df
