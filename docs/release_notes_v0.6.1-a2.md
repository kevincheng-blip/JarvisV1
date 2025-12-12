# J-GOD v0.6.1-A2 Release Notes

**發布日期：** 2025-12-13  
**版本：** v0.6.1-A2

---

## 亮點 (Highlights)

此版本 (v0.6.1-A2) 為 Decision Engine V3 新增**決策快照存取能力**，提供完整的快照管理與重播基礎：

- **Decision V3 Snapshot Storage**：JSONL 儲存（`data/decision_v3/snapshots.jsonl`）
- **快照 API**：`/recompute`（計算並存檔）、`/latest`（讀取最新）、`/list`（列出歷史）
- **War Room V2 整合**：DecisionV3Card 新增 "Recompute" 按鈕，一鍵重新計算並存檔
- **快照歷史顯示**：顯示最近 N 筆快照（created_at + primary strategy + confidence）
- **永不 404**：所有 API 端點保證回 200（無資料時回空狀態）

---

## 新增/更新端點 (New/Updated Endpoints)

### 新增後端 API
- `POST /api/v1/decision-v3/recompute/{symbol}?mode=performance&limit=60&k=5`
  - 重新計算並存檔 Decision V3 決策快照
  - 回應：`DecisionV3SnapshotResponseSchema`（含 snapshot_id, created_at, result）

- `GET /api/v1/decision-v3/latest/{symbol}`
  - 讀取最新存檔的決策快照
  - 若無快照：回 200 + 空狀態（risk_state="RISK_OFF"），永不 404

- `GET /api/v1/decision-v3/list/{symbol}?n=20`
  - 列出指定股票的決策快照列表（最新 N 筆）
  - 若無快照：回 200 + items=[]，永不 404

### 保留既有端點
- `GET /api/v1/decision-v3/decide/{symbol}`（不變，即時計算不存檔）

### 新增前端 API Wrapper (in `trading-ui/jgod-trading-ui/src/api/client.ts`)
- `getDecisionV3Latest(symbol)`
- `recomputeDecisionV3(symbol, {mode, limit, k})`
- `listDecisionV3Snapshots(symbol, n)`

---

## 驗證指令 (Verification Commands)

### 後端驗證
1. **語法檢查**
   ```bash
   python3 -m compileall jgod -q
   # 預期：無輸出（0 錯誤）
   ```

2. **Decision V3 Snapshot 合約測試**
   ```bash
   pytest tests/test_decision_v3_snapshot_contract.py -q -v
   # 預期：4 passed
   ```

3. **完整 CI 檢查**
   ```bash
   bash scripts/ci_quick_check.sh
   # 預期：所有 10 個檢查通過
   ```

4. **手動 Curl 範例**
   ```bash
   # Recompute (計算並存檔)
   curl -X POST "http://127.0.0.1:8000/api/v1/decision-v3/recompute/2330?mode=performance&limit=60&k=5"
   # 預期：200 OK, JSON 包含 snapshot_id, created_at, result
   
   # Get Latest
   curl -i "http://127.0.0.1:8000/api/v1/decision-v3/latest/2330"
   # 預期：200 OK, JSON 包含 snapshot_id（若已 recompute）或空狀態（若無快照）
   
   # List Snapshots
   curl -i "http://127.0.0.1:8000/api/v1/decision-v3/list/2330?n=20"
   # 預期：200 OK, JSON 包含 items[]（可能為空）
   
   # NO_DATA case (Latest)
   curl -i "http://127.0.0.1:8000/api/v1/decision-v3/latest/NO_SYMBOL"
   # 預期：200 OK, risk_state="RISK_OFF", position_scale <= 0.25
   ```

### 前端驗證
1. **啟動開發伺服器**
   ```bash
   cd trading-ui/jgod-trading-ui && npm run dev
   ```

2. **導航至 War Room V2**
3. **驗證 DecisionV3Card**：
   - 應顯示在右側欄（SRankRecommendationCard 下方）
   - 顯示最新快照時間（若有）
   - 顯示 "Recompute" 按鈕
   - 點擊 "Recompute"：
     - 按鈕顯示 "計算中..."
     - 成功後顯示 "決策重新計算成功"
     - 卡片自動刷新（顯示新的快照時間）
   - 顯示最近快照列表（最多 5 筆）：
     - 顯示 created_at（格式化）
     - 顯示 primary strategy
     - 顯示 confidence
   - 若無快照：仍顯示決策結果（即時計算），但無快照時間

4. **驗證快照持久化**：
   - 點擊 "Recompute" 產生快照
   - 重新整理頁面
   - 驗證快照時間仍顯示（從 latest endpoint 讀取）

---

## 已知限制 (Known Limitations)

- **快照格式**：目前使用 JSONL，未來可擴充為更結構化的儲存（如 SQLite）
- **快照清理**：目前無自動清理機制，需手動管理 `data/decision_v3/snapshots.jsonl`
- **快照查詢**：目前僅支援按 symbol 查詢，未來可擴充為按日期範圍、mode 等條件查詢
- **前端快照列表**：目前僅顯示最近 5 筆，未來可擴充為分頁或無限滾動

---

## 技術細節

### Decision V3 Snapshot 格式

```json
{
  "snapshot_id": "uuid",
  "created_at": "2025-12-13T10:30:00",
  "symbol": "2330",
  "mode": "performance",
  "limit": 60,
  "k": 5,
  "result": {
    "symbol": "2330",
    "selected_primary_strategy": "trend_follow",
    "selected_secondary_strategies": ["momentum"],
    "weights": [...],
    "risk_plan": {
      "position_scale": 0.80,
      "risk_state": "RISK_ON",
      "reasons": [...]
    },
    "confidence": 0.85,
    "explain": "..."
  }
}
```

### Storage 路徑
- `data/decision_v3/snapshots.jsonl`（append-only JSONL 格式）

### API 錯誤處理策略
- **永不 404**：所有端點保證回 200
- **無資料時**：回空狀態（risk_state="RISK_OFF", position_scale=0.20）
- **系統錯誤時**：回錯誤狀態（仍為 200，但 explain 說明錯誤）

---

**文件結束**

