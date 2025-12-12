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

echo "================================"
echo "✅ All CI quick checks passed!"
echo ""

