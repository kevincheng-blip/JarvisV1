# J-GOD v0.6.3-A4 Release Notes

**發布日期：** 2025-12-13  
**版本：** v0.6.3-A4  
**類型：** Epic Pack (V3 vs Baseline Compare + Evolution Report)

---

## Highlights

本版本為 Decision Engine V3 新增「對照評估」功能，讓系統能夠比較 Decision V3 與 Baseline 的表現差異，形成可追蹤的 evolution loop。

### 核心功能

1. **Decision Compare Engine**：V3 vs Baseline 對照評估
   - Baseline 定義：固定 risk_state="CAUTION", position_scale=0.50, primary_strategy="momentum", confidence=0.50
   - 使用相同 evaluator 分別評估 V3 與 Baseline
   - Winner 判定：V3 / BASELINE / TIE / NO_DATA
   - Delta metrics：每個指標的差值（v3 - baseline）
   - Summary：繁中 <= 8 行（說明為什麼贏/輸）
   - Recommendation：繁中 <= 6 行（指向下一個工程動作）

2. **Compare Snapshot Storage**：JSONL append-only 儲存
   - 路徑：`data/decision_v3/compare.jsonl`
   - 支援 save/load_latest/list 操作

3. **War Room V2 UI 整合**：DecisionV3Card 新增 Compare 區塊
   - "Run Compare" 按鈕
   - Winner badge + delta metrics grid + summary + next step
   - 空狀態處理（NO_DATA 不算 error）

---

## New APIs

### Decision V3 Compare Endpoints

- `POST /api/v1/decision-v3/compare/recompute/{symbol}?mode=performance&limit=60&k=5&window=20`
  - 重新計算並存檔對照評估快照
  - 回傳：`CompareSnapshotResponseSchema`

- `GET /api/v1/decision-v3/compare/latest/{symbol}`
  - 讀取最新存檔的對照評估快照
  - 無資料時回傳 200 + NO_DATA 狀態（不拋 404）

- `GET /api/v1/decision-v3/compare/list/{symbol}?n=20`
  - 列出指定股票的對照評估快照列表
  - 空列表時仍回傳 200

---

## Compare Logic

### Baseline Definition

- **risk_state**: "CAUTION"
- **position_scale**: 0.50
- **primary_strategy**: "momentum" (固定)
- **confidence**: 0.50
- **weights**: momentum=0.60, trend_follow=0.25, risk_off=0.15

### Winner Determination

使用 composite score 比較：
- **score = avg_return_proxy - 0.7*max_drawdown_proxy + 0.2*hit_rate_proxy - 0.1*turnover_proxy**
- 比較 `score_v3` vs `score_baseline`
- 若 `abs(score_diff) < 0.01` → TIE
- 若 `score_v3 > score_baseline` → V3
- 否則 → BASELINE

### Delta Metrics

- **hit_rate_proxy**: v3 - baseline
- **avg_return_proxy**: v3 - baseline
- **max_drawdown_proxy**: v3 - baseline（負值表示 V3 回撤更小）
- **turnover_proxy**: v3 - baseline
- **decision_consistency**: v3 - baseline

---

## Tests

### New Contract Tests

- `tests/test_decision_v3_compare_contract.py`
  - 測試 recompute → 200 + schema
  - 測試 latest → 200 + schema（含 NO_DATA case）
  - 測試 list → 200 + items

### Updated Smoke Tests

- `tests/test_war_room_v2_smoke.py`
  - 新增 health checks：
    - `test_decision_v3_compare_recompute_health_check`
    - `test_decision_v3_compare_latest_health_check`
    - `test_decision_v3_compare_list_health_check`

### CI Quick Check

- `scripts/ci_quick_check.sh`
  - 新增 Check 12：`pytest tests/test_decision_v3_compare_contract.py -q`
  - 總計 12 個檢查全部通過

---

## Frontend Changes

### New Hooks

- `trading-ui/jgod-trading-ui/src/hooks/useDecisionV3Compare.ts`
  - `useDecisionV3CompareLatest(symbol)`
  - `useRecomputeDecisionV3Compare(symbol)`
  - `useDecisionV3CompareList(symbol, n)`

### Updated Components

- `trading-ui/jgod-trading-ui/src/components/war-room-v2/DecisionV3Card.tsx`
  - 新增 Compare 區塊（在 Evaluation 區塊下方）
  - "Run Compare" 按鈕（window 預設 20）
  - Winner badge + delta metrics grid + summary + recommendation_next_step
  - 最近 N 筆對照歷史

### API Client

- `trading-ui/jgod-trading-ui/src/api/client.ts`
  - 新增 wrappers：
    - `recomputeDecisionV3Compare(symbol, options)`
    - `getDecisionV3CompareLatest(symbol)`
    - `listDecisionV3Compares(symbol, n)`

---

## Verification Commands

### Backend

```bash
# Syntax check
python3 -m compileall jgod -q

# Full CI check (12 checks)
bash scripts/ci_quick_check.sh

# Individual contract test
pytest tests/test_decision_v3_compare_contract.py -q
```

### Manual API Tests

```bash
# Recompute compare
curl -X POST "http://127.0.0.1:8000/api/v1/decision-v3/compare/recompute/2330?mode=performance&window=20"

# Get latest compare
curl "http://127.0.0.1:8000/api/v1/decision-v3/compare/latest/2330"

# List compares
curl "http://127.0.0.1:8000/api/v1/decision-v3/compare/list/2330?n=20"
```

### Frontend

```bash
cd trading-ui/jgod-trading-ui && npm run dev
# Navigate to War Room V2 → Decision V3 Card → Compare section
# Click "Run Compare" button
# Verify winner badge, delta metrics grid, and summary display
```

---

## Known Limitations

1. **Baseline Strategy**: 目前固定為 "momentum"，未來可擴充為可配置
2. **Score Formula**: Composite score 權重（0.7, 0.2, 0.1）為固定值，未來可調整
3. **Tie Threshold**: 目前為 0.01，未來可根據實際數據調整
4. **Storage**: JSONL 檔案無自動清理機制（需手動管理）

---

## Storage Paths

- Decision V3 Compares: `data/decision_v3/compare.jsonl`

---

## Next Steps

- [ ] 擴充 Baseline 策略池（可選擇不同 baseline）
- [ ] 加入歷史對比（比較不同時間點的 winner）
- [ ] 自動化對照排程（定期 recompute）
- [ ] 對照報告匯出功能

