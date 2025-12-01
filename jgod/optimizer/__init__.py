"""J-GOD Optimizer Module

投資組合優化器模組，提供 Mean-Variance 優化與各種限制條件支援。

Reference: 
- docs/J-GOD_OPTIMIZER_STANDARD_v1.md
- docs/JGOD_OPTIMIZER_STANDARD_v1.md (v2)
"""

from .optimizer_config import (
    OptimizerConfig,
    RiskObjectiveConfig,
    TrackingErrorConstraint,
    WeightConstraints,
    FactorExposureConstraints,
    SectorNeutralityConstraints,
)
from .optimizer_core import OptimizerCore, OptimizerResult
from .optimizer_constraints import ConstraintBuilder

# Optimizer v2
from .optimizer_types import OptimizerRequest, OptimizerResult as OptimizerResultV2
from .optimizer_core_v2 import OptimizerCoreV2

__all__ = [
    # v1 exports
    "OptimizerConfig",
    "RiskObjectiveConfig",
    "TrackingErrorConstraint",
    "WeightConstraints",
    "FactorExposureConstraints",
    "SectorNeutralityConstraints",
    "OptimizerCore",
    "OptimizerResult",
    "ConstraintBuilder",
    # v2 exports
    "OptimizerRequest",
    "OptimizerResultV2",
    "OptimizerCoreV2",
]

