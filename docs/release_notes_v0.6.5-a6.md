# J-GOD v0.6.5-A6 版本說明

**發布日期：** 2025-12-14  
**版本類型：** Epic Pack (Execution Grounding)  
**目標：** 引入執行層基礎設施，讓 Decision V3 評估/競技場使用虛擬帳本模擬的已實現損益

---

## 一、版本定位

v0.6.5-A6 是「執行層基礎化」版本，建立虛擬帳本（Virtual Ledger）和訂單生成引擎（Order Generation Engine），讓 Decision V3 的評估與競技場系統從「代理報酬指標」升級為「基於實際 P&L 的評估」，為後續真實交易執行奠定基礎。

---

## 二、核心功能完成清單

### 2.1 Virtual Ledger（虛擬帳本）

**功能說明：**
- 模擬真實交易帳本，追蹤現金、持倉、平均成本、已實現損益、未實現損益、淨資產（NAV）
- 支援買入/賣出操作，自動計算手續費（0.1425%）和賣出稅（0.3%）
- 支援 mark-to-market 更新未實現損益和 NAV
- 確保賣出數量不超過持倉（自動 clamp）

**實作位置：**
- `jgod/execution/virtual_ledger.py`：核心帳本邏輯
- `jgod/execution/storage.py`：JSONL 持久化（`data/execution/ledger_snapshots.jsonl`）

**關鍵方法：**
- `buy(symbol, qty, price)`：買入，更新現金和平均成本
- `sell(symbol, qty, price)`：賣出，計算已實現損益
- `mark_to_market(symbol, price)`：更新未實現損益和 NAV
- `snapshot(symbol)`：產生快照供 API/儲存使用

### 2.2 Order Generation Engine（訂單生成引擎）

**功能說明：**
- 將 `DecisionV3Result` 轉換為 `OrderRequest`（BUY/SELL/HOLD + 數量）
- 考慮現金充足性（買入時）和持倉限制（賣出時）
- 根據 `position_scale` 計算目標持倉價值，決定買賣方向和數量
- 確保不產生「無法執行」的訂單

**實作位置：**
- `jgod/execution/order_engine.py`：`OrderGenerationEngine.generate_orders()`

**邏輯流程：**
1. 計算目標持倉價值 = NAV × `position_scale`
2. 計算當前持倉價值 = 持倉數量 × 當前價格
3. 計算差值 = 目標價值 - 當前價值
4. 根據差值決定 BUY/SELL/HOLD
5. 檢查現金/持倉限制，clamp 數量

### 2.3 Decision V3 Evaluation/Arena 升級為 P&L Grounded

**功能說明：**
- `evaluate_decision_v3()` 新增 `use_ledger=True` 參數（預設啟用）
- 評估迴圈中：
  1. 從 `final_score` 變化推導價格代理（price proxy）
  2. 對帳本進行 mark-to-market
  3. 根據決策生成訂單
  4. 執行買賣操作
  5. 從帳本歷史計算指標（avg_daily_nav_return, max_drawdown_proxy, turnover_proxy, hit_rate_proxy）

**實作位置：**
- `jgod/decision_v3/evaluation.py`：升級評估邏輯
- `jgod/decision_v3/compare.py`：使用 ledger-based 評估（預設 `use_ledger=True`）
- `jgod/decision_v3/arena.py`：使用 ledger-based 評估（預設 `use_ledger=True`）

**指標計算：**
- `avg_return_proxy` → `avg_daily_nav_return`（從 NAV 曲線計算）
- `max_drawdown_proxy` → 從 NAV 曲線計算
- `turnover_proxy` → 總交易名目價值 / 平均 NAV
- `hit_rate_proxy` → 正 NAV 報酬天數比例

### 2.4 War Room V2 Ledger Status Display

**功能說明：**
- 新增 `LedgerStatusCard` 顯示虛擬帳本狀態
- 顯示 NAV、現金、已實現/未實現損益、持倉資訊
- 提供「Reset Ledger」和「Simulate Order」按鈕
- 顯示模擬訂單結果（side, qty, reason）

**實作位置：**
- `trading-ui/jgod-trading-ui/src/components/war-room-v2/LedgerStatusCard.tsx`
- `trading-ui/jgod-trading-ui/src/hooks/useExecution.ts`
- `trading-ui/jgod-trading-ui/src/api/client.ts`：新增 Execution API wrappers

---

## 三、新增 API 端點

### 3.1 Execution API

**Base Path：** `/api/v1/execution`

| 方法 | 路徑 | 說明 | 回傳狀態 |
|------|------|------|----------|
| GET | `/ledger/latest/{symbol}` | 取得最新帳本快照 | 200（無資料時回傳預設帳本） |
| POST | `/ledger/recompute/{symbol}?initial_cash=1000000` | 重置並建立新帳本快照 | 200 |
| POST | `/order/simulate/{symbol}?mode=performance&limit=60&k=5` | 模擬訂單生成 | 200（無資料時回傳 HOLD） |

**重要特性：**
- 所有端點保證回傳 200（永不 404）
- 無資料時回傳空狀態或預設值
- 支援 `initial_cash` 參數（預設 1,000,000）

---

## 四、測試與 CI

### 4.1 新增測試

- `tests/test_virtual_ledger_contract.py`：帳本操作合約測試（buy/sell/mark_to_market）
- `tests/test_execution_api_contract.py`：Execution API 合約測試
- `tests/test_war_room_v2_smoke.py`：新增 Execution API 健康檢查

### 4.2 CI 更新

