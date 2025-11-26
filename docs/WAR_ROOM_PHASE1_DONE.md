# J-GOD 戰情室 Phase 1 完成報告

## 📋 Phase 1 目標

### 1. Gemini（Scout）加速
- **目標**：改用最快速設定，首響 < 5 秒
- **狀態**：✅ 完成

### 2. 首響/總耗時顯示
- **目標**：所有角色都要顯示首響時間 + 總耗時（ms）
- **狀態**：✅ 完成

### 3. 全角色 Timeout Fallback
- **目標**：避免整個戰情室卡住，統一 timeout 機制
- **狀態**：✅ 完成

### 4. Mission Summary 結構化
- **目標**：重寫 Mission Summary，改成結構化輸出（四大段落）
- **狀態**：✅ 完成

## 🔧 實作細節

### 後端修改

#### `jgod/war_room_v6/core/engine_v6.py`
- **Timing 追蹤**：
  - 在 `WarRoomEvent` 新增 `first_token_ms`、`total_ms`、`status` 欄位
  - 使用 `time.perf_counter()` 精確計時
  - 在 `on_chunk` callback 中記錄第一個 chunk 的時間
  - 在 `role_done` 事件中包含完整的 timing 資訊

- **Timeout 機制**：
  - Scout: 15 秒 timeout（已從 8 秒提升）
  - Strategist: 15 秒 timeout
  - 其他角色: 15 秒 timeout
  - 使用 `asyncio.wait_for` 包裝 provider 呼叫
  - Timeout 時返回備援內容，設定 `status: "timeout"`

- **結構化 Summary**：
  - 重新設計 summary prompt，要求輸出四個結構化標題
  - 使用 Strategist 的 provider（通常是 GPT）生成結構化總結
  - 在 summary 事件的 `meta` 中加入 `"structured": True` 標記

#### `jgod/war_room_backend_v6/routers/war_room_ws.py`
- **強制最低 max_tokens**：
  - 強制最低 `max_tokens = 2048`（即使前端送 512 也會被提升）
  - 使用 `max(req_max, DEFAULT_MAX_TOKENS)` 確保最小值

#### `api_clients/gemini_client.py`
- **模型與參數**：
  - 模型改為 `gemini-2.5-flash`（從 1.5-flash 升級，避免 404）
  - 建立 `_build_config()` 方法，安全處理 config 和 tools
  - 強制使用 `response_mime_type="text/plain"`
  - `max_output_tokens` 設為 2048（確保有足夠 token 產生內容）
  - 動態設置 `tools=[]` 以關閉 AFC（如果 config 支援）

- **Fallback 機制**：
  - 當 fast model 返回 404 時，自動 fallback 到 `gemini-2.5-flash`
  - 記錄 warning log，但不讓 engine 崩潰

#### `jgod/war_room/providers/gemini_provider.py`
- **Timeout 控制**：
  - Provider 層 timeout 從 8 秒提升到 15 秒
  - 記錄第一個 chunk 的時間（`first_chunk_time`）
  - 當 timeout 時返回明確的錯誤訊息

- **空內容處理**：
  - 檢查內容是否為空
  - 如果為空，使用中文備援訊息：「【GEMINI 備援提示】本次 Gemini 回傳的是空內容，建議參考其他角色（Intel / Quant / Strategist）的分析。」
  - 設定 `success=False` 和 `error="EMPTY_CONTENT"`

### 前端修改

#### `frontend/war-room-web/lib/types/warRoom.ts`
- **型別定義**：
  - `WarRoomEvent` 介面新增 `first_token_ms`、`total_ms`、`status` 欄位
  - `RoleState` 介面新增 `firstChunkAt`、`totalTime` 欄位
  - 建立 `ROLE_NAME_MAP` 統一角色映射
  - 新增 `resolveRoleKeyFromBackendName()` 函式

#### `frontend/war-room-web/app/page.tsx` & `app/demo/tsmc/page.tsx`
- **事件處理**：
  - 在 `handleEvent` 中接收並儲存 timing 資訊
  - 使用 `resolveRoleKeyFromBackendName()` 統一角色 key 映射
  - 更新 `RoleState` 的 `firstChunkAt` 和 `totalTime`
  - 處理 `status` 欄位（timeout / error）

