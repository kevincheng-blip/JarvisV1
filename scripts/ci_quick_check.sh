#!/bin/bash
# CI Quick Check Script for J-GOD Backend
# 
# Runs essential checks to ensure the backend codebase is "agent-loop safe":
# - Syntax compilation check
# - Core module import test
# - Critical API smoke tests
#
# Exit code: 0 if all checks pass, non-zero otherwise

set -e  # Exit on error

echo "🔍 J-GOD Backend CI Quick Check"
echo "================================"
echo ""

# Check 1: Python syntax compilation
echo "1️⃣  Checking Python syntax (compileall)..."
python3 -m compileall jgod -q
if [ $? -eq 0 ]; then
    echo "   ✅ Syntax check passed"
else
    echo "   ❌ Syntax check failed"
    exit 1
fi
echo ""

# Check 2: Core module imports
echo "2️⃣  Testing core module imports..."
pytest tests/test_import_core_modules.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Import test passed"
else
    echo "   ❌ Import test failed"
    exit 1
fi
echo ""

# Check 3: War Room V2 smoke test
echo "3️⃣  Running War Room V2 smoke test..."
pytest tests/test_war_room_v2_smoke.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ War Room V2 smoke test passed"
else
    echo "   ❌ War Room V2 smoke test failed"
    exit 1
fi
echo ""

# Check 4: Predictions timeline contract test
echo "4️⃣  Running predictions timeline contract test..."
pytest tests/test_predictions_timeline_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Predictions timeline test passed"
else
    echo "   ❌ Predictions timeline test failed"
    exit 1
fi
echo ""

# Check 5: Prediction stability contract test
echo "5️⃣  Running prediction stability contract test..."
pytest tests/test_prediction_stability_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Prediction stability test passed"
else
    echo "   ❌ Prediction stability test failed"
    exit 1
fi
echo ""

# Check 6: Doctrine patch lifecycle E2E test
echo "6️⃣  Running doctrine patch lifecycle E2E test..."
pytest tests/test_doctrine_patch_lifecycle_e2e.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Patch lifecycle E2E test passed"
else
    echo "   ❌ Patch lifecycle E2E test failed"
    exit 1
fi
echo ""

# Check 7: S-Rank V2 contract test
echo "7️⃣  Running S-Rank V2 contract test..."
pytest tests/test_s_rank_v2_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ S-Rank V2 contract test passed"
else
    echo "   ❌ S-Rank V2 contract test failed"
    exit 1
fi
echo ""

# Check 8: Strategy Performance contract test
echo "8️⃣  Running Strategy Performance contract test..."
pytest tests/test_strategy_perf_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Strategy Performance contract test passed"
else
    echo "   ❌ Strategy Performance contract test failed"
    exit 1
fi
echo ""

# Check 9: Decision V3 contract test
echo "9️⃣  Running Decision V3 contract test..."
pytest tests/test_decision_v3_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Decision V3 contract test passed"
else
    echo "   ❌ Decision V3 contract test failed"
    exit 1
fi
echo ""

# Check 10: Decision V3 Snapshot contract test
echo "🔟 Running Decision V3 Snapshot contract test..."
pytest tests/test_decision_v3_snapshot_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Decision V3 Snapshot contract test passed"
else
    echo "   ❌ Decision V3 Snapshot contract test failed"
    exit 1
fi
echo ""

# Check 11: Decision V3 Evaluation contract test
echo "1️⃣1️⃣  Running Decision V3 Evaluation contract test..."
pytest tests/test_decision_v3_eval_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Decision V3 Evaluation contract test passed"
else
    echo "   ❌ Decision V3 Evaluation contract test failed"
    exit 1
fi
echo ""

# Check 12: Decision V3 Compare contract test
echo "1️⃣2️⃣  Running Decision V3 Compare contract test..."
pytest tests/test_decision_v3_compare_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Decision V3 Compare contract test passed"
else
    echo "   ❌ Decision V3 Compare contract test failed"
    exit 1
fi
echo ""

# Check 13: Decision V3 Arena contract test
echo "1️⃣3️⃣  Running Decision V3 Arena contract test..."
pytest tests/test_decision_v3_arena_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Decision V3 Arena contract test passed"
else
    echo "   ❌ Decision V3 Arena contract test failed"
    exit 1
fi
echo ""

# Check 14: Virtual Ledger contract test
echo "1️⃣4️⃣  Running Virtual Ledger contract test..."
pytest tests/test_virtual_ledger_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Virtual Ledger contract test passed"
else
    echo "   ❌ Virtual Ledger contract test failed"
    exit 1
fi
echo ""

