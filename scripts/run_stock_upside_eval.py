#!/usr/bin/env python
"""
J-GOD Stock Upside Evaluation CLI

Command-line tool for evaluating stock upside potential using 100-indicator framework.

Usage:
    export FINMIND_API_TOKEN='YOUR_TOKEN'
    python scripts/run_stock_upside_eval.py 2330
    python scripts/run_stock_upside_eval.py 2330 --date 2024-01-15 --top-n 15
"""

from __future__ import annotations

import argparse
import os
from datetime import date, datetime
from typing import List

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, skip (will rely on system environment)
    pass

from jgod.prediction.data.indicator_builder_100 import StockIndicatorBuilder100
from jgod.prediction.rules.stock_upside_filter_60_v1 import (
    StockUpsideFilter60V1,
    IndicatorScore,
    StockUpsideResult,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="J-GOD · Stock Upside Evaluation (100-indicator pipeline → 60-filter)"
    )
    parser.add_argument(
        "stock_id",
        type=str,
        help="Stock ID, e.g. 2330, 1101",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="As-of date, format YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of strongest positive/negative indicators to display (default: 10)",
    )
    return parser.parse_args()


def _parse_date(date_str: str | None) -> date:
    if not date_str:
        return date.today()
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _format_indicator_score(ind: IndicatorScore, weighted: float) -> str:
    return f"{ind.code:<4} score={ind.score:+.3f} weight={ind.weight:.2f} weighted={weighted:+.3f} ({ind.reason})"


def _print_header(stock_id: str, as_of: date):
    print("==================================================")
    print(" J-GOD · Stock Upside Evaluation")
    print("==================================================")
    print(f" Symbol : {stock_id}")
    print(f" Date   : {as_of.isoformat()}")
    print("--------------------------------------------------")


def _print_summary(result: StockUpsideResult):
    print(" Summary")
    print("--------------------------------------------------")
    print(f" Verdict     : {result.verdict}")
    print(f" Total Score : {result.total_score:.3f}")
    print(f" Detail      : {result.summary}")
    print("--------------------------------------------------")


def _print_top_indicators(result: StockUpsideResult, top_n: int):
    scored: List[tuple[IndicatorScore, float]] = []
    for ind in result.indicator_scores:
        weighted = ind.score * ind.weight
        scored.append((ind, weighted))

    # 分成正向、負向
    positives = [x for x in scored if x[1] > 0]
    negatives = [x for x in scored if x[1] < 0]

    positives.sort(key=lambda x: x[1], reverse=True)
    negatives.sort(key=lambda x: x[1])

    print(" Top Positive Indicators")
    print("--------------------------------------------------")
    if positives:
        for ind, w in positives[:top_n]:
            print("  +", _format_indicator_score(ind, w))
    else:
        print("  (no strong positive indicators)")
    print("--------------------------------------------------")

    print(" Top Negative Indicators")
    print("--------------------------------------------------")
    if negatives:
        for ind, w in negatives[:top_n]:
            print("  -", _format_indicator_score(ind, w))
    else:
        print("  (no strong negative indicators)")
    print("--------------------------------------------------")


def main():
    args = parse_args()
    stock_id = args.stock_id
    as_of = _parse_date(args.date)
    top_n = args.top_n

    token = os.getenv("FINMIND_API_TOKEN")
    if not token:
        print("[ERROR] FINMIND_API_TOKEN is not set in environment.")
        print("        Please export your FinMind API token, e.g.:")
        print("        export FINMIND_API_TOKEN='YOUR_TOKEN_HERE'")
        raise SystemExit(1)

    _print_header(stock_id, as_of)

    # 1) Build indicators (100 codes)
    builder = StockIndicatorBuilder100(finmind_token=token)
    indicators = builder.build_indicators(stock_id, as_of)

    # 2) Run filter
    filter_ = StockUpsideFilter60V1()
    result = filter_.evaluate(stock_id, indicators)

    # 3) Print summary + top indicators
    _print_summary(result)
    _print_top_indicators(result, top_n)


if __name__ == "__main__":
    main()

