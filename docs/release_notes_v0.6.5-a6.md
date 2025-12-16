# J-GOD v0.6.5-A6 Release Notes

## 版本定位

**v0.6.5-A6: Execution Grounding Layer (執行層落地)**

本版本引入「執行層落地」（Execution Grounding Layer），透過 VirtualLedger（虛擬帳本）為 Decision V3 的評估與競技場提供基於模擬實現損益（P&L）的評估能力，取代原本的代理指標（proxy metrics）。

## 核心功能完成清單

### 1. VirtualLedger 核心模組

- **`jgod/execution/virtual_ledger.py`**: 實現虛擬帳本核心邏輯
  - `PositionState`: 持倉狀態（數量、平均成本）
  - `VirtualLedger`: 帳本主體（現金、持倉、已實現/未實現損益、NAV）
  - `mark_to_market()`: 市價標記
  - `buy()` / `sell()`: 買賣操作（含手續費、稅費計算）
  - `snapshot()`: 生成快照
  - 固定費率：`FEE_RATE = 0.001425`（台股手續費 0.1425%），`SELL_TAX_RATE = 0.003`（賣出交易稅 0.3%）

### 2. Order Generation Engine

- **`jgod/execution/order_engine.py`**: 訂單生成引擎
  - `OrderGenerationEngine.generate_orders()`: 從 Decision V3 結果與帳本狀態生成訂單請求
  - 考慮目標倉位比例、現金充足性、持倉限制
  - 返回 `OrderRequest`（BUY/SELL/HOLD + 數量 + 原因）

### 3. Execution Storage & Service

- **`jgod/execution/storage.py`**: JSONL 儲存（`data/execution/ledger_snapshots.jsonl`）
  - `save_ledger_snapshot()`: 儲存帳本快照
  - `load_latest()`: 載入最新快照
  - `list_latest()`: 列出最近 N 筆快照

- **`jgod/execution/service.py`**: 服務層
  - `get_latest_ledger()`: 取得最新帳本（或預設空帳本）
  - `recompute_ledger()`: 重置帳本並儲存
  - `simulate_order_from_latest_decision()`: 從最新 Decision V3 模擬訂單

### 4. API: Execution Endpoints

- **`jgod/api/schemas/execution.py`**: Pydantic 回應 schema
  - `LedgerPositionSchema`: 持倉 schema
  - `LedgerSnapshotSchema`: 帳本快照 schema
  - `OrderRequestSchema`: 訂單請求 schema
  - `ExecutionSimulateResponseSchema`: 模擬回應 schema
  - `LedgerResponseSchema`: 帳本回應 schema

- **`jgod/api/routers/execution.py`**: 新增端點
  - `GET /api/v1/execution/ledger/latest/{symbol}`: 取得最新帳本（200 OK，無資料時返回預設帳本）
  - `POST /api/v1/execution/ledger/recompute/{symbol}`: 重置帳本（200 OK）
  - `POST /api/v1/execution/order/simulate/{symbol}`: 模擬訂單（200 OK，無資料時返回 HOLD）

### 5. Decision V3 Evaluation/Arena 升級為 P&L Grounded

- **`jgod/decision_v3/evaluation.py`**: 
  - `evaluate_decision_v3_grounded()`: 使用 VirtualLedger 的評估函數
  - 在評估回放中執行帳本操作（mark_to_market、生成訂單、執行買賣）
  - 指標從帳本歷史計算：`avg_return_proxy` → `avg_daily_nav_return`，`max_drawdown_proxy` 從 NAV 曲線計算，`turnover_proxy` 從成交金額/平均 NAV 計算
  - `evaluate_decision_v3()` 預設 `use_ledger=True`，自動使用帳本評估

- **`jgod/decision_v3/compare.py`**: 已使用 `evaluate_decision_v3()`（預設使用帳本）

- **`jgod/decision_v3/arena.py`**: 已使用 `evaluate_decision_v3()`（預設使用帳本）

### 6. Frontend: War Room V2 Ledger & Order Preview

- **`trading-ui/jgod-trading-ui/src/api/client.ts`**: 已包含執行 API 包裝
  - `getExecutionLedgerLatest()`
  - `recomputeExecutionLedger()`
  - `simulateExecutionOrder()`

- **`trading-ui/jgod-trading-ui/src/hooks/useExecution.ts`**: React Query hooks
  - `useLedgerLatest()`
  - `useRecomputeLedger()`
  - `useSimulateOrder()`

