"""S-Rank Factor Engine Configuration

Default parameters and weights for S-Rank calculation.
"""

from pathlib import Path

# Default time horizon for performance evaluation
DEFAULT_TIME_HORIZON_DAYS = 90

# Weights for S-Rank score calculation
S_RANK_WEIGHTS = {
    "sharpe_ratio": 0.4,
    "inv_max_drawdown": 0.3,
    "consistency_score": 0.15,
    "inv_factor_decay": 0.15,
}

# Storage path
S_RANK_REPORTS_PATH = Path("data/s_rank_engine/s_rank_factors_v1.jsonl")

# Rank level thresholds
RANK_THRESHOLDS = {
    "S": 0.85,
    "A": 0.70,
    "B": 0.50,
    "C": 0.30,
    "D": 0.0,
}

