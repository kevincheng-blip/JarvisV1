#!/usr/bin/env python
"""
Run a Path A v1 experiment with FinMind data.

Usage example:

    python scripts/run_path_a_experiment.py \
        --start-date 2024-01-01 \
        --end-date 2024-06-30 \
        --rebalance-frequency M \
        --experiment-name demo_2024H1

This script is intentionally simple and opinionated:
- It uses a small, hard-coded universe for now (you can edit it later).
- It relies on FinMind's DataLoader as the FinMindClient implementation.
- It writes basic outputs (NAV / returns) to the `output/` directory.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

# FinMind real client (you need FinMind installed in your environment)
try:
    from FinMind.data import DataLoader as FinMindDataLoader  # type: ignore[import]
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "FinMind is not installed. Please install it with:\n\n"
        "    pip install FinMind\n"
    ) from exc

# J-GOD modules
from jgod.path_a.path_a_schema import PathAConfig
from jgod.path_a.path_a_backtest import PathARunContext, run_path_a_backtest
from jgod.path_a.finmind_loader import FinMindPathADataLoader
from jgod.path_a.path_a_error_bridge import PathAErrorBridge

from jgod.alpha_engine.alpha_engine import AlphaEngine
from jgod.risk.risk_model import MultiFactorRiskModel
from jgod.optimizer.optimizer_core import OptimizerCore
from jgod.optimizer.optimizer_config import OptimizerConfig

from jgod.knowledge.knowledge_brain import KnowledgeBrain
from jgod.learning.error_learning_engine import ErrorLearningEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Path A v1 experiment with FinMind data."
    )
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Experiment start date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="Experiment end date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--rebalance-frequency",
        type=str,
        default="M",
        choices=["D", "W", "M"],
        help="Rebalance frequency: D (daily), W (weekly), M (monthly). Default: M.",
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        default="path_a_experiment",
        help="Name of the experiment (used in output filenames).",
    )
    return parser.parse_args()


def build_default_universe() -> List[str]:
    """
    Build a small default universe for initial experiments.
    
    You can edit this function later to:
    - Load a TW50 universe from a file
    - Or use a config-based universe definition
    """
    return [
        "2330.TW",  # TSMC
        "2317.TW",  # Foxconn
        "2303.TW",  # UMC
        "2881.TW",  # Fubon
        "2882.TW",  # Cathay
    ]


def ensure_output_dir() -> Path:
    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def build_knowledge_brain() -> KnowledgeBrain:
    """
    Load the J-GOD knowledge brain from the JSONL knowledge base.
    
    If the file path changes in the future, this function is the single
    place you need to update.
    """
    kb_path = Path("knowledge_base") / "jgod_knowledge_v1.jsonl"
    if not kb_path.exists():
        # We fail loudly here; Path A can run without knowledge, but the
        # ErrorLearningEngine will work much better with it.
        raise FileNotFoundError(
            f"Knowledge base not found at: {kb_path}. "
            "Please ensure you have generated jgod_knowledge_v1.jsonl."
        )
    brain = KnowledgeBrain(path=kb_path)
    brain.load()
    return brain


def compute_basic_stats(nav_series: pd.Series) -> dict:
    """
    Compute a few basic performance statistics from NAV series.
    
    Note:
    - This is a very simple implementation; you can replace it later
      with a more complete analytics module.
    """
    if nav_series.empty:
        return {"final_nav": np.nan, "cagr": np.nan, "max_drawdown": np.nan}
    
    start_nav = float(nav_series.iloc[0])
    end_nav = float(nav_series.iloc[-1])
    final_nav = end_nav
    
    # Approximate number of years
    num_days = (nav_series.index[-1] - nav_series.index[0]).days
    years = max(num_days / 252.0, 1e-6)
    
    cagr = (end_nav / start_nav) ** (1.0 / years) - 1.0 if start_nav > 0 else np.nan
    
    # max drawdown
    running_max = nav_series.cummax()
    drawdown = nav_series / running_max - 1.0
    max_drawdown = float(drawdown.min())
    
    return {
        "final_nav": final_nav,
        "cagr": cagr,
        "max_drawdown": max_drawdown,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = parse_args()
    universe = build_default_universe()
    out_dir = ensure_output_dir()
    
    # 1) Build Path A config
    config = PathAConfig(
        start_date=args.start_date,
        end_date=args.end_date,
        universe=universe,
        rebalance_frequency=args.rebalance_frequency,
        experiment_name=args.experiment_name,
    )
    
    # 2) Build FinMind-backed data loader
    finmind_client = FinMindDataLoader()
    data_loader = FinMindPathADataLoader(client=finmind_client)
    
    # 3) Build knowledge brain + error engine
    knowledge_brain = build_knowledge_brain()
    error_engine = ErrorLearningEngine(knowledge_brain=knowledge_brain)
    
    # 4) Build core engines
    alpha_engine = AlphaEngine()
    risk_model = MultiFactorRiskModel()
    optimizer_config = OptimizerConfig()  # you can tweak configs later
    optimizer = OptimizerCore(config=optimizer_config)
    
    # 5) Error bridge
    error_bridge = PathAErrorBridge()
    
    # 6) Build run context
    ctx = PathARunContext(
        config=config,
        data_loader=data_loader,
        alpha_engine=alpha_engine,
        risk_model=risk_model,
        optimizer=optimizer,
        error_engine=error_engine,
        error_bridge=error_bridge,
    )
    
    # 7) Run backtest
    print(f"[Path A] Running experiment: {config.experiment_name}")
    print(f"  Date range : {config.start_date} ~ {config.end_date}")
    print(f"  Universe   : {', '.join(universe)}")
    print(f"  Rebalance  : {config.rebalance_frequency}")
    
    result = run_path_a_backtest(ctx)
    
    # 8) Save outputs
    nav_path = out_dir / f"path_a_{config.experiment_name}_nav.csv"
    ret_path = out_dir / f"path_a_{config.experiment_name}_returns.csv"
    
    result.nav_series.to_csv(nav_path, header=["nav"])
    result.return_series.to_csv(ret_path, header=["return"])
    
    stats = compute_basic_stats(result.nav_series)
    
    print("\n[Path A] Experiment finished.")
    print(f"  Final NAV     : {stats['final_nav']:.4f}")
    print(f"  CAGR (approx) : {stats['cagr'] * 100:.2f}%")
    print(f"  Max Drawdown  : {stats['max_drawdown'] * 100:.2f}%")
    print(f"\nOutputs written to:\n  {nav_path}\n  {ret_path}")


if __name__ == "__main__":
    main()

