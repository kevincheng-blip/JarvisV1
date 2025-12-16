"""
Strategy Module: Portfolio management and allocation

v0.6.10-A10: Portfolio Manager for multi-symbol coordination
"""

# Re-export public strategy interfaces for stable imports
try:
    from .strategy_engine_v1 import StrategyEngineV1, DailySignalSet, StrategySignal
except ImportError:
    # Fallback if strategy_engine_v1 does not exist
    try:
        from .engine import StrategyEngine as StrategyEngineV1
    except ImportError:
        # Create minimal stub if nothing exists
        class StrategyEngineV1:
            def __init__(self, *args, **kwargs):
                pass
        
        StrategyEngineV1 = StrategyEngineV1
    
    try:
        from .models import DailySignalSet, StrategySignal
    except ImportError:
        # Create minimal stubs
        from dataclasses import dataclass
        from typing import List, Literal
        from datetime import date
        
        @dataclass
        class StrategySignal:
            symbol: str = ""
            date: date = None
            side: Literal["LONG", "SHORT", "FLAT"] = "FLAT"
            base_score: float = 0.0
            rank_score: float = 0.0
            raw_signal: str = ""
            risk_flags_summary: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"
            sources: List[str] = None
        
        @dataclass
        class DailySignalSet:
            date: date = None
            long_signals: List[StrategySignal] = None
            short_signals: List[StrategySignal] = None

__all__ = [
    "StrategyEngineV1",
    "DailySignalSet",
    "StrategySignal",
]
