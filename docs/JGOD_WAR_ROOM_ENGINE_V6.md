# War Room Engine v6.0 文件

## 概述

War Room Engine v6.0 是一個**純事件流引擎**，專為 FastAPI WebSocket 和 Next.js 前端設計。與 v5.1 的主要差異在於：

- **v5.1 (舊引擎)**: 依賴 Streamlit，使用 `session_state` 管理狀態，整合在 Streamlit UI 中
- **v6.0 (新引擎)**: 不依賴 Streamlit，純事件驅動，透過 async generator 產生事件流，可被任何後端框架使用

## 架構設計

### 目錄結構

```
jgod/war_room_v6/
├── __init__.py              # 模組匯出
├── core/
│   ├── __init__.py
│   └── engine_v6.py         # 核心引擎實作
└── config/
    └── __init__.py          # 重用 v5 的設定
```

### 核心類別

#### `WarRoomEngineV6`

主要的引擎類別，提供 `run_session()` 方法產生事件流。

**初始化**:
```python
from jgod.war_room.providers import ProviderManager
from jgod.war_room_v6 import WarRoomEngineV6

provider_manager = ProviderManager()
engine = WarRoomEngineV6(provider_manager)
```

**核心方法**:
```python
async def run_session(
    self,
    request: WarRoomRequest,
) -> AsyncGenerator[WarRoomEvent, None]:
    """啟動戰情室 Session，產生事件流"""
    ...
```

#### `WarRoomRequest`

執行請求的資料結構：

```python
@dataclass
class WarRoomRequest:
    session_id: str
    stock_ids: List[str]
    mode: Literal["god", "custom"]
    enabled_providers: List[str]
    max_tokens: int = 512
    user_prompt: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    market_context: Optional[str] = None
```

#### `WarRoomEvent`

事件資料結構：

```python
@dataclass
class WarRoomEvent:
    type: EventType  # "session_start" | "role_start" | "role_chunk" | "role_done" | "summary" | "error"
    session_id: str
    role: Optional[str] = None
    role_label: Optional[str] = None  # 中文名稱
    provider: Optional[str] = None
    chunk: Optional[str] = None
    content: Optional[str] = None
    error: Optional[str] = None
    meta: Optional[Dict] = None
    
    def dict(self) -> Dict:
        """轉換為字典（用於 JSON 序列化）"""
        ...
```

## 使用方式

### FastAPI WebSocket 整合

```python
from fastapi import WebSocket
from jgod.war_room_v6 import WarRoomEngineV6, WarRoomRequest, WarRoomEvent
from jgod.war_room.providers import ProviderManager

provider_manager = ProviderManager()
engine = WarRoomEngineV6(provider_manager)

@app.websocket("/ws/war-room/{session_id}")
async def war_room_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    # 接收請求（從 WebSocket 接收 JSON）
    request_data = await websocket.receive_json()
    request = WarRoomRequest(
        session_id=session_id,
        stock_ids=request_data["stock_ids"],
        mode=request_data["mode"],
        enabled_providers=request_data["enabled_providers"],
        user_prompt=request_data["user_prompt"],
        # ... 其他欄位
    )
    
    # 執行 Session 並串流事件
    async for event in engine.run_session(request):
        # 將事件轉為 JSON 並發送
        await websocket.send_json(event.dict())
```

### 事件流順序

1. **session_start**: Session 開始
2. **role_start**: 每個角色開始執行（並行）
3. **role_chunk**: 每個角色的 streaming chunk（可能多次，並行）
4. **role_done**: 每個角色完成
5. **summary**: 最終總結
6. **error**: 錯誤事件（如果發生）

### 範例事件

**session_start**:
```json
{
  "type": "session_start",
  "session_id": "uuid-123",
  "meta": {
    "mode": "god",
    "enabled_providers": ["gpt", "claude", "gemini", "perplexity"],
    "stock_ids": ["2330", "2412"]
  }
}
```

**role_chunk**:
```json
{
  "type": "role_chunk",
  "session_id": "uuid-123",
  "role": "Intel Officer",
  "role_label": "情報官",
  "provider": "perplexity",
  "chunk": "根據市場分析..."
}
```

