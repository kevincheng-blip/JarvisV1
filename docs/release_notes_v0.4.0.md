# J-GOD v0.4.0 Release Notes

**Release Date:** 2025-12-13  
**Tag:** `v0.4.0` (pending)

## Overview

v0.4.0 completes the frontend API consistency migration and adds full Patch lifecycle E2E support with War Room V2 quick actions UI.

## Highlights

### v0.3.1: Frontend API Consistency
- **100% Unified API Client**: All hooks now use `src/api/client.ts` as single-source-of-truth
- **Removed Scattered baseURL**: Migrated `useDoctrinePatches.ts`, `useDecisionAbTest.ts`, `useObserver.ts` to use `apiClient`
- **Centralized Logging**: All API requests log through `client.ts` interceptor (dev-only)

### v0.4.0: Patch Lifecycle E2E
- **Complete Lifecycle API**: All endpoints support Body parameters (approve/reject/deploy/revert)
- **E2E Contract Test**: `tests/test_doctrine_patch_lifecycle_e2e.py` validates full flow
- **War Room V2 Quick Actions**: PatchQueueCard now includes action buttons (Run Sim, Approve, Reject, Deploy, Revert)
- **State Machine Guards**: UI buttons respect backend state transitions (no invalid actions)
- **Governance Bottleneck**: ExecutiveSummary shows pending_review_count + pending_simulation_count

## New/Updated Endpoints

### Doctrine Patch (Updated)
- `POST /api/v1/doctrine/patches/{patch_id}/approve` - Now accepts Body `{reviewer_id, comment?}`
- `POST /api/v1/doctrine/patches/{patch_id}/reject` - Now accepts Body `{reviewer_id, comment?}`
- `POST /api/v1/doctrine/patches/{patch_id}/deploy` - Now accepts Body `{operator_id}`
- `POST /api/v1/doctrine/patches/{patch_id}/revert` - Now accepts Body `{operator_id}`

### Frontend API Wrappers (New in client.ts)
- `getDoctrinePatchQueue(status?)` - Get patch queue (404 → empty array)
- `getDoctrinePatch(patchId)` - Get patch details (404 → error)
- `createDoctrinePatch(request)` - Create new patch
- `runDoctrinePatchSim(patchId)` - Run Rule Sim
- `approveDoctrinePatch(patchId, request)` - Approve patch
- `rejectDoctrinePatch(patchId, request)` - Reject patch
- `deployDoctrinePatch(patchId, request)` - Deploy patch
- `revertDoctrinePatch(patchId, request)` - Revert patch

## Verification Commands

### Backend Quick Check
```bash
bash scripts/ci_quick_check.sh
```

This now includes:
1. Python syntax check (`compileall`)
2. Core module import test
3. War Room V2 smoke test (9 tests, includes patch queue)
4. Predictions timeline contract test
5. Prediction stability contract test
6. **Patch lifecycle E2E test** (new)

### Manual API Verification
```bash
# Create patch (2 changes = guaranteed sim APPROVED)
curl -X POST "http://127.0.0.1:8000/api/v1/doctrine/patches" \
  -H "Content-Type: application/json" \
  -d '{
    "author_id": "test-user",
    "description": "Test patch",
    "changes": [
      {"change_type": "add", "rule_id": "rule-1", "new_text": "Content 1"},
      {"change_type": "modify", "rule_id": "rule-2", "old_text": "Old", "new_text": "New"}
    ]
  }'

# Run sim (use patch_id from above)
curl -X POST "http://127.0.0.1:8000/api/v1/doctrine/patches/{patch_id}/run-sim"

# Approve
curl -X POST "http://127.0.0.1:8000/api/v1/doctrine/patches/{patch_id}/approve" \
  -H "Content-Type: application/json" \
  -d '{"reviewer_id": "reviewer-1"}'

# Deploy
curl -X POST "http://127.0.0.1:8000/api/v1/doctrine/patches/{patch_id}/deploy" \
  -H "Content-Type: application/json" \
  -d '{"operator_id": "operator-1"}'

# Revert
curl -X POST "http://127.0.0.1:8000/api/v1/doctrine/patches/{patch_id}/revert" \
  -H "Content-Type: application/json" \
  -d '{"operator_id": "operator-1"}'
```

### Frontend Quick Check
See `scripts/frontend_quick_check.md` for updated UI verification steps including Patch quick actions.

## Known Limitations

- **Patch Actions**: Operator/reviewer IDs are hardcoded as "war-room-user" (should come from auth context in future)
- **Error Messages**: UI shows inline messages (toast-style), not full toast library
- **State Guards**: UI guards match backend, but some edge cases may need refinement

## Technical Debt Addressed

- ✅ All War Room V2 hooks migrated to unified `apiClient`
- ✅ Backend API consistency: approve/reject/deploy/revert use Body parameters
- ✅ E2E test coverage for patch lifecycle
- ✅ UI quick actions with state-aware button visibility

## Files Changed Summary

### Backend
- `jgod/api/routers/doctrine_patch.py` - Updated approve/reject/deploy/revert to accept Body parameters
- `jgod/api/schemas/doctrine_patch.py` - Added request body schemas (ApprovePatchRequest, etc.)
- `jgod/doctrine_v2/patch_service.py` - No changes (already supports lifecycle)
- `tests/test_doctrine_patch_lifecycle_e2e.py` - New E2E test
- `tests/test_war_room_v2_smoke.py` - Added patch queue health check

### Frontend
- `trading-ui/jgod-trading-ui/src/api/client.ts` - Added 8 patch lifecycle API wrappers
- `trading-ui/jgod-trading-ui/src/hooks/useDoctrinePatches.ts` - Migrated to use api wrappers
- `trading-ui/jgod-trading-ui/src/hooks/useDecisionAbTest.ts` - Migrated to use apiClient
- `trading-ui/jgod-trading-ui/src/components/war-room-v2/PatchQueueCard.tsx` - Added quick action buttons
- `trading-ui/jgod-trading-ui/src/components/war-room-v2/ExecutiveSummary.tsx` - Updated bottleneck calculation
- `trading-ui/jgod-trading-ui/src/pages/WarRoomV2Dashboard.tsx` - No changes needed (already wired)

## Next Steps (v0.5.0+)

- Add authentication context for operator/reviewer IDs
- Enhance error handling with proper toast notifications
- Add patch detail modal/drawer in War Room V2
- Expand E2E tests to cover edge cases (reject flow, multiple patches)

