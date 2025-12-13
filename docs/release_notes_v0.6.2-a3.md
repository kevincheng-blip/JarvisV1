# J-GOD v0.6.2-A3 Release Notes

**發布日期：** 2025-12-13  
**版本：** v0.6.2-A3  
**類型：** Epic Pack (Self-Compare / Self-Evolve)

---

## Highlights

本版本為 Decision Engine V3 新增「自我評估迴路」功能，讓系統能夠自動回放驗證決策表現，生成對照報告，形成可追蹤的 evolution loop。

### 核心功能

1. **Decision V3 Evaluation API**：可重現的回放評估機制
   - 評估指標：hit_rate_proxy, avg_return_proxy, max_drawdown_proxy, turnover_proxy, decision_consistency
   - Verdict：IMPROVED / NEUTRAL / REGRESSED / NO_DATA
   - 自動生成建議（Traditional Chinese）

2. **Evaluation Snapshot Storage**：JSONL append-only 儲存
   - 路徑：`data/decision_v3/evaluations.jsonl`
   - 支援 save/load_latest/list 操作

3. **War Room V2 UI 整合**：DecisionV3Card 新增 Evaluation 區塊
   - "Run Evaluation" 按鈕
   - Verdict badge + 指標 grid + next step 建議
   - 空狀態處理（NO_DATA 不算 error）

---

## New APIs

### Decision V3 Evaluation Endpoints

- `POST /api/v1/decision-v3/eval/recompute/{symbol}?mode=performance&limit=60&k=5&window=20`
  - 重新計算並存檔評估快照
  - 回傳：`DecisionV3EvalSnapshotResponseSchema`

- `GET /api/v1/decision-v3/eval/latest/{symbol}`
  - 讀取最新存檔的評估快照
  - 無資料時回傳 200 + NO_DATA 狀態（不拋 404）

- `GET /api/v1/decision-v3/eval/list/{symbol}?n=20`
  - 列出指定股票的評估快照列表
  - 空列表時仍回傳 200

---

## Evaluation Metrics

### 指標定義

- **hit_rate_proxy**: 命中率（依 primary strategy 決定方向）
  - trend_follow/breakout/momentum: 正 delta 比例
  - mean_reversion: 負 delta 比例

- **avg_return_proxy**: 平均報酬代理（mean(delta(final_score))）

- **max_drawdown_proxy**: 最大回撤（從 equity curve 計算）

- **turnover_proxy**: 週轉率代理（abs(delta(final_score)) 平均）

- **decision_consistency**: 決策一致性（最近 5 筆 signal 穩定度）

### Verdict 判定規則

- **NO_DATA**: `n_points < 10`
- **IMPROVED**: `avg_return_proxy > 0` 且 `hit_rate_proxy >= 0.55` 且 `max_drawdown_proxy <= 0.18`
- **REGRESSED**: `avg_return_proxy < 0` 且 `max_drawdown_proxy > 0.25`
- **NEUTRAL**: 其他情況

---

## Tests

### New Contract Tests

- `tests/test_decision_v3_eval_contract.py`
  - 測試 recompute → 200 + schema
  - 測試 latest → 200 + schema（含 NO_DATA case）
  - 測試 list → 200 + items

### Updated Smoke Tests

- `tests/test_war_room_v2_smoke.py`
  - 新增 health checks：
    - `test_decision_v3_eval_recompute_health_check`
    - `test_decision_v3_eval_latest_health_check`
    - `test_decision_v3_eval_list_health_check`

### CI Quick Check

- `scripts/ci_quick_check.sh`
  - 新增 Check 11：`pytest tests/test_decision_v3_eval_contract.py -q`
  - 總計 11 個檢查全部通過

---

## Frontend Changes

### New Hooks

- `trading-ui/jgod-trading-ui/src/hooks/useDecisionV3Eval.ts`
  - `useDecisionV3EvalLatest(symbol)`
  - `useRecomputeDecisionV3Eval(symbol)`
  - `useDecisionV3EvalList(symbol, n)`

### Updated Components

- `trading-ui/jgod-trading-ui/src/components/war-room-v2/DecisionV3Card.tsx`
  - 新增 Evaluation 區塊
  - "Run Evaluation" 按鈕（window 預設 20）
  - Verdict badge + metrics grid + recommendation_next_step
  - 最近 N 筆評估歷史

### API Client

- `trading-ui/jgod-trading-ui/src/api/client.ts`
  - 新增 wrappers：
    - `recomputeDecisionV3Eval(symbol, options)`
    - `getDecisionV3EvalLatest(symbol)`
    - `listDecisionV3Evals(symbol, n)`

---

## Verification Commands

### Backend

```bash
# Syntax check
python3 -m compileall jgod -q

# Full CI check (11 checks)
bash scripts/ci_quick_check.sh

# Individual contract test
pytest tests/test_decision_v3_eval_contract.py -q
```

### Manual API Tests

```bash
# Recompute evaluation
curl -X POST "http://127.0.0.1:8000/api/v1/decision-v3/eval/recompute/2330?mode=performance&window=20"

# Get latest evaluation
curl "http://127.0.0.1:8000/api/v1/decision-v3/eval/latest/2330"

# List evaluations
curl "http://127.0.0.1:8000/api/v1/decision-v3/eval/list/2330?n=20"
```

### Frontend

```bash
cd trading-ui/jgod-trading-ui && npm run dev
# Navigate to War Room V2 → Decision V3 Card → Evaluation section
# Click "Run Evaluation" button
# Verify verdict badge, metrics grid, and recommendation display
```

---

## Known Limitations

1. **Evaluation Window**: 預設 window=20，可調整但需注意資料點數限制（至少 10 點）
2. **Return Proxy**: 使用 `delta(final_score)` 作為報酬代理，非真實交易回報
3. **Decision Consistency**: 使用 signal 穩定度作為 proxy，非真實決策歷史比較
4. **Storage**: JSONL 檔案無自動清理機制（需手動管理）

---

## Storage Paths

- Decision V3 Evaluations: `data/decision_v3/evaluations.jsonl`

---

## Next Steps

- [ ] 整合真實交易回報（若有 VirtualTrade 資料）
- [ ] 加入評估歷史對比（比較不同時間點的 verdict）
- [ ] 自動化評估排程（定期 recompute）
- [ ] 評估報告匯出功能