- `scripts/ci_quick_check.sh`：
  - Check 14：`pytest tests/test_virtual_ledger_contract.py -q`
  - Check 15：`pytest tests/test_execution_api_contract.py -q`

---

## 五、已知限制

1. **價格代理（Price Proxy）**：
   - 目前從 `final_score` 變化推導價格，非真實市場價格
   - 公式：`daily_return_proxy = clamp((current_score - prev_score) * 0.002, -0.05, 0.05)`
   - 未來需整合真實價格資料源

2. **訂單執行模擬**：
   - 目前僅模擬訂單生成，不涉及真實成交（fills）
   - 不考慮滑點（slippage）和流動性限制

3. **手續費/稅率**：
   - 固定費率（手續費 0.1425%，賣出稅 0.3%）
   - 未考慮不同券商費率差異

---

## 六、驗證命令

### 6.1 後端驗證

```bash
# 語法檢查
python3 -m compileall jgod -q

# CI 快速檢查（15 個檢查點）
bash scripts/ci_quick_check.sh

# 個別測試
pytest tests/test_virtual_ledger_contract.py -q -v
pytest tests/test_execution_api_contract.py -q -v
pytest tests/test_war_room_v2_smoke.py -q -v
```

### 6.2 API 驗證（curl）

```bash
# 取得最新帳本
curl http://127.0.0.1:8000/api/v1/execution/ledger/latest/2330

# 重置帳本
curl -X POST "http://127.0.0.1:8000/api/v1/execution/ledger/recompute/2330?initial_cash=1000000"

# 模擬訂單
curl -X POST "http://127.0.0.1:8000/api/v1/execution/order/simulate/2330?mode=performance&limit=60&k=5"
```

### 6.3 前端驗證

1. 啟動後端：`uvicorn jgod.api.main:app --reload`
2. 啟動前端：`cd trading-ui/jgod-trading-ui && npm run dev`
3. 開啟 War Room V2 Dashboard
4. 選擇股票（如 2330）
5. 確認 `LedgerStatusCard` 顯示：
   - NAV、現金、P&L、持倉資訊
   - 「Reset Ledger」和「Simulate Order」按鈕可用
   - 模擬訂單結果正確顯示

---

## 七、檔案變更清單

### 7.1 後端核心模組（新增）

- `jgod/execution/__init__.py`
- `jgod/execution/virtual_ledger.py`
- `jgod/execution/order_engine.py`
- `jgod/execution/storage.py`
- `jgod/execution/service.py`

### 7.2 API 層（新增）

- `jgod/api/schemas/execution.py`
- `jgod/api/routers/execution.py`

### 7.3 API 層（修改）

- `jgod/api/main.py`：註冊 execution router
- `jgod/api/routers/__init__.py`：匯出 execution router

### 7.4 Decision V3 升級（修改）

- `jgod/decision_v3/evaluation.py`：新增 ledger-based 評估邏輯
- `jgod/decision_v3/compare.py`：使用 ledger-based 評估（預設）
- `jgod/decision_v3/arena.py`：使用 ledger-based 評估（預設）

### 7.5 測試（新增）

- `tests/test_virtual_ledger_contract.py`
- `tests/test_execution_api_contract.py`

### 7.6 測試（修改）

- `tests/test_war_room_v2_smoke.py`：新增 Execution API 健康檢查
- `scripts/ci_quick_check.sh`：新增 Check 14 和 Check 15

### 7.7 前端（新增）

- `trading-ui/jgod-trading-ui/src/hooks/useExecution.ts`
- `trading-ui/jgod-trading-ui/src/components/war-room-v2/LedgerStatusCard.tsx`

### 7.8 前端（修改）

- `trading-ui/jgod-trading-ui/src/api/client.ts`：新增 Execution API wrappers
- `trading-ui/jgod-trading-ui/src/pages/WarRoomV2Dashboard.tsx`：整合 LedgerStatusCard

### 7.9 文件（新增）

- `docs/release_notes_v0.6.5-a6.md`（本文件）

---

## 八、與前一版（v0.6.4-A5）的能力差異

| 項目 | v0.6.4-A5 | v0.6.5-A6 |
|------|-----------|-----------|
| 評估指標來源 | 代理報酬（proxy returns） | 虛擬帳本 P&L（grounded metrics） |
| 訂單生成 | 無 | 有（OrderGenerationEngine） |
| 帳本追蹤 | 無 | 有（VirtualLedger） |
| 手續費/稅 | 不考慮 | 考慮（0.1425% / 0.3%） |
| War Room UI | Arena/Compare/Eval 卡片 | 新增 LedgerStatusCard |
| 執行層基礎 | 無 | 有（為真實執行預留） |

---

## 九、後續延伸點（預留）

1. **真實價格整合**：
   - 從 `PredictionSnapshot` 或外部資料源取得真實價格
   - 移除價格代理邏輯

2. **訂單執行模擬增強**：
   - 滑點（slippage）模擬
   - 流動性限制
   - 部分成交（partial fills）

3. **多標的帳本**：
   - 支援同時追蹤多個標的
   - 組合 NAV 計算

4. **真實交易橋接**：
   - 將 `OrderRequest` 轉換為券商 API 呼叫
   - 真實成交回報整合

---

## 十、總結

v0.6.5-A6 成功建立執行層基礎設施，讓 Decision V3 的評估與競技場系統從「理論指標」升級為「基於實際 P&L 的評估」，為後續真實交易執行奠定基礎。所有 CI 檢查通過，API 端點保證 200 回傳，前端 UI 完整整合。

**下一步建議：**
- 整合真實價格資料源
- 增強訂單執行模擬（滑點、流動性）
- 準備真實交易橋接（A7/A8）

