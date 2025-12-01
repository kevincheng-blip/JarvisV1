"""J-GOD Alpha Engine Module

This module provides multi-factor alpha generation capabilities for the J-GOD trading system.
Includes Flow, Divergence, Reversion, Inertia, Value/Quality, and Micro-Momentum factors.

See spec/JGOD_Python_Interface_Spec.md for interface specifications.
"""

from jgod.alpha_engine.alpha_engine import AlphaEngine
from jgod.alpha_engine.factor_base import FactorBase
from jgod.alpha_engine.flow_factor import FlowFactor
from jgod.alpha_engine.divergence_factor import DivergenceFactor
from jgod.alpha_engine.reversion_factor import ReversionFactor
from jgod.alpha_engine.inertia_factor import InertiaFactor
from jgod.alpha_engine.value_quality_factor import ValueQualityFactor
from jgod.alpha_engine.micro_momentum_factor import MicroMomentumFactor

__all__ = [
    'AlphaEngine',
    'FactorBase',
    'FlowFactor',
    'DivergenceFactor',
    'ReversionFactor',
    'InertiaFactor',
    'ValueQualityFactor',
    'MicroMomentumFactor'
]

