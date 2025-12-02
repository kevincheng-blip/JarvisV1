"""
Risk Engine - 風險管理引擎
提供風險管理、投資組合管理、部位大小計算等功能
"""
from .risk_manager import RiskManager
from .portfolio import Portfolio
from .sizing import PositionSizer

# Risk Model v1.0 - Multi-Factor Risk Model
from .exposure_schema import FactorExposure, exposures_from_alpha_df, exposures_to_dataframe
from .risk_model import MultiFactorRiskModel

# Risk Model Extreme
try:
    from .risk_model_extreme import (
        MultiFactorRiskModelExtreme,
        RiskModelExtremeConfig,
    )
    _EXTREME_AVAILABLE = True
except ImportError:
    _EXTREME_AVAILABLE = False
from .portfolio_risk import (
    compute_portfolio_exposure,
    compute_portfolio_risk,
    decompose_portfolio_risk_by_factor
)
from .risk_factors import (
    RiskFactor,
    RiskFactorCalculator,
    get_standard_risk_factor_names,
    map_alpha_to_risk_factors,
    STANDARD_FACTOR_NAMES
)

__all__ = [
    "RiskManager",
    "Portfolio",
    "PositionSizer",
    # Risk Model v1.0
    "FactorExposure",
    "exposures_from_alpha_df",
    "exposures_to_dataframe",
    "MultiFactorRiskModel",
    "compute_portfolio_exposure",
    "compute_portfolio_risk",
    "decompose_portfolio_risk_by_factor",
    # Eight Risk Factors
    "RiskFactor",
    "RiskFactorCalculator",
    "get_standard_risk_factor_names",
    "map_alpha_to_risk_factors",
    "STANDARD_FACTOR_NAMES",
]

if _EXTREME_AVAILABLE:
    __all__.extend([
        "MultiFactorRiskModelExtreme",
        "RiskModelExtremeConfig",
    ])

