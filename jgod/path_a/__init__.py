"""Path A - Validation Lab

Path A is the validation laboratory for J-GOD system.
It runs historical backtests and integrates with:
- Alpha Engine
- Risk Model
- Optimizer
- Error Learning Engine

This module provides the core infrastructure for Path A experiments.
"""

from .path_a_schema import (
    PathAConfig,
    PathADailyInput,
    PathAFeatureFrame,
    PathAPrediction,
    PathAPortfolioSnapshot,
    PathABacktestResult,
)
from .path_a_backtest import (
    PathARunContext,
    run_path_a_backtest,
    PathADataLoader,
    PathAErrorBridge,
)
from .path_a_error_bridge import PathAErrorBridge as PathAErrorBridgeImpl
from .mock_data_loader import MockPathADataLoader
from .finmind_loader import FinMindPathADataLoader, FinMindClient

__all__ = [
    "PathAConfig",
    "PathADailyInput",
    "PathAFeatureFrame",
    "PathAPrediction",
    "PathAPortfolioSnapshot",
    "PathABacktestResult",
    "PathARunContext",
    "run_path_a_backtest",
    "PathADataLoader",
    "PathAErrorBridge",
    "PathAErrorBridgeImpl",
    "MockPathADataLoader",
    "FinMindPathADataLoader",
    "FinMindClient",
]

