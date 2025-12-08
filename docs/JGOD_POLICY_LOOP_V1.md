# J-GOD Policy Loop v1 (Milestone)

## Overview

The first end-to-end AI policy cycle is now fully operational. This milestone marks the completion of the first automated feedback and policy-tuning loop in the J-GOD system.

## Components

### Path A v1 Backtest Engine
- Executes simulated trades based on PortfolioPlan
- Writes JSONL backtest logs to `data/path_a_backtest_logs.jsonl`
- Tracks daily equity curve, PnL, and performance metrics

### Policy Log Reader v1
- Reads and analyzes backtest experiment logs
- Scores experiments using Sharpe Ratio and Max Drawdown
- Filters and ranks experiments by performance
- CLI: `scripts/run_policy_log_reader_v1.py`

### Policy Writer v1
- Selects best-performing experiments
- Generates recommended RiskConfig YAML files
- Outputs to `policy/risk_config_suggested_v1.yaml`
- CLI: `scripts/run_policy_writer_v1.py`

## Configuration Parameters

The Policy Loop manages the following risk configuration parameters:

- `long_budget`: Long position budget (default: 0.6 = 60%)
- `short_budget`: Short position budget (default: 0.2 = 20%)
- `max_weight_per_symbol`: Maximum weight per stock (default: 0.10 = 10%)
- `min_score`: Minimum score threshold (default: 0.0)
- `allow_short`: Whether to allow short positions (default: True)

## Workflow

1. **Run Backtests**: Execute Path A v1 with various parameter combinations
2. **Generate Logs**: Each backtest writes a JSONL log entry
3. **Analyze Results**: Policy Log Reader scores and ranks experiments
4. **Generate Policy**: Policy Writer selects best experiment and creates RiskConfig YAML
5. **Apply Policy**: Decision Engine can load RiskConfig YAML for future runs

## Usage Examples

### Generate Multiple Backtests
```bash
PYTHONPATH=. python scripts/run_path_a_batch_v1.py
```

### Analyze Experiment Results
```bash
PYTHONPATH=. python scripts/run_policy_log_reader_v1.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --top-n 20
```

### Generate Recommended Policy
```bash
PYTHONPATH=. python scripts/run_policy_writer_v1.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31
```

### Apply Policy to Decision Engine
```bash
PYTHONPATH=. python scripts/run_path_a_v1.py \
  2024-01-01 2024-12-31 \
  --risk-config-file policy/risk_config_suggested_v1.yaml
```

## Architecture

```
Path A Backtest → JSONL Logs → Policy Log Reader → Policy Writer → RiskConfig YAML → Decision Engine
```

This closed-loop system enables automated parameter tuning based on historical performance.

## Status

✅ **Completed**: Policy Loop v1 is fully operational and ready for production use.

## Future Enhancements

- Multi-objective optimization (v2)
- Time-weighted experiment ranking
- Automated parameter search (grid search / Bayesian optimization)
- Policy versioning and rollback mechanisms

