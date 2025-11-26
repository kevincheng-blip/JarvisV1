# Engine v6 Chunk Callback & WebSocket 斷線修復總結

## ✅ 修復完成

### 問題 1: "no running event loop" 錯誤

**問題描述**:
- Engine v6 的 `on_chunk` callback 中使用了 `asyncio.get_running_loop()` 和 `asyncio.get_event_loop()`
- 當 callback 在沒有 event loop 的 context 中被呼叫時，會拋出 `RuntimeError: no running event loop`
- 導致大量錯誤日誌：`Error putting chunk event: no running event loop`

**修復方案**:
- ✅ 在 `async def run_single_role()` 函式一開始就取得 event loop
- ✅ `on_chunk` callback 使用外層已取得的 loop，不再呼叫 `get_running_loop()`
- ✅ 簡化 callback 邏輯，只使用 `loop.call_soon_threadsafe()`

**修改前**:
```python
def on_chunk(chunk: str):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.call_soon_threadsafe(...)
        else:
            asyncio.create_task(...)
    except RuntimeError:
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(...)
        except Exception as e:
            logger.error(f"Error putting chunk event: {e}")
```

**修改後**:
```python
# 在 async context 一開始就取得 event loop
loop = asyncio.get_running_loop()

def on_chunk(chunk: str):
    chunk_event = WarRoomEvent(...)
    # 只使用外層已取得的 loop，不再呼叫 get_running_loop()
    loop.call_soon_threadsafe(
        lambda: asyncio.create_task(event_queue.put(chunk_event))
    )
```

### 問題 2: WebSocket 斷線時 Engine 繼續執行

**問題描述**:
- WebSocket 斷線後，Engine v6 繼續執行到所有角色完成（例如 111 秒）
- 浪費 Provider token 和計算資源
- 日誌顯示 "No connections for session" 但 Engine 仍繼續執行

**修復方案**:
- ✅ 將 Engine 執行包裝成獨立的 `asyncio.Task`
- ✅ 監聽 WebSocket 連線狀態
- ✅ 當 session 沒有任何連線時，取消 Engine 任務
- ✅ 在 `WebSocketManager` 中新增 `has_connections()` 方法

**修改檔案**:

1. **`jgod/war_room_backend_v6/routers/war_room_ws.py`**:
   - 將 `engine.run_session()` 包裝成獨立的 task
   - 監聽 WebSocket 訊息和斷線事件
   - 當沒有連線時，取消 engine task

2. **`jgod/war_room_backend_v6/websocket_manager.py`**:
   - 新增 `has_connections(session_id: str) -> bool` 方法

**修改後結構**:
```python
async def war_room_websocket(websocket: WebSocket, session_id: str):
    await websocket_manager.connect(session_id, websocket)
    
    # 建立獨立的 engine task
    async def run_engine_and_broadcast():
        try:
            async for event in engine.run_session(war_room_request):
                # 檢查是否還有連線
                if not websocket_manager.has_connections(session_id):
                    break
                await websocket_manager.send_json(session_id, event.dict())
        except asyncio.CancelledError:
            logger.info(f"Engine task cancelled for session {session_id}")
            raise
    
    engine_task = asyncio.create_task(run_engine_and_broadcast())
    
    try:
        # 監聽 WebSocket 訊息
        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
            except asyncio.TimeoutError:
                # 定期檢查連線狀態
                if not websocket_manager.has_connections(session_id):
                    break
                continue
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: session={session_id}")
    finally:
        websocket_manager.disconnect(session_id, websocket)
        
        # 如果沒有連線，取消 engine 任務
        if not websocket_manager.has_connections(session_id):
            if not engine_task.done():
                engine_task.cancel()
                try:
                    await engine_task
                except asyncio.CancelledError:
                    logger.info(f"Engine task cancelled successfully")
```

## 📝 修改的檔案

1. **`jgod/war_room_v6/core/engine_v6.py`**
   - 修正 `on_chunk` callback，在 async context 一開始就取得 event loop
   - 移除 callback 中的 `get_running_loop()` 和 `get_event_loop()` 呼叫

2. **`jgod/war_room_backend_v6/routers/war_room_ws.py`**
   - 將 Engine 執行包裝成獨立 task
   - 加入 WebSocket 訊息監聽和連線狀態檢查
   - 實現 Engine 任務取消邏輯

3. **`jgod/war_room_backend_v6/websocket_manager.py`**
   - 新增 `has_connections(session_id: str) -> bool` 方法

## 🎯 預期行為

### 修復前
- ❌ 大量 "Error putting chunk event: no running event loop" 錯誤
- ❌ WebSocket 斷線後，Engine 繼續執行到完成（111 秒）
- ❌ 浪費 Provider token 和計算資源

### 修復後
- ✅ 不再出現 "no running event loop" 錯誤
- ✅ WebSocket 斷線後，Engine 任務立即被取消
- ✅ 不會再浪費資源執行無人接收的分析

## 🧪 測試建議

1. **語法檢查**: ✅ 通過（無 linter 錯誤）
2. **手動測試**:
   - 啟動後端和前端
   - 輸入股票代碼，啟動戰情室
   - 觀察各角色在 2～5 秒內開始打字
   - 中途關閉頁面，確認後端 Engine 任務被取消（不會執行超過 30 秒）

## 📊 技術細節

### Engine v6 on_chunk 修正
- **關鍵改變**: 在 `async def run_single_role()` 一開始就取得 `loop = asyncio.get_running_loop()`
- **Callback 簡化**: `on_chunk` 只使用外層的 `loop`，不再嘗試取得新的 loop
- **錯誤處理**: 移除複雜的 try-except 邏輯，因為設計已正確

### WebSocket 斷線處理
- **Task 管理**: Engine 執行包裝成 `asyncio.create_task()`
- **連線檢查**: 定期檢查 `websocket_manager.has_connections(session_id)`
- **任務取消**: 當沒有連線時，呼叫 `engine_task.cancel()` 並等待取消完成