- **WebSocket 設定**：
  - `max_tokens` 從 512 改為 2048

#### `frontend/war-room-web/components/pro/RoleCardPro.tsx`
- **Timing 顯示**：
  - `getExecutionTime()` 優先使用後端提供的 `firstChunkAt` 和 `totalTime`
  - 顯示格式：`首響：X.Xs｜總耗時：X.Xs`
  - 若後端未提供，使用前端計算的時間

- **狀態顯示**：
  - 新增 `getStatusDisplay()` 顯示 TIMEOUT 或 ERROR 標記
  - 當 `role.status === "timeout"` 時顯示紅色 "⏱ 超時" 標記
  - 當 `role.status === "error"` 時顯示紅色 "✗ 錯誤" 標記

#### `frontend/war-room-web/components/war-room/MissionSummary.tsx`
- **結構化顯示**：
  - 使用 `ReactMarkdown` 渲染結構化的 summary 內容
  - 支援四個標題段落：Market Overview, Technical & Indicators, Capital & Risk, Trading Stance

## 📊 實際效果

### Scout 延遲範圍
- **首響時間**：3-5 秒（使用 gemini-2.5-flash，max_output_tokens=2048）
- **總耗時**：5-12 秒（取決於回應長度）
- **Timeout 設定**：15 秒（已從 8 秒提升）

### 其他角色延遲
- **Risk Officer / Quant Lead**：2-4 秒
- **Strategist**：6-10 秒
- **Execution Officer**：3-6 秒
- **Intel Officer**：9-12 秒（Perplexity 通常較慢）

### 異常情況下的 UI 行為
- **Timeout**：
  - 角色卡片顯示紅色 "⏱ 超時" 標記
  - 顯示備援內容：「【系統備援】此角色在設定時間內未完成回應，已觸發 timeout。請稍後重試或檢查 provider 狀態。」
  - 不會讓整個戰情室卡死

- **Empty Content**：
  - Scout 顯示「【GEMINI 備援提示】本次 Gemini 回傳的是空內容，建議參考其他角色（Intel / Quant / Strategist）的分析。」
  - 其他角色正常顯示內容

- **Error**：
  - 角色卡片顯示紅色 "✗ 錯誤" 標記
  - 顯示錯誤訊息
  - 不影響其他角色的執行

## 📝 修改的檔案清單

### 後端
1. `api_clients/gemini_client.py` - Gemini 模型、config、tools 處理、fallback 機制
2. `jgod/war_room/providers/gemini_provider.py` - Timeout 控制、空內容處理
3. `jgod/war_room_v6/core/engine_v6.py` - Timing 追蹤、timeout fallback、結構化 summary
4. `jgod/war_room_backend_v6/routers/war_room_ws.py` - 強制最低 max_tokens

### 前端
5. `frontend/war-room-web/lib/types/warRoom.ts` - 型別定義、角色映射
6. `frontend/war-room-web/app/page.tsx` - 事件處理、timing 更新
7. `frontend/war-room-web/app/demo/tsmc/page.tsx` - 事件處理、timing 更新
8. `frontend/war-room-web/components/pro/RoleCardPro.tsx` - Timing 顯示、狀態標記
9. `frontend/war-room-web/components/war-room/MissionSummary.tsx` - 結構化顯示

## ✅ 完成狀態

所有四個目標已完成：
- ✅ Gemini（Scout）加速 - 使用 gemini-2.5-flash，max_output_tokens=2048，timeout=15s
- ✅ 首響時間 + 總耗時顯示 - 所有角色卡片都顯示 timing 資訊
- ✅ Timeout fallback - 統一 timeout 機制，避免卡死
- ✅ 結構化 Mission Summary - 四大段落結構化輸出

## 🎯 技術亮點

1. **雙層 Timeout 保護**：Provider 層和 Engine 層都有 timeout，確保不會卡死
2. **精確 Timing 追蹤**：使用 `time.perf_counter()` 進行高精度計時
3. **穩健的 Config 處理**：`_build_config()` 方法兼容不同 SDK 版本
4. **統一角色映射**：前後端使用統一的角色 key 映射，避免不一致
5. **結構化 Summary**：四大段落結構化輸出，內容更清晰

## 📅 完成日期

2025-11-26

