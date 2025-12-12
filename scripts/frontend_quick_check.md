# Frontend Quick Check Guide

## Prerequisites

1. Backend must be running:
   ```bash
   cd /Users/kevincheng/JarvisV1
   .venv/bin/uvicorn jgod.api.main:app --reload --port 8000
   ```

2. Frontend dependencies installed:
   ```bash
   cd trading-ui/jgod-trading-ui
   npm install
   ```

## Quick Check Steps

### 1. Start Frontend Dev Server

```bash
cd trading-ui/jgod-trading-ui
npm run dev
```

Frontend should start on `http://localhost:3000` (or another port if 3000 is taken).

### 2. Navigate to War Room V2

1. Open browser: `http://localhost:3000`
2. Navigate to **War Room V2** page (check navigation menu)

### 3. Verify Core Features

#### A. Top Predictions Panel
- **Location**: Left column (large panel)
- **Expected**: Should show Top 5 Long and Top 5 Short predictions
- **Check**: 
  - Lists load without errors
  - Click a symbol (e.g., "2330") to open Decision Context drawer

#### B. Prediction Stability Card
- **Location**: Right column, below S-Rank Trend Card
- **Expected**: Shows stability metrics for selected symbol (default: "2330")
- **Check**:
  - Card displays with grade badge (STABLE/WATCH/VOLATILE/NO_DATA)
  - Metrics shown: n_points, score_std, max_abs_delta, trend_slope
  - If NO_DATA: shows friendly empty state message

#### C. Timeline Integration
- **Location**: Dashboard page (if timeline panel exists)
- **Expected**: Timeline chart loads for selected symbol
- **Check**:
  - No 404 errors in browser console
  - Timeline displays data points or empty state

#### D. Latest Prediction
- **Location**: Signal Panel or Decision Context drawer
- **Expected**: Latest prediction data loads
- **Check**:
  - No 404 errors
  - Shows prediction data or "No latest prediction data" message

### 4. Browser Console Checks

Open browser DevTools (F12) and check:

1. **Network Tab**:
   - All API requests return 200 (not 404/500)
   - Request URLs are correct (e.g., `http://127.0.0.1:8000/api/v1/...`)

2. **Console Tab**:
   - Dev-only debug logs show request URLs: `[API] GET http://127.0.0.1:8000/...`
   - No red error messages
   - No 404 warnings

### 5. Symbol Selection Flow

1. Click a symbol in Top Predictions panel (e.g., "2330")
2. Verify:
   - Decision Context drawer opens
   - Prediction Stability Card updates to show that symbol's metrics
   - All related API calls succeed (check Network tab)

### 6. Empty State Handling

Test with a symbol that has no data:
1. Try selecting a symbol with no predictions (if available)
2. Verify:
   - Stability card shows "NO_DATA" grade or empty state message
   - Timeline shows empty state (not error)
   - Latest prediction shows "No latest prediction data" (not error)

### 7. Patch Quick Actions (v0.4.0)

Test Patch lifecycle quick actions:
1. **Create Patch** (via API or /docs):
   ```bash
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
   ```

2. **Verify in UI**:
   - PatchQueueCard should show the new patch with status "PENDING_SIMULATION"
   - "Run Sim" button should be visible and enabled

3. **Run Sim**:
   - Click "Run Sim" button
   - Verify: Success message appears, queue refreshes, status changes to "PENDING_REVIEW"
   - "Approve" button should now be visible

4. **Approve**:
   - Click "Approve" button
   - Verify: Success message, status changes to "APPROVED"
   - "Deploy" button should now be visible

5. **Deploy**:
   - Click "Deploy" button
   - Verify: Success message, status changes to "DEPLOYED"
   - "Revert" button should now be visible

6. **Revert**:
   - Click "Revert" button
   - Verify: Success message, status changes to "REVERTED"
   - Patch should disappear from active queue

7. **State Guards**:
   - Try clicking invalid actions (e.g., Deploy on PENDING_SIMULATION)
   - Verify: Error message appears, action is blocked

## Expected Behavior

✅ **Success Indicators:**
- All API calls return 200 (or gracefully handle 404 with empty states)
- No console errors
- UI components render correctly (loading → data/empty state)
- Symbol selection updates related components

❌ **Failure Indicators:**
- 404 errors in Network tab
- Red error messages in console
- Components stuck in loading state
- API calls to wrong URLs (e.g., `localhost:8000` instead of `127.0.0.1:8000`)

## Troubleshooting

### Backend Not Running
- **Symptom**: All API calls fail with network errors
- **Fix**: Start backend: `uvicorn jgod.api.main:app --reload --port 8000`

### Wrong API Base URL
- **Symptom**: API calls go to `localhost:8000` instead of `127.0.0.1:8000`
- **Fix**: Check `trading-ui/jgod-trading-ui/src/api/client.ts` - should use `127.0.0.1:8000`

### CORS Errors
- **Symptom**: Browser console shows CORS policy errors
- **Fix**: Ensure backend CORS allows `http://localhost:3000` (check `jgod/api/main.py`)

### No Data Showing
- **Symptom**: Components show empty states even for symbols with data
- **Fix**: 
  - Check backend logs for errors
  - Verify database has prediction data for test symbol (e.g., "2330")
  - Run: `curl http://127.0.0.1:8000/api/v1/predictions/latest/2330`

