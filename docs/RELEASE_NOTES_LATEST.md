# J-GOD Latest Release Notes

**Last Updated:** 2025-12-13  
**Current Version:** v0.6.1-A2

---

## Highlights

This release includes three major feature packages:

1. **v0.4.0**: Patch lifecycle E2E + War Room Quick Actions + Frontend API consistency
2. **v0.5.0-B1 + v0.5.1-B2**: S-Rank Engine V2 recommendation system (rule-based → performance-driven)
3. **v0.6.0-A1 + v0.6.1-A2**: Decision Engine V3 (rule-based × S-Rank V2 × Performance Feed) with snapshot management

---

## New APIs

### S-Rank Engine V2
- `GET /api/v1/s-rank-v2/recommendation/{symbol}?mode=performance&limit=60&k=5` - Get strategy recommendation
- `POST /api/v1/s-rank-v2/recompute/{symbol}?mode=performance&limit=60&k=5` - Recompute and save snapshot
- `GET /api/v1/s-rank-v2/latest/{symbol}` - Get latest recommendation snapshot

### Strategy Performance Feed
- `GET /api/v1/strategy-perf/latest/{symbol}` - Get latest performance snapshot
- `POST /api/v1/strategy-perf/recompute/{symbol}?limit=60&window=20` - Recompute and save performance snapshot

### Decision Engine V3
- `GET /api/v1/decision-v3/decide/{symbol}?mode=performance&limit=60&k=5` - Get decision (real-time, no storage)
- `POST /api/v1/decision-v3/recompute/{symbol}?mode=performance&limit=60&k=5` - Recompute and save decision snapshot
- `GET /api/v1/decision-v3/latest/{symbol}` - Get latest decision snapshot
- `GET /api/v1/decision-v3/list/{symbol}?n=20` - List decision snapshots

### Doctrine Patch (Enhanced)
- `POST /api/v1/doctrine/patches/{patchId}/approve` - Approve patch (with request body)
- `POST /api/v1/doctrine/patches/{patchId}/reject` - Reject patch (with request body)
- `POST /api/v1/doctrine/patches/{patchId}/deploy` - Deploy patch (with request body)
- `POST /api/v1/doctrine/patches/{patchId}/revert` - Revert patch (with request body)

---

## Tests

### New Contract Tests
- `tests/test_doctrine_patch_lifecycle_e2e.py` - Doctrine Patch lifecycle E2E test
- `tests/test_s_rank_v2_contract.py` - S-Rank V2 recommendation contract tests
- `tests/test_strategy_perf_contract.py` - Strategy Performance contract tests
- `tests/test_decision_v3_contract.py` - Decision V3 contract tests
- `tests/test_decision_v3_snapshot_contract.py` - Decision V3 snapshot contract tests

### Updated Smoke Tests
- `tests/test_war_room_v2_smoke.py` - Added health checks for:
  - S-Rank V2 recommendation
  - Strategy Performance latest
  - Decision V3 decide/latest/recompute

### CI Quick Check
- `scripts/ci_quick_check.sh` - Now includes 10 checks:
  1. Compileall syntax check
  2. War Room V2 smoke test
  3. Predictions timeline contract test
  4. Core modules import test
  5. Prediction stability contract test
  6. Doctrine Patch lifecycle E2E test
  7. S-Rank V2 contract test
  8. Strategy Performance contract test
  9. Decision V3 contract test
  10. Decision V3 Snapshot contract test

---

## Verification Commands

### Backend
```bash
# Syntax check
python3 -m compileall jgod -q

# Full CI check
bash scripts/ci_quick_check.sh

# Individual contract tests
pytest tests/test_doctrine_patch_lifecycle_e2e.py -q
pytest tests/test_s_rank_v2_contract.py -q
pytest tests/test_strategy_perf_contract.py -q
pytest tests/test_decision_v3_contract.py -q
pytest tests/test_decision_v3_snapshot_contract.py -q
```

### Frontend
```bash
cd trading-ui/jgod-trading-ui && npm run dev
# Navigate to War Room V2 and verify:
# - Patch Queue Card with quick actions (Run Sim, Approve, Reject, Deploy, Revert)
# - S-Rank Recommendation Card with performance metrics and Recompute Perf button
# - Decision V3 Card with Recompute button and snapshot history
```

### Manual API Tests
```bash
# S-Rank V2
curl "http://127.0.0.1:8000/api/v1/s-rank-v2/recommendation/2330?mode=performance"

# Strategy Performance
curl "http://127.0.0.1:8000/api/v1/strategy-perf/latest/2330"

# Decision V3
curl "http://127.0.0.1:8000/api/v1/decision-v3/decide/2330?mode=performance"
curl -X POST "http://127.0.0.1:8000/api/v1/decision-v3/recompute/2330?mode=performance"
curl "http://127.0.0.1:8000/api/v1/decision-v3/latest/2330"
```

---

## Known Limitations

1. **Snapshot Storage**: JSONL files in `data/` directory (no automatic cleanup)
2. **Performance Evaluator**: Deterministic proxy metrics (not real backtest results)
3. **Decision Logic**: Rule-based (not ML/RL integrated yet)
4. **Frontend State**: No global state management (using React Query + local state)
5. **API Versioning**: Some endpoints still use `/api` prefix (legacy), new ones use `/api/v1`

---

## Storage Paths

- Doctrine Patches: `data/doctrine/patches.jsonl`
- S-Rank V2 Snapshots: `data/s_rank_v2/recommendations.jsonl`
- Strategy Performance Snapshots: `data/strategy_perf/perf_snapshots.jsonl`
- Decision V3 Snapshots: `data/decision_v3/snapshots.jsonl`

---

**For detailed release notes, see:**
- `docs/release_notes_v0.4.0.md`
- `docs/release_notes_v0.6.0-a1.md`
- `docs/release_notes_v0.6.1-a2.md`

