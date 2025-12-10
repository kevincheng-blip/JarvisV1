"""Rule Simulation Engine Configuration

Default paths and thresholds for rule simulation.
"""

from pathlib import Path

# Storage paths
RULE_SIM_REPORTS_PATH = Path("data/rule_sim/rule_sim_reports_v1.jsonl")
RULE_SIM_SANDBOX_ROOT = Path("data/rule_sim/sandbox/")

# Default thresholds for recommendation logic
MAX_SHARPE_DROP = -0.1  # If Sharpe drops more than 0.1 → warning
MAX_MAXDD_INCREASE = 0.05  # MaxDD increases more than 5% → warning
MAX_ALERT_INCREASE = 20  # Alert count increases too much → warning

# Default experiment parameters
DEFAULT_UNIVERSE = []  # Empty = use Path A default universe
DEFAULT_PATH_A_CONFIG = "path_a_tw_basic_v1"
DEFAULT_BACKTEST_DAYS = 180  # 6 months default

