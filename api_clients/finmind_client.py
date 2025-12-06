"""
FinMind API Client

Thin wrapper around FinMind.DataLoader for J-GOD stock indicator pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

import logging
import os
from datetime import date
from typing import Optional

import pandas as pd

try:
    # 假設已安裝 FinMind 官方套件
    from FinMind.data import DataLoader
except ImportError:  # pragma: no cover
    DataLoader = None

from jgod.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


@dataclass
class FinMindClientConfig:
    api_token: Optional[str] = None
    # 預留：未來可加入 proxy、timeout 等設定


class FinMindClient:
    """Thin wrapper around FinMind DataLoader with rate limiting support.

    This client is used by:
    - StockIndicatorBuilder100
    - Backfill scripts
    - Rule-based stock upside evaluation

    All external API calls should go through this client so that
    rate limiting can be applied consistently.
    """

    def __init__(
        self,
        config: Optional[FinMindClientConfig] = None,
        finmind_token: Optional[str] = None,
        rate_limiter: Optional[RateLimiter] = None,
        max_calls_per_minute: int = 80,
        max_calls_per_hour: int = 5800,
    ) -> None:
        if DataLoader is None:
            raise ImportError("FinMind package not installed. Please `pip install FinMind` first.")

        # Support both old config pattern and new direct token pattern
        if config is not None:
            api_token = config.api_token
        else:
            api_token = finmind_token

        self.loader = DataLoader()

        token = api_token or os.getenv("FINMIND_API_TOKEN")
        if not token:
            logger.warning(
                "FinMindClient initialized without FINMIND_API_TOKEN. "
                "API calls will likely fail."
            )
        else:
            try:
                self.loader.login_by_token(api_token=token)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to login FinMind by token: %s", exc)

        # Shared rate limiter for all FinMind calls
        self.rate_limiter = rate_limiter or RateLimiter(
            minute_limit=max_calls_per_minute,
            hour_limit=max_calls_per_hour,
        )

    def _acquire(self, label: str) -> None:
        """Acquire a rate-limit slot before calling FinMind."""
        if self.rate_limiter is not None:
            self.rate_limiter.acquire(label)

    # -------------------- 基本價量 --------------------
    def get_daily_price(
        self,
        stock_id: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        self._acquire("price")

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
        self._acquire("capital_institutions")

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
        self._acquire("margin_short")

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
        self._acquire("shareholding")

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
        self._acquire("day_trading")

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
        self._acquire("revenue")

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
        self._acquire("financials")

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
        self._acquire("balance_sheet")

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
        self._acquire("cash_flow")

        df = self.loader.taiwan_stock_cash_flows_statement(
            stock_id=stock_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df
