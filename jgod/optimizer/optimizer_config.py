"""Optimizer Configuration

定義 Optimizer 會用到的所有設定參數（Sharpe/TE/權重/因子暴露等）。

Reference: docs/J-GOD_OPTIMIZER_STANDARD_v1.md
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass
class RiskObjectiveConfig:
    """
    風險／報酬目標設定：
    - 支援 Max Sharpe（預設）
    - 或純 Mean-Variance（未來可擴充）

    參數說明：
    - use_max_sharpe: 是否使用 Max Sharpe 目標（預設 True）
    - risk_aversion: 風險厭惡係數 λ，如不用 Sharpe 則當作 mean-variance 的權重
    """

    use_max_sharpe: bool = True
    risk_aversion: float = 1.0  # λ


@dataclass
class TrackingErrorConstraint:
    """
    追蹤誤差限制：
    TE(w) <= te_max

    若不啟用，設為 enabled=False

    參數說明：
    - enabled: 是否啟用 TE 限制（預設 True）
    - te_max: Tracking Error 上限（年化，例如 0.05 表示 5%）
    - benchmark_weights: Benchmark 權重字典 {stock_id: weight}
    """

    enabled: bool = True
    te_max: float = 0.05  # 例如 5%
    benchmark_weights: Optional[Dict[str, float]] = None  # stock_id -> weight


@dataclass
class WeightConstraints:
    """
    權重相關限制：
    - long_only: 是否禁止空頭
    - min_weight / max_weight: 個股權重上下限（若有個別 override，可在 future 擴充）
    - leverage_limit: |w_long| + |w_short| 的上限（v1 可先不用強調）

    參數說明：
    - long_only: 是否為 Long-only 策略（預設 True）
    - min_weight: 個股最小權重（預設 0.0）
    - max_weight: 個股最大權重（預設 0.05，即 5%）
    - leverage_limit: 槓桿上限（v1 可忽略，未來版本使用）
    """

    long_only: bool = True
    min_weight: float = 0.0
    max_weight: float = 0.05
    leverage_limit: Optional[float] = 1.0  # v1 可以忽略，未來版本使用


@dataclass
class FactorExposureConstraints:
    """
    因子暴露限制：
    - key: 風險因子名稱（例如 'R_MKT', 'R_SIZE', ...）
    - value: (min_exposure, max_exposure) 或 (min_delta, max_delta)

    若字典為空，則不限制。

    參數說明：
    - factor_bounds: 因子暴露邊界字典，key 為因子名稱，value 為 (min, max) tuple
                     例如：{'R_MKT': (-0.1, 0.1), 'R_FLOW': (-0.3, 0.3)}
    """

    factor_bounds: Dict[str, Tuple[float, float]] = field(default_factory=dict)


@dataclass
class SectorNeutralityConstraints:
    """
    行業/板塊中性限制：
    - key: sector_name, value: (min_delta, max_delta)

    例如：{'TECH': (-0.02, 0.02)}

    sector 資訊由呼叫者提供（stock_id -> sector_name）

    參數說明：
    - enabled: 是否啟用 Sector 中性限制（預設 False）
    - sector_bounds: Sector 暴露邊界字典，key 為 sector 名稱，value 為 (min_delta, max_delta)
    """

    enabled: bool = False
    sector_bounds: Dict[str, Tuple[float, float]] = field(default_factory=dict)


@dataclass
class OptimizerConfig:
    """
    Optimizer v1 的總設定：
    - 將所有子設定集中管理
    - 未來 Path A / Backtest 可直接建立此 config 丟給 OptimizerCore

    參數說明：
    - risk_objective: 風險目標配置
    - tracking_error: Tracking Error 限制配置
    - weight_constraints: 權重限制配置
    - factor_constraints: 因子暴露限制配置
    - sector_constraints: Sector 中性限制配置
    """

    risk_objective: RiskObjectiveConfig = field(default_factory=RiskObjectiveConfig)
    tracking_error: TrackingErrorConstraint = field(default_factory=TrackingErrorConstraint)
    weight_constraints: WeightConstraints = field(default_factory=WeightConstraints)
    factor_constraints: FactorExposureConstraints = field(default_factory=FactorExposureConstraints)
    sector_constraints: SectorNeutralityConstraints = field(default_factory=SectorNeutralityConstraints)

    # 預留欄位：例如 turnover 限制、VaR/CVaR 限制... 可在 v2 擴充

