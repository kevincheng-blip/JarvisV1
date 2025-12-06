"""
Indicator Builder for 100-Indicator Framework

Build 100-indicator dict for StockUpsideFilter60V1.evaluate()
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, Any, Optional
import time

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
        # Use new FinMindClient API (backward compatible)
        self.client = FinMindClient(finmind_token=finmind_token)
        # 每秒最多 1 次 API
        self._api_calls = deque()
        self._max_calls_per_sec = 1

    def _rate_limit(self) -> None:
        """簡單的每秒節流：最多 self._max_calls_per_sec 次"""
        now = time.time()
        # 清理 1 秒前的紀錄
        while self._api_calls and now - self._api_calls[0] > 1.0:
            self._api_calls.popleft()

        if len(self._api_calls) >= self._max_calls_per_sec:
            # 算還要睡多久
            sleep_for = 1.0 - (now - self._api_calls[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
            # 清掉過期的，再更新 now
            now = time.time()
            while self._api_calls and now - self._api_calls[0] > 1.0:
                self._api_calls.popleft()

        # 記錄這次呼叫時間
        self._api_calls.append(time.time())

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
        
        # Handle leap year edge case: 2024-02-29 → 2022-02-29 doesn't exist
        try:
            start_fundamental = as_of.replace(year=as_of.year - 2)
        except ValueError:
            safe_date = as_of - timedelta(days=1)
            start_fundamental = safe_date.replace(year=safe_date.year - 2)

        # 1) 基本價量
        self._rate_limit()
        price_df = self.client.get_daily_price(stock_id, start_price, as_of)

        # 2) 三大法人 + 融資券 + 持股結構
        self._rate_limit()
        inst_df = self.client.get_institutional_investors(stock_id, start_capital, as_of)
        self._rate_limit()
        margin_df = self.client.get_margin_short(stock_id, start_capital, as_of)
        self._rate_limit()
        share_df = self.client.get_shareholding(stock_id, start_capital, as_of)
        self._rate_limit()
        daytrade_df = self.client.get_day_trading(stock_id, start_capital, as_of)

        # 3) 營收 & 財報
        self._rate_limit()
        revenue_df = self.client.get_month_revenue(stock_id, start_fundamental, as_of)
        self._rate_limit()
        fs_df = self.client.get_financial_statement(stock_id, start_fundamental, as_of)
        self._rate_limit()
        bs_df = self.client.get_balance_sheet(stock_id, start_fundamental, as_of)
        self._rate_limit()
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
                # C08: 融資變化（使用 FinMind 正確欄位）
                if "MarginPurchaseTodayBalance" in margin_df.columns and "MarginPurchaseYesterdayBalance" in margin_df.columns:
                    margin_df["margin_change"] = (
                        margin_df["MarginPurchaseTodayBalance"] - margin_df["MarginPurchaseYesterdayBalance"]
                    )
                elif "MarginPurchaseTodayBalance" in margin_df.columns:
                    # 退而求其次，用當日餘額的 diff 當作變化量
                    margin_df["margin_change"] = margin_df["MarginPurchaseTodayBalance"].diff()
                else:
                    # 若欄位仍不存在，避免拋錯，先設為 0
                    margin_df["margin_change"] = 0.0
                
                # C09: 融券變化（使用 FinMind 正確欄位）
                if "ShortSaleTodayBalance" in margin_df.columns and "ShortSaleYesterdayBalance" in margin_df.columns:
                    margin_df["short_change"] = (
                        margin_df["ShortSaleTodayBalance"] - margin_df["ShortSaleYesterdayBalance"]
                    )
                elif "ShortSaleTodayBalance" in margin_df.columns:
                    # 退而求其次，用當日餘額的 diff 當作變化量
                    margin_df["short_change"] = margin_df["ShortSaleTodayBalance"].diff()
                else:
                    # 若欄位仍不存在，避免拋錯，先設為 0
                    margin_df["short_change"] = 0.0
                
                out["C08"] = float(margin_df["margin_change"].iloc[-1]) if "margin_change" in margin_df.columns else 0.0
                out["C09"] = float(margin_df["short_change"].iloc[-1]) if "short_change" in margin_df.columns else 0.0

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
            # 動態偵測營收欄位
            revenue_col = None
            for col in ["revenue", "Revenue", "revenue_amount", "operating_revenue"]:
                if col in revenue_df.columns:
                    revenue_col = col
                    break
            
            if revenue_col:
                revenue_df["YoY"] = revenue_df[revenue_col].pct_change(12)
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
            
            # F02: 毛利率 - 動態偵測欄位
            gross_profit_col = None
            revenue_col_fs = None
            for col in ["gross_profit", "GrossProfit", "gross_profit_amount"]:
                if col in last_fs:
                    gross_profit_col = col
                    break
            for col in ["operating_revenue", "OperatingRevenue", "revenue", "Revenue"]:
                if col in last_fs:
                    revenue_col_fs = col
                    break
            
            if gross_profit_col and revenue_col_fs:
                gp = float(last_fs.get(gross_profit_col, 0.0))
                rev = float(last_fs.get(revenue_col_fs, 0.0))
                if rev != 0:
                    out["F02"] = (gp / rev) * 100
            
            # F03: 營益率 - 動態偵測欄位
            operating_income_col = None
            for col in ["operating_income", "OperatingIncome", "operating_profit"]:
                if col in last_fs:
                    operating_income_col = col
                    break
            
            if operating_income_col and revenue_col_fs:
                op = float(last_fs.get(operating_income_col, 0.0))
                rev = float(last_fs.get(revenue_col_fs, 0.0))
                if rev != 0:
                    out["F03"] = (op / rev) * 100
            
            # F04: EPS
            eps_col = None
            for col in ["eps", "EPS", "earnings_per_share"]:
                if col in last_fs:
                    eps_col = col
                    break
            if eps_col:
                out["F04"] = float(last_fs[eps_col])

        # F05: FCF（營運現金流 - 資本支出）
        if not cf_df.empty:
            cf_df = cf_df.sort_values("date")
            last_cf = cf_df.iloc[-1]
            
            # 動態偵測現金流欄位
            ocf_col = None
            capex_col = None
            for col in ["operating_cash_flow", "OperatingCashFlow", "cash_flow_from_operations"]:
                if col in last_cf:
                    ocf_col = col
                    break
            for col in ["capital_expenditure", "CapitalExpenditure", "capex", "investment_cash_flow"]:
                if col in last_cf:
                    capex_col = col
                    break
            
            ocf = float(last_cf.get(ocf_col, 0.0)) if ocf_col else 0.0
            capex = float(last_cf.get(capex_col, 0.0)) if capex_col else 0.0
            out["F05"] = ocf - capex

        # F06, F07, F08：ROE/ROA/負債比/股東權益成長
        if not bs_df.empty:
            bs_df = bs_df.sort_values("date")
            last_bs = bs_df.iloc[-1]
            
            # 動態偵測資產負債表欄位
            total_assets_col = None
            total_equity_col = None
            total_liabilities_col = None
            
            for col in ["total_assets", "TotalAssets", "assets", "Assets"]:
                if col in bs_df.columns:
                    total_assets_col = col
                    break
            
            for col in ["equity", "Equity", "total_equity", "TotalEquity", "total_equity_and_liabilities"]:
                if col in bs_df.columns:
                    total_equity_col = col
                    break
            
            for col in ["total_liabilities", "TotalLiabilities", "liabilities", "Liabilities"]:
                if col in bs_df.columns:
                    total_liabilities_col = col
                    break

            total_assets = float(last_bs.get(total_assets_col, 0.0)) if total_assets_col else 0.0
            total_equity = float(last_bs.get(total_equity_col, 0.0)) if total_equity_col else 0.0
            total_liabilities = float(last_bs.get(total_liabilities_col, 0.0)) if total_liabilities_col else 0.0

            # F07: 負債比
            if total_assets and total_assets != 0:
                out["F07"] = (total_liabilities / total_assets) * 100

            # F06: ROE（使用 net_income / total_equity）
            if not fs_df.empty and total_equity and total_equity != 0 and total_equity_col:
                # 動態偵測淨利欄位
                net_income_col = None
                for col in ["net_income", "NetIncome", "profit_after_tax", "net_profit"]:
                    if col in fs_df.columns:
                        net_income_col = col
                        break
                
                if net_income_col:
                    fs_sorted = fs_df.sort_values("date")
                    last_fs_row = fs_sorted.iloc[-1]
                    net_income = float(last_fs_row.get(net_income_col, 0.0))
                    roe = net_income / total_equity
                    out["F06"] = roe * 100

            # F08: 股東權益成長（YoY）
            if total_equity_col:
                equity_col = total_equity_col
                bs_df_eq = bs_df[["date", equity_col]].dropna()
                if len(bs_df_eq) >= 5:
                    bs_df_eq = bs_df_eq.sort_values("date")
                    # 取最近兩個年度點
                    last2 = bs_df_eq.tail(2)
                    if len(last2) >= 2:
                        eq_prev = last2[equity_col].iloc[0]
                        eq_last = last2[equity_col].iloc[1]
                        if eq_prev and eq_prev != 0:
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