**role_done**:
```json
{
  "type": "role_done",
  "session_id": "uuid-123",
  "role": "Intel Officer",
  "role_label": "情報官",
  "provider": "perplexity",
  "content": "完整分析內容...",
  "meta": {
    "success": true,
    "execution_time": 3.45,
    "provider_name": "perplexity"
  }
}
```

**summary**:
```json
{
  "type": "summary",
  "session_id": "uuid-123",
  "content": "戰情室分析完成...",
  "meta": {
    "total_roles": 4,
    "successful_roles": 4,
    "failed_roles": 0
  }
}
```

## Next.js 前端整合

### WebSocket 訂閱

```typescript
// 建立 WebSocket 連線
const ws = new WebSocket(`ws://localhost:8000/ws/war-room/${sessionId}`);

// 發送請求
ws.onopen = () => {
  ws.send(JSON.stringify({
    stock_ids: ["2330", "2412"],
    mode: "god",
    enabled_providers: ["gpt", "claude", "gemini", "perplexity"],
    user_prompt: "請分析台積電和聯發科的投資建議"
  }));
};

// 接收事件
ws.onmessage = (event) => {
  const warRoomEvent: WarRoomEvent = JSON.parse(event.data);
  
  switch (warRoomEvent.type) {
    case "session_start":
      console.log("Session started:", warRoomEvent.meta);
      break;
    
    case "role_start":
      console.log(`Role started: ${warRoomEvent.role} (${warRoomEvent.provider})`);
      break;
    
    case "role_chunk":
      // 即時更新 UI
      appendChunkToRole(warRoomEvent.role, warRoomEvent.chunk);
      break;
    
    case "role_done":
      console.log(`Role done: ${warRoomEvent.role}, success: ${warRoomEvent.meta?.success}`);
      break;
    
    case "summary":
      console.log("Summary:", warRoomEvent.content);
      break;
    
    case "error":
      console.error("Error:", warRoomEvent.error);
      break;
  }
};
```

### UI 更新策略

1. **即時更新**: 收到 `role_chunk` 事件時，立即 append 到對應角色的文字區域
2. **狀態管理**: 使用 React state 或 Zustand 管理角色狀態（pending / running / done / error）
3. **並行顯示**: 多個角色可以同時顯示 streaming 內容，不需要等待全部完成

## 與 v5.1 的差異

| 特性 | v5.1 (舊引擎) | v6.0 (新引擎) |
|------|--------------|--------------|
| 依賴 | Streamlit | 無（純 Python） |
| 狀態管理 | `st.session_state` | 無（事件驅動） |
| UI 整合 | Streamlit UI | 任何前端框架 |
| 事件流 | 透過 callback 更新 state | Async generator |
| 使用場景 | 本機 Streamlit 應用 | FastAPI + Next.js |
| 並行執行 | ✅ | ✅ |
| Streaming | ✅ | ✅ |

## 設定重用

v6 引擎重用 v5 的設定模組（`jgod/war_room/config/roles.py`），包括：

- `ROLE_PROVIDER_MAP`: 角色到 Provider 的映射
- `ROLE_SYSTEM_PROMPTS`: 角色系統提示
- `ROLE_CHINESE_NAMES`: 角色中文名稱
- `MODE_PROVIDER_MAP`: 模式到 Provider 的映射

這樣可以確保 v5 和 v6 使用相同的角色和 Provider 設定，避免不一致。

## ProviderManager 整合

v6 引擎使用現有的 `ProviderManager`（`jgod/war_room/providers/provider_manager.py`），透過 `run_role_streaming()` 方法執行角色。這樣可以：

- 重用現有的 Provider 實作（GPT, Claude, Gemini, Perplexity）
- 保持 Provider 的統一管理
- 未來新增 Provider 時，v6 自動支援

## 測試

基本的單元測試位於 `tests/war_room_v6/test_engine_v6.py`，包含：

- 基本 Session 執行測試
- 事件流順序驗證
- 錯誤處理測試

## 未來擴展

- [ ] 支援多股票並行分析
- [ ] 支援自訂角色配置
- [ ] 支援事件回放（replay）
- [ ] 支援 Session 暫停/恢復
- [ ] 支援事件過濾（只接收特定角色的事件）

