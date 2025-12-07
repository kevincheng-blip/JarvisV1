#!/usr/bin/env python
"""
J-GOD · Indicator Coverage Checker

用途：
- 檢查 indicator_snapshots 在指定日期區間內的覆蓋率
- 以「symbol × 日期」為粒度，計算：
    - daily_bars 有多少天
    - indicator_snapshots 有多少天
    - 覆蓋率 = 有指標的天數 / 有價量資料的天數
- 支援：
    - 指定日期區間
    - 過濾覆蓋率低於門檻的標的
    - 輸出 summary 統計資訊

使用範例：
PYTHONPATH=. python scripts/check_indicator_gaps.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31

PYTHONPATH=. python scripts/check_indicator_gaps.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --min-coverage 0.8
"""

import argparse
from datetime import date, datetime
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from jgod.storage.db import get_session
from jgod.storage.models import Stock, DailyBar, IndicatorSnapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="J-GOD · Indicator Coverage Checker"
    )
    parser.add_argument(
        "--start-date",
        required=True,
        help="起始日期 (YYYY-MM-DD)，例如 2024-01-01",
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="結束日期 (YYYY-MM-DD)，例如 2024-12-31",
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=0.0,
        help="只顯示覆蓋率低於此門檻的標的（0~1）。預設顯示全部",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="只顯示前 N 檔覆蓋率最低的標的，0 表示不限制",
    )
    return parser.parse_args()


def _parse_date(d: str) -> date:
    return datetime.strptime(d, "%Y-%m-%d").date()


def compute_coverage(
    session: Session,
    start_date: date,
    end_date: date,
) -> List[Dict]:
    """
    回傳每一檔股票在指定區間內的覆蓋資訊：
    [
      {
        "symbol": "2330",
        "name": "台積電",
        "bar_days": 242,
        "indicator_days": 242,
        "coverage": 1.0,
      },
      ...
    ]
    """
    # 1) 取得所有股票
    stocks: List[Stock] = (
        session.query(Stock)
        .order_by(Stock.symbol.asc())
        .all()
    )

    # 2) daily_bars：統計每檔有幾天有價量資料
    bar_subq = (
        session.query(
            DailyBar.symbol.label("symbol"),
            func.count().label("bar_days"),
        )
        .filter(
            DailyBar.date >= start_date,
            DailyBar.date <= end_date,
        )
        .group_by(DailyBar.symbol)
        .subquery()
    )

    # 3) indicator_snapshots：統計每檔有幾天有指標（distinct date）
    ind_subq = (
        session.query(
            IndicatorSnapshot.symbol.label("symbol"),
            func.count(func.distinct(IndicatorSnapshot.date)).label(
                "indicator_days"
            ),
        )
        .filter(
            IndicatorSnapshot.date >= start_date,
            IndicatorSnapshot.date <= end_date,
        )
        .group_by(IndicatorSnapshot.symbol)
        .subquery()
    )

    # 4) join 回 Stock
    rows = (
        session.query(
            Stock.symbol,
            Stock.name_zh,
            func.coalesce(bar_subq.c.bar_days, 0).label("bar_days"),
            func.coalesce(ind_subq.c.indicator_days, 0).label("indicator_days"),
        )
        .outerjoin(bar_subq, bar_subq.c.symbol == Stock.symbol)
        .outerjoin(ind_subq, ind_subq.c.symbol == Stock.symbol)
        .order_by(Stock.symbol.asc())
        .all()
    )

    results: List[Dict] = []
    for symbol, name, bar_days, indicator_days in rows:
        if bar_days and bar_days > 0:
            coverage = float(indicator_days) / float(bar_days)
        else:
            coverage = 0.0

        results.append(
            {
                "symbol": symbol,
                "name": name or "",
                "bar_days": int(bar_days or 0),
                "indicator_days": int(indicator_days or 0),
                "coverage": coverage,
            }
        )

    return results


def print_summary(
    start_date: date,
    end_date: date,
    rows: List[Dict],
    min_coverage: float = 0.0,
    limit: int = 0,
) -> None:
    total = len(rows)
    if total == 0:
        print("⚠️ 沒有任何股票資料。")
        return

    # 全體統計
    completed = sum(1 for r in rows if r["coverage"] >= 0.999)
    avg_cov = sum(r["coverage"] for r in rows) / total

    print("==================================================")
    print(" J-GOD · Indicator Coverage Report")
    print("==================================================")
    print(f" Date Range : {start_date} ~ {end_date}")
    print(f" Symbols    : {total}")
    print(f" Completed  : {completed} / {total} "
          f"({completed / total:.1%})  (coverage ≥ 99.9%)")
    print(f" Avg Cover  : {avg_cov:.1%}")
    print("--------------------------------------------------")

    # 過濾 / 排序
    filtered = [r for r in rows if r["coverage"] >= min_coverage]
    # 你要看「低覆蓋」比較直觀，所以用 coverage 升冪
    filtered.sort(key=lambda r: r["coverage"])

    if limit > 0:
        filtered = filtered[:limit]

    if not filtered:
        print(f"👏 所有標的覆蓋率都 ≥ {min_coverage:.0%}，沒有低覆蓋標的。")
        return

    print(f" 詳細列表（覆蓋率 ≥ {min_coverage:.0%}，依覆蓋率由低到高）：")
    print("--------------------------------------------------")
    print(
        f"{'Symbol':<8} {'Name':<10} "
        f"{'Bars':>6} {'IndDays':>8} {'Coverage':>10}"
    )
    print("-" * 60)
    for r in filtered:
        print(
            f"{r['symbol']:<8} "
            f"{r['name'][:10]:<10} "
            f"{r['bar_days']:>6} "
            f"{r['indicator_days']:>8} "
            f"{r['coverage']*100:>8.1f}%"
        )


def main() -> None:
    args = parse_args()
    start = _parse_date(args.start_date)
    end = _parse_date(args.end_date)

    if start > end:
        raise SystemExit("❌ start-date 不可大於 end-date")

    session_gen = get_session()
    session = next(session_gen)
    try:
        rows = compute_coverage(session, start, end)
    finally:
        session.close()

    print_summary(
        start_date=start,
        end_date=end,
        rows=rows,
        min_coverage=args.min_coverage,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()

