# J-GOD 戰情室 Phase 1 升級總結

## ✅ 完成項目

### 目標 1：Gemini（Scout）加速：改用最快速設定，首響 < 5 秒

**修改檔案**：
- `api_clients/gemini_client.py`
  - 模型改為 `gemini-1.5-flash`（最快的版本）
  - 在 `ask_stream` 中加入 `generation_config`，限制 `max_output_tokens` 為 512-768

- `jgod/war_room/providers/gemini_provider.py`
  - 在 `run_stream` 中加入 8 秒 timeout（使用 `asyncio.wait_for`）
  - 記錄第一個 chunk 的時間（`first_chunk_time`）
  - 當 timeout 時返回明確的錯誤訊息

**效果**：
- Scout 角色使用最快的 Gemini 模型
- 輸出長度限制在 512-768 tokens，加速回應
- Provider 層有 8 秒 timeout 保護

### 目標 2：所有角色都要顯示：首響時間 + 總耗時（ms）

**後端修改**：
- `jgod/war_room_v6/core/engine_v6.py`
  - `WarRoomEvent` dataclass 新增欄位：
    - `first_token_ms: Optional[int]` - 首響時間（毫秒）
    - `total_ms: Optional[int]` - 總耗時（毫秒）
    - `status: Optional[str]` - 狀態（ok, timeout, error）
  - 在 `run_single_role` 中：
    - 使用 `time.perf_counter()` 精確計時
    - 在 `on_chunk` callback 中記錄第一個 chunk 的時間
    - 在 `role_done` 事件中包含 `first_token_ms` 和 `total_ms`

**前端修改**：
- `frontend/war-room-web/lib/types/warRoom.ts`
  - `WarRoomEvent` 介面新增 `first_token_ms`, `total_ms`, `status` 欄位
  - `RoleState` 介面新增 `firstTokenMs`, `totalMs`, `roleStatus` 欄位

- `frontend/war-room-web/app/page.tsx` 和 `app/demo/tsmc/page.tsx`
  - 在 `handleEvent` 中接收並儲存 timing 資訊

- `frontend/war-room-web/components/pro/RoleCardPro.tsx`
  - `getExecutionTime()` 優先使用後端提供的 `firstTokenMs` 和 `totalMs`
  - 顯示格式：`首響：X.Xs｜總耗時：X.Xs`
  - 新增 `getStatusBadge()` 顯示 TIMEOUT 或 ERROR 標記

**效果**：
- 所有角色卡片都會顯示首響時間和總耗時
- 時間精確到毫秒級別
- 前端優先使用後端提供的精確時間

### 目標 3：全角色 Timeout fallback（避免整個卡住）

**修改檔案**：
- `jgod/war_room_v6/core/engine_v6.py`
  - 在 `run_single_role` 中為每個角色設定不同的 timeout：
    - Scout: 8 秒（已在 provider 層有 8 秒 timeout，這裡是第二層保險）
    - Strategist: 15 秒
    - 其他角色: 15 秒
  - 使用 `asyncio.wait_for` 包裝 provider 呼叫
  - 當 timeout 時：
    - 設定 `role_status = "timeout"`
    - 返回備援內容：「【系統備援】此角色在設定時間內未完成回應，已觸發 timeout。請稍後重試或檢查 provider 狀態。」
    - 在 `role_done` 事件中包含 `status: "timeout"`

**前端顯示**：
- `RoleCardPro.tsx` 中新增 `getStatusBadge()` 函式
- 當 `role.roleStatus === "timeout"` 時顯示紅色 "TIMEOUT" 標記
- 當 `role.roleStatus === "error"` 時顯示紅色 "ERROR" 標記

**效果**：
- 即使某個 provider 掛掉或太慢，也不會讓整個戰情室卡死
- 前端會明確顯示 timeout 狀態
- 使用者可以清楚知道哪些角色超時

### 目標 4：重寫 Mission Summary，改成結構化輸出

