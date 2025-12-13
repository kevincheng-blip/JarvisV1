# J-GOD v0.6.4-A5 Release Notes

**發布日期：** 2025-12-13  
**版本：** v0.6.4-A5  
**類型：** Epic Pack (Multi-Compare + Champion/Challenger + Auto-Tuning)

---

## Highlights

本版本為 Decision Engine V3 新增「競技場對照」功能，實現多挑戰者比較、冠軍-挑戰者機制，以及自動調參能力，形成完整的 evolution loop。

### 核心功能

1. **Decision V3 Arena：多挑戰者競技場**
   - Champion：Decision V3（現有引擎）
   - Challengers：
     - RISK_OFF baseline：固定 risk_state="RISK_OFF", position_scale=0.20, primary_strategy="risk_off"
     - MOMENTUM baseline：固定 risk_state="CAUTION", position_scale=0.50, primary_strategy="momentum"
     - EQUAL_WEIGHT baseline：均等權重策略，position_scale=0.50
   - Scoreboard：每個挑戰者的 composite score + metrics
   - Winner 判定：最高 composite score（若被 Pareto 支配則降權）
   - Regression 警報：若 winner != V3 且差距 >= 0.03 → 觸發回歸警報
   - Pareto 支配檢查：在 (return↑, MDD↓, turnover↓) 三維上檢查是否被支配

2. **Auto-Tuning：自動調參**
   - 風險映射 grid search：STABLE/WATCH/VOLATILE 的 position_scale 候選值
   - Composite weights grid search：權重組合優化
   - 產出 best_config、top_variants（前 5）、recommended_update（繁中建議）

3. **Arena Snapshot Storage**：JSONL append-only 儲存
   - 路徑：`data/decision_v3/arena.jsonl`
   - 支援 save/load_latest/list 操作

4. **War Room V2 UI 整合**：DecisionV3Card 新增 Arena 區塊
   - "Run Arena" 按鈕
   - Winner badge + Regression alert badge
   - Scoreboard table（至少 4 列）
   - Auto-Tuning 結果（best config + top variants）
   - 空狀態處理（NO_DATA 不算 error）

---

## New APIs

### Decision V3 Arena Endpoints

- `POST /api/v1/decision-v3/arena/recompute/{symbol}?mode=performance&limit=60&k=5&window=20`
  - 重新計算並存檔競技場快照
  - 回傳：`ArenaResponseSchema`

- `GET /api/v1/decision-v3/arena/latest/{symbol}`
  - 讀取最新存檔的競技場快照
  - 無資料時回傳 200 + NO_DATA 狀態（不拋 404）

- `GET /api/v1/decision-v3/arena/list/{symbol}?n=20`
  - 列出指定股票的競技場快照列表
  - 空列表時仍回傳 200

---

## Arena Logic

### Composite Score Formula

```
score = avg_return_proxy * 1.0
      - max_drawdown_proxy * 0.9
      + hit_rate_proxy * 0.15
      - turnover_proxy * 0.12
      + decision_consistency * 0.08
```

### Winner Determination

- 計算所有挑戰者的 composite score
- 檢查 Pareto 支配：若被支配則 composite_score *= 0.95
- Winner = 最高 composite_score 的挑戰者

### Regression Detection

- 若 `winner_id != "V3"` 且 `(winner_score - v3_score) >= 0.03` → `is_regression = True`
- 門檻：0.03（固定值）

### Auto-Tuning Grid Search

**Risk Mapping Candidates:**
- STABLE: [0.70, 0.80, 0.90]
- WATCH: [0.45, 0.55, 0.65]
- VOLATILE: [0.25, 0.35, 0.45]
- NO_DATA: 0.20（固定）

**Composite Weight Candidates:**
- 3 組權重組合（簡化以控制計算量）

**Grid Search:**
- 3x3 = 9 個組合
- 對每個 variant 執行完整評估
- 選取 composite_score 最高者作為 best_config
- 取前 5 名作為 top_variants

---

## Tests

### New Contract Tests

- `tests/test_decision_v3_arena_contract.py`
  - 測試 recompute → 200 + schema
  - 測試 latest → 200 + schema（含 NO_DATA case）
  - 測試 list → 200 + items

### Updated Smoke Tests

- `tests/test_war_room_v2_smoke.py`
  - 新增 health checks：
    - `test_decision_v3_arena_recompute_health_check`
    - `test_decision_v3_arena_latest_health_check`
    - `test_decision_v3_arena_list_health_check`

### CI Quick Check

- `scripts/ci_quick_check.sh`
  - 新增 Check 13：`pytest tests/test_decision_v3_arena_contract.py -q`
  - 總計 13 個檢查全部通過

---

## Frontend Changes

### New Hooks

- `trading-ui/jgod-trading-ui/src/hooks/useDecisionV3Arena.ts`
  - `useDecisionV3ArenaLatest(symbol)`
  - `useRecomputeDecisionV3Arena(symbol)`
  - `useDecisionV3ArenaList(symbol, n)`

### Updated Components

- `trading-ui/jgod-trading-ui/src/components/war-room-v2/DecisionV3Card.tsx`
  - 新增 Arena 區塊（在 Compare 區塊下方）
  - "Run Arena" 按鈕（window 預設 20）
  - Winner badge + Regression alert badge
  - Scoreboard table（挑戰者、分數、報酬、回撤、支配狀態）
  - Auto-Tuning 結果（best config + top 5 variants）
  - 最近 N 筆競技場歷史

### API Client

- `trading-ui/jgod-trading-ui/src/api/client.ts`
  - 新增 wrappers：
    - `recomputeDecisionV3Arena(symbol, options)`
    - `getDecisionV3ArenaLatest(symbol)`
    - `listDecisionV3Arena(symbol, n)`

---

## Verification Commands

### Backend

```bash
# Syntax check
python3 -m compileall jgod -q

# Full CI check (13 checks)
bash scripts/ci_quick_check.sh

# Individual contract test
pytest tests/test_decision_v3_arena_contract.py -q
```

### Manual API Tests

```bash
# Recompute arena
curl -X POST "http://127.0.0.1:8000/api/v1/decision-v3/arena/recompute/2330?mode=performance&window=20"

# Get latest arena
curl "http://127.0.0.1:8000/api/v1/decision-v3/arena/latest/2330"

# List arenas
curl "http://127.0.0.1:8000/api/v1/decision-v3/arena/list/2330?n=20"
```

### Frontend

```bash
cd trading-ui/jgod-trading-ui && npm run dev
# Navigate to War Room V2 → Decision V3 Card → Arena section
# Click "Run Arena" button
# Verify scoreboard table, winner badge, auto-tuning results
```

---

## Known Limitations

1. **Grid Search Scope**: 目前僅測試 9 個組合（3x3），未來可擴充
2. **Regression Threshold**: 固定為 0.03，未來可根據實際數據調整
3. **Pareto Penalty**: 被支配者降權 5%（固定值），未來可調整
4. **Storage**: JSONL 檔案無自動清理機制（需手動管理）
5. **V3_VARIANT**: 目前未實作，未來可加入更多 variant 類型

---

## Storage Paths

- Decision V3 Arena: `data/decision_v3/arena.jsonl`

---

## Next Steps

- [ ] 擴充 Grid Search 範圍（更多 risk mapping 和 weight 組合）
- [ ] 實作 V3_VARIANT challenger（動態參數變體）
- [ ] 加入歷史對比（比較不同時間點的 winner）
- [ ] 自動化競技場排程（定期 recompute）
- [ ] 競技場報告匯出功能
- [ ] 可配置的 regression threshold 和 Pareto penalty