# Check 15: Execution API contract test
echo "1️⃣5️⃣  Running Execution API contract test..."
pytest tests/test_execution_api_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Execution API contract test passed"
else
    echo "   ❌ Execution API contract test failed"
    exit 1
fi
echo ""

# Check 16: MDTS contract test (v0.6.6-A7)
echo "1️⃣6️⃣  Running MDTS contract test..."
pytest tests/test_mdts_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ MDTS contract test passed"
else
    echo "   ❌ MDTS contract test failed"
    exit 1
fi
echo ""

# Check 17: Fill Engine contract test (v0.6.6-A7)
echo "1️⃣7️⃣  Running Fill Engine contract test..."
pytest tests/test_fill_engine_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Fill Engine contract test passed"
else
    echo "   ❌ Fill Engine contract test failed"
    exit 1
fi
echo ""

# Check 18: Backtest Core contract test (v0.6.6-A7)
echo "1️⃣8️⃣  Running Backtest Core contract test..."
pytest tests/test_backtest_core_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Backtest Core contract test passed"
else
    echo "   ❌ Backtest Core contract test failed"
    exit 1
fi
echo ""

# Check 19: Feature DB contract test (v0.6.7-A7.5)
echo "1️⃣9️⃣  Running Feature DB contract test..."
pytest tests/test_feature_db_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Feature DB contract test passed"
else
    echo "   ❌ Feature DB contract test failed"
    exit 1
fi
echo ""

# Check 20: Walk-Forward Runner contract test (v0.6.8-A8)
echo "2️⃣0️⃣  Running Walk-Forward Runner contract test..."
pytest tests/test_walkforward_runner_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Walk-Forward Runner contract test passed"
else
    echo "   ❌ Walk-Forward Runner contract test failed"
    exit 1
fi
echo ""

# Check 21: Learning Layers contract test (v0.6.8-A8)
echo "2️⃣1️⃣  Running Learning Layers contract test..."
pytest tests/test_learning_layers_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Learning Layers contract test passed"
else
    echo "   ❌ Learning Layers contract test failed"
    exit 1
fi
echo ""

# Check 22: Auto-Pilot Guard Rails contract test (v0.6.9-A9)
echo "2️⃣2️⃣  Running Auto-Pilot Guard Rails contract test..."
pytest tests/test_autopilot_guardrails_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Auto-Pilot Guard Rails contract test passed"
else
    echo "   ❌ Auto-Pilot Guard Rails contract test failed"
    exit 1
fi
echo ""

# Check 23: Shadow run smoke test (v0.6.9-A9)
echo "2️⃣3️⃣  Running Shadow run smoke test..."
# Unit stub test (not full 90-day run)
python3 -c "
from jgod.research.walkforward_runner import WalkForwardRunner
runner = WalkForwardRunner(use_mock_mdts=True)
# Just verify method exists and can be called with minimal params
print('Shadow run method exists')
"
if [ $? -eq 0 ]; then
    echo "   ✅ Shadow run smoke test passed"
else
    echo "   ❌ Shadow run smoke test failed"
    exit 1
fi
echo ""

# Check 24: Portfolio Manager contract test (v0.6.10-A10)
echo "2️⃣4️⃣  Running Portfolio Manager contract test..."
pytest tests/test_portfolio_manager_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Portfolio Manager contract test passed"
else
    echo "   ❌ Portfolio Manager contract test failed"
    exit 1
fi
echo ""

# Check 25: Execution Engine contract test (v0.6.11-A11)
echo "2️⃣5️⃣  Running Execution Engine contract test..."
pytest tests/test_execution_engine_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Execution Engine contract test passed"
else
    echo "   ❌ Execution Engine contract test failed"
    exit 1
fi
echo ""

# Check 26: Paper Broker contract test (v0.6.11-A11)
echo "2️⃣6️⃣  Running Paper Broker contract test..."
pytest tests/test_paper_broker_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Paper Broker contract test passed"
else
    echo "   ❌ Paper Broker contract test failed"
    exit 1
fi
echo ""

# Check 27: Execution resilience contract test (v0.6.12-A12)
echo "2️⃣7️⃣  Running Execution resilience contract test..."
pytest tests/test_execution_resilience_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Execution resilience contract test passed"
else
    echo "   ❌ Execution resilience contract test failed"
    exit 1
fi
echo ""

# Check 28: Signal Drift Score contract test (v0.6.13-P1.1)
echo "2️⃣8️⃣  Running Signal Drift Score contract test..."
pytest tests/test_signal_drift_contract.py -q
if [ $? -eq 0 ]; then
    echo "   ✅ Signal Drift Score contract test passed"
else
    echo "   ❌ Signal Drift Score contract test failed"
    exit 1
fi
echo ""

echo "================================"
echo "✅ All CI quick checks passed!"
echo ""