- **`trading-ui/jgod-trading-ui/src/components/war-room-v2/LedgerStatusCard.tsx`**: 帳本狀態卡片
  - 顯示 NAV、現金、P&L、持倉
  - 「重置帳本」按鈕
  - 「模擬訂單」按鈕
  - 訂單預覽（BUY/SELL/HOLD + 數量 + 原因）

- **`trading-ui/jgod-trading-ui/src/pages/WarRoomV2Dashboard.tsx`**: 整合 `LedgerStatusCard`

### 7. Tests & CI

- **`tests/test_virtual_ledger_contract.py`**: VirtualLedger 合約測試
  - 初始化、mark_to_market、買賣操作、平均成本計算、快照生成

- **`tests/test_execution_api_contract.py`**: Execution API 合約測試
  - `GET ledger/latest`、`POST ledger/recompute`、`POST order/simulate`
  - NO_DATA 處理（200 OK，返回預設狀態）

- **`tests/test_war_room_v2_smoke.py`**: 已包含執行端點健康檢查

- **`scripts/ci_quick_check.sh`**: 已包含 Check 14（Virtual Ledger）和 Check 15（Execution API）

## 新 API 端點

### Execution API

1. **`GET /api/v1/execution/ledger/latest/{symbol}?initial_cash=1000000.0`**
   - 取得最新帳本快照
   - 回應：`LedgerResponseSchema`（200 OK，無資料時返回預設帳本）

2. **`POST /api/v1/execution/ledger/recompute/{symbol}?initial_cash=1000000.0`**
   - 重置帳本並儲存新快照
   - 回應：`LedgerResponseSchema`（200 OK）

3. **`POST /api/v1/execution/order/simulate/{symbol}?mode=performance&limit=60&k=5`**
   - 從最新 Decision V3 模擬訂單
   - 回應：`ExecutionSimulateResponseSchema`（200 OK，無資料時返回 HOLD）

## 驗證命令

```bash
# 語法檢查
python3 -m compileall jgod -q

# 合約測試
pytest tests/test_virtual_ledger_contract.py -q
pytest tests/test_execution_api_contract.py -q

# CI 快速檢查
bash scripts/ci_quick_check.sh

# 手動 API 測試
curl http://127.0.0.1:8000/api/v1/execution/ledger/latest/2330
curl -X POST http://127.0.0.1:8000/api/v1/execution/ledger/recompute/2330
curl -X POST http://127.0.0.1:8000/api/v1/execution/order/simulate/2330
```

## 已知限制

1. **價格代理**: 目前使用 `final_score` 推導價格代理（`price_t = price_{t-1} * (1 + daily_return_proxy)`），非真實市場價格
2. **單一標的**: VirtualLedger 目前僅支援單一標的（symbol），多標的組合需在未來版本擴展
3. **簡化滑價**: 訂單執行假設完全成交，無滑價模擬（v0.6.6-A7 將引入 Fill Engine）
4. **評估回放**: 評估使用固定決策（整個 window 期間使用同一個 Decision V3 結果），非逐日重新決策

## 與前一版（v0.6.4-A5）的能力差異

### Before (v0.6.4-A5)
- Decision V3 Evaluation/Arena 使用代理指標（proxy metrics）
- `avg_return_proxy`: 基於 `final_score` 變化
- `max_drawdown_proxy`: 基於權益曲線（equity curve）
- `turnover_proxy`: 基於 `final_score` 絕對變化
- 無實際 P&L 追蹤

### After (v0.6.5-A6)
- Decision V3 Evaluation/Arena 使用 VirtualLedger 模擬實現損益
- `avg_return_proxy`: 基於 NAV 日報酬率（`avg_daily_nav_return`）
- `max_drawdown_proxy`: 基於 NAV 曲線計算
- `turnover_proxy`: 基於成交金額 / 平均 NAV
- 完整 P&L 追蹤（已實現、未實現、NAV）
- 手續費、稅費計算
- 訂單生成與模擬

## 延伸點（預留）

1. **多標的組合**: 擴展 VirtualLedger 支援多標的組合帳本
2. **真實價格**: 整合市場資料服務（MDTS）使用真實 OHLCV 價格
3. **Fill Engine**: 引入滑價與部分成交模擬（v0.6.6-A7）
4. **逐日重新決策**: 評估回放中每日重新計算 Decision V3（而非固定決策）
5. **風險限制**: 加入持倉上限、單一標的上限等風險控制

## 技術細節

- **儲存格式**: JSONL（append-only）
- **費率**: 台股標準（手續費 0.1425%，賣出交易稅 0.3%）
- **價格代理**: `daily_return_proxy = max(-0.05, min(0.05, final_score * 0.002))`
- **初始現金**: 預設 1,000,000.0（可配置）
