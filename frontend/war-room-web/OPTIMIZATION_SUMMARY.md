# J-GOD War Room v6.0 優化總結

## ✅ 完成的優化項目

### A. 首頁可以連續啟動戰情室

**修改檔案**:
- `lib/types/warRoom.ts` - 新增 `SessionStatus` 類型（idle/running/finished）
- `lib/types/warRoom.ts` - 新增 `resetForNextRun()` helper 函數
- `app/page.tsx` - 更新狀態管理，支援連續啟動
- `components/pro/CommandPanelPro.tsx` - 更新按鈕 disabled 條件
- `components/layout/WarRoomLayoutPro.tsx` - 傳遞 wsStatus 給 CommandPanelPro

**功能**:
- ✅ 狀態機：idle（可啟動）→ running（執行中）→ finished（完成，可再啟動）
- ✅ 按鈕 disabled 條件：`state.status === "running" || wsStatus === "connecting"`
- ✅ 完成後自動重置為 idle，保留上一輪內容
- ✅ 不需要 F5 重整即可啟動下一輪

### B. 移除首頁自動送出行為

**修改檔案**:
- `app/page.tsx` - 確認沒有自動啟動邏輯
- `app/demo/tsmc/page.tsx` - 保留自動啟動（僅 Demo 頁面）

**功能**:
- ✅ 首頁（`/`）絕對不會自動啟動
- ✅ 只有 Demo 頁面（`/demo/tsmc`）會自動啟動
- ✅ 自動啟動邏輯僅在 Demo 頁面的 useEffect 中

### C. UI 全中文化

**修改檔案**:
- `lib/types/warRoom.ts` - 新增 `ROLE_DISPLAY_NAME_ZH` 和 `ROLE_DISPLAY_NAME_EN`
- `components/pro/RoleCardPro.tsx` - 顯示中文職稱 + 英文副標
- `components/pro/CommandPanelPro.tsx` - 所有 UI 文案中文化
- `components/war-room/RoleGrid.tsx` - 更新 RoleKey 格式
- `components/pro/SummaryCardPro.tsx` - 更新 RoleKey 格式

**功能**:
- ✅ 六大角色顯示：中文職稱（大）+ 英文名稱（小）
  - 情報官 (Intel Officer)
  - 斥候官 (Scout)
  - 風控官 (Risk Officer)
  - 量化官 (Quant Lead)
  - 策略官 (Strategist)
  - 執行官 (Execution Officer)
- ✅ 所有 UI 文案中文化
- ✅ Provider 名稱保持英文（GPT / Claude / Gemini / Perplexity）

### D. 性能優化：加速回應

**修改檔案**:
- `jgod/war_room_v6/core/engine_v6.py` - 不同角色設定不同 max_tokens
- `jgod/war_room_v6/core/engine_v6.py` - 在 role prompt 加上簡短回答指示
- `jgod/war_room/providers/provider_manager.py` - 支援 max_tokens 參數
- `jgod/war_room/providers/base_provider.py` - 更新 run_stream 簽名
- `app/page.tsx` - 追蹤首響時間（firstChunkAt）
- `components/pro/RoleCardPro.tsx` - 顯示首響時間和總耗時

**功能**:
- ✅ Strategist：max_tokens = 512（維持）
- ✅ 其他角色：max_tokens = 256（加速）
- ✅ 非 Strategist 角色的 system prompt 加上「請用 2～4 句話給出最關鍵的觀點與建議，不要寫長篇大論。」
- ✅ 前端追蹤首響時間（firstChunkAt）
- ✅ 卡片顯示：`首響：2.8s｜總耗時：9.7s`

## 📝 修改的檔案清單

### 前端
1. `frontend/war-room-web/lib/types/warRoom.ts`
2. `frontend/war-room-web/app/page.tsx`
3. `frontend/war-room-web/app/demo/tsmc/page.tsx`
4. `frontend/war-room-web/components/pro/CommandPanelPro.tsx`
5. `frontend/war-room-web/components/pro/RoleCardPro.tsx`
6. `frontend/war-room-web/components/pro/SummaryCardPro.tsx`
7. `frontend/war-room-web/components/war-room/RoleGrid.tsx`
8. `frontend/war-room-web/components/layout/WarRoomLayoutPro.tsx`

### 後端
1. `jgod/war_room_v6/core/engine_v6.py`
2. `jgod/war_room/providers/provider_manager.py`
3. `jgod/war_room/providers/base_provider.py`

## 🎯 預期行為

1. **連續啟動**: 首頁可以連續啟動多次戰情室，不需重整頁面
2. **無自動送出**: 首頁不會自動啟動，只有 Demo 頁面會自動啟動
3. **全中文 UI**: 所有角色顯示中文職稱，所有 UI 文案中文化
4. **快速回應**: 除 Strategist 外，其他角色 2～4 秒內開始打字，回答簡短精煉

## 📊 性能指標

- **首響時間**: 2～4 秒（非 Strategist 角色）
- **總耗時**: 視角色而定，但會比之前更快
- **回答長度**: 非 Strategist 角色限制為 2～4 句話

