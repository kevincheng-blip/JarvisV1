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

echo "================================"
echo "✅ All CI quick checks passed!"
echo ""