**修改檔案**：
- `jgod/war_room_v6/core/engine_v6.py`
  - 將 `_generate_summary` 改為 `async` 方法
  - 重新設計 summary prompt，要求輸出四個結構化標題：
    1. **Market Overview（市場概況）** - 大盤/產業/指數方向與重要事件
    2. **Technical & Indicators（技術與指標）** - K 線、型態、RSI/KD/MA 等技術指標
    3. **Capital & Risk（資金與風險）** - 資金流向、籌碼變化、風險點
    4. **Trading Stance（操作立場）** - 多空立場與具體操作建議
  - 如果 Strategist 的內容已經符合結構化格式，直接使用
  - 否則使用 Strategist 的 provider（通常是 GPT）重新生成結構化總結
  - 在 summary 事件的 `meta` 中加入 `"structured": True` 標記

**前端顯示**：
- `SummaryCardPro.tsx` 已經支援 Markdown 渲染
- 結構化的 summary 會自動以 Markdown 格式顯示，包含四個標題段落

**效果**：
- Mission Summary 變成結構化的四大段落
- 內容更清晰、更有條理
- 方便使用者快速理解市場概況、技術指標、風險評估和操作建議

## 📝 修改的檔案清單

### 後端
1. `api_clients/gemini_client.py` - Gemini 模型改為 1.5-flash，加入 generation_config
2. `jgod/war_room/providers/gemini_provider.py` - 加入 8 秒 timeout 和首響時間追蹤
3. `jgod/war_room_v6/core/engine_v6.py` - 加入 timing 追蹤、timeout fallback、結構化 summary

### 前端
4. `frontend/war-room-web/lib/types/warRoom.ts` - 新增 timing 相關欄位
5. `frontend/war-room-web/app/page.tsx` - 接收並處理 timing 資訊
6. `frontend/war-room-web/app/demo/tsmc/page.tsx` - 接收並處理 timing 資訊
7. `frontend/war-room-web/components/pro/RoleCardPro.tsx` - 顯示 timing 和 status badge

## 🎯 預期效果

1. **Scout 加速**：
   - 使用最快的 Gemini 1.5-flash 模型
   - 輸出長度限制在 512-768 tokens
   - Provider 層和 Engine 層都有 timeout 保護
   - 首響時間應該在 5 秒內

2. **Timing 顯示**：
   - 所有角色卡片都會顯示「首響：X.Xs｜總耗時：X.Xs」
   - 時間精確到毫秒級別
   - 前端優先使用後端提供的精確時間

3. **Timeout 保護**：
   - Scout: 8 秒 timeout
   - 其他角色: 15 秒 timeout
   - 超時時顯示明確的 TIMEOUT 標記和備援內容
   - 不會讓整個戰情室卡死

4. **結構化 Summary**：
   - 包含四個標題段落：Market Overview, Technical & Indicators, Capital & Risk, Trading Stance
   - 內容更清晰、更有條理
   - 方便使用者快速理解

## 🧪 測試建議

1. **啟動後端**：
   ```bash
   cd /Users/kevincheng/JarvisV1
   uvicorn jgod.war_room_backend_v6.main:app --host 0.0.0.0 --port 8081 --reload
   ```

2. **啟動前端**：
   ```bash
   cd /Users/kevincheng/JarvisV1/frontend/war-room-web
   npm run dev
   ```

3. **測試項目**：
   - 在首頁輸入股票代碼（例如：2330），啟動戰情室
   - 觀察 Scout 角色是否在 5 秒內開始回應
   - 檢查所有角色卡片是否顯示首響時間和總耗時
   - 如果某個 provider 超時，檢查是否顯示 TIMEOUT 標記
   - 檢查 Mission Summary 是否包含四個結構化標題段落

## 📊 技術細節

### Timing 追蹤
- 使用 `time.perf_counter()` 進行高精度計時
- 在 `on_chunk` callback 中記錄第一個 chunk 的時間
- 時間單位為毫秒（ms），便於前端顯示

### Timeout 機制
- Provider 層（Gemini）: 8 秒 timeout
- Engine 層: Scout 8 秒，其他角色 15 秒
- 雙層保護確保不會卡死

### 結構化 Summary
- 使用 Strategist 的 provider（通常是 GPT）生成結構化總結
- Prompt 明確要求四個標題段落
- 如果 Strategist 的內容已經符合格式，直接使用

## ✅ 完成狀態

所有四個目標已完成：
- ✅ Gemini（Scout）加速
- ✅ 首響時間 + 總耗時顯示
- ✅ Timeout fallback
- ✅ 結構化 Mission Summary

所有修改已自動 commit 並 push 到遠端。

