"""
Indicator Builder for 100-Indicator Framework

Build 100-indicator dict for StockUpsideFilter60V1.evaluate()
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd

import sys
from pathlib import Path

# Add project root to path for api_clients import
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from api_clients.finmind_client import FinMindClient, FinMindClientConfig


@dataclass
class IndicatorBuilderConfig:
    """
    Config for building 100-indicator input dict.
    """
    lookback_days_price: int = 180
    lookback_days_capital: int = 60
    lookback_months_fundamental: int = 12


class StockIndicatorBuilder100:
    """
    Build 100-indicator dict for StockUpsideFilter60V1.evaluate()

    Output:
        Dict[str, Any], keys = P01..P12, C01..C09, F01..F08,
                             K01..K07, S01..S06, Q01..Q06,
                             X01..X16, M01..M36
    """

    def __init__(self, finmind_token: Optional[str] = None, config: Optional[IndicatorBuilderConfig] = None):
        self.config = config or IndicatorBuilderConfig()
        self.client = FinMindClient(FinMindClientConfig(api_token=finmind_token))

    # ======================================================================
    # Public API
    # ======================================================================
    def build_indicators(
        self,
        stock_id: str,
        as_of: date,
    ) -> Dict[str, Any]:
        """
        Main entry: build 100-indicator snapshot for a single stock on a specific date.
        """
        start_price = as_of - timedelta(days=self.config.lookback_days_price)
        start_capital = as_of - timedelta(days=self.config.lookback_days_capital)
        start_fundamental = as_of.replace(year=as_of.year - 2)

        # 1) 基本價量
        price_df = self.client.get_daily_price(stock_id, start_price, as_of)

        # 2) 三大法人 + 融資券 + 持股結構
        inst_df = self.client.get_institutional_investors(stock_id, start_capital, as_of)
        margin_df = self.client.get_margin_short(stock_id, start_capital, as_of)
        share_df = self.client.get_shareholding(stock_id, start_capital, as_of)
        daytrade_df = self.client.get_day_trading(stock_id, start_capital, as_of)

        # 3) 營收 & 財報
        revenue_df = self.client.get_month_revenue(stock_id, start_fundamental, as_of)
        fs_df = self.client.get_financial_statement(stock_id, start_fundamental, as_of)
        bs_df = self.client.get_balance_sheet(stock_id, start_fundamental, as_of)
        cf_df = self.client.get_cash_flow(stock_id, start_fundamental, as_of)

        indicators: Dict[str, Any] = {}

        # -------------------- P 系列：價量技術 --------------------
        indicators.update(self._build_price_indicators(price_df))

        # -------------------- C 系列：籌碼 ------------------------
        indicators.update(self._build_capital_indicators(inst_df, margin_df, share_df, daytrade_df))

        # -------------------- F 系列：財報 ------------------------
        indicators.update(self._build_fundamental_indicators(revenue_df, fs_df, bs_df, cf_df))

        # -------------------- K / S / Q / X / M 系列：先 placeholder ----------------
        indicators.update(self._build_placeholder_k_s_q_x_m(indicators))

        return indicators

    # ======================================================================
    # Internal helpers: Price
    # ======================================================================
    def _build_price_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        out: Dict[str, Any] = {f"P{idx:02d}": 0.0 for idx in range(1, 13)}
        if df.empty:
            return out

        df = df.sort_values("date").set_index("date")
        # 確保欄位
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                return out

        # MA
        df["ma20"] = df["close"].rolling(20).mean()
        df["ma60"] = df["close"].rolling(60).mean()
        df["ma120"] = df["close"].rolling(120).mean()

        # 斜率（簡單用最近 N 天線性回歸近似）
        def slope(series: pd.Series, window: int = 20) -> float:
            s = series.dropna()
            if len(s) < window:
                return 0.0
            s = s.iloc[-window:]
            x = np.arange(len(s))
            # 線性回歸 slope
            A = np.vstack([x, np.ones(len(x))]).T
            m, _ = np.linalg.lstsq(A, s.values, rcond=None)[0]
            return float(m)

        last = df.iloc[-1]

        # P01: 趨勢斜率（用 ma20 slope）
        out["P01"] = slope(df["ma20"], window=20)

        # P02: 多頭均線排列
        if last["ma20"] > last["ma60"] > last["ma120"]:
            out["P02"] = 1.0
        else:
            out["P02"] = -1.0

        # P03: 均線糾結突破（ma20/60/120 之間距小、且收盤大於三線）
        ma_spread = (df["ma120"] - df["ma20"]).abs().iloc[-1]
        if ma_spread / last["close"] < 0.03 and last["close"] > max(last["ma20"], last["ma60"], last["ma120"]):
            out["P03"] = 1.0

        # P04: K 棒結構（長紅 or 長下影）
        body = abs(last["close"] - df["open"].iloc[-1])
        total_range = df["high"].iloc[-1] - df["low"].iloc[-1]
        if total_range > 0 and body / total_range > 0.6 and last["close"] > df["open"].iloc[-1]:
            out["P04"] = 1.0  # 多方 K 棒

        # P05: 支撐/壓力（用近 N 日高低的相對位置）
        recent_high = df["high"].tail(60).max()
        recent_low = df["low"].tail(60).min()
        if last["close"] > recent_high:
            out["P05"] = 1.0  # 突破壓力
        elif last["close"] < recent_low:
            out["P05"] = -1.0  # 跌破支撐

        # P06: 缺口（今日開盤 vs 昨日收盤）
        if len(df) >= 2:
            prev_close = df["close"].iloc[-2]
            today_open = df["open"].iloc[-1]
            gap = (today_open - prev_close) / prev_close if prev_close != 0 else 0
            if gap > 0.02:
                out["P06"] = 1.0
            elif gap < -0.02:
                out["P06"] = -1.0

        # P07: 量能結構（近 N 日放量上漲 & 縮量回檔）
        vol_ma20 = df["volume"].rolling(20).mean()
        today_vol = df["volume"].iloc[-1]
        if today_vol > vol_ma20.iloc[-1] * 1.5 and last["close"] > df["close"].iloc[-2]:
            out["P07"] = 1.0  # 放量上漲

        # P08: 量價背離（價漲量縮或價跌量增）
        if len(df) >= 3:
            close_change = df["close"].pct_change().iloc[-1]
            vol_change = df["volume"].pct_change().iloc[-1]
            if close_change > 0 and vol_change < 0:
                out["P08"] = -1.0  # 價漲量縮
            elif close_change < 0 and vol_change > 0:
                out["P08"] = -1.0  # 價跌量增

        # P09: 布林通道
        ma20 = df["close"].rolling(20).mean()
        std20 = df["close"].rolling(20).std()
        upper = ma20 + 2 * std20
        lower = ma20 - 2 * std20
        if last["close"] > upper.iloc[-1]:
            out["P09"] = 1.0
        elif last["close"] < lower.iloc[-1]:
            out["P09"] = -1.0

        # P10: RSI/KD/MACD 動能（簡化版：RSI）
        # RSI 14 day
        delta = df["close"].diff()
        up = delta.clip(lower=0).rolling(14).mean()
        down = -delta.clip(upper=0).rolling(14).mean()
        rs = up / (down + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        rsi_last = float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0
        out["P10"] = (rsi_last - 50.0) / 50.0  # 中心化

        # P11: ATR 波動度
        high_low = df["high"] - df["low"]
        high_prev_close = (df["high"] - df["close"].shift(1)).abs()
        low_prev_close = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        if last["close"] != 0:
            out["P11"] = float(atr.iloc[-1] / last["close"])

        # P12: VAP 套牢壓力（v1 先留 0，未來實作）
        # TODO: implement VAP based on price and volume distribution

        return out

    # ======================================================================
    # Internal helpers: Capital
    # ======================================================================
    def _build_capital_indicators(
        self,
        inst_df: pd.DataFrame,
        margin_df: pd.DataFrame,
        share_df: pd.DataFrame,
        daytrade_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        out: Dict[str, Any] = {f"C{idx:02d}": 0.0 for idx in range(1, 10)}

        # C01, C02, C03: 外資、投信、自營連續買賣超強度
        if not inst_df.empty:
            inst_df = inst_df.sort_values("date")
            last_date = inst_df["date"].max()
            recent = inst_df[inst_df["date"] >= last_date - pd.Timedelta(days=10)]
            # FinMind 欄位名稱示意：foreign_buy/sell, investment_trust_buy/sell, dealer_buy/sell
            def net_and_streak(buy_col: str, sell_col: str) -> float:
                if buy_col not in recent.columns or sell_col not in recent.columns:
                    return 0.0
                recent["net"] = recent[buy_col] - recent[sell_col]
                # 連續正或負天數
                streak = 0
                for v in reversed(recent["net"].tolist()):
                    if v > 0:
                        if streak >= 0:
                            streak += 1
                        else:
                            break
                    elif v < 0:
                        if streak <= 0:
                            streak -= 1
                        else:
                            break
                    else:
                        break
                return float(streak)

            out["C01"] = net_and_streak("foreign_buy", "foreign_sell")
            out["C02"] = net_and_streak("investment_trust_buy", "investment_trust_sell")
            out["C03"] = net_and_streak("dealer_buy", "dealer_sell")

        # C08, C09: 融資、融券變化
        if not margin_df.empty:
            margin_df = margin_df.sort_values("date")
            if len(margin_df) >= 2:
                margin_df["margin_change"] = margin_df["MarginPurchaseToday"].diff()
                margin_df["short_change"] = margin_df["ShortSaleToday"].diff()
                out["C08"] = float(margin_df["margin_change"].iloc[-1])
                out["C09"] = float(margin_df["short_change"].iloc[-1])

        # C04, C05: 大戶/散戶比例（FinMind 欄位 dependent）
        if not share_df.empty:
            share_df = share_df.sort_values("date")
            last = share_df.iloc[-1]
            # 假設 FinMind 有 big_dealer_ratio, retail_ratio 類似欄位
            if "big_dealer_ratio" in last:
                out["C04"] = float(last["big_dealer_ratio"])
            if "retail_ratio" in last:
                out["C05"] = float(last["retail_ratio"])

        # C06, C07, C06(分點), C07(主力成本) v1 先留 0，未來用分點 + VWAP 實作
        # C06: 分點籌碼
        # C07: 主力成本
        # TODO: implement with daytrade_df + 分點資料

        return out

    # ======================================================================
    # Internal helpers: Fundamental
    # ======================================================================
    def _build_fundamental_indicators(
        self,
        revenue_df: pd.DataFrame,
        fs_df: pd.DataFrame,
        bs_df: pd.DataFrame,
        cf_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        out: Dict[str, Any] = {f"F{idx:02d}": 0.0 for idx in range(1, 9)}

        # F01: 營收成長（近 3 月 avg YoY）
        if not revenue_df.empty:
            revenue_df = revenue_df.sort_values("date")
            revenue_df["YoY"] = revenue_df["revenue"].pct_change(12)
            last3 = revenue_df["YoY"].tail(3).dropna()
            if not last3.empty:
                out["F01"] = float(last3.mean() * 100)

        # 財報資料會依 FinMind 欄位命名調整，這裡給示意邏輯
        # F02: 毛利率
        # F03: 營益率
        # F04: EPS
        if not fs_df.empty:
            fs_df = fs_df.sort_values("date")
            last_fs = fs_df.iloc[-1]
            # 以下欄位名稱需依實際 FinMind 欄位修正
            if "gross_profit" in last_fs and "operating_revenue" in last_fs:
                gp = last_fs["gross_profit"]
                rev = last_fs["operating_revenue"]
                out["F02"] = float((gp / rev) * 100) if rev else 0.0
            if "operating_income" in last_fs and "operating_revenue" in last_fs:
                op = last_fs["operating_income"]
                rev = last_fs["operating_revenue"]
                out["F03"] = float((op / rev) * 100) if rev else 0.0
            if "eps" in last_fs:
                out["F04"] = float(last_fs["eps"])

        # F05: FCF（營運現金流 - 資本支出）
        if not cf_df.empty:
            cf_df = cf_df.sort_values("date")
            last_cf = cf_df.iloc[-1]
            # 假設欄位名稱 operating_cash_flow, capital_expenditure
            ocf = float(last_cf.get("operating_cash_flow", 0.0))
            capex = float(last_cf.get("capital_expenditure", 0.0))
            out["F05"] = ocf - capex

        # F06, F07, F08：ROE/ROA/負債比/股東權益成長
        if not bs_df.empty:
            bs_df = bs_df.sort_values("date")
            last_bs = bs_df.iloc[-1]
            # 欄位名稱示意，需依實際 FinMind 欄位修正
            total_assets = float(last_bs.get("total_assets", 0.0))
            total_equity = float(last_bs.get("total_equity", 0.0))
            total_liabilities = float(last_bs.get("total_liabilities", 0.0))

            # F07: 負債比
            if total_assets:
                out["F07"] = (total_liabilities / total_assets) * 100

            # F06: ROE/ROA（v1 可以先用近一年 EPS * 股本估算 or 用 fs_df 的 net_income）
            if not fs_df.empty:
                net_income = float(fs_df.sort_values("date").iloc[-1].get("net_income", 0.0))
                if total_equity:
                    roe = net_income / total_equity
                    out["F06"] = roe * 100

            # F08: 股東權益成長（YoY）
            bs_df_eq = bs_df[["date", "total_equity"]].dropna()
            if len(bs_df_eq) >= 5:
                bs_df_eq = bs_df_eq.sort_values("date")
                # 取最近兩個年度點
                last2 = bs_df_eq.tail(2)
                eq_prev, eq_last = last2["total_equity"].iloc[0], last2["total_equity"].iloc[1]
                if eq_prev:
                    out["F08"] = (eq_last / eq_prev - 1) * 100

        return out

    # ======================================================================
    # K / S / Q / X / M placeholder
    # ======================================================================
    def _build_placeholder_k_s_q_x_m(self, base_indicators: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}

        # K 系列：先全部 0.0
        for idx in range(1, 8):
            out[f"K{idx:02d}"] = 0.0

        # S 系列：v1 先 0.0，未來接 TSMC/NASDAQ/FX/VIX
        for idx in range(1, 7):
            out[f"S{idx:02d}"] = 0.0

        # Q 系列：先用 P11 波動度填 Q02，其餘 0
        out["Q01"] = 0.0  # Sharpe
        out["Q02"] = float(base_indicators.get("P11", 0.0))  # 波動度 proxy
        out["Q03"] = 0.0  # MDD
        out["Q04"] = 0.0  # Beta
        out["Q05"] = 0.0  # Factor Exposure
        out["Q06"] = 0.0  # Concentration

        # X 系列：衍生品 + 微觀 v1 先 0.0
        for idx in range(1, 17):
            out[f"X{idx:02d}"] = 0.0

        # M 系列：Meta / Composite v1 先 0.0
        for idx in range(1, 37):
            out[f"M{idx:02d}"] = 0.0

        return out

