# War Room Frontend v6.0 修復總結

## ✅ 修復完成

### Part 1: Demo Page useState 重複宣告錯誤

**檔案**: `app/demo/tsmc/page.tsx`

**問題**: 
- 檔案中有兩個 React import：
  - 第 3 行：`import { useEffect, useState, useCallback } from "react";`
  - 第 13 行：`import { useState, useCallback } from "react";`（重複！）

**修復**:
- ✅ 移除第 13 行的重複 import
- ✅ 現在只有一個 React import：`import { useEffect, useState, useCallback } from "react";`
- ✅ 確認檔案頂部有 `"use client";` 標記
- ✅ 確認沒有其他重複宣告

**驗證**:
- ✅ 只有一個 React import
- ✅ 沒有 `const useState = ...` 之類的錯誤宣告
- ✅ 檔案是 Client Component

### Part 2: WebSocket 403 Forbidden 修復

**檔案**: `lib/ws/warRoomClientPro.ts`

**問題**:
- WebSocket URL 組合不正確
- 缺少 debug log

**修復**:

1. **建立 `buildWebSocketUrl` 函數**:
   ```typescript
   function buildWebSocketUrl(sessionId: string): string {
     // 轉換 http:// -> ws://, https:// -> wss://
     let base = BACKEND_BASE_URL.replace("http://", "ws://").replace("https://", "wss://");
     
     // 確保不會多一個或少一個斜線
     base = base.endsWith("/") ? base.slice(0, -1) : base;
     
     // 組合完整 WebSocket URL（後端路由 prefix 是 /api/v6/war-room）
     const wsUrl = `${base}/api/v6/war-room/ws/v6/war-room/${sessionId}`;
     
     return wsUrl;
   }
   ```

2. **更新 `connect` 方法使用新函數**:
   - ✅ 使用 `buildWebSocketUrl(sessionId)` 取代原本的 URL 組合
   - ✅ 確保 URL 格式正確

3. **添加 Debug Log**:
   - ✅ 連線前：`console.log("[WS_PRO] Connecting to:", wsUrl);`
   - ✅ 連線成功：`console.log("[WS_PRO] WS connected");`
   - ✅ 發送請求：`console.log("[WS_PRO] Sending request data:", requestData);`
   - ✅ 錯誤：`console.error("[WS_PRO] WS error", error);`
   - ✅ 關閉：`console.warn("[WS_PRO] WS closed", event.code, event.reason || "No reason");`

**後端路由結構**:
- Router prefix: `/api/v6/war-room`
- WebSocket route: `/ws/v6/war-room/{session_id}`
- 完整路徑: `/api/v6/war-room/ws/v6/war-room/{session_id}`

### 確認使用 PRO 版客戶端

**檢查結果**:
- ✅ `app/page.tsx` - 使用 `WarRoomWebSocketClientPro`
- ✅ `app/demo/tsmc/page.tsx` - 使用 `WarRoomWebSocketClientPro`
- ✅ 沒有使用舊版 `WarRoomWebSocketClient`

## 📝 修改的檔案

1. `frontend/war-room-web/app/demo/tsmc/page.tsx`
   - 移除重複的 React import

2. `frontend/war-room-web/lib/ws/warRoomClientPro.ts`
   - 新增 `buildWebSocketUrl` 函數
   - 更新 `connect` 方法使用新函數
   - 添加完整的 debug log

## 🧪 驗證步驟

### 1. 編譯檢查
```bash
cd frontend/war-room-web
npm run dev
```
- ✅ 不應出現 `Identifier 'useState' has already been declared` 錯誤

### 2. 頁面訪問
- ✅ `http://localhost:3000/` - 主頁正常打開
- ✅ `http://localhost:3000/demo/tsmc` - Demo 頁面正常打開，不會 500

### 3. WebSocket 連線
- ✅ 啟動後端：`uvicorn jgod.war_room_backend_v6.main:app --host 0.0.0.0 --port 8081 --reload`
- ✅ 啟動前端：`npm run dev`
- ✅ 打開 `http://localhost:3000/demo/tsmc`
- ✅ 在瀏覽器 DevTools Console 看到：
  - `[WS_PRO] Connecting to: ws://localhost:8081/api/v6/war-room/ws/v6/war-room/{session_id}`
  - `[WS_PRO] WS connected`
  - `[WS_PRO] Sending request data: {...}`
  - `[WS_PRO] Event received: session_start`
  - `[WS_PRO] Event received: role_start`
  - `[WS_PRO] Event received: role_chunk`
  - ...

### 4. 後端 Log
- ✅ 看到 `[API] Session created: {session_id}`
- ✅ 看到 `[WS] Client connected: session={session_id}`
- ✅ 看到 `[WS] Received request for session {session_id}`
- ✅ 看到 `[WS] Event sent: {event_type} for session {session_id}`
- ✅ 不應出現 403 Forbidden

### 5. UI 功能
- ✅ 6 個角色卡片逐步開始「打字」
- ✅ 事件時間軸會滾動新增事件
- ✅ Mission Summary 會顯示 AI 總結

## 🎯 預期結果

1. **編譯**: 無錯誤，可以正常啟動
2. **連線**: WebSocket 成功連線，不再出現 403
3. **事件流**: 前端可以正常接收並顯示 War Room 事件
4. **UI**: 所有功能正常運作

## 📌 注意事項

- WebSocket URL 現在使用統一的 `buildWebSocketUrl` 函數組合
- 所有 debug log 都在 Console 中可見，方便除錯
- 確保後端路由結構與前端 URL 組合一致

