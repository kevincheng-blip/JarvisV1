# J-GOD v0.3.0 Release Notes

**Release Date:** 2025-12-13  
**Tag:** `v0.3.0-war-room-v2`

## Overview

v0.3.0 focuses on War Room V2 enhancements, prediction quality metrics, and backend stability improvements. This release makes the codebase "agent-loop safe" and adds measurable prediction stability tracking.

## Highlights

### P0: Unified API Client & Timeline Endpoint
- **Frontend API Consistency**: Single-source-of-truth for API baseURL (`src/api/client.ts`)
- **Latest Prediction Endpoint**: `GET /api/v1/predictions/latest/{symbol}` returns latest prediction with raw_score and final_score
- **Timeline Endpoint**: `GET /api/v1/predictions/timeline/{symbol}?limit=60` provides historical prediction data
- **Error Handling**: Refined empty-state handling (404 → null/empty, 5xx → error)

### P1: Agent-Loop Safety
- **Compile Clean**: All Python syntax errors fixed (`python -m compileall jgod -q` passes)
- **Core Import Test**: `tests/test_import_core_modules.py` verifies critical modules import without side effects
- **CI Quick Check**: `scripts/ci_quick_check.sh` provides one-click verification

### P2: Prediction Stability Metrics
- **Stability API**: `GET /api/v1/observer/prediction-stability/{symbol}?limit=60` computes stability metrics
- **War Room V2 Card**: New `PredictionStabilityCard` displays stability grade, std, max_delta, trend_slope
- **Metrics**: NO_DATA, STABLE, WATCH, VOLATILE grades based on score_std and max_abs_delta thresholds

## New Endpoints

### Predictions
- `GET /api/v1/predictions/latest/{symbol}` - Get latest prediction for symbol
- `GET /api/v1/predictions/timeline/{symbol}?limit=60` - Get prediction timeline

### Observer
- `GET /api/v1/observer/prediction-stability/{symbol}?limit=60` - Get prediction stability metrics

## Verification Commands

### Backend Quick Check
```bash
bash scripts/ci_quick_check.sh
```

This runs:
1. Python syntax check (`compileall`)
2. Core module import test
3. War Room V2 smoke test (includes new endpoints)
4. Predictions timeline contract test
5. Prediction stability contract test

### Manual API Verification
```bash
# Latest prediction
curl -i "http://127.0.0.1:8000/api/v1/predictions/latest/2330"

# Timeline
curl -i "http://127.0.0.1:8000/api/v1/predictions/timeline/2330?limit=10"

# Stability
curl -i "http://127.0.0.1:8000/api/v1/observer/prediction-stability/2330?limit=10"
```

### Frontend Quick Check
See `scripts/frontend_quick_check.md` for UI verification steps.

## Known Limitations

- **Timeline Endpoint**: Currently uses `raw_score` as `final_score` (Decision Layer integration can be enhanced later)
- **Stability Metrics**: Thresholds are tuned for current data scale; may need adjustment as more data accumulates
- **Frontend**: Some legacy hooks still use direct axios calls (will be migrated in future releases)

## Technical Debt Addressed

- Fixed 7 Python syntax errors (missing imports, indentation, top-level return)
- Unified frontend API client (removed scattered baseURL usage in War Room V2 components)
- Added contract tests for all new endpoints
- Improved empty-state handling (no more 404 errors for missing data)

## Files Changed Summary

### Backend
- `jgod/api/routers/predictions.py` - Added latest and timeline endpoints
- `jgod/api/routers/observer.py` - Added prediction-stability endpoint
- `jgod/observer/prediction_stability.py` - New stability metrics module
- `tests/test_predictions_timeline_contract.py` - Timeline contract test
- `tests/test_prediction_stability_contract.py` - Stability contract test
- `tests/test_war_room_v2_smoke.py` - Expanded to include new endpoints

### Frontend
- `trading-ui/jgod-trading-ui/src/api/client.ts` - Added getPredictionStability, unified baseURL
- `trading-ui/jgod-trading-ui/src/components/war-room-v2/PredictionStabilityCard.tsx` - New card component
- `trading-ui/jgod-trading-ui/src/pages/WarRoomV2Dashboard.tsx` - Integrated stability card
- `trading-ui/jgod-trading-ui/src/hooks/useObserver.ts` - Migrated to use apiClient from client.ts
- `trading-ui/jgod-trading-ui/src/hooks/war-room/usePredictions.ts` - Already using apiClient (P0)

## Next Steps (v0.4.0+)

- Migrate remaining frontend hooks to use `apiClient` from `client.ts`
- Enhance timeline endpoint with Decision Layer final_score calculation
- Add more stability metric visualizations (charts, trends)
- Expand War Room V2 with additional observer metrics

